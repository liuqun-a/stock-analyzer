#!/usr/bin/env python3
"""
A 股短期走势分析 - 技术面 + 基本面
"""

import sys
import json
import urllib.request
import re
from datetime import datetime

def get_fund_data(symbol):
    """获取基金数据"""
    # 净值估算
    url = f'http://fundgz.1234567.com.cn/js/{symbol}.js'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8')
            match = re.search(r'\((.*)\);', content)
            if match:
                data = json.loads(match.group(1))
                return {
                    'name': data.get('name', ''),
                    'date': data.get('jzrq', ''),
                    'nav': float(data.get('dwjz', 0)),  # 单位净值
                    'estimate': float(data.get('gsz', 0)),  # 估算净值
                    'estimate_change': float(data.get('gszzl', 0)),  # 估算涨幅
                }
    except:
        pass
    return None

def get_oil_price():
    """获取国际油价"""
    prices = {}
    
    # WTI 原油
    try:
        url = 'http://qt.gtimg.cn/q=hf_CL'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('gbk', errors='ignore')
            match = re.search(r'="([^"]+)"', content)
            if match:
                data = match.group(1).split(',')
                prices['wti'] = {
                    'price': float(data[0]) if data[0] else 0,
                    'change': float(data[1]) if data[1] else 0,
                    'name': data[-1] if len(data) > 6 else 'WTI',
                }
    except:
        pass
    
    # 布伦特原油
    try:
        url = 'http://qt.gtimg.cn/q=hf_OIL'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('gbk', errors='ignore')
            match = re.search(r'="([^"]+)"', content)
            if match:
                data = match.group(1).split(',')
                prices['brent'] = {
                    'price': float(data[0]) if data[0] else 0,
                    'change': float(data[1]) if data[1] else 0,
                    'name': data[-1] if len(data) > 6 else '布伦特',
                }
    except:
        pass
    
    return prices

def analyze_short_term(symbol):
    """短期走势分析"""
    fund_data = get_fund_data(symbol)
    oil_prices = get_oil_price()
    
    result = {
        'symbol': symbol,
        'fund': fund_data,
        'oil': oil_prices,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    
    return result

def format_analysis(data):
    """格式化分析报告"""
    output = f"📊 {data['symbol']} 短期走势分析\n"
    output += "═" * 50 + "\n"
    output += f"⏰ 分析时间：{data['timestamp']}\n\n"
    
    # 基金数据
    if data.get('fund'):
        f = data['fund']
        output += "【基金净值】\n"
        output += f"📅 最新净值日期：{f['date']}\n"
        output += f"💰 单位净值：¥{f['nav']:.4f}\n"
        output += f"📈 估算净值：¥{f['estimate']:.4f}\n"
        output += f"📊 估算涨幅：{f['estimate_change']:+.2f}%\n\n"
    
    # 油价数据
    if data.get('oil'):
        output += "【国际油价】\n"
        for key, oil in data['oil'].items():
            arrow = '📈' if oil['change'] > 0 else '📉' if oil['change'] < 0 else '➖'
            pct = (oil['change'] / (oil['price'] - oil['change']) * 100) if oil['price'] != oil['change'] else 0
            output += f"{arrow} {oil['name']}: ${oil['price']:.2f} ({oil['change']:+.2f}, {pct:+.2f}%)\n"
        output += "\n"
    
    # 走势分析
    output += "【短期走势判断】\n"
    
    fund_change = data.get('fund', {}).get('estimate_change', 0)
    oil_wti_change = data.get('oil', {}).get('wti', {}).get('change', 0)
    oil_brent_change = data.get('oil', {}).get('brent', {}).get('change', 0)
    
    # 分析逻辑
    if oil_wti_change > 3 or oil_brent_change > 3:
        output += "🟢 利好因素：国际油价大幅上涨，直接利好油气 ETF\n"
    elif oil_wti_change > 0 or oil_brent_change > 0:
        output += "🟡 中性偏多：油价小幅上涨，对 ETF 有支撑\n"
    else:
        output += "🔴 利空因素：油价下跌，ETF 承压\n"
    
    if abs(fund_change) > 2:
        output += f"📊 ETF 日内波动较大 ({fund_change:+.2f}%)，注意风险\n"
    
    output += "\n【操作建议】\n"
    if oil_wti_change > 5 or oil_brent_change > 5:
        output += "⚠️ 油价大涨后可能回调，追高需谨慎\n"
        output += "💡 可关注回调后的布局机会\n"
    elif oil_wti_change > 0:
        output += "💡 趋势向好，可持有观望\n"
    else:
        output += "💡 注意止损，控制仓位\n"
    
    output += "\n" + "═" * 50 + "\n"
    output += "⚠️ 风险提示：\n"
    output += "• ETF 跟踪误差可能影响实际收益\n"
    output += "• 油价波动大，注意仓位控制\n"
    output += "• 以上分析仅供参考，不构成投资建议\n"
    
    return output

def main():
    if len(sys.argv) < 2:
        print("用法：python analysis.py <基金/股票代码>")
        print("示例：python analysis.py 561570")
        sys.exit(1)
    
    symbol = sys.argv[1]
    data = analyze_short_term(symbol)
    print(format_analysis(data))

if __name__ == '__main__':
    main()
