# Stock API Dev

## 快速开始

```bash
# 建议先创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 1. 终端模式
```bash
# 单次查询
python cli.py AAPL
```

### 2. 本地 API
```bash
# 启动服务器 (http://127.0.0.1:8000/stock/AAPL)
python cli.py

# 亦可手动启动
uvicorn stock_api.main:app --reload
```

### 3. 部署到网站
因为使用 FastAPI，后续可选择：
- Docker + Uvicorn/Gunicorn
- 部署到 Vercel / Render / Railway / AWS 等
- 或在前端直接 fetch `https://your-domain/stock/AAPL` 