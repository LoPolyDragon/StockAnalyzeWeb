import yfinance as yf
import pandas as pd
from pandas_datareader import data as pdr
import time
import logging
from typing import Optional
from functools import wraps

# 配置日志
logger = logging.getLogger(__name__)

# 简单内存缓存
_cache = {}
_cache_timeout = 300  # 5分钟缓存
_last_request_time = 0
_min_request_interval = 2.0  # 最小请求间隔（秒）


def with_retry(max_retries: int = 3, delay: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global _last_request_time
            last_exception = None
            for attempt in range(max_retries):
                try:
                    # 确保请求间隔
                    current_time = time.time()
                    time_since_last_request = current_time - _last_request_time
                    if time_since_last_request < _min_request_interval:
                        time.sleep(_min_request_interval - time_since_last_request)
                    
                    result = func(*args, **kwargs)
                    _last_request_time = time.time()
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # 指数退避
                        logger.warning(f"尝试 {attempt + 1} 失败: {e}, {wait_time}秒后重试...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"所有重试都失败: {e}")
            raise last_exception
        return wrapper
    return decorator


def _get_cache_key(ticker: str, period: str) -> str:
    """生成缓存键"""
    return f"{ticker.upper()}_{period}"


def _get_from_cache(cache_key: str) -> Optional[pd.DataFrame]:
    """从缓存获取数据"""
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < _cache_timeout:
            logger.info(f"从缓存获取数据: {cache_key}")
            return data.copy()
        else:
            # 缓存过期，删除
            del _cache[cache_key]
    return None


def _save_to_cache(cache_key: str, data: pd.DataFrame):
    """保存数据到缓存"""
    _cache[cache_key] = (data.copy(), time.time())
    logger.info(f"数据已缓存: {cache_key}")


@with_retry(max_retries=3, delay=2.0)
def _fetch_from_yfinance(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """从yfinance获取数据"""
    logger.info(f"从yfinance获取数据: {ticker}, period={period}, interval={interval}")
    try:
        yf.pdr_override()  # 使用pandas_datareader作为备用
        hist = pdr.get_data_yahoo(ticker, period=period, interval=interval)
        
        if hist.empty:
            raise ValueError(f"yfinance返回空数据: {ticker}")
        
        return hist
    except Exception as e:
        logger.error(f"yfinance获取失败: {e}")
        # 尝试直接使用yfinance作为备用
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=period, interval=interval, timeout=20)
        
        if hist.empty:
            raise ValueError(f"yfinance备用方法也返回空数据: {ticker}")
        
        return hist


@with_retry(max_retries=2, delay=3.0)
def _fetch_from_stooq(ticker: str) -> pd.DataFrame:
    """从stooq获取数据作为备用"""
    logger.info(f"从stooq获取备用数据: {ticker}")
    try:
        hist = pdr.DataReader(ticker, "stooq")
        
        if hist.empty:
            raise ValueError(f"stooq返回空数据: {ticker}")
        
        hist.sort_index(inplace=True)
        return hist
    except Exception as e:
        logger.error(f"stooq获取失败: {e}")
        raise


def get_stock_data(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    增强版股票数据获取：重试机制 + 缓存 + 多数据源备用
    """
    # 参数验证
    if not ticker or not ticker.strip():
        raise ValueError("股票代码不能为空")
    
    ticker = ticker.upper().strip()
    cache_key = _get_cache_key(ticker, period)
    
    # 尝试从缓存获取
    cached_data = _get_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # 自动匹配 interval
    period_interval_map = {
        "1d": "5m",
        "5d": "15m", 
        "1wk": "30m",
        "1mo": "1h",
        "3mo": "1d",
        "6mo": "1d",
        "ytd": "1d",
        "1y": "1d",
        "2y": "1wk",
        "5y": "1wk",
        "10y": "1mo",
        "max": "1mo"
    }
    interval = period_interval_map.get(period, "1d")
    
    hist = None
    errors = []
    
    # 主数据源：yfinance
    try:
        hist = _fetch_from_yfinance(ticker, period, interval)
        logger.info(f"成功从yfinance获取 {ticker} 数据，共 {len(hist)} 条记录")
    except Exception as e:
        errors.append(f"yfinance: {str(e)}")
        logger.warning(f"yfinance获取失败: {e}")
    
    # 备用数据源：stooq (仅当主数据源失败时)
    if hist is None or hist.empty:
        try:
            hist = _fetch_from_stooq(ticker)
            logger.info(f"成功从stooq获取 {ticker} 备用数据，共 {len(hist)} 条记录")
        except Exception as e:
            errors.append(f"stooq: {str(e)}")
            logger.warning(f"stooq备用数据源也失败: {e}")
    
    # 如果所有数据源都失败
    if hist is None or hist.empty:
        error_msg = " | ".join(errors)
        logger.error(f"所有数据源都无法获取 {ticker} 的数据: {error_msg}")
        return pd.DataFrame()  # 返回空DataFrame
    
    # 数据清理和验证
    try:
        # 确保必要的列存在
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in hist.columns]
        if missing_columns:
            logger.error(f"数据缺少必要列: {missing_columns}")
            return pd.DataFrame()
        
        # 删除包含NaN的行
        hist = hist.dropna(subset=required_columns)
        
        # 确保数据类型正确
        for col in ['Open', 'High', 'Low', 'Close']:
            hist[col] = pd.to_numeric(hist[col], errors='coerce')
        hist['Volume'] = pd.to_numeric(hist['Volume'], errors='coerce').fillna(0).astype(int)
        
        # 过滤无效数据（价格为0或负数）
        hist = hist[hist['Close'] > 0]
        
        if hist.empty:
            logger.error(f"数据清理后无有效数据: {ticker}")
            return pd.DataFrame()
        
        # 重置索引
        hist.reset_index(inplace=True)
        
        # 缓存成功获取的数据
        _save_to_cache(cache_key, hist)
        
        logger.info(f"成功获取并处理 {ticker} 数据，最终 {len(hist)} 条有效记录")
        return hist
        
    except Exception as e:
        logger.error(f"数据处理失败: {e}")
        return pd.DataFrame() 