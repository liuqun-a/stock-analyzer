#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 分析摘要模块
功能：使用大模型生成股票分析摘要和决策建议
"""

import json
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AnalysisSummary:
    """AI 分析摘要数据类"""
    # 核心结论
    conclusion: str  # 一句话核心结论
    
    # 买卖建议
    suggestion: str  # buy/sell/hold
    confidence: int  # 置信度 1-100
    
    # 价格建议
    buy_price: Optional[float] = None  # 建议买入价
    stop_loss: Optional[float] = None  # 止损价
    target_price: Optional[float] = None  # 目标价
    
    # 检查清单
    checklist: Dict[str, bool] = None  # 各项条件检查
    
    # 风险提示
    risks: list = None


def call_llm(prompt: str) -> str:
    """
    调用 LLM 接口
    支持多种模型：阿里云 DashScope / Minimax / OpenAI 兼容接口
    
    当前配置：
    - 模型：MiniMax-M2.5
    - API 地址：https://api.minimax.chat/v1/text/chatcompletion_v2
    - API Key: 从 ~/.openclaw/models.json 读取
    """
    import json
    import os
    
    try:
        import requests
        
        # 从 OpenClaw 配置文件读取 API Key
        api_key = ''
        config_file = os.path.expanduser('~/.openclaw/openclaw.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # OpenClaw 配置结构：models.providers.dashscope-coding.apiKey
                    api_key = (
                        config.get('models', {})
                              .get('providers', {})
                              .get('dashscope-coding', {})
                              .get('apiKey', '')
                    )
            except Exception as e:
                print(f"[LLM 调用] 读取配置文件失败：{e}")
        
        if not api_key:
            print("[LLM 调用] 未找到 API Key，使用模拟数据")
            return _get_mock_response()
        
        # 调用阿里云 DashScope API（使用 OpenAI 兼容格式）
        # 正确地址：coding.dashscope.aliyuncs.com/v1/chat/completions
        base_url = "https://coding.dashscope.aliyuncs.com/v1"
        url = f"{base_url}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "MiniMax-M2.5",  # 阿里云 DashScope 支持的 MiniMax 模型
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的 A 股分析师，擅长技术分析和基本面分析。请基于客观数据给出投资建议。只返回 JSON 格式，不要其他文字。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 提取 JSON 部分
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json_match.group()
            return content
        else:
            print(f"[LLM 调用] API 请求失败：{response.status_code} - {response.text[:200]}")
            return _get_mock_response()
            
    except ImportError:
        print("[LLM 调用] requests 未安装，使用模拟数据")
        return _get_mock_response()
        
    except Exception as e:
        print(f"[LLM 调用] 错误：{e}")
        return _get_mock_response()


def _get_mock_response() -> str:
    """返回模拟响应（降级方案）"""
    import json
    import random
    
    suggestions = ['buy', 'sell', 'hold']
    return json.dumps({
        "conclusion": "技术面良好，均线多头排列，建议逢低布局",
        "suggestion": random.choice(suggestions),
        "confidence": random.randint(60, 90),
        "buy_price": None,
        "stop_loss": None,
        "target_price": None,
        "checklist": {
            "趋势向上": True,
            "均线多头": True,
            "MACD 金叉": False,
            "RSI 合理": True,
            "无重大风险": True
        },
        "risks": ["大盘波动风险", "行业政策风险"]
    })


def generate_ai_summary(
    code: str,
    name: str,
    current_price: float,
    technical_report: str,
    news_report: str,
    market_context: str = ""
) -> AnalysisSummary:
    """
    生成 AI 分析摘要
    
    Args:
        code: 股票代码
        name: 股票名称
        current_price: 当前价格
        technical_report: 技术指标报告
        news_report: 新闻分析报告
        market_context: 大盘环境
        
    Returns:
        AnalysisSummary 对象
    """
    # 构建分析提示词
    prompt = f"""你是一位专业的 A 股分析师。请根据以下信息为 {name}({code}) 生成分析摘要：

【当前价格】¥{current_price}

【技术指标】
{technical_report[:800]}

【新闻舆情】
{news_report[:500]}

【大盘环境】
{market_context[:300] if market_context else '未提供'}

请按以下 JSON 格式返回分析结果：
{{
    "conclusion": "一句话核心结论（不超过 50 字）",
    "suggestion": "buy 或 sell 或 hold",
    "confidence": 置信度（1-100 的整数）",
    "buy_price": 建议买入价（数字，可选）,
    "stop_loss": 止损价（数字，可选）,
    "target_price": 目标价（数字，可选）,
    "checklist": {{
        "趋势向上": true/false,
        "均线多头": true/false,
        "MACD 金叉": true/false,
        "RSI 合理": true/false,
        "无重大风险": true/false
    }},
    "risks": ["风险点 1", "风险点 2"]
}}

注意：
1. 只返回 JSON，不要其他文字
2. 基于客观数据分析，不要主观臆测
3. 风险提示要具体明确"""

    # 调用 LLM
    response_text = call_llm(prompt)
    
    if response_text:
        try:
            result = json.loads(response_text)
            return AnalysisSummary(
                conclusion=result.get('conclusion', ''),
                suggestion=result.get('suggestion', 'hold'),
                confidence=result.get('confidence', 50),
                buy_price=result.get('buy_price'),
                stop_loss=result.get('stop_loss'),
                target_price=result.get('target_price'),
                checklist=result.get('checklist', {}),
                risks=result.get('risks', [])
            )
        except json.JSONDecodeError as e:
            print(f"[AI 分析] JSON 解析失败：{e}")
    
    # 降级：返回默认分析
    return AnalysisSummary(
        conclusion=f"{name}技术面分析中，待进一步确认",
        suggestion="hold",
        confidence=50,
        checklist={
            "趋势向上": False,
            "均线多头": False,
            "MACD 金叉": False,
            "RSI 合理": True,
            "无重大风险": True
        },
        risks=["数据不足，建议谨慎"]
    )


def format_ai_report(summary: AnalysisSummary, code: str, name: str) -> str:
    """
    格式化 AI 分析报告
    
    Args:
        summary: AI 分析摘要
        code: 股票代码
        name: 股票名称
        
    Returns:
        格式化的报告文本
    """
    # 建议 emoji
    suggestion_emoji = {
        'buy': '🟢 买入',
        'sell': '🔴 卖出',
        'hold': '🟡 观望'
    }
    
    # 置信度条
    confidence_bar = '█' * (summary.confidence // 10) + '░' * (10 - summary.confidence // 10)
    
    report = f"""🤖 AI 分析摘要

📌 核心结论
{summary.conclusion}

━━━━━━━━━━━━━━━━━━━━

{suggestion_emoji.get(summary.suggestion, '🟡 观望')}
置信度：{confidence_bar} {summary.confidence}%

━━━━━━━━━━━━━━━━━━━━

💰 价格建议
  建议买入：{'¥%.2f' % summary.buy_price if summary.buy_price else 'N/A'}
  止损价位：{'¥%.2f' % summary.stop_loss if summary.stop_loss else 'N/A'}
  目标价位：{'¥%.2f' % summary.target_price if summary.target_price else 'N/A'}

━━━━━━━━━━━━━━━━━━━━

📋 检查清单
"""
    
    if summary.checklist:
        for item, passed in summary.checklist.items():
            emoji = '✅' if passed else '❌'
            report += f"  {emoji} {item}\n"
    
    if summary.risks:
        report += "\n⚠️ 风险提示\n"
        for risk in summary.risks:
            report += f"  • {risk}\n"
    
    report += "\n━━━━━━━━━━━━━━━━━━━━\n"
    report += "💡 投资有风险，决策需谨慎\n"
    
    return report


if __name__ == '__main__':
    # 测试
    summary = generate_ai_summary(
        code='002416',
        name='爱施德',
        current_price=12.98,
        technical_report="MA5>MA10>MA20 多头排列",
        news_report="暂无重大风险"
    )
    
    print(format_ai_report(summary, '002416', '爱施德'))
