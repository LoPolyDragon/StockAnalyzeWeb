import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid
import numpy as np
import pandas as pd
from .stock_service import get_stock_data
from .schemas import PortfolioResponse, PortfolioHolding, PortfolioPerformance, AddHoldingRequest

# 简单的JSON文件存储（生产环境建议使用数据库）
PORTFOLIO_DATA_FILE = "portfolios.json"

class PortfolioService:
    def __init__(self):
        self.portfolios = self._load_portfolios()
    
    def _load_portfolios(self) -> Dict:
        """从文件加载投资组合数据"""
        if os.path.exists(PORTFOLIO_DATA_FILE):
            try:
                with open(PORTFOLIO_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_portfolios(self):
        """保存投资组合数据到文件"""
        with open(PORTFOLIO_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.portfolios, f, ensure_ascii=False, indent=2, default=str)
    
    def create_portfolio(self, name: str, description: Optional[str] = None) -> str:
        """创建新的投资组合"""
        portfolio_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        self.portfolios[portfolio_id] = {
            "id": portfolio_id,
            "name": name,
            "description": description or "",
            "holdings": {},  # {ticker: {shares, avg_cost, transactions}}
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        self._save_portfolios()
        return portfolio_id
    
    def add_holding(self, portfolio_id: str, ticker: str, shares: float, cost_per_share: float) -> bool:
        """添加或更新股票持仓"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        now = datetime.now(timezone.utc)
        
        if ticker in portfolio["holdings"]:
            # 更新现有持仓（加权平均成本）
            holding = portfolio["holdings"][ticker]
            current_shares = holding["shares"]
            current_avg_cost = holding["avg_cost"]
            
            total_shares = current_shares + shares
            total_cost = (current_shares * current_avg_cost) + (shares * cost_per_share)
            new_avg_cost = total_cost / total_shares if total_shares > 0 else 0
            
            portfolio["holdings"][ticker] = {
                "shares": total_shares,
                "avg_cost": new_avg_cost,
                "transactions": holding.get("transactions", []) + [{
                    "date": now.isoformat(),
                    "shares": shares,
                    "price": cost_per_share,
                    "type": "buy" if shares > 0 else "sell"
                }]
            }
        else:
            # 新增持仓
            portfolio["holdings"][ticker] = {
                "shares": shares,
                "avg_cost": cost_per_share,
                "transactions": [{
                    "date": now.isoformat(),
                    "shares": shares,
                    "price": cost_per_share,
                    "type": "buy" if shares > 0 else "sell"
                }]
            }
        
        portfolio["updated_at"] = now.isoformat()
        self._save_portfolios()
        return True
    
    def get_portfolio(self, portfolio_id: str) -> Optional[PortfolioResponse]:
        """获取投资组合详情"""
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_id]
        holdings = []
        total_value = 0
        total_cost = 0
        
        for ticker, holding_data in portfolio["holdings"].items():
            shares = holding_data["shares"]
            avg_cost = holding_data["avg_cost"]
            
            if shares <= 0:  # 已清仓的股票不显示
                continue
                
            try:
                # 获取当前价格
                stock_data = get_stock_data(ticker, period="1d")
                if stock_data.empty:
                    continue
                    
                current_price = float(stock_data.iloc[-1]["Close"])
                market_value = shares * current_price
                cost_basis = shares * avg_cost
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                holdings.append(PortfolioHolding(
                    ticker=ticker,
                    shares=shares,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    weight=0  # 将在后面计算
                ))
                
                total_value += market_value
                total_cost += cost_basis
                
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
        
        # 计算权重
        for holding in holdings:
            holding.weight = (holding.market_value / total_value * 100) if total_value > 0 else 0
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return PortfolioResponse(
            id=portfolio["id"],
            name=portfolio["name"],
            description=portfolio["description"],
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            holdings=holdings,
            created_at=datetime.fromisoformat(portfolio["created_at"]),
            updated_at=datetime.fromisoformat(portfolio["updated_at"])
        )
    
    def list_portfolios(self) -> List[Dict]:
        """列出所有投资组合"""
        portfolio_list = []
        for portfolio_id, portfolio in self.portfolios.items():
            portfolio_summary = self.get_portfolio(portfolio_id)
            if portfolio_summary:
                portfolio_list.append({
                    "id": portfolio_id,
                    "name": portfolio["name"],
                    "description": portfolio["description"],
                    "total_value": portfolio_summary.total_value,
                    "total_pnl_pct": portfolio_summary.total_pnl_pct,
                    "holdings_count": len(portfolio_summary.holdings),
                    "updated_at": portfolio["updated_at"]
                })
        return portfolio_list
    
    def get_portfolio_performance(self, portfolio_id: str, period: str = "1y") -> Optional[PortfolioPerformance]:
        """计算投资组合表现指标"""
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_id]
        
        # 获取历史数据并计算每日组合价值
        try:
            daily_values = self._calculate_daily_portfolio_values(portfolio, period)
            if len(daily_values) < 2:
                return None
            
            # 计算日收益率
            returns = []
            for i in range(1, len(daily_values)):
                prev_value = daily_values[i-1]["value"]
                curr_value = daily_values[i]["value"]
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    returns.append(daily_return)
                    daily_values[i]["return_pct"] = daily_return * 100
            
            if not returns:
                return None
                
            returns_array = np.array(returns)
            
            # 计算性能指标
            cumulative_return = (daily_values[-1]["value"] / daily_values[0]["value"] - 1) * 100
            annualized_return = np.mean(returns_array) * 252 * 100  # 假设252个交易日
            volatility = np.std(returns_array) * np.sqrt(252) * 100
            sharpe_ratio = (annualized_return - 3) / volatility if volatility > 0 else 0  # 假设无风险利率3%
            
            # 计算最大回撤
            peak = daily_values[0]["value"]
            max_drawdown = 0
            for day in daily_values:
                if day["value"] > peak:
                    peak = day["value"]
                drawdown = (peak - day["value"]) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            max_drawdown *= 100
            
            # 找出最好和最坏的一天
            best_day = max(daily_values[1:], key=lambda x: x.get("return_pct", 0))
            worst_day = min(daily_values[1:], key=lambda x: x.get("return_pct", 0))
            
            return PortfolioPerformance(
                portfolio_id=portfolio_id,
                daily_returns=daily_values,
                cumulative_return=cumulative_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                best_day={"date": best_day["date"], "return_pct": best_day.get("return_pct", 0)},
                worst_day={"date": worst_day["date"], "return_pct": worst_day.get("return_pct", 0)}
            )
            
        except Exception as e:
            print(f"Error calculating portfolio performance: {e}")
            return None
    
    def _calculate_daily_portfolio_values(self, portfolio: Dict, period: str = "1y") -> List[Dict]:
        """计算投资组合的每日价值"""
        holdings = portfolio["holdings"]
        if not holdings:
            return []
        
        # 获取所有股票的历史数据
        all_stock_data = {}
        for ticker in holdings.keys():
            try:
                stock_data = get_stock_data(ticker, period=period)
                if not stock_data.empty:
                    all_stock_data[ticker] = stock_data
            except Exception:
                continue
        
        if not all_stock_data:
            return []
        
        # 找到共同的日期范围
        common_dates = set(all_stock_data[list(all_stock_data.keys())[0]].index)
        for ticker, data in all_stock_data.items():
            common_dates = common_dates.intersection(set(data.index))
        
        common_dates = sorted(list(common_dates))
        
        # 计算每日组合价值
        daily_values = []
        for date in common_dates:
            total_value = 0
            for ticker, holding_data in holdings.items():
                if ticker in all_stock_data and date in all_stock_data[ticker].index:
                    price = all_stock_data[ticker].loc[date, "Close"]
                    shares = holding_data["shares"]
                    total_value += price * shares
            
            daily_values.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": total_value
            })
        
        return daily_values

# 全局实例
portfolio_service = PortfolioService()