from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from .schemas import StockResponse
from .stock_service import get_stock_data
from .ai_agent import make_decision

app = FastAPI(title="Stock AI Advisor API", version="0.1.0")

# 配置模板目录
templates = Jinja2Templates(directory="templates")

# 首页 UI
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stock/{ticker}", response_model=StockResponse)
def get_stock(ticker: str):
    """
    查询单只股票并给出决策
    """
    try:
        hist = get_stock_data(ticker, period="5d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch data: {e}")

    if hist.empty:
        raise HTTPException(status_code=404, detail="No data found for this ticker")

    last_row = hist.iloc[-1]
    decision, reasons = make_decision(hist)

    # 最近 90 天收盘价用于前端绘图
    hist_tail = hist.tail(90)
    date_col = hist_tail.columns[0]  # first column after reset_index
    history_data = [
        {"date": str(row[date_col])[:10], "close": round(row["Close"], 2)}
        for _, row in hist_tail.iterrows()
    ]

    return StockResponse(
        ticker=ticker.upper(),
        current_price=round(last_row["Close"], 2),
        open=round(last_row["Open"], 2),
        high=round(last_row["High"], 2),
        low=round(last_row["Low"], 2),
        volume=int(last_row["Volume"]),
        decision=decision,
        reasons=reasons,
        history=history_data,
    ) 