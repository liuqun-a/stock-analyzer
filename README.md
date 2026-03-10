# 🦞 股票监控系统 - 快速启动指南

## ✅ 已完成配置

- [x] 智兔数服 API Token 已配置
- [x] 监控脚本 `monitor.py` 已创建（✅ 限流控制）
- [x] 日报生成 `daily_report.py` 已创建
- [x] 配置文件已创建（`config/` 目录）
- [x] Python 依赖已安装
- [x] 智能刷新策略（根据剩余额度动态调整间隔）

---

## 🚀 快速测试

### 1. 测试行情获取
```bash
cd /home/admin/.openclaw/workspace/skills/stock-analyzer
uv run scripts/monitor.py --test
```

**预期输出：**
```
测试模式 - 检查贵州茅台
行情数据：{'source': 'zhitu', 'price': 1406.1, 'change_pct': 0.65...}
```

### 2. 单次监控检查
```bash
uv run scripts/monitor.py --once
```

### 3. 生成今日日报
```bash
uv run scripts/daily_report.py
```

---

## 📝 配置监控股票池

编辑 `config/stocks.yaml`，添加你要监控的股票：

```yaml
a_shares:
  - code: "600519"
    name: "贵州茅台"
    alert_pct: 3      # 涨跌幅超过 3% 预警
    enabled: true
    
  - code: "000001"    # 添加你的股票
    name: "平安银行"
    alert_pct: 3
    enabled: true

hk_shares:
  - code: "00700"
    name: "腾讯控股"
    alert_pct: 3
    enabled: true
```

---

## ⏰ 设置定时任务

### 方案 1：Cron（简单）

```bash
crontab -e
```

添加以下任务：

```bash
# 交易日 9:25 集合竞价提醒
25 9 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/monitor.py --once

# 交易日 16:00 生成日报
0 16 * * 1-5 cd /home/admin/.openclaw/workspace/skills/stock-analyzer && uv run scripts/daily_report.py
```

### 方案 2：Systemd Service（7×24 实时监控）

创建服务文件：

```bash
sudo nano /etc/systemd/system/stock-monitor.service
```

内容：

```ini
[Unit]
Description=Stock Monitor Service
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/skills/stock-analyzer
ExecStart=/home/admin/.local/bin/uv run scripts/monitor.py --interval 5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-monitor
sudo systemctl start stock-monitor
sudo systemctl status stock-monitor
```

---

## 🔔 飞书推送配置

当前版本已集成飞书推送框架，需要配置 Webhook：

1. 在飞书创建机器人
2. 获取 Webhook URL
3. 编辑 `config/alerts.yaml` 添加 Webhook

或者直接使用 OpenClaw 的消息工具（已集成）。

---

## 📊 查看监控日志

```bash
# 查看实时日志
sudo journalctl -u stock-monitor -f

# 查看今日报告
cat reports/report_$(date +%Y-%m-%d).json
```

---

## 🛠️ 常用命令

| 命令 | 说明 |
|-----|------|
| `uv run scripts/monitor.py --test` | 测试模式（检查贵州茅台） |
| `uv run scripts/monitor.py --once` | 单次检查所有股票 |
| `uv run scripts/monitor.py --interval 10` | 实时监控（10 秒刷新） |
| `uv run scripts/daily_report.py` | 生成今日日报 |

---

## ⚠️ 注意事项

1. **API 频率限制（已自动管理）**
   - 智兔数服免费额度：**200 次/日，300 次/分钟**
   - ✅ 已内置限流器，自动计数
   - ✅ 智能刷新策略：根据剩余额度动态调整间隔
   - ✅ 额度不足时自动切换到备用数据源（东方财富/AkShare）
   
   **限流逻辑：**
   - 每日 0 点自动重置计数
   - 根据剩余交易时间和额度计算最优刷新间隔
   - 剩余额度少 → 自动延长间隔（最长 60 秒）
   - 剩余额度多 → 缩短间隔（最短 5 秒）

2. **交易时间**
   - A 股：9:30-11:30, 13:00-15:00
   - 港股：9:30-12:00, 13:00-16:00

3. **静默时段**
   - 默认 23:00-8:00 只推送高优先级预警
   - 可在 `config/alerts.yaml` 调整

4. **数据源切换**
   - 自动故障切换：智兔数服 → 东方财富 → AkShare
   - 无需手动干预

---

## 📁 目录结构

```
stock-analyzer/
├── config/
│   ├── api_keys.yaml      # API 密钥（⚠️ 勿泄露）
│   ├── alerts.yaml        # 预警配置
│   └── stocks.yaml        # 监控股票池
├── scripts/
│   ├── monitor.py         # 实时监控脚本
│   ├── daily_report.py    # 日报生成
│   ├── quote.py           # 行情查询（原有）
│   └── ...                # 其他原有脚本
├── reports/
│   └── report_YYYY-MM-DD.json  # 日报文件
├── SKILL.md               # 技能文档
└── README.md              # 本文件
```

---

## 🆘 故障排查

### 问题 1：API 返回 404
检查智兔数服 Token 是否正确：
```bash
uv run python3 -c "import requests; r=requests.get('https://api.zhituapi.com/hs/real/time/600519', params={'token': '你的 TOKEN'}); print(r.status_code, r.text)"
```

### 问题 2：依赖缺失
```bash
cd /home/admin/.openclaw/workspace/skills/stock-analyzer
uv sync
```

### 问题 3：权限错误
```bash
chmod +x scripts/*.py
```

---

## 🎯 下一步

1. **添加你要监控的股票** → 编辑 `config/stocks.yaml`
2. **测试单次监控** → `uv run scripts/monitor.py --once`
3. **设置定时任务** → 选择 Cron 或 Systemd
4. **配置飞书推送** → 添加 Webhook 或使用 OpenClaw 消息

---

**投资有风险，决策需谨慎 🦞**
