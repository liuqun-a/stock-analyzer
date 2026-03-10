#!/usr/bin/env python3
"""
A 股财报分析 - 主要财务指标
数据源：东方财富 API
"""

import sys
import json
import urllib.request
from datetime import datetime

def get_financials(symbol):
    """获取主要财务指标"""
    # 判断市场
    if symbol.startswith('6'):
        market = '1'
    elif symbol.startswith('0') or symbol.startswith('3'):
        market = '0'
    elif symbol.startswith('4') or symbol.startswith('8'):
        market = '0'
    elif symbol.startswith('5') or symbol.startswith('1'):
        market = '1'  # 基金
    else:
        return {'error': '无法识别市场'}
    
    # 东方财富实时行情 API（包含部分财务指标）
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{symbol}&fields=f43,f57,f58,f105,f106,f107,f108,f116,f117,f127,f128,f160,f164,f184,f190"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'http://quote.eastmoney.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)
            
        if data.get('data'):
            f = data['data']
            return {
                'symbol': symbol,
                'name': f.get('f58', 'N/A'),
                'industry': f.get('f127', 'N/A'),  # 行业
                'concept': f.get('f129', 'N/A') if len(f.get('f129', '')) < 100 else 'N/A',  # 概念
                # 估值指标
                'pe_ttm': f.get('f164', 0) / 100 if f.get('f164') else 0,  # 市盈率 TTM
                'pe_ratio': f.get('f108', 0) / 100 if f.get('f108') else 0,  # 市盈率 (动)
                'pb_ratio': f.get('f107', 0) / 100 if f.get('f107') else 0,  # 市净率
                'ps_ratio': f.get('f106', 0) / 100 if f.get('f106') else 0,  # 市销率
                'pcf_ratio': f.get('f105', 0) / 100000000 if f.get('f105') else 0,  # 市现率
                # 市值
                'total_market_cap': f.get('f116', 0),  # 总市值
                'float_market_cap': f.get('f117', 0),  # 流通市值
                # 其他
                'dividend_yield': f.get('f190', 0) / 100 if f.get('f190') else 0,  # 股息率
                'turnover_rate': f.get('f184', 0),  # 换手率
                'current': f.get('f43', 0) / 100 if f.get('f43') else 0,  # 现价
            }
        return {'error': '数据获取失败'}
    except Exception as e:
        return {'error': str(e)}

def format_financials(data):
    """格式化输出"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    def fmt_num(n, unit=''):
        if n is None or n == 0:
            return 'N/A'
        if abs(n) >= 100000000:
            return f"{n/100000000:.2f}亿{unit}"
        elif abs(n) >= 10000:
            return f"{n/10000:.2f}万{unit}"
        return f"{n:.2f}{unit}"
    
    def fmt_ratio(n):
        if n is None or n == 0:
            return 'N/A'
        return f"{n:.2f}"
    
    return f"""
📊 {data['name']} ({data['symbol']}) - 财务指标
═══════════════════════════════════
🏷️ 行业：{data['industry']}

【估值指标】
📈 市盈率 (TTM): {fmt_ratio(data['pe_ttm'])}
📈 市盈率 (动): {fmt_ratio(data['pe_ratio'])}
📊 市净率：{fmt_ratio(data['pb_ratio'])}
📊 市销率：{fmt_ratio(data['ps_ratio'])}
📊 市现率：{fmt_num(data['pcf_ratio'])}
💰 股息率：{fmt_ratio(data['dividend_yield'])}%

【市值】
💎 总市值：{fmt_num(data['total_market_cap'])}
💎 流通市值：{fmt_num(data['float_market_cap'])}

【其他】
💰 现价：¥{data['current']:.2f}
🔄 换手率：{fmt_ratio(data['turnover_rate'])}%

═══════════════════════════════════
💡 提示：数据仅供参考，投资需谨慎
"""

def main():
    if len(sys.argv) < 2:
        print("用法：python financials.py <股票代码>")
        print("示例：python financials.py 000858")
        sys.exit(1)
    
    symbol = sys.argv[1]
    data = get_financials(symbol)
    print(format_financials(data))

if __name__ == '__main__':
    main()
