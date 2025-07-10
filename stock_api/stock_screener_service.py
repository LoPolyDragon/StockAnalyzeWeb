"""
股票筛选服务
提供多维度的股票筛选功能
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
import time

logger = logging.getLogger(__name__)

@dataclass
class Stock:
    """股票数据结构"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    market_cap: float
    pe_ratio: float
    volume: int
    sector: str
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'volume': self.volume,
            'sector': self.sector
        }

class StockScreenerService:
    """股票筛选服务"""
    
    def __init__(self):
        # 模拟股票数据库
        self.stocks = self._create_sample_stocks()
        
    def _create_sample_stocks(self) -> List[Stock]:
        """创建模拟股票数据"""
        sample_stocks = [
            # 科技股
            Stock("AAPL", "苹果公司", 180.50, 2.30, 1.29, 2800000000000, 28.5, 45231000, "technology"),
            Stock("MSFT", "微软公司", 335.20, -1.80, -0.53, 2500000000000, 32.1, 23456000, "technology"),
            Stock("GOOGL", "谷歌", 138.40, 3.50, 2.59, 1700000000000, 22.8, 31234000, "technology"),
            Stock("NVDA", "英伟达", 450.80, 12.30, 2.81, 1100000000000, 65.2, 28945000, "technology"),
            Stock("TSLA", "特斯拉", 242.60, -8.90, -3.54, 760000000000, 48.3, 42567000, "technology"),
            Stock("META", "Meta", 295.40, 5.20, 1.79, 750000000000, 23.7, 19834000, "technology"),
            Stock("AMZN", "亚马逊", 145.20, 1.80, 1.26, 1500000000000, 45.6, 35678000, "technology"),
            Stock("NFLX", "奈飞", 389.50, -2.40, -0.61, 170000000000, 28.9, 8234000, "technology"),
            
            # 医疗股
            Stock("JNJ", "强生", 163.80, 0.80, 0.49, 420000000000, 15.2, 12345000, "healthcare"),
            Stock("PFE", "辉瑞", 29.40, -0.30, -1.01, 165000000000, 12.8, 28456000, "healthcare"),
            Stock("UNH", "联合健康", 521.30, 3.40, 0.66, 490000000000, 25.1, 3456000, "healthcare"),
            Stock("MRNA", "Moderna", 68.70, 1.20, 1.78, 26000000000, 35.4, 8765000, "healthcare"),
            Stock("ABBV", "艾伯维", 144.50, 0.90, 0.63, 255000000000, 18.7, 5678000, "healthcare"),
            
            # 金融股
            Stock("JPM", "摩根大通", 145.80, 1.50, 1.04, 425000000000, 11.2, 15234000, "financial"),
            Stock("BAC", "美国银行", 34.20, 0.40, 1.18, 275000000000, 12.5, 42567000, "financial"),
            Stock("WFC", "富国银行", 42.80, 0.60, 1.42, 160000000000, 10.8, 23456000, "financial"),
            Stock("GS", "高盛", 358.90, 2.30, 0.65, 120000000000, 13.4, 3456000, "financial"),
            Stock("MS", "摩根士丹利", 87.60, 1.10, 1.27, 145000000000, 14.2, 8765000, "financial"),
            
            # 消费股
            Stock("KO", "可口可乐", 59.20, 0.30, 0.51, 256000000000, 24.6, 12345000, "consumer"),
            Stock("PG", "宝洁", 154.70, 0.80, 0.52, 365000000000, 26.8, 6789000, "consumer"),
            Stock("WMT", "沃尔玛", 161.30, 1.20, 0.75, 440000000000, 27.3, 9876000, "consumer"),
            Stock("MCD", "麦当劳", 281.40, 1.60, 0.57, 205000000000, 32.1, 4567000, "consumer"),
            Stock("NKE", "耐克", 103.80, -0.90, -0.86, 160000000000, 28.4, 7890000, "consumer"),
            
            # 能源股
            Stock("XOM", "埃克森美孚", 102.50, 3.20, 3.23, 420000000000, 13.5, 25678000, "energy"),
            Stock("CVX", "雪佛龙", 158.40, 2.10, 1.34, 295000000000, 14.7, 15234000, "energy"),
            Stock("COP", "康菲石油", 113.80, 2.80, 2.52, 145000000000, 12.3, 8765000, "energy"),
            
            # 工业股
            Stock("BA", "波音", 204.30, -1.80, -0.87, 120000000000, 38.2, 6789000, "industrial"),
            Stock("CAT", "卡特彼勒", 256.70, 1.90, 0.75, 135000000000, 16.8, 4567000, "industrial"),
            Stock("HON", "霍尼韦尔", 191.20, 0.70, 0.37, 128000000000, 24.1, 3456000, "industrial"),
            Stock("GE", "通用电气", 115.40, 2.30, 2.03, 125000000000, 19.6, 12345000, "industrial"),
        ]
        
        return sample_stocks
    
    def screen_stocks(self, filters: Dict) -> List[Stock]:
        """根据筛选条件筛选股票"""
        try:
            results = self.stocks.copy()
            
            # 市值筛选
            if filters.get('market_cap'):
                results = self._filter_by_market_cap(results, filters['market_cap'])
            
            # 市盈率筛选
            if filters.get('pe_ratio'):
                results = self._filter_by_pe_ratio(results, filters['pe_ratio'])
            
            # 涨跌幅筛选
            if filters.get('price_change'):
                results = self._filter_by_price_change(results, filters['price_change'])
            
            # 成交量筛选
            if filters.get('volume'):
                results = self._filter_by_volume(results, filters['volume'])
            
            # 行业筛选
            if filters.get('sector'):
                results = self._filter_by_sector(results, filters['sector'])
            
            # 排序
            if filters.get('sort_by'):
                results = self._sort_stocks(results, filters['sort_by'])
            
            logger.info(f"股票筛选完成，找到{len(results)}只股票")
            return results
            
        except Exception as e:
            logger.error(f"股票筛选失败: {e}")
            return []
    
    def _filter_by_market_cap(self, stocks: List[Stock], market_cap_filter: str) -> List[Stock]:
        """按市值筛选"""
        if market_cap_filter == 'large':
            return [s for s in stocks if s.market_cap > 500000000000]  # >5000亿
        elif market_cap_filter == 'mid':
            return [s for s in stocks if 50000000000 <= s.market_cap <= 500000000000]  # 500-5000亿
        elif market_cap_filter == 'small':
            return [s for s in stocks if s.market_cap < 50000000000]  # <500亿
        return stocks
    
    def _filter_by_pe_ratio(self, stocks: List[Stock], pe_filter: str) -> List[Stock]:
        """按市盈率筛选"""
        if pe_filter == 'low':
            return [s for s in stocks if s.pe_ratio < 15]
        elif pe_filter == 'medium':
            return [s for s in stocks if 15 <= s.pe_ratio <= 30]
        elif pe_filter == 'high':
            return [s for s in stocks if s.pe_ratio > 30]
        return stocks
    
    def _filter_by_price_change(self, stocks: List[Stock], change_filter: str) -> List[Stock]:
        """按涨跌幅筛选"""
        if change_filter == 'up5':
            return [s for s in stocks if s.change_percent > 5]
        elif change_filter == 'up2':
            return [s for s in stocks if s.change_percent > 2]
        elif change_filter == 'down2':
            return [s for s in stocks if s.change_percent < -2]
        elif change_filter == 'down5':
            return [s for s in stocks if s.change_percent < -5]
        return stocks
    
    def _filter_by_volume(self, stocks: List[Stock], volume_filter: str) -> List[Stock]:
        """按成交量筛选"""
        # 计算成交量分位数
        volumes = [s.volume for s in stocks]
        volumes.sort()
        
        high_threshold = volumes[int(len(volumes) * 0.7)]  # 70分位数
        low_threshold = volumes[int(len(volumes) * 0.3)]   # 30分位数
        
        if volume_filter == 'high':
            return [s for s in stocks if s.volume > high_threshold]
        elif volume_filter == 'medium':
            return [s for s in stocks if low_threshold <= s.volume <= high_threshold]
        elif volume_filter == 'low':
            return [s for s in stocks if s.volume < low_threshold]
        return stocks
    
    def _filter_by_sector(self, stocks: List[Stock], sector_filter: str) -> List[Stock]:
        """按行业筛选"""
        return [s for s in stocks if s.sector == sector_filter]
    
    def _sort_stocks(self, stocks: List[Stock], sort_by: str) -> List[Stock]:
        """股票排序"""
        if sort_by == 'marketCap':
            return sorted(stocks, key=lambda s: s.market_cap, reverse=True)
        elif sort_by == 'priceChange':
            return sorted(stocks, key=lambda s: s.change_percent, reverse=True)
        elif sort_by == 'volume':
            return sorted(stocks, key=lambda s: s.volume, reverse=True)
        elif sort_by == 'pe':
            return sorted(stocks, key=lambda s: s.pe_ratio)
        return stocks
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根据股票代码获取股票信息"""
        for stock in self.stocks:
            if stock.symbol == symbol:
                return stock
        return None
    
    def get_top_stocks(self, sort_by: str = 'marketCap', limit: int = 10) -> List[Stock]:
        """获取热门股票"""
        sorted_stocks = self._sort_stocks(self.stocks, sort_by)
        return sorted_stocks[:limit]
    
    def get_sectors_summary(self) -> Dict:
        """获取行业概况"""
        sectors = {}
        for stock in self.stocks:
            sector = stock.sector
            if sector not in sectors:
                sectors[sector] = {
                    'count': 0,
                    'avg_change': 0,
                    'total_market_cap': 0,
                    'stocks': []
                }
            
            sectors[sector]['count'] += 1
            sectors[sector]['avg_change'] += stock.change_percent
            sectors[sector]['total_market_cap'] += stock.market_cap
            sectors[sector]['stocks'].append(stock.symbol)
        
        # 计算平均值
        for sector_data in sectors.values():
            if sector_data['count'] > 0:
                sector_data['avg_change'] /= sector_data['count']
                sector_data['avg_change'] = round(sector_data['avg_change'], 2)
                sector_data['total_market_cap'] = round(sector_data['total_market_cap'] / 1000000000, 2)  # 转换为十亿
        
        return sectors

# 创建服务实例
screener_service = StockScreenerService()

# 便捷函数
def screen_stocks(filters: Dict) -> List[Dict]:
    """股票筛选便捷函数"""
    try:
        stocks = screener_service.screen_stocks(filters)
        return [stock.to_dict() for stock in stocks]
    except Exception as e:
        logger.error(f"股票筛选失败: {e}")
        return []

def get_stock_info(symbol: str) -> Dict:
    """获取股票信息便捷函数"""
    try:
        stock = screener_service.get_stock_by_symbol(symbol)
        if stock:
            return stock.to_dict()
        return {}
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        return {}

def get_top_stocks(sort_by: str = 'marketCap', limit: int = 10) -> List[Dict]:
    """获取热门股票便捷函数"""
    try:
        stocks = screener_service.get_top_stocks(sort_by, limit)
        return [stock.to_dict() for stock in stocks]
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        return []

def get_sectors_summary() -> Dict:
    """获取行业概况便捷函数"""
    try:
        return screener_service.get_sectors_summary()
    except Exception as e:
        logger.error(f"获取行业概况失败: {e}")
        return {}