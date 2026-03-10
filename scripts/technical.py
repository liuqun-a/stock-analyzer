#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标分析模块
参考：Daily Stock Analysis 项目
功能：计算 MA/MACD/RSI 等技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    # 均线
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    
    # MACD
    macd_dif: float = 0.0
    macd_dea: float = 0.0
    macd_hist: float = 0.0
    
    # RSI
    rsi6: float = 0.0
    rsi12: float = 0.0
    rsi24: float = 0.0
    
    # 趋势判断
    trend: str = "unknown"  # bullish/bearies/unknown
    ma_arrangement: str = "unknown"  # 多头/空头/混乱
    
    # 买卖信号
    signal: str = "hold"  # buy/sell/hold
    signal_strength: int = 0  # 信号强度 1-5


class TechnicalAnalyzer:
    """技术指标分析器"""
    
    def __init__(self):
        pass
    
    def calculate_ma(self, df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
        """计算移动平均线"""
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算 MACD 指标
        
        MACD 由三部分组成：
        - DIF (快线): EMA12 - EMA26
        - DEA (慢线): DIF 的 9 日 EMA
        - MACD 柱：(DIF - DEA) * 2
        """
        # 计算 EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        # DIF = EMA12 - EMA26
        df['DIF'] = ema_fast - ema_slow
        
        # DEA = DIF 的 9 日 EMA
        df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
        
        # MACD 柱 = (DIF - DEA) * 2
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """
        计算 RSI (相对强弱指标)
        
        RSI = 100 - (100 / (1 + RS))
        RS = N 日内上涨幅度平均值 / N 日内下跌幅度平均值
        
        RSI 解读：
        - RSI > 70: 超买区
        - RSI < 30: 超卖区
        - RSI 50: 强弱分界线
        """
        for period in periods:
            # 计算价格变化
            delta = df['close'].diff()
            
            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均涨幅和跌幅
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 计算 RS 和 RSI
            rs = avg_gain / avg_loss
            df[f'RSI{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def analyze_trend(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        分析趋势
        
        返回：
        - trend: bullish (多头) / bearish (空头) / unknown
        - arrangement: 多头排列 / 空头排列 / 混乱
        """
        if len(df) < 60:
            return "unknown", "数据不足"
        
        latest = df.iloc[-1]
        
        # 检查均线排列
        ma5 = latest.get('MA5', 0)
        ma10 = latest.get('MA10', 0)
        ma20 = latest.get('MA20', 0)
        ma60 = latest.get('MA60', 0)
        
        # 多头排列：MA5 > MA10 > MA20 > MA60
        if ma5 > ma10 > ma20 > ma60:
            arrangement = "多头排列"
            trend = "bullish"
        
        # 空头排列：MA5 < MA10 < MA20 < MA60
        elif ma5 < ma10 < ma20 < ma60:
            arrangement = "空头排列"
            trend = "bearish"
        
        else:
            arrangement = "混乱"
            trend = "unknown"
        
        return trend, arrangement
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[str, int]:
        """
        生成买卖信号
        
        基于：
        1. 均线排列（趋势）
        2. MACD 金叉/死叉
        3. RSI 超买/超卖
        
        返回：
        - signal: buy/sell/hold
        - strength: 1-5 (5 最强)
        """
        if len(df) < 60:
            return "hold", 0
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        strength = 0
        signal = "hold"
        
        # 1. 均线排列分析
        ma5 = latest.get('MA5', 0)
        ma10 = latest.get('MA10', 0)
        ma20 = latest.get('MA20', 0)
        
        if ma5 > ma10 > ma20:
            strength += 2  # 多头排列 +2
            signal = "buy"
        elif ma5 < ma10 < ma20:
            strength += 2  # 空头排列 +2
            signal = "sell"
        
        # 2. MACD 金叉/死叉
        dif = latest.get('DIF', 0)
        dea = latest.get('DEA', 0)
        prev_dif = prev.get('DIF', 0)
        prev_dea = prev.get('DEA', 0)
        
        # 金叉：DIF 从下向上穿越 DEA
        if prev_dif <= prev_dea and dif > dea:
            strength += 2
            if signal != "sell":
                signal = "buy"
        
        # 死叉：DIF 从上向下穿越 DEA
        elif prev_dif >= prev_dea and dif < dea:
            strength += 2
            if signal != "buy":
                signal = "sell"
        
        # 3. RSI 超买/超卖
        rsi6 = latest.get('RSI6', 50)
        
        if rsi6 < 30:  # 超卖
            strength += 1
            if signal != "sell":
                signal = "buy"
        elif rsi6 > 70:  # 超买
            strength += 1
            if signal != "buy":
                signal = "sell"
        
        # 限制强度在 1-5 范围
        strength = max(1, min(5, strength))
        
        return signal, strength
    
    def analyze(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        完整技术分析流程
        
        Args:
            df: DataFrame，包含 close 列（收盘价）
            
        Returns:
            TechnicalIndicators 对象
        """
        # 计算所有指标
        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        
        # 获取最新数据
        latest = df.iloc[-1] if len(df) > 0 else None
        
        if latest is None:
            return TechnicalIndicators()
        
        # 提取指标值
        indicators = TechnicalIndicators(
            ma5=latest.get('MA5', 0),
            ma10=latest.get('MA10', 0),
            ma20=latest.get('MA20', 0),
            ma60=latest.get('MA60', 0),
            macd_dif=latest.get('DIF', 0),
            macd_dea=latest.get('DEA', 0),
            macd_hist=latest.get('MACD', 0),
            rsi6=latest.get('RSI6', 50),
            rsi12=latest.get('RSI12', 50),
            rsi24=latest.get('RSI24', 50),
        )
        
        # 趋势分析
        indicators.trend, indicators.ma_arrangement = self.analyze_trend(df)
        
        # 买卖信号
        indicators.signal, indicators.signal_strength = self.generate_signal(df)
        
        return indicators
    
    def format_report(self, code: str, name: str, indicators: TechnicalIndicators, current_price: float) -> str:
        """
        格式化技术指标报告
        
        Args:
            code: 股票代码
            name: 股票名称
            indicators: 技术指标对象
            current_price: 当前价格
            
        Returns:
            格式化的报告文本
        """
        # 信号 emoji
        signal_emoji = {
            'buy': '🟢',
            'sell': '🔴',
            'hold': '🟡'
        }
        
        # 趋势 emoji
        trend_emoji = {
            'bullish': '📈',
            'bearish': '📉',
            'unknown': '➖'
        }
        
        report = f"""📊 技术指标分析

🏷️ {name} ({code})
💰 当前价：¥{current_price:.2f}

━━━━━━━━━━━━━━━━━━━━

📈 均线系统
  MA5:  {indicators.ma5:.2f}
  MA10: {indicators.ma10:.2f}
  MA20: {indicators.ma20:.2f}
  MA60: {indicators.ma60:.2f}
  排列：{indicators.ma_arrangement}

━━━━━━━━━━━━━━━━━━━━

📉 MACD
  DIF: {indicators.macd_dif:.3f}
  DEA: {indicators.macd_dea:.3f}
  柱： {indicators.macd_hist:.3f}

━━━━━━━━━━━━━━━━━━━━

💪 RSI
  RSI6:  {indicators.rsi6:.1f}
  RSI12: {indicators.rsi12:.1f}
  RSI24: {indicators.rsi24:.1f}

━━━━━━━━━━━━━━━━━━━━

{signal_emoji.get(indicators.signal, '🟡')} 信号：{indicators.signal.upper()}
  强度：{'⭐' * indicators.signal_strength}
  趋势：{trend_emoji.get(indicators.trend, '➖')} {indicators.trend}

━━━━━━━━━━━━━━━━━━━━
"""
        return report
