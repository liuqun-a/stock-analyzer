# 🚀 GitHub 发布配置指南

## 📋 功能说明

GitHub 配置管理工具帮你：

- ✅ 保存 GitHub 账号信息
- ✅ 保存仓库配置
- ✅ 一键发布到 GitHub
- ✅ 复用配置（无需重复输入）

---

## 🔧 配置步骤

### 步骤 1：生成 GitHub Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 填写说明（如：stock-analyzer）
4. 选择权限：
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. 点击 "Generate token"
6. **复制 Token**（只显示一次，妥善保存）

---

### 步骤 2：初始化配置

```bash
cd /home/admin/.openclaw/workspace/skills/stock-analyzer

# 运行配置向导
uv run scripts/github_config.py setup
```

**交互式输入：**

```
🔧 GitHub 配置向导
============================================================

📛 GitHub 账号信息
------------------------------------------------------------
GitHub 用户名：YOUR_USERNAME
GitHub 邮箱：your-email@example.com

🔑 GitHub Token 配置
------------------------------------------------------------
生成 Token：https://github.com/settings/tokens
需要的权限：repo, workflow

GitHub Token: ghp_xxxxxxxxxxxxxxxxxxxx

📦 仓库配置
------------------------------------------------------------
仓库名称：stock-analyzer
仓库描述：A 股/港股智能分析系统
可见性 (public/private) [public]: public
许可证 (MIT/Apache-2.0/GPL-3.0) [MIT]: MIT

🏷️  主题标签（逗号分隔）
例如：stock,python,openclaw [stock,python,ai]: stock,python,openclaw,ai,quant

============================================================
保存配置？(y/N): y

✅ 配置已保存！
```

---

### 步骤 3：查看配置

```bash
# 查看当前配置
uv run scripts/github_config.py show
```

**输出示例：**

```
============================================================
📋 GitHub 配置
============================================================

📛 GitHub 账号
  用户名：YOUR_USERNAME
  邮箱：your-email@example.com
  Token: 已配置

📦 仓库配置
  名称：stock-analyzer
  描述：A 股/港股智能分析系统
  可见性：public
  许可证：MIT
  主题：stock, python, openclaw, ai, quant

🔧 Git 配置
  默认分支：main
  远程名称：origin

🌐 远程仓库：https://github.com/YOUR_USERNAME/stock-analyzer.git

============================================================
```

---

### 步骤 4：测试连接

```bash
# 测试 GitHub 连接
uv run scripts/github_config.py test
```

**输出示例：**

```
🔍 测试 GitHub 连接...

✅ GitHub 连接正常
   用户：YOUR_USERNAME
   邮箱：your-email@example.com
```

---

## 🚀 发布到 GitHub

### 方法 1：一键发布（推荐）

```bash
# 自动检查、确认、发布
uv run scripts/github_config.py publish
```

**流程：**

1. ✅ 测试 GitHub 连接
2. ✅ 检查 Git 仓库
3. ✅ 添加远程仓库
4. ✅ 推送到 GitHub
5. ✅ 显示仓库链接

---

### 方法 2：手动发布

```bash
# 1. 初始化 Git
git init
git add .
git commit -m "Initial commit"

# 2. 查看远程 URL
uv run scripts/github_config.py show

# 3. 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git

# 4. 推送
git push -u origin main
```

---

## 📁 配置文件说明

### 配置位置

```
~/.openclaw/workspace/skills/stock-analyzer/config/github_config.yaml
```

### 配置文件内容

```yaml
github:
  username: "YOUR_USERNAME"
  email: "your-email@example.com"
  token: "ghp_xxxxxxxxxxxxxxxxxxxx"

repository:
  name: "stock-analyzer"
  description: "A 股/港股智能分析系统"
  visibility: "public"
  license: "MIT"
  topics:
    - stock
    - python
    - openclaw
    - ai
    - quant

git:
  default_branch: "main"
  remote_name: "origin"

publish:
  auto_release: false
  auto_push: true
  pre_commit_check: true
```

---

## 🔐 安全说明

### 文件权限

配置文件自动设置为 **600 权限**（只有所有者可读写）：

```bash
ls -la config/github_config.yaml
# -rw------- 1 admin admin ...
```

### .gitignore

配置文件已添加到 `.gitignore`，**不会被提交到 Git**：

```gitignore
# Config (包含敏感信息)
config/api_keys.yaml
config/secrets.yaml
config/github_config.yaml  # ← GitHub 配置
```

### Token 安全

- ✅ Token 只保存在本地配置文件
- ✅ 不会提交到 GitHub
- ✅ 文件权限 600（仅所有者可读）

---

## 🛠️ 常用命令

### 配置管理

```bash
# 初始化配置
uv run scripts/github_config.py setup

# 查看配置
uv run scripts/github_config.py show

# 测试连接
uv run scripts/github_config.py test
```

### 发布

```bash
# 一键发布
uv run scripts/github_config.py publish

# 手动推送
git push origin main
```

### 修改配置

```bash
# 编辑配置文件
nano config/github_config.yaml

# 重新配置
uv run scripts/github_config.py setup
```

---

## ⚠️ 注意事项

### 1. Token 安全

- ❌ 不要分享 Token
- ❌ 不要提交到 Git
- ✅ 定期更换 Token
- ✅ 使用最小权限

### 2. 配置文件

- ✅ 自动保存，可复用
- ✅ 权限保护（600）
- ✅ 已加入 .gitignore

### 3. 发布前检查

```bash
# 运行敏感信息检查
uv run scripts/check_secrets.py --all

# 确认没有敏感信息
✅ 未发现敏感信息
```

---

## 🔄 更新配置

### 修改用户名

```bash
# 编辑配置文件
nano config/github_config.yaml

# 修改 username 字段
github:
  username: "NEW_USERNAME"
```

### 修改仓库信息

```bash
# 编辑配置文件
nano config/github_config.yaml

# 修改 repository 字段
repository:
  name: "new-repo-name"
  description: "新描述"
```

### 重新配置

```bash
# 删除旧配置
rm config/github_config.yaml

# 重新初始化
uv run scripts/github_config.py setup
```

---

## 📞 故障排查

### 问题 1：配置未找到

**症状：**
```
⚠️  配置未初始化
```

**解决：**
```bash
uv run scripts/github_config.py setup
```

---

### 问题 2：Token 无效

**症状：**
```
❌ GitHub 连接失败：401
```

**解决：**
1. 检查 Token 是否正确
2. 重新生成 Token：https://github.com/settings/tokens
3. 更新配置：`uv run scripts/github_config.py setup`

---

### 问题 3：推送失败

**症状：**
```
❌ 推送失败：Permission denied
```

**解决：**
1. 检查 Token 权限（需要 repo 权限）
2. 检查用户名是否正确
3. 检查仓库是否存在

---

## 🎯 完整发布流程

```bash
# 1. 配置 GitHub
uv run scripts/github_config.py setup

# 2. 测试连接
uv run scripts/github_config.py test

# 3. 敏感信息检查
uv run scripts/check_secrets.py --all

# 4. 安全提交
uv run scripts/commit_with_check.py "Initial commit"

# 5. 发布到 GitHub
uv run scripts/github_config.py publish

# 6. 完成！
🌐 查看仓库：https://github.com/YOUR_USERNAME/stock-analyzer
```

---

**🦞 配置完成后，发布只需一条命令！**
