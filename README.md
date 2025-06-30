# Stock AI Advisor 🚀

基于 FastAPI + yfinance + pandas 的本地股票查询与 AI 决策 API，同时附带简易可视化网页前端。

---
## 功能特性
1. **查询美股 & 港股**：支持 `AAPL`、`00700.HK` 等格式。
2. **AI 决策**：结合 SMA、RSI、MACD 等指标，给出 买入 / 卖出 / 持有 建议并列出理由。
3. **可视化**：网页端展示最近 90 日价格折线图与彩色决策徽章。
4. **CLI / API / Web** 三种访问方式，方便二次开发。

---
## 本地安装步骤（macOS / Linux / Windows WSL 通用）

> ⚠️ 需要 Python ≥ 3.10

```bash
# 1. 克隆仓库（或已在本地直接跳过）
# git clone https://github.com/<your-user>/stock-ai-advisor.git
# cd stock-ai-advisor

# 2. 创建并激活虚拟环境（推荐）
python3 -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows (PowerShell)
# .\venv\Scripts\Activate.ps1

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖
pip install -r requirements.txt
```

如因网络原因安装缓慢，可使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---
## 运行方式

### 1. CLI 单次查询
```bash
# 查询 AAPL
python cli.py AAPL

# 查询港股
python cli.py 00700.HK
```

### 2. 启动本地 API + 网页
```bash
python cli.py     # 默认监听 http://127.0.0.1:8000/
```
启动后：
* API 接口示例：`http://127.0.0.1:8000/stock/AAPL`
* 网页前端：`http://127.0.0.1:8000/`  输入代码即可查看图表与决策。

### 3. 热重载（开发模式）
```bash
uvicorn stock_api.main:app --reload --reload-dir stock_api --reload-exclude venv/*
```

---
## 项目结构
```
.
├── stock_api          # 后端业务包
│   ├── __init__.py
│   ├── ai_agent.py    # 决策逻辑
│   ├── main.py        # FastAPI 路由
│   ├── schemas.py     # Pydantic 模型
│   └── stock_service.py
├── templates
│   └── index.html     # 网页前端 (Tailwind + Chart.js)
├── cli.py             # 启动脚本 / CLI
├── requirements.txt   # 依赖清单
└── README.md
```

---
## 常见问题
| 问题 | 解决方案 |
|------|-----------|
| `yfinance` 返回 `No price data found` | 网络被 Yahoo Finance 阻断，可开代理；或依赖项目已自动回退到 Stooq。 |
| Uvicorn 无限重载 | 已在 `cli.py` 关闭热重载；开发时手动添加 `--reload` 并排除 `venv` 目录即可。 |
| 端口占用 `8000` | `lsof -ti:8000 | xargs kill -9` 后重新运行。 |

---
## 部署建议
* **Docker**：`FROM python:3.10` → `pip install -r requirements.txt` → `CMD uvicorn stock_api.main:app --host 0.0.0.0 --port 80`
* **Serverless**：FastAPI 可轻松部署到 Vercel / Render / Railway。

---
## License
MIT
