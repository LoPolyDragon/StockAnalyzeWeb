# Stock AI Advisor 项目结构

## 📁 项目文件结构

```
stock-ai-advisor/
├── 📄 README.md                    # 项目说明文档
├── 📄 INSTALL.md                   # 安装指南
├── 📄 PROJECT_STRUCTURE.md         # 项目结构说明
├── 📄 requirements.txt             # Python依赖清单
├── 🚀 deploy.sh                    # 一键部署脚本
├── 🧪 test_dependencies.py         # 依赖检测脚本
├── 🖥️  cli.py                      # 命令行入口
├── 📁 stock_api/                   # 核心API模块
│   ├── 📄 __init__.py
│   ├── 🧠 main.py                  # FastAPI主应用
│   ├── 📊 schemas.py               # 数据模型定义
│   ├── 🤖 ai_agent.py              # AI决策引擎
│   ├── 📈 stock_service.py         # 股票数据服务
│   ├── 💰 fundamental_service.py   # 基本面分析
│   ├── ⚖️  risk_service.py          # 风险管理
│   ├── 💼 portfolio_service.py     # 投资组合管理
│   ├── 📰 news_service.py          # 新闻数据
│   ├── 🌍 market_service.py        # 市场概况
│   ├── 💹 futu_service.py          # 富途API服务
│   └── 🤖 trading_strategy.py      # 自动化交易策略
├── 📁 templates/                   # 前端模板
│   └── 🎨 index.html               # 主页面
├── 📁 tests/                       # 测试文件
│   ├── 🧪 test_fundamental.py
│   ├── 🧪 test_portfolio.py
│   └── 🧪 test_risk_management.py
├── 📁 venv/                        # Python虚拟环境
└── 📁 Docs/                        # 其他文档
```

## 🏗️ 核心模块说明

### 🖥️ 应用入口
- **cli.py**: 命令行启动脚本，支持Web服务器和直接查询模式

### 🧠 API核心 (stock_api/)

#### 🌐 Web框架
- **main.py**: FastAPI主应用，定义所有REST API端点
- **schemas.py**: Pydantic数据模型，用于API请求/响应验证

#### 📊 数据服务
- **stock_service.py**: 股票数据获取，支持多数据源和缓存
- **news_service.py**: 股票相关新闻数据
- **market_service.py**: 市场概况和推荐股票

#### 🤖 分析引擎
- **ai_agent.py**: AI决策引擎，基于技术指标的智能决策
- **fundamental_service.py**: 基本面分析，财务指标和健康度评分
- **risk_service.py**: 风险管理，VaR、回撤、波动率分析

#### 💼 投资管理
- **portfolio_service.py**: 投资组合管理和绩效分析
- **trading_strategy.py**: 自动化交易策略和信号生成

#### 💹 富途集成
- **futu_service.py**: 富途牛牛API集成，实时行情和交易功能

### 🎨 前端界面 (templates/)
- **index.html**: 响应式Web界面，支持多标签页和实时图表

## 🔧 工具脚本

### 🚀 部署和启动
- **deploy.sh**: 全自动部署脚本，一键安装环境和依赖
- **start.sh**: 启动脚本 (由deploy.sh生成)
- **start.bat**: Windows启动脚本

### 🧪 测试和验证
- **test_dependencies.py**: 依赖检测脚本，验证所有包是否正确安装
- **tests/**: 单元测试目录

## 📋 配置文件

### 📦 依赖管理
- **requirements.txt**: Python依赖包清单，包含所有必需库

### 📚 文档
- **README.md**: 项目主要说明文档
- **INSTALL.md**: 详细安装指南
- **PROJECT_STRUCTURE.md**: 当前文件，项目结构说明

## 🔗 API端点结构

### 📊 股票数据
- `GET /stock/{ticker}` - 股票技术分析和AI决策
- `GET /news/{ticker}` - 股票相关新闻
- `GET /market` - 市场概况
- `GET /recommend` - AI推荐股票

### 💰 基本面分析
- `GET /fundamental/{ticker}` - 财务指标
- `GET /fundamental/{ticker}/health` - 财务健康度
- `GET /fundamental/{ticker}/industry` - 行业对比
- `GET /analysis/{ticker}` - 综合分析

### ⚖️ 风险管理
- `GET /risk/{ticker}/var` - VaR分析
- `GET /risk/{ticker}/drawdown` - 回撤分析
- `GET /risk/{ticker}/volatility` - 波动率分析
- `GET /risk/{ticker}/correlation` - 相关性分析
- `GET /risk/{ticker}/position` - 仓位建议
- `GET /risk/{ticker}/comprehensive` - 综合风险分析

### 💼 投资组合
- `POST /portfolio` - 创建投资组合
- `GET /portfolios` - 获取组合列表
- `GET /portfolio/{id}` - 组合详情
- `POST /portfolio/{id}/holding` - 添加持仓
- `GET /portfolio/{id}/performance` - 绩效分析

### 💹 富途API
- `GET /futu/status` - 连接状态
- `GET /futu/snapshot/{code}` - 实时行情
- `GET /futu/kline/{code}` - K线数据
- `GET /futu/search/{keyword}` - 股票搜索
- `GET /futu/plates` - 板块列表

### 🤖 自动化交易
- `GET /trading/status` - 交易引擎状态
- `POST /trading/start` - 启动自动交易
- `POST /trading/stop` - 停止自动交易
- `POST /trading/scan` - 扫描交易机会
- `POST /trading/execute/{account_id}` - 执行交易周期
- `GET /trading/strategies` - 可用策略

### 🔧 系统
- `GET /health` - 健康检查

## 🎯 数据流

```
用户请求 → FastAPI路由 → 服务层 → 数据源 → 处理分析 → 返回结果
    ↓
Web界面 ← JSON响应 ← AI决策 ← 数据缓存 ← 多源数据
```

## 🔧 扩展性

项目采用模块化设计，易于扩展：
- 新增数据源：在相应service文件中添加
- 新增策略：继承TradingStrategy基类
- 新增指标：在ai_agent.py中添加计算逻辑
- 新增API：在main.py中添加路由

## 📈 性能优化

- **缓存机制**: 数据自动缓存5分钟
- **异步处理**: 支持并发请求
- **多数据源**: 自动故障切换
- **重试机制**: 网络失败自动重试
- **数据验证**: 确保数据完整性