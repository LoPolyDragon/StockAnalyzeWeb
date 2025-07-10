#!/usr/bin/env python3
"""
用法:
1. 本地启动 API:   python cli.py
                  python cli.py --port 8080
2. 直接查询股票:   python cli.py AAPL
"""
import sys
import json
import uvicorn
import argparse

from stock_api.stock_service import get_stock_data
from stock_api.ai_agent import make_decision
from stock_api.main import app


def run_server(port=8080):
    # 仅监控 `stock_api` 目录，避免虚拟环境(venv)中的包反复触发重载
    uvicorn.run(
        "stock_api.main:app",
        host="0.0.0.0",
        port=port,
    )


def run_cli(ticker: str):
    hist = get_stock_data(ticker, period="5d")
    if hist.empty:
        print("未找到数据")
        return
    
    last_row = hist.iloc[-1]
    decision, reasons = make_decision(hist)
    
    # 获取公司名称
    company_name = ""
    try:
        import yfinance as yf
        ticker_info = yf.Ticker(ticker)
        info = ticker_info.info
        if info and 'longName' in info:
            company_name = info['longName']
        elif info and 'shortName' in info:
            company_name = info['shortName']
    except Exception:
        # 常见股票名称映射
        stock_names = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "AMZN": "Amazon.com, Inc.",
            "GOOGL": "Alphabet Inc.",
            "GOOG": "Alphabet Inc.",
            "META": "Meta Platforms, Inc.",
            "TSLA": "Tesla, Inc.",
            "NVDA": "NVIDIA Corporation",
            "NFLX": "Netflix, Inc.",
            "BABA": "Alibaba Group Holding Limited",
            "9988.HK": "阿里巴巴集团控股有限公司",
            "0700.HK": "腾讯控股有限公司",
            "9999.HK": "网易公司",
            "1810.HK": "小米集团",
            "1815.HK": "小鹏汽车",
            "9618.HK": "京东集团",
            "3690.HK": "美团",
            "9888.HK": "百度集团",
        }
        company_name = stock_names.get(ticker.upper(), "")
    
    print(
        json.dumps(
            {
                "ticker": ticker.upper(),
                "company_name": company_name,
                "current_price": round(last_row["Close"], 2),
                "open": round(last_row["Open"], 2),
                "high": round(last_row["High"], 2),
                "low": round(last_row["Low"], 2),
                "volume": int(last_row["Volume"]),
                "decision": decision,
                "reasons": reasons,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stock AI Advisor CLI')
    parser.add_argument('--port', type=int, default=8080, help='Web服务端口号 (默认: 8080)')
    parser.add_argument('ticker', nargs='?', help='股票代码 (例如: AAPL)')
    
    args = parser.parse_args()
    
    if args.ticker:
        run_cli(args.ticker)
    else:
        print(f"🚀 启动 Stock AI Advisor 服务 (端口: {args.port})...")
        run_server(args.port) 