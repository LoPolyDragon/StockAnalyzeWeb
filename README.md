# Stock AI Advisor 🚀

专业级股票投资AI助手，集成技术面分析、基本面分析、风险管理、投资组合管理于一体。

## 🌟 核心功能

### 📈 技术分析
- **多指标决策**：集成SMA、RSI、MACD、布林带等技术指标
- **智能信号**：AI算法自动识别买入/卖出/持有信号
- **多时间周期**：支持1D到10Y的各种时间框架分析

### 💰 基本面分析  
- **财务指标**：P/E、P/B、ROE、债务比率等30+关键指标
- **健康度评分**：5维度财务健康评分系统（0-100分）
- **行业对比**：自动对比行业平均水平，识别投资机会
- **综合决策**：技术面+基本面双重验证

### ⚡ 风险管理
- **VaR计算**：历史模拟法和参数法计算风险价值
- **回撤分析**：最大回撤、当前回撤、恢复时间分析
- **波动率监控**：多时间维度波动率跟踪
- **仓位建议**：凯利公式优化仓位配置
- **相关性分析**：构建分散化投资组合

### 📊 投资组合管理
- **组合创建**：灵活创建和管理多个投资组合
- **实时盈亏**：自动计算未实现盈亏和收益率
- **性能分析**：夏普比率、最大回撤、年化收益等指标
- **风险分散**：评估投资组合分散化程度

### 🤖 自动化交易（即将上线）
- **富途API集成**：接入富途牛牛实现自动交易
- **策略执行**：基于AI决策自动执行交易策略
- **风险控制**：智能止损止盈机制

## 🚀 快速开始

### 环境要求
- Python ≥ 3.10
- 8GB RAM (推荐)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-username/stock-ai-advisor.git
cd stock-ai-advisor

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 .\venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 如需单独安装富途API
pip install futu-api

# 依赖安装常见问题
# 如果遇到 ImportError 或 ModuleNotFoundError，优先检查虚拟环境是否激活，并确保所有依赖都已在虚拟环境中安装。
# 推荐始终使用如下命令激活虚拟环境：
source venv/bin/activate

# 运行 cli.py
python cli.py
```

访问 `http://127.0.0.1:8000` 开始使用！

## 📱 使用方式

### 1. Web界面（推荐）
- **股票分析**：输入股票代码获取全面分析报告
- **基本面分析**：深度财务数据和行业对比
- **风险管理**：专业风险评估和仓位建议
- **投资组合**：创建和管理投资组合

### 2. API接口
```bash
# 股票基础数据
curl http://localhost:8000/stock/AAPL

# 基本面分析
curl http://localhost:8000/fundamental/AAPL

# 风险分析
curl http://localhost:8000/risk/AAPL/comprehensive

# 投资组合
curl http://localhost:8000/portfolios
```

### 3. CLI命令行
```bash
# 快速查询
python cli.py AAPL
python cli.py 00700.HK  # 港股
```

## 🏗️ 项目架构

```
stock-ai-advisor/
├── stock_api/                 # 核心API模块
│   ├── main.py               # FastAPI主应用
│   ├── schemas.py            # 数据模型定义
│   ├── ai_agent.py           # AI决策引擎
│   ├── fundamental_service.py # 基本面分析
│   ├── risk_service.py       # 风险管理
│   ├── portfolio_service.py  # 投资组合管理
│   ├── stock_service.py      # 数据获取服务
│   ├── news_service.py       # 新闻数据
│   └── market_service.py     # 市场概况
├── templates/
│   └── index.html            # 前端界面
├── tests/                    # 测试文件
├── cli.py                    # 命令行入口
└── requirements.txt          # 依赖清单
```

## 🔧 API文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🎯 核心特性

### 💡 智能决策
- **多因子模型**：综合技术面、基本面、市场情绪
- **机器学习**：持续优化决策准确率
- **风险调整**：根据个人风险偏好调整建议

### 📊 专业级分析
- **机构级指标**：VaR、夏普比率、最大回撤等
- **行业标准**：对标专业投资机构分析框架
- **实时更新**：数据自动更新，决策始终基于最新信息

### 🛡️ 风险管控
- **多层防护**：技术风险+基本面风险+市场风险
- **量化评估**：精确量化各类投资风险
- **动态调整**：根据市场环境动态调整风险参数

## 🔮 即将推出

- 🤖 **AI自动交易**：基于强化学习的智能交易机器人
- 📱 **移动端APP**：iOS/Android原生应用
- 🌐 **多市场支持**：A股、港股、美股、加密货币
- 👥 **社交投资**：策略分享、跟单功能
- 📈 **高级图表**：专业级K线图表工具

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

## ⚠️ 富途API导入说明

- futu-api 的部分类型（如 TrdSide, OrderType, TrdEnv, KLType, Market 等）应从 futu.common.constant 导入：

```python
from futu.common.constant import TrdSide, OrderType, TrdEnv, KLType, Market
```

- 行情和交易上下文应这样导入：

```python
from futu.quote.open_quote_context import OpenQuoteContext
from futu.trade.open_trade_context import OpenSecTradeContext
```

- 不要直接 from futu import TrdSide 等，否则会报 ImportError。

## 🐛 虚拟环境常见问题排查

- 如果激活虚拟环境后依然提示找不到模块（如 uvicorn、futu），请确认 pip 安装路径和 python 运行路径一致：

```bash
which python
which pip
```

- 推荐用虚拟环境自带的 pip 安装依赖：

```bash
./venv/bin/pip install -r requirements.txt
```

- 如果虚拟环境损坏，可删除 venv 目录后重新创建：

```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```