#!/usr/bin/env python3
"""
测试真实新闻服务
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock_api.real_news_service import real_news_service

def test_market_news():
    print("🔍 测试获取市场新闻...")
    try:
        news = real_news_service.get_market_news(5)
        print(f"✅ 成功获取 {len(news)} 条新闻")
        
        for i, item in enumerate(news[:3]):
            print(f"\n📰 新闻 {i+1}:")
            print(f"   标题: {item['title'][:100]}...")
            print(f"   来源: {item['source']}")
            print(f"   链接: {item['url']}")
            print(f"   时间: {item['published_at']}")
            print(f"   情感: {item['sentiment']}")
            
    except Exception as e:
        print(f"❌ 获取市场新闻失败: {e}")

def test_stock_news():
    print("\n🔍 测试获取AAPL股票新闻...")
    try:
        news = real_news_service.get_stock_news('AAPL', 3)
        print(f"✅ 成功获取 {len(news)} 条AAPL新闻")
        
        for i, item in enumerate(news):
            print(f"\n📰 AAPL新闻 {i+1}:")
            print(f"   标题: {item['title'][:100]}...")
            print(f"   来源: {item['source']}")
            print(f"   链接: {item['url']}")
            
    except Exception as e:
        print(f"❌ 获取AAPL新闻失败: {e}")

if __name__ == "__main__":
    test_market_news()
    test_stock_news()