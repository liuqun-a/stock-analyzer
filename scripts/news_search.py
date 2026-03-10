#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻搜索模块
参考：Daily Stock Analysis 项目
功能：搜索股票相关新闻和舆情
数据源：SearXNG (本地部署，免费)
"""

import subprocess
import json
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NewsResult:
    """新闻结果数据类"""
    title: str
    content: str  # 摘要
    url: str
    source: str  # 来源网站
    published_date: Optional[str] = None
    
    def to_text(self) -> str:
        """转换为文本格式"""
        date_str = f" ({self.published_date})" if self.published_date else ""
        return f"【{self.source}】{self.title}{date_str}\n{self.content[:200]}"


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: List[NewsResult]
    provider: str = "SearXNG"
    success: bool = True
    error_message: Optional[str] = None
    search_time: float = 0.0
    
    def to_context(self, max_results: int = 5) -> str:
        """将搜索结果转换为可用于 AI 分析的上下文"""
        if not self.success or not self.results:
            return f"搜索 '{self.query}' 未找到相关结果。"
        
        lines = [f"【{self.query} 搜索结果】（来源：{self.provider}）"]
        for i, result in enumerate(self.results[:max_results], 1):
            lines.append(f"\n{i}. {result.to_text()}")
        
        return "\n".join(lines)


class NewsSearcher:
    """新闻搜索器（基于 SearXNG）"""
    
    def __init__(self, searxng_url: str = "http://localhost:8080"):
        """
        初始化新闻搜索器
        
        Args:
            searxng_url: SearXNG 服务地址
        """
        self.searxng_url = searxng_url
        self.script_path = "/home/admin/.openclaw/workspace/skills/searxng/scripts/searxng.py"
    
    def search(self, query: str, max_results: int = 5, category: str = "news") -> SearchResponse:
        """
        执行新闻搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            category: 搜索类别 (news/general)
            
        Returns:
            SearchResponse 对象
        """
        import time
        start_time = time.time()
        
        try:
            # 调用 SearXNG 脚本
            cmd = [
                "uv", "run", "python3", self.script_path,
                "search", query,
                "-c", category,
                "--json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/admin/.openclaw/workspace/skills/searxng"
            )
            
            if result.returncode != 0:
                return SearchResponse(
                    query=query,
                    results=[],
                    success=False,
                    error_message=f"SearXNG 调用失败：{result.stderr}"
                )
            
            # 解析 JSON 结果
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                return SearchResponse(
                    query=query,
                    results=[],
                    success=False,
                    error_message="JSON 解析失败"
                )
            
            # 转换为 NewsResult 列表
            results = []
            for item in data.get('results', [])[:max_results]:
                results.append(NewsResult(
                    title=item.get('title', ''),
                    content=item.get('content', item.get('snippet', '')),
                    url=item.get('url', ''),
                    source=item.get('source', ''),
                    published_date=item.get('publishedDate'),
                ))
            
            elapsed = time.time() - start_time
            
            return SearchResponse(
                query=query,
                results=results,
                provider="SearXNG",
                success=True,
                search_time=elapsed
            )
            
        except subprocess.TimeoutExpired:
            return SearchResponse(
                query=query,
                results=[],
                success=False,
                error_message="搜索超时"
            )
        except Exception as e:
            return SearchResponse(
                query=query,
                results=[],
                success=False,
                error_message=str(e)
            )
    
    def search_stock_news(self, code: str, name: str, days: int = 7) -> SearchResponse:
        """
        搜索股票相关新闻
        
        Args:
            code: 股票代码
            name: 股票名称
            days: 搜索最近 N 天的新闻
            
        Returns:
            SearchResponse 对象
        """
        query = f"{name} {code} 股票"
        return self.search(query, max_results=10, category="news")
    
    def search_stock_risks(self, code: str, name: str) -> SearchResponse:
        """
        搜索股票风险相关信息
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            SearchResponse 对象
        """
        query = f"{name} {code} 风险 利空 违规 处罚"
        return self.search(query, max_results=5, category="news")
    
    def search_industry_news(self, industry: str) -> SearchResponse:
        """
        搜索行业新闻
        
        Args:
            industry: 行业名称
            
        Returns:
            SearchResponse 对象
        """
        query = f"{industry} 行业 新闻 政策"
        return self.search(query, max_results=5, category="news")


class MarketNewsAnalyzer:
    """市场新闻分析器"""
    
    def __init__(self):
        self.searcher = NewsSearcher()
    
    def analyze_stock(self, code: str, name: str) -> dict:
        """
        分析单只股票的新闻面
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            分析结果字典
        """
        # 搜索新闻
        news_response = self.searcher.search_stock_news(code, name)
        risk_response = self.searcher.search_stock_risks(code, name)
        
        # 汇总分析
        analysis = {
            'code': code,
            'name': name,
            'news_count': len(news_response.results),
            'risk_count': len(risk_response.results),
            'news_context': news_response.to_context(5),
            'risk_context': risk_response.to_context(3),
            'sentiment': 'neutral',  # positive/negative/neutral
        }
        
        # 简单情感分析（根据风险新闻数量）
        if len(risk_response.results) > 2:
            analysis['sentiment'] = 'negative'
        elif len(news_response.results) > 5:
            analysis['sentiment'] = 'positive'
        
        return analysis
    
    def format_news_report(self, code: str, name: str, analysis: dict) -> str:
        """
        格式化新闻分析报告
        
        Args:
            code: 股票代码
            name: 股票名称
            analysis: 分析结果
            
        Returns:
            格式化的报告文本
        """
        sentiment_map = {
            'positive': '🟢',
            'negative': '🔴',
            'neutral': '🟡'
        }
        
        emoji = sentiment_map.get(analysis['sentiment'], '🟡')
        
        report = f"""📰 新闻舆情分析

{emoji} {name} ({code})
情感倾向：{analysis['sentiment']}

━━━━━━━━━━━━━━━━━━━━

📊 新闻统计
  相关新闻：{analysis['news_count']} 条
  风险信息：{analysis['risk_count']} 条

━━━━━━━━━━━━━━━━━━━━

📈 最新动态
{analysis['news_context'][:500]}...

━━━━━━━━━━━━━━━━━━━━

⚠️ 风险提示
{analysis['risk_context'][:300] if analysis['risk_context'] else '暂无重大风险'}

━━━━━━━━━━━━━━━━━━━━
"""
        return report


if __name__ == '__main__':
    # 测试
    analyzer = MarketNewsAnalyzer()
    
    print("测试新闻搜索...")
    result = analyzer.analyze_stock('002416', '爱施德')
    print(f"新闻数量：{result['news_count']}")
    print(f"情感倾向：{result['sentiment']}")
