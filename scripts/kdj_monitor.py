#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KDJ 超短线监控脚本
监控频率：1 分钟一次
触发条件：
- 买入：KDJ_J ≤ 20 + 金叉 + 回踩均价线不破
- 卖出：KDJ_J ≥ 80 + 死叉 + 跌破均价线
- 止损：亏损 ≥ 6%
"""

import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from feishu_push import send_alert


class KDJCalculator:
    """KDJ 指标计算器"""
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n: int = 9, m: int = 3) -> pd.DataFrame:
        """
        计算 KDJ 指标
        
        Args:
            df: DataFrame，包含 high、low、close 列
            n: RSV 计算周期（默认 9）
            m: K/D 平滑周期（默认 3）
            
        Returns:
            DataFrame，包含 K、D、J 列
        """
        # 计算 RSV
        lowest_n = df['low'].rolling(window=n).min()
        highest_n = df['high'].rolling(window=n).max()
        
        df['RSV'] = (df['close'] - lowest_n) / (highest_n - lowest_n) * 100
        
        # 计算 K 线（RSV 的 M 日移动平均）
        df['K'] = df['RSV'].rolling(window=m).mean()
        
        # 计算 D 线（K 的 M 日移动平均）
        df['D'] = df['K'].rolling(window=m).mean()
        
        # 计算 J 线（3K - 2D）
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        # 处理 NaN 值
        df.fillna(50, inplace=True)
        
        return df
    
    @staticmethod
    def is_golden_cross(kdj_current: dict, kdj_prev: dict) -> bool:
        """
        检测金叉
        金叉：J 线从下向上穿过 K 线和 D 线
        """
        # 当前 J > K 且 J > D
        current_cross = (kdj_current['J'] > kdj_current['K']) and \
                        (kdj_current['J'] > kdj_current['D'])
        
        # 之前 J < K 或 J < D（之前没金叉）
        prev_no_cross = (kdj_prev['J'] <= kdj_prev['K']) or \
                        (kdj_prev['J'] <= kdj_prev['D'])
        
        return current_cross and prev_no_cross
    
    @staticmethod
    def is_dead_cross(kdj_current: dict, kdj_prev: dict) -> bool:
        """
        检测死叉
        死叉：J 线从上向下穿过 K 线和 D 线
        """
        # 当前 J < K 且 J < D
        current_cross = (kdj_current['J'] < kdj_current['K']) and \
                        (kdj_current['J'] < kdj_current['D'])
        
        # 之前 J > K 或 J > D（之前没死叉）
        prev_no_cross = (kdj_prev['J'] >= kdj_prev['K']) or \
                        (kdj_prev['J'] >= kdj_prev['D'])
        
        return current_cross and prev_no_cross


class KDJMonitor:
    """KDJ 监控器"""
    
    def __init__(self, interval: int = 60):
        """
        初始化监控器
        
        Args:
            interval: 监控频率（秒），默认 60 秒（1 分钟）
        """
        self.interval = interval
        self.calculator = KDJCalculator()
        
        # 监控配置
        self.config = {
            'kdj_j_buy': 20,      # J 值买入阈值
            'kdj_j_sell': 80,     # J 值卖出阈值
            'stop_loss_pct': 6,   # 止损百分比
            'kdj_n': 9,           # KDJ 计算周期
            'kdj_m': 3,           # KDJ 平滑周期
        }
        
        # 监控股票池
        self.watchlist: List[Dict] = []
        
        # 持仓记录
        self.positions: Dict[str, Dict] = {}
        
        # 上一次 KDJ 值（用于检测金叉死叉）
        self.prev_kdj: Dict[str, Dict] = {}
        
        # 日志目录
        self.log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir.mkdir(exist_ok=True)
    
    def add_stock(self, code: str, name: str):
        """
        添加监控股票
        
        Args:
            code: 股票代码
            name: 股票名称
        """
        stock = {
            'code': code,
            'name': name,
            'enabled': True,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.watchlist.append(stock)
        print(f"✅ 已添加监控：{name} ({code})")
    
    def remove_stock(self, code: str):
        """移除监控股票"""
        self.watchlist = [s for s in self.watchlist if s['code'] != code]
        print(f"✅ 已移除监控：{code}")
    
    def get_minute_data(self, code: str, market: str = 'A') -> Optional[pd.DataFrame]:
        """
        获取 1 分钟 K 线数据
        
        Args:
            code: 股票代码
            market: 市场类型（A/HK）
            
        Returns:
            DataFrame，包含 timestamp、open、high、low、close、volume 列
        """
        try:
            # 东方财富 API（简化示例，实际需要使用正确的分钟线 API）
            # 这里使用模拟数据演示逻辑
            
            # TODO: 实际应该调用东方财富分钟线 API
            # 示例：http://push2.eastmoney.com/api/qt/stock/get
            
            # 生成模拟数据（实际使用时替换为真实 API）
            np.random.seed(hash(code) % 1000 + int(time.time()) // 60)
            
            # 生成最近 30 根 1 分钟 K 线
            minutes = 30
            base_price = 10 + np.random.random() * 100
            
            data = {
                'timestamp': pd.date_range(end=datetime.now(), periods=minutes, freq='1min'),
                'open': base_price + np.cumsum(np.random.randn(minutes)) * 0.1,
                'high': base_price + np.cumsum(np.random.randn(minutes)) * 0.1 + np.random.random(minutes),
                'low': base_price + np.cumsum(np.random.randn(minutes)) * 0.1 - np.random.random(minutes),
                'close': base_price + np.cumsum(np.random.randn(minutes)) * 0.1,
                'volume': np.random.randint(1000, 10000, minutes)
            }
            
            df = pd.DataFrame(data)
            
            # 确保 high >= close, high >= open, low <= close, low <= open
            df['high'] = df[['high', 'open', 'close']].max(axis=1)
            df['low'] = df[['low', 'open', 'close']].min(axis=1)
            
            return df
            
        except Exception as e:
            print(f"❌ 获取 K 线数据失败 {code}: {e}")
            return None
    
    def check_signals(self, code: str, name: str, df: pd.DataFrame):
        """
        检查交易信号
        
        Args:
            code: 股票代码
            name: 股票名称
            df: K 线数据
        """
        if df is None or len(df) < 10:
            return
        
        # 计算 KDJ
        df = self.calculator.calculate_kdj(df, self.config['kdj_n'], self.config['kdj_m'])
        
        # 获取最新数据
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
        
        kdj_current = {
            'K': current['K'],
            'D': current['D'],
            'J': current['J']
        }
        
        kdj_prev = {
            'K': prev['K'],
            'D': prev['D'],
            'J': prev['J']
        }
        
        # 估算均价线（简单用 VWAP 近似）
        avg_price = (current['open'] + current['high'] + current['low'] + current['close']) / 4
        
        # 检查买入信号
        buy_signal = self.check_buy_signal(kdj_current, kdj_prev, current, avg_price, code, name)
        
        # 检查卖出信号
        sell_signal = self.check_sell_signal(kdj_current, kdj_prev, current, avg_price, code, name)
        
        # 检查止损
        if code in self.positions:
            self.check_stop_loss(code, name, current['close'])
        
        # 保存当前 KDJ 用于下次比较
        self.prev_kdj[code] = kdj_current
    
    def check_buy_signal(self, kdj_current: dict, kdj_prev: dict, 
                         price: pd.Series, avg_price: float, 
                         code: str, name: str):
        """
        检查买入信号
        
        条件：
        1. KDJ_J ≤ 20
        2. 金叉
        3. 回踩均价线不破（最低价 >= 均价线）
        """
        # 条件 1: J ≤ 20
        condition_1 = kdj_current['J'] <= self.config['kdj_j_buy']
        
        # 条件 2: 金叉
        condition_2 = self.calculator.is_golden_cross(kdj_current, kdj_prev)
        
        # 条件 3: 回踩均价线不破
        condition_3 = price['low'] >= avg_price
        
        # 3 个条件同时满足
        if condition_1 and condition_2 and condition_3:
            message = f"""KDJ 买入信号

📊 KDJ 指标
  K: {kdj_current['K']:.2f}
  D: {kdj_current['D']:.2f}
  J: {kdj_current['J']:.2f}

💰 价格
  当前价：¥{price['close']:.2f}
  均价线：¥{avg_price:.2f}

✅ 触发条件
  ✅ J ≤ 20（超卖）
  ✅ KDJ 金叉
  ✅ 回踩均价线不破

⚠️ 建议止损价：¥{price['close'] * 0.94:.2f}（-6%）"""
            
            alert = {
                'code': code,
                'name': name,
                'price': price['close'],
                'message': message,
                'time': datetime.now().strftime('%H:%M:%S'),
                'level': 'high',
                'type': 'kdj_buy'
            }
            
            print(f"\n🟢 {name} ({code}) KDJ 买入信号")
            send_alert(alert)
            
            # 记录持仓
            self.positions[code] = {
                'buy_price': price['close'],
                'buy_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stop_loss': price['close'] * 0.94
            }
            
            return True
        
        return False
    
    def check_sell_signal(self, kdj_current: dict, kdj_prev: dict,
                          price: pd.Series, avg_price: float,
                          code: str, name: str):
        """
        检查卖出信号
        
        条件：
        1. KDJ_J ≥ 80
        2. 死叉
        3. 跌破均价线（现价 < 均价线）
        """
        # 条件 1: J ≥ 80
        condition_1 = kdj_current['J'] >= self.config['kdj_j_sell']
        
        # 条件 2: 死叉
        condition_2 = self.calculator.is_dead_cross(kdj_current, kdj_prev)
        
        # 条件 3: 跌破均价线
        condition_3 = price['close'] < avg_price
        
        # 3 个条件同时满足
        if condition_1 and condition_2 and condition_3:
            message = f"""KDJ 卖出信号

📊 KDJ 指标
  K: {kdj_current['K']:.2f}
  D: {kdj_current['D']:.2f}
  J: {kdj_current['J']:.2f}

💰 价格
  当前价：¥{price['close']:.2f}
  均价线：¥{avg_price:.2f}

✅ 触发条件
  ✅ J ≥ 80（超买）
  ✅ KDJ 死叉
  ✅ 跌破均价线

💡 建议：及时止盈"""
            
            alert = {
                'code': code,
                'name': name,
                'price': price['close'],
                'message': message,
                'time': datetime.now().strftime('%H:%M:%S'),
                'level': 'high',
                'type': 'kdj_sell'
            }
            
            print(f"\n🔴 {name} ({code}) KDJ 卖出信号")
            send_alert(alert)
            
            # 清除持仓
            if code in self.positions:
                del self.positions[code]
            
            return True
        
        return False
    
    def check_stop_loss(self, code: str, name: str, current_price: float):
        """检查止损"""
        if code not in self.positions:
            return
        
        position = self.positions[code]
        buy_price = position['buy_price']
        stop_loss = position['stop_loss']
        
        loss_pct = (buy_price - current_price) / buy_price * 100
        
        if loss_pct >= self.config['stop_loss_pct']:
            message = f"""止损预警

💰 价格
  买入价：¥{buy_price:.2f}
  当前价：¥{current_price:.2f}
  亏损：-{loss_pct:.2f}%

⚠️ 亏损已达 6%，坚决止损！"""
            
            alert = {
                'code': code,
                'name': name,
                'price': current_price,
                'message': message,
                'time': datetime.now().strftime('%H:%M:%S'),
                'level': 'high',
                'type': 'stop_loss'
            }
            
            print(f"\n🔴 {name} ({code}) 触发止损")
            send_alert(alert)
            
            # 清除持仓
            del self.positions[code]
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        log_file = self.log_dir / f"kdj_monitor_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        with open(log_file, 'a') as f:
            f.write(log_message)
    
    def run(self):
        """运行监控"""
        print("=" * 70)
        print("🦞 KDJ 超短线监控启动")
        print("=" * 70)
        print(f"监控频率：{self.interval}秒（1 分钟）")
        print(f"监控股票：{len(self.watchlist)} 只")
        print(f"买入阈值：J ≤ {self.config['kdj_j_buy']}")
        print(f"卖出阈值：J ≥ {self.config['kdj_j_sell']}")
        print(f"止损阈值：亏损 ≥ {self.config['stop_loss_pct']}%")
        print("=" * 70)
        print()
        
        self.log("KDJ 监控启动")
        
        try:
            while True:
                # 检查是否是交易时间
                now = datetime.now()
                is_trading_time = (
                    (now.hour == 9 and now.minute >= 30) or now.hour == 10 or
                    (now.hour == 11 and now.minute <= 30) or
                    (now.hour == 13 or now.hour == 14 or
                     (now.hour == 15 and now.minute <= 0))
                ) and now.weekday() < 5
                
                if is_trading_time:
                    for stock in self.watchlist:
                        if not stock['enabled']:
                            continue
                        
                        code = stock['code']
                        name = stock['name']
                        
                        # 获取 K 线数据
                        df = self.get_minute_data(code)
                        
                        if df is not None:
                            # 检查信号
                            self.check_signals(code, name, df)
                    
                    # 记录日志
                    self.log(f"检查完成，监控 {len(self.watchlist)} 只股票")
                
                # 等待下一次检查
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\n监控停止")
            self.log("监控停止")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='KDJ 超短线监控')
    parser.add_argument('--interval', type=int, default=60, help='监控频率（秒），默认 60 秒')
    parser.add_argument('--stock', type=str, help='监控股票代码，如 002416')
    parser.add_argument('--name', type=str, help='股票名称，如 爱施德')
    
    args = parser.parse_args()
    
    monitor = KDJMonitor(interval=args.interval)
    
    # 如果指定了股票，添加到监控
    if args.stock and args.name:
        monitor.add_stock(args.stock, args.name)
    
    # 运行监控
    monitor.run()


if __name__ == '__main__':
    main()
