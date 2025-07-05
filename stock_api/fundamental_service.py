import yfinance as yf
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from .schemas import FinancialMetrics, FinancialHealth, IndustryComparison, ComprehensiveAnalysis
from .ai_agent import make_decision

class FundamentalAnalysisService:
    
    def __init__(self):
        # 行业平均值参考数据（实际应用中可以从数据库或API获取）
        self.industry_benchmarks = {
            "Technology": {
                "avg_pe": 25.0, "avg_pb": 3.5, "avg_roe": 15.0, 
                "avg_debt_ratio": 0.3, "avg_gross_margin": 0.65
            },
            "Financial Services": {
                "avg_pe": 12.0, "avg_pb": 1.2, "avg_roe": 12.0,
                "avg_debt_ratio": 0.8, "avg_gross_margin": 0.45
            },
            "Healthcare": {
                "avg_pe": 20.0, "avg_pb": 2.8, "avg_roe": 14.0,
                "avg_debt_ratio": 0.4, "avg_gross_margin": 0.70
            },
            "Consumer Cyclical": {
                "avg_pe": 18.0, "avg_pb": 2.2, "avg_roe": 13.0,
                "avg_debt_ratio": 0.5, "avg_gross_margin": 0.35
            },
            "Communication Services": {
                "avg_pe": 22.0, "avg_pb": 2.0, "avg_roe": 10.0,
                "avg_debt_ratio": 0.6, "avg_gross_margin": 0.50
            },
            "Default": {
                "avg_pe": 18.0, "avg_pb": 2.5, "avg_roe": 12.0,
                "avg_debt_ratio": 0.5, "avg_gross_margin": 0.40
            }
        }
    
    def get_financial_metrics(self, ticker: str) -> Optional[FinancialMetrics]:
        """获取股票的财务指标"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 基本信息
            company_name = info.get('longName', ticker)
            sector = info.get('sector', '未知')
            industry = info.get('industry', '未知')
            market_cap = info.get('marketCap')
            enterprise_value = info.get('enterpriseValue')
            
            # 估值指标
            pe_ratio = info.get('trailingPE')
            forward_pe = info.get('forwardPE')
            peg_ratio = info.get('pegRatio')
            pb_ratio = info.get('priceToBook')
            ps_ratio = info.get('priceToSalesTrailing12Months')
            ev_revenue = info.get('enterpriseToRevenue')
            ev_ebitda = info.get('enterpriseToEbitda')
            
            # 盈利能力
            gross_margin = info.get('grossMargins')
            operating_margin = info.get('operatingMargins')
            net_margin = info.get('profitMargins')
            roe = info.get('returnOnEquity')
            roa = info.get('returnOnAssets')
            
            # 财务健康度
            debt_to_equity = info.get('debtToEquity')
            current_ratio = info.get('currentRatio')
            quick_ratio = info.get('quickRatio')
            
            # 成长性
            revenue_growth = info.get('revenueGrowth')
            earnings_growth = info.get('earningsGrowth')
            dividend_yield = info.get('dividendYield')
            payout_ratio = info.get('payoutRatio')
            
            # 其他指标
            beta = info.get('beta')
            shares_outstanding = info.get('sharesOutstanding')
            float_shares = info.get('floatShares')
            avg_volume = info.get('averageVolume')
            
            # 计算债务资产比
            total_debt = info.get('totalDebt', 0)
            total_assets = info.get('totalAssets', 1)
            debt_to_assets = (total_debt / total_assets) if total_assets > 0 else None
            
            # 计算投入资本回报率 (ROIC)
            ebit = info.get('ebit')
            invested_capital = info.get('totalAssets', 0) - info.get('totalCurrentLiabilities', 0)
            roic = (ebit / invested_capital) if ebit and invested_capital > 0 else None
            
            return FinancialMetrics(
                ticker=ticker.upper(),
                company_name=company_name,
                sector=sector,
                industry=industry,
                market_cap=market_cap,
                enterprise_value=enterprise_value,
                pe_ratio=pe_ratio,
                forward_pe=forward_pe,
                peg_ratio=peg_ratio,
                pb_ratio=pb_ratio,
                ps_ratio=ps_ratio,
                ev_revenue=ev_revenue,
                ev_ebitda=ev_ebitda,
                gross_margin=gross_margin * 100 if gross_margin else None,
                operating_margin=operating_margin * 100 if operating_margin else None,
                net_margin=net_margin * 100 if net_margin else None,
                roe=roe * 100 if roe else None,
                roa=roa * 100 if roa else None,
                roic=roic * 100 if roic else None,
                debt_to_equity=debt_to_equity,
                current_ratio=current_ratio,
                quick_ratio=quick_ratio,
                debt_to_assets=debt_to_assets * 100 if debt_to_assets else None,
                revenue_growth=revenue_growth * 100 if revenue_growth else None,
                earnings_growth=earnings_growth * 100 if earnings_growth else None,
                dividend_yield=dividend_yield * 100 if dividend_yield else None,
                payout_ratio=payout_ratio * 100 if payout_ratio else None,
                beta=beta,
                shares_outstanding=shares_outstanding,
                float_shares=float_shares,
                avg_volume=avg_volume
            )
            
        except Exception as e:
            print(f"Error fetching financial metrics for {ticker}: {e}")
            return None
    
    def calculate_financial_health(self, metrics: FinancialMetrics) -> FinancialHealth:
        """计算财务健康度评分"""
        
        # 盈利能力评分 (0-100)
        profitability_score = 0
        if metrics.roe:
            profitability_score += min(metrics.roe * 2, 40)  # ROE > 20% = 40分
        if metrics.net_margin:
            profitability_score += min(metrics.net_margin * 2, 30)  # 净利率 > 15% = 30分
        if metrics.gross_margin:
            profitability_score += min(metrics.gross_margin / 2, 30)  # 毛利率 > 60% = 30分
        
        # 流动性评分 (0-100)
        liquidity_score = 50  # 基础分
        if metrics.current_ratio:
            if metrics.current_ratio >= 2.0:
                liquidity_score += 30
            elif metrics.current_ratio >= 1.5:
                liquidity_score += 20
            elif metrics.current_ratio >= 1.0:
                liquidity_score += 10
            else:
                liquidity_score -= 20
        
        if metrics.quick_ratio:
            if metrics.quick_ratio >= 1.0:
                liquidity_score += 20
            elif metrics.quick_ratio >= 0.5:
                liquidity_score += 10
            else:
                liquidity_score -= 10
        
        # 杠杆评分 (0-100)
        leverage_score = 50
        if metrics.debt_to_equity:
            if metrics.debt_to_equity <= 0.3:
                leverage_score += 30
            elif metrics.debt_to_equity <= 0.6:
                leverage_score += 20
            elif metrics.debt_to_equity <= 1.0:
                leverage_score += 10
            else:
                leverage_score -= 20
        
        if metrics.debt_to_assets:
            if metrics.debt_to_assets <= 30:
                leverage_score += 20
            elif metrics.debt_to_assets <= 50:
                leverage_score += 10
            else:
                leverage_score -= 10
        
        # 效率评分 (0-100)
        efficiency_score = 0
        if metrics.roa:
            efficiency_score += min(metrics.roa * 3, 40)
        if metrics.roic:
            efficiency_score += min(metrics.roic * 2, 40)
        if metrics.operating_margin:
            efficiency_score += min(metrics.operating_margin, 20)
        
        # 成长性评分 (0-100)
        growth_score = 50
        if metrics.revenue_growth:
            if metrics.revenue_growth > 0:
                growth_score += min(metrics.revenue_growth * 2, 30)
            else:
                growth_score += max(metrics.revenue_growth, -30)
        
        if metrics.earnings_growth:
            if metrics.earnings_growth > 0:
                growth_score += min(metrics.earnings_growth, 20)
            else:
                growth_score += max(metrics.earnings_growth / 2, -20)
        
        # 确保分数在0-100范围内
        profitability_score = max(0, min(100, profitability_score))
        liquidity_score = max(0, min(100, liquidity_score))
        leverage_score = max(0, min(100, leverage_score))
        efficiency_score = max(0, min(100, efficiency_score))
        growth_score = max(0, min(100, growth_score))
        
        # 计算总体评分
        overall_score = (profitability_score * 0.3 + 
                        liquidity_score * 0.2 + 
                        leverage_score * 0.2 + 
                        efficiency_score * 0.2 + 
                        growth_score * 0.1)
        
        # 生成优缺点分析
        strengths = []
        weaknesses = []
        recommendations = []
        
        if profitability_score > 70:
            strengths.append("盈利能力强劲，ROE和净利率表现优秀")
        elif profitability_score < 40:
            weaknesses.append("盈利能力较弱，需关注成本控制")
            
        if liquidity_score > 70:
            strengths.append("流动性充足，短期偿债能力强")
        elif liquidity_score < 40:
            weaknesses.append("流动性不足，存在短期偿债风险")
            recommendations.append("关注现金流管理，提高流动比率")
            
        if leverage_score > 70:
            strengths.append("债务水平合理，财务结构稳健")
        elif leverage_score < 40:
            weaknesses.append("债务负担较重，财务杠杆风险较高")
            recommendations.append("考虑降低债务水平，优化资本结构")
            
        if growth_score > 70:
            strengths.append("业务增长强劲，发展前景良好")
        elif growth_score < 40:
            weaknesses.append("增长乏力，需寻找新的增长点")
            recommendations.append("关注公司战略转型和业务创新")
        
        return FinancialHealth(
            ticker=metrics.ticker,
            overall_score=round(overall_score, 1),
            profitability_score=round(profitability_score, 1),
            liquidity_score=round(liquidity_score, 1),
            leverage_score=round(leverage_score, 1),
            efficiency_score=round(efficiency_score, 1),
            growth_score=round(growth_score, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def get_industry_comparison(self, metrics: FinancialMetrics) -> IndustryComparison:
        """行业对比分析"""
        
        # 获取行业基准数据
        industry_key = metrics.sector if metrics.sector in self.industry_benchmarks else "Default"
        benchmarks = self.industry_benchmarks[industry_key]
        
        # 计算百分位数（简化版，实际应用中需要更多同行业数据）
        def calculate_percentile(value, benchmark, higher_is_better=True):
            if not value:
                return None
            ratio = value / benchmark
            if higher_is_better:
                if ratio >= 1.2:
                    return 80
                elif ratio >= 1.1:
                    return 70
                elif ratio >= 0.9:
                    return 50
                elif ratio >= 0.8:
                    return 30
                else:
                    return 20
            else:  # lower is better
                if ratio <= 0.8:
                    return 80
                elif ratio <= 0.9:
                    return 70
                elif ratio <= 1.1:
                    return 50
                elif ratio <= 1.2:
                    return 30
                else:
                    return 20
        
        pe_percentile = calculate_percentile(metrics.pe_ratio, benchmarks["avg_pe"], False)
        pb_percentile = calculate_percentile(metrics.pb_ratio, benchmarks["avg_pb"], False)
        roe_percentile = calculate_percentile(metrics.roe, benchmarks["avg_roe"], True)
        margin_percentile = calculate_percentile(metrics.gross_margin, benchmarks["avg_gross_margin"] * 100, True)
        
        # 生成对比总结
        summary_parts = []
        
        if pe_percentile and pe_percentile > 60:
            summary_parts.append("估值相对行业偏低")
        elif pe_percentile and pe_percentile < 40:
            summary_parts.append("估值相对行业偏高")
            
        if roe_percentile and roe_percentile > 60:
            summary_parts.append("盈利能力超越行业平均")
        elif roe_percentile and roe_percentile < 40:
            summary_parts.append("盈利能力低于行业平均")
            
        if margin_percentile and margin_percentile > 60:
            summary_parts.append("毛利率表现优秀")
        elif margin_percentile and margin_percentile < 40:
            summary_parts.append("成本控制有待改善")
        
        comparison_summary = "，".join(summary_parts) if summary_parts else "与行业平均水平基本一致"
        
        return IndustryComparison(
            ticker=metrics.ticker,
            industry=f"{metrics.sector} - {metrics.industry}",
            industry_avg_pe=benchmarks["avg_pe"],
            industry_avg_pb=benchmarks["avg_pb"],
            industry_avg_roe=benchmarks["avg_roe"],
            industry_avg_debt_ratio=benchmarks["avg_debt_ratio"],
            industry_avg_gross_margin=benchmarks["avg_gross_margin"] * 100,
            pe_percentile=pe_percentile,
            pb_percentile=pb_percentile,
            roe_percentile=roe_percentile,
            margin_percentile=margin_percentile,
            comparison_summary=comparison_summary
        )
    
    def get_comprehensive_analysis(self, ticker: str) -> Optional[ComprehensiveAnalysis]:
        """综合分析：技术面 + 基本面"""
        try:
            # 获取技术分析
            from .stock_service import get_stock_data
            hist = get_stock_data(ticker, period="6mo")
            if hist.empty:
                return None
                
            technical_decision, technical_reasons = make_decision(hist)
            
            # 获取基本面数据
            financial_metrics = self.get_financial_metrics(ticker)
            if not financial_metrics:
                return None
                
            financial_health = self.calculate_financial_health(financial_metrics)
            industry_comparison = self.get_industry_comparison(financial_metrics)
            
            # 综合决策逻辑
            confidence_level = 50  # 基础信心度
            
            # 技术面权重 40%
            technical_score = 0
            if technical_decision == "BUY":
                technical_score = 80
                confidence_level += 15
            elif technical_decision == "SELL":
                technical_score = 20
                confidence_level += 15
            else:
                technical_score = 50
            
            # 基本面权重 60%
            fundamental_score = financial_health.overall_score
            
            # 加权综合分数
            overall_score = technical_score * 0.4 + fundamental_score * 0.6
            
            # 最终建议
            if overall_score >= 70:
                final_recommendation = "BUY"
                confidence_level += 20
            elif overall_score <= 40:
                final_recommendation = "SELL"
                confidence_level += 20
            else:
                final_recommendation = "HOLD"
                confidence_level += 10
            
            # 调整信心度
            if financial_health.overall_score > 80:
                confidence_level += 10
            elif financial_health.overall_score < 30:
                confidence_level -= 10
                
            confidence_level = max(20, min(95, confidence_level))
            
            # 目标价计算（简化版）
            current_price = hist.iloc[-1]["Close"]
            target_price = None
            
            if financial_metrics.pe_ratio and financial_metrics.pe_ratio > 0:
                if overall_score >= 70:
                    target_price = current_price * 1.15  # 15% 上涨空间
                elif overall_score <= 40:
                    target_price = current_price * 0.85  # 15% 下跌空间
                else:
                    target_price = current_price * 1.05  # 5% 上涨空间
            
            # 分析总结
            analysis_summary = []
            analysis_summary.append(f"技术分析显示{technical_decision}信号")
            analysis_summary.append(f"财务健康度评分{financial_health.overall_score:.1f}/100")
            analysis_summary.extend(financial_health.strengths[:2])
            analysis_summary.append(industry_comparison.comparison_summary)
            
            return ComprehensiveAnalysis(
                ticker=ticker.upper(),
                technical_decision=technical_decision,
                technical_reasons=technical_reasons,
                financial_metrics=financial_metrics,
                financial_health=financial_health,
                industry_comparison=industry_comparison,
                final_recommendation=final_recommendation,
                confidence_level=confidence_level,
                target_price=target_price,
                analysis_summary=analysis_summary
            )
            
        except Exception as e:
            print(f"Error in comprehensive analysis for {ticker}: {e}")
            return None

# 全局实例
fundamental_service = FundamentalAnalysisService()