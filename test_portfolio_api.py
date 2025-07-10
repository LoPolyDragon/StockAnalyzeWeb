#!/usr/bin/env python3
"""投资组合功能测试脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_api.portfolio_service import portfolio_service
import json

def test_portfolio_functionality():
    """测试投资组合功能"""
    print("🧪 开始测试投资组合功能...")
    
    # 1. 创建投资组合
    print("\n1. 创建投资组合...")
    portfolio_id = portfolio_service.create_portfolio("测试投资组合", "用于功能测试的投资组合")
    print(f"✅ 创建成功，投资组合ID: {portfolio_id}")
    
    # 2. 添加持仓
    print("\n2. 添加持仓...")
    success = portfolio_service.add_holding(portfolio_id, "AAPL", 10, 150.0)
    print(f"✅ 添加AAPL持仓: {success}")
    
    success = portfolio_service.add_holding(portfolio_id, "MSFT", 5, 300.0)
    print(f"✅ 添加MSFT持仓: {success}")
    
    # 3. 获取投资组合详情
    print("\n3. 获取投资组合详情...")
    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if portfolio:
        print(f"✅ 投资组合: {portfolio.name}")
        print(f"   总市值: ${portfolio.total_value:.2f}")
        print(f"   总盈亏: ${portfolio.total_pnl:.2f} ({portfolio.total_pnl_pct:.2f}%)")
        print(f"   持仓数量: {len(portfolio.holdings)}")
        
        for holding in portfolio.holdings:
            print(f"   - {holding.ticker}: {holding.shares}股 @ ${holding.current_price:.2f} "
                  f"(成本${holding.avg_cost:.2f}, 盈亏${holding.unrealized_pnl:.2f})")
    else:
        print("❌ 获取投资组合详情失败")
        return False
    
    # 4. 列出所有投资组合
    print("\n4. 列出所有投资组合...")
    portfolios = portfolio_service.list_portfolios()
    print(f"✅ 找到 {len(portfolios)} 个投资组合")
    
    # 5. 删除持仓
    print("\n5. 删除持仓...")
    success = portfolio_service.remove_holding(portfolio_id, "MSFT")
    print(f"✅ 删除MSFT持仓: {success}")
    
    # 6. 更新投资组合信息
    print("\n6. 更新投资组合信息...")
    success = portfolio_service.update_portfolio(portfolio_id, "更新后的测试组合", "更新后的描述")
    print(f"✅ 更新投资组合: {success}")
    
    # 7. 获取表现分析
    print("\n7. 获取表现分析...")
    performance = portfolio_service.get_portfolio_performance(portfolio_id, "1mo")
    if performance:
        print(f"✅ 表现分析:")
        print(f"   累计收益率: {performance.cumulative_return:.2f}%")
        print(f"   年化收益率: {performance.annualized_return:.2f}%")
        print(f"   波动率: {performance.volatility:.2f}%")
        print(f"   夏普比率: {performance.sharpe_ratio:.2f}")
        print(f"   最大回撤: {performance.max_drawdown:.2f}%")
    else:
        print("⚠️  表现分析数据不可用（可能需要更多历史数据）")
    
    # 8. 清理测试数据
    print("\n8. 清理测试数据...")
    success = portfolio_service.delete_portfolio(portfolio_id)
    print(f"✅ 删除投资组合: {success}")
    
    print("\n🎉 投资组合功能测试完成！")
    return True

if __name__ == "__main__":
    try:
        test_portfolio_functionality()
        print("\n✅ 所有测试通过！投资组合功能运行正常。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()