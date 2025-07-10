"""
AI量化选股算法
基于技术面、基本面、市场情绪等多维度分析进行股票推荐
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

from .schemas import (
    AIStockRecommendation, AITradingStrategy, FinancialMetrics, 
    AIAnalysisRequest, AIAnalysisResponse
)
from .stock_service import get_stock_data
from .fundamental_service import get_financial_metrics, analyze_financial_health


class TechnicalAnalyzer:
    """技术分析器"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, std_dev: int = 2) -> Dict:
        """计算布林带"""
        ma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        
        return {
            'middle': ma,
            'upper': upper,
            'lower': lower
        }
    
    @staticmethod
    def calculate_moving_averages(prices: pd.Series) -> Dict:
        """计算多种移动平均线"""
        return {
            'ma_5': prices.rolling(5).mean(),
            'ma_10': prices.rolling(10).mean(),
            'ma_20': prices.rolling(20).mean(),
            'ma_50': prices.rolling(50).mean(),
            'ma_200': prices.rolling(200).mean()
        }
    
    @staticmethod
    def analyze_price_momentum(data: pd.DataFrame) -> Dict:
        """分析价格动量"""
        close_prices = data['Close']
        
        # 计算收益率
        returns_1d = close_prices.pct_change(1)
        returns_5d = close_prices.pct_change(5)
        returns_20d = close_prices.pct_change(20)
        
        # 计算动量得分
        momentum_score = 0
        
        # 短期动量 (1-5天)
        if returns_5d.iloc[-1] > 0:
            momentum_score += 25
        if returns_1d.iloc[-1] > 0:
            momentum_score += 15
        
        # 中期动量 (20天)
        if returns_20d.iloc[-1] > 0:
            momentum_score += 35
        
        # 趋势强度
        ma = TechnicalAnalyzer.calculate_moving_averages(close_prices)
        current_price = close_prices.iloc[-1]
        
        if current_price > ma['ma_5'].iloc[-1]:
            momentum_score += 5
        if current_price > ma['ma_20'].iloc[-1]:
            momentum_score += 10
        if current_price > ma['ma_50'].iloc[-1]:
            momentum_score += 10
        
        return {
            'momentum_score': momentum_score,
            'returns_1d': returns_1d.iloc[-1],
            'returns_5d': returns_5d.iloc[-1],
            'returns_20d': returns_20d.iloc[-1]
        }
    
    @staticmethod
    def technical_analysis(data: pd.DataFrame) -> Dict:
        """综合技术分析"""
        if len(data) < 50:
            return {'technical_score': 50, 'signals': [], 'warnings': ['数据不足']}
        
        close_prices = data['Close']
        volume = data['Volume']
        
        # 计算技术指标
        rsi = TechnicalAnalyzer.calculate_rsi(close_prices)
        macd_data = TechnicalAnalyzer.calculate_macd(close_prices)
        bb_data = TechnicalAnalyzer.calculate_bollinger_bands(close_prices)
        ma_data = TechnicalAnalyzer.calculate_moving_averages(close_prices)
        momentum = TechnicalAnalyzer.analyze_price_momentum(data)
        
        signals = []
        warnings = []
        technical_score = 50  # 基准分数
        
        # RSI分析
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        if current_rsi < 30:
            signals.append(f"RSI超卖({current_rsi:.1f})，可能反弹")
            technical_score += 15
        elif current_rsi > 70:
            warnings.append(f"RSI超买({current_rsi:.1f})，注意回调风险")
            technical_score -= 10
        elif 40 < current_rsi < 60:
            signals.append("RSI中性区间，趋势稳定")
            technical_score += 5
        
        # MACD分析
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        if current_macd > current_signal:
            signals.append("MACD金叉，上涨信号")
            technical_score += 10
        else:
            signals.append("MACD死叉，下跌信号")
            technical_score -= 10
        
        # 布林带分析
        current_price = close_prices.iloc[-1]
        bb_upper = bb_data['upper'].iloc[-1]
        bb_lower = bb_data['lower'].iloc[-1]
        bb_middle = bb_data['middle'].iloc[-1]
        
        if current_price > bb_upper:
            warnings.append("价格突破布林带上轨，可能超买")
            technical_score -= 5
        elif current_price < bb_lower:
            signals.append("价格跌破布林带下轨，可能超卖")
            technical_score += 10
        elif current_price > bb_middle:
            signals.append("价格在布林带上半部，相对强势")
            technical_score += 5
        
        # 移动平均线分析
        ma_signals = []
        if current_price > ma_data['ma_5'].iloc[-1]:
            ma_signals.append("5日线上方")
            technical_score += 3
        if current_price > ma_data['ma_20'].iloc[-1]:
            ma_signals.append("20日线上方")
            technical_score += 5
        if current_price > ma_data['ma_50'].iloc[-1]:
            ma_signals.append("50日线上方")
            technical_score += 7
        
        if ma_signals:
            signals.append(f"站稳{', '.join(ma_signals)}")
        
        # 成交量分析
        avg_volume = volume.rolling(20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        if current_volume > avg_volume * 1.5:
            signals.append("放量上涨，资金关注")
            technical_score += 8
        elif current_volume < avg_volume * 0.5:
            warnings.append("缩量，关注度不足")
            technical_score -= 3
        
        # 动量分析
        technical_score += momentum['momentum_score'] * 0.2
        
        # 限制分数范围
        technical_score = max(0, min(100, technical_score))
        
        return {
            'technical_score': technical_score,
            'signals': signals,
            'warnings': warnings,
            'rsi': current_rsi,
            'macd_signal': 'bullish' if current_macd > current_signal else 'bearish',
            'momentum': momentum
        }


class FundamentalAnalyzer:
    """基本面分析器"""
    
    @staticmethod
    def calculate_fundamental_score(metrics: FinancialMetrics) -> Dict:
        """计算基本面得分"""
        score = 50  # 基准分数
        reasons = []
        warnings = []
        
        # P/E比率评估
        if metrics.pe_ratio:
            if metrics.pe_ratio < 15:
                score += 15
                reasons.append(f"P/E比率较低({metrics.pe_ratio:.1f})，估值合理")
            elif metrics.pe_ratio > 30:
                score -= 10
                warnings.append(f"P/E比率偏高({metrics.pe_ratio:.1f})，估值可能过高")
        
        # P/B比率评估
        if metrics.pb_ratio:
            if metrics.pb_ratio < 2:
                score += 10
                reasons.append(f"P/B比率较低({metrics.pb_ratio:.1f})，账面价值支撑")
            elif metrics.pb_ratio > 5:
                score -= 8
                warnings.append(f"P/B比率过高({metrics.pb_ratio:.1f})")
        
        # ROE评估
        if metrics.roe:
            if metrics.roe > 15:
                score += 20
                reasons.append(f"ROE优秀({metrics.roe:.1f}%)，盈利能力强")
            elif metrics.roe > 10:
                score += 10
                reasons.append(f"ROE良好({metrics.roe:.1f}%)")
            elif metrics.roe < 5:
                score -= 15
                warnings.append(f"ROE较低({metrics.roe:.1f}%)")
        
        # 债务评估
        if metrics.debt_to_equity:
            if metrics.debt_to_equity < 0.3:
                score += 12
                reasons.append("财务杠杆较低，财务稳健")
            elif metrics.debt_to_equity > 1.0:
                score -= 15
                warnings.append("债务负担较重")
        
        # 增长性评估
        if metrics.revenue_growth:
            if metrics.revenue_growth > 15:
                score += 18
                reasons.append(f"营收增长强劲({metrics.revenue_growth:.1f}%)")
            elif metrics.revenue_growth > 5:
                score += 8
                reasons.append(f"营收稳定增长({metrics.revenue_growth:.1f}%)")
            elif metrics.revenue_growth < -5:
                score -= 20
                warnings.append("营收下滑")
        
        # 利润率评估
        if metrics.net_margin:
            if metrics.net_margin > 20:
                score += 15
                reasons.append(f"净利润率优秀({metrics.net_margin:.1f}%)")
            elif metrics.net_margin > 10:
                score += 8
                reasons.append(f"净利润率良好({metrics.net_margin:.1f}%)")
            elif metrics.net_margin < 5:
                score -= 10
                warnings.append("利润率偏低")
        
        # 限制分数范围
        score = max(0, min(100, score))
        
        return {
            'fundamental_score': score,
            'reasons': reasons,
            'warnings': warnings
        }


class SentimentAnalyzer:
    """市场情绪分析器"""
    
    @staticmethod
    def analyze_market_sentiment(ticker: str, data: pd.DataFrame) -> Dict:
        """分析市场情绪"""
        sentiment_score = 50  # 基准分数
        signals = []
        
        # 成交量趋势分析
        recent_volume = data['Volume'].tail(5).mean()
        historical_volume = data['Volume'].head(-5).mean()
        
        if recent_volume > historical_volume * 1.2:
            sentiment_score += 15
            signals.append("近期成交量放大，市场关注度提升")
        elif recent_volume < historical_volume * 0.8:
            sentiment_score -= 10
            signals.append("成交量萎缩，市场关注度下降")
        
        # 价格波动性分析
        returns = data['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        if volatility < 0.2:
            sentiment_score += 8
            signals.append("波动率较低，价格稳定")
        elif volatility > 0.4:
            sentiment_score -= 12
            signals.append("波动率较高，价格不稳定")
        
        # 趋势一致性分析
        ma_5 = data['Close'].rolling(5).mean()
        ma_20 = data['Close'].rolling(20).mean()
        
        # 检查趋势方向一致性
        trend_consistency = 0
        for i in range(-5, 0):
            if ma_5.iloc[i] > ma_20.iloc[i]:
                trend_consistency += 1
        
        if trend_consistency >= 4:
            sentiment_score += 10
            signals.append("短期趋势向上且稳定")
        elif trend_consistency <= 1:
            sentiment_score -= 10
            signals.append("短期趋势向下")
        
        # 模拟新闻情绪（实际实现中可以集成新闻API）
        news_sentiment = self._simulate_news_sentiment(ticker)
        sentiment_score += news_sentiment * 10
        
        sentiment_score = max(0, min(100, sentiment_score))
        
        return {
            'sentiment_score': sentiment_score,
            'signals': signals,
            'volatility': volatility,
            'volume_trend': 'increasing' if recent_volume > historical_volume else 'decreasing',
            'news_sentiment': news_sentiment
        }
    
    @staticmethod
    def _simulate_news_sentiment(ticker: str) -> float:
        """模拟新闻情绪评分（-1到1之间）"""
        # 基于ticker的hash值生成模拟情绪分数
        hash_val = hash(ticker + str(datetime.now().date())) % 200
        return (hash_val - 100) / 100


class RiskAnalyzer:
    """风险分析器"""
    
    @staticmethod
    def calculate_risk_metrics(data: pd.DataFrame, benchmark_data: Optional[pd.DataFrame] = None) -> Dict:
        """计算风险指标"""
        returns = data['Close'].pct_change().dropna()
        
        # 基本风险指标
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        max_drawdown = RiskAnalyzer._calculate_max_drawdown(data['Close'])
        
        # VaR计算
        var_95 = np.percentile(returns, 5) * 100
        var_99 = np.percentile(returns, 1) * 100
        
        # 风险评级
        risk_level = "LOW"
        if volatility > 0.4:
            risk_level = "HIGH"
        elif volatility > 0.25:
            risk_level = "MEDIUM"
        
        # Beta计算（如果有基准数据）
        beta = None
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
            if len(returns) == len(benchmark_returns):
                covariance = np.cov(returns, benchmark_returns)[0][1]
                benchmark_variance = np.var(benchmark_returns)
                beta = covariance / benchmark_variance if benchmark_variance != 0 else None
        
        return {
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'var_99': var_99,
            'risk_level': risk_level,
            'beta': beta,
            'sharpe_ratio': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) != 0 else 0
        }
    
    @staticmethod
    def _calculate_max_drawdown(prices: pd.Series) -> float:
        """计算最大回撤"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        max_drawdown = drawdown.min()
        return abs(max_drawdown) * 100


class AIStockAnalyzer:
    """AI股票分析器主类"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
    
    async def analyze_stock(self, ticker: str, strategy: AITradingStrategy) -> AIStockRecommendation:
        """分析单只股票"""
        try:
            # 获取股票数据
            stock_data = get_stock_data(ticker, period="1y")
            if stock_data.empty:
                raise ValueError(f"无法获取{ticker}的数据")
            
            # 获取基本面数据
            try:
                financial_metrics = await get_financial_metrics(ticker)
            except:
                financial_metrics = None
            
            # 技术分析
            technical_analysis = self.technical_analyzer.technical_analysis(stock_data)
            
            # 基本面分析
            fundamental_analysis = {'fundamental_score': 50, 'reasons': [], 'warnings': []}
            if financial_metrics:
                fundamental_analysis = self.fundamental_analyzer.calculate_fundamental_score(financial_metrics)
            
            # 情绪分析
            sentiment_analysis = self.sentiment_analyzer.analyze_market_sentiment(ticker, stock_data)
            
            # 风险分析
            risk_analysis = self.risk_analyzer.calculate_risk_metrics(stock_data)
            
            # 应用策略过滤器
            if not self._passes_strategy_filters(ticker, financial_metrics, risk_analysis, strategy):
                return None
            
            # 综合评分
            final_score, recommendation, reasons, risk_factors = self._calculate_final_score(
                technical_analysis, fundamental_analysis, sentiment_analysis, risk_analysis, strategy
            )
            
            # 计算建议仓位
            suggested_position, suggested_weight = self._calculate_position_sizing(
                final_score, risk_analysis, strategy
            )
            
            # 获取公司名称
            try:
                yf_ticker = yf.Ticker(ticker)
                info = yf_ticker.info
                company_name = info.get('longName', ticker)
            except:
                company_name = ticker
            
            return AIStockRecommendation(
                ticker=ticker,
                company_name=company_name,
                recommendation=recommendation,
                confidence_score=final_score / 100,
                target_price=self._calculate_target_price(stock_data, technical_analysis, fundamental_analysis),
                technical_score=technical_analysis['technical_score'],
                fundamental_score=fundamental_analysis['fundamental_score'],
                sentiment_score=sentiment_analysis['sentiment_score'],
                final_score=final_score,
                reasons=reasons,
                risk_factors=risk_factors,
                suggested_position_size=suggested_position,
                suggested_weight=suggested_weight,
                analysis_date=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=1)
            )
            
        except Exception as e:
            print(f"分析{ticker}时出错: {str(e)}")
            return None
    
    def _passes_strategy_filters(self, ticker: str, metrics: Optional[FinancialMetrics], 
                               risk_analysis: Dict, strategy: AITradingStrategy) -> bool:
        """检查是否通过策略过滤器"""
        
        # 检查排除行业
        if metrics and metrics.sector in strategy.excluded_sectors:
            return False
        
        # 检查市值要求
        if strategy.min_market_cap and metrics and metrics.market_cap:
            if metrics.market_cap < strategy.min_market_cap:
                return False
        
        # 检查PE比率要求
        if strategy.max_pe_ratio and metrics and metrics.pe_ratio:
            if metrics.pe_ratio > strategy.max_pe_ratio:
                return False
        
        # 检查风险承受度
        if strategy.risk_tolerance == "conservative" and risk_analysis['risk_level'] == "HIGH":
            return False
        
        return True
    
    def _calculate_final_score(self, technical: Dict, fundamental: Dict, 
                             sentiment: Dict, risk: Dict, strategy: AITradingStrategy) -> Tuple[float, str, List[str], List[str]]:
        """计算综合得分和推荐"""
        
        # 根据风险承受度调整权重
        if strategy.risk_tolerance == "conservative":
            weights = {'technical': 0.2, 'fundamental': 0.5, 'sentiment': 0.1, 'risk': 0.2}
        elif strategy.risk_tolerance == "aggressive":
            weights = {'technical': 0.4, 'fundamental': 0.3, 'sentiment': 0.2, 'risk': 0.1}
        else:  # moderate
            weights = {'technical': 0.3, 'fundamental': 0.4, 'sentiment': 0.2, 'risk': 0.1}
        
        # 计算加权得分
        final_score = (
            technical['technical_score'] * weights['technical'] +
            fundamental['fundamental_score'] * weights['fundamental'] +
            sentiment['sentiment_score'] * weights['sentiment'] +
            (100 - risk['volatility'] * 100) * weights['risk']  # 风险越低分数越高
        )
        
        # 确定推荐
        if final_score >= 75:
            recommendation = "BUY"
        elif final_score >= 60:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        # 汇总原因
        reasons = []
        reasons.extend(technical['signals'][:3])  # 最多3个技术面原因
        reasons.extend(fundamental['reasons'][:3])  # 最多3个基本面原因
        reasons.extend(sentiment['signals'][:2])   # 最多2个情绪面原因
        
        # 风险因素
        risk_factors = []
        risk_factors.extend(technical.get('warnings', []))
        risk_factors.extend(fundamental.get('warnings', []))
        if risk['risk_level'] == "HIGH":
            risk_factors.append(f"高波动性({risk['volatility']:.1%})")
        if risk['max_drawdown'] > 30:
            risk_factors.append(f"历史最大回撤较大({risk['max_drawdown']:.1f}%)")
        
        return final_score, recommendation, reasons[:5], risk_factors[:3]
    
    def _calculate_position_sizing(self, score: float, risk_analysis: Dict, 
                                 strategy: AITradingStrategy) -> Tuple[float, float]:
        """计算建议仓位大小"""
        base_position = strategy.max_position_size / 100  # 转换为小数
        
        # 根据得分调整
        score_multiplier = score / 75  # 75分为基准
        
        # 根据风险调整
        risk_multiplier = 1.0
        if risk_analysis['risk_level'] == "HIGH":
            risk_multiplier = 0.5
        elif risk_analysis['risk_level'] == "LOW":
            risk_multiplier = 1.2
        
        # 根据风险承受度调整
        tolerance_multiplier = {
            "conservative": 0.7,
            "moderate": 1.0,
            "aggressive": 1.3
        }.get(strategy.risk_tolerance, 1.0)
        
        suggested_weight = min(
            base_position * score_multiplier * risk_multiplier * tolerance_multiplier,
            base_position
        )
        
        # 假设组合总价值为100万
        suggested_position = suggested_weight * 1000000
        
        return suggested_position, suggested_weight * 100
    
    def _calculate_target_price(self, data: pd.DataFrame, technical: Dict, fundamental: Dict) -> Optional[float]:
        """计算目标价格"""
        current_price = data['Close'].iloc[-1]
        
        # 基于技术分析的目标价格
        technical_target = current_price * 1.1  # 默认10%涨幅
        
        # 基于基本面的调整
        if fundamental['fundamental_score'] > 80:
            multiplier = 1.2
        elif fundamental['fundamental_score'] > 60:
            multiplier = 1.1
        else:
            multiplier = 1.05
        
        target_price = current_price * multiplier
        return round(target_price, 2)
    
    async def batch_analyze_stocks(self, tickers: List[str], strategy: AITradingStrategy) -> List[AIStockRecommendation]:
        """批量分析股票"""
        recommendations = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 创建任务
            tasks = []
            for ticker in tickers:
                task = asyncio.create_task(self.analyze_stock(ticker, strategy))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, AIStockRecommendation):
                    recommendations.append(result)
                elif isinstance(result, Exception):
                    print(f"分析出错: {result}")
        
        # 按照综合得分排序
        recommendations.sort(key=lambda x: x.final_score, reverse=True)
        
        return recommendations[:strategy.max_stocks_to_analyze]
    
    async def generate_analysis_response(self, request: AIAnalysisRequest, strategy: AITradingStrategy) -> AIAnalysisResponse:
        """生成AI分析响应"""
        
        # 获取股票池（这里使用一些热门股票作为示例）
        stock_pool = self._get_stock_pool(request.target_sectors)
        
        # 批量分析
        recommendations = await self.batch_analyze_stocks(stock_pool, strategy)
        
        # 过滤推荐数量
        top_recommendations = recommendations[:request.max_recommendations]
        
        # 分析市场情绪
        market_sentiment = self._analyze_overall_market_sentiment(recommendations)
        
        # 生成建议行动
        suggested_actions = self._generate_suggested_actions(top_recommendations, strategy)
        
        # 生成风险警告
        risk_warnings = self._generate_risk_warnings(top_recommendations)
        
        return AIAnalysisResponse(
            portfolio_id=request.portfolio_id,
            analysis_date=datetime.now(timezone.utc),
            recommendations=top_recommendations,
            market_sentiment=market_sentiment,
            suggested_actions=suggested_actions,
            risk_warnings=risk_warnings,
            next_analysis_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
    
    def _get_stock_pool(self, target_sectors: List[str]) -> List[str]:
        """获取股票池"""
        # 这里返回一些示例股票，实际实现中应该从数据库或API获取
        default_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "JNJ", "PG",
            "UNH", "HD", "MA", "BAC", "ABBV", "PFE", "KO", "PEP", "TMO", "COST",
            "AVGO", "XOM", "LLY", "CVX", "WMT", "DHR", "ABT", "CRM", "ACN", "VZ"
        ]
        
        # 如果指定了行业，可以在这里进行过滤
        # 这里简化处理，直接返回默认股票池
        return default_stocks[:50]  # 限制分析数量
    
    def _analyze_overall_market_sentiment(self, recommendations: List[AIStockRecommendation]) -> str:
        """分析整体市场情绪"""
        if not recommendations:
            return "neutral"
        
        buy_count = sum(1 for rec in recommendations if rec.recommendation == "BUY")
        sell_count = sum(1 for rec in recommendations if rec.recommendation == "SELL")
        
        if buy_count > sell_count * 1.5:
            return "bullish"
        elif sell_count > buy_count * 1.5:
            return "bearish"
        else:
            return "neutral"
    
    def _generate_suggested_actions(self, recommendations: List[AIStockRecommendation], 
                                  strategy: AITradingStrategy) -> List[str]:
        """生成建议行动"""
        actions = []
        
        buy_recommendations = [r for r in recommendations if r.recommendation == "BUY"]
        
        if buy_recommendations:
            actions.append(f"考虑买入{len(buy_recommendations)}只推荐股票")
            
            # 按得分排序，推荐前3只
            top_3 = sorted(buy_recommendations, key=lambda x: x.final_score, reverse=True)[:3]
            for stock in top_3:
                actions.append(f"重点关注{stock.ticker}，建议仓位{stock.suggested_weight:.1f}%")
        
        if strategy.enable_sector_diversification:
            actions.append("注意行业分散化，避免集中投资单一行业")
        
        if strategy.enable_risk_management:
            actions.append(f"设置止损位({strategy.stop_loss_pct}%)和止盈位({strategy.take_profit_pct}%)")
        
        return actions
    
    def _generate_risk_warnings(self, recommendations: List[AIStockRecommendation]) -> List[str]:
        """生成风险警告"""
        warnings = []
        
        high_risk_stocks = [r for r in recommendations if "高波动性" in str(r.risk_factors)]
        if high_risk_stocks:
            warnings.append(f"有{len(high_risk_stocks)}只股票具有高波动性风险")
        
        low_score_stocks = [r for r in recommendations if r.final_score < 60]
        if low_score_stocks:
            warnings.append(f"有{len(low_score_stocks)}只股票评分较低，需谨慎考虑")
        
        warnings.append("市场存在不确定性，建议分散投资")
        warnings.append("请根据个人风险承受能力调整仓位")
        
        return warnings


# 全局AI分析器实例
ai_stock_analyzer = AIStockAnalyzer()