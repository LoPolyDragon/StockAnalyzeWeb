import yfinance as yf
import pandas as pd
from pandas_datareader import data as pdr


def get_stock_data(ticker: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    """
    使用 yfinance 抓取股票历史数据
    """
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period=period, interval=interval)

    # 如果 yfinance 返回为空，尝试使用 stooq 作为后备数据源
    if hist.empty:
        try:
            hist = pdr.DataReader(ticker, "stooq")
            hist.sort_index(inplace=True)
        except Exception:
            pass  # 保持 empty，让上层处理

    hist.reset_index(inplace=True)
    return hist 