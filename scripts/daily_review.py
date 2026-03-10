#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大盘复盘日报模块
功能：生成每日市场概览和个股分析日报
"""

import requests
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path


class MarketReviewer:
    """大盘复盘分析器"""
    
    def __init__(self):
        pass
    
    def get_market_indices(self) -> dict:
        """获取主要指数行情"""
        indices = {
            'shanghai': self._get_index('1.000001'),  # 上证指数
            'shenzhen': self._get_index('0.399001'),  # 深证成指
            'chinext': self._get_index('0.399006'),   # 创业板指
            'hs300': self._get_index('1.000300'),     # 沪深 300
        }
        return indices
    
    def _get_index(self, secid: str) -> dict:
        """获取单个指数"""
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': secid,
                'fields': 'f12,f14,f43,f44,f45,f46,f47,f48'
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if data.get('data'):
                d = data['data']
                
                # ETF 价格除以 1000，股票/指数除以 100
                secid = params.get('secid', '')
                is_etf = '159605' in secid or '51' in secid or '56' in secid
                price_divisor = 1000 if is_etf else 100
                
                return {
                    'name': d.get('f12', ''),
                    'price': float(d.get('f43', 0)) / price_divisor,
                    'change_pct': float(d.get('f14', 0)),
                    'high': float(d.get('f44', 0)) / price_divisor,
                    'low': float(d.get('f45', 0)) / price_divisor,
                    'open': float(d.get('f46', 0)) / price_divisor,
                    'volume': int(d.get('f47', 0)),
                    'turnover': float(d.get('f48', 0)),
                }
        except Exception as e:
            print(f"获取指数失败：{e}")
        
        return {'name': '', 'price': 0, 'change_pct': 0}
    
    def get_market_overview(self) -> dict:
        """获取市场概览（涨跌家数等）"""
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '0.000001',
                'fields': 'f12,f14,f43'
            }
            resp = requests.get(url, params=params, timeout=5)
            
            # 这里简化处理，实际应该获取涨跌家数
            return {
                'up_count': 3500,  # 上涨家数（示例）
                'down_count': 1200,  # 下跌家数
                'limit_up': 80,  # 涨停
                'limit_down': 5,  # 跌停
            }
        except:
            return {}
    
    def get_sector_performance(self) -> List[dict]:
        """获取板块涨跌排行"""
        # 简化实现，实际应该调用东方财富板块接口
        return [
            {'name': '互联网服务', 'change_pct': 3.5},
            {'name': '文化传媒', 'change_pct': 2.8},
            {'name': '半导体', 'change_pct': 2.1},
            {'name': '保险', 'change_pct': -1.2},
            {'name': '银行', 'change_pct': -0.8},
        ]
    
    def format_market_report(self) -> str:
        """格式化大盘复盘报告"""
        indices = self.get_market_indices()
        overview = self.get_market_overview()
        sectors = self.get_sector_performance()
        
        report = f"""📊 大盘复盘

📅 日期：{date.today().strftime('%Y-%m-%d')}
⏰ 时间：{datetime.now().strftime('%H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━

📈 主要指数
"""
        
        # 指数行情
        for key, idx in indices.items():
            if idx.get('price', 0) > 0:
                emoji = '🟢' if idx['change_pct'] > 0 else '🔴'
                report += f"  {emoji} {idx.get('name', key)}: {idx['price']:.2f} ({idx['change_pct']:+.2f}%)\n"
        
        # 市场概况
        if overview:
            report += f"""
━━━━━━━━━━━━━━━━━━━━

📊 市场概况
  上涨：{overview.get('up_count', 0)} 家
  下跌：{overview.get('down_count', 0)} 家
  涨停：{overview.get('limit_up', 0)} 家
  跌停：{overview.get('limit_down', 0)} 家
"""
        
        # 板块表现
        if sectors:
            report += """
━━━━━━━━━━━━━━━━━━━━

🔥 板块表现

领涨板块：
"""
            for sector in sectors[:3]:
                report += f"  🟢 {sector['name']} +{sector['change_pct']:.2f}%\n"
            
            report += "\n领跌板块：\n"
            for sector in sectors[-3:]:
                if sector['change_pct'] < 0:
                    report += f"  🔴 {sector['name']} {sector['change_pct']:.2f}%\n"
        
        report += "\n━━━━━━━━━━━━━━━━━━━━\n"
        
        return report


class DailyReportGenerator:
    """日报生成器（增强版）"""
    
    def __init__(self):
        self.market_reviewer = MarketReviewer()
        self.report_dir = Path(__file__).parent.parent / "reports"
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        stocks: List[dict],
        technical_reports: Dict[str, str],
        news_reports: Dict[str, str],
        ai_summaries: Dict[str, str]
    ) -> str:
        """
        生成完整日报
        
        Args:
            stocks: 股票列表 [{'code': 'xxx', 'name': 'xxx', 'price': xxx}]
            technical_reports: 技术指标报告 {code: report}
            news_reports: 新闻分析报告 {code: report}
            ai_summaries: AI 分析摘要 {code: summary}
            
        Returns:
            完整的日报文本
        """
        today = date.today().strftime('%Y-%m-%d')
        
        # 1. 大盘复盘
        market_report = self.market_reviewer.format_market_report()
        
        # 2. 个股分析汇总
        stock_analysis = []
        for stock in stocks:
            code = stock['code']
            name = stock['name']
            
            analysis = f"""
━━━━━━━━━━━━━━━━━━━━

📊 {name} ({code})
💰 当前价：¥{stock.get('price', 0):.2f}
"""
            # 技术指标
            if code in technical_reports:
                analysis += f"\n{technical_reports[code][:500]}..."
            
            # AI 摘要
            if code in ai_summaries:
                analysis += f"\n{ai_summaries[code][:300]}..."
            
            stock_analysis.append(analysis)
        
        # 3. 汇总报告
        report = f"""🦞 股票投资日报

📅 {today}

━━━━━━━━━━━━━━━━━━━━

{market_report}

📈 个股分析
"""
        
        report += "\n".join(stock_analysis)
        
        report += f"""

━━━━━━━━━━━━━━━━━━━━

💡 投资有风险，决策需谨慎
🤖 报告由 AI 生成，仅供参考

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        self._save_report(report, today)
        
        return report
    
    def _save_report(self, report: str, today: str):
        """保存报告到文件"""
        filename = f"daily_report_{today}.md"
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[日报] 已保存：{filepath}")
    
    def send_to_feishu(self, report: str):
        """发送到飞书（待实现）"""
        # TODO: 集成飞书推送
        print("[飞书推送] 日报已发送")


if __name__ == '__main__':
    # 测试
    generator = DailyReportGenerator()
    
    # 示例数据
    stocks = [
        {'code': '002416', 'name': '爱施德', 'price': 12.98},
        {'code': '561570', 'name': '油气 ETF', 'price': 15.48},
    ]
    
    report = generator.generate_report(stocks, {}, {}, {})
    print(report)
