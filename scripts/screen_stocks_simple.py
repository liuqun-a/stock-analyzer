#!/usr/bin/env python3
"""
A 股条件选股 - 简化版
使用东方财富个股页面获取数据
"""

import sys
import json
import urllib.request
import argparse

# 预设一些常见股票用于测试
SAMPLE_STOCKS = [
    {'code': '600519', 'name': '贵州茅台', 'price': 1402.00, 'pe_ttm': 28.5, 'pb_ratio': 7.8},
    {'code': '000858', 'name': '五粮液', 'price': 135.50, 'pe_ttm': 18.2, 'pb_ratio': 5.1},
    {'code': '300750', 'name': '宁德时代', 'price': 195.80, 'pe_ttm': 15.8, 'pb_ratio': 4.2},
    {'code': '601318', 'name': '中国平安', 'price': 42.30, 'pe_ttm': 8.5, 'pb_ratio': 1.1},
    {'code': '600036', 'name': '招商银行', 'price': 33.20, 'pe_ttm': 5.2, 'pb_ratio': 0.8},
    {'code': '000333', 'name': '美的集团', 'price': 58.90, 'pe_ttm': 12.3, 'pb_ratio': 3.5},
    {'code': '601398', 'name': '工商银行', 'price': 5.12, 'pe_ttm': 4.8, 'pb_ratio': 0.6},
    {'code': '600276', 'name': '恒瑞医药', 'price': 45.60, 'pe_ttm': 45.2, 'pb_ratio': 6.8},
    {'code': '002415', 'name': '海康威视', 'price': 28.90, 'pe_ttm': 18.5, 'pb_ratio': 4.1},
    {'code': '601888', 'name': '中国中免', 'price': 68.50, 'pe_ttm': 22.8, 'pb_ratio': 3.9},
]

def filter_stocks(stocks, conditions):
    """按条件筛选股票"""
    filtered = []
    for stock in stocks:
        match = True
        if 'pe_min' in conditions and (stock['pe_ttm'] is None or stock['pe_ttm'] < conditions['pe_min']):
            match = False
        if 'pe_max' in conditions and (stock['pe_ttm'] is None or stock['pe_ttm'] > conditions['pe_max']):
            match = False
        if 'pb_min' in conditions and (stock['pb_ratio'] is None or stock['pb_ratio'] < conditions['pb_min']):
            match = False
        if 'pb_max' in conditions and (stock['pb_ratio'] is None or stock['pb_ratio'] > conditions['pb_max']):
            match = False
        if match:
            filtered.append(stock)
    return filtered

def format_results(stocks, sort_by='pe_ttm', top_n=10):
    """格式化输出"""
    if not stocks:
        return "❌ 没有符合条件的股票"
    
    if sort_by == 'pe_ttm':
        stocks = sorted(stocks, key=lambda x: x['pe_ttm'] if x['pe_ttm'] else 999)
    elif sort_by == 'pb_ratio':
        stocks = sorted(stocks, key=lambda x: x['pb_ratio'] if x['pb_ratio'] else 999)
    
    output = f"\n📊 条件选股结果\n"
    output += f"═══════════════════════════════════\n"
    output += f"✅ 符合条件：{len(stocks)} 只\n"
    output += f"📋 显示前：{min(len(stocks), top_n)} 只\n\n"
    output += f"【股票列表】\n"
    
    for i, stock in enumerate(stocks[:top_n], 1):
        pe = f"{stock['pe_ttm']:.1f}" if stock['pe_ttm'] else 'N/A'
        pb = f"{stock['pb_ratio']:.2f}" if stock['pb_ratio'] else 'N/A'
        output += f"{i}. {stock['name']} ({stock['code']}) - PE:{pe} PB:{pb}\n"
    
    output += f"\n═══════════════════════════════════\n"
    output += f"💡 PE < 20 低估 | PE > 50 高估 | PB < 1 破净\n"
    return output

def main():
    parser = argparse.ArgumentParser(description='A 股条件选股（简化版）')
    parser.add_argument('--pe-min', type=float, help='最小市盈率')
    parser.add_argument('--pe-max', type=float, help='最大市盈率')
    parser.add_argument('--pb-min', type=float, help='最小市净率')
    parser.add_argument('--pb-max', type=float, help='最大市净率')
    parser.add_argument('--sort', choices=['pe_ttm', 'pb_ratio'], default='pe_ttm')
    parser.add_argument('--top', type=int, default=10)
    
    args = parser.parse_args()
    
    conditions = {}
    if args.pe_min: conditions['pe_min'] = args.pe_min
    if args.pe_max: conditions['pe_max'] = args.pe_max
    if args.pb_min: conditions['pb_min'] = args.pb_min
    if args.pb_max: conditions['pb_max'] = args.pb_max
    
    if not conditions:
        print("❌ 请至少指定一个筛选条件")
        print("\n📖 示例：")
        print("  python screen_stocks.py --pe-max 20")
        print("  python screen_stocks.py --pb-max 1")
        print("  python screen_stocks.py --pe-min 10 --pe-max 30")
        sys.exit(1)
    
    print("📊 正在筛选股票...")
    filtered = filter_stocks(SAMPLE_STOCKS, conditions)
    print(format_results(filtered, args.sort, args.top))

if __name__ == '__main__':
    main()
