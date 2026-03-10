#!/usr/bin/env python3
"""
A 股分析 - 主入口
统一调用行情、财报、公告、资金流
"""

import sys
import os

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def print_help():
    print("""
📈 A 股分析工具 - 财神爷版
═══════════════════════════════════

用法：python main.py <命令> <股票代码> [参数]

命令：
  quote       查行情（实时股价、成交量）
  financials  看财报（财务指标、估值）
  announce    查公告（最新公告）
  flow        资金流（主力、北向）
  all         全部信息（推荐）

示例：
  python main.py quote 600519
  python main.py financials 000858
  python main.py announce 300750 7
  python main.py flow 601318
  python main.py all 600519

═══════════════════════════════════
💡 提示：数据仅供参考，投资需谨慎
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'help' or command == '-h' or command == '--help':
        print_help()
        return
    
    if len(sys.argv) < 3:
        print("❌ 请提供股票代码")
        print_help()
        sys.exit(1)
    
    symbol = sys.argv[2]
    extra_arg = sys.argv[3] if len(sys.argv) > 3 else ''
    
    # 导入对应模块
    if command == 'quote':
        from quote import get_quote, format_quote
        data = get_quote(symbol)
        print(format_quote(data))
    
    elif command == 'financials':
        from financials import get_financials, format_financials
        data = get_financials(symbol)
        print(format_financials(data))
    
    elif command == 'announce' or command == 'announcements':
        from announcements import get_announcements, format_announcements
        days = int(extra_arg) if extra_arg else 30
        data = get_announcements(symbol, days)
        print(format_announcements(data))
    
    elif command == 'flow' or command == 'capital_flow':
        from capital_flow import get_capital_flow, format_capital_flow
        data = get_capital_flow(symbol)
        print(format_capital_flow(data))
    
    elif command == 'all':
        # 全部信息
        print("=" * 60)
        print("📈 行 情")
        print("=" * 60)
        from quote import get_quote, format_quote
        data = get_quote(symbol)
        print(format_quote(data))
        
        print("\n" + "=" * 60)
        print("📊 财 报")
        print("=" * 60)
        from financials import get_financials, format_financials
        data = get_financials(symbol)
        print(format_financials(data))
        
        print("\n" + "=" * 60)
        print("📢 公 告")
        print("=" * 60)
        from announcements import get_announcements, format_announcements
        data = get_announcements(symbol, 30)
        print(format_announcements(data))
        
        print("\n" + "=" * 60)
        print("💰 资 金 流")
        print("=" * 60)
        from capital_flow import get_capital_flow, format_capital_flow
        data = get_capital_flow(symbol)
        print(format_capital_flow(data))
    
    else:
        print(f"❌ 未知命令：{command}")
        print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
