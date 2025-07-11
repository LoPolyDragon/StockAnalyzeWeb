import requests
import logging
from typing import Dict, List
import json
import re

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        # 简单的金融术语翻译字典
        self.finance_terms = {
            # 股票相关
            'stock': '股票',
            'shares': '股份',
            'market': '市场',
            'trading': '交易',
            'investor': '投资者',
            'investment': '投资',
            'portfolio': '投资组合',
            'dividend': '股息',
            'earnings': '财报',
            'revenue': '营收',
            'profit': '利润',
            'loss': '亏损',
            'bull market': '牛市',
            'bear market': '熊市',
            'IPO': '首次公开募股',
            'CEO': '首席执行官',
            'CFO': '首席财务官',
            
            # 经济术语
            'inflation': '通胀',
            'GDP': '国内生产总值',
            'Federal Reserve': '美联储',
            'interest rate': '利率',
            'tariff': '关税',
            'trade': '贸易',
            'economy': '经济',
            'economic': '经济的',
            'financial': '金融的',
            'banking': '银行业',
            'currency': '货币',
            'dollar': '美元',
            
            # 公司名称
            'Apple': '苹果',
            'Microsoft': '微软',
            'Google': '谷歌',
            'Tesla': '特斯拉',
            'Amazon': '亚马逊',
            'Meta': 'Meta',
            'NVIDIA': '英伟达',
            'Delta': '达美航空',
            
            # 常用词汇
            'technology': '科技',
            'artificial intelligence': '人工智能',
            'AI': '人工智能',
            'data': '数据',
            'growth': '增长',
            'increase': '增加',
            'decrease': '减少',
            'rise': '上涨',
            'fall': '下跌',
            'jump': '跳涨',
            'surge': '激增',
            'outlook': '前景',
            'forecast': '预测',
            'analyst': '分析师',
            'report': '报告',
        }
        
        # 界面文本翻译
        self.ui_translations = {
            'zh': {
                # 导航菜单
                'market_dashboard': '市场仪表盘',
                'stock_analysis': '股票分析',
                'fundamental_analysis': '基本面分析',
                'risk_management': '风险管理',
                'portfolio': '投资组合',
                'investment_tools': '投资工具',
                'settings': '设置',
                'login': '登录',
                
                # 市场仪表盘
                'market_indices': '市场指数',
                'sector_heatmap': '行业热力图',
                'market_sentiment': '市场情绪',
                'top_gainers': '涨幅榜',
                'top_losers': '跌幅榜',
                'volume_leaders': '成交量排行',
                'market_news': '市场快讯',
                'fear_greed_index': '恐惧贪婪指数',
                'vix_volatility': 'VIX波动率',
                'advance_decline': '上涨/下跌比例',
                'new_high_low': '新高/新低比',
                
                # 股票分析
                'smart_stock_analysis': '智能股票分析',
                'enter_stock_code': '输入股票代码',
                'smart_analysis': '智能分析',
                'hot_stocks': '热门股票',
                'current_price': '当前价格',
                'open': '开盘价',
                'high': '最高价',
                'low': '最低价',
                'volume': '成交量',
                'decision': '决策建议',
                'reasons': '分析原因',
                
                # 投资工具
                'smart_stock_screener': '智能股票筛选器',
                'compound_calculator': '复利计算器',
                'stop_loss_calculator': '止损止盈计算器',
                'position_calculator': '仓位管理计算器',
                'risk_reward_calculator': '风险收益比计算器',
                'initial_investment': '初始投资',
                'annual_return': '年化收益率',
                'investment_years': '投资年限',
                'monthly_investment': '定期投入',
                'calculate': '计算',
                'result': '计算结果',
                
                # 设置页面
                'language_settings': '语言设置',
                'select_language': '选择语言',
                'chinese': '中文',
                'english': 'English',
                'auto_translate_news': '自动翻译新闻',
                'save_settings': '保存设置',
                'settings_saved': '设置已保存',
                
                # 通用
                'loading': '加载中...',
                'error': '错误',
                'no_data': '暂无数据',
                'retry': '重试',
                'close': '关闭',
                'confirm': '确认',
                'cancel': '取消',
                'search': '搜索',
                'filter': '筛选',
                'reset': '重置',
                'export': '导出',
                'import': '导入',
                'delete': '删除',
                'edit': '编辑',
                'add': '添加',
                'save': '保存',
            },
            'en': {
                # Navigation
                'market_dashboard': 'Market Dashboard',
                'stock_analysis': 'Stock Analysis',
                'fundamental_analysis': 'Fundamental Analysis',
                'risk_management': 'Risk Management',
                'portfolio': 'Portfolio',
                'investment_tools': 'Investment Tools',
                'settings': 'Settings',
                'login': 'Login',
                
                # Market Dashboard
                'market_indices': 'Market Indices',
                'sector_heatmap': 'Sector Heatmap',
                'market_sentiment': 'Market Sentiment',
                'top_gainers': 'Top Gainers',
                'top_losers': 'Top Losers',
                'volume_leaders': 'Volume Leaders',
                'market_news': 'Market News',
                'fear_greed_index': 'Fear & Greed Index',
                'vix_volatility': 'VIX Volatility',
                'advance_decline': 'Advance/Decline Ratio',
                'new_high_low': 'New High/Low Ratio',
                
                # Stock Analysis
                'smart_stock_analysis': 'Smart Stock Analysis',
                'enter_stock_code': 'Enter Stock Code',
                'smart_analysis': 'Smart Analysis',
                'hot_stocks': 'Hot Stocks',
                'current_price': 'Current Price',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'volume': 'Volume',
                'decision': 'Decision',
                'reasons': 'Reasons',
                
                # Investment Tools
                'smart_stock_screener': 'Smart Stock Screener',
                'compound_calculator': 'Compound Calculator',
                'stop_loss_calculator': 'Stop Loss Calculator',
                'position_calculator': 'Position Calculator',
                'risk_reward_calculator': 'Risk/Reward Calculator',
                'initial_investment': 'Initial Investment',
                'annual_return': 'Annual Return',
                'investment_years': 'Investment Years',
                'monthly_investment': 'Monthly Investment',
                'calculate': 'Calculate',
                'result': 'Result',
                
                # Settings
                'language_settings': 'Language Settings',
                'select_language': 'Select Language',
                'chinese': '中文',
                'english': 'English',
                'auto_translate_news': 'Auto Translate News',
                'save_settings': 'Save Settings',
                'settings_saved': 'Settings Saved',
                
                # Common
                'loading': 'Loading...',
                'error': 'Error',
                'no_data': 'No Data',
                'retry': 'Retry',
                'close': 'Close',
                'confirm': 'Confirm',
                'cancel': 'Cancel',
                'search': 'Search',
                'filter': 'Filter',
                'reset': 'Reset',
                'export': 'Export',
                'import': 'Import',
                'delete': 'Delete',
                'edit': 'Edit',
                'add': 'Add',
                'save': 'Save',
            }
        }

    def simple_translate(self, text: str, target_lang: str = 'zh') -> str:
        """简单的文本翻译，使用词典替换"""
        if not text or target_lang == 'en':
            return text
            
        # 如果目标语言是中文，进行英译中
        translated = text
        
        # 按长度排序，优先替换较长的词组
        sorted_terms = sorted(self.finance_terms.items(), key=lambda x: len(x[0]), reverse=True)
        
        for en_term, zh_term in sorted_terms:
            # 使用正则表达式进行单词边界匹配
            pattern = r'\b' + re.escape(en_term) + r'\b'
            translated = re.sub(pattern, zh_term, translated, flags=re.IGNORECASE)
        
        return translated

    def translate_news_item(self, news_item: Dict, target_lang: str = 'zh') -> Dict:
        """翻译新闻条目"""
        if target_lang == 'en':
            return news_item
            
        translated_item = news_item.copy()
        
        # 翻译标题和摘要
        translated_item['title'] = self.simple_translate(news_item['title'], target_lang)
        translated_item['summary'] = self.simple_translate(news_item['summary'], target_lang)
        
        # 添加翻译标记
        translated_item['translated'] = True
        translated_item['original_title'] = news_item['title']
        translated_item['original_summary'] = news_item['summary']
        
        return translated_item

    def translate_news_list(self, news_list: List[Dict], target_lang: str = 'zh') -> List[Dict]:
        """翻译新闻列表"""
        return [self.translate_news_item(item, target_lang) for item in news_list]

    def get_ui_text(self, key: str, lang: str = 'zh') -> str:
        """获取界面文本"""
        return self.ui_translations.get(lang, {}).get(key, key)

    def get_all_ui_texts(self, lang: str = 'zh') -> Dict:
        """获取所有界面文本"""
        return self.ui_translations.get(lang, {})

# 创建全局实例
translation_service = TranslationService()