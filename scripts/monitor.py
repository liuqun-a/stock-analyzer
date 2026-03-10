#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票实时监控脚本
功能：
- 实时监控股票池价格
- 检测涨跌幅、成交量异常
- 触发预警自动推送飞书
- 支持 A 股 + 港股
"""

import requests
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import subprocess

# 配置路径
BASE_DIR = Path(__file__).parent.parent  # 返回到 stock-analyzer 根目录
CONFIG_DIR = BASE_DIR / "config"
CACHE_DIR = BASE_DIR / "cache"

# 确保缓存目录存在
CACHE_DIR.mkdir(exist_ok=True)


class Config:
    """配置管理"""
    
    def __init__(self):
        self.api_keys = self._load_yaml(CONFIG_DIR / "api_keys.yaml")
        self.alerts = self._load_yaml(CONFIG_DIR / "alerts.yaml")
        self.stocks = self._load_yaml(CONFIG_DIR / "stocks.yaml")
        
    def _load_yaml(self, path: Path) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)


class RateLimiter:
    """API 限流器"""
    
    def __init__(self, daily_limit: int = 200, per_minute_limit: int = 300):
        self.daily_limit = daily_limit
        self.per_minute_limit = per_minute_limit
        self.daily_count = 0
        self.minute_count = 0
        self.last_minute_reset = time.time()
        self.reset_daily_at = None  # 每日重置时间点
        
    def _check_daily_reset(self):
        """检查是否需要重置每日计数"""
        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        
        if self.reset_daily_at != today_str:
            self.daily_count = 0
            self.reset_daily_at = today_str
            print(f"[限流] 新的一天，每日计数已重置")
            
    def _check_minute_reset(self):
        """检查是否需要重置分钟计数"""
        now = time.time()
        if now - self.last_minute_reset >= 60:
            self.minute_count = 0
            self.last_minute_reset = now
            
    def acquire(self) -> bool:
        """
        获取请求许可
        返回 True 表示可以请求，False 表示需要等待
        """
        self._check_daily_reset()
        self._check_minute_reset()
        
        # 检查每日限制
        if self.daily_count >= self.daily_limit:
            print(f"[限流] 已达到每日限制 ({self.daily_limit}次)，请明日再用")
            return False
            
        # 检查每分钟限制
        if self.minute_count >= self.per_minute_limit:
            wait_time = 60 - (time.time() - self.last_minute_reset)
            if wait_time > 0:
                print(f"[限流] 已达到每分钟限制 ({self.per_minute_limit}次)，等待 {wait_time:.1f}秒")
                time.sleep(wait_time)
                self._check_minute_reset()
                
        # 增加计数
        self.daily_count += 1
        self.minute_count += 1
        
        return True
        
    def get_status(self) -> dict:
        """获取限流状态"""
        self._check_daily_reset()
        self._check_minute_reset()
        
        return {
            'daily_used': self.daily_count,
            'daily_remaining': self.daily_limit - self.daily_count,
            'minute_used': self.minute_count,
            'minute_remaining': self.per_minute_limit - self.minute_count
        }


class DataSourceManager:
    """数据源管理（主→备→兜底）"""
    
    def __init__(self, config: Config):
        self.config = config
        self.zhitu_token = config.api_keys.get('zhitu', {}).get('token', '')
        self.zhitu_base = config.api_keys.get('zhitu', {}).get('base_url', 'https://api.zhituapi.com')
        
        # 智兔数服限流器（免费额度：200 次/日，300 次/分钟）
        self.rate_limiter = RateLimiter(daily_limit=200, per_minute_limit=300)
        
    def get_realtime_quote(self, code: str, market: str = 'A') -> Optional[dict]:
        """
        获取实时行情
        优先使用智兔数服（带限流），失败则切换到东方财富
        ETF/基金优先使用东方财富（智兔支持不佳）
        """
        # ETF/基金优先使用东方财富（智兔数服支持不佳）
        is_etf = (code.startswith('51') or code.startswith('56') or 
                  code.startswith('15') or code.startswith('16'))
        
        if is_etf:
            try:
                data = self._get_eastmoney_quote(code, market)
                if data:
                    return data
            except Exception as e:
                print(f"[东方财富] 获取失败：{e}")
            # ETF 不使用智兔数服，直接返回
            return None
            
        # 股票：检查智兔数服限流
        if not self.rate_limiter.acquire():
            print(f"[限流] 智兔数服已达限制，切换到备用数据源")
            try:
                data = self._get_eastmoney_quote(code, market)
                if data:
                    return data
            except Exception as e:
                print(f"[东方财富] 获取失败：{e}")
            return None
            
        # 尝试智兔数服
        try:
            data = self._get_zhitu_quote(code, market)
            if data:
                return data
        except Exception as e:
            print(f"[智兔数服] 获取失败：{e}")
            
        # 切换到东方财富
        try:
            data = self._get_eastmoney_quote(code, market)
            if data:
                return data
        except Exception as e:
            print(f"[东方财富] 获取失败：{e}")
            
        # 最后尝试 AkShare
        try:
            data = self._get_akshare_quote(code, market)
            if data:
                return data
        except Exception as e:
            print(f"[AkShare] 获取失败：{e}")
            
        return None
    
    def _get_zhitu_quote(self, code: str, market: str) -> Optional[dict]:
        """智兔数服实时行情"""
        # 智兔数服 API 格式：https://api.zhituapi.com/hs/real/time/{code}?token=xxx
        if market == 'A':
            url = f"{self.zhitu_base}/hs/real/time/{code}"
        else:  # HK - 港股 API
            url = f"{self.zhitu_base}/hk/real/time/{code}"
            
        params = {'token': self.zhitu_token}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # 智兔返回格式：直接是数组或对象
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    return {
                        'source': 'zhitu',
                        'price': float(item.get('dj', 0)),  # 当前价
                        'change_pct': float(item.get('zdf', 0)),  # 涨跌幅
                        'volume': int(item.get('cj', 0)),  # 成交量
                        'turnover': float(item.get('cje', 0)),  # 成交额
                        'high': float(item.get('zgcj', 0)),  # 最高
                        'low': float(item.get('zdcj', 0)),  # 最低
                        'open': float(item.get('rpc', 0)),  # 昨收
                        'prev_close': float(item.get('rpc', 0)),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
                elif isinstance(data, dict):
                    # 智兔数服字段映射：
                    # p=当前价，pc=涨跌幅，v=成交量 (手), cje=成交额，h=最高，l=最低，o=开盘，yc=昨收
                    return {
                        'source': 'zhitu',
                        'price': float(data.get('p', 0)),
                        'change_pct': float(data.get('pc', 0)),
                        'volume': int(data.get('v', 0)) * 100,  # 手→股
                        'turnover': float(data.get('cje', 0)),
                        'high': float(data.get('h', 0)),
                        'low': float(data.get('l', 0)),
                        'open': float(data.get('o', 0)),
                        'prev_close': float(data.get('yc', 0)),
                        'time': data.get('t', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    }
        except Exception as e:
            print(f"[智兔数服] 错误：{e}")
        return None
    
    def _get_eastmoney_quote(self, code: str, market: str) -> Optional[dict]:
        """东方财富实时行情（支持 A 股/ETF/基金/港股，包含当天最低价）"""
        if market == 'A':
            # 自动识别股票类型
            # 51/56 开头：沪市 ETF/基金
            # 15/16 开头：深市 ETF/基金
            # 6 开头：沪市股票
            # 0/3 开头：深市股票
            if code.startswith('51') or code.startswith('56'):
                symbol = f"1.{code}"  # 沪市 ETF/基金
            elif code.startswith('15') or code.startswith('16'):
                symbol = f"0.{code}"  # 深市 ETF/基金
            elif code.startswith('6'):
                symbol = f"1{code}"  # 沪市股票
            else:
                symbol = f"0{code}"  # 深市股票
                
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': symbol,
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f128'
            }
        else:  # HK
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': f"116.{code}",
                'fields': 'f43,f44,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f128'
            }
            
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {})
            if result:
                return {
                    'source': 'eastmoney',
                    'price': float(result.get('f43', 0)) / 100,
                    'change_pct': float(result.get('f14', 0)),
                    'volume': int(result.get('f47', 0)),
                    'turnover': float(result.get('f38', 0)),
                    'high': float(result.get('f44', 0)) / 100,
                    'low': float(result.get('f45', 0)) / 100,  # 当天最低价
                    'open': float(result.get('f46', 0)) / 100,
                    'prev_close': float(result.get('f60', 0)) / 100,
                    'daily_low': float(result.get('f45', 0)) / 100,  # 当天最低价（别名）
                    'time': datetime.now().strftime('%H:%M:%S')
                }
        return None
    
    def _get_akshare_quote(self, code: str, market: str) -> Optional[dict]:
        """AkShare 实时行情（兜底）"""
        try:
            import akshare as ak
            
            if market == 'A':
                # 使用 akshare 获取实时行情
                df = ak.stock_zh_a_spot_em()
                stock_data = df[df['代码'] == code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'source': 'akshare',
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'volume': int(row.get('成交量', 0)),
                        'turnover': float(row.get('成交额', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'open': float(row.get('今开', 0)),
                        'prev_close': float(row.get('昨收', 0)),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
            else:  # HK
                df = ak.stock_hk_spot_em()
                stock_data = df[df['代码'] == code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'source': 'akshare',
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'volume': int(row.get('成交量', 0)),
                        'turnover': float(row.get('成交额', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'open': float(row.get('今开', 0)),
                        'prev_close': float(row.get('昨收', 0)),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
        except Exception as e:
            print(f"[AkShare] 错误：{e}")
        return None


class AlertEngine:
    """预警引擎"""
    
    def __init__(self, config: Config):
        self.config = config
        self.alert_config = config.alerts
        self.last_alerts = {}  # 记录上次预警时间（去重）
        
    def check_alerts(self, stock: dict, quote: dict) -> List[dict]:
        """检查是否触发预警（支持实时价格 + 当天最低价）"""
        alerts = []
        code = stock['code']
        name = stock['name']
        
        # 检查是否有当天最低价预警配置
        custom_thresholds = self.alert_config.get('custom_thresholds', {})
        
        # 价格预警（实时价格）
        if self.alert_config.get('price_alert', {}).get('enabled'):
            alert = self._check_price_alert(code, name, quote)
            if alert:
                alerts.append(alert)
        
        # 当天最低价预警（仅针对配置了 alert_price 的股票）
        if code in custom_thresholds:
            config = custom_thresholds[code]
            if config.get('alert_type') == 'price_below' and config.get('check_daily_low', True):
                alert = self._check_daily_low_alert(code, name, quote, config)
                if alert:
                    alerts.append(alert)
                
        # 成交量预警
        if self.alert_config.get('volume_alert', {}).get('enabled'):
            alert = self._check_volume_alert(code, name, quote)
            if alert:
                alerts.append(alert)
                
        return alerts
    
    def _check_daily_low_alert(self, code: str, name: str, quote: dict, config: dict) -> Optional[dict]:
        """当天最低价预警检查"""
        alert_price = config.get('alert_price', 0)
        daily_low = quote.get('daily_low', 0)
        
        if alert_price > 0 and daily_low > 0 and daily_low <= alert_price:
            return {
                'type': 'daily_low_below',
                'level': 'high',
                'code': code,
                'name': name,
                'message': f'当天最低价¥{daily_low:.2f} 低于警戒价¥{alert_price:.2f}',
                'price': quote.get('price', daily_low),
                'daily_low': daily_low,
                'alert_price': alert_price,
                'time': datetime.now().strftime('%H:%M:%S')
            }
        return None
    
    def _check_price_alert(self, code: str, name: str, quote: dict) -> Optional[dict]:
        """价格预警检查（支持个股自定义阈值和警戒价）"""
        current_price = quote.get('price', 0)
        change_pct = quote.get('change_pct', 0)
        
        # 检查是否有自定义阈值
        custom_thresholds = self.alert_config.get('custom_thresholds', {})
        if code in custom_thresholds:
            config = custom_thresholds[code]
            
            # 检查是否是"价格低于警戒线"类型
            if config.get('alert_type') == 'price_below':
                alert_price = config.get('alert_price', 0)
                if alert_price > 0 and current_price <= alert_price:
                    return {
                        'type': 'price_below',
                        'level': 'high',
                        'code': code,
                        'name': name,
                        'message': f'价格¥{current_price:.2f} 低于警戒价¥{alert_price:.2f}',
                        'price': current_price,
                        'alert_price': alert_price,
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
                return None  # 未触发警戒价，不预警
            
            # 涨跌幅预警（原有逻辑）
            threshold = config.get('alert_pct', 3)
            base_price = config.get('base_price', current_price)
            if base_price > 0:
                change_from_base = ((current_price - base_price) / base_price) * 100
            else:
                change_from_base = change_pct
                
            if abs(change_from_base) >= threshold:
                alert_type = '大涨' if change_from_base > 0 else '大跌'
                level = 'high' if abs(change_from_base) >= 7 else 'medium'
                message = f"相对基准价¥{base_price:.2f} {alert_type} {change_from_base:+.2f}%"
                
                return {
                    'type': 'price',
                    'level': level,
                    'code': code,
                    'name': name,
                    'message': message,
                    'price': current_price,
                    'base_price': base_price,
                    'change_from_base': change_from_base,
                    'time': datetime.now().strftime('%H:%M:%S')
                }
        else:
            # 默认涨跌幅预警
            threshold = self.alert_config['price_alert']['threshold_pct']
            if abs(change_pct) >= threshold:
                alert_type = '大涨' if change_pct > 0 else '大跌'
                level = 'high' if abs(change_pct) >= 7 else 'medium'
                
                return {
                    'type': 'price',
                    'level': level,
                    'code': code,
                    'name': name,
                    'message': f"{alert_type} {change_pct:+.2f}%",
                    'price': current_price,
                    'time': datetime.now().strftime('%H:%M:%S')
                }
            
        return None
    
    def _check_volume_alert(self, code: str, name: str, quote: dict) -> Optional[dict]:
        """成交量预警检查（简化版，实际需要历史均量对比）"""
        # TODO: 需要计算 5 日/10 日均量
        # 这里先做简单实现
        return None
    
    def should_push(self, alert: dict) -> bool:
        """检查是否应该推送（去重 + 静默时段）"""
        code = alert['code']
        alert_key = f"{code}_{alert['type']}"
        now = datetime.now()
        
        # 检查静默时段
        quiet_hours = self.alert_config.get('notification', {}).get('quiet_hours', {})
        if quiet_hours:
            start = datetime.strptime(quiet_hours.get('start', '23:00'), '%H:%M').time()
            end = datetime.strptime(quiet_hours.get('end', '8:00'), '%H:%M').time()
            if now.time() >= start or now.time() <= end:
                # 静默时段，只推送高优先级
                if alert['level'] != 'high':
                    return False
                    
        # 检查去重
        last_time = self.last_alerts.get(alert_key)
        dedup_interval = self.alert_config.get('notification', {}).get('dedup_interval', 300)
        if last_time and (now.timestamp() - last_time) < dedup_interval:
            return False
            
        self.last_alerts[alert_key] = now.timestamp()
        return True


class FeishuNotifier:
    """飞书通知"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        
    def send_alert(self, alert: dict):
        """发送预警消息到飞书"""
        # 调用飞书推送脚本
        import subprocess
        
        alert_json = json.dumps(alert)
        cmd = [
            'uv', 'run', 'python3', '-c',
            f'from feishu_push import send_alert; send_alert({alert_json})'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"[飞书推送] ✅ 预警已发送")
                print(f"  股票：{alert['name']} ({alert['code']})")
                print(f"  类型：{alert.get('type', 'price')}")
                print(f"  详情：{alert['message']}")
                return True
            else:
                print(f"[飞书推送] ⚠️ 发送失败，输出到控制台")
                self._print_alert(alert)
                return False
        except Exception as e:
            print(f"[飞书推送] ⚠️ 异常：{e}")
            self._print_alert(alert)
            return False
    
    def _print_alert(self, alert: dict):
        """控制台输出预警（降级方案）"""
        color_map = {
            'high': '🔴',
            'medium': '🟠',
            'low': '🟡'
        }
        
        emoji = color_map.get(alert['level'], '🔵')
        
        # 根据预警类型构建不同消息
        alert_type = alert.get('type', 'price')
        
        if alert_type == 'daily_low_below':
            # 当天最低价预警
            message = f"""{emoji} 当天最低价预警

股票：{alert['name']} ({alert['code']})
💰 现价：¥{alert['price']:.2f}
📉 当天最低：¥{alert.get('daily_low', alert['price']):.2f}
⚠️ 警戒价：¥{alert.get('alert_price', 0):.2f}
详情：{alert['message']}
时间：{alert['time']}"""
        else:
            # 实时价格预警
            message = f"""{emoji} 价格预警

股票：{alert['name']} ({alert['code']})
💰 现价：¥{alert['price']:.2f}
详情：{alert['message']}
时间：{alert['time']}"""

        print(message)
        
    def send_daily_report(self, report: dict):
        """发送日报"""
        # 简化实现，直接输出
        message = f"""📊 交易日报

日期：{report.get('date')}
监控股票：{report.get('watch_count')} 只
触发预警：{report.get('alert_count')} 次

[查看详细报告]"""
        
        print(f"[飞书推送] {message}")
        return message


class SmartIntervalManager:
    """智能刷新间隔管理（根据 API 剩余额度动态调整）"""
    
    def __init__(self, config: dict, rate_limiter: RateLimiter):
        self.config = config
        self.rate_limiter = rate_limiter
        self.min_interval = config.get('min_interval', 5)
        self.max_interval = config.get('max_interval', 60)
        
    def get_interval(self) -> int:
        """
        根据剩余额度计算刷新间隔
        剩余额度少 → 延长间隔
        剩余额度多 → 缩短间隔
        """
        status = self.rate_limiter.get_status()
        daily_remaining = status['daily_remaining']
        
        # 交易时段估算（9:30-11:30, 13:00-15:00 = 4 小时 = 240 分钟）
        trading_minutes_remaining = self._get_trading_minutes_remaining()
        
        if trading_minutes_remaining <= 0:
            # 非交易时段，返回最大间隔
            return self.max_interval
            
        # 计算理想间隔：确保剩余额度够用到收盘
        if daily_remaining > 0:
            ideal_interval = (trading_minutes_remaining * 60) / daily_remaining
            # 限制在最小和最大间隔之间
            interval = max(self.min_interval, min(self.max_interval, int(ideal_interval)))
        else:
            interval = self.max_interval
            
        return interval
        
    def _get_trading_minutes_remaining(self) -> int:
        """获取今日剩余交易分钟数"""
        now = datetime.now()
        
        # 检查是否是交易日（周一至周五）
        if now.weekday() >= 5:  # 周末
            return 0
            
        # 上午时段
        morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
        morning_end = now.replace(hour=11, minute=30, second=0, microsecond=0)
        
        # 下午时段
        afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        total_minutes = 0
        
        # 计算上午剩余
        if now < morning_start:
            total_minutes += 120  # 上午完整 2 小时
        elif now < morning_end:
            total_minutes += int((morning_end - now).total_seconds() / 60)
            
        # 计算下午剩余
        if now < afternoon_start:
            total_minutes += 120  # 下午完整 2 小时
        elif now < afternoon_end:
            total_minutes += int((afternoon_end - now).total_seconds() / 60)
            
        return max(0, total_minutes)


class StockMonitor:
    """股票监控主类"""
    
    def __init__(self):
        self.config = Config()
        self.data_source = DataSourceManager(self.config)
        self.alert_engine = AlertEngine(self.config)
        self.notifier = FeishuNotifier()
        
        # 智能间隔管理
        rate_limit_config = self.config.alerts.get('rate_limit', {})
        if rate_limit_config.get('enabled', True):
            self.smart_interval = SmartIntervalManager(
                rate_limit_config,
                self.data_source.rate_limiter
            )
        else:
            self.smart_interval = None
        
    def run(self, interval: int = 5):
        """运行监控（interval: 秒）"""
        print(f"🦞 股票监控启动 - 刷新间隔：{interval}秒（智能调整：{'开启' if self.smart_interval else '关闭'}）")
        print(f"监控股票池：A 股{len(self.config.stocks.get('a_shares', []))}只，港股{len(self.config.stocks.get('hk_shares', []))}只")
        print(f"智兔数服限流：{self.data_source.rate_limiter.daily_limit}次/日，{self.data_source.rate_limiter.per_minute_limit}次/分钟")
        print("-" * 60)
        
        current_interval = interval
        
        while True:
            try:
                # 显示限流状态
                status = self.data_source.rate_limiter.get_status()
                print(f"[限流状态] 今日剩余：{status['daily_remaining']}次 | 分钟剩余：{status['minute_remaining']}次 | 下次刷新：{current_interval}秒")
                
                self._check_all_stocks()
                
                # 智能调整间隔
                if self.smart_interval:
                    current_interval = self.smart_interval.get_interval()
                    
                time.sleep(current_interval)
            except KeyboardInterrupt:
                print("\n监控停止")
                break
            except Exception as e:
                print(f"[错误] {e}")
                time.sleep(current_interval)
                
    def _check_all_stocks(self):
        """检查所有股票"""
        all_stocks = []
        
        # A 股
        for stock in self.config.stocks.get('a_shares', []):
            if stock.get('enabled', True):
                stock['market'] = 'A'
                all_stocks.append(stock)
                
        # 港股
        for stock in self.config.stocks.get('hk_shares', []):
            if stock.get('enabled', True):
                stock['market'] = 'HK'
                all_stocks.append(stock)
                
        for stock in all_stocks:
            quote = self.data_source.get_realtime_quote(stock['code'], stock['market'])
            if quote:
                alerts = self.alert_engine.check_alerts(stock, quote)
                for alert in alerts:
                    if self.alert_engine.should_push(alert):
                        self.notifier.send_alert(alert)
                        
    def check_once(self):
        """单次检查（用于测试）"""
        self._check_all_stocks()
        
    def check_single_stock(self, code: str):
        """单独监控某只股票"""
        # 查找股票信息
        stock_info = None
        
        # 在 custom_watch 中查找
        for stock in self.config.stocks.get('custom_watch', []):
            if stock.get('code') == code and stock.get('enabled', True):
                stock_info = stock
                stock_info['market'] = 'A'
                break
                
        # 在 a_shares 中查找
        if not stock_info:
            for stock in self.config.stocks.get('a_shares', []):
                if stock.get('code') == code and stock.get('enabled', True):
                    stock_info = stock
                    stock_info['market'] = 'A'
                    break
        
        if not stock_info:
            print(f"❌ 未找到股票 {code} 的配置")
            return
            
        print(f"📊 检查 {stock_info['name']} ({code})")
        quote = self.data_source.get_realtime_quote(code, stock_info['market'])
        
        if quote:
            alerts = self.alert_engine.check_alerts(stock_info, quote)
            for alert in alerts:
                if self.alert_engine.should_push(alert):
                    self.notifier.send_alert(alert)
                    
            if not alerts:
                print(f"✅ 无预警触发")
        else:
            print(f"❌ 无法获取行情数据")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='股票实时监控')
    parser.add_argument('--interval', type=int, default=5, help='刷新间隔（秒）')
    parser.add_argument('--once', action='store_true', help='只检查一次')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--stock', type=str, help='监控股票代码（单独监控某只股票）')
    
    args = parser.parse_args()
    
    monitor = StockMonitor()
    
    if args.test:
        print("测试模式 - 检查贵州茅台")
        quote = monitor.data_source.get_realtime_quote('600519', 'A')
        print(f"行情数据：{quote}")
    elif args.stock:
        print(f"单次检查模式 - 监控 {args.stock}")
        monitor.check_single_stock(args.stock)
    elif args.once:
        print("单次检查模式")
        monitor.check_once()
    else:
        monitor.run(interval=args.interval)


if __name__ == '__main__':
    main()
