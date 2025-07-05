# Stock AI Advisor 安装指南

## 系统要求

- Python 3.8+ (推荐 3.10+)
- 内存: 最低 4GB，推荐 8GB+
- 存储空间: 1GB+
- 网络连接（用于获取股票数据）

## 快速安装

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd stock-ai-advisor
```

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. 一键安装所有依赖

```bash
pip install -r requirements.txt
```

### 4. 启动应用

```bash
# 启动Web服务器
python cli.py

# 或者直接查询股票
python cli.py AAPL
```

### 5. 访问应用

打开浏览器访问: http://127.0.0.1:8000

## 依赖说明

### 核心框架
- **FastAPI**: 现代高性能Web框架
- **Uvicorn**: ASGI服务器
- **Jinja2**: 模板引擎

### 数据处理
- **Pandas**: 数据分析库
- **NumPy**: 数值计算库  
- **Scikit-learn**: 机器学习库

### 金融数据
- **yfinance**: Yahoo Finance数据接口
- **pandas_datareader**: 多数据源财经数据
- **ta**: 技术分析指标库

### 富途交易
- **futu-api**: 富途牛牛API（港美股实时数据和交易）

### 辅助工具
- **requests**: HTTP请求库
- **beautifulsoup4**: HTML解析
- **httpx**: 异步HTTP客户端
- **aiofiles**: 异步文件操作

## 可选配置

### 富途API配置

如果需要使用富途牛牛的实时数据和交易功能：

1. 下载并安装 [富途牛牛客户端](https://www.futunn.com/)
2. 开启OpenAPI权限
3. 下载并运行 [FutuOpenD](https://openapi.futunn.com/futu-api-doc/en/quick/opend-base.html)

### 环境变量配置

创建 `.env` 文件（可选）：

```bash
# API配置
FUTU_HOST=127.0.0.1
FUTU_PORT=11111

# 日志级别
LOG_LEVEL=INFO

# 缓存配置
CACHE_TIMEOUT=300
```

## 故障排除

### 1. 依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 如果某个包安装失败，可以单独安装
pip install package_name

# 清理缓存重试
pip cache purge
pip install -r requirements.txt
```

### 2. 富途API连接失败

- 确保富途牛牛客户端已启动
- 确保FutuOpenD已运行
- 检查防火墙设置
- 确认端口11111未被占用

### 3. 数据获取失败

- 检查网络连接
- 某些数据源可能需要VPN
- yfinance偶尔会有限制，系统会自动切换备用数据源

### 4. 内存不足

- 增加系统虚拟内存
- 减少并发数据请求
- 清理缓存数据

## 功能验证

安装完成后，可以测试各个功能模块：

```bash
# 测试股票查询
python cli.py AAPL

# 测试Web界面
python cli.py
# 然后访问 http://127.0.0.1:8000

# 测试API接口
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/stock/AAPL
```

## API文档

启动服务后，可以访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 技术支持

如遇到问题：
1. 查看日志输出
2. 检查网络连接
3. 确认Python版本兼容性
4. 查看GitHub Issues