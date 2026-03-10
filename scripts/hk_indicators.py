#!/usr/bin/env python3
"""
港股技术指标分析 - 支持腾讯/阿里/美团等
数据源：预设数据（因为免费 API 不稳定）
"""

import sys
import json
import urllib.request
import argparse

# 港股股票代码映射
HK_STOCKS = {
    '00700': {'name': '腾讯控股', 'market': 'HK'},
    '09988': {'name': '阿里巴巴-SW', 'market': 'HK'},
    '03690': {'name': '美团-W', 'market': 'HK'},
    '01810': {'name': '小米集团-W', 'market': 'HK'},
    '09618': {'name': '京东健康', 'market': 'HK'},
}

def get_hk_kline(symbol):
    """
    获取港股 K 线数据
    目前用预设数据，后续可以扩展真实 API
    """
    if symbol not in HK_STOCKS:
        return {'error': f'不支持的港股代码：{symbol}'}
    
    stock = HK_STOCKS[symbol]
    
    # 预设数据（实际应该从 API 获取）
    # 这里用随机生成的演示数据
    import random
    from datetime import datetime, timedelta
    
    base_price = {
        '00700': 500,  # 腾讯
        '09988': 80,   # 阿里
        '03690': 120,  # 美团
        '01810': 15,   # 小米
    }.get(symbol, 100)
    
    klines = []
    price = base_price
    today = datetime.now()
    
    for i in range(60):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        change = random.uniform(-0.03, 0.03)
        open_p = price
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * 1.02
        low_p = min(open_p, close_p) * 0.98
        
        klines.append({
            'date': date,
            'open': open_p,
            'close': close_p,
            'high': high_p,
            'low': low_p,
        })
        price = close_p
    
    klines.reverse()
    return {'symbol': symbol, 'name': stock['name'], 'klines': klines}

def calculate_ma(prices, n):
    """计算 N 日均线"""
    if len(prices) < n:
        return [None] * len(prices)
    ma = []
    for i in range(len(prices)):
        if i < n - 1:
            ma.append(None)
        else:
            avg = sum(prices[i-n+1:i+1]) / n
            ma.append(round(avg, 2))
    return ma

def format_indicators(data):
    """格式化输出技术指标"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    symbol = data['symbol']
    name = data['name']
    klines = data['klines']
    latest = klines[-1]
    closes = [k['close'] for k in klines]
    
    # 计算均线
    ma5 = calculate_ma(closes, 5)[-1]
    ma10 = calculate_ma(closes, 10)[-1]
    ma20 = calculate_ma(closes, 20)[-1]
    
    # 趋势判断
    trend = "📈 上涨" if closes[-1] > closes[-5] else "📉 下跌"
    
    output = f"""
📊 {name} ({symbol}.HK) 技术指标分析
═══════════════════════════════════
📅 数据日期：{latest['date']}
💰 收盘价：HK$ {latest['close']:.2f}
📊 趋势：{trend}

【均线系统】
📈 MA5:  HK$ {ma5:.2f}
📈 MA10: HK$ {ma10:.2f}
📈 MA20: HK$ {ma20:.2f}

【支撑/阻力】
📊 支撑位：HK$ {min(k['low'] for k in klines[-20:]):.2f}
📊 阻力位：HK$ {max(k['high'] for k in klines[-20:]):.2f}

═══════════════════════════════════
⚠️  注：目前使用演示数据
    真实数据需要配置付费 API 或访问港交所官网
"""
    return output

def main():
    parser = argparse.ArgumentParser(description='港股技术指标分析')
    parser.add_argument('symbol', help='港股代码（如 00700）')
    
    args = parser.parse_args()
    
    # 去掉可能的.HK 后缀
    symbol = args.symbol.replace('.HK', '').replace('HK', '')
    
    print(f"📊 正在获取 {symbol} 的 K 线数据...")
    data = get_hk_kline(symbol)
    print(format_indicators(data))

if __name__ == '__main__':
    main()
