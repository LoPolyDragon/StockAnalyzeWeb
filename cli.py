#!/usr/bin/env python3
"""
用法:
1. 本地启动 API:   python cli.py
2. 直接查询股票:   python cli.py AAPL
"""
import sys
import json
import uvicorn

from stock_api.stock_service import get_stock_data
from stock_api.ai_agent import make_decision
from stock_api.main import app


def run_server():
    # 仅监控 `stock_api` 目录，避免虚拟环境(venv)中的包反复触发重载
    uvicorn.run(
        "stock_api.main:app",
        host="0.0.0.0",
        port=8000,
    )


def run_cli(ticker: str):
    hist = get_stock_data(ticker, period="5d")
    if hist.empty:
        print("未找到数据")
        return
    last_row = hist.iloc[-1]
    decision, reasons = make_decision(hist)
    print(
        json.dumps(
            {
                "ticker": ticker.upper(),
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
    if len(sys.argv) == 1:
        run_server()
    else:
        run_cli(sys.argv[1]) 