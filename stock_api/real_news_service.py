import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)

class RealNewsService:
    def __init__(self):
        self.rss_feeds = {
            'market': [
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'https://www.cnbc.com/id/10000664/device/rss/rss.html',  # Business news
                'https://www.cnbc.com/id/15839135/device/rss/rss.html',  # Top news
            ],
            'tech': [
                'https://www.cnbc.com/id/19854910/device/rss/rss.html',  # Technology
                'https://www.cnbc.com/id/19746125/device/rss/rss.html',  # Tech companies
            ],
            'finance': [
                'https://www.cnbc.com/id/10000664/device/rss/rss.html',   # Business
                'https://www.cnbc.com/id/100727362/device/rss/rss.html',  # Markets
            ]
        }
        
        # 用户代理列表，避免被封
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # 缓存新闻数据，避免频繁请求
        self.news_cache = {}
        self.cache_expiry = 300  # 5分钟缓存

    def get_headers(self):
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def fetch_rss_feed(self, url: str) -> List[Dict]:
        """获取RSS feed数据"""
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            news_items = []
            for entry in feed.entries[:10]:  # 限制每个feed最多10条新闻
                try:
                    # 解析发布时间
                    published_at = datetime.now().isoformat()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6]).isoformat()
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6]).isoformat()
                    
                    # 获取摘要
                    summary = getattr(entry, 'summary', '')
                    if len(summary) > 200:
                        summary = summary[:200] + '...'
                    
                    # 获取链接
                    link = getattr(entry, 'link', '')
                    
                    news_item = {
                        'title': getattr(entry, 'title', ''),
                        'summary': summary,
                        'url': link,
                        'source': getattr(feed.feed, 'title', 'Unknown'),
                        'published_at': published_at,
                        'sentiment': self._analyze_sentiment(entry.title + ' ' + summary),
                        'sentiment_score': random.uniform(0.3, 0.9),  # 模拟情感分析
                        'tickers': self._extract_tickers(entry.title + ' ' + summary)
                    }
                    
                    if news_item['title'] and news_item['url']:
                        news_items.append(news_item)
                        
                except Exception as e:
                    logger.warning(f"解析新闻条目失败: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"获取RSS feed失败 {url}: {e}")
            return []

    def _analyze_sentiment(self, text: str) -> str:
        """简单的情感分析"""
        positive_words = ['上涨', '增长', '突破', '创新高', '乐观', '强劲', '改善', 'growth', 'up', 'gain', 'high', 'strong', 'positive']
        negative_words = ['下跌', '下降', '担忧', '风险', '困难', '挑战', 'down', 'fall', 'decline', 'concern', 'risk', 'challenge']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return '积极'
        elif negative_count > positive_count:
            return '消极'
        else:
            return '中性'

    def _extract_tickers(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        common_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
            'JNJ', 'PFE', 'UNH', 'CVS', 'ABBV',
            'XOM', 'CVX', 'COP', 'EOG'
        ]
        
        found_tickers = []
        text_upper = text.upper()
        
        for ticker in common_tickers:
            if ticker in text_upper:
                found_tickers.append(ticker)
        
        return found_tickers[:3]  # 最多返回3个股票代码

    def get_market_news(self, limit: int = 20) -> List[Dict]:
        """获取市场新闻"""
        cache_key = f"market_news_{limit}"
        
        # 检查缓存
        if cache_key in self.news_cache:
            cached_data, timestamp = self.news_cache[cache_key]
            if time.time() - timestamp < self.cache_expiry:
                return cached_data
        
        all_news = []
        
        # 获取所有类型的新闻
        for category, feeds in self.rss_feeds.items():
            for feed_url in feeds:
                try:
                    news_items = self.fetch_rss_feed(feed_url)
                    all_news.extend(news_items)
                    time.sleep(1)  # 避免请求过快
                except Exception as e:
                    logger.error(f"获取新闻失败 {feed_url}: {e}")
                    continue
        
        # 去重和排序
        unique_news = []
        seen_titles = set()
        
        for news in all_news:
            title_key = news['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 按时间排序
        unique_news.sort(key=lambda x: x['published_at'], reverse=True)
        
        # 限制数量
        result = unique_news[:limit]
        
        # 缓存结果
        self.news_cache[cache_key] = (result, time.time())
        
        return result

    def get_stock_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """获取特定股票的新闻"""
        # 先获取市场新闻
        market_news = self.get_market_news(50)
        
        # 筛选包含该股票代码的新闻
        stock_news = []
        ticker_upper = ticker.upper()
        
        for news in market_news:
            if ticker_upper in news['tickers'] or ticker_upper in news['title'].upper():
                stock_news.append(news)
        
        # 如果没有找到相关新闻，使用Yahoo Finance的RSS
        if not stock_news:
            try:
                yahoo_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}"
                stock_news = self.fetch_rss_feed(yahoo_url)
            except Exception as e:
                logger.error(f"获取{ticker}新闻失败: {e}")
        
        return stock_news[:limit]

    def get_news_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """按分类获取新闻"""
        if category not in self.rss_feeds:
            return []
        
        all_news = []
        for feed_url in self.rss_feeds[category]:
            try:
                news_items = self.fetch_rss_feed(feed_url)
                all_news.extend(news_items)
                time.sleep(1)
            except Exception as e:
                logger.error(f"获取{category}新闻失败 {feed_url}: {e}")
                continue
        
        # 去重和排序
        unique_news = []
        seen_titles = set()
        
        for news in all_news:
            title_key = news['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['published_at'], reverse=True)
        
        return unique_news[:limit]

# 创建全局实例
real_news_service = RealNewsService()