"""
交易API接口抽象层
支持多种交易平台的统一接口
"""

import os
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import requests
import time
from .schemas import TradingApiConfig, TradingOrder, PortfolioHolding


class TradingAPIError(Exception):
    """交易API异常"""
    pass


class OrderExecutionError(TradingAPIError):
    """订单执行异常"""
    pass


class InsufficientFundsError(TradingAPIError):
    """资金不足异常"""
    pass


class TradingAPIInterface(ABC):
    """交易API抽象接口"""
    
    def __init__(self, config: TradingApiConfig):
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self) -> bool:
        """连接到交易API"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict:
        """获取账户信息"""
        pass
    
    @abstractmethod
    async def get_buying_power(self) -> float:
        """获取购买力"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[PortfolioHolding]:
        """获取当前持仓"""
        pass
    
    @abstractmethod
    async def submit_order(self, order: TradingOrder) -> str:
        """提交订单，返回broker订单ID"""
        pass
    
    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> Dict:
        """获取订单状态"""
        pass
    
    @abstractmethod
    async def get_market_data(self, ticker: str) -> Dict:
        """获取实时市场数据"""
        pass
    
    def is_market_open(self) -> bool:
        """检查市场是否开盘"""
        now = datetime.now().time()
        # 简单的美股交易时间检查 (9:30-16:00 ET)
        # 在实际实现中应该考虑节假日和时区
        market_open = now.hour >= 9 and (now.hour < 16 or (now.hour == 9 and now.minute >= 30))
        return market_open


class AlpacaTradingAPI(TradingAPIInterface):
    """Alpaca交易API实现"""
    
    def __init__(self, config: TradingApiConfig):
        super().__init__(config)
        self.base_url = config.base_url or ("https://paper-api.alpaca.markets" if config.is_sandbox else "https://api.alpaca.markets")
        self.headers = {
            "APCA-API-KEY-ID": config.api_key,
            "APCA-API-SECRET-KEY": config.api_secret,
            "Content-Type": "application/json"
        }
    
    async def connect(self) -> bool:
        """连接到Alpaca API"""
        try:
            response = requests.get(f"{self.base_url}/v2/account", headers=self.headers)
            if response.status_code == 200:
                self.is_connected = True
                return True
            else:
                raise TradingAPIError(f"Alpaca连接失败: {response.text}")
        except Exception as e:
            raise TradingAPIError(f"Alpaca连接异常: {str(e)}")
    
    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
    
    async def get_account_info(self) -> Dict:
        """获取账户信息"""
        if not self.is_connected:
            await self.connect()
        
        response = requests.get(f"{self.base_url}/v2/account", headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise TradingAPIError(f"获取账户信息失败: {response.text}")
    
    async def get_buying_power(self) -> float:
        """获取购买力"""
        account = await self.get_account_info()
        return float(account.get("buying_power", 0))
    
    async def get_positions(self) -> List[PortfolioHolding]:
        """获取当前持仓"""
        if not self.is_connected:
            await self.connect()
        
        response = requests.get(f"{self.base_url}/v2/positions", headers=self.headers)
        if response.status_code == 200:
            positions = response.json()
            holdings = []
            
            for pos in positions:
                if float(pos["qty"]) > 0:  # 只返回多头持仓
                    # 获取当前价格
                    current_price = float(pos.get("market_value", 0)) / float(pos["qty"])
                    avg_cost = float(pos["avg_cost"])
                    shares = float(pos["qty"])
                    market_value = float(pos["market_value"])
                    unrealized_pnl = float(pos["unrealized_pl"])
                    unrealized_pnl_pct = (unrealized_pnl / (avg_cost * shares) * 100) if avg_cost * shares > 0 else 0
                    
                    holding = PortfolioHolding(
                        ticker=pos["symbol"],
                        shares=shares,
                        avg_cost=avg_cost,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_pct=unrealized_pnl_pct,
                        weight=0  # 权重需要在外部计算
                    )
                    holdings.append(holding)
            
            return holdings
        else:
            raise TradingAPIError(f"获取持仓失败: {response.text}")
    
    async def submit_order(self, order: TradingOrder) -> str:
        """提交订单"""
        if not self.is_connected:
            await self.connect()
        
        # 检查购买力
        if order.side == "buy":
            buying_power = await self.get_buying_power()
            estimated_cost = order.quantity * (order.price or 0)
            if estimated_cost > buying_power:
                raise InsufficientFundsError(f"资金不足: 需要${estimated_cost:.2f}, 可用${buying_power:.2f}")
        
        # 构建订单数据
        order_data = {
            "symbol": order.ticker,
            "qty": str(order.quantity),
            "side": order.side,
            "type": order.order_type,
            "time_in_force": "day"
        }
        
        if order.order_type == "limit" and order.price:
            order_data["limit_price"] = str(order.price)
        elif order.order_type == "stop" and order.stop_price:
            order_data["stop_price"] = str(order.stop_price)
        elif order.order_type == "stop_limit" and order.price and order.stop_price:
            order_data["limit_price"] = str(order.price)
            order_data["stop_price"] = str(order.stop_price)
        
        response = requests.post(f"{self.base_url}/v2/orders", 
                               headers=self.headers, 
                               json=order_data)
        
        if response.status_code == 201:
            order_response = response.json()
            return order_response["id"]
        else:
            raise OrderExecutionError(f"订单提交失败: {response.text}")
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        """取消订单"""
        if not self.is_connected:
            await self.connect()
        
        response = requests.delete(f"{self.base_url}/v2/orders/{broker_order_id}", 
                                 headers=self.headers)
        return response.status_code == 204
    
    async def get_order_status(self, broker_order_id: str) -> Dict:
        """获取订单状态"""
        if not self.is_connected:
            await self.connect()
        
        response = requests.get(f"{self.base_url}/v2/orders/{broker_order_id}", 
                              headers=self.headers)
        
        if response.status_code == 200:
            order_data = response.json()
            return {
                "status": order_data["status"],
                "filled_qty": float(order_data.get("filled_qty", 0)),
                "filled_price": float(order_data.get("filled_avg_price", 0)) if order_data.get("filled_avg_price") else None,
                "updated_at": order_data.get("updated_at")
            }
        else:
            raise TradingAPIError(f"获取订单状态失败: {response.text}")
    
    async def get_market_data(self, ticker: str) -> Dict:
        """获取实时市场数据"""
        if not self.is_connected:
            await self.connect()
        
        response = requests.get(f"{self.base_url}/v2/stocks/{ticker}/quotes/latest", 
                              headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            quote = data["quote"]
            return {
                "ticker": ticker,
                "price": (float(quote["bid_price"]) + float(quote["ask_price"])) / 2,
                "bid": float(quote["bid_price"]),
                "ask": float(quote["ask_price"]),
                "volume": int(quote.get("bid_size", 0) + quote.get("ask_size", 0)),
                "timestamp": quote["timestamp"]
            }
        else:
            raise TradingAPIError(f"获取市场数据失败: {response.text}")


class PaperTradingAPI(TradingAPIInterface):
    """纸上交易API实现"""
    
    def __init__(self, config: TradingApiConfig):
        super().__init__(config)
        self.data_file = "paper_trading_data.json"
        self.account_data = self._load_account_data()
    
    def _load_account_data(self) -> Dict:
        """加载纸上交易账户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认账户数据
        return {
            "cash": 100000.0,  # 默认10万美元
            "positions": {},
            "orders": {},
            "order_history": []
        }
    
    def _save_account_data(self):
        """保存账户数据"""
        with open(self.data_file, 'w') as f:
            json.dump(self.account_data, f, indent=2, default=str)
    
    async def connect(self) -> bool:
        """连接（纸上交易总是成功）"""
        self.is_connected = True
        return True
    
    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
    
    async def get_account_info(self) -> Dict:
        """获取账户信息"""
        total_value = self.account_data["cash"]
        for ticker, position in self.account_data["positions"].items():
            # 模拟获取当前价格（实际应该调用市场数据API）
            current_price = position["avg_cost"] * 1.05  # 假设上涨5%
            total_value += position["shares"] * current_price
        
        return {
            "cash": self.account_data["cash"],
            "buying_power": self.account_data["cash"],
            "portfolio_value": total_value,
            "equity": total_value
        }
    
    async def get_buying_power(self) -> float:
        """获取购买力"""
        return self.account_data["cash"]
    
    async def get_positions(self) -> List[PortfolioHolding]:
        """获取当前持仓"""
        holdings = []
        
        for ticker, position in self.account_data["positions"].items():
            if position["shares"] > 0:
                # 模拟当前价格
                current_price = position["avg_cost"] * (1 + (hash(ticker) % 20 - 10) / 100)  # 模拟价格波动
                shares = position["shares"]
                avg_cost = position["avg_cost"]
                market_value = shares * current_price
                cost_basis = shares * avg_cost
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                holding = PortfolioHolding(
                    ticker=ticker,
                    shares=shares,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    weight=0
                )
                holdings.append(holding)
        
        return holdings
    
    async def submit_order(self, order: TradingOrder) -> str:
        """提交订单"""
        broker_order_id = str(uuid.uuid4())
        
        # 模拟市价单立即成交
        if order.order_type == "market":
            if order.side == "buy":
                cost = order.quantity * order.price if order.price else order.quantity * 100  # 假设价格
                if cost > self.account_data["cash"]:
                    raise InsufficientFundsError(f"资金不足")
                
                # 扣除现金
                self.account_data["cash"] -= cost
                
                # 更新持仓
                if order.ticker in self.account_data["positions"]:
                    pos = self.account_data["positions"][order.ticker]
                    total_shares = pos["shares"] + order.quantity
                    total_cost = pos["shares"] * pos["avg_cost"] + cost
                    self.account_data["positions"][order.ticker] = {
                        "shares": total_shares,
                        "avg_cost": total_cost / total_shares if total_shares > 0 else 0
                    }
                else:
                    self.account_data["positions"][order.ticker] = {
                        "shares": order.quantity,
                        "avg_cost": order.price if order.price else 100
                    }
            
            elif order.side == "sell":
                if order.ticker not in self.account_data["positions"]:
                    raise OrderExecutionError(f"没有{order.ticker}的持仓")
                
                pos = self.account_data["positions"][order.ticker]
                if pos["shares"] < order.quantity:
                    raise OrderExecutionError(f"持仓不足")
                
                # 卖出股票
                proceeds = order.quantity * (order.price if order.price else pos["avg_cost"] * 1.05)
                self.account_data["cash"] += proceeds
                pos["shares"] -= order.quantity
                
                if pos["shares"] <= 0:
                    del self.account_data["positions"][order.ticker]
            
            # 保存数据
            self._save_account_data()
        
        return broker_order_id
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        """取消订单（纸上交易总是成功）"""
        return True
    
    async def get_order_status(self, broker_order_id: str) -> Dict:
        """获取订单状态（纸上交易总是已成交）"""
        return {
            "status": "filled",
            "filled_qty": 100,  # 模拟数据
            "filled_price": 150.0,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_market_data(self, ticker: str) -> Dict:
        """获取市场数据（模拟数据）"""
        # 生成模拟价格
        base_price = 100 + (hash(ticker) % 500)
        price = base_price + (hash(ticker + str(time.time())) % 10 - 5)
        
        return {
            "ticker": ticker,
            "price": price,
            "bid": price - 0.01,
            "ask": price + 0.01,
            "volume": 1000 + (hash(ticker) % 10000),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class TradingAPIFactory:
    """交易API工厂"""
    
    @staticmethod
    def create_api(config: TradingApiConfig) -> TradingAPIInterface:
        """根据配置创建交易API实例"""
        if config.api_provider == "alpaca":
            return AlpacaTradingAPI(config)
        elif config.api_provider == "paper_trading":
            return PaperTradingAPI(config)
        elif config.api_provider == "interactive_brokers":
            # TODO: 实现Interactive Brokers API
            raise NotImplementedError("Interactive Brokers API尚未实现")
        elif config.api_provider == "td_ameritrade":
            # TODO: 实现TD Ameritrade API
            raise NotImplementedError("TD Ameritrade API尚未实现")
        elif config.api_provider == "schwab":
            # TODO: 实现Schwab API
            raise NotImplementedError("Schwab API尚未实现")
        else:
            raise ValueError(f"不支持的API提供商: {config.api_provider}")


class TradingManager:
    """交易管理器"""
    
    def __init__(self):
        self.api_connections: Dict[str, TradingAPIInterface] = {}
    
    async def get_api(self, config: TradingApiConfig) -> TradingAPIInterface:
        """获取或创建API连接"""
        api_key = f"{config.api_provider}_{config.api_key[:8]}"
        
        if api_key not in self.api_connections:
            api = TradingAPIFactory.create_api(config)
            await api.connect()
            self.api_connections[api_key] = api
        
        return self.api_connections[api_key]
    
    async def sync_portfolio_positions(self, portfolio_id: str, config: TradingApiConfig) -> List[PortfolioHolding]:
        """同步投资组合持仓"""
        api = await self.get_api(config)
        return await api.get_positions()
    
    async def execute_order(self, order: TradingOrder, config: TradingApiConfig) -> str:
        """执行订单"""
        api = await self.get_api(config)
        return await api.submit_order(order)
    
    async def get_account_summary(self, config: TradingApiConfig) -> Dict:
        """获取账户摘要"""
        api = await self.get_api(config)
        return await api.get_account_info()
    
    async def close_all_connections(self):
        """关闭所有连接"""
        for api in self.api_connections.values():
            await api.disconnect()
        self.api_connections.clear()


# 全局交易管理器实例
trading_manager = TradingManager()