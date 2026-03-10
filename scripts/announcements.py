#!/usr/bin/env python3
"""
A 股公告监控 - 抓取公司公告
数据源：巨潮资讯网 + 东方财富
"""

import sys
import json
import urllib.request
from datetime import datetime

def get_announcements(symbol, days=30):
    """获取公司公告/基金公告"""
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
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date
    if days > 0:
        from datetime import timedelta
        start_date = end_date - timedelta(days=days)
    
    result = {
        'symbol': symbol,
        'market': market_name,
        'days': days,
        'cninfo_url': f'http://www.cninfo.com.cn/new/commonUrl/pageOfDeclare?url=stock/{market}{symbol}',
        'eastmoney_url': f'http://quote.eastmoney.com/{market}{symbol}.html#f10',
        'note': '公告数据建议访问官方渠道查看',
    }
    
    # 尝试东方财富 F10 公告链接
    result['quick_links'] = [
        {
            'name': '巨潮资讯网',
            'url': result['cninfo_url'],
            'desc': '证监会指定信息披露网站'
        },
        {
            'name': '东方财富 F10',
            'url': result['eastmoney_url'],
            'desc': '个股资料 - 公告大全'
        }
    ]
    
    return result

def format_announcements(data):
    """格式化输出"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    output = f"📢 {data['symbol']} ({data['market']}) - 公告查询\n"
    output += "═" * 50 + "\n\n"
    
    if data.get('days', 0) > 0:
        output += f"📅 查询范围：最近 {data['days']} 天\n\n"
    
    output += "🔗 快速链接：\n"
    for link in data.get('quick_links', []):
        output += f"\n  • {link['name']}\n"
        output += f"    {link['url']}\n"
        output += f"    💡 {link['desc']}\n"
    
    output += "\n" + "═" * 50 + "\n"
    output += "💡 提示：点击链接查看完整公告列表\n"
    output += "💡 重要公告：年报、季报、重大事项等\n"
    
    return output

def main():
    if len(sys.argv) < 2:
        print("用法：python announcements.py <股票代码> [天数]")
        print("示例：python announcements.py 600519 30")
        sys.exit(1)
    
    symbol = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    data = get_announcements(symbol, days)
    print(format_announcements(data))

if __name__ == '__main__':
    main()
