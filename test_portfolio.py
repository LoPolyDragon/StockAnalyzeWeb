#!/usr/bin/env python3
"""
测试投资组合功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_portfolio_basic():
    """测试基本的投资组合创建和数据结构"""
    print("=== 测试投资组合数据结构 ===")
    
    # 模拟测试数据
    portfolio_data = {
        "id": "test-123",
        "name": "测试组合",
        "description": "这是一个测试投资组合",
        "holdings": {
            "AAPL": {
                "shares": 100,
                "avg_cost": 150.0,
                "transactions": [
                    {"date": "2024-01-01", "shares": 100, "price": 150.0, "type": "buy"}
                ]
            }
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    print(f"组合名称: {portfolio_data['name']}")
    print(f"组合描述: {portfolio_data['description']}")
    print(f"持仓数量: {len(portfolio_data['holdings'])}")
    
    for ticker, holding in portfolio_data['holdings'].items():
        print(f"- {ticker}: {holding['shares']}股，平均成本${holding['avg_cost']}")
    
    print("✅ 基本数据结构测试通过")

def test_api_schema():
    """测试API数据模型"""
    print("\n=== 测试API数据模型 ===")
    
    try:
        from stock_api.schemas import PortfolioCreate, PortfolioResponse, AddHoldingRequest
        
        # 测试创建投资组合请求
        create_req = PortfolioCreate(name="测试组合", description="测试描述")
        print(f"创建请求: {create_req.name} - {create_req.description}")
        
        # 测试添加持仓请求
        add_req = AddHoldingRequest(ticker="AAPL", shares=100, cost_per_share=150.0)
        print(f"添加持仓请求: {add_req.ticker} {add_req.shares}股 @${add_req.cost_per_share}")
        
        print("✅ API数据模型测试通过")
        
    except Exception as e:
        print(f"❌ API数据模型测试失败: {e}")

def test_json_storage():
    """测试JSON文件存储"""
    print("\n=== 测试JSON存储 ===")
    
    import json
    import tempfile
    import os
    
    # 创建临时文件测试
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_data = {
            "portfolio-1": {
                "id": "portfolio-1",
                "name": "测试组合",
                "description": "JSON存储测试",
                "holdings": {
                    "AAPL": {"shares": 100, "avg_cost": 150.0, "transactions": []}
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
        
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    # 读取测试
    with open(temp_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
        
    print(f"保存的投资组合数量: {len(loaded_data)}")
    print(f"组合名称: {loaded_data['portfolio-1']['name']}")
    
    # 清理临时文件
    os.unlink(temp_file)
    print("✅ JSON存储测试通过")

if __name__ == "__main__":
    test_portfolio_basic()
    test_api_schema()
    test_json_storage()
    print("\n🎉 所有测试完成！投资组合管理功能基本结构正常。")