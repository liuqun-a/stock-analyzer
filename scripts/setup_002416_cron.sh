#!/bin/bash
# 设置 002416 爱施德监控定时任务
# 每天上午 10 点和下午 2 点各检查一次

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor.py"
LOG_FILE="$SCRIPT_DIR/../logs/002416_monitor.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

echo "🦞 设置 002416 爱施德监控定时任务..."
echo "监控时间：每天 10:00 和 14:00"
echo "监控条件：股价低于 ¥12.00 时预警"
echo "日志文件：$LOG_FILE"
echo ""

# 备份现有 crontab
crontab -l > /tmp/cron_backup.$$.bak 2>/dev/null || true

# 删除旧的 002416 任务（如果有）
crontab -l 2>/dev/null | grep -v "002416" | crontab - 2>/dev/null || true

# 添加新任务：每天 10:00 和 14:00
CRON_10="0 10 * * * cd $SCRIPT_DIR/.. && uv run scripts/monitor.py --stock 002416 >> $LOG_FILE 2>&1"
CRON_14="0 14 * * * cd $SCRIPT_DIR/.. && uv run scripts/monitor.py --stock 002416 >> $LOG_FILE 2>&1"

# 添加任务
(crontab -l 2>/dev/null; echo "$CRON_10"; echo "$CRON_14") | crontab -

echo ""
echo "✅ 定时任务已设置！"
echo ""
echo "📋 当前 002416 相关任务:"
crontab -l | grep "002416"
echo ""
echo "📝 说明:"
echo "  - 监控时间：每天 10:00 和 14:00"
echo "  - 监控条件：股价低于 ¥12.00 时飞书推送"
echo "  - 日志文件：$LOG_FILE"
echo ""
echo "🔍 查看日志：tail -f $LOG_FILE"
echo "🛑 停止监控：crontab -e  # 注释掉 002416 相关行"
