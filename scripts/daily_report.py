#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日交易报告生成
功能：
- 汇总全天预警记录
- 持仓股票表现
- 资金流向 Top5
- 自动生成飞书文档/消息
"""

import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import requests

# 配置路径
BASE_DIR = Path(__file__).parent.parent  # 返回到 stock-analyzer 根目录
CONFIG_DIR = BASE_DIR / "config"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)


class DailyReportGenerator:
    """日报生成器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def _load_config(self) -> dict:
        with open(CONFIG_DIR / "stocks.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def generate_report(self) -> dict:
        """生成日报"""
        report = {
            'date': self.today,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_summary': self._get_market_summary(),
            'stock_performance': self._get_stock_performance(),
            'alerts_summary': self._get_alerts_summary(),
            'capital_flow': self._get_capital_flow_top(),
            'tomorrow_watch': self._get_tomorrow_watch()
        }
        
        # 保存报告
        self._save_report(report)
        
        return report
        
    def _get_market_summary(self) -> dict:
        """获取市场概览"""
        # 上证指数
        sh = self._get_index_quote('000001')
        # 深证成指
        sz = self._get_index_quote('399001')
        # 恒生指数（港股）
        hk = self._get_index_quote('HSI')
        
        return {
            'shanghai': sh,
            'shenzhen': sz,
            'hangseng': hk
        }
        
    def _get_index_quote(self, index_code: str) -> dict:
        """获取指数行情"""
        try:
            if index_code == 'HSI':
                # 恒生指数
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    'secid': '116.HSI',
                    'fields': 'f43,f14'
                }
            elif index_code == '000001':
                # 上证指数
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    'secid': '1.000001',
                    'fields': 'f43,f14'
                }
            else:
                # 深证成指
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    'secid': '0.399001',
                    'fields': 'f43,f14'
                }
                
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                return {
                    'price': float(result.get('f43', 0)) / 100,
                    'change_pct': float(result.get('f14', 0))
                }
        except Exception as e:
            print(f"[指数行情] 错误：{e}")
            
        return {'price': 0, 'change_pct': 0}
        
    def _get_stock_performance(self) -> List[dict]:
        """获取监控股票表现"""
        performance = []
        
        all_stocks = self.config.get('a_shares', []) + self.config.get('hk_shares', [])
        
        for stock in all_stocks:
            if not stock.get('enabled', True):
                continue
                
            code = stock['code']
            market = 'A' if code in [s['code'] for s in self.config.get('a_shares', [])] else 'HK'
            
            quote = self._get_quote(code, market)
            if quote:
                performance.append({
                    'code': code,
                    'name': stock['name'],
                    'market': market,
                    'price': quote.get('price', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'volume': quote.get('volume', 0)
                })
                
        # 按涨跌幅排序
        performance.sort(key=lambda x: x['change_pct'], reverse=True)
        
        return performance
        
    def _get_quote(self, code: str, market: str) -> dict:
        """获取个股行情"""
        try:
            if market == 'A':
                if code.startswith('6'):
                    symbol = f"1{code}"
                else:
                    symbol = f"0{code}"
            else:
                symbol = f"116.{code}"
                
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': symbol,
                'fields': 'f43,f14,f47'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                # ETF 价格除以 1000，股票除以 100
                is_etf = code.startswith('51') or code.startswith('56') or \
                         code.startswith('15') or code.startswith('16')
                price_divisor = 1000 if is_etf else 100
                
                return {
                    'price': float(result.get('f43', 0)) / price_divisor,
                    'change_pct': float(result.get('f14', 0)),
                    'volume': int(result.get('f47', 0))
                }
        except Exception as e:
            print(f"[个股行情] 错误：{e}")
        return {}
        
    def _get_alerts_summary(self) -> dict:
        """获取预警汇总（从缓存读取）"""
        # TODO: 实际应该从预警日志读取
        return {
            'total': 0,
            'price_alerts': 0,
            'volume_alerts': 0,
            'details': []
        }
        
    def _get_capital_flow_top(self) -> List[dict]:
        """获取资金流向 Top5"""
        # TODO: 调用资金流接口
        return []
        
    def _get_tomorrow_watch(self) -> List[dict]:
        """明日关注股票"""
        # 简单逻辑：今日涨幅前 3 + 跌幅前 3
        performance = self._get_stock_performance()
        watch = []
        
        if len(performance) >= 3:
            # 涨幅前 3
            for stock in performance[:3]:
                watch.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'reason': f"今日涨幅 {stock['change_pct']:+.2f}%"
                })
            # 跌幅前 3
            for stock in performance[-3:]:
                watch.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'reason': f"今日跌幅 {stock['change_pct']:+.2f}%"
                })
                
        return watch
        
    def _save_report(self, report: dict):
        """保存报告到文件"""
        filename = f"report_{self.today}.json"
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"[日报] 已保存：{filepath}")
        
    def format_message(self, report: dict) -> str:
        """格式化飞书消息"""
        market = report.get('market_summary', {})
        sh = market.get('shanghai', {})
        sz = market.get('shenzhen', {})
        hk = market.get('hangseng', {})
        
        performance = report.get('stock_performance', [])
        top_gainer = performance[0] if performance else {}
        top_loser = performance[-1] if performance else {}
        
        message = f"""📊 交易日报

📅 日期：{report.get('date')}
⏰ 生成时间：{report.get('generated_at')}

━━━━━━━━━━━━━━━━━━━━

📈 市场概览
━━━━━━━━━━━━━━━━━━━━
上证指数：{sh.get('price', 0):.2f} ({sh.get('change_pct', 0):+.2f}%)
深证成指：{sz.get('price', 0):.2f} ({sz.get('change_pct', 0):+.2f}%)
恒生指数：{hk.get('price', 0):.2f} ({hk.get('change_pct', 0):+.2f}%)

━━━━━━━━━━━━━━━━━━━━

🏆 今日表现
━━━━━━━━━━━━━━━━━━━━
✅ 最佳：{top_gainer.get('name', 'N/A')} ({top_gainer.get('change_pct', 0):+.2f}%)
❌ 最差：{top_loser.get('name', 'N/A')} ({top_loser.get('change_pct', 0):+.2f}%)

━━━━━━━━━━━━━━━━━━━━

👀 明日关注
━━━━━━━━━━━━━━━━━━━━
"""
        for stock in report.get('tomorrow_watch', [])[:5]:
            message += f"• {stock['name']} - {stock['reason']}\n"
            
        message += "\n━━━━━━━━━━━━━━━━━━━━\n"
        message += f"⚠️ 预警统计：{report.get('alerts_summary', {}).get('total', 0)} 次\n"
        message += "\n投资有风险，决策需谨慎 🦞"
        
        return message


def main():
    generator = DailyReportGenerator()
    report = generator.generate_report()
    message = generator.format_message(report)
    
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)
    
    # TODO: 发送到飞书
    # send_to_feishu(message)


if __name__ == '__main__':
    main()
