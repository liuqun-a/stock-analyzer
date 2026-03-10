#!/usr/bin/env python3
"""
A 股行情查询 - 实时股价、K 线数据
数据源：东方财富 API
"""

import sys
import json
import urllib.request
from datetime import datetime

def get_quote(symbol):
    """获取实时行情"""
    # 判断市场 - 东方财富 secid 格式：1=沪市，0=深市
    if symbol.startswith('6'):
        market = '1'
    elif symbol.startswith('0') or symbol.startswith('3'):
        market = '0'
    elif symbol.startswith('4') or symbol.startswith('8'):
        market = '0'  # 北交所也用 0
    elif symbol.startswith('5') or symbol.startswith('1'):
        market = '1'  # 基金（51/56 开头 ETF 等）
    else:
        return {'error': '无法识别市场，请输入 6 位代码'}
    
    # 东方财富实时行情 API - f57=代码，f58=名称，f184=换手率
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{symbol}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f107,f108,f116,f117,f184"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'http://quote.eastmoney.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)
            
        if data.get('data'):
            f = data['data']
            # 东方财富价格单位需要除以 100
            return {
                'symbol': symbol,
                'name': f.get('f58', f.get('f14', 'N/A')),  # f58=股票名称
                'current': f.get('f43', 0) / 100,  # 最新价
                'open': f.get('f46', 0) / 100,     # 开盘
                'high': f.get('f44', 0) / 100,     # 最高
                'low': f.get('f45', 0) / 100,      # 最低
                'pre_close': f.get('f60', 0) / 100, # 昨收
                'volume': f.get('f47', 0),   # 成交量 (手)
                'amount': f.get('f48', 0),   # 成交额 (元)
                'turnover_rate': f.get('f184', 0),  # 换手率 (%)
                'pe_ratio': f.get('f108', 0),  # 市盈率
                'pb_ratio': f.get('f107', 0),  # 市净率
                'total_market_cap': f.get('f116', 0),  # 总市值
                'float_market_cap': f.get('f117', 0),  # 流通市值
            }
        return {'error': '数据获取失败'}
    except Exception as e:
        return {'error': str(e)}

def format_quote(data):
    """格式化输出"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    change = data['current'] - data['pre_close']
    change_pct = (change / data['pre_close'] * 100) if data['pre_close'] else 0
    arrow = '📈' if change >= 0 else '📉'
    
    return f"""
{arrow} {data['name']} ({data['symbol']})
━━━━━━━━━━━━━━━━
💰 现价：¥{data['current']:.2f}
📊 涨跌：{change:+.2f} ({change_pct:+.2f}%)
━━━━━━━━━━━━━━━━
📌 开盘：¥{data['open']:.2f}
🔝 最高：¥{data['high']:.2f}
🔻 最低：¥{data['low']:.2f}
📉 昨收：¥{data['pre_close']:.2f}
━━━━━━━━━━━━━━━━
📦 成交量：{data['volume']/10000:.1f}万手
💵 成交额：{data['amount']/100000000:.2f}亿元
🔄 换手率：{data['turnover_rate']:.2f}%
━━━━━━━━━━━━━━━━
📈 市盈率：{data['pe_ratio']:.2f}
📊 市净率：{data['pb_ratio']:.2f}
💎 总市值：{data['total_market_cap']/100000000:.2f}亿
💎 流通值：{data['float_market_cap']/100000000:.2f}亿
"""

def main():
    if len(sys.argv) < 2:
        print("用法：python quote.py <股票代码>")
        print("示例：python quote.py 600519")
        sys.exit(1)
    
    symbol = sys.argv[1]
    data = get_quote(symbol)
    print(format_quote(data))

if __name__ == '__main__':
    main()
