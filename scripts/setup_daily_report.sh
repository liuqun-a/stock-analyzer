#!/bin/bash
# 设置股票日报定时任务（每日 18:00）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_SCRIPT="$SCRIPT_DIR/daily_review.py"
LOG_FILE="$SCRIPT_DIR/../logs/daily_report.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

echo "🦞 设置股票日报定时任务..."
echo "运行时间：每日 18:00（北京时间）"
echo "日志文件：$LOG_FILE"
echo ""

# 备份现有 crontab
crontab -l > /tmp/cron_backup.$$.bak 2>/dev/null || true

# 删除旧的日报任务（如果有）
crontab -l 2>/dev/null | grep -v "daily_review.py" | crontab - 2>/dev/null || true

# 添加新任务：每日 18:00（北京时间 = UTC+8，所以 cron 用 10 点 UTC）
CRON_JOB="0 10 * * * cd $SCRIPT_DIR/.. && uv run scripts/daily_review.py >> $LOG_FILE 2>&1"

# 添加任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 日报定时任务已设置！"
echo ""
echo "📋 当前日报相关任务:"
crontab -l | grep "daily_review"
echo ""
echo "📝 说明:"
echo "  - 运行时间：每日 18:00（北京时间）"
echo "  - 内容：大盘复盘 + 个股分析 + AI 摘要"
echo "  - 日志文件：$LOG_FILE"
echo ""
echo "🔍 查看日志：tail -f $LOG_FILE"
echo "🛑 停止任务：crontab -e  # 注释掉 daily_review.py 行"
