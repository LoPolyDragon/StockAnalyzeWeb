from typing import Literal
from typing import Tuple
import pandas as pd
import ta


def _calc_indicators(df: pd.DataFrame):
    """Add SMA20, SMA50, SMA200, RSI14, MACD columns to df inplace."""
    close = df["Close"]
    df["SMA20"] = close.rolling(window=20).mean()
    df["SMA50"] = close.rolling(window=50).mean()
    df["SMA200"] = close.rolling(window=200).mean()
    df["RSI14"] = ta.momentum.rsi(close, window=14, fillna=False)
    macd_line = ta.trend.macd(close, fillna=False)
    signal_line = ta.trend.macd_signal(close, fillna=False)
    df["MACD"] = macd_line
    df["MACD_SIGNAL"] = signal_line
    df["MACD_HIST"] = ta.trend.macd_diff(close, fillna=False)
    if "Volume" in df:
        df["VOL_MA20"] = df["Volume"].rolling(window=20).mean()


def make_decision(hist: pd.DataFrame) -> Tuple[str, list]:
    """
    升级版策略：
    - SMA20/50/200 均线金叉死叉
    - RSI 超买超卖
    - MACD 金叉死叉+柱状动能
    - 成交量突破
    - 仅顺大趋势做多/做空
    """
    if hist.empty:
        return "HOLD", ["无历史数据"]

    _calc_indicators(hist)
    row = hist.iloc[-1]
    price = row["Close"]
    sma20 = row.get("SMA20")
    sma50 = row.get("SMA50")
    sma200 = row.get("SMA200")
    rsi = row.get("RSI14")
    macd = row.get("MACD")
    macd_sig = row.get("MACD_SIGNAL")
    macd_hist = row.get("MACD_HIST")
    vol = row.get("Volume")
    vol_ma20 = row.get("VOL_MA20")

    reasons = []
    # 趋势过滤器
    if pd.notna(sma50) and pd.notna(sma200):
        if sma50 > sma200:
            reasons.append("大趋势向上：50日均线高于200日均线（黄金交叉）")
            trend = "UP"
        elif sma50 < sma200:
            reasons.append("大趋势向下：50日均线低于200日均线（死亡交叉）")
            trend = "DOWN"
        else:
            trend = None
    else:
        trend = None

    # 均线短线信号
    if pd.notna(sma20) and pd.notna(sma50):
        if sma20 > sma50:
            reasons.append("短线多头：20日均线高于50日均线")
        elif sma20 < sma50:
            reasons.append("短线空头：20日均线低于50日均线")

    # RSI
    if pd.notna(rsi):
        if rsi > 70:
            reasons.append(f"RSI {rsi:.1f} → 超买，警惕回调")
        elif rsi < 30:
            reasons.append(f"RSI {rsi:.1f} → 超卖，可能反弹")
        else:
            reasons.append(f"RSI {rsi:.1f} → 中性")

    # MACD
    if pd.notna(macd) and pd.notna(macd_sig):
        if macd > macd_sig and pd.notna(macd_hist) and macd_hist > 0:
            reasons.append("MACD金叉且柱状图为正 → 多头动能增强")
        elif macd < macd_sig and pd.notna(macd_hist) and macd_hist < 0:
            reasons.append("MACD死叉且柱状图为负 → 空头动能增强")
        else:
            reasons.append("MACD无明显方向")

    # 成交量突破
    if pd.notna(vol) and pd.notna(vol_ma20):
        if vol > 1.5 * vol_ma20:
            reasons.append("今日成交量大幅放大，主力异动")

    # 组合决策
    buy = (
        trend == "UP"
        and pd.notna(sma20) and pd.notna(sma50) and sma20 > sma50
        and pd.notna(macd) and pd.notna(macd_sig) and macd > macd_sig 
        and pd.notna(macd_hist) and macd_hist > 0
        and (pd.isna(rsi) or rsi < 70)
    )
    sell = (
        trend == "DOWN"
        and pd.notna(sma20) and pd.notna(sma50) and sma20 < sma50
        and pd.notna(macd) and pd.notna(macd_sig) and macd < macd_sig 
        and pd.notna(macd_hist) and macd_hist < 0
        and (pd.isna(rsi) or rsi > 30)
    )
    if buy:
        decision = "BUY"
        reasons.append("【买入信号】大趋势向上+短线金叉+MACD金叉+无超买")
    elif sell:
        decision = "SELL"
        reasons.append("【卖出信号】大趋势向下+短线死叉+MACD死叉+无超卖")
    else:
        decision = "HOLD"
        reasons.append("【观望】信号不一致或震荡区间")
    return decision, reasons 