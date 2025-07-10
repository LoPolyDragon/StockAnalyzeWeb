"""
市场仪表板服务
提供实时市场数据、指数信息、热力图等功能
"""

import logging
import random
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class MarketIndex:
    """市场指数数据结构"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    last_updated: str
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'last_updated': self.last_updated
        }

@dataclass
class SectorData:
    """行业数据结构"""
    sector: str
    name: str
    change_percent: float
    market_cap: float
    stock_count: int
    
    def to_dict(self) -> Dict:
        return {
            'sector': self.sector,
            'name': self.name,
            'change_percent': self.change_percent,
            'market_cap': self.market_cap,
            'stock_count': self.stock_count
        }

@dataclass
class TopStock:
    """热门股票数据结构"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume
        }

class MarketDashboardService:
    """市场仪表板服务"""
    
    def __init__(self):
        # 模拟数据更新时间
        self.last_update = datetime.now()
        self.update_interval = 60  # 60秒更新一次
        
        # 初始化模拟数据
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """初始化模拟数据"""
        # 主要市场指数
        self.market_indices = {
            'SPX': MarketIndex('SPX', 'S&P 500', 4320.45, 12.34, 0.29, 0, datetime.now().isoformat()),
            'NASDAQ': MarketIndex('NASDAQ', 'NASDAQ', 13456.78, -25.67, -0.19, 0, datetime.now().isoformat()),
            'DOW': MarketIndex('DOW', 'Dow Jones', 34567.89, 89.12, 0.26, 0, datetime.now().isoformat()),
            'VIX': MarketIndex('VIX', 'VIX恐慌指数', 18.45, -0.52, -2.74, 0, datetime.now().isoformat())
        }
        
        # 行业数据
        self.sectors = [
            SectorData('technology', '科技', 1.25, 12500000000000, 285),
            SectorData('healthcare', '医疗', 0.67, 4200000000000, 156),
            SectorData('financial', '金融', -0.34, 3800000000000, 198),
            SectorData('consumer', '消费', 0.89, 2900000000000, 142),
            SectorData('energy', '能源', 2.14, 1800000000000, 89),
            SectorData('industrial', '工业', 0.45, 2100000000000, 124),
            SectorData('utilities', '公用事业', -0.12, 950000000000, 67),
            SectorData('materials', '材料', 1.78, 1200000000000, 78)
        ]
        
        # 示例股票池
        self.sample_stocks = [
            # 科技股
            {'symbol': 'AAPL', 'name': '苹果', 'price': 180.50, 'change': 2.30, 'change_percent': 1.29, 'volume': 45231000, 'sector': 'technology'},
            {'symbol': 'MSFT', 'name': '微软', 'price': 335.20, 'change': -1.80, 'change_percent': -0.53, 'volume': 23456000, 'sector': 'technology'},
            {'symbol': 'GOOGL', 'name': '谷歌', 'price': 138.40, 'change': 3.50, 'change_percent': 2.59, 'volume': 31234000, 'sector': 'technology'},
            {'symbol': 'NVDA', 'name': '英伟达', 'price': 450.80, 'change': 12.30, 'change_percent': 2.81, 'volume': 28945000, 'sector': 'technology'},
            {'symbol': 'TSLA', 'name': '特斯拉', 'price': 242.60, 'change': -8.90, 'change_percent': -3.54, 'volume': 42567000, 'sector': 'technology'},
            {'symbol': 'META', 'name': 'Meta', 'price': 295.40, 'change': 5.20, 'change_percent': 1.79, 'volume': 19834000, 'sector': 'technology'},
            
            # 医疗股
            {'symbol': 'JNJ', 'name': '强生', 'price': 163.80, 'change': 0.80, 'change_percent': 0.49, 'volume': 12345000, 'sector': 'healthcare'},
            {'symbol': 'PFE', 'name': '辉瑞', 'price': 29.40, 'change': -0.30, 'change_percent': -1.01, 'volume': 28456000, 'sector': 'healthcare'},
            {'symbol': 'UNH', 'name': '联合健康', 'price': 521.30, 'change': 3.40, 'change_percent': 0.66, 'volume': 3456000, 'sector': 'healthcare'},
            
            # 金融股
            {'symbol': 'JPM', 'name': '摩根大通', 'price': 145.80, 'change': 1.50, 'change_percent': 1.04, 'volume': 15234000, 'sector': 'financial'},
            {'symbol': 'BAC', 'name': '美国银行', 'price': 34.20, 'change': 0.40, 'change_percent': 1.18, 'volume': 42567000, 'sector': 'financial'},
            {'symbol': 'WFC', 'name': '富国银行', 'price': 42.80, 'change': 0.60, 'change_percent': 1.42, 'volume': 23456000, 'sector': 'financial'},
            
            # 消费股
            {'symbol': 'KO', 'name': '可口可乐', 'price': 59.20, 'change': 0.30, 'change_percent': 0.51, 'volume': 12345000, 'sector': 'consumer'},
            {'symbol': 'PG', 'name': '宝洁', 'price': 154.70, 'change': 0.80, 'change_percent': 0.52, 'volume': 6789000, 'sector': 'consumer'},
            {'symbol': 'WMT', 'name': '沃尔玛', 'price': 161.30, 'change': 1.20, 'change_percent': 0.75, 'volume': 9876000, 'sector': 'consumer'},
            
            # 能源股
            {'symbol': 'XOM', 'name': '埃克森美孚', 'price': 102.50, 'change': 3.20, 'change_percent': 3.23, 'volume': 25678000, 'sector': 'energy'},
            {'symbol': 'CVX', 'name': '雪佛龙', 'price': 158.40, 'change': 2.10, 'change_percent': 1.34, 'volume': 15234000, 'sector': 'energy'},
            
            # 工业股
            {'symbol': 'BA', 'name': '波音', 'price': 204.30, 'change': -1.80, 'change_percent': -0.87, 'volume': 6789000, 'sector': 'industrial'},
            {'symbol': 'CAT', 'name': '卡特彼勒', 'price': 256.70, 'change': 1.90, 'change_percent': 0.75, 'volume': 4567000, 'sector': 'industrial'},
        ]
    
    def _add_market_noise(self, base_value: float, volatility: float = 0.02) -> float:
        """为市场数据添加随机波动"""
        noise = random.uniform(-volatility, volatility)
        return base_value * (1 + noise)
    
    def _should_update_data(self) -> bool:
        """检查是否需要更新数据"""
        return (datetime.now() - self.last_update).seconds > self.update_interval
    
    def get_market_indices(self) -> Dict[str, Dict]:
        """获取主要市场指数"""
        if self._should_update_data():
            self._update_market_indices()
        
        return {symbol: index.to_dict() for symbol, index in self.market_indices.items()}
    
    def _update_market_indices(self):
        """更新市场指数数据（模拟实时变化）"""
        for symbol, index in self.market_indices.items():
            # 添加小幅随机变化
            new_price = self._add_market_noise(index.price, 0.005)
            change = new_price - index.price
            change_percent = (change / index.price) * 100
            
            index.price = round(new_price, 2)
            index.change = round(change, 2)
            index.change_percent = round(change_percent, 2)
            index.last_updated = datetime.now().isoformat()
        
        self.last_update = datetime.now()
    
    def get_sector_heatmap(self) -> List[Dict]:
        """获取行业热力图数据"""
        # 添加一些随机变化
        updated_sectors = []
        for sector in self.sectors:
            # 为行业变化添加小幅波动
            new_change = self._add_market_noise(sector.change_percent, 0.3)
            updated_sector = SectorData(
                sector.sector,
                sector.name,
                round(new_change, 2),
                sector.market_cap,
                sector.stock_count
            )
            updated_sectors.append(updated_sector.to_dict())
        
        return updated_sectors
    
    def get_top_gainers(self, limit: int = 5) -> List[Dict]:
        """获取涨幅榜"""
        # 按涨幅排序
        sorted_stocks = sorted(self.sample_stocks, key=lambda x: x['change_percent'], reverse=True)
        
        # 添加一些随机变化
        top_gainers = []
        for stock in sorted_stocks[:limit]:
            # 为涨幅榜股票添加一些变化
            new_change_percent = max(0.1, self._add_market_noise(stock['change_percent'], 0.1))
            new_price = self._add_market_noise(stock['price'], 0.01)
            new_change = new_price * (new_change_percent / 100)
            
            gainer = TopStock(
                stock['symbol'],
                stock['name'],
                round(new_price, 2),
                round(new_change, 2),
                round(new_change_percent, 2),
                stock['volume']
            )
            top_gainers.append(gainer.to_dict())
        
        return top_gainers
    
    def get_top_losers(self, limit: int = 5) -> List[Dict]:
        """获取跌幅榜"""
        # 按跌幅排序
        sorted_stocks = sorted(self.sample_stocks, key=lambda x: x['change_percent'])
        
        # 添加一些随机变化
        top_losers = []
        for stock in sorted_stocks[:limit]:
            # 为跌幅榜股票添加一些变化
            new_change_percent = min(-0.1, self._add_market_noise(stock['change_percent'], 0.1))
            new_price = self._add_market_noise(stock['price'], 0.01)
            new_change = new_price * (new_change_percent / 100)
            
            loser = TopStock(
                stock['symbol'],
                stock['name'],
                round(new_price, 2),
                round(new_change, 2),
                round(new_change_percent, 2),
                stock['volume']
            )
            top_losers.append(loser.to_dict())
        
        return top_losers
    
    def get_volume_leaders(self, limit: int = 5) -> List[Dict]:
        """获取成交量排行"""
        # 按成交量排序
        sorted_stocks = sorted(self.sample_stocks, key=lambda x: x['volume'], reverse=True)
        
        volume_leaders = []
        for stock in sorted_stocks[:limit]:
            # 为成交量添加一些变化
            new_volume = int(self._add_market_noise(stock['volume'], 0.1))
            new_price = self._add_market_noise(stock['price'], 0.01)
            
            leader = TopStock(
                stock['symbol'],
                stock['name'],
                round(new_price, 2),
                stock['change'],
                stock['change_percent'],
                new_volume
            )
            volume_leaders.append(leader.to_dict())
        
        return volume_leaders
    
    def get_market_sentiment(self) -> Dict:
        """获取市场情绪指标"""
        # 模拟市场情绪数据
        vix_value = self.market_indices['VIX'].price
        
        # 恐惧贪婪指数（基于VIX反向计算）
        fear_greed_index = max(0, min(100, 100 - (vix_value - 10) * 4))
        
        # 计算上涨股票比例
        positive_stocks = sum(1 for stock in self.sample_stocks if stock['change_percent'] > 0)
        advance_ratio = (positive_stocks / len(self.sample_stocks)) * 100
        
        # 新高新低比（模拟）
        high_low_ratio = self._add_market_noise(3.2, 0.2)
        
        return {
            'fear_greed_index': round(fear_greed_index, 1),
            'fear_greed_label': self._get_fear_greed_label(fear_greed_index),
            'vix_value': round(vix_value, 2),
            'advance_decline_ratio': round(advance_ratio, 1),
            'high_low_ratio': round(high_low_ratio, 1),
            'market_trend': self._get_market_trend(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fear_greed_label(self, index: float) -> str:
        """根据恐惧贪婪指数返回标签"""
        if index >= 80:
            return "极度贪婪"
        elif index >= 60:
            return "贪婪"
        elif index >= 40:
            return "中性"
        elif index >= 20:
            return "恐惧"
        else:
            return "极度恐惧"
    
    def _get_market_trend(self) -> str:
        """获取市场趋势"""
        sp500_change = self.market_indices['SPX'].change_percent
        nasdaq_change = self.market_indices['NASDAQ'].change_percent
        
        avg_change = (sp500_change + nasdaq_change) / 2
        
        if avg_change > 1:
            return "强势上涨"
        elif avg_change > 0.3:
            return "温和上涨"
        elif avg_change > -0.3:
            return "震荡整理"
        elif avg_change > -1:
            return "温和下跌"
        else:
            return "明显下跌"
    
    def get_comprehensive_dashboard_data(self) -> Dict:
        """获取仪表板综合数据"""
        return {
            'market_indices': self.get_market_indices(),
            'sector_heatmap': self.get_sector_heatmap(),
            'top_gainers': self.get_top_gainers(),
            'top_losers': self.get_top_losers(),
            'volume_leaders': self.get_volume_leaders(),
            'market_sentiment': self.get_market_sentiment(),
            'last_updated': datetime.now().isoformat()
        }

# 创建服务实例
dashboard_service = MarketDashboardService()

# 便捷函数
def get_market_dashboard_data() -> Dict:
    """获取市场仪表板数据的便捷函数"""
    try:
        return dashboard_service.get_comprehensive_dashboard_data()
    except Exception as e:
        logger.error(f"获取市场仪表板数据失败: {e}")
        return {'error': str(e)}

def get_market_indices_data() -> Dict:
    """获取市场指数数据的便捷函数"""
    try:
        return dashboard_service.get_market_indices()
    except Exception as e:
        logger.error(f"获取市场指数数据失败: {e}")
        return {'error': str(e)}

def get_sector_heatmap_data() -> List[Dict]:
    """获取行业热力图数据的便捷函数"""
    try:
        return dashboard_service.get_sector_heatmap()
    except Exception as e:
        logger.error(f"获取行业热力图数据失败: {e}")
        return []