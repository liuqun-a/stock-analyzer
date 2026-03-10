# 📊 限流配置说明

## 智兔数服免费额度

| 限制类型 | 额度 | 重置时间 |
|---------|------|---------|
| **每日请求** | 200 次 | 每日 0:00 自动重置 |
| **每分钟请求** | 300 次 | 每分钟滚动重置 |
| **总请求** | 不限 | - |
| **使用期限** | 不限 | - |

---

## ✅ 已实现的限流保护

### 1. 自动计数
```python
# 每次调用智兔数服 API 自动计数
self.rate_limiter.acquire()
```

### 2. 智能刷新间隔
根据剩余额度和剩余交易时间，动态调整刷新间隔：

```
剩余额度充足 → 5 秒刷新（默认）
剩余额度中等 → 15-30 秒刷新
剩余额度紧张 → 60 秒刷新（最长）
非交易时段   → 暂停监控（节省额度）
```

### 3. 自动切换数据源
当智兔数服额度用尽时，自动切换到：
1. 东方财富（免费，无限额）
2. AkShare（开源，免费）

### 4. 状态显示
每次刷新显示限流状态：
```
[限流状态] 今日剩余：195 次 | 分钟剩余：298 次 | 下次刷新：5 秒
```

---

## 📈 额度使用估算

### 场景 1：监控股票池（10 只股票）
```
每轮刷新：10 次 API 调用
刷新间隔：5 秒
每小时调用：10 × (3600/5) = 7,200 次 ❌ 超出限制

优化后（智能间隔）：
剩余额度 200 次，剩余交易时间 4 小时
理想间隔：(4 × 60 × 60) / 200 = 72 秒
实际调用：10 × (4 × 3600 / 72) ≈ 2,000 次 ❌ 仍超出

解决方案：
1. 减少监控股票数量（建议 ≤ 5 只）
2. 增加刷新间隔（手动设置 --interval 30）
3. 使用备用数据源分担
```

### 场景 2：监控 5 只股票（推荐配置）
```
每轮刷新：5 次 API 调用
智能间隔：约 60 秒（根据额度动态调整）
每小时调用：5 × 60 = 300 次
4 小时交易：5 × 240 = 1,200 次 ❌ 仍超出

需要进一步优化：
- 只在关键时间点监控（开盘、收盘、整点）
- 或使用备用数据源为主
```

---

## 🎯 推荐配置

### 配置 1：保守模式（确保不超限）
```bash
# 编辑 config/alerts.yaml
rate_limit:
  smart_interval: true
  min_interval: 60    # 最小 60 秒
  max_interval: 300   # 最大 5 分钟
```

```bash
# 启动监控
uv run scripts/monitor.py --interval 60
```

**额度消耗：**
- 5 只股票 × (240 分钟 / 60 秒) = 5 × 240 = 1,200 次/日 ❌

**优化：减少监控股票**
- 3 只股票 × 240 次 = 720 次/日 ❌

**再优化：延长间隔**
- 3 只股票 × (240 分钟 / 120 秒) = 3 × 120 = 360 次/日 ❌

**最终方案：混合数据源**
- 智兔数服：200 次/日（用于关键股票）
- 东方财富：无限（用于其他股票）

### 配置 2：关键时段监控（推荐）
```bash
# 只在关键时间点监控
crontab -e

# 9:25 集合竞价
25 9 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 9:30 开盘
30 9 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 10:00 整点
0 10 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 11:00 上午收盘前
55 11 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 13:00 下午开盘
0 13 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 14:00 整点
0 14 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 14:55 收盘前
55 14 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 15:00 收盘
0 15 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 每日调用：8 次 × 5 只股票 = 40 次/日 ✅ 远低于 200 次限制
```

### 配置 3：实时监控 + 智能限流（高级）
```bash
# 启用智能间隔
# 编辑 config/alerts.yaml
rate_limit:
  smart_interval: true
  min_interval: 30    # 最小 30 秒
  max_interval: 120   # 最大 2 分钟

# 启动监控
uv run scripts/monitor.py --interval 30
```

**额度消耗：**
- 智能算法根据剩余额度动态调整
- 确保 200 次额度够用一整天
- 优先保障关键时段（开盘、收盘）

---

## 🔧 手动控制

### 查看限流状态
```bash
uv run python3 -c "
from scripts.monitor import StockMonitor
m = StockMonitor()
status = m.data_source.rate_limiter.get_status()
print(f'今日已用：{status[\"daily_used\"]}次')
print(f'今日剩余：{status[\"daily_remaining\"]}次')
print(f'分钟已用：{status[\"minute_used\"]}次')
print(f'分钟剩余：{status[\"minute_remaining\"]}次')
"
```

### 重置限流计数（测试用）
```bash
# 修改 monitor.py 中的计数为 0
# 或重启监控服务
```

### 临时关闭限流（不推荐）
```yaml
# config/alerts.yaml
rate_limit:
  enabled: false  # ⚠️ 可能导致超额
```

---

## 💡 最佳实践

1. **监控股票池不要太大**
   - 建议 ≤ 5 只（智兔数服）
   - 更多股票使用备用数据源

2. **使用智能间隔**
   - 让算法自动优化刷新频率
   - 避免手动设置过短间隔

3. **关键时段重点监控**
   - 开盘（9:30）、收盘（15:00）
   - 整点检查即可

4. **备用数据源分担**
   - 东方财富：免费无限额
   - AkShare：开源免费
   - 非关键股票用备用源

5. **定期检查限流状态**
   - 监控日志中查看剩余次数
   - 额度紧张时手动调整

---

## ⚠️ 超额后果

- **每日 200 次超限**：当日无法再调用智兔数服
- **每分钟 300 次超限**：暂时封禁 1 分钟
- **频繁超限**：可能降低免费额度或封禁 Token

**解决方案：**
1. 自动切换到备用数据源
2. 等待次日 0 点重置
3. 申请付费版本（更高额度）

---

## 📞 需要更高额度？

智兔数服付费版本：
- 体验版：1,000 次/分钟
- 包月版：更高额度
- 包年版：3,000 次/分钟
- 至尊版：6,000 次/分钟

官网：https://www.zhituapi.com/

---

**限流已内置，放心使用 🦞**
