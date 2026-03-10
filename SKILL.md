---
name: stock-analyzer
description: A 股/港股分析工具 - 行情查询、实时监控、财报分析、公告监控、资金流向
author: 财神爷
version: 2.1.0
metadata: {"clawdbot":{"emoji":"📈","requires":{"bins":["python3"]}}}
rules:
  - 提交前必须执行敏感信息检查
  - 新 Skill 必须使用独立仓库
  - 仓库名必须经用户确认
  - 提交前必须显示内容并确认
---

# A 股/港股分析技能

查询 A 股/港股行情、实时监控预警、分析财报、监控公告、追踪资金流向。

## 命令

### 📈 查行情
```bash
uv run {baseDir}/scripts/quote.py <股票代码>
```

**示例：**
```bash
uv run {baseDir}/scripts/quote.py 600519    # 贵州茅台
uv run {baseDir}/scripts/quote.py 000858    # 五粮液
uv run {baseDir}/scripts/quote.py 300750    # 宁德时代
```

### 🦞 实时监控（新增）
```bash
# 启动实时监控（默认 5 秒刷新）
uv run {baseDir}/scripts/monitor.py

# 自定义刷新间隔
uv run {baseDir}/scripts/monitor.py --interval 10

# 单次检查（测试用）
uv run {baseDir}/scripts/monitor.py --once

# 测试模式
uv run {baseDir}/scripts/monitor.py --test
```

**功能：**
- ✅ 实时价格监控（A 股 + 港股）
- ✅ 涨跌幅预警（可配置阈值）
- ✅ 成交量异常检测
- ✅ 飞书自动推送

### 📊 生成日报（新增）
```bash
uv run {baseDir}/scripts/daily_report.py
```

**功能：**
- ✅ 市场概览（上证/深证/恒生）
- ✅ 监控股票表现排行
- ✅ 预警记录汇总
- ✅ 明日关注股票池

### 📊 分析财报
```bash
uv run {baseDir}/scripts/financials.py <股票代码>
```

**示例：**
```bash
uv run {baseDir}/scripts/financials.py 600519
uv run {baseDir}/scripts/financials.py 000858
```

### 📢 监控公告
```bash
uv run {baseDir}/scripts/announcements.py <股票代码> [天数]
```

**示例：**
```bash
uv run {baseDir}/scripts/announcements.py 300750      # 最近 30 天
uv run {baseDir}/scripts/announcements.py 300750 7    # 最近 7 天
```

### 💰 资金流向
```bash
uv run {baseDir}/scripts/capital_flow.py <股票代码>
```

**示例：**
```bash
uv run {baseDir}/scripts/capital_flow.py 601318   # 中国平安
uv run {baseDir}/scripts/capital_flow.py 600519   # 贵州茅台
```

## 数据源

| 数据源 | 用途 | 状态 |
|-------|------|------|
| **智兔数服** | 实时行情、历史数据、复权数据 | ✅ 主数据源 |
| **东方财富** | 实时行情、财报、资金流 | ✅ 备用 |
| **新浪财经** | 实时行情 | ✅ 备用 |
| **AkShare** | 兜底数据源 | ✅ 开源免费 |

## 配置文件

### `config/api_keys.yaml`
API 密钥配置（智兔数服 Token 等）

### `config/alerts.yaml`
预警阈值配置：
```yaml
price_alert:
  threshold_pct: 3        # 涨跌幅超过 3% 预警
  
volume_alert:
  threshold_ratio: 2      # 成交量超日均 2 倍
```

### `config/stocks.yaml`
监控股票池配置：
```yaml
a_shares:
  - code: "600519"
    name: "贵州茅台"
    alert_pct: 3
    
hk_shares:
  - code: "00700"
    name: "腾讯控股"
    alert_pct: 3
```

## 定时任务配置

```bash
# 编辑 crontab
crontab -e

# 交易日 9:25 集合竞价提醒
25 9 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 交易日 16:00 生成日报
0 16 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/daily_report.py
```

## 注意事项

1. **股票代码格式**
   - A 股：6 位数字（6 开头沪市，0/3 开头深市）
   - 港股：5 位数字（如 00700）

2. **数据仅供参考，投资需谨慎**

3. **API 频率限制**
   - 智兔数服：注意免费额度
   - 东方财富/AkShare：避免高频请求

4. **实时监控**
   - 建议使用 systemd service 而非 cron（高频任务）
   - 静默时段（23:00-8:00）只推送高优先级预警

## 功能状态

✅ 已实现：
- ✅ 实时行情查询（A 股 + 港股）
- ✅ 实时监控预警（价格/成交量）
- ✅ 飞书自动推送
- ✅ 每日交易报告
- ✅ 财务指标分析
- ✅ 公告监控
- ✅ 资金流向

📝 说明：
- 监控数据源支持自动故障切换（智兔→东方财富→AkShare）
- 预警消息自动推送到飞书
- 日报自动生成并保存

## 待扩展

- [ ] 技术指标（MACD、KDJ、RSI）
- [ ] K 线图分析
- [ ] 龙虎榜数据
- [ ] 融资融券数据
- [ ] 机构调研
- [ ] 盈利预测

---

## ⚠️ 规则（重要）

**提交规则：**
- ✅ 提交前必须执行敏感信息检查
- ✅ 新 Skill 必须使用独立仓库
- ✅ 仓库名必须经用户确认
- ✅ 提交前必须显示内容并确认

**详细规则：**
- [docs/COMMIT_RULES.md](docs/COMMIT_RULES.md) - 提交规则
- [docs/AI_RULES.md](docs/AI_RULES.md) - AI 会话规则
- [docs/PUBLISH_RULES.md](docs/PUBLISH_RULES.md) - 发布规则

**违反后果：**
- ❌ 第一次：警告
- ❌ 第二次：撤销提交
- ❌ 第三次：禁止提交权限
- [ ] 策略回测
