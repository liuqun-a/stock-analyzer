# 📋 Skill 发布规则

## ✅ 已确认的规则

### 规则 1：仓库命名

**当前 Skill：**
- 仓库名：`stock-analyzer`
- GitHub: https://github.com/liuqun-a/stock-analyzer

### 规则 2：新 Skill 发布流程

**发布新 Skill 时：**

1. **必须创建独立仓库**
   ```
   ❌ 不要放在现有仓库中
   ✅ 每个 Skill 独立仓库
   ```

2. **仓库名需要确认**
   ```bash
   # 发布前必须询问
   "新 Skill 要发布到哪个仓库？"
   "仓库名：xxx-skill"
   ```

3. **等待用户确认后执行**
   ```bash
   # 用户确认后
   git remote add origin git@github.com:liuqun-a/仓库名.git
   git push -u origin main
   ```

---

## 📝 发布检查清单

### 发布前检查

- [ ] 敏感信息已移除
- [ ] 已通过 `check_secrets.py` 检查
- [ ] 仓库名已确认
- [ ] GitHub 配置已更新

### 发布步骤

```bash
# 1. 确认仓库名
仓库名：xxx-skill  ← 必须用户确认

# 2. 初始化 Git
cd /home/admin/.openclaw/workspace/skills/xxx-skill
git init
git add .
git commit -m "Initial commit"

# 3. 设置远程仓库
git remote add origin git@github.com:liuqun-a/xxx-skill.git

# 4. 推送
git push -u origin main
```

---

## 🎯 当前仓库列表

| Skill | 仓库名 | GitHub 地址 |
|------|--------|-----------|
| stock-analyzer | stock-analyzer | https://github.com/liuqun-a/stock-analyzer |

---

## ⚠️ 重要提醒

**发布新 Skill 前必须：**
1. ✅ 询问用户仓库名
2. ✅ 等待用户确认
3. ✅ 确认后才能推送

**禁止行为：**
- ❌ 擅自决定仓库名
- ❌ 放在现有仓库中
- ❌ 未确认就推送

---

**🦞 规则已建立，严格遵守！**
