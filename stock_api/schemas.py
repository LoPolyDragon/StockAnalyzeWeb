from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class StockResponse(BaseModel):
    ticker: str
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    decision: str
    reasons: list[str]
    history: list[dict]  # 每日 {date, close} 列表


# 投资组合相关数据模型
class PortfolioHolding(BaseModel):
    ticker: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight: float  # 占投资组合比重

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    holdings: List[PortfolioHolding]
    created_at: datetime
    updated_at: datetime

class AddHoldingRequest(BaseModel):
    ticker: str
    shares: float
    cost_per_share: float

class PortfolioPerformance(BaseModel):
    portfolio_id: str
    daily_returns: List[Dict]  # [{date, value, return_pct}]
    cumulative_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    best_day: Dict  # {date, return_pct}
    worst_day: Dict  # {date, return_pct}


# 基本面分析相关数据模型
class FinancialMetrics(BaseModel):
    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    
    # 估值指标
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_revenue: Optional[float] = None
    ev_ebitda: Optional[float] = None
    
    # 盈利能力
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None  # 净资产收益率
    roa: Optional[float] = None  # 总资产收益率
    roic: Optional[float] = None  # 投入资本回报率
    
    # 财务健康度
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_assets: Optional[float] = None
    
    # 成长性
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    
    # 其他指标
    beta: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    avg_volume: Optional[float] = None

class FinancialHealth(BaseModel):
    ticker: str
    overall_score: float  # 0-100分
    profitability_score: float
    liquidity_score: float
    leverage_score: float
    efficiency_score: float
    growth_score: float
    
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

class IndustryComparison(BaseModel):
    ticker: str
    industry: str
    industry_avg_pe: Optional[float] = None
    industry_avg_pb: Optional[float] = None
    industry_avg_roe: Optional[float] = None
    industry_avg_debt_ratio: Optional[float] = None
    industry_avg_gross_margin: Optional[float] = None
    
    pe_percentile: Optional[float] = None  # 在行业中的百分位
    pb_percentile: Optional[float] = None
    roe_percentile: Optional[float] = None
    margin_percentile: Optional[float] = None
    
    comparison_summary: str

class ComprehensiveAnalysis(BaseModel):
    ticker: str
    technical_decision: str
    technical_reasons: List[str]
    financial_metrics: FinancialMetrics
    financial_health: FinancialHealth
    industry_comparison: IndustryComparison
    final_recommendation: str  # BUY/HOLD/SELL
    confidence_level: float  # 0-100%
    target_price: Optional[float] = None
    analysis_summary: List[str]


# 风险管理相关数据模型
class VaRAnalysis(BaseModel):
    ticker: str
    period_days: int
    confidence_level: float  # 95%, 99% etc
    
    # VaR计算结果
    historical_var: Optional[float] = None  # 历史模拟法VaR
    parametric_var: Optional[float] = None  # 参数法VaR
    current_price: float
    
    # 风险解释
    var_explanation: str
    risk_level: str  # LOW/MEDIUM/HIGH
    
    # 历史损失分布
    historical_returns: List[float]
    worst_day_loss: float
    worst_week_loss: float

class DrawdownAnalysis(BaseModel):
    ticker: str
    period: str
    
    # 最大回撤指标
    max_drawdown: float  # 最大回撤幅度 (%)
    max_drawdown_duration: int  # 最大回撤持续天数
    current_drawdown: float  # 当前回撤幅度
    
    # 回撤历史
    drawdown_periods: List[Dict]  # [{start_date, end_date, drawdown_pct, duration}]
    recovery_time_avg: float  # 平均恢复时间（天）
    
    # 风险评估
    drawdown_score: float  # 0-100分，越高越好
    risk_warning: Optional[str] = None

class VolatilityAnalysis(BaseModel):
    ticker: str
    
    # 波动率指标
    daily_volatility: float  # 日波动率 (%)
    weekly_volatility: float  # 周波动率 (%)
    monthly_volatility: float  # 月波动率 (%)
    annualized_volatility: float  # 年化波动率 (%)
    
    # 滚动波动率
    volatility_30d: float  # 30日滚动波动率
    volatility_90d: float  # 90日滚动波动率
    volatility_trend: str  # INCREASING/DECREASING/STABLE
    
    # 波动率分级
    volatility_rank: str  # LOW/MEDIUM/HIGH
    vs_market_beta: Optional[float] = None  # 相对市场Beta

class CorrelationAnalysis(BaseModel):
    base_ticker: str
    comparison_tickers: List[str]
    
    # 相关性矩阵
    correlation_matrix: Dict[str, Dict[str, float]]
    
    # 关键相关性
    highest_correlation: Dict  # {ticker, value}
    lowest_correlation: Dict   # {ticker, value}
    market_correlation: Optional[float] = None  # 与市场(SPY)相关性
    
    # 分散化评估
    diversification_score: float  # 0-100分
    diversification_advice: str

class PositionSizing(BaseModel):
    ticker: str
    current_price: float
    
    # 凯利公式计算
    win_rate: float  # 胜率
    avg_win: float   # 平均盈利
    avg_loss: float  # 平均亏损
    kelly_percentage: float  # 凯利建议仓位 (%)
    
    # 风险调整建议
    conservative_position: float  # 保守建议 (%)
    aggressive_position: float    # 激进建议 (%)
    recommended_position: float   # 推荐建议 (%)
    
    # 仓位管理策略
    stop_loss_price: float
    take_profit_price: float
    max_position_size: float  # 最大持仓金额
    
    # 风险提示
    risk_warnings: List[str]

class PortfolioRiskMetrics(BaseModel):
    portfolio_id: str
    
    # 整体风险指标
    portfolio_var_95: float     # 95%置信度VaR
    portfolio_var_99: float     # 99%置信度VaR
    expected_shortfall: float   # 期望损失
    
    # 波动率和回撤
    portfolio_volatility: float
    portfolio_max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # 分散化指标
    effective_num_stocks: float  # 有效股票数量
    concentration_risk: float    # 集中度风险 (%)
    sector_concentration: Dict[str, float]  # 行业集中度
    
    # 风险分解
    individual_var_contributions: Dict[str, float]  # 个股VaR贡献
    risk_budget: Dict[str, float]  # 风险预算分配
    
    # 压力测试
    stress_test_results: Dict[str, float]  # {scenario: loss_pct}
    
    # 风险评级
    overall_risk_score: float  # 0-100分
    risk_grade: str  # A/B/C/D/F
    recommendations: List[str]

class RiskManagementSummary(BaseModel):
    ticker_or_portfolio: str
    analysis_type: str  # "SINGLE_STOCK" or "PORTFOLIO"
    
    var_analysis: Optional[VaRAnalysis] = None
    drawdown_analysis: Optional[DrawdownAnalysis] = None
    volatility_analysis: Optional[VolatilityAnalysis] = None
    correlation_analysis: Optional[CorrelationAnalysis] = None
    position_sizing: Optional[PositionSizing] = None
    portfolio_risk: Optional[PortfolioRiskMetrics] = None
    
    # 综合风险评估
    overall_risk_level: str  # LOW/MEDIUM/HIGH/EXTREME
    risk_score: float        # 0-100分
    key_risks: List[str]
    risk_mitigation_suggestions: List[str]
