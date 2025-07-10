# 🔑 API密钥设置指南

## 免费API密钥注册和配置

### 1. Alpha Vantage（已配置）
- **状态**: ✅ 已配置
- **每日限制**: 25次请求
- **功能**: 新闻 + 情感分析
- **API Key**: `QSUOL2TCXDHPANCE`

### 2. NewsAPI.org（推荐）
- **注册地址**: https://newsapi.org/register
- **免费额度**: 每天100次请求
- **功能**: 全球新闻，可按关键词搜索
- **获取步骤**:
  1. 访问 https://newsapi.org/register
  2. 填写邮箱和密码注册
  3. 验证邮箱
  4. 获取API Key

### 3. Finnhub.io（推荐）
- **注册地址**: https://finnhub.io/register
- **免费额度**: 每分钟60次请求
- **功能**: 专业金融数据，包含新闻
- **获取步骤**:
  1. 访问 https://finnhub.io/register
  2. 注册免费账户
  3. 在Dashboard中获取API Key

### 4. Marketaux（可选）
- **注册地址**: https://www.marketaux.com/
- **免费额度**: 每天200次请求
- **功能**: 专业金融新闻 + 情感分析
- **获取步骤**:
  1. 访问 https://www.marketaux.com/
  2. 注册免费账户
  3. 获取API Token

### 5. Yahoo Finance RSS（免费）
- **状态**: ✅ 无需注册
- **限制**: 无限制
- **功能**: 基础新闻RSS源

## 📝 配置API密钥

### 方法1：直接修改代码
编辑 `stock_api/enhanced_news_service.py` 文件：

```python
self.apis = {
    'newsapi': {
        'api_key': 'YOUR_NEWSAPI_KEY_HERE',  # 替换为你的NewsAPI密钥
        # ...
    },
    'finnhub': {
        'api_key': 'YOUR_FINNHUB_KEY_HERE',  # 替换为你的Finnhub密钥
        # ...
    },
    'marketaux': {
        'api_key': 'YOUR_MARKETAUX_KEY_HERE',  # 替换为你的Marketaux密钥
        # ...
    }
}
```

### 方法2：使用环境变量（推荐）
创建 `.env` 文件：

```bash
# 新闻API密钥
NEWSAPI_KEY=your_newsapi_key_here
FINNHUB_KEY=your_finnhub_key_here
MARKETAUX_KEY=your_marketaux_key_here
```

然后修改代码读取环境变量：

```python
import os
from dotenv import load_dotenv

load_dotenv()

self.apis = {
    'newsapi': {
        'api_key': os.getenv('NEWSAPI_KEY', 'YOUR_NEWSAPI_KEY'),
        # ...
    },
    'finnhub': {
        'api_key': os.getenv('FINNHUB_KEY', 'YOUR_FINNHUB_KEY'),
        # ...
    },
    'marketaux': {
        'api_key': os.getenv('MARKETAUX_KEY', 'YOUR_MARKETAUX_KEY'),
        # ...
    }
}
```

## 🚀 快速开始

### 1. 最简单的方式（只用免费的）
如果你不想注册任何API，可以只使用：
- Alpha Vantage（已配置）
- Yahoo Finance RSS（无需注册）

### 2. 推荐配置
建议至少注册以下两个：
- **NewsAPI**：新闻覆盖面广
- **Finnhub**：专业金融数据

### 3. 完整配置
注册所有API获得最佳体验：
- Alpha Vantage ✅
- NewsAPI
- Finnhub  
- Marketaux
- Yahoo RSS ✅

## 🔍 使用示例

```python
# 获取苹果公司相关新闻
apple_news = get_stock_news('AAPL', limit=10)

# 获取市场新闻
market_news = get_market_news(limit=20)

# 检查API使用状态
from stock_api.enhanced_news_service import enhanced_news_service
status = enhanced_news_service.get_api_status()
print(status)
```

## 💡 优化建议

### 1. API调用优先级
1. **Alpha Vantage**：有情感分析，质量高
2. **Yahoo RSS**：免费稳定，作为备选
3. **Finnhub**：专业数据，针对特定股票
4. **NewsAPI**：新闻覆盖面广
5. **Marketaux**：专业金融新闻

### 2. 缓存策略
- 新闻数据缓存5分钟
- 相同请求避免重复调用
- 自动去重相似新闻

### 3. 错误处理
- API限额达到时自动切换到其他源
- 网络错误时使用缓存数据
- 记录API使用情况

## 📊 成本分析

| API | 免费额度 | 成本 | 推荐度 |
|-----|----------|------|--------|
| Alpha Vantage | 25/天 | 免费 | ⭐⭐⭐⭐⭐ |
| NewsAPI | 100/天 | 免费 | ⭐⭐⭐⭐ |
| Finnhub | 60/分钟 | 免费 | ⭐⭐⭐⭐ |
| Marketaux | 200/天 | 免费 | ⭐⭐⭐ |
| Yahoo RSS | 无限制 | 免费 | ⭐⭐⭐⭐ |

## 🔧 故障排除

### 常见问题

1. **API密钥无效**
   - 检查密钥是否正确复制
   - 确认API账户状态是否正常

2. **请求限制**
   - 检查是否超过每日/每分钟限制
   - 系统会自动切换到其他API源

3. **网络错误**
   - 检查网络连接
   - 系统会使用缓存数据

### 日志查看
```python
import logging
logging.basicConfig(level=logging.INFO)
```

这样可以看到详细的API调用日志。