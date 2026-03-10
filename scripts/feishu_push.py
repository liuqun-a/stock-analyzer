#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书消息推送工具
使用飞书 API 直连发送预警（不经过 OpenClaw CLI，不影响私聊配对）

敏感信息从 OpenClaw 配置文件读取 (~/.openclaw/openclaw.json)
"""

import requests
import json
from pathlib import Path
from typing import Optional


def load_feishu_config() -> dict:
    """从 OpenClaw 配置文件读取飞书信息"""
    config_file = Path.home() / ".openclaw" / "openclaw.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # 读取飞书配置
        feishu_config = config['channels']['feishu']['accounts']['feishubot']
        
        # 从配置读取 receive_id，如果没有则从环境变量读取
        receive_id = feishu_config.get('receiveId', '')
        if not receive_id:
            import os
            receive_id = os.getenv('FEISHU_RECEIVE_ID', '')
        
        return {
            'app_id': feishu_config['appId'],
            'app_secret': feishu_config['appSecret'],
            'receive_id': receive_id
        }
    except Exception as e:
        print(f"[配置加载] 读取飞书配置失败：{e}")
        # 降级返回空配置
        return {'app_id': '', 'app_secret': '', 'receive_id': ''}


def get_access_token() -> str:
    """获取飞书 access_token"""
    config = load_feishu_config()
    
    if not config['app_id'] or not config['app_secret']:
        print("[飞书 API] 配置未加载，无法获取 token")
        return ""
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        resp = requests.post(url, json={"app_id": config['app_id'], "app_secret": config['app_secret']}, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get('code') == 0:
            return result['tenant_access_token']
        else:
            print(f"[飞书 API] 获取 token 失败：{result}")
            return ""
    except Exception as e:
        print(f"[飞书 API] 请求失败：{e}")
        return ""


def send_feishu_message(title: str, content: str, level: str = "medium"):
    """
    发送飞书消息（使用飞书 API 直连）
    
    Args:
        title: 消息标题
        content: 消息内容
        level: 预警级别 (high/medium/low)
    """
    # 颜色映射
    color_map = {
        'high': '🔴',
        'medium': '🟠',
        'low': '🟡'
    }
    
    emoji = color_map.get(level, '🔵')
    
    # 构建消息
    message = f"""{emoji} {title}

{content}

---
⏰ 推送时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🦞 股票监控系统"""

    # 使用飞书 API 直接发送
    try:
        # 获取 access_token
        token = get_access_token()
        if not token:
            print(f"[飞书推送] ❌ 获取 token 失败，降级输出")
            print(message)
            return False
        
        # 发送消息
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 飞书 API 要求 content 是 JSON 字符串
        config = load_feishu_config()
        payload = {
            "receive_id": config['receive_id'],
            "msg_type": "text",
            "content": json.dumps({"text": message})
        }
        
        # 添加 receive_id_type 参数（飞书 API 要求）
        params = {"receive_id_type": "open_id"}
        
        resp = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        
        result = resp.json()
        if result.get('code') == 0:
            print(f"[飞书推送] ✅ 消息已发送（API 直连，不影响私聊）")
            return True
        else:
            print(f"[飞书推送] ⚠️ 发送失败：{result}")
            print(message)
            return True
            
    except Exception as e:
        print(f"[飞书推送] ❌ 异常：{e}")
        # 降级：直接输出
        print(message)
        return False


def send_alert(alert: dict) -> bool:
    """发送预警消息"""
    title = "股票预警通知"
    
    content = f"""📊 股票：{alert['name']} ({alert['code']})
💰 现价：¥{alert['price']:.2f}
📈 基准价：¥{alert.get('base_price', alert['price']):.2f}
📊 涨跌幅：{alert.get('change_from_base', 0):+.2f}%
⚠️ 详情：{alert['message']}
⏰ 时间：{alert['time']}"""

    return send_feishu_message(title, content, alert.get('level', 'medium'))


def send_daily_report(report: dict) -> bool:
    """发送日报"""
    title = "📊 交易日报"
    
    content = f"""📅 日期：{report.get('date', 'N/A')}
👁️ 监控股票：{report.get('watch_count', 0)} 只
⚠️ 触发预警：{report.get('alert_count', 0)} 次

🏆 今日最佳：{report.get('top_gainer', 'N/A')}
📉 今日最差：{report.get('top_loser', 'N/A')}

💡 投资有风险，决策需谨慎"""

    return send_feishu_message(title, content, 'low')


if __name__ == '__main__':
    # 测试
    test_alert = {
        'code': '561570',
        'name': '科创 50ETF',
        'price': 15.48,
        'base_price': 15.48,
        'change_from_base': 1.5,
        'message': '相对基准价¥15.48 大涨 +1.50%',
        'time': '09:45:00',
        'level': 'medium'
    }
    
    send_alert(test_alert)
