#!/bin/bash
# Stock AI Advisor 启动脚本

echo "🚀 启动 Stock AI Advisor..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行 ./deploy.sh"
    exit 1
fi

# 启动应用
echo "🌐 启动Web服务器..."
echo "📱 访问地址: http://127.0.0.1:8000"
echo "📋 API文档: http://127.0.0.1:8000/docs"
echo "🛑 按 Ctrl+C 停止服务"
echo ""

python cli.py