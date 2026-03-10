#!/usr/bin/env python3
"""
A 股资金流向 - 主力资金、北向资金
数据源：腾讯财经 + 东方财富
"""

import sys
import json
import urllib.request
import re
from datetime import datetime

def get_capital_flow_data(symbol, market):
    """从东方财富获取资金流数据"""
    # 基金/股票通用 API
    url = f'http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{symbol}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f116,f117,f184'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://quote.eastmoney.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8')
            data = json.loads(content)
            
        if data.get('data'):
            f = data['data']
            return {
                'name': f.get('f58', 'N/A'),
                'current': f.get('f43', 0) / 100,  # 价格需要除以 100
                'turnover_rate': f.get('f184', 0),
                'total_market_cap': f.get('f116', 0),
                'float_market_cap': f.get('f117', 0),
            }
    except Exception as e:
        pass
    
    return None

def get_capital_flow(symbol):
    """获取资金流向数据"""
    # 判断市场
    if symbol.startswith('6'):
        market = 'sh'
        market_name = '沪市'
    elif symbol.startswith('0') or symbol.startswith('3'):
        market = 'sz'
        market_name = '深市'
    elif symbol.startswith('4') or symbol.startswith('8'):
        market = 'bj'
        market_name = '北交所'
    elif symbol.startswith('5') or symbol.startswith('1'):
        market = 'sh'
        market_name = '沪市基金'
    else:
        return {'error': '无法识别市场'}
    
    # 从东方财富获取基础数据
    em_data = get_capital_flow_data(symbol, '1' if market == 'sh' else '0')
    
    # 基金代码特殊处理链接
    if symbol.startswith('5') or symbol.startswith('1'):
        fund_prefix = 'sh' if market == 'sh' else 'sz'
        em_url = f'http://quote.eastmoney.com/{fund_prefix}{symbol}.html'
        fund_link = f'http://fund.eastmoney.com/{symbol}.html'
        quick_links = [
            {
                'name': '东方财富 - 基金详情',
                'url': fund_link,
                'desc': '基金净值、持仓、公告'
            },
            {
                'name': '天天基金网',
                'url': f'http://fundgz.1234567.com.cn/js/{symbol}.js',
                'desc': '实时净值估算'
            },
        ]
    else:
        em_url = f'http://quote.eastmoney.com/{market}{symbol}.html'
        quick_links = [
            {
                'name': '东方财富 - 资金流向',
                'url': em_url,
                'desc': 'F10 资料 - 资金流向页面'
            },
            {
                'name': '新浪财经 - 资金流向',
                'url': f'http://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?stockid={market}{symbol}',
                'desc': '主力资金、北向资金数据'
            },
            {
                'name': '同花顺 - 资金流向',
                'url': f'http://data.10jqka.com.cn/funds/ggzjl/field/zdf/order/desc/page/1/ajax/1/code/{market}{symbol}',
                'desc': '个股资金流向排行'
            }
        ]
    
    result = {
        'symbol': symbol,
        'market': market_name,
        'name': em_data['name'] if em_data else 'N/A',
        'current': em_data['current'] if em_data else 0,
        'turnover_rate': em_data['turnover_rate'] if em_data else 0,
        'total_market_cap': em_data['total_market_cap'] if em_data else 0,
        'float_market_cap': em_data['float_market_cap'] if em_data else 0,
        'quick_links': quick_links,
        'note': '基金请关注净值、持仓、费率等指标',
    }
    
    return result

def format_capital_flow(data):
    """格式化输出"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    def fmt_num(n):
        if n is None or n == 0:
            return 'N/A'
        # 东方财富市值单位是元，需要转换
        if abs(n) >= 100000000:
            return f"{n/100000000:.2f}亿"
        elif abs(n) >= 10000:
            return f"{n/10000:.2f}万"
        return f"{n:.2f}"
    
    is_fund = data.get('symbol', '').startswith('5') or data.get('symbol', '').startswith('1')
    
    output = f"💰 {data.get('name', data['symbol'])} ({data['symbol']})"
    if is_fund:
        output += " - 基金资金流\n"
    else:
        output += " - 资金流向\n"
    output += "═" * 50 + "\n\n"
    
    if data.get('current', 0) > 0:
        if is_fund:
            output += f"💰 净值：¥{data['current']:.4f}\n"
        else:
            output += f"💰 现价：¥{data['current']:.2f}\n"
    
    if data.get('turnover_rate', 0) > 0:
        output += f"🔄 换手率：{data['turnover_rate']:.2f}%\n"
    
    if data.get('total_market_cap', 0) > 0:
        output += f"💎 规模：{fmt_num(data['total_market_cap'])}\n"
    
    if data.get('float_market_cap', 0) > 0:
        output += f"💎 流通：{fmt_num(data['float_market_cap'])}\n"
    
    output += "\n" + "═" * 50 + "\n\n"
    output += "🔗 快速链接：\n"
    
    for link in data.get('quick_links', []):
        output += f"\n  • {link['name']}\n"
        output += f"    {link['url']}\n"
        output += f"    💡 {link['desc']}\n"
    
    output += "\n" + "═" * 50 + "\n"
    if is_fund:
        output += "💡 提示：\n"
        output += "• 关注基金净值、持仓、费率\n"
        output += "• ETF 可在场内实时交易\n"
    else:
        output += "💡 提示：\n"
        output += "• 主力净流入 > 0 表示资金流入\n"
        output += "• 北向资金仅适用于沪深股通标的\n"
    output += "• 数据仅供参考，投资需谨慎\n"
    
    return output

def main():
    if len(sys.argv) < 2:
        print("用法：python capital_flow.py <股票代码>")
        print("示例：python capital_flow.py 601318")
        sys.exit(1)
    
    symbol = sys.argv[1]
    data = get_capital_flow(symbol)
    print(format_capital_flow(data))

if __name__ == '__main__':
    main()
