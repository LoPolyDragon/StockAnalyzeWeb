"""
自动化投资组合API路由
处理投资组合自动化相关的API请求
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

from .schemas import (
    AutomatedPortfolioCreate, AutomatedPortfolioUpdate, AutomatedPortfolio,
    AIAnalysisRequest, AIAnalysisResponse, AutoTradingStatus
)
from .automated_trading_service import automated_trading_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/automated-portfolio", response_model=str)
async def create_automated_portfolio(request: AutomatedPortfolioCreate):
    """创建自动化投资组合"""
    try:
        portfolio_id = await automated_trading_service.create_automated_portfolio(request)
        return portfolio_id
    except Exception as e:
        logger.error(f"创建自动化投资组合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automated-portfolios", response_model=List[dict])
async def list_automated_portfolios():
    """获取所有自动化投资组合列表"""
    try:
        portfolios = await automated_trading_service.list_automated_portfolios()
        return portfolios
    except Exception as e:
        logger.error(f"获取投资组合列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automated-portfolio/{portfolio_id}", response_model=AutomatedPortfolio)
async def get_automated_portfolio(portfolio_id: str):
    """获取指定自动化投资组合详情"""
    try:
        portfolio = await automated_trading_service.get_automated_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取投资组合详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/automated-portfolio/{portfolio_id}", response_model=bool)
async def update_automated_portfolio(portfolio_id: str, request: AutomatedPortfolioUpdate):
    """更新自动化投资组合"""
    try:
        success = await automated_trading_service.update_automated_portfolio(portfolio_id, request)
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新投资组合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automated-portfolio/{portfolio_id}", response_model=bool)
async def delete_automated_portfolio(portfolio_id: str):
    """删除自动化投资组合"""
    try:
        success = await automated_trading_service.delete_portfolio(portfolio_id)
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在或有待处理订单")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除投资组合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/ai-analysis", response_model=AIAnalysisResponse)
async def run_ai_analysis(portfolio_id: str, force_refresh: bool = False):
    """运行AI分析"""
    try:
        analysis = await automated_trading_service.run_ai_analysis(portfolio_id, force_refresh)
        if not analysis:
            raise HTTPException(status_code=400, detail="AI分析失败或投资组合不存在")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/execute-recommendations", response_model=List[str])
async def execute_ai_recommendations(portfolio_id: str, background_tasks: BackgroundTasks):
    """执行AI推荐"""
    try:
        results = await automated_trading_service.execute_ai_recommendations(portfolio_id)
        
        # 在后台检查止损止盈
        background_tasks.add_task(
            automated_trading_service.check_stop_loss_take_profit, 
            portfolio_id
        )
        
        return results
    except Exception as e:
        logger.error(f"执行AI推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/rebalance", response_model=List[str])
async def rebalance_portfolio(portfolio_id: str):
    """重新平衡投资组合"""
    try:
        results = await automated_trading_service.rebalance_portfolio(portfolio_id)
        return results
    except Exception as e:
        logger.error(f"重新平衡失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automated-portfolio/{portfolio_id}/status", response_model=AutoTradingStatus)
async def get_auto_trading_status(portfolio_id: str):
    """获取自动交易状态"""
    try:
        status = await automated_trading_service.get_auto_trading_status(portfolio_id)
        if not status:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取自动交易状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/toggle-mode")
async def toggle_portfolio_mode(portfolio_id: str, new_mode: str):
    """切换投资组合模式"""
    try:
        if new_mode not in ["manual", "auto", "hybrid"]:
            raise HTTPException(status_code=400, detail="无效的投资模式")
        
        update_request = AutomatedPortfolioUpdate(mode=new_mode)
        success = await automated_trading_service.update_automated_portfolio(portfolio_id, update_request)
        
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        
        return {"success": True, "new_mode": new_mode}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换投资模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/start-auto-trading")
async def start_auto_trading(portfolio_id: str):
    """启动自动交易"""
    try:
        update_request = AutomatedPortfolioUpdate(is_active=True, mode="auto")
        success = await automated_trading_service.update_automated_portfolio(portfolio_id, update_request)
        
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        
        # 立即运行一次AI分析
        await automated_trading_service.run_ai_analysis(portfolio_id, force_refresh=True)
        
        return {"success": True, "message": "自动交易已启动"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动自动交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automated-portfolio/{portfolio_id}/stop-auto-trading")
async def stop_auto_trading(portfolio_id: str):
    """停止自动交易"""
    try:
        update_request = AutomatedPortfolioUpdate(is_active=False)
        success = await automated_trading_service.update_automated_portfolio(portfolio_id, update_request)
        
        if not success:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        
        return {"success": True, "message": "自动交易已停止"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止自动交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automated-portfolio/{portfolio_id}/recommendations")
async def get_ai_recommendations(portfolio_id: str):
    """获取AI推荐"""
    try:
        portfolio = await automated_trading_service.get_automated_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="投资组合不存在")
        
        recommendations = portfolio.ai_recommendations
        return {
            "portfolio_id": portfolio_id,
            "recommendations": recommendations,
            "last_analysis": portfolio.last_ai_analysis,
            "count": len(recommendations)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-automated-trading-cycle")
async def run_automated_trading_cycle(background_tasks: BackgroundTasks):
    """手动触发自动交易周期（用于测试）"""
    try:
        background_tasks.add_task(automated_trading_service.run_automated_trading_cycle)
        return {"success": True, "message": "自动交易周期已启动"}
    except Exception as e:
        logger.error(f"启动自动交易周期失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trading-providers")
async def get_trading_providers():
    """获取支持的交易API提供商列表"""
    providers = [
        {
            "id": "paper_trading",
            "name": "纸上交易 (模拟)",
            "description": "完全模拟的交易环境，适合测试和学习",
            "requires_api_key": False,
            "is_sandbox_available": True
        },
        {
            "id": "alpaca",
            "name": "Alpaca",
            "description": "美股佣金免费交易平台",
            "requires_api_key": True,
            "is_sandbox_available": True
        },
        {
            "id": "interactive_brokers",
            "name": "Interactive Brokers",
            "description": "全球化投资平台",
            "requires_api_key": True,
            "is_sandbox_available": True
        },
        {
            "id": "td_ameritrade",
            "name": "TD Ameritrade",
            "description": "美国知名券商",
            "requires_api_key": True,
            "is_sandbox_available": True
        },
        {
            "id": "schwab",
            "name": "Charles Schwab",
            "description": "大型投资管理公司",
            "requires_api_key": True,
            "is_sandbox_available": True
        }
    ]
    return providers


@router.get("/ai-strategies/templates")
async def get_ai_strategy_templates():
    """获取AI策略模板"""
    templates = [
        {
            "name": "保守价值投资",
            "description": "注重基本面分析，低风险低波动",
            "risk_tolerance": "conservative",
            "max_position_size": 10.0,
            "max_daily_trades": 2,
            "stop_loss_pct": 8.0,
            "take_profit_pct": 15.0,
            "rebalance_frequency": "weekly",
            "confidence_threshold": 0.8
        },
        {
            "name": "稳健成长策略",
            "description": "平衡风险与收益，适合长期投资",
            "risk_tolerance": "moderate",
            "max_position_size": 15.0,
            "max_daily_trades": 5,
            "stop_loss_pct": 10.0,
            "take_profit_pct": 20.0,
            "rebalance_frequency": "daily",
            "confidence_threshold": 0.7
        },
        {
            "name": "激进增长策略",
            "description": "追求高收益，承担较高风险",
            "risk_tolerance": "aggressive",
            "max_position_size": 20.0,
            "max_daily_trades": 10,
            "stop_loss_pct": 12.0,
            "take_profit_pct": 30.0,
            "rebalance_frequency": "daily",
            "confidence_threshold": 0.6
        }
    ]
    return templates