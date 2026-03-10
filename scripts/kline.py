#!/usr/bin/env python3
"""
A 股 K 线图生成 - 日线/周线/月线
数据源：东方财富 API
输出：PNG 图片 + 文字摘要
"""

import sys
import json
import urllib.request
import argparse
from datetime import datetime, timedelta

def get_kline(symbol, period='day', count=60):
    """
    获取 K 线数据
    
    Args:
        symbol: 股票代码（6 位数字）
        period: 周期 day/week/month
        count: 获取多少根 K 线（默认 60 天）
    
    Returns:
        dict: K 线数据列表
    """
    # 判断市场
    if symbol.startswith('6'):
        market = '1'
    elif symbol.startswith('0') or symbol.startswith('3'):
        market = '0'
    elif symbol.startswith('4') or symbol.startswith('8'):
        market = '0'
    else:
        return {'error': '无法识别市场'}
    
    # 周期映射
    period_map = {
        'day': '101',      # 日线
        'week': '102',     # 周线
        'month': '103',    # 月线
    }
    ktype = period_map.get(period, '101')
    
    # 东方财富 K 线 API
    # fields1=f1,f2,f3,f4,f5,f6 (前复权等)
    # fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61 (日期，开盘，收盘，最高，最低，成交量，成交额，振幅，涨跌幅，涨跌额，换手率)
    url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt={ktype}&fqt=1&beg=0&end=20500101&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'http://quote.eastmoney.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)
            
        if data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines'][-count:]  # 取最近 count 条
            parsed = []
            for k in klines:
                parts = k.split(',')
                parsed.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]),
                    'amount': float(parts[6]),
                    'amplitude': float(parts[7]),
                    'change_pct': float(parts[8]),
                    'change': float(parts[9]),
                    'turnover': float(parts[10]) if len(parts) > 10 else 0,
                })
            return {'symbol': symbol, 'klines': parsed}
        return {'error': '数据获取失败'}
    except Exception as e:
        return {'error': str(e)}

def calculate_ma(klines, n=5):
    """计算 N 日均线"""
    if len(klines) < n:
        return []
    ma = []
    for i in range(len(klines)):
        if i < n - 1:
            ma.append(None)
        else:
            avg = sum(k['close'] for k in klines[i-n+1:i+1]) / n
            ma.append(round(avg, 2))
    return ma

def format_kline_summary(data):
    """格式化输出 K 线摘要"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    klines = data['klines']
    if not klines:
        return "❌ 无数据"
    
    latest = klines[-1]
    first = klines[0]
    
    # 计算区间统计
    period_high = max(k['high'] for k in klines)
    period_low = min(k['low'] for k in klines)
    period_change = (latest['close'] - first['open']) / first['open'] * 100
    
    # 计算均线
    ma5 = calculate_ma(klines, 5)
    ma10 = calculate_ma(klines, 10)
    ma20 = calculate_ma(klines, 20)
    
    summary = f"""
📈 {data['symbol']} K 线摘要
═══════════════════════════════════
📅 数据范围：{first['date']} ~ {latest['date']}
📊 K 线数量：{len(klines)} 根

【最新数据】({latest['date']})
💰 收盘价：¥{latest['close']:.2f}
📊 涨跌幅：{latest['change_pct']:+.2f}%
📈 成交量：{latest['volume']/10000:.1f}万手
💵 成交额：{latest['amount']/100000000:.2f}亿元

【区间统计】
🔝 最高价：¥{period_high:.2f}
🔻 最低价：¥{period_low:.2f}
📊 区间涨跌：{period_change:+.2f}%

【均线】
📈 MA5:  {ma5[-1] if ma5[-1] else 'N/A'}
📈 MA10: {ma10[-1] if ma10[-1] else 'N/A'}
📈 MA20: {ma20[-1] if ma20[-1] else 'N/A'}

═══════════════════════════════════
💡 提示：数据仅供参考，投资需谨慎
"""
    return summary

def main():
    parser = argparse.ArgumentParser(description='A 股 K 线图生成')
    parser.add_argument('symbol', help='股票代码（6 位数字）')
    parser.add_argument('-p', '--period', choices=['day', 'week', 'month'], default='day', help='周期（day/week/month）')
    parser.add_argument('-n', '--count', type=int, default=60, help='K 线数量（默认 60）')
    parser.add_argument('--no-plot', action='store_true', help='不生成图表，只输出摘要')
    
    args = parser.parse_args()
    
    # 获取 K 线数据
    print(f"📊 正在获取 {args.symbol} 的{args.period}线数据...")
    data = get_kline(args.symbol, args.period, args.count)
    
    # 输出摘要
    print(format_kline_summary(data))
    
    # 生成图表（如果有 matplotlib）
    if not args.no_plot and 'klines' in data:
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            
            klines = data['klines']
            dates = [k['date'][5:] for k in klines]  # 去掉年份，只显示 MM-DD
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            
            # 计算均线
            ma5 = calculate_ma(klines, 5)
            ma10 = calculate_ma(klines, 10)
            ma20 = calculate_ma(klines, 20)
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(14, 7))
            
            # 绘制 K 线（用折线近似）
            ax.plot(dates, closes, 'b-', linewidth=1.5, label='Close')
            ax.fill_between(range(len(dates)), highs, lows, alpha=0.3, color='gray', label='High-Low Range')
            
            # 绘制均线
            if ma5[-1]:
                ax.plot(dates, ma5, 'r-', linewidth=1, label='MA5')
            if ma10[-1]:
                ax.plot(dates, ma10, 'g-', linewidth=1, label='MA10')
            if ma20[-1]:
                ax.plot(dates, ma20, 'm-', linewidth=1, label='MA20')
            
            # 设置图表
            ax.set_title(f"{data['symbol']} K 线图 ({args.period})", fontsize=14, fontweight='bold')
            ax.set_xlabel('Date', fontsize=10)
            ax.set_ylabel('Price (¥)', fontsize=10)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # 旋转 x 轴标签
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存图片
            output_file = f"/tmp/{args.symbol}_{args.period}_kline.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"\n✅ K 线图已保存至：{output_file}")
            
        except ImportError:
            print("\n⚠️  未安装 matplotlib，跳过图表生成")
            print("   安装命令：pip install matplotlib")
        except Exception as e:
            print(f"\n⚠️  图表生成失败：{e}")

if __name__ == '__main__':
    main()
