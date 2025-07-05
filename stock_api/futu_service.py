"""
富途牛牛API服务模块
提供股票数据查询、交易功能
"""

import logging
from typing import Dict, List, Optional, Tuple
from futu.quote.open_quote_context import OpenQuoteContext
from futu.trade.open_trade_context import OpenSecTradeContext
from futu.common.constant import (
    RET_OK, RET_ERROR, Market, SecurityType, KLType, AuType,
    TrdEnv, TrdMarket, OrderType, TrdSide, Plate
)
import pandas as pd
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class FutuService:
    def __init__(self, host: str = '127.0.0.1', port: int = 11111):
        """
        初始化富途API连接
        
        Args:
            host: 富途OpenD的IP地址
            port: 富途OpenD的端口号
        """
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self._connected = False
        
    def connect(self) -> bool:
        """建立连接"""
        try:
            # 行情连接
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            
            # 检查连接状态
            ret, data = self.quote_ctx.get_global_state()
            if ret == RET_OK:
                self._connected = True
                logger.info("富途API连接成功")
                return True
            else:
                logger.error(f"富途API连接失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"富途API连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
            if self.trade_ctx:
                self.trade_ctx.close()
            self._connected = False
            logger.info("富途API连接已断开")
        except Exception as e:
            logger.error(f"断开富途API连接时出错: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def get_stock_basicinfo(self, stock_codes: List[str]) -> Dict:
        """
        获取股票基本信息
        
        Args:
            stock_codes: 股票代码列表，如 ['HK.00700', 'US.AAPL']
            
        Returns:
            包含股票基本信息的字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data = self.quote_ctx.get_stock_basicinfo(Market.NONE, SecurityType.STOCK, stock_codes)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                logger.error(f"获取股票基本信息失败: {data}")
                return {"error": f"获取失败: {data}"}
                
        except Exception as e:
            logger.error(f"获取股票基本信息异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def get_market_snapshot(self, stock_codes: List[str]) -> Dict:
        """
        获取股票快照数据（实时行情）
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            包含实时行情的字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data = self.quote_ctx.get_market_snapshot(stock_codes)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                logger.error(f"获取市场快照失败: {data}")
                return {"error": f"获取失败: {data}"}
                
        except Exception as e:
            logger.error(f"获取市场快照异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def get_history_kline(self, code: str, start: str, end: str, 
                         ktype: KLType = KLType.K_DAY, 
                         autype: AuType = AuType.QFQ) -> Dict:
        """
        获取历史K线数据
        
        Args:
            code: 股票代码，如 'HK.00700'
            start: 开始日期 'YYYY-MM-DD'
            end: 结束日期 'YYYY-MM-DD'
            ktype: K线类型
            autype: 复权类型
            
        Returns:
            包含K线数据的字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code, start=start, end=end, ktype=ktype, autype=autype, max_count=1000
            )
            
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records'),
                    "total_count": len(data)
                }
            else:
                logger.error(f"获取历史K线失败: {data}")
                return {"error": f"获取失败: {data}"}
                
        except Exception as e:
            logger.error(f"获取历史K线异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def get_cur_kline(self, code: str, num: int = 100, 
                     ktype: KLType = KLType.K_DAY) -> Dict:
        """
        获取当前K线数据
        
        Args:
            code: 股票代码
            num: 获取数量
            ktype: K线类型
            
        Returns:
            包含K线数据的字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data = self.quote_ctx.get_cur_kline(code, num, ktype)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records'),
                    "count": len(data)
                }
            else:
                logger.error(f"获取当前K线失败: {data}")
                return {"error": f"获取失败: {data}"}
                
        except Exception as e:
            logger.error(f"获取当前K线异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def search_stock(self, keyword: str) -> Dict:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            搜索结果字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data = self.quote_ctx.get_stock_filter(Market.NONE, keyword)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                logger.error(f"搜索股票失败: {data}")
                return {"error": f"搜索失败: {data}"}
                
        except Exception as e:
            logger.error(f"搜索股票异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def get_plate_list(self, market: Market = Market.NONE) -> Dict:
        """
        获取板块列表
        
        Args:
            market: 市场类型
            
        Returns:
            板块列表字典
        """
        if not self.is_connected():
            if not self.connect():
                return {"error": "无法连接富途API"}
        
        try:
            ret, data = self.quote_ctx.get_plate_list(market, Plate.ALL)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                logger.error(f"获取板块列表失败: {data}")
                return {"error": f"获取失败: {data}"}
                
        except Exception as e:
            logger.error(f"获取板块列表异常: {e}")
            return {"error": f"API异常: {e}"}
    
    def convert_stock_code(self, symbol: str) -> str:
        """
        转换股票代码格式
        将通用格式转换为富途格式
        
        Args:
            symbol: 通用股票代码，如 'AAPL', '00700', '00700.HK'
            
        Returns:
            富途格式代码，如 'US.AAPL', 'HK.00700'
        """
        symbol = symbol.upper().strip()
        
        # 如果已经是富途格式，直接返回
        if '.' in symbol and symbol.split('.')[0] in ['US', 'HK', 'SH', 'SZ']:
            return symbol
        
        # 处理港股
        if symbol.endswith('.HK') or (symbol.isdigit() and len(symbol) == 5):
            code = symbol.replace('.HK', '').zfill(5)
            return f"HK.{code}"
        
        # 处理A股
        if symbol.startswith(('0', '3')):  # 深圳
            return f"SZ.{symbol}"
        elif symbol.startswith(('6', '9')):  # 上海
            return f"SH.{symbol}"
        
        # 默认当作美股处理
        return f"US.{symbol}"
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class FutuTradeService(FutuService):
    """富途交易服务（继承自FutuService）"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 11111, 
                 trade_env: TrdEnv = TrdEnv.SIMULATE):
        """
        初始化交易服务
        
        Args:
            host: 富途OpenD的IP地址
            port: 富途OpenD的端口号
            trade_env: 交易环境（模拟/实盘）
        """
        super().__init__(host, port)
        self.trade_env = trade_env
        self.trade_ctx = None
    
    def connect_trade(self, market: TrdMarket = TrdMarket.HK) -> bool:
        """
        建立交易连接
        
        Args:
            market: 交易市场
            
        Returns:
            连接是否成功
        """
        try:
            if not self._connected:
                if not self.connect():
                    return False
            
            # 建立交易连接
            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=market, 
                host=self.host, 
                port=self.port,
                is_encrypt=True
            )
            
            # 解锁交易
            ret, data = self.trade_ctx.unlock_trade(password_md5="your_password_md5")
            if ret != RET_OK:
                logger.error(f"解锁交易失败: {data}")
                return False
                
            logger.info("富途交易API连接成功")
            return True
            
        except Exception as e:
            logger.error(f"富途交易API连接异常: {e}")
            return False
    
    def get_acc_list(self) -> Dict:
        """获取账户列表"""
        if not self.trade_ctx:
            return {"error": "交易连接未建立"}
        
        try:
            ret, data = self.trade_ctx.get_acc_list()
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                return {"error": f"获取账户列表失败: {data}"}
        except Exception as e:
            return {"error": f"获取账户列表异常: {e}"}
    
    def get_positions(self, acc_id: int) -> Dict:
        """
        获取持仓信息
        
        Args:
            acc_id: 账户ID
            
        Returns:
            持仓信息字典
        """
        if not self.trade_ctx:
            return {"error": "交易连接未建立"}
        
        try:
            ret, data = self.trade_ctx.position_list_query(acc_id=acc_id)
            if ret == RET_OK:
                return {
                    "success": True,
                    "data": data.to_dict('records')
                }
            else:
                return {"error": f"获取持仓失败: {data}"}
        except Exception as e:
            return {"error": f"获取持仓异常: {e}"}
    
    def place_order(self, acc_id: int, code: str, price: float, 
                   qty: int, order_type: OrderType = OrderType.NORMAL,
                   trd_side: TrdSide = TrdSide.BUY) -> Dict:
        """
        下单
        
        Args:
            acc_id: 账户ID
            code: 股票代码
            price: 价格
            qty: 数量
            order_type: 订单类型
            trd_side: 买卖方向
            
        Returns:
            下单结果字典
        """
        if not self.trade_ctx:
            return {"error": "交易连接未建立"}
        
        try:
            ret, data = self.trade_ctx.place_order(
                price=price,
                qty=qty,
                code=code,
                trd_side=trd_side,
                order_type=order_type,
                trd_env=self.trade_env,
                acc_id=acc_id
            )
            
            if ret == RET_OK:
                return {
                    "success": True,
                    "order_id": data['order_id'][0],
                    "data": data.to_dict('records')
                }
            else:
                return {"error": f"下单失败: {data}"}
                
        except Exception as e:
            return {"error": f"下单异常: {e}"}


# 全局富途服务实例
futu_service = FutuService()
futu_trade_service = FutuTradeService()


def get_futu_quote_service() -> FutuService:
    """获取富途行情服务实例"""
    return futu_service


def get_futu_trade_service() -> FutuTradeService:
    """获取富途交易服务实例"""
    return futu_trade_service