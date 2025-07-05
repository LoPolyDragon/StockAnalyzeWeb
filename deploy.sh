#!/bin/bash

# Stock AI Advisor 一键部署脚本
# 支持 macOS, Linux 和 Windows (WSL)

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查系统环境
check_system() {
    print_step "检查系统环境..."
    
    # 检查操作系统
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        *)          MACHINE="UNKNOWN:${OS}"
    esac
    print_info "检测到系统: $MACHINE"
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python版本: $PYTHON_VERSION"
        
        # 检查Python版本是否 >= 3.8
        python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" || {
            print_error "Python版本过低，需要3.8+，当前: $PYTHON_VERSION"
            exit 1
        }
        print_success "Python版本兼容"
    else
        print_error "未找到Python3，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 可用"
    else
        print_error "未找到pip3"
        exit 1
    fi
}

# 创建虚拟环境
setup_venv() {
    print_step "设置Python虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        print_info "创建虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source venv/bin/activate
    print_success "虚拟环境已激活"
    
    # 升级pip
    print_info "升级pip..."
    pip install --upgrade pip > /dev/null 2>&1
    print_success "pip已升级"
}

# 安装依赖
install_dependencies() {
    print_step "安装Python依赖包..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到requirements.txt文件"
        exit 1
    fi
    
    print_info "从requirements.txt安装依赖..."
    pip install -r requirements.txt
    print_success "依赖安装完成"
}

# 验证安装
verify_installation() {
    print_step "验证安装..."
    
    if [ -f "test_dependencies.py" ]; then
        print_info "运行依赖检测..."
        python test_dependencies.py
    else
        print_warning "未找到依赖检测脚本，跳过验证"
    fi
}

# 创建启动脚本
create_startup_scripts() {
    print_step "创建启动脚本..."
    
    # 创建启动脚本 (Unix/Linux/macOS)
    cat > start.sh << 'EOF'
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
EOF

    # 创建Windows启动脚本
    cat > start.bat << 'EOF'
@echo off
echo 🚀 启动 Stock AI Advisor...

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境不存在，请先运行 deploy.sh
    pause
    exit /b 1
)

REM 启动应用
echo 🌐 启动Web服务器...
echo 📱 访问地址: http://127.0.0.1:8000
echo 📋 API文档: http://127.0.0.1:8000/docs
echo 🛑 按 Ctrl+C 停止服务
echo.

python cli.py
pause
EOF

    chmod +x start.sh
    print_success "启动脚本已创建"
}

# 显示完成信息
show_completion_info() {
    print_success "🎉 部署完成！"
    echo ""
    echo "🚀 启动应用:"
    echo "   ./start.sh              # Linux/macOS"
    echo "   start.bat               # Windows"
    echo "   或者手动:"
    echo "   source venv/bin/activate"
    echo "   python cli.py"
    echo ""
    echo "🌐 访问地址:"
    echo "   http://127.0.0.1:8000   # Web界面"
    echo "   http://127.0.0.1:8000/docs  # API文档"
    echo ""
    echo "📚 更多信息:"
    echo "   查看 README.md 了解详细使用说明"
    echo "   查看 INSTALL.md 了解安装详情"
    echo ""
    print_info "测试快速查询: python cli.py AAPL"
}

# 主函数
main() {
    echo "🏗️  Stock AI Advisor 自动部署脚本"
    echo "======================================"
    echo ""
    
    # 检查是否在项目根目录
    if [ ! -f "cli.py" ] || [ ! -f "requirements.txt" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行部署步骤
    check_system
    setup_venv
    install_dependencies
    verify_installation
    create_startup_scripts
    show_completion_info
}

# 错误处理
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "部署过程中出现错误"
        print_info "请检查错误信息并重试"
        print_info "如需帮助，请查看 INSTALL.md 或提交 Issue"
    fi
}

trap cleanup EXIT

# 运行主函数
main "$@"