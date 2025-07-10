"""
增强新闻服务 - 集成多个免费美股新闻API
"""

import requests
import feedparser
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """新闻项目数据结构"""
    title: str
    summary: str
    url: str
    source: str
    published_at: str
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    tickers: List[str] = None
    
    def __post_init__(self):
        if self.tickers is None:
            self.tickers = []

class EnhancedNewsService:
    """增强新闻服务，集成多个免费新闻源"""
    
    def __init__(self):
        # API配置
        self.apis = {
            'alpha_vantage': {
                'api_key': 'QSUOL2TCXDHPANCE',  # 你项目中已有的key
                'base_url': 'https://www.alphavantage.co/query',
                'daily_limit': 25,
                'current_usage': 0,
                'last_reset': datetime.now().date()
            },
            'newsapi': {
                'api_key': 'YOUR_NEWSAPI_KEY',  # 需要注册获取
                'base_url': 'https://newsapi.org/v2/everything',
                'daily_limit': 100,
                'current_usage': 0,
                'last_reset': datetime.now().date()
            },
            'finnhub': {
                'api_key': 'YOUR_FINNHUB_KEY',  # 需要注册获取
                'base_url': 'https://finnhub.io/api/v1/company-news',
                'minute_limit': 60,
                'current_usage': 0,
                'last_reset': datetime.now().minute
            },
            'marketaux': {
                'api_key': 'YOUR_MARKETAUX_KEY',  # 需要注册获取
                'base_url': 'https://api.marketaux.com/v1/news/all',
                'daily_limit': 200,
                'current_usage': 0,
                'last_reset': datetime.now().date()
            }
        }
        
        # Yahoo Finance RSS feeds
        self.yahoo_rss_feeds = {
            'general': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'markets': 'https://feeds.finance.yahoo.com/rss/2.0/category-markets',
            'tech': 'https://feeds.finance.yahoo.com/rss/2.0/category-technology',
            'earnings': 'https://feeds.finance.yahoo.com/rss/2.0/category-earnings'
        }
        
        # 缓存
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
        
    def _check_rate_limit(self, api_name: str) -> bool:
        """检查API调用限制"""
        api_config = self.apis.get(api_name)
        if not api_config:
            return False
            
        now = datetime.now()
        
        # 重置计数器
        if api_name == 'finnhub':
            if now.minute != api_config['last_reset']:
                api_config['current_usage'] = 0
                api_config['last_reset'] = now.minute
        else:
            if now.date() != api_config['last_reset']:
                api_config['current_usage'] = 0
                api_config['last_reset'] = now.date()
        
        # 检查是否超限
        limit_key = 'minute_limit' if api_name == 'finnhub' else 'daily_limit'
        return api_config['current_usage'] < api_config[limit_key]
    
    def _increment_usage(self, api_name: str):
        """增加API使用计数"""
        if api_name in self.apis:
            self.apis[api_name]['current_usage'] += 1
    
    def get_news_from_alpha_vantage(self, ticker: str = None, limit: int = 10) -> List[NewsItem]:
        """从Alpha Vantage获取新闻"""
        if not self._check_rate_limit('alpha_vantage'):
            logger.warning("Alpha Vantage API达到限制")
            return []
        
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.apis['alpha_vantage']['api_key'],
                'limit': limit
            }
            
            if ticker:
                params['tickers'] = ticker
            
            response = requests.get(self.apis['alpha_vantage']['base_url'], params=params)
            response.raise_for_status()
            
            self._increment_usage('alpha_vantage')
            
            data = response.json()
            news_items = []
            
            if 'feed' in data:
                for item in data['feed']:
                    news_item = NewsItem(
                        title=item.get('title', ''),
                        summary=item.get('summary', ''),
                        url=item.get('url', ''),
                        source=item.get('source', 'Alpha Vantage'),
                        published_at=item.get('time_published', ''),
                        sentiment=self._convert_sentiment_score(item.get('overall_sentiment_score', 0)),
                        sentiment_score=float(item.get('overall_sentiment_score', 0)),
                        tickers=[t['ticker'] for t in item.get('ticker_sentiment', [])]
                    )
                    news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取Alpha Vantage新闻失败: {e}")
            return []
    
    def get_news_from_newsapi(self, query: str = "stock market", limit: int = 10) -> List[NewsItem]:
        """从NewsAPI获取新闻"""
        if not self._check_rate_limit('newsapi'):
            logger.warning("NewsAPI达到限制")
            return []
        
        try:
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.apis['newsapi']['api_key'],
                'domains': 'reuters.com,bloomberg.com,marketwatch.com,cnbc.com,wsj.com'
            }
            
            response = requests.get(self.apis['newsapi']['base_url'], params=params)
            response.raise_for_status()
            
            self._increment_usage('newsapi')
            
            data = response.json()
            news_items = []
            
            if 'articles' in data:
                for article in data['articles']:
                    news_item = NewsItem(
                        title=article.get('title', ''),
                        summary=article.get('description', ''),
                        url=article.get('url', ''),
                        source=article.get('source', {}).get('name', 'NewsAPI'),
                        published_at=article.get('publishedAt', ''),
                        tickers=self._extract_tickers(article.get('title', '') + ' ' + article.get('description', ''))
                    )
                    news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取NewsAPI新闻失败: {e}")
            return []
    
    def get_news_from_finnhub(self, ticker: str) -> List[NewsItem]:
        """从Finnhub获取特定股票新闻"""
        if not self._check_rate_limit('finnhub'):
            logger.warning("Finnhub API达到限制")
            return []
        
        try:
            from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = datetime.now()
            
            params = {
                'symbol': ticker,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.apis['finnhub']['api_key']
            }
            
            response = requests.get(self.apis['finnhub']['base_url'], params=params)
            response.raise_for_status()
            
            self._increment_usage('finnhub')
            
            data = response.json()
            news_items = []
            
            for item in data:
                news_item = NewsItem(
                    title=item.get('headline', ''),
                    summary=item.get('summary', ''),
                    url=item.get('url', ''),
                    source=item.get('source', 'Finnhub'),
                    published_at=datetime.fromtimestamp(item.get('datetime', 0)).isoformat(),
                    tickers=[ticker]
                )
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取Finnhub新闻失败: {e}")
            return []
    
    def get_news_from_marketaux(self, ticker: str = None, limit: int = 10) -> List[NewsItem]:
        """从Marketaux获取新闻"""
        if not self._check_rate_limit('marketaux'):
            logger.warning("Marketaux API达到限制")
            return []
        
        try:
            params = {
                'api_token': self.apis['marketaux']['api_key'],
                'limit': limit,
                'language': 'en'
            }
            
            if ticker:
                params['symbols'] = ticker
            
            response = requests.get(self.apis['marketaux']['base_url'], params=params)
            response.raise_for_status()
            
            self._increment_usage('marketaux')
            
            data = response.json()
            news_items = []
            
            if 'data' in data:
                for item in data['data']:
                    news_item = NewsItem(
                        title=item.get('title', ''),
                        summary=item.get('description', ''),
                        url=item.get('url', ''),
                        source=item.get('source', 'Marketaux'),
                        published_at=item.get('published_at', ''),
                        sentiment=item.get('sentiment', ''),
                        tickers=item.get('entities', [])
                    )
                    news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取Marketaux新闻失败: {e}")
            return []
    
    def get_news_from_yahoo_rss(self, category: str = 'general', limit: int = 10) -> List[NewsItem]:
        """从Yahoo Finance RSS获取新闻"""
        try:
            if category not in self.yahoo_rss_feeds:
                category = 'general'
            
            feed_url = self.yahoo_rss_feeds[category]
            feed = feedparser.parse(feed_url)
            
            news_items = []
            
            for entry in feed.entries[:limit]:
                news_item = NewsItem(
                    title=entry.get('title', ''),
                    summary=entry.get('summary', ''),
                    url=entry.get('link', ''),
                    source='Yahoo Finance',
                    published_at=entry.get('published', ''),
                    tickers=self._extract_tickers(entry.get('title', '') + ' ' + entry.get('summary', ''))
                )
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取Yahoo RSS新闻失败: {e}")
            return []
    
    def get_comprehensive_news(self, ticker: str = None, limit: int = 20) -> List[NewsItem]:
        """获取综合新闻，整合多个来源"""
        cache_key = f"comprehensive_news_{ticker}_{limit}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        all_news = []
        
        # 从多个源获取新闻
        try:
            # Alpha Vantage（优先，有情感分析）
            alpha_news = self.get_news_from_alpha_vantage(ticker, limit//4)
            all_news.extend(alpha_news)
            
            # Yahoo RSS（免费，稳定）
            yahoo_news = self.get_news_from_yahoo_rss('general', limit//4)
            all_news.extend(yahoo_news)
            
            # Finnhub（如果有特定ticker）
            if ticker:
                finnhub_news = self.get_news_from_finnhub(ticker)
                all_news.extend(finnhub_news)
            
            # NewsAPI（如果有API key）
            if self.apis['newsapi']['api_key'] != 'YOUR_NEWSAPI_KEY':
                query = f"{ticker} stock" if ticker else "stock market"
                newsapi_news = self.get_news_from_newsapi(query, limit//4)
                all_news.extend(newsapi_news)
            
            # Marketaux（如果有API key）
            if self.apis['marketaux']['api_key'] != 'YOUR_MARKETAUX_KEY':
                marketaux_news = self.get_news_from_marketaux(ticker, limit//4)
                all_news.extend(marketaux_news)
            
        except Exception as e:
            logger.error(f"获取综合新闻失败: {e}")
        
        # 去重和排序
        unique_news = self._deduplicate_news(all_news)
        sorted_news = sorted(unique_news, key=lambda x: x.published_at, reverse=True)
        
        # 缓存结果
        self.cache[cache_key] = (time.time(), sorted_news[:limit])
        
        return sorted_news[:limit]
    
    def _deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """去重新闻"""
        seen_titles = set()
        unique_news = []
        
        for item in news_items:
            title_key = item.title.lower().strip()
            if title_key not in seen_titles and title_key:
                seen_titles.add(title_key)
                unique_news.append(item)
        
        return unique_news
    
    def _extract_tickers(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        # 常见股票代码模式
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_tickers = re.findall(ticker_pattern, text)
        
        # 常见股票代码列表（可以扩展）
        known_tickers = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'BRK.B', 'JNJ', 'JPM', 'UNH', 'V', 'PG', 'MA', 'HD', 'DIS',
            'ADBE', 'NFLX', 'CRM', 'CMCSA', 'PEP', 'ABBV', 'KO', 'TMO',
            'COST', 'ABT', 'AVGO', 'ACN', 'DHR', 'TXN', 'NEE', 'XOM',
            'LLY', 'QCOM', 'WMT', 'MDT', 'BMY', 'HON', 'UPS', 'LOW',
            'ORCL', 'IBM', 'INTC', 'AMD', 'CISCO', 'PYPL', 'UBER', 'LYFT'
        }
        
        # 过滤出真正的股票代码
        tickers = [ticker for ticker in potential_tickers if ticker in known_tickers]
        
        return list(set(tickers))  # 去重
    
    def _convert_sentiment_score(self, score: float) -> str:
        """将情感分数转换为文字"""
        if score > 0.15:
            return "积极"
        elif score < -0.15:
            return "消极"
        else:
            return "中性"
    
    def get_api_status(self) -> Dict:
        """获取API使用状态"""
        status = {}
        for api_name, config in self.apis.items():
            limit_key = 'minute_limit' if api_name == 'finnhub' else 'daily_limit'
            status[api_name] = {
                'current_usage': config['current_usage'],
                'limit': config[limit_key],
                'available': config[limit_key] - config['current_usage']
            }
        return status

# 创建服务实例
enhanced_news_service = EnhancedNewsService()

# 便捷函数
def get_stock_news(ticker: str, limit: int = 10) -> List[Dict]:
    """获取股票新闻的便捷函数"""
    try:
        news_items = enhanced_news_service.get_comprehensive_news(ticker, limit)
        return [
            {
                'title': item.title,
                'summary': item.summary,
                'url': item.url,
                'source': item.source,
                'published_at': item.published_at,
                'sentiment': item.sentiment,
                'sentiment_score': item.sentiment_score,
                'tickers': item.tickers
            }
            for item in news_items
        ]
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        return []

def get_market_news(limit: int = 20) -> List[Dict]:
    """获取市场新闻的便捷函数"""
    try:
        news_items = enhanced_news_service.get_comprehensive_news(None, limit)
        return [
            {
                'title': item.title,
                'summary': item.summary,
                'url': item.url,
                'source': item.source,
                'published_at': item.published_at,
                'sentiment': item.sentiment,
                'sentiment_score': item.sentiment_score,
                'tickers': item.tickers
            }
            for item in news_items
        ]
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        return []