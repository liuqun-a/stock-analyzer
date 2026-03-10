# 🦞 Stock Analyzer - A 股/港股智能分析系统

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-orange.svg)](https://openclaw.ai)

基于 OpenClaw 的股票智能分析系统，支持实时监控、技术分析、AI 辅助决策。

---

## ✨ 功能特性

### 📊 核心功能

- **实时监控** - 5 分钟一次自动检测价格波动
- **技术指标** - MA/MACD/RSI 完整计算
- **AI 分析** - MiniMax-M2.5 大模型辅助决策
- **预警推送** - 飞书实时推送预警消息
- **大盘复盘** - 每日自动生成投资日报

### 🎯 监控类型

| 类型 | 说明 | 频率 |
|-----|------|------|
| **ETF 监控** | 价格涨跌幅 ±1% | 5 分钟 |
| **个股监控** | 价格低于警戒线 | 定点检查 |
| **技术指标** | MA/MACD/RSI 信号 | 实时计算 |

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- OpenClaw 环境
- 飞书账号（用于推送）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/stock-analyzer.git
cd stock-analyzer

# 2. 安装依赖
uv sync

# 3. 配置 OpenClaw
# 确保 ~/.openclaw/openclaw.json 中配置了飞书账号
```

### 配置

**1. 编辑监控股票池**
```yaml
# config/stocks.yaml
custom_watch:
  - code: "561570"
    name: "油气 ETF"
    alert_pct: 1  # ±1% 预警
    enabled: true
```

**2. 编辑预警阈值**
```yaml
# config/alerts.yaml
price_alert:
  threshold_pct: 3  # 默认涨跌幅阈值
```

### 使用

```bash
# 实时监控
uv run scripts/monitor.py

# 单次检查
uv run scripts/monitor.py --once

# 技术指标分析
uv run scripts/technical.py

# 大盘复盘
uv run scripts/daily_review.py
```

---

## 📁 项目结构

```
stock-analyzer/
├── scripts/              # Python 脚本
│   ├── monitor.py        # 实时监控
│   ├── technical.py      # 技术指标
│   ├── news_search.py    # 新闻搜索
│   ├── ai_summary.py     # AI 分析
│   └── daily_review.py   # 大盘复盘
├── config/               # 配置文件（不提交到 Git）
│   ├── stocks.yaml       # 监控股票池
│   └── alerts.yaml       # 预警配置
├── docs/                 # 文档
├── SKILL.md              # OpenClaw Skill 定义
└── README.md             # 本文件
```

---

## 📊 功能演示

### 实时监控

```bash
🦞 股票监控启动 - 刷新间隔：5 秒
监控股票池：A 股 3 只，港股 3 只，ETF 2 只

📊 检查 卫星 ETF (159206)
⚠️  触发预警：相对基准价¥18.29 大跌 -1.42%
📬 发送飞书推送...
✅ 预警已发送
```

### 技术指标

```
📈 油气 ETF (561570)
  MA5:  14.35
  MA10: 14.12
  MA20: 13.89
  MACD DIF: 0.160
  RSI6: 80.8
  信号：BUY (强度：⭐⭐⭐)
```

---

## 🔧 开发

### 添加新股票

编辑 `config/stocks.yaml`：
```yaml
custom_watch:
  - code: "000001"
    name: "平安银行"
    alert_pct: 3
    enabled: true
```

### 添加新功能

1. 在 `scripts/` 目录创建新脚本
2. 在 `SKILL.md` 中注册命令
3. 更新本文档

---

## 📝 配置说明

### 配置文件

| 文件 | 说明 | 是否提交 |
|-----|------|---------|
| `config/stocks.yaml` | 监控股票池 | ✅ 提交模板 |
| `config/alerts.yaml` | 预警阈值 | ✅ 提交 |
| `config/api_keys.yaml` | API 密钥 | ❌ 不提交 |

### 环境变量

无需额外环境变量，复用 OpenClaw 全局配置。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenClaw](https://openclaw.ai) - AI 助手框架
- [MiniMax](https://platform.minimaxi.com/) - AI 大模型
- [东方财富](https://www.eastmoney.com/) - 行情数据

---

## 📞 联系方式

- 项目地址：https://github.com/YOUR_USERNAME/stock-analyzer
- 问题反馈：https://github.com/YOUR_USERNAME/stock-analyzer/issues

---

**🦞 Happy Coding & Happy Investing!**
