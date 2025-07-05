import yfinance as yf
from datetime import datetime, timezone
from typing import List, Dict


def get_ticker_news(ticker: str, limit: int = 8) -> List[Dict]:
    """利用 yfinance 提供的 Yahoo Finance 新闻接口，返回最近新闻列表"""
    try:
        news_items = yf.Ticker(ticker).news or []
    except Exception:
        news_items = []

    cleaned = []
    for item in news_items[:limit]:
        cleaned.append(
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "publisher": item.get("publisher"),
                "time": datetime.fromtimestamp(item.get("providerPublishTime", 0), tz=timezone.utc).isoformat(),
            }
        )
    return cleaned 