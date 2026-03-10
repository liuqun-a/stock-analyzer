#!/bin/bash
# 设置股票监控定时任务（5 分钟一次）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor.py"
LOG_FILE="$SCRIPT_DIR/../logs/monitor.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

echo "🦞 设置股票监控定时任务..."
echo "监控频率：5 分钟一次"
echo "日志文件：$LOG_FILE"
echo ""

# 备份现有 crontab
crontab -l > /tmp/cron_backup.$$.bak 2>/dev/null || true

# 添加监控任务（5 分钟一次，仅交易日）
# 注意：cron 最小粒度是分钟，5 分钟一次用 */5
CRON_JOB="*/5 9-11,13-15 * * 1-5 cd $SCRIPT_DIR/.. && uv run scripts/monitor.py --once >> $LOG_FILE 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "monitor.py --once"; then
    echo "⚠️ 监控任务已存在，先删除旧任务..."
    crontab -l 2>/dev/null | grep -v "monitor.py --once" | crontab -
fi

# 添加新任务
(crontab -l 2>/dev/null | grep -v "monitor.py --once"; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 定时任务已设置！"
echo ""
echo "📋 当前 crontab:"
crontab -l | grep "monitor.py"
echo ""
echo "📝 说明:"
echo "  - 监控时间：交易日 9:00-11:30, 13:00-15:30"
echo "  - 监控频率：每 5 分钟一次"
echo "  - 日志文件：$LOG_FILE"
echo ""
echo "🔍 查看日志：tail -f $LOG_FILE"
echo "🛑 停止监控：crontab -e  # 注释掉对应行"
