from typing import Literal
from typing import Tuple
import pandas as pd
import ta


def _calc_indicators(df: pd.DataFrame):
    """Add SMA50, SMA200, RSI14, MACD columns to df inplace."""
    close = df["Close"]
    df["SMA50"] = close.rolling(window=50).mean()
    df["SMA200"] = close.rolling(window=200).mean()
    df["RSI14"] = ta.momentum.rsi(close, window=14, fillna=False)
    macd_line = ta.trend.macd(close, fillna=False)
    signal_line = ta.trend.macd_signal(close, fillna=False)
    df["MACD"] = macd_line
    df["MACD_SIGNAL"] = signal_line


def make_decision(hist: pd.DataFrame) -> Tuple[str, list]:
    """
    结合常见技术指标（SMA50、SMA200、RSI14、MACD）给出决策与详细解释。

    Returns
    -------
    decision: str  (BUY / SELL / HOLD)
    reasons: list[str]
    """
    if hist.empty:
        return "HOLD", ["No historical data available"]

    _calc_indicators(hist)

    row = hist.iloc[-1]
    price = row["Close"]
    sma50 = row["SMA50"]
    sma200 = row["SMA200"]
    rsi = row["RSI14"]
    macd = row["MACD"]
    macd_sig = row["MACD_SIGNAL"]

    reasons = []

    # Trend based on moving averages
    if pd.notna(sma50) and pd.notna(sma200):
        if sma50 > sma200:
            reasons.append("上升趋势：50日均线高于200日均线（黄金交叉）。")
        elif sma50 < sma200:
            reasons.append("下降趋势：50日均线低于200日均线（死亡交叉）。")

    # Price relative to SMA50
    if pd.notna(sma50):
        diff_pct = round((price - sma50) / sma50 * 100, 2)
        reasons.append(f"价格 {diff_pct}% {'高于' if diff_pct>=0 else '低于'} 50-day MA.")

    # RSI interpretation
    if pd.notna(rsi):
        if rsi > 70:
            reasons.append(f"RSI {rsi:.1f} → 超买。")
        elif rsi < 30:
            reasons.append(f"RSI {rsi:.1f} → 超卖。")
        else:
            reasons.append(f"RSI {rsi:.1f} → 中性。")

    # MACD crossover
    if pd.notna(macd) and pd.notna(macd_sig):
        if macd > macd_sig:
            reasons.append("MACD线上穿信号线 → 多头动能。")
        elif macd < macd_sig:
            reasons.append("MACD线下穿信号线 → 空头动能。")

    # Simplified rule-set to decide
    bullish = (
        (pd.notna(sma50) and price > sma50) and
        (pd.notna(rsi) and rsi < 70) and
        (pd.notna(macd) and macd > macd_sig)
    )
    bearish = (
        (pd.notna(sma50) and price < sma50) and
        (pd.notna(rsi) and rsi > 30) and
        (pd.notna(macd) and macd < macd_sig)
    )

    if bullish:
        decision = "BUY"
    elif bearish:
        decision = "SELL"
    else:
        decision = "HOLD"

    return decision, reasons 