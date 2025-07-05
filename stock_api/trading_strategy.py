"""
自动化交易策略模块
基于AI决策和风险管理的自动交易系统
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
from .ai_agent import make_decision
from .stock_service import get_stock_data
from .risk_service import risk_service
from .futu_service import get_futu_trade_service, get_futu_quote_service
from futu.common.constant import TrdSide, OrderType, TrdEnv

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyType(Enum):
    """策略类型"""
    MOMENTUM = "momentum"  # 动量策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    BREAKOUT = "breakout"  # 突破策略
    AI_DECISION = "ai_decision"  # AI决策策略


@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 信号置信度 0-1
    price: float
    timestamp: datetime
    reasons: List[str]
    strategy: StrategyType
    risk_score: float  # 风险评分 0-100
    position_size: float  # 建议仓位比例 0-1


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_size: float = 0.1, 
                 max_total_risk: float = 0.2,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.15):
        """
        初始化风险管理参数
        
        Args:
            max_position_size: 单只股票最大仓位比例
            max_total_risk: 总风险敞口上限
            stop_loss_pct: 止损比例
            take_profit_pct: 止盈比例
        """
        self.max_position_size = max_position_size
        self.max_total_risk = max_total_risk
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
    
    def calculate_position_size(self, signal: TradingSignal, 
                              account_value: float,
                              current_positions: List[PositionInfo]) -> float:
        """
        计算建议仓位大小
        
        Args:
            signal: 交易信号
            account_value: 账户总价值
            current_positions: 当前持仓
            
        Returns:
            建议投资金额
        """
        # 基于风险评分调整仓位
        risk_factor = 1.0 - (signal.risk_score / 100.0)
        base_position = self.max_position_size * risk_factor
        
        # 考虑信号置信度
        confidence_factor = signal.confidence
        adjusted_position = base_position * confidence_factor
        
        # 检查总风险敞口
        current_risk = sum(pos.unrealized_pnl for pos in current_positions if pos.unrealized_pnl < 0)
        max_risk_amount = account_value * self.max_total_risk
        
        if abs(current_risk) + (adjusted_position * account_value) > max_risk_amount:
            adjusted_position = max(0, (max_risk_amount - abs(current_risk)) / account_value)
        
        return min(adjusted_position * account_value, account_value * self.max_position_size)
    
    def should_stop_loss(self, position: PositionInfo) -> bool:
        """判断是否应该止损"""
        return position.unrealized_pnl_pct < -self.stop_loss_pct
    
    def should_take_profit(self, position: PositionInfo) -> bool:
        """判断是否应该止盈"""
        return position.unrealized_pnl_pct > self.take_profit_pct


class TradingStrategy:
    """基础交易策略类"""
    
    def __init__(self, name: str, strategy_type: StrategyType):
        self.name = name
        self.strategy_type = strategy_type
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """生成交易信号（基类方法，需要子类实现）"""
        raise NotImplementedError
    
    def backtest(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """策略回测（预留接口）"""
        # TODO: 实现回测功能
        pass


class AIDecisionStrategy(TradingStrategy):
    """AI决策策略"""
    
    def __init__(self):
        super().__init__("AI决策策略", StrategyType.AI_DECISION)
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """基于AI决策生成交易信号"""
        try:
            if data.empty:
                return None
            
            # 获取AI决策
            decision, reasons = make_decision(data)
            
            # 获取风险评估
            risk_analysis = risk_service.get_comprehensive_risk_analysis(symbol)
            risk_score = risk_analysis.risk_score if risk_analysis else 50.0
            
            # 转换决策为信号
            if decision == "BUY":
                signal_type = SignalType.BUY
                confidence = 0.8  # 基础置信度
            elif decision == "SELL":
                signal_type = SignalType.SELL
                confidence = 0.8
            else:
                signal_type = SignalType.HOLD
                confidence = 0.5
            
            # 根据风险评分调整置信度
            risk_factor = 1.0 - (risk_score / 200.0)  # 风险越高，置信度越低
            confidence = max(0.1, confidence * risk_factor)
            
            current_price = float(data.iloc[-1]['Close'])
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasons=reasons,
                strategy=self.strategy_type,
                risk_score=risk_score,
                position_size=min(0.1, confidence * 0.15)  # 基于置信度计算仓位
            )
            
        except Exception as e:
            logger.error(f"生成AI交易信号失败: {e}")
            return None


class MomentumStrategy(TradingStrategy):
    """动量策略"""
    
    def __init__(self, lookback_period: int = 20):
        super().__init__("动量策略", StrategyType.MOMENTUM)
        self.lookback_period = lookback_period
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """基于动量指标生成信号"""
        try:
            if len(data) < self.lookback_period:
                return None
            
            # 计算动量指标
            data['returns'] = data['Close'].pct_change()
            momentum = data['returns'].rolling(self.lookback_period).mean()
            
            current_momentum = momentum.iloc[-1]
            current_price = float(data.iloc[-1]['Close'])
            
            # 生成信号
            if current_momentum > 0.02:  # 2%以上动量
                signal_type = SignalType.BUY
                confidence = min(0.9, abs(current_momentum) * 10)
                reasons = [f"动量指标显示强势上涨，{self.lookback_period}日平均收益率: {current_momentum:.2%}"]
            elif current_momentum < -0.02:  # -2%以下动量
                signal_type = SignalType.SELL
                confidence = min(0.9, abs(current_momentum) * 10)
                reasons = [f"动量指标显示弱势下跌，{self.lookback_period}日平均收益率: {current_momentum:.2%}"]
            else:
                signal_type = SignalType.HOLD
                confidence = 0.3
                reasons = ["动量指标显示横盘整理"]
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasons=reasons,
                strategy=self.strategy_type,
                risk_score=50.0,  # 默认风险评分
                position_size=confidence * 0.1
            )
            
        except Exception as e:
            logger.error(f"生成动量策略信号失败: {e}")
            return None


class AutoTradingEngine:
    """自动交易引擎"""
    
    def __init__(self, strategies: List[TradingStrategy] = None,
                 risk_manager: RiskManager = None,
                 dry_run: bool = True):
        """
        初始化自动交易引擎
        
        Args:
            strategies: 交易策略列表
            risk_manager: 风险管理器
            dry_run: 是否为模拟模式
        """
        self.strategies = strategies or [AIDecisionStrategy(), MomentumStrategy()]
        self.risk_manager = risk_manager or RiskManager()
        self.dry_run = dry_run
        self.trade_service = get_futu_trade_service()
        self.quote_service = get_futu_quote_service()
        self.active = False
    
    def start(self):
        """启动自动交易"""
        self.active = True
        logger.info("自动交易引擎已启动")
    
    def stop(self):
        """停止自动交易"""
        self.active = False
        logger.info("自动交易引擎已停止")
    
    def scan_opportunities(self, watchlist: List[str]) -> List[TradingSignal]:
        """扫描交易机会"""
        signals = []
        
        for symbol in watchlist:
            try:
                # 获取股票数据
                data = get_stock_data(symbol, period="3mo")
                if data.empty:
                    continue
                
                # 各策略生成信号
                for strategy in self.strategies:
                    signal = strategy.generate_signal(symbol, data)
                    if signal and signal.signal_type != SignalType.HOLD:
                        signals.append(signal)
                        logger.info(f"发现交易信号: {symbol} - {signal.signal_type.value}, 置信度: {signal.confidence:.2f}")
                
            except Exception as e:
                logger.error(f"扫描 {symbol} 时出错: {e}")
                continue
        
        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)
        return signals
    
    def execute_signal(self, signal: TradingSignal, account_id: int) -> Dict:
        """执行交易信号"""
        try:
            if self.dry_run:
                logger.info(f"模拟交易: {signal.symbol} {signal.signal_type.value} at {signal.price}")
                return {
                    "success": True,
                    "mode": "dry_run",
                    "signal": signal,
                    "message": "模拟交易执行成功"
                }
            
            # 获取账户信息和当前持仓
            positions = self.trade_service.get_positions(account_id)
            if "error" in positions:
                return {"error": f"获取持仓失败: {positions['error']}"}
            
            # 计算仓位大小
            account_value = 100000  # TODO: 从账户获取实际净值
            current_positions = []  # TODO: 解析持仓数据
            
            position_amount = self.risk_manager.calculate_position_size(
                signal, account_value, current_positions
            )
            
            if position_amount < 100:  # 最小交易金额
                return {"error": "建议仓位过小，跳过交易"}
            
            # 转换股票代码
            futu_code = self.quote_service.convert_stock_code(signal.symbol)
            quantity = int(position_amount / signal.price)
            
            # 执行交易
            trade_side = TrdSide.BUY if signal.signal_type == SignalType.BUY else TrdSide.SELL
            
            result = self.trade_service.place_order(
                acc_id=account_id,
                code=futu_code,
                price=signal.price,
                qty=quantity,
                trd_side=trade_side,
                order_type=OrderType.NORMAL
            )
            
            if "error" in result:
                return {"error": f"下单失败: {result['error']}"}
            
            logger.info(f"交易执行成功: {signal.symbol} {signal.signal_type.value} {quantity}股")
            return {
                "success": True,
                "order_id": result.get("order_id"),
                "signal": signal,
                "quantity": quantity,
                "amount": position_amount
            }
            
        except Exception as e:
            logger.error(f"执行交易信号失败: {e}")
            return {"error": f"交易执行异常: {e}"}
    
    def run_cycle(self, watchlist: List[str], account_id: int) -> Dict:
        """运行一次交易周期"""
        try:
            if not self.active:
                return {"message": "交易引擎未启动"}
            
            # 扫描机会
            signals = self.scan_opportunities(watchlist)
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "signals_found": len(signals),
                "executed_trades": [],
                "errors": []
            }
            
            # 执行前N个最优信号
            max_trades_per_cycle = 3
            for signal in signals[:max_trades_per_cycle]:
                if signal.confidence > 0.6:  # 置信度阈值
                    trade_result = self.execute_signal(signal, account_id)
                    
                    if "error" in trade_result:
                        results["errors"].append({
                            "symbol": signal.symbol,
                            "error": trade_result["error"]
                        })
                    else:
                        results["executed_trades"].append(trade_result)
            
            return results
            
        except Exception as e:
            logger.error(f"交易周期运行失败: {e}")
            return {"error": f"交易周期异常: {e}"}


# 全局交易引擎实例
auto_trading_engine = AutoTradingEngine(dry_run=True)


def get_trading_engine() -> AutoTradingEngine:
    """获取自动交易引擎实例"""
    return auto_trading_engine