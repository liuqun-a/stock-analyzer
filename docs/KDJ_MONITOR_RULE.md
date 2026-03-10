# 📊 KDJ 监控规则

**版本：** 1.0  
**创建日期：** 2026-03-10  
**类型：** 超短线监控（1 分钟 K 线）

---

## 🎯 监控规则名称

**KDJ 监控**

---

## 📋 规则定义

### 买入信号（3 条件共振）

```
条件 1: 1 分钟 KDJ 的 J 值 ≤ 20
条件 2: KDJ 金叉（J 线上穿 K 线和 D 线）
条件 3: 分时回踩均价线不破

→ 同时满足 → 买入预警
```

### 卖出信号（3 条件共振）

```
条件 1: 1 分钟 KDJ 的 J 值 ≥ 80
条件 2: KDJ 死叉（J 线下穿 K 线和 D 线）
条件 3: 分时跌破均价线

→ 同时满足 → 卖出预警
```

### 止损规则

```
亏损 ≥ 6% → 坚决止损预警
```

---

## ⚙️ 可配置参数

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| **KDJ_J_BUY** | 20 | J 值买入阈值（超卖区） |
| **KDJ_J_SELL** | 80 | J 值卖出阈值（超买区） |
| **STOP_LOSS_PCT** | 6 | 止损百分比 |
| **TIMEFRAME** | 1 分钟 | K 线周期 |
| **KDJ_N** | 9 | KDJ 计算周期（RSV 的 N 日） |
| **KDJ_M** | 3 | KDJ 平滑周期（K 的 M 日） |

---

## 📊 KDJ 计算公式

```python
# RSV（未成熟随机值）
RSV = (收盘价 - N 日最低价) / (N 日最高价 - 最低价) × 100

# K 线（快线）
K = RSV 的 M 日移动平均

# D 线（慢线）
D = K 的 M 日移动平均

# J 线（超快线）
J = 3 × K - 2 × D
```

**默认参数：**
- N = 9
- M = 3

---

## 🔍 信号检测逻辑

### 金叉检测

```python
def is_golden_cross(kdj_current, kdj_prev):
    """
    检测金叉
    金叉：J 线从下向上穿过 K 线和 D 线
    """
    # 当前 J > K 且 J > D
    current_cross = (kdj_current['J'] > kdj_current['K']) and \
                    (kdj_current['J'] > kdj_current['D'])
    
    # 之前 J < K 或 J < D（之前没金叉）
    prev_no_cross = (kdj_prev['J'] <= kdj_prev['K']) or \
                    (kdj_prev['J'] <= kdj_prev['D'])
    
    return current_cross and prev_no_cross
```

### 死叉检测

```python
def is_dead_cross(kdj_current, kdj_prev):
    """
    检测死叉
    死叉：J 线从上向下穿过 K 线和 D 线
    """
    # 当前 J < K 且 J < D
    current_cross = (kdj_current['J'] < kdj_current['K']) and \
                    (kdj_current['J'] < kdj_current['D'])
    
    # 之前 J > K 或 J > D（之前没死叉）
    prev_no_cross = (kdj_prev['J'] >= kdj_prev['K']) or \
                    (kdj_prev['J'] >= kdj_prev['D'])
    
    return current_cross and prev_no_cross
```

### 买入信号检测

```python
def check_buy_signal(kdj, price, avg_price):
    """
    检测买入信号（3 条件共振）
    """
    # 条件 1: J ≤ 20
    condition_1 = kdj['J'] <= 20
    
    # 条件 2: 金叉
    condition_2 = is_golden_cross(kdj_current, kdj_prev)
    
    # 条件 3: 回踩均价线不破（最低价 >= 均价线）
    condition_3 = price['low'] >= avg_price
    
    # 3 个条件同时满足
    return condition_1 and condition_2 and condition_3
```

### 卖出信号检测

```python
def check_sell_signal(kdj, price, avg_price):
    """
    检测卖出信号（3 条件共振）
    """
    # 条件 1: J ≥ 80
    condition_1 = kdj['J'] >= 80
    
    # 条件 2: 死叉
    condition_2 = is_dead_cross(kdj_current, kdj_prev)
    
    # 条件 3: 跌破均价线（现价 < 均价线）
    condition_3 = price['current'] < avg_price
    
    # 3 个条件同时满足
    return condition_1 and condition_2 and condition_3
```

### 止损检测

```python
def check_stop_loss(buy_price, current_price, stop_loss_pct=6):
    """
    检测止损
    """
    loss_pct = (buy_price - current_price) / buy_price * 100
    return loss_pct >= stop_loss_pct
```

---

## 📬 预警推送格式

### 买入预警

```
🟢 KDJ 买入信号

股票：{name} ({code})
时间：{time}

📊 KDJ 指标
  K: {K:.2f}
  D: {D:.2f}
  J: {J:.2f}

💰 价格
  当前价：¥{price:.2f}
  均价线：¥{avg_price:.2f}

✅ 触发条件
  ✅ J ≤ 20（超卖）
  ✅ KDJ 金叉
  ✅ 回踩均价线不破

⚠️ 建议止损价：¥{stop_price:.2f}（-6%）
```

### 卖出预警

```
🔴 KDJ 卖出信号

股票：{name} ({code})
时间：{time}

📊 KDJ 指标
  K: {K:.2f}
  D: {D:.2f}
  J: {J:.2f}

💰 价格
  当前价：¥{price:.2f}
  均价线：¥{avg_price:.2f}

✅ 触发条件
  ✅ J ≥ 80（超买）
  ✅ KDJ 死叉
  ✅ 跌破均价线

💡 建议：及时止盈
```

### 止损预警

```
🔴 止损预警

股票：{name} ({code})
时间：{time}

💰 价格
  买入价：¥{buy_price:.2f}
  当前价：¥{current_price:.2f}
  亏损：-{loss_pct:.2f}%

⚠️ 亏损已达 6%，坚决止损！
```

---

## 🎯 使用方法

### 告知监控股票

**格式：**
```
用 KDJ 监控规则监控 {股票代码}
```

**示例：**
```
用 KDJ 监控规则监控 002416
用 KDJ 监控规则监控 300750
用 KDJ 监控规则监控 600519
```

### 修改参数

**格式：**
```
KDJ 监控参数调整为 J 买入={值}, J 卖出={值}, 止损={值}%
```

**示例：**
```
KDJ 监控参数调整为 J 买入=15, J 卖出=85, 止损=5%
```

### 查看监控状态

**格式：**
```
查看 KDJ 监控状态
```

---

## ⚠️ 注意事项

### 适用场景

- ✅ **震荡市** - 最有效
- ⚠️ **单边市** - 谨慎使用（可能连续超买/超卖）
- ❌ **停牌/涨跌停** - 无法交易

### 不适用场景

- ❌ 涨停板股票（无法买入）
- ❌ 跌停板股票（无法卖出）
- ❌ 停牌股票（无法交易）
- ❌ 流动性差的股票（买卖困难）

### 风险提示

1. **超短线风险**
   - 1 分钟 K 线变化快
   - 需要快速反应
   - 不适合长线投资者

2. **假信号风险**
   - 单一 KDJ 信号不可靠
   - 必须 3 条件共振
   - 仍需结合其他指标

3. **止损纪律**
   - 亏损 6% 坚决执行
   - 不抱侥幸心理
   - 保住本金第一

---

## 📊 监控日志

**记录内容：**
- 每次信号触发时间
- KDJ 数值
- 价格信息
- 是否执行交易
- 盈亏结果

**日志位置：**
```
logs/kdj_monitor_YYYY-MM-DD.log
```

---

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|-----|------|------|
| 1.0 | 2026-03-10 | 初始版本 |

---

## 📞 相关文档

- [COMMIT_RULES.md](COMMIT_RULES.md) - 提交规则
- [AI_RULES.md](AI_RULES.md) - AI 会话规则
- [PUBLISH_RULES.md](PUBLISH_RULES.md) - 发布规则

---

**🦞 KDJ 监控规则已建立，随时可以启用！**
