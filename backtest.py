import pandas as pd, json
from stock_api.ai_agent import make_decision
from pandas_datareader import data as pdr
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL"]
START, END = "2014-01-01", "2024-12-31"

INIT_CASH = 10_000.0
cash = INIT_CASH
positions = {t: None for t in TICKERS}  # ticker: (shares, cost)
trades = []

# 更灵活的买入条件：只要大趋势向上+MACD金叉即可

def fetch_close(ticker):
    # 1. yfinance
    try:
        df = yf.download(ticker, START, END)["Close"].dropna()
        if not df.empty:
            return df
    except Exception as e:
        print(f"yfinance fail: {ticker} {e}")
    # 2. Stooq
    try:
        df = pdr.DataReader(ticker, "stooq", START, END)["Close"].sort_index()
        if not df.empty:
            return df
    except Exception as e:
        print(f"stooq fail: {ticker} {e}")
    return pd.Series(dtype=float)

def run():
    global cash, positions
    data = {t: fetch_close(t) for t in TICKERS}
    all_dates = sorted(
        set().union(*[set(s.index) for s in data.values() if not s.empty])
    )
    for d in all_dates:
        n_open = sum(positions[t] is not None for t in TICKERS)
        for t, series in data.items():
            if d not in series.index:
                continue
            price_today = series.loc[d]
            hist = series.loc[:d].to_frame("Close")
            hist.reset_index(inplace=True)
            decision, reasons = make_decision(hist)
            # 买入：大趋势向上+MACD金叉+无超买，且当前无持仓
            if positions[t] is None and decision == "BUY":
                # 动态分配剩余现金，最多1/N仓
                alloc = cash / (len(TICKERS) - n_open) if (len(TICKERS) - n_open) > 0 else 0
                shares = alloc // price_today
                if shares:
                    cost = shares * price_today
                    cash -= cost
                    positions[t] = (shares, price_today)
                    trades.append(
                        dict(date=str(d)[:10], action="BUY", ticker=t,
                             price=round(price_today,2), shares=int(shares), cash=round(cash,2), reason=reasons)
                    )
                    n_open += 1
            # 卖出：大趋势向下+MACD死叉 或 RSI超买，且有持仓
            elif positions[t] is not None and (decision == "SELL" or ("RSI" in reasons[-1] and "超买" in reasons[-1])):
                shares, _ = positions[t]
                proceeds = shares * price_today
                cash += proceeds
                trades.append(
                    dict(date=str(d)[:10], action="SELL", ticker=t,
                         price=round(price_today,2), shares=int(shares), cash=round(cash,2), reason=reasons)
                )
                positions[t] = None
                n_open -= 1
    # 收盘强制平仓
    for t, pos in positions.items():
        if pos:
            shares, _ = pos
            last_price = data[t].iloc[-1]
            cash += shares * last_price
            trades.append({
                "date": str(data[t].index[-1])[:10], "action": "SELL",
                "ticker": t, "price": round(last_price,2), "shares": int(shares),
                "cash": round(cash, 2), "reason": ["年末强制平仓"]
            })
            positions[t] = None
    # 统计
    n_buy = sum(1 for tr in trades if tr["action"]=="BUY")
    n_sell = sum(1 for tr in trades if tr["action"]=="SELL")
    win = sum(1 for i,tr in enumerate(trades) if tr["action"]=="SELL" and tr["price"] > trades[i-1]["price"])
    loss = n_sell - win
    print(json.dumps({
        "trades": trades,
        "final_cash": round(cash,2),
        "return_pct": round((cash-INIT_CASH)/INIT_CASH*100,2),
        "n_buy": n_buy, "n_sell": n_sell, "win": win, "loss": loss
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run() 