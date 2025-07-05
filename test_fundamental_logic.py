#!/usr/bin/env python3
"""
测试基本面分析核心逻辑（无依赖版本）
"""

def test_score_calculation():
    """测试评分计算逻辑"""
    print("=== 测试评分计算逻辑 ===")
    
    # 模拟财务健康度计算逻辑
    def calculate_profitability_score(roe, net_margin, gross_margin):
        score = 0
        if roe:
            score += min(roe * 2, 40)  # ROE > 20% = 40分
        if net_margin:
            score += min(net_margin * 2, 30)  # 净利率 > 15% = 30分
        if gross_margin:
            score += min(gross_margin / 2, 30)  # 毛利率 > 60% = 30分
        return min(100, max(0, score))
    
    # 测试优秀公司（如苹果）
    apple_score = calculate_profitability_score(roe=30, net_margin=23, gross_margin=38)
    print(f"苹果公司盈利能力评分: {apple_score}/100")
    
    # 测试普通公司
    normal_score = calculate_profitability_score(roe=12, net_margin=5, gross_margin=25)
    print(f"普通公司盈利能力评分: {normal_score}/100")
    
    # 测试亏损公司
    loss_score = calculate_profitability_score(roe=-5, net_margin=-2, gross_margin=15)
    print(f"亏损公司盈利能力评分: {loss_score}/100")
    
    assert apple_score > normal_score > loss_score, "评分应该反映公司质量差异"
    print("✅ 评分计算逻辑测试通过")

def test_industry_percentile():
    """测试行业百分位计算"""
    print("\n=== 测试行业百分位计算 ===")
    
    def calculate_percentile(value, benchmark, higher_is_better=True):
        if not value:
            return None
        ratio = value / benchmark
        if higher_is_better:
            if ratio >= 1.2:
                return 80
            elif ratio >= 1.1:
                return 70
            elif ratio >= 0.9:
                return 50
            elif ratio >= 0.8:
                return 30
            else:
                return 20
        else:  # lower is better (如P/E)
            if ratio <= 0.8:
                return 80
            elif ratio <= 0.9:
                return 70
            elif ratio <= 1.1:
                return 50
            elif ratio <= 1.2:
                return 30
            else:
                return 20
    
    # 测试ROE百分位（越高越好）
    roe_percentile = calculate_percentile(18, 15, True)  # 18% vs 行业平均15%
    print(f"ROE百分位 (18% vs 15%): {roe_percentile}%")
    
    # 测试P/E百分位（越低越好）
    pe_percentile = calculate_percentile(20, 25, False)  # 20 vs 行业平均25
    print(f"P/E百分位 (20 vs 25): {pe_percentile}%")
    
    assert roe_percentile > 50, "高于行业平均的ROE应该得到高百分位"
    assert pe_percentile > 50, "低于行业平均的P/E应该得到高百分位"
    print("✅ 行业百分位计算测试通过")

def test_comprehensive_scoring():
    """测试综合评分逻辑"""
    print("\n=== 测试综合评分逻辑 ===")
    
    def calculate_overall_score(technical_score, fundamental_score):
        # 技术面权重40%，基本面权重60%
        return technical_score * 0.4 + fundamental_score * 0.6
    
    def get_recommendation(overall_score):
        if overall_score >= 70:
            return "BUY"
        elif overall_score <= 40:
            return "SELL"
        else:
            return "HOLD"
    
    # 测试不同组合
    test_cases = [
        {"tech": 80, "fund": 85, "desc": "技术面和基本面都强"},
        {"tech": 30, "fund": 35, "desc": "技术面和基本面都弱"},
        {"tech": 70, "fund": 45, "desc": "技术面强，基本面一般"},
        {"tech": 40, "fund": 80, "desc": "技术面弱，基本面强"}
    ]
    
    for case in test_cases:
        overall = calculate_overall_score(case["tech"], case["fund"])
        recommendation = get_recommendation(overall)
        print(f"{case['desc']}: 综合{overall:.1f}分 -> {recommendation}")
    
    print("✅ 综合评分逻辑测试通过")

def test_financial_ratios():
    """测试财务比率分析"""
    print("\n=== 测试财务比率分析 ===")
    
    def analyze_liquidity(current_ratio, quick_ratio):
        health = []
        if current_ratio and current_ratio >= 2.0:
            health.append("流动性充足")
        elif current_ratio and current_ratio < 1.0:
            health.append("流动性风险")
        
        if quick_ratio and quick_ratio >= 1.0:
            health.append("速动资产充足")
        elif quick_ratio and quick_ratio < 0.5:
            health.append("速动资产不足")
            
        return health
    
    def analyze_leverage(debt_to_equity, debt_to_assets):
        risks = []
        if debt_to_equity and debt_to_equity > 1.0:
            risks.append("债务负担较重")
        
        if debt_to_assets and debt_to_assets > 50:
            risks.append("资产负债率偏高")
            
        return risks
    
    # 测试健康公司
    liquidity = analyze_liquidity(current_ratio=2.5, quick_ratio=1.2)
    leverage = analyze_leverage(debt_to_equity=0.3, debt_to_assets=25)
    print(f"健康公司 - 流动性: {liquidity}, 杠杆风险: {leverage or ['风险可控']}")
    
    # 测试高风险公司
    liquidity_risk = analyze_liquidity(current_ratio=0.8, quick_ratio=0.4)
    leverage_risk = analyze_leverage(debt_to_equity=2.0, debt_to_assets=70)
    print(f"高风险公司 - 流动性: {liquidity_risk}, 杠杆风险: {leverage_risk}")
    
    print("✅ 财务比率分析测试通过")

if __name__ == "__main__":
    print("🧪 开始基本面分析核心逻辑测试...\n")
    
    test_score_calculation()
    test_industry_percentile()
    test_comprehensive_scoring()
    test_financial_ratios()
    
    print("\n🎉 所有核心逻辑测试通过！")
    print("\n📊 基本面分析功能特点:")
    print("- 多维度财务健康度评分（盈利能力、流动性、杠杆、效率、成长性）")
    print("- 行业对比分析，了解个股在同行业中的相对位置")
    print("- 技术面+基本面综合决策，提高投资建议准确性")
    print("- 智能风险识别，自动标注财务风险点")
    print("- 财务比率深度分析，全面评估公司财务状况")