from pydantic import BaseModel


class StockResponse(BaseModel):
    ticker: str
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    decision: str
    reasons: list[str]
    history: list[dict]  # 每日 {date, close} 列表 