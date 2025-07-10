"""
自动交易执行逻辑
处理AI推荐的自动买卖决策
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import logging
from decimal import Decimal, ROUND_DOWN

from .schemas import (
    AutomatedPortfolio, AutomatedPortfolioCreate, AutomatedPortfolioUpdate,
    TradingOrder, AIStockRecommendation, AIAnalysisRequest, AIAnalysisResponse,
    AutoTradingStatus, PortfolioPerformanceMetrics, TradingApiConfig, AITradingStrategy
)
from .trading_interface import TradingManager, TradingAPIError, InsufficientFundsError
from .ai_stock_analyzer import ai_stock_analyzer

logger = logging.getLogger(__name__)


class AutomatedTradingService:
    """自动交易服务"""
    
    def __init__(self):
        self.data_file = "automated_portfolios.json"
        self.portfolios = self._load_portfolios()
        self.trading_manager = TradingManager()
        self.order_history = []
        self.performance_history = []
    
    def _load_portfolios(self) -> Dict:
        """加载自动化投资组合数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载投资组合数据失败: {e}")
                return {}
        return {}
    
    def _save_portfolios(self):
        """保存投资组合数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolios, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存投资组合数据失败: {e}")
    
    async def create_automated_portfolio(self, request: AutomatedPortfolioCreate) -> str:
        """创建自动化投资组合"""
        portfolio_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        portfolio_data = {
            "id": portfolio_id,
            "name": request.name,
            "description": request.description or "",
            "mode": request.mode,
            "is_active": True,
            "total_budget": request.total_budget,
            "available_cash": request.total_budget,
            "reserved_cash": 0,
            "max_single_position": request.max_single_position,
            "trading_api": request.trading_api.dict() if request.trading_api else None,
            "ai_strategy": request.ai_strategy.dict() if request.ai_strategy else None,
            "holdings": [],
            "ai_recommendations": [],
            "pending_orders": [],
            "order_history": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_ai_analysis": None,
            "last_trade_execution": None
        }
        
        self.portfolios[portfolio_id] = portfolio_data
        self._save_portfolios()
        
        logger.info(f"创建自动化投资组合: {request.name} (ID: {portfolio_id})")
        return portfolio_id
    
    async def update_automated_portfolio(self, portfolio_id: str, request: AutomatedPortfolioUpdate) -> bool:
        """更新自动化投资组合"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        
        # 更新字段
        if request.name is not None:
            portfolio["name"] = request.name
        if request.description is not None:
            portfolio["description"] = request.description
        if request.mode is not None:
            portfolio["mode"] = request.mode
        if request.total_budget is not None:
            # 调整可用现金
            budget_change = request.total_budget - portfolio["total_budget"]
            portfolio["total_budget"] = request.total_budget
            portfolio["available_cash"] += budget_change
        if request.max_single_position is not None:
            portfolio["max_single_position"] = request.max_single_position
        if request.is_active is not None:
            portfolio["is_active"] = request.is_active
        if request.trading_api is not None:
            portfolio["trading_api"] = request.trading_api.dict()
        if request.ai_strategy is not None:
            portfolio["ai_strategy"] = request.ai_strategy.dict()
        
        portfolio["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_portfolios()
        
        logger.info(f"更新投资组合: {portfolio_id}")
        return True
    
    async def get_automated_portfolio(self, portfolio_id: str) -> Optional[AutomatedPortfolio]:
        """获取自动化投资组合"""
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio_data = self.portfolios[portfolio_id]
        
        # 如果配置了交易API，同步持仓
        if portfolio_data.get("trading_api") and portfolio_data.get("mode") != "manual":
            await self._sync_portfolio_positions(portfolio_id)
        
        return AutomatedPortfolio(**portfolio_data)
    
    async def list_automated_portfolios(self) -> List[Dict]:
        """列出所有自动化投资组合"""
        portfolio_list = []
        for portfolio_id, portfolio_data in self.portfolios.items():
            # 计算基本统计信息
            total_value = portfolio_data["available_cash"]
            for holding in portfolio_data.get("holdings", []):
                total_value += holding.get("market_value", 0)
            
            total_pnl = total_value - portfolio_data["total_budget"]
            total_pnl_pct = (total_pnl / portfolio_data["total_budget"] * 100) if portfolio_data["total_budget"] > 0 else 0
            
            portfolio_list.append({
                "id": portfolio_id,
                "name": portfolio_data["name"],
                "description": portfolio_data["description"],
                "mode": portfolio_data["mode"],
                "is_active": portfolio_data["is_active"],
                "total_value": total_value,
                "total_pnl_pct": total_pnl_pct,
                "holdings_count": len(portfolio_data.get("holdings", [])),
                "updated_at": portfolio_data["updated_at"]
            })
        
        return portfolio_list
    
    async def run_ai_analysis(self, portfolio_id: str, force_refresh: bool = False) -> Optional[AIAnalysisResponse]:
        """运行AI分析"""
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_id]
        
        # 检查是否需要分析
        if not force_refresh and portfolio.get("last_ai_analysis"):
            last_analysis = datetime.fromisoformat(portfolio["last_ai_analysis"])
            if datetime.now(timezone.utc) - last_analysis < timedelta(hours=6):
                logger.info(f"投资组合 {portfolio_id} 最近已进行AI分析，跳过")
                return None
        
        # 获取AI策略
        ai_strategy_data = portfolio.get("ai_strategy")
        if not ai_strategy_data:
            logger.warning(f"投资组合 {portfolio_id} 未配置AI策略")
            return None
        
        ai_strategy = AITradingStrategy(**ai_strategy_data)
        
        # 创建分析请求
        analysis_request = AIAnalysisRequest(
            portfolio_id=portfolio_id,
            max_recommendations=10,
            force_refresh=force_refresh,
            exclude_current_holdings=False
        )
        
        # 执行AI分析
        try:
            analysis_response = await ai_stock_analyzer.generate_analysis_response(
                analysis_request, ai_strategy
            )
            
            # 更新投资组合的AI推荐
            portfolio["ai_recommendations"] = [rec.dict() for rec in analysis_response.recommendations]
            portfolio["last_ai_analysis"] = datetime.now(timezone.utc).isoformat()
            self._save_portfolios()
            
            logger.info(f"完成投资组合 {portfolio_id} 的AI分析，获得 {len(analysis_response.recommendations)} 个推荐")
            return analysis_response
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return None
    
    async def execute_ai_recommendations(self, portfolio_id: str) -> List[str]:
        """执行AI推荐"""
        if portfolio_id not in self.portfolios:
            return ["投资组合不存在"]
        
        portfolio = self.portfolios[portfolio_id]
        
        # 检查是否为自动模式
        if portfolio["mode"] == "manual":
            return ["投资组合处于手动模式，无法执行自动交易"]
        
        if not portfolio["is_active"]:
            return ["投资组合未激活"]
        
        # 检查交易API配置
        if not portfolio.get("trading_api"):
            return ["未配置交易API"]
        
        # 获取AI推荐
        recommendations = portfolio.get("ai_recommendations", [])
        if not recommendations:
            return ["无AI推荐数据，请先运行AI分析"]
        
        executed_orders = []
        errors = []
        
        # 获取策略配置
        ai_strategy_data = portfolio.get("ai_strategy", {})
        ai_strategy = AITradingStrategy(**ai_strategy_data)
        
        # 检查每日交易限制
        today_trades = self._count_today_trades(portfolio_id)
        if today_trades >= ai_strategy.max_daily_trades:
            return [f"已达到每日交易限制 ({ai_strategy.max_daily_trades})"]
        
        try:
            # 获取交易API
            trading_config = TradingApiConfig(**portfolio["trading_api"])
            api = await self.trading_manager.get_api(trading_config)
            
            # 获取账户信息
            account_info = await api.get_account_info()
            available_cash = float(account_info.get("cash", portfolio["available_cash"]))
            
            # 处理BUY推荐
            buy_recommendations = [
                AIStockRecommendation(**rec) for rec in recommendations 
                if rec["recommendation"] == "BUY" and rec["confidence_score"] >= ai_strategy.confidence_threshold
            ]
            
            for recommendation in buy_recommendations[:ai_strategy.max_daily_trades - today_trades]:
                try:
                    # 计算投资金额
                    investment_amount = min(
                        recommendation.suggested_position_size,
                        portfolio["max_single_position"],
                        available_cash * 0.2  # 单次投资不超过可用资金的20%
                    )
                    
                    if investment_amount < 100:  # 最小投资金额
                        continue
                    
                    # 获取当前价格
                    market_data = await api.get_market_data(recommendation.ticker)
                    current_price = market_data["price"]
                    
                    # 计算购买数量
                    quantity = int(investment_amount / current_price)
                    if quantity == 0:
                        continue
                    
                    # 创建订单
                    order = TradingOrder(
                        id=str(uuid.uuid4()),
                        portfolio_id=portfolio_id,
                        order_type="market",
                        side="buy",
                        ticker=recommendation.ticker,
                        quantity=quantity,
                        price=current_price,
                        status="pending",
                        execution_source="ai_auto",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    
                    # 提交订单
                    broker_order_id = await api.submit_order(order)
                    order.broker_order_id = broker_order_id
                    
                    # 更新订单状态
                    order_status = await api.get_order_status(broker_order_id)
                    order.status = order_status["status"]
                    order.filled_quantity = order_status.get("filled_qty", 0)
                    order.filled_price = order_status.get("filled_price")
                    
                    # 保存订单
                    portfolio["pending_orders"].append(order.dict())
                    portfolio["order_history"].append(order.dict())
                    
                    # 更新可用资金
                    if order.status == "filled":
                        cost = order.filled_quantity * order.filled_price
                        available_cash -= cost
                        portfolio["available_cash"] = available_cash
                    
                    executed_orders.append(f"买入 {recommendation.ticker} {quantity}股")
                    logger.info(f"执行买入订单: {recommendation.ticker}, 数量: {quantity}")
                    
                except InsufficientFundsError as e:
                    errors.append(f"资金不足，无法买入 {recommendation.ticker}")
                    logger.warning(f"资金不足: {e}")
                    break
                except Exception as e:
                    errors.append(f"买入 {recommendation.ticker} 失败: {str(e)}")
                    logger.error(f"执行买入订单失败: {e}")
            
            # 更新投资组合
            portfolio["last_trade_execution"] = datetime.now(timezone.utc).isoformat()
            self._save_portfolios()
            
            result = executed_orders + errors
            return result if result else ["无符合条件的交易"]
            
        except Exception as e:
            logger.error(f"执行AI推荐失败: {e}")
            return [f"执行失败: {str(e)}"]
    
    async def check_stop_loss_take_profit(self, portfolio_id: str) -> List[str]:
        """检查止损止盈"""
        if portfolio_id not in self.portfolios:
            return ["投资组合不存在"]
        
        portfolio = self.portfolios[portfolio_id]
        
        if portfolio["mode"] == "manual":
            return []
        
        # 获取策略配置
        ai_strategy_data = portfolio.get("ai_strategy")
        if not ai_strategy_data:
            return []
        
        ai_strategy = AITradingStrategy(**ai_strategy_data)
        executed_actions = []
        
        try:
            # 获取交易API
            trading_config = TradingApiConfig(**portfolio["trading_api"])
            api = await self.trading_manager.get_api(trading_config)
            
            # 获取当前持仓
            positions = await api.get_positions()
            
            for position in positions:
                # 计算盈亏百分比
                pnl_pct = position.unrealized_pnl_pct
                
                # 检查止损
                if pnl_pct <= -ai_strategy.stop_loss_pct:
                    try:
                        # 创建卖出订单
                        order = TradingOrder(
                            id=str(uuid.uuid4()),
                            portfolio_id=portfolio_id,
                            order_type="market",
                            side="sell",
                            ticker=position.ticker,
                            quantity=position.shares,
                            status="pending",
                            execution_source="stop_loss",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        
                        broker_order_id = await api.submit_order(order)
                        order.broker_order_id = broker_order_id
                        
                        executed_actions.append(f"止损卖出 {position.ticker}")
                        logger.info(f"执行止损: {position.ticker}, 亏损: {pnl_pct:.2f}%")
                        
                    except Exception as e:
                        logger.error(f"执行止损失败: {e}")
                
                # 检查止盈
                elif pnl_pct >= ai_strategy.take_profit_pct:
                    try:
                        # 创建卖出订单
                        order = TradingOrder(
                            id=str(uuid.uuid4()),
                            portfolio_id=portfolio_id,
                            order_type="market",
                            side="sell",
                            ticker=position.ticker,
                            quantity=position.shares,
                            status="pending",
                            execution_source="take_profit",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        
                        broker_order_id = await api.submit_order(order)
                        order.broker_order_id = broker_order_id
                        
                        executed_actions.append(f"止盈卖出 {position.ticker}")
                        logger.info(f"执行止盈: {position.ticker}, 盈利: {pnl_pct:.2f}%")
                        
                    except Exception as e:
                        logger.error(f"执行止盈失败: {e}")
        
        except Exception as e:
            logger.error(f"检查止损止盈失败: {e}")
            return [f"检查失败: {str(e)}"]
        
        return executed_actions
    
    async def rebalance_portfolio(self, portfolio_id: str) -> List[str]:
        """重新平衡投资组合"""
        if portfolio_id not in self.portfolios:
            return ["投资组合不存在"]
        
        portfolio = self.portfolios[portfolio_id]
        
        if portfolio["mode"] == "manual":
            return ["手动模式无法自动重新平衡"]
        
        # 获取AI策略
        ai_strategy_data = portfolio.get("ai_strategy")
        if not ai_strategy_data:
            return ["未配置AI策略"]
        
        ai_strategy = AITradingStrategy(**ai_strategy_data)
        
        # 检查重新平衡频率
        last_rebalance = portfolio.get("last_rebalance")
        if last_rebalance:
            last_rebalance_date = datetime.fromisoformat(last_rebalance)
            time_since_last = datetime.now(timezone.utc) - last_rebalance_date
            
            required_interval = {
                "daily": timedelta(days=1),
                "weekly": timedelta(days=7),
                "monthly": timedelta(days=30)
            }.get(ai_strategy.rebalance_frequency, timedelta(days=7))
            
            if time_since_last < required_interval:
                return ["距离上次重新平衡时间太短"]
        
        try:
            # 运行AI分析
            await self.run_ai_analysis(portfolio_id, force_refresh=True)
            
            # 执行推荐
            execution_results = await self.execute_ai_recommendations(portfolio_id)
            
            # 更新重新平衡时间
            portfolio["last_rebalance"] = datetime.now(timezone.utc).isoformat()
            self._save_portfolios()
            
            logger.info(f"完成投资组合 {portfolio_id} 重新平衡")
            return execution_results
            
        except Exception as e:
            logger.error(f"重新平衡失败: {e}")
            return [f"重新平衡失败: {str(e)}"]
    
    async def get_auto_trading_status(self, portfolio_id: str) -> Optional[AutoTradingStatus]:
        """获取自动交易状态"""
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_id]
        
        # 计算今日交易次数
        today_trades = self._count_today_trades(portfolio_id)
        
        # 获取策略限制
        ai_strategy_data = portfolio.get("ai_strategy", {})
        daily_limit = ai_strategy_data.get("max_daily_trades", 5)
        
        # 检查错误信息
        error_messages = []
        if not portfolio.get("trading_api"):
            error_messages.append("未配置交易API")
        if not portfolio.get("ai_strategy"):
            error_messages.append("未配置AI策略")
        if portfolio["available_cash"] < 100:
            error_messages.append("可用资金不足")
        
        return AutoTradingStatus(
            portfolio_id=portfolio_id,
            is_enabled=portfolio["mode"] in ["auto", "hybrid"] and portfolio["is_active"],
            last_execution=datetime.fromisoformat(portfolio["last_trade_execution"]) if portfolio.get("last_trade_execution") else None,
            next_execution=self._calculate_next_execution_time(portfolio),
            pending_orders_count=len(portfolio.get("pending_orders", [])),
            daily_trades_count=today_trades,
            daily_trades_limit=daily_limit,
            error_messages=error_messages
        )
    
    async def _sync_portfolio_positions(self, portfolio_id: str):
        """同步投资组合持仓"""
        portfolio = self.portfolios[portfolio_id]
        
        if not portfolio.get("trading_api"):
            return
        
        try:
            trading_config = TradingApiConfig(**portfolio["trading_api"])
            positions = await self.trading_manager.sync_portfolio_positions(portfolio_id, trading_config)
            
            # 更新持仓数据
            portfolio["holdings"] = [pos.dict() for pos in positions]
            
            # 更新可用资金
            account_info = await self.trading_manager.get_account_summary(trading_config)
            portfolio["available_cash"] = float(account_info.get("cash", 0))
            
            self._save_portfolios()
            
        except Exception as e:
            logger.error(f"同步持仓失败: {e}")
    
    def _count_today_trades(self, portfolio_id: str) -> int:
        """统计今日交易次数"""
        portfolio = self.portfolios[portfolio_id]
        today = datetime.now(timezone.utc).date()
        
        count = 0
        for order in portfolio.get("order_history", []):
            order_date = datetime.fromisoformat(order["created_at"]).date()
            if order_date == today and order["execution_source"] in ["ai_auto", "stop_loss", "take_profit"]:
                count += 1
        
        return count
    
    def _calculate_next_execution_time(self, portfolio: Dict) -> Optional[datetime]:
        """计算下次执行时间"""
        if portfolio["mode"] == "manual" or not portfolio["is_active"]:
            return None
        
        ai_strategy_data = portfolio.get("ai_strategy")
        if not ai_strategy_data:
            return None
        
        rebalance_frequency = ai_strategy_data.get("rebalance_frequency", "daily")
        
        last_execution = portfolio.get("last_trade_execution")
        if not last_execution:
            return datetime.now(timezone.utc) + timedelta(hours=1)
        
        last_execution_dt = datetime.fromisoformat(last_execution)
        
        if rebalance_frequency == "daily":
            return last_execution_dt + timedelta(days=1)
        elif rebalance_frequency == "weekly":
            return last_execution_dt + timedelta(days=7)
        elif rebalance_frequency == "monthly":
            return last_execution_dt + timedelta(days=30)
        
        return None
    
    async def run_automated_trading_cycle(self):
        """运行自动交易周期（定时任务）"""
        logger.info("开始自动交易周期")
        
        for portfolio_id, portfolio in self.portfolios.items():
            if portfolio["mode"] in ["auto", "hybrid"] and portfolio["is_active"]:
                try:
                    # 检查止损止盈
                    await self.check_stop_loss_take_profit(portfolio_id)
                    
                    # 检查是否需要重新平衡
                    status = await self.get_auto_trading_status(portfolio_id)
                    if status and status.is_enabled:
                        if status.next_execution and datetime.now(timezone.utc) >= status.next_execution:
                            await self.rebalance_portfolio(portfolio_id)
                    
                except Exception as e:
                    logger.error(f"自动交易周期处理投资组合 {portfolio_id} 失败: {e}")
        
        logger.info("自动交易周期完成")
    
    async def delete_portfolio(self, portfolio_id: str) -> bool:
        """删除投资组合"""
        if portfolio_id not in self.portfolios:
            return False
        
        # 检查是否有未完成的订单
        portfolio = self.portfolios[portfolio_id]
        pending_orders = portfolio.get("pending_orders", [])
        if pending_orders:
            logger.warning(f"投资组合 {portfolio_id} 还有 {len(pending_orders)} 个待处理订单")
            return False
        
        del self.portfolios[portfolio_id]
        self._save_portfolios()
        
        logger.info(f"删除投资组合: {portfolio_id}")
        return True


# 全局自动交易服务实例
automated_trading_service = AutomatedTradingService()