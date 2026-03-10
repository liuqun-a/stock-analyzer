#!/usr/bin/env python3
"""
A 股条件选股 - 按 PE/PB/ROE/市值等条件筛选股票
数据源：东方财富 API
"""

import sys
import json
import urllib.request
import argparse

# ==================== 获取全市场股票列表 ====================

def get_all_stocks(market='all'):
    """
    获取全市场股票列表
    
    Args:
        market: 'all'=全部，'sh'=沪市，'sz'=深市，'bj'=北交所
    
    Returns:
        list: 股票列表，每项包含 {'code': '600519', 'name': '贵州茅台'}
    """
    stocks = []
    
    # 东方财富股票列表 API（简化版，只获取基本数据）
    # 沪市：m=1，深市：m=0
    markets = []
    if market == 'all' or market == 'sh':
        markets.append('m:1')  # 沪市
    if market == 'all' or market == 'sz':
        markets.append('m:0')  # 深市
    if market == 'all' or market == 'bj':
        markets.append('m:0')  # 北交所（和深市一起）
    
    for m in markets:
        try:
            # 分页获取，每页 100 条
            for pn in range(1, 20):  # 最多获取 20 页（2000 只股票）
                url = f"http://nufm.dfcfw.com/EM_Fund2099/QF_ColStockItems/JS/RealTimeRankData.js?ct=1&cmd=C&st=z&sr=1&p={pn}&ps=100&js=var%20data={{data:(x)}}&token=894050c76af8597a853f67180e13c6ae&type=z&fs={m}&fields=f12,f14,f2,f3,f9,f10,f11"
                
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Referer': 'http://quote.eastmoney.com/',
                })
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read().decode('utf-8')
                    # 解析 JSONP: var data={data:(x)}
                    import re
                    match = re.search(r'var\s+data=\{data:\((.*)\)\}', content)
                    if not match:
                        continue
                    json_str = '{' + match.group(1) + '}'
                    data = json.loads(json_str)
                
                if not data.get('data') or not data['data'].get('diff'):
                    break
                
                for stock in data['data']['diff']:
                    # 过滤掉非股票（指数、基金、债券等）
                    code = stock.get('f12', '')
                    if not code or code.startswith(('SH', 'SZ', 'BJ', 'HK')):
                        continue
                    # 过滤掉名称带特殊标记的（ST、退市等可以保留，但指数要过滤）
                    name = stock.get('f14', '')
                    if '指数' in name or 'ETF' in name or 'LOF' in name:
                        continue
                    
                    # 处理 PE 数据（可能是"-"字符串）
                    pe_ttm = stock.get('f9')
                    if pe_ttm == '-' or pe_ttm is None:
                        pe_ttm = None
                    else:
                        pe_ttm = float(pe_ttm)
                    
                    pe_ratio = stock.get('f10')
                    if pe_ratio == '-' or pe_ratio is None:
                        pe_ratio = None
                    else:
                        pe_ratio = float(pe_ratio)
                    
                    pb_ratio = stock.get('f11')
                    if pb_ratio == '-' or pb_ratio is None:
                        pb_ratio = None
                    else:
                        pb_ratio = float(pb_ratio)
                    
                    stocks.append({
                        'code': code,
                        'name': name,
                        'price': float(stock.get('f2', 0) or 0),
                        'change_pct': float(stock.get('f3', 0) or 0),
                        'pe_ttm': pe_ttm,  # 市盈率 TTM
                        'pe_ratio': pe_ratio,  # 市盈率 (动)
                        'pb_ratio': pb_ratio,  # 市净率
                    })
                
                # 如果返回少于 100 条，说明是最后一页
                if len(data['data']['diff']) < 100:
                    break
                    
        except Exception as e:
            print(f"⚠️  获取{m}市场数据失败：{e}")
            continue
    
    return stocks

# ==================== 条件筛选 ====================

def filter_stocks(stocks, conditions):
    """
    按条件筛选股票
    
    Args:
        stocks: 股票列表
        conditions: 筛选条件 dict
    
    Returns:
        list: 符合条件的股票
    """
    filtered = []
    
    for stock in stocks:
        match = True
        
        # 价格条件
        if 'price_min' in conditions:
            if stock['price'] is None or stock['price'] < conditions['price_min']:
                match = False
        if 'price_max' in conditions:
            if stock['price'] is None or stock['price'] > conditions['price_max']:
                match = False
        
        # 涨跌幅条件
        if 'change_pct_min' in conditions:
            if stock['change_pct'] < conditions['change_pct_min']:
                match = False
        if 'change_pct_max' in conditions:
            if stock['change_pct'] > conditions['change_pct_max']:
                match = False
        
        # PE 条件（TTM）
        if 'pe_min' in conditions:
            if stock['pe_ttm'] is None or stock['pe_ttm'] < conditions['pe_min']:
                match = False
        if 'pe_max' in conditions:
            if stock['pe_ttm'] is None or stock['pe_ttm'] > conditions['pe_max']:
                match = False
        
        # PB 条件
        if 'pb_min' in conditions:
            if stock['pb_ratio'] is None or stock['pb_ratio'] < conditions['pb_min']:
                match = False
        if 'pb_max' in conditions:
            if stock['pb_ratio'] is None or stock['pb_ratio'] > conditions['pb_max']:
                match = False
        
        if match:
            filtered.append(stock)
    
    return filtered

# ==================== 格式化输出 ====================

def format_results(stocks, sort_by='pe_ttm', top_n=20):
    """格式化输出筛选结果"""
    if not stocks:
        return "❌ 没有符合条件的股票"
    
    # 排序
    if sort_by == 'pe_ttm':
        stocks = sorted(stocks, key=lambda x: x['pe_ttm'] if x['pe_ttm'] else 999999)
    elif sort_by == 'pb_ratio':
        stocks = sorted(stocks, key=lambda x: x['pb_ratio'] if x['pb_ratio'] else 999999)
    elif sort_by == 'market_cap':
        stocks = sorted(stocks, key=lambda x: x['total_market_cap'] if x['total_market_cap'] else 0, reverse=True)
    elif sort_by == 'change_pct':
        stocks = sorted(stocks, key=lambda x: x['change_pct'], reverse=True)
    
    # 取前 N 只
    top_stocks = stocks[:top_n]
    
    output = f"""
📊 条件选股结果
═══════════════════════════════════
✅ 符合条件：{len(stocks)} 只
📋 显示前：{len(top_stocks)} 只

【股票列表】
"""
    
    for i, stock in enumerate(top_stocks, 1):
        arrow = '📈' if stock['change_pct'] >= 0 else '📉'
        pe = f"{stock['pe_ttm']:.1f}" if stock['pe_ttm'] else 'N/A'
        pb = f"{stock['pb_ratio']:.2f}" if stock['pb_ratio'] else 'N/A'
        
        output += f"""
{i}. {stock['name']} ({stock['code']})
   💰 {stock['price']:.2f} {arrow} {stock['change_pct']:+.2f}%
   📊 PE: {pe}  |  PB: {pb}
"""
    
    output += f"""
═══════════════════════════════════
💡 提示：
- PE < 20：低估
- PE > 50：高估
- PB < 1：破净
- PB > 5：高估值

⚠️ 数据仅供参考，投资需谨慎
"""
    
    return output

# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(description='A 股条件选股')
    parser.add_argument('--market', choices=['all', 'sh', 'sz', 'bj'], default='all', help='市场（all/sh/sz/bj）')
    
    # 价格条件
    parser.add_argument('--price-min', type=float, help='最低股价')
    parser.add_argument('--price-max', type=float, help='最高股价')
    
    # 涨跌幅条件
    parser.add_argument('--change-min', type=float, help='最小涨跌幅%')
    parser.add_argument('--change-max', type=float, help='最大涨跌幅%')
    
    # PE 条件
    parser.add_argument('--pe-min', type=float, help='最小市盈率')
    parser.add_argument('--pe-max', type=float, help='最大市盈率')
    
    # PB 条件
    parser.add_argument('--pb-min', type=float, help='最小市净率')
    parser.add_argument('--pb-max', type=float, help='最大市净率')
    

    
    # 排序和显示
    parser.add_argument('--sort', choices=['pe_ttm', 'pb_ratio', 'market_cap', 'change_pct'], default='pe_ttm', help='排序方式')
    parser.add_argument('--top', type=int, default=20, help='显示前 N 只（默认 20）')
    
    args = parser.parse_args()
    
    # 构建筛选条件
    conditions = {}
    if args.price_min: conditions['price_min'] = args.price_min
    if args.price_max: conditions['price_max'] = args.price_max
    if args.change_min: conditions['change_pct_min'] = args.change_min
    if args.change_max: conditions['change_pct_max'] = args.change_max
    if args.pe_min: conditions['pe_min'] = args.pe_min
    if args.pe_max: conditions['pe_max'] = args.pe_max
    if args.pb_min: conditions['pb_min'] = args.pb_min
    if args.pb_max: conditions['pb_max'] = args.pb_max
    
    # 检查是否有筛选条件
    if not conditions:
        print("❌ 请至少指定一个筛选条件")
        print("\n📖 使用示例：")
        print("  # 低估值股票（PE < 20）")
        print("  python screen_stocks.py --pe-max 20")
        print("\n  # 破净股票（PB < 1）")
        print("  python screen_stocks.py --pb-max 1")
        print("\n  # 小盘低估值（市值<50 亿，PE < 30）")
        print("  python screen_stocks.py --market-cap-max 50 --pe-max 30")
        print("\n  # 绩优股（PE 20-50，涨幅>3%）")
        print("  python screen_stocks.py --pe-min 20 --pe-max 50 --change-min 3")
        sys.exit(1)
    
    # 获取股票数据
    print(f"📊 正在获取{args.market}市场股票数据...")
    stocks = get_all_stocks(args.market)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    
    # 筛选
    print(f"🔍 正在筛选...")
    filtered = filter_stocks(stocks, conditions)
    
    # 输出结果
    print(format_results(filtered, args.sort, args.top))

if __name__ == '__main__':
    main()
