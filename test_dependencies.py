#!/usr/bin/env python3
"""
依赖测试脚本
验证所有必需的Python包是否正确安装
"""

import sys
import importlib
from typing import List, Tuple

def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    测试模块导入
    
    Args:
        module_name: 模块名
        package_name: 包名（用于显示）
    
    Returns:
        (成功状态, 错误信息)
    """
    package_name = package_name or module_name
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"未知错误: {e}"

def test_submodule_imports() -> List[Tuple[str, bool, str]]:
    """测试子模块导入"""
    submodule_tests = [
        ("futu.quote.open_quote_context", "富途行情API"),
        ("futu.trade.open_trade_context", "富途交易API"),
        ("futu.common.constant", "富途常量定义"),
        ("pandas_datareader.data", "pandas数据读取器"),
        ("ta.momentum", "技术分析-动量指标"),
        ("ta.trend", "技术分析-趋势指标"),
        ("sklearn.model_selection", "机器学习模型选择"),
    ]
    
    results = []
    for module, description in submodule_tests:
        success, error = test_import(module)
        results.append((description, success, error))
    
    return results

def main():
    """主测试函数"""
    print("🔍 Stock AI Advisor - 依赖检测")
    print("=" * 50)
    
    # 核心依赖测试
    core_dependencies = [
        ("fastapi", "FastAPI Web框架"),
        ("uvicorn", "ASGI服务器"),
        ("pandas", "数据处理库"),
        ("numpy", "数值计算库"),
        ("yfinance", "Yahoo Finance数据"),
        ("requests", "HTTP请求库"),
        ("jinja2", "模板引擎"),
        ("ta", "技术分析库"),
        ("sklearn", "机器学习库", "scikit-learn"),
        ("bs4", "HTML解析", "beautifulsoup4"),
        ("lxml", "XML解析器"),
        ("futu", "富途API"),
        ("httpx", "异步HTTP客户端"),
        ("aiofiles", "异步文件操作"),
        ("email_validator", "邮箱验证"),
        ("multipart", "多部分表单数据", "python-multipart"),
        ("dateutil", "日期处理", "python-dateutil"),
        ("pytz", "时区处理"),
    ]
    
    print("\n📦 核心依赖检测:")
    failed_deps = []
    
    for module, description, *install_name in core_dependencies:
        install_name = install_name[0] if install_name else module
        success, error = test_import(module)
        
        status = "✅" if success else "❌"
        print(f"{status} {description:<25} ({install_name})")
        
        if not success:
            failed_deps.append((install_name, error))
            print(f"   错误: {error}")
    
    # 子模块测试
    print("\n🔧 子模块检测:")
    submodule_results = test_submodule_imports()
    
    for description, success, error in submodule_results:
        status = "✅" if success else "⚠️"
        print(f"{status} {description}")
        if not success and error:
            print(f"   警告: {error}")
    
    # Python版本检查
    print(f"\n🐍 Python版本: {sys.version}")
    
    python_version = sys.version_info
    if python_version >= (3, 8):
        print("✅ Python版本兼容")
    else:
        print("❌ Python版本过低，需要3.8+")
        failed_deps.append(("Python", "版本需要3.8+"))
    
    # 总结
    print("\n" + "=" * 50)
    
    if not failed_deps:
        print("🎉 所有依赖检测通过！")
        print("\n✨ 可以运行以下命令启动应用:")
        print("   python cli.py")
        print("   或访问: http://127.0.0.1:8000")
        return 0
    else:
        print(f"❌ 发现 {len(failed_deps)} 个问题:")
        for dep, error in failed_deps:
            print(f"   - {dep}: {error}")
        
        print(f"\n🔧 修复建议:")
        print("   1. 确保虚拟环境已激活:")
        print("      source venv/bin/activate")
        print("   2. 重新安装依赖:")
        print("      pip install -r requirements.txt")
        print("   3. 如果问题持续，尝试:")
        print("      pip install --upgrade pip")
        print("      pip cache purge")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)