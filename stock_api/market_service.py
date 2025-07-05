import yfinance as yf
from datetime import datetime, timezone
from typing import List, Dict
from .news_service import get_ticker_news
from .stock_service import get_stock_data
from stock_api.ai_agent import make_decision
import pandas as pd
import random


INDEX_TICKERS = {
    "SPY": "S&P 500",
    "QQQ": "Nasdaq 100",
    "DIA": "Dow Jones",
}

MAJOR_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "META",
    "GOOGL",
]


def _get_price_change(ticker: str):
    data = get_stock_data(ticker, period="30d")
    if data.empty or len(data) < 2:
        return None
    last = data.iloc[-1]
    prev = data.iloc[-2]
    price = round(last["Close"], 2)
    pct = round((last["Close"] - prev["Close"]) / prev["Close"] * 100, 2)
    return price, pct


def get_market_summary() -> Dict:
    # Indices
    indices = []
    for t, name in INDEX_TICKERS.items():
        res = _get_price_change(t)
        if res:
            price, pct = res
            indices.append({"ticker": t, "name": name, "price": price, "pct": pct})

    # Major movers
    movers = []
    for t in MAJOR_TICKERS:
        res = _get_price_change(t)
        if res:
            price, pct = res
            movers.append({"ticker": t, "price": price, "pct": pct})
    gainers = sorted([m for m in movers if m["pct"] > 0], key=lambda x: -x["pct"])[:5]
    losers = sorted([m for m in movers if m["pct"] < 0], key=lambda x: x["pct"])[:5]

    # Market news (use SPY)
    news = get_ticker_news("SPY", limit=8)

    return {
        "indices": indices,
        "gainers": gainers,
        "losers": losers,
        "news": news,
        "updated": datetime.now(timezone.utc).isoformat()
    }

# S&P 500 成分股列表（可用 yfinance 的 sp500 tickers）
def get_sp500_tickers():
    try:
        import requests
        table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        return table["Symbol"].tolist()
    except Exception:
        # fallback: 只用 MAJOR_TICKERS
        return MAJOR_TICKERS


def recommend_top3():
    tickers = get_sp500_tickers()
    results = []
    API_KEY = "QSUOL2TCXDHPANCE"
    from pandas_datareader import data as pdr
    import time
    for t in tickers:
        try:
            # 1. yfinance
            df = yf.download(t, period="6mo", progress=False)[["Close"]].dropna()
            if len(df) < 50:
                # 2. Alpha Vantage fallback
                try:
                    df = pdr.DataReader(t, "av-daily", api_key=API_KEY)["close"]
                    df = df[-126:]  # 6个月大约126个交易日
                except Exception:
                    continue
            if len(df) < 50:
                continue
            hist = df.reset_index()
            decision, reasons = make_decision(hist)
            if decision == "BUY":
                price = df.iloc[-1][0] if isinstance(df, pd.DataFrame) else df.iloc[-1]
                target = round(price * 1.05, 2)
                results.append({
                    "ticker": t,
                    "price": round(price,2),
                    "target": target,
                    "reasons": reasons
                })
            # Alpha Vantage 免费额度有限，防止超限
            if len(results) >= 3:
                break
            time.sleep(1.5)
        except Exception:
            continue
    # 如果不足3只，随机补足
    if len(results) < 3:
        fallback = random.sample(tickers, 3-len(results))
        for t in fallback:
            try:
                df = yf.download(t, period="6mo", progress=False)[["Close"]].dropna()
                if len(df) < 1:
                    try:
                        df = pdr.DataReader(t, "av-daily", api_key=API_KEY)["close"]
                        df = df[-126:]
                    except Exception:
                        continue
                if len(df) < 1:
                    continue
                price = df.iloc[-1][0] if isinstance(df, pd.DataFrame) else df.iloc[-1]
                results.append({
                    "ticker": t,
                    "price": round(price,2),
                    "target": round(price*1.03,2),
                    "reasons": ["数据不足或无买入信号，随机推荐"]
                })
            except Exception:
                continue
    return results[:3] 