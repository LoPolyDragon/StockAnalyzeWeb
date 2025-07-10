#!/bin/bash

# 默认端口
PORT=8080

# 解析命令行参数
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--port) PORT="$2"; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，尝试清理..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 寻找可用的Python解释器
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到Python解释器，请确保已安装Python 3"
    exit 1
fi

echo "🐍 使用Python解释器: $PYTHON_CMD"

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "🔄 激活虚拟环境..."
    source venv/bin/activate
    
    # 检查虚拟环境中的Python和pip
    if [ -f "venv/bin/python" ]; then
        PYTHON_CMD="venv/bin/python"
    elif [ -f "venv/bin/python3" ]; then
        PYTHON_CMD="venv/bin/python3"
    fi
    
    # 设置pip命令
    if [ -f "venv/bin/pip" ]; then
        PIP_CMD="venv/bin/pip"
    elif [ -f "venv/bin/pip3" ]; then
        PIP_CMD="venv/bin/pip3"
    else
        PIP_CMD="$PYTHON_CMD -m pip"
    fi
else
    echo "⚠️  未找到虚拟环境，使用系统Python"
    
    # 设置系统pip命令
    if command -v pip3 >/dev/null 2>&1; then
        PIP_CMD="pip3"
    elif command -v pip >/dev/null 2>&1; then
        PIP_CMD="pip"
    else
        PIP_CMD="$PYTHON_CMD -m pip"
    fi
fi

echo "📦 使用pip命令: $PIP_CMD"

# 检查必要依赖
echo "🔍 检查依赖..."
if ! $PYTHON_CMD -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "❌ 缺少必要依赖，正在安装..."
    $PIP_CMD install -r requirements.txt
fi

# 启动服务
echo "🚀 启动 Stock AI Advisor 服务 (端口: $PORT)..."
echo "📝 执行命令: $PYTHON_CMD cli.py --port $PORT"

# 直接运行，不放到后台，这样可以看到错误信息
$PYTHON_CMD cli.py --port $PORT