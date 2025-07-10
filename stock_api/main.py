from fastapi import FastAPI, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from .schemas import (
    StockResponse, PortfolioCreate, PortfolioResponse, AddHoldingRequest, PortfolioPerformance,
    FinancialMetrics, FinancialHealth, IndustryComparison, ComprehensiveAnalysis,
    VaRAnalysis, DrawdownAnalysis, VolatilityAnalysis, CorrelationAnalysis,
    PositionSizing, RiskManagementSummary
)
from .stock_service import get_stock_data
from .ai_agent import make_decision
from .news_service import get_ticker_news
from .market_service import get_market_summary, recommend_top3
from .portfolio_service import portfolio_service
from .fundamental_service import fundamental_service
from .risk_service import risk_service
from .futu_service import get_futu_quote_service, get_futu_trade_service
from .trading_strategy import get_trading_engine, TradingSignal, SignalType

from typing import List, Dict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入新闻服务
try:
    from .real_news_service import real_news_service
    HAS_NEWS_SERVICE = True
    logger.info("新闻服务加载成功")
except Exception as e:
    HAS_NEWS_SERVICE = False
    logger.error(f"新闻服务加载失败: {e}")

app = FastAPI(
    title="Stock AI Advisor API", 
    version="2.0.0",
    description="专业级股票投资AI助手 - 集成技术面分析、基本面分析、风险管理、投资组合管理",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 尝试导入认证路由
try:
    from .auth_routes import router as auth_router
    has_auth_router = True
    logger.info("成功加载认证路由")
except ImportError as e:
    has_auth_router = False
    logger.error(f"加载认证路由失败: {e}")
    auth_router = None

# 包含认证路由
if has_auth_router:
    app.include_router(auth_router)

# 配置静态文件和模板目录
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# 挂载静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 直接挂载auth.html作为静态文件
@app.get("/auth.html")
async def auth_html():
    return FileResponse(os.path.join(static_dir, "auth.html"))

# 测试登录页面
@app.get("/test_auth.html")
async def test_auth_html():
    return FileResponse(os.path.join(static_dir, "test_auth.html"))

# 错误处理装饰器
def handle_api_errors(func):
    """统一API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"服务暂时不可用: {str(e)}")
    return wrapper

# 首页 UI
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

# 登录注册页面
@app.get("/auth.html", response_class=HTMLResponse)
async def auth_page(request: Request):
    """登录注册页面"""
    try:
        return templates.TemplateResponse("auth.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering auth.html: {e}")
        return HTMLResponse(content=f"<h1>Error loading auth page: {str(e)}</h1>", status_code=500)

# ==================== 股票基础API ====================

@app.get("/stock/{ticker}", response_model=StockResponse)
def get_stock(ticker: str, period: str = Query("1d", description="K线区间")):
    """
    查询单只股票并给出决策
    
    - **ticker**: 股票代码 (如 AAPL, 00700.HK)
    - **period**: 时间周期 (1d, 1wk, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    """
    try:
        hist = get_stock_data(ticker, period=period)
    except Exception as e:
        logger.error(f"Failed to fetch stock data for {ticker}: {e}")
        raise HTTPException(status_code=400, detail=f"无法获取股票数据: {e}")

    if hist.empty:
        raise HTTPException(status_code=404, detail=f"未找到股票代码 {ticker} 的数据")

    try:
        last_row = hist.iloc[-1]
        decision, reasons = make_decision(hist)

        # 获取股票名称
        company_name = ""
        try:
            import yfinance as yf
            ticker_info = yf.Ticker(ticker)
            info = ticker_info.info
            if info and 'longName' in info:
                company_name = info['longName']
            elif info and 'shortName' in info:
                company_name = info['shortName']
        except Exception as e:
            logger.warning(f"无法获取 {ticker} 的公司名称: {e}")
            
            # 常见股票名称映射
            stock_names = {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "AMZN": "Amazon.com, Inc.",
                "GOOGL": "Alphabet Inc.",
                "GOOG": "Alphabet Inc.",
                "META": "Meta Platforms, Inc.",
                "TSLA": "Tesla, Inc.",
                "NVDA": "NVIDIA Corporation",
                "NFLX": "Netflix, Inc.",
                "BABA": "Alibaba Group Holding Limited",
                "9988.HK": "阿里巴巴集团控股有限公司",
                "0700.HK": "腾讯控股有限公司",
                "9999.HK": "网易公司",
                "1810.HK": "小米集团",
                "1815.HK": "小鹏汽车",
                "9618.HK": "京东集团",
                "3690.HK": "美团",
                "9888.HK": "百度集团",
            }
            company_name = stock_names.get(ticker.upper(), "")

        # 最近 90 天完整OHLC数据用于前端绘图
        hist_tail = hist.tail(90)
        date_col = hist_tail.columns[0]  # first column after reset_index
        history_data = [
            {
                "date": str(row[date_col])[:10], 
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            }
            for _, row in hist_tail.iterrows()
        ]

        return StockResponse(
            ticker=ticker.upper(),
            company_name=company_name,
            current_price=round(last_row["Close"], 2),
            open=round(last_row["Open"], 2),
            high=round(last_row["High"], 2),
            low=round(last_row["Low"], 2),
            volume=int(last_row["Volume"]),
            decision=decision,
            reasons=reasons,
            history=history_data,
        )
    except Exception as e:
        logger.error(f"Error processing stock data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"数据处理错误: {e}")

# 新闻 API
@app.get("/news/{ticker}")
def news(ticker: str) -> List[Dict]:
    """获取股票相关新闻（原版）"""
    try:
        return get_ticker_news(ticker)
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

# 增强新闻 API
@app.get("/news/enhanced/{ticker}")
def enhanced_news(ticker: str, limit: int = Query(10, description="新闻数量限制")) -> List[Dict]:
    """获取增强版股票新闻（多数据源）"""
    try:
        from .enhanced_news_service import get_stock_news
        return get_stock_news(ticker, limit)
    except Exception as e:
        logger.error(f"Error fetching enhanced news for {ticker}: {e}")
        # 如果增强版失败，回退到原版
        try:
            return get_ticker_news(ticker)
        except:
            return []

@app.get("/news/test")
def test_news():
    """测试新闻接口"""
    return [
        {
            'title': '测试新闻1',
            'summary': '这是一条测试新闻',
            'url': 'https://example.com',
            'source': '测试源',
            'published_at': '2025-07-09T10:00:00',
            'sentiment': '积极',
            'sentiment_score': 0.8,
            'tickers': ['AAPL']
        }
    ]

@app.get("/news/market")
def market_news(limit: int = Query(20, description="新闻数量限制")):
    """获取市场新闻"""
    if HAS_NEWS_SERVICE:
        try:
            news = real_news_service.get_market_news(limit)
            logger.info(f"成功获取市场新闻 {len(news)} 条")
            return news
        except Exception as e:
            logger.error(f"获取真实新闻失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    # 如果失败，返回备用数据
    return [
        {
            'title': '无法获取实时新闻',
            'summary': '新闻服务暂时不可用，请稍后重试',
            'url': 'https://finance.yahoo.com/news/markets/',
            'source': '系统提示',
            'published_at': '2025-07-09T15:30:00',
            'sentiment': '中性',
            'sentiment_score': 0.5,
            'tickers': []
        }
    ][:limit]

@app.get("/news/api-status")
def news_api_status() -> Dict:
    """获取新闻API使用状态"""
    try:
        from .enhanced_news_service import enhanced_news_service
        return enhanced_news_service.get_api_status()
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return {"error": "无法获取API状态"}

@app.get("/market")
def market():
    """获取市场概况"""
    try:
        return get_market_summary()
    except Exception as e:
        logger.error(f"Error fetching market summary: {e}")
        raise HTTPException(status_code=500, detail="无法获取市场数据")

@app.get("/recommend")
def recommend():
    """获取AI推荐股票"""
    try:
        return recommend_top3()
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []

# ==================== 投资组合管理API ====================

@app.post("/portfolio", response_model=Dict)
def create_portfolio(portfolio: PortfolioCreate):
    """创建新的投资组合"""
    try:
        portfolio_id = portfolio_service.create_portfolio(portfolio.name, portfolio.description)
        return {"portfolio_id": portfolio_id, "message": "投资组合创建成功"}
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"创建投资组合失败: {e}")

@app.get("/portfolios", response_model=List[Dict])
def list_portfolios():
    """获取所有投资组合列表"""
    try:
        return portfolio_service.list_portfolios()
    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        return []

@app.get("/portfolio/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: str):
    """获取投资组合详情"""
    try:
        portfolio = portfolio_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取投资组合失败: {e}")

@app.post("/portfolio/{portfolio_id}/holding")
def add_holding(portfolio_id: str, holding: AddHoldingRequest):
    """添加股票持仓"""
    try:
        success = portfolio_service.add_holding(
            portfolio_id, 
            holding.ticker, 
            holding.shares, 
            holding.cost_per_share
        )
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return {"message": "持仓添加成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding holding to portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"添加持仓失败: {e}")

@app.get("/portfolio/{portfolio_id}/performance", response_model=PortfolioPerformance)
def get_portfolio_performance(portfolio_id: str, period: str = Query("1y", description="时间周期")):
    """获取投资组合表现分析"""
    try:
        performance = portfolio_service.get_portfolio_performance(portfolio_id, period)
        if not performance:
            raise HTTPException(status_code=404, detail="无法计算投资组合表现")
        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio performance {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"计算投资组合表现失败: {e}")

@app.delete("/portfolio/{portfolio_id}")
def delete_portfolio(portfolio_id: str):
    """删除投资组合"""
    try:
        success = portfolio_service.delete_portfolio(portfolio_id)
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return {"message": "投资组合删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"删除投资组合失败: {e}")

@app.delete("/portfolio/{portfolio_id}/holding/{ticker}")
def remove_holding(portfolio_id: str, ticker: str):
    """移除股票持仓"""
    try:
        success = portfolio_service.remove_holding(portfolio_id, ticker)
        if not success:
            raise HTTPException(status_code=404, detail="投资组合或持仓不存在")
        return {"message": "持仓移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing holding {ticker} from portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"移除持仓失败: {e}")

@app.put("/portfolio/{portfolio_id}")
def update_portfolio(portfolio_id: str, portfolio: PortfolioCreate):
    """更新投资组合信息"""
    try:
        success = portfolio_service.update_portfolio(portfolio_id, portfolio.name, portfolio.description)
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return {"message": "投资组合更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"更新投资组合失败: {e}")

# ==================== 基本面分析API ====================

@app.get("/fundamental/{ticker}", response_model=FinancialMetrics)
def get_financial_metrics(ticker: str):
    """获取股票财务指标"""
    try:
        metrics = fundamental_service.get_financial_metrics(ticker)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"无法获取 {ticker} 的财务数据，可能是股票代码无效或数据源问题")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial metrics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取财务数据失败: {e}")

@app.get("/fundamental/{ticker}/health", response_model=FinancialHealth)
def get_financial_health(ticker: str):
    """获取财务健康度评分"""
    try:
        metrics = fundamental_service.get_financial_metrics(ticker)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"无法获取 {ticker} 的财务数据")
        health = fundamental_service.calculate_financial_health(metrics)
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating financial health for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算财务健康度失败: {e}")

@app.get("/fundamental/{ticker}/industry", response_model=IndustryComparison)
def get_industry_comparison(ticker: str):
    """获取行业对比分析"""
    try:
        metrics = fundamental_service.get_financial_metrics(ticker)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"无法获取 {ticker} 的财务数据")
        comparison = fundamental_service.get_industry_comparison(metrics)
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting industry comparison for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取行业对比失败: {e}")

@app.get("/analysis/{ticker}", response_model=ComprehensiveAnalysis)
def get_comprehensive_analysis(ticker: str):
    """获取综合分析：技术面 + 基本面"""
    try:
        analysis = fundamental_service.get_comprehensive_analysis(ticker)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"无法获取 {ticker} 的综合分析数据，请检查股票代码是否正确")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comprehensive analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取综合分析失败: {e}")

# ==================== 风险管理API ====================

@app.get("/risk/{ticker}/var", response_model=VaRAnalysis)
def get_var_analysis(ticker: str, confidence: float = Query(0.95, description="置信度")):
    """获取VaR（风险价值）分析"""
    try:
        if not 0.8 <= confidence <= 0.99:
            raise HTTPException(status_code=400, detail="置信度必须在0.8-0.99之间")
        
        var_analysis = risk_service.calculate_var(ticker, confidence)
        if not var_analysis:
            raise HTTPException(status_code=404, detail=f"无法计算 {ticker} 的VaR数据")
        return var_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating VaR for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算VaR失败: {e}")

@app.get("/risk/{ticker}/drawdown", response_model=DrawdownAnalysis)
def get_drawdown_analysis(ticker: str, period: str = Query("2y", description="分析周期")):
    """获取最大回撤分析"""
    try:
        drawdown_analysis = risk_service.calculate_drawdown(ticker, period)
        if not drawdown_analysis:
            raise HTTPException(status_code=404, detail=f"无法计算 {ticker} 的回撤数据")
        return drawdown_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating drawdown for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算回撤分析失败: {e}")

@app.get("/risk/{ticker}/volatility", response_model=VolatilityAnalysis)
def get_volatility_analysis(ticker: str):
    """获取波动率分析"""
    try:
        volatility_analysis = risk_service.calculate_volatility(ticker)
        if not volatility_analysis:
            raise HTTPException(status_code=404, detail=f"无法计算 {ticker} 的波动率数据")
        return volatility_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating volatility for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算波动率失败: {e}")

@app.get("/risk/{ticker}/correlation", response_model=CorrelationAnalysis)
def get_correlation_analysis(ticker: str, compare_with: str = Query(..., description="对比股票代码，多个用逗号分隔")):
    """获取相关性分析"""
    try:
        comparison_tickers = [t.strip().upper() for t in compare_with.split(",") if t.strip()]
        if not comparison_tickers:
            raise HTTPException(status_code=400, detail="请提供有效的对比股票代码")
        
        correlation_analysis = risk_service.calculate_correlation(ticker, comparison_tickers)
        if not correlation_analysis:
            raise HTTPException(status_code=404, detail=f"无法计算 {ticker} 的相关性数据")
        return correlation_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating correlation for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算相关性失败: {e}")

@app.get("/risk/{ticker}/position", response_model=PositionSizing)
def get_position_sizing(ticker: str, investment_amount: float = Query(10000, description="投资金额")):
    """获取仓位管理建议"""
    try:
        if investment_amount <= 0:
            raise HTTPException(status_code=400, detail="投资金额必须大于0")
        
        position_sizing = risk_service.calculate_position_sizing(ticker, investment_amount)
        if not position_sizing:
            raise HTTPException(status_code=404, detail=f"无法计算 {ticker} 的仓位建议")
        return position_sizing
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating position sizing for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"计算仓位建议失败: {e}")

@app.get("/risk/{ticker}/comprehensive", response_model=RiskManagementSummary)
def get_comprehensive_risk_analysis(ticker: str):
    """获取综合风险分析"""
    try:
        risk_analysis = risk_service.get_comprehensive_risk_analysis(ticker)
        if not risk_analysis:
            raise HTTPException(status_code=404, detail=f"无法获取 {ticker} 的风险分析数据，请检查股票代码是否正确")
        return risk_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comprehensive risk analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"获取风险分析失败: {e}")

# ==================== 富途API接口 ====================

@app.get("/futu/status")
def futu_connection_status():
    """检查富途API连接状态"""
    try:
        futu_service = get_futu_quote_service()
        is_connected = futu_service.is_connected()
        if not is_connected:
            # 尝试连接
            is_connected = futu_service.connect()
        
        return {
            "connected": is_connected,
            "service": "富途OpenAPI",
            "status": "已连接" if is_connected else "未连接"
        }
    except Exception as e:
        logger.error(f"检查富途连接状态失败: {e}")
        return {
            "connected": False,
            "service": "富途OpenAPI",
            "status": "连接失败",
            "error": str(e)
        }

@app.get("/futu/snapshot/{code}")
def get_futu_snapshot(code: str):
    """获取富途实时行情快照"""
    try:
        futu_service = get_futu_quote_service()
        
        # 转换股票代码格式
        futu_code = futu_service.convert_stock_code(code)
        result = futu_service.get_market_snapshot([futu_code])
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取富途快照数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时数据失败: {e}")

@app.get("/futu/kline/{code}")
def get_futu_kline(code: str, days: int = Query(30, description="获取天数")):
    """获取富途K线数据"""
    try:
        futu_service = get_futu_quote_service()
        
        # 转换股票代码格式
        futu_code = futu_service.convert_stock_code(code)
        result = futu_service.get_cur_kline(futu_code, num=days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取富途K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {e}")

@app.get("/futu/search/{keyword}")
def search_futu_stocks(keyword: str):
    """搜索股票"""
    try:
        futu_service = get_futu_quote_service()
        result = futu_service.search_stock(keyword)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")

@app.get("/futu/plates")
def get_futu_plate_list():
    """获取板块列表"""
    try:
        futu_service = get_futu_quote_service()
        result = futu_service.get_plate_list()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块数据失败: {e}")

# ==================== 富途交易API ====================

@app.get("/futu/trade/accounts")
def get_futu_accounts():
    """获取富途交易账户列表"""
    try:
        trade_service = get_futu_trade_service()
        if not trade_service.connect_trade():
            raise HTTPException(status_code=503, detail="无法连接富途交易服务")
        
        result = trade_service.get_acc_list()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {e}")

@app.get("/futu/trade/positions/{acc_id}")
def get_futu_positions(acc_id: int):
    """获取持仓信息"""
    try:
        trade_service = get_futu_trade_service()
        result = trade_service.get_positions(acc_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {e}")

# ==================== 自动化交易API ====================

@app.get("/trading/status")
def get_trading_status():
    """获取自动交易引擎状态"""
    try:
        engine = get_trading_engine()
        return {
            "active": engine.active,
            "dry_run": engine.dry_run,
            "strategies": [strategy.name for strategy in engine.strategies],
            "risk_management": {
                "max_position_size": engine.risk_manager.max_position_size,
                "max_total_risk": engine.risk_manager.max_total_risk,
                "stop_loss_pct": engine.risk_manager.stop_loss_pct,
                "take_profit_pct": engine.risk_manager.take_profit_pct
            }
        }
    except Exception as e:
        logger.error(f"获取交易状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {e}")

@app.post("/trading/start")
def start_trading():
    """启动自动交易"""
    try:
        engine = get_trading_engine()
        engine.start()
        return {"message": "自动交易引擎已启动", "status": "active"}
    except Exception as e:
        logger.error(f"启动交易失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动失败: {e}")

@app.post("/trading/stop")
def stop_trading():
    """停止自动交易"""
    try:
        engine = get_trading_engine()
        engine.stop()
        return {"message": "自动交易引擎已停止", "status": "inactive"}
    except Exception as e:
        logger.error(f"停止交易失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止失败: {e}")

@app.post("/trading/scan")
def scan_trading_opportunities(watchlist: List[str]):
    """扫描交易机会"""
    try:
        engine = get_trading_engine()
        signals = engine.scan_opportunities(watchlist)
        
        return {
            "timestamp": "now",
            "watchlist": watchlist,
            "signals_found": len(signals),
            "signals": [
                {
                    "symbol": signal.symbol,
                    "signal_type": signal.signal_type.value,
                    "confidence": signal.confidence,
                    "price": signal.price,
                    "risk_score": signal.risk_score,
                    "position_size": signal.position_size,
                    "reasons": signal.reasons,
                    "strategy": signal.strategy.value
                }
                for signal in signals
            ]
        }
    except Exception as e:
        logger.error(f"扫描交易机会失败: {e}")
        raise HTTPException(status_code=500, detail=f"扫描失败: {e}")

@app.post("/trading/execute/{account_id}")
def execute_trading_cycle(account_id: int, watchlist: List[str]):
    """执行一次完整的交易周期"""
    try:
        engine = get_trading_engine()
        result = engine.run_cycle(watchlist, account_id)
        return result
    except Exception as e:
        logger.error(f"执行交易周期失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {e}")

@app.get("/trading/strategies")
def get_available_strategies():
    """获取可用的交易策略"""
    return {
        "strategies": [
            {
                "name": "AI决策策略",
                "type": "ai_decision",
                "description": "基于技术指标AI分析的决策策略，结合多项技术指标综合判断"
            },
            {
                "name": "动量策略", 
                "type": "momentum",
                "description": "基于价格动量的趋势跟随策略，捕捉强势股票"
            },
            {
                "name": "均值回归策略",
                "type": "mean_reversion", 
                "description": "基于统计学的均值回归策略，寻找偏离均值的机会"
            },
            {
                "name": "突破策略",
                "type": "breakout",
                "description": "基于价格突破关键阻力/支撑位的策略"
            }
        ]
    }

# ==================== 健康检查API ====================

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "features": [
            "技术分析", "基本面分析", "风险管理", 
            "投资组合管理", "市场数据", "新闻资讯", "富途API集成"
        ],
        "news_test": [
            {
                "title": "测试新闻",
                "summary": "这是在健康检查中的测试新闻",
                "source": "测试"
            }
        ]
    }

@app.get("/debug/working")
def debug_working():
    """调试用的工作接口"""
    return {
        "message": "这个接口正常工作",
        "data": [
            {
                "title": "测试标题",
                "content": "测试内容"
            }
        ]
    }

@app.get("/market-updates")
def market_updates():
    """市场动态（避开news路径）"""
    if HAS_NEWS_SERVICE:
        try:
            news = real_news_service.get_market_news(10)
            logger.info(f"成功获取市场动态 {len(news)} 条")
            return news
        except Exception as e:
            logger.error(f"获取市场动态失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    return [
        {
            'title': '无法获取实时市场动态',
            'summary': '新闻服务暂时不可用，请稍后重试',
            'url': 'https://finance.yahoo.com/news/markets/',
            'source': '系统提示',
            'published_at': '2025-07-09T15:30:00',
            'sentiment': '中性',
            'sentiment_score': 0.5,
            'tickers': []
        }
    ]

@app.get("/stock-updates/{ticker}")
def stock_updates(ticker: str):
    """股票相关动态（避开news路径）"""
    try:
        from .real_news_service import real_news_service
        return real_news_service.get_stock_news(ticker, 10)
    except Exception as e:
        logger.error(f"获取{ticker}新闻失败: {e}")
        # 如果失败，返回备用数据
        return [
            {
                'title': f'{ticker} 股票动态',
                'summary': f'无法获取{ticker}的实时新闻，请稍后重试',
                'url': f'https://finance.yahoo.com/quote/{ticker}/news',
                'source': '系统提示',
                'published_at': '2025-07-09T14:00:00',
                'sentiment': '中性',
                'sentiment_score': 0.5,
                'tickers': [ticker]
            }
        ]

# ==================== 股票筛选器API ====================

@app.post("/stock-screener")
def screen_stocks_api(filters: Dict):
    """股票筛选API"""
    try:
        from .stock_screener_service import screen_stocks
        logger.info(f"股票筛选请求: {filters}")
        
        # 处理筛选条件
        screening_filters = {}
        
        if filters.get('marketCap'):
            screening_filters['market_cap'] = filters['marketCap']
        
        if filters.get('pe'):
            screening_filters['pe_ratio'] = filters['pe']
        
        if filters.get('priceChange'):
            screening_filters['price_change'] = filters['priceChange']
        
        if filters.get('volume'):
            screening_filters['volume'] = filters['volume']
        
        if filters.get('sector'):
            screening_filters['sector'] = filters['sector']
        
        if filters.get('sortBy'):
            screening_filters['sort_by'] = filters['sortBy']
        
        # 执行筛选
        results = screen_stocks(screening_filters)
        
        logger.info(f"筛选完成，找到{len(results)}只股票")
        return {
            'success': True,
            'count': len(results),
            'data': results
        }
        
    except Exception as e:
        logger.error(f"股票筛选失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

@app.get("/stock-screener/top")
def get_top_stocks_api(sort_by: str = Query('marketCap', description="排序方式"), limit: int = Query(10, description="数量限制")):
    """获取热门股票"""
    try:
        from .stock_screener_service import get_top_stocks
        
        results = get_top_stocks(sort_by, limit)
        return {
            'success': True,
            'count': len(results),
            'data': results
        }
        
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

@app.get("/stock-screener/sectors")
def get_sectors_summary_api():
    """获取行业概况"""
    try:
        from .stock_screener_service import get_sectors_summary
        
        sectors = get_sectors_summary()
        return {
            'success': True,
            'data': sectors
        }
        
    except Exception as e:
        logger.error(f"获取行业概况失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

@app.get("/stock-screener/stock/{symbol}")
def get_stock_info_api(symbol: str):
    """获取单个股票信息"""
    try:
        from .stock_screener_service import get_stock_info
        
        stock = get_stock_info(symbol.upper())
        if stock:
            return {
                'success': True,
                'data': stock
            }
        else:
            return {
                'success': False,
                'error': '未找到该股票',
                'data': {}
            }
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

# ==================== 市场仪表板API ====================

@app.get("/market-dashboard")
def get_market_dashboard():
    """获取市场仪表板综合数据"""
    try:
        from .market_dashboard_service import get_market_dashboard_data
        
        data = get_market_dashboard_data()
        if 'error' in data:
            return {
                'success': False,
                'error': data['error'],
                'data': {}
            }
        
        return {
            'success': True,
            'data': data
        }
        
    except Exception as e:
        logger.error(f"获取市场仪表板数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

@app.get("/market-indices")
def get_market_indices():
    """获取市场指数数据"""
    try:
        from .market_dashboard_service import get_market_indices_data
        
        indices = get_market_indices_data()
        if 'error' in indices:
            return {
                'success': False,
                'error': indices['error'],
                'data': {}
            }
        
        return {
            'success': True,
            'data': indices
        }
        
    except Exception as e:
        logger.error(f"获取市场指数数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

@app.get("/sector-heatmap")
def get_sector_heatmap():
    """获取行业热力图数据"""
    try:
        from .market_dashboard_service import get_sector_heatmap_data
        
        heatmap = get_sector_heatmap_data()
        
        return {
            'success': True,
            'data': heatmap
        }
        
    except Exception as e:
        logger.error(f"获取行业热力图数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

@app.get("/market-movers")
def get_market_movers():
    """获取市场热门股票（涨跌榜、成交量排行）"""
    try:
        from .market_dashboard_service import dashboard_service
        
        data = {
            'top_gainers': dashboard_service.get_top_gainers(),
            'top_losers': dashboard_service.get_top_losers(),
            'volume_leaders': dashboard_service.get_volume_leaders()
        }
        
        return {
            'success': True,
            'data': data
        }
        
    except Exception as e:
        logger.error(f"获取市场热门股票数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

@app.get("/market-sentiment")
def get_market_sentiment():
    """获取市场情绪指标"""
    try:
        from .market_dashboard_service import dashboard_service
        
        sentiment = dashboard_service.get_market_sentiment()
        
        return {
            'success': True,
            'data': sentiment
        }
        
    except Exception as e:
        logger.error(f"获取市场情绪数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }

if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口，默认为8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)