import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
import yfinance as yf
from .stock_service import get_stock_data
from .schemas import (
    VaRAnalysis, DrawdownAnalysis, VolatilityAnalysis, CorrelationAnalysis,
    PositionSizing, PortfolioRiskMetrics, RiskManagementSummary
)

class RiskManagementService:
    
    def __init__(self):
        # 市场基准数据
        self.market_ticker = "SPY"  # S&P 500 ETF作为市场基准
        
    def calculate_var(self, ticker: str, confidence_level: float = 0.95, 
                     period_days: int = 252) -> Optional[VaRAnalysis]:
        """计算VaR（风险价值）"""
        try:
            # 获取历史数据
            hist = get_stock_data(ticker, period="2y")
            if hist.empty or len(hist) < 30:
                return None
                
            # 计算日收益率
            returns = hist['Close'].pct_change().dropna()
            current_price = float(hist['Close'].iloc[-1])
            
            # 历史模拟法VaR
            sorted_returns = returns.sort_values()
            var_index = int((1 - confidence_level) * len(sorted_returns))
            historical_var = abs(sorted_returns.iloc[var_index]) * 100
            
            # 参数法VaR（假设正态分布）
            mean_return = returns.mean()
            std_return = returns.std()
            z_score = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}.get(confidence_level, 1.645)
            parametric_var = abs(mean_return - z_score * std_return) * 100
            
            # 计算最差情况
            worst_day_loss = abs(returns.min()) * 100
            
            # 计算最差周收益
            weekly_returns = returns.rolling(5).sum().dropna()
            worst_week_loss = abs(weekly_returns.min()) * 100
            
            # 风险等级评估
            if historical_var <= 2:
                risk_level = "LOW"
            elif historical_var <= 5:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            var_explanation = (
                f"在{confidence_level*100:.0f}%的置信度下，{ticker}单日最大损失不会超过"
                f"{historical_var:.2f}%。历史上最坏的一天损失了{worst_day_loss:.2f}%。"
            )
            
            return VaRAnalysis(
                ticker=ticker,
                period_days=period_days,
                confidence_level=confidence_level,
                historical_var=historical_var,
                parametric_var=parametric_var,
                current_price=current_price,
                var_explanation=var_explanation,
                risk_level=risk_level,
                historical_returns=returns.tolist()[-100:],  # 最近100日收益率
                worst_day_loss=worst_day_loss,
                worst_week_loss=worst_week_loss
            )
            
        except Exception as e:
            print(f"VaR calculation error for {ticker}: {e}")
            return None
    
    def calculate_drawdown(self, ticker: str, period: str = "2y") -> Optional[DrawdownAnalysis]:
        """计算最大回撤分析"""
        try:
            hist = get_stock_data(ticker, period=period)
            if hist.empty:
                return None
                
            prices = hist['Close']
            
            # 计算累计最高价和回撤
            cumulative_max = prices.cummax()
            drawdown = (prices - cumulative_max) / cumulative_max * 100
            
            # 最大回撤
            max_drawdown = drawdown.min()
            max_dd_date = drawdown.idxmin()
            
            # 当前回撤
            current_drawdown = drawdown.iloc[-1]
            
            # 找出所有回撤期间
            drawdown_periods = []
            in_drawdown = False
            start_date = None
            peak_price = 0
            
            for date, price in prices.items():
                current_max = cumulative_max.loc[date]
                current_dd = drawdown.loc[date]
                
                if current_dd < -0.5 and not in_drawdown:  # 开始回撤（超过0.5%）
                    in_drawdown = True
                    start_date = date
                    peak_price = current_max
                elif current_dd >= -0.1 and in_drawdown:  # 结束回撤（恢复到0.1%以内）
                    end_date = date
                    duration = (end_date - start_date).days
                    drawdown_pct = (peak_price - price) / peak_price * 100
                    
                    if duration > 5:  # 持续5天以上的回撤才记录
                        drawdown_periods.append({
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "drawdown_pct": round(drawdown_pct, 2),
                            "duration": duration
                        })
                    
                    in_drawdown = False
            
            # 计算平均恢复时间
            if drawdown_periods:
                avg_recovery_time = np.mean([period["duration"] for period in drawdown_periods])
                max_dd_duration = max([period["duration"] for period in drawdown_periods])
            else:
                avg_recovery_time = 0
                max_dd_duration = 0
            
            # 回撤评分（0-100分）
            if abs(max_drawdown) <= 5:
                drawdown_score = 90
            elif abs(max_drawdown) <= 10:
                drawdown_score = 80
            elif abs(max_drawdown) <= 20:
                drawdown_score = 60
            elif abs(max_drawdown) <= 30:
                drawdown_score = 40
            else:
                drawdown_score = 20
            
            # 风险警告
            risk_warning = None
            if abs(current_drawdown) > 15:
                risk_warning = f"当前回撤{abs(current_drawdown):.1f}%，接近历史最大回撤，需谨慎"
            elif abs(current_drawdown) > 10:
                risk_warning = f"当前回撤{abs(current_drawdown):.1f}%，处于较高风险区域"
            
            return DrawdownAnalysis(
                ticker=ticker,
                period=period,
                max_drawdown=round(max_drawdown, 2),
                max_drawdown_duration=max_dd_duration,
                current_drawdown=round(current_drawdown, 2),
                drawdown_periods=drawdown_periods[-10:],  # 最近10次回撤
                recovery_time_avg=round(avg_recovery_time, 1),
                drawdown_score=drawdown_score,
                risk_warning=risk_warning
            )
            
        except Exception as e:
            print(f"Drawdown calculation error for {ticker}: {e}")
            return None
    
    def calculate_volatility(self, ticker: str) -> Optional[VolatilityAnalysis]:
        """计算波动率分析"""
        try:
            hist = get_stock_data(ticker, period="1y")
            if hist.empty:
                return None
                
            returns = hist['Close'].pct_change().dropna()
            
            # 各周期波动率
            daily_vol = returns.std() * 100
            weekly_vol = returns.rolling(5).sum().std() * 100
            monthly_vol = returns.rolling(21).sum().std() * 100
            annual_vol = returns.std() * np.sqrt(252) * 100
            
            # 滚动波动率
            vol_30d = returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100
            vol_90d = returns.rolling(90).std().iloc[-1] * np.sqrt(252) * 100
            
            # 波动率趋势
            recent_vol = returns.rolling(30).std().iloc[-30:]
            if len(recent_vol) > 20:
                vol_trend_slope = np.polyfit(range(len(recent_vol)), recent_vol, 1)[0]
                if vol_trend_slope > 0.0001:
                    volatility_trend = "INCREASING"
                elif vol_trend_slope < -0.0001:
                    volatility_trend = "DECREASING" 
                else:
                    volatility_trend = "STABLE"
            else:
                volatility_trend = "STABLE"
            
            # 波动率分级
            if annual_vol <= 15:
                volatility_rank = "LOW"
            elif annual_vol <= 25:
                volatility_rank = "MEDIUM"
            else:
                volatility_rank = "HIGH"
            
            # 计算Beta（相对市场）
            try:
                market_data = get_stock_data(self.market_ticker, period="1y")
                if not market_data.empty:
                    market_returns = market_data['Close'].pct_change().dropna()
                    # 对齐数据
                    aligned_data = pd.concat([returns, market_returns], axis=1, join='inner')
                    if len(aligned_data) > 50:
                        covariance = aligned_data.cov().iloc[0, 1]
                        market_variance = aligned_data.iloc[:, 1].var()
                        beta = covariance / market_variance if market_variance != 0 else None
                    else:
                        beta = None
                else:
                    beta = None
            except:
                beta = None
            
            return VolatilityAnalysis(
                ticker=ticker,
                daily_volatility=round(daily_vol, 2),
                weekly_volatility=round(weekly_vol, 2),
                monthly_volatility=round(monthly_vol, 2),
                annualized_volatility=round(annual_vol, 2),
                volatility_30d=round(vol_30d, 2),
                volatility_90d=round(vol_90d, 2),
                volatility_trend=volatility_trend,
                volatility_rank=volatility_rank,
                vs_market_beta=round(beta, 2) if beta else None
            )
            
        except Exception as e:
            print(f"Volatility calculation error for {ticker}: {e}")
            return None
    
    def calculate_correlation(self, base_ticker: str, 
                            comparison_tickers: List[str]) -> Optional[CorrelationAnalysis]:
        """计算相关性分析"""
        try:
            # 获取所有股票数据
            all_data = {}
            for ticker in [base_ticker] + comparison_tickers:
                hist = get_stock_data(ticker, period="1y")
                if not hist.empty:
                    all_data[ticker] = hist['Close'].pct_change().dropna()
            
            if len(all_data) < 2:
                return None
            
            # 构建DataFrame并计算相关性
            df = pd.DataFrame(all_data)
            correlation_matrix = df.corr()
            
            # 转换为字典格式
            corr_dict = {}
            for ticker1 in correlation_matrix.index:
                corr_dict[ticker1] = {}
                for ticker2 in correlation_matrix.columns:
                    corr_dict[ticker1][ticker2] = round(correlation_matrix.loc[ticker1, ticker2], 3)
            
            # 找出最高和最低相关性（排除自身）
            base_correlations = correlation_matrix[base_ticker].drop(base_ticker)
            if len(base_correlations) > 0:
                highest_corr = base_correlations.max()
                lowest_corr = base_correlations.min()
                highest_ticker = base_correlations.idxmax()
                lowest_ticker = base_correlations.idxmin()
                
                highest_correlation = {"ticker": highest_ticker, "value": round(highest_corr, 3)}
                lowest_correlation = {"ticker": lowest_ticker, "value": round(lowest_corr, 3)}
            else:
                highest_correlation = {"ticker": "N/A", "value": 0}
                lowest_correlation = {"ticker": "N/A", "value": 0}
            
            # 与市场相关性
            market_correlation = None
            if self.market_ticker in all_data and base_ticker != self.market_ticker:
                market_data = get_stock_data(self.market_ticker, period="1y")
                if not market_data.empty:
                    market_returns = market_data['Close'].pct_change().dropna()
                    base_returns = all_data[base_ticker]
                    aligned = pd.concat([base_returns, market_returns], axis=1, join='inner')
                    if len(aligned) > 50:
                        market_correlation = round(aligned.corr().iloc[0, 1], 3)
            
            # 分散化评分
            avg_correlation = abs(base_correlations.mean()) if len(base_correlations) > 0 else 0
            if avg_correlation <= 0.3:
                diversification_score = 90
                diversification_advice = "相关性较低，分散化效果良好"
            elif avg_correlation <= 0.6:
                diversification_score = 70
                diversification_advice = "相关性中等，分散化效果一般"
            else:
                diversification_score = 40
                diversification_advice = "相关性较高，分散化效果有限，建议增加不相关资产"
            
            return CorrelationAnalysis(
                base_ticker=base_ticker,
                comparison_tickers=comparison_tickers,
                correlation_matrix=corr_dict,
                highest_correlation=highest_correlation,
                lowest_correlation=lowest_correlation,
                market_correlation=market_correlation,
                diversification_score=diversification_score,
                diversification_advice=diversification_advice
            )
            
        except Exception as e:
            print(f"Correlation calculation error: {e}")
            return None
    
    def calculate_position_sizing(self, ticker: str, investment_amount: float = 10000) -> Optional[PositionSizing]:
        """计算仓位管理建议"""
        try:
            hist = get_stock_data(ticker, period="2y")
            if hist.empty:
                return None
                
            returns = hist['Close'].pct_change().dropna()
            current_price = float(hist['Close'].iloc[-1])
            
            # 简化的胜率和盈亏比计算
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            
            win_rate = len(positive_returns) / len(returns)
            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
            avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
            
            # 凯利公式: f = (bp - q) / b
            # b = 平均盈利/平均亏损, p = 胜率, q = 败率
            if avg_loss > 0:
                b = avg_win / avg_loss
                kelly_percentage = (b * win_rate - (1 - win_rate)) / b * 100
                kelly_percentage = max(0, min(50, kelly_percentage))  # 限制在0-50%之间
            else:
                kelly_percentage = 0
            
            # 风险调整建议
            conservative_position = kelly_percentage * 0.25  # 保守：凯利的1/4
            aggressive_position = kelly_percentage * 0.5     # 激进：凯利的1/2
            recommended_position = kelly_percentage * 0.375  # 推荐：凯利的3/8
            
            # 止损止盈价格
            volatility = returns.std()
            stop_loss_price = current_price * (1 - 2 * volatility)
            take_profit_price = current_price * (1 + 3 * volatility)
            
            # 最大持仓金额
            max_position_size = investment_amount * (recommended_position / 100)
            
            # 风险提示
            risk_warnings = []
            if kelly_percentage < 5:
                risk_warnings.append("凯利公式建议仓位较低，该股票可能不适合投资")
            if volatility > 0.03:
                risk_warnings.append("股票波动率较高，建议降低仓位")
            if win_rate < 0.45:
                risk_warnings.append("历史胜率较低，投资需谨慎")
            
            return PositionSizing(
                ticker=ticker,
                current_price=current_price,
                win_rate=round(win_rate * 100, 1),
                avg_win=round(avg_win * 100, 2),
                avg_loss=round(avg_loss * 100, 2),
                kelly_percentage=round(kelly_percentage, 1),
                conservative_position=round(conservative_position, 1),
                aggressive_position=round(aggressive_position, 1),
                recommended_position=round(recommended_position, 1),
                stop_loss_price=round(stop_loss_price, 2),
                take_profit_price=round(take_profit_price, 2),
                max_position_size=round(max_position_size, 2),
                risk_warnings=risk_warnings
            )
            
        except Exception as e:
            print(f"Position sizing calculation error for {ticker}: {e}")
            return None
    
    def get_comprehensive_risk_analysis(self, ticker: str) -> Optional[RiskManagementSummary]:
        """获取股票的综合风险分析"""
        try:
            # 计算各项风险指标
            var_analysis = self.calculate_var(ticker)
            drawdown_analysis = self.calculate_drawdown(ticker)
            volatility_analysis = self.calculate_volatility(ticker)
            position_sizing = self.calculate_position_sizing(ticker)
            
            # 计算综合风险评分
            risk_scores = []
            key_risks = []
            
            if var_analysis:
                if var_analysis.risk_level == "LOW":
                    risk_scores.append(20)
                elif var_analysis.risk_level == "MEDIUM":
                    risk_scores.append(50)
                else:
                    risk_scores.append(80)
                    key_risks.append(f"日VaR风险较高({var_analysis.historical_var:.1f}%)")
            
            if drawdown_analysis:
                risk_scores.append(100 - drawdown_analysis.drawdown_score)
                if abs(drawdown_analysis.max_drawdown) > 20:
                    key_risks.append(f"历史最大回撤较大({abs(drawdown_analysis.max_drawdown):.1f}%)")
            
            if volatility_analysis:
                if volatility_analysis.volatility_rank == "LOW":
                    risk_scores.append(20)
                elif volatility_analysis.volatility_rank == "MEDIUM":
                    risk_scores.append(50)
                else:
                    risk_scores.append(80)
                    key_risks.append(f"波动率较高({volatility_analysis.annualized_volatility:.1f}%)")
            
            # 综合风险评分
            overall_risk_score = np.mean(risk_scores) if risk_scores else 50
            
            if overall_risk_score <= 30:
                overall_risk_level = "LOW"
            elif overall_risk_score <= 60:
                overall_risk_level = "MEDIUM"
            elif overall_risk_score <= 80:
                overall_risk_level = "HIGH"
            else:
                overall_risk_level = "EXTREME"
            
            # 风险缓解建议
            risk_mitigation_suggestions = []
            if overall_risk_level in ["HIGH", "EXTREME"]:
                risk_mitigation_suggestions.extend([
                    "建议降低仓位规模，控制单一标的风险敞口",
                    "设置严格的止损点，及时止损",
                    "考虑分批建仓，降低时点风险"
                ])
            if volatility_analysis and volatility_analysis.volatility_rank == "HIGH":
                risk_mitigation_suggestions.append("可通过期权等衍生品进行对冲")
            if len(key_risks) == 0:
                risk_mitigation_suggestions.append("风险水平适中，建议定期复评")
            
            return RiskManagementSummary(
                ticker_or_portfolio=ticker,
                analysis_type="SINGLE_STOCK",
                var_analysis=var_analysis,
                drawdown_analysis=drawdown_analysis,
                volatility_analysis=volatility_analysis,
                position_sizing=position_sizing,
                overall_risk_level=overall_risk_level,
                risk_score=round(overall_risk_score, 1),
                key_risks=key_risks,
                risk_mitigation_suggestions=risk_mitigation_suggestions
            )
            
        except Exception as e:
            print(f"Comprehensive risk analysis error for {ticker}: {e}")
            return None

# 全局实例
risk_service = RiskManagementService()