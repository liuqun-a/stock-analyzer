#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版股票监控脚本
集成：技术指标 + 新闻搜索 + AI 分析 + 大盘复盘
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from technical import TechnicalAnalyzer
from news_search import MarketNewsAnalyzer
from ai_summary import generate_ai_summary, format_ai_report
from daily_review import MarketReviewer, DailyReportGenerator


class EnhancedStockMonitor:
    """增强版股票监控器"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.news_analyzer = MarketNewsAnalyzer()
        self.market_reviewer = MarketReviewer()
        self.report_generator = DailyReportGenerator()
        
        # 数据缓存
        self.technical_cache: Dict[str, str] = {}
        self.news_cache: Dict[str, str] = {}
        self.ai_cache: Dict[str, str] = {}
    
    def analyze_stock(self, code: str, name: str, current_price: float, df) -> dict:
        """
        分析单只股票（完整流程）
        
        Args:
            code: 股票代码
            name: 股票名称
            current_price: 当前价格
            df: 历史 K 线数据（DataFrame）
            
        Returns:
            分析结果字典
        """
        result = {
            'code': code,
            'name': name,
            'price': current_price,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 1. 技术指标分析
        try:
            indicators = self.technical_analyzer.analyze(df)
            result['technical'] = {
                'ma5': indicators.ma5,
                'ma10': indicators.ma10,
                'ma20': indicators.ma20,
                'macd_dif': indicators.macd_dif,
                'rsi6': indicators.rsi6,
                'trend': indicators.trend,
                'signal': indicators.signal,
                'signal_strength': indicators.signal_strength
            }
            result['technical_report'] = self.technical_analyzer.format_report(
                code, name, indicators, current_price
            )
        except Exception as e:
            print(f"[{code}] 技术分析失败：{e}")
            result['technical'] = None
            result['technical_report'] = ''
        
        # 2. 新闻搜索（可选，耗时较长）
        try:
            news_analysis = self.news_analyzer.analyze_stock(code, name)
            result['news'] = news_analysis
            result['news_report'] = self.news_analyzer.format_news_report(
                code, name, news_analysis
            )
        except Exception as e:
            print(f"[{code}] 新闻搜索失败：{e}")
            result['news'] = None
            result['news_report'] = ''
        
        # 3. AI 分析摘要
        try:
            ai_summary = generate_ai_summary(
                code=code,
                name=name,
                current_price=current_price,
                technical_report=result['technical_report'],
                news_report=result['news_report'],
                market_context=''
            )
            result['ai_summary'] = ai_summary
            result['ai_report'] = format_ai_report(ai_summary, code, name)
        except Exception as e:
            print(f"[{code}] AI 分析失败：{e}")
            result['ai_summary'] = None
            result['ai_report'] = ''
        
        return result
    
    def generate_daily_report(self, stocks: List[dict]) -> str:
        """
        生成每日复盘报告
        
        Args:
            stocks: 股票分析结果列表
            
        Returns:
            完整的日报文本
        """
        # 大盘复盘
        market_report = self.market_reviewer.format_market_report()
        
        # 个股分析汇总
        stock_sections = []
        for stock in stocks:
            section = f"""
━━━━━━━━━━━━━━━━━━━━

📊 {stock['name']} ({stock['code']})
💰 当前价：¥{stock['price']:.2f}

"""
            if stock.get('technical_report'):
                section += f"{stock['technical_report'][:500]}...\n"
            
            if stock.get('ai_report'):
                section += f"\n{stock['ai_report'][:400]}...\n"
            
            stock_sections.append(section)
        
        # 组合报告
        report = f"""🦞 股票投资日报

📅 {datetime.now().strftime('%Y-%m-%d')}

━━━━━━━━━━━━━━━━━━━━

{market_report}

📈 个股分析
"""
        report += "\n".join(stock_sections)
        
        report += f"""

━━━━━━━━━━━━━━━━━━━━

💡 投资有风险，决策需谨慎
🤖 报告由 AI 生成，仅供参考

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def check_signals(self, analysis_result: dict) -> List[dict]:
        """
        检查买卖信号
        
        Args:
            analysis_result: 股票分析结果
            
        Returns:
            信号列表
        """
        signals = []
        
        tech = analysis_result.get('technical')
        if tech:
            # 技术指标信号
            if tech['signal'] == 'buy' and tech['signal_strength'] >= 3:
                signals.append({
                    'type': 'technical_buy',
                    'level': 'high' if tech['signal_strength'] >= 4 else 'medium',
                    'message': f"技术指标买入信号（强度：{'⭐' * tech['signal_strength']}）"
                })
            elif tech['signal'] == 'sell' and tech['signal_strength'] >= 3:
                signals.append({
                    'type': 'technical_sell',
                    'level': 'high' if tech['signal_strength'] >= 4 else 'medium',
                    'message': f"技术指标卖出信号（强度：{'⭐' * tech['signal_strength']}）"
                })
        
        # AI 建议
        ai = analysis_result.get('ai_summary')
        if ai and ai.suggestion in ['buy', 'sell']:
            signals.append({
                'type': 'ai_suggestion',
                'level': 'medium',
                'message': f"AI 建议：{ai.suggestion.upper()}（置信度：{ai.confidence}%）"
            })
        
        return signals


if __name__ == '__main__':
    print("🦞 增强版股票监控器")
    print("=" * 60)
    
    monitor = EnhancedStockMonitor()
    
    # 示例：分析 002416
    print("\n测试分析 002416 爱施德...")
    
    # 模拟数据（实际应该从 API 获取）
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=60, freq='D')
    prices = 13 + np.cumsum(np.random.randn(60)) * 0.3
    prices = np.maximum(prices, 10)
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    result = monitor.analyze_stock('002416', '爱施德', 12.98, df)
    
    print(f"\n✅ 分析完成")
    print(f"  代码：{result['code']}")
    print(f"  名称：{result['name']}")
    print(f"  价格：¥{result['price']}")
    
    if result.get('technical'):
        print(f"\n📊 技术指标:")
        print(f"  信号：{result['technical']['signal']}")
        print(f"  强度：{'⭐' * result['technical']['signal_strength']}")
        print(f"  趋势：{result['technical']['trend']}")
    
    if result.get('ai_summary'):
        print(f"\n🤖 AI 分析:")
        print(f"  结论：{result['ai_summary'].conclusion}")
        print(f"  建议：{result['ai_summary'].suggestion.upper()}")
        print(f"  置信度：{result['ai_summary'].confidence}%")
    
    # 检查信号
    signals = monitor.check_signals(result)
    if signals:
        print(f"\n📬 检测到的信号:")
        for signal in signals:
            print(f"  [{signal['level']}] {signal['message']}")
    
    print("\n" + "=" * 60)
    print("✅ 增强版监控器测试完成")
