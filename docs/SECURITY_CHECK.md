# 🔐 敏感信息检查工具

## 📋 功能说明

在 Git 提交前自动检查代码中是否包含敏感信息：

- ✅ API Keys（阿里云、GitHub、AWS 等）
- ✅ 飞书配置（AppID、AppSecret、用户 ID）
- ✅ 密码/密钥
- ✅ 数据库连接字符串
- ✅ 私钥文件
- ✅ JWT Tokens

---

## 🚀 使用方法

### 方法 1：使用安全提交脚本（推荐）

```bash
# 替代 git commit，自动检查并要求确认
uv run scripts/commit_with_check.py "提交信息"
```

**流程：**
1. 自动检查暂存区文件
2. 发现敏感信息时阻止提交
3. 要求用户确认后才能提交

---

### 方法 2：手动检查

```bash
# 检查指定文件
uv run scripts/check_secrets.py scripts/feishu_push.py

# 检查整个目录
uv run scripts/check_secrets.py --all

# 输出 JSON 报告
uv run scripts/check_secrets.py --all --json
```

---

### 方法 3：Git Pre-commit Hook（自动）

**安装 Hook：**

```bash
# 复制 hook 到 .git/hooks
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**效果：**
- 每次 `git commit` 时自动检查
- 发现敏感信息自动阻止提交

---

## 📊 检查规则

### 检测的敏感信息类型

| 类型 | 示例 | 检测规则 |
|-----|------|---------|
| **API Keys** | `sk-xxxxxxxx` | 阿里云、Google 等 |
| **飞书配置** | `cli_xxxxx` | AppID、用户 ID |
| **GitHub Token** | `ghp_xxxxx` | Personal Access Token |
| **AWS Key** | `AKIAxxxxx` | Access Key ID |
| **密码** | `password=xxx` | 硬编码密码 |
| **数据库** | `mongodb://xxx` | 连接字符串 |
| **私钥** | `BEGIN PRIVATE KEY` | RSA/DSA 私钥 |
| **JWT** | `eyJxxxx.eyJxxx` | JWT Tokens |

### 白名单规则

以下情况不会被标记：

- `example.com`
- `your_username` / `YOUR_USERNAME`
- `xxx+` / `***`
- `<placeholder>`
- `{{变量}}`（模板变量）

---

## 🔧 配置白名单

如果某些匹配是误报，可以添加到白名单：

**编辑：** `scripts/check_secrets.py`

```python
# 白名单（允许的模式）
WHITELIST_PATTERNS = [
    r'example\.com',
    r'your[_-]?username',
    r'YOUR[_-]?USERNAME',
    # 添加新的白名单规则
    r'你的规则',
]
```

---

## 📝 提交流程

### 标准流程

```bash
# 1. 添加文件
git add .

# 2. 安全检查
uv run scripts/check_secrets.py --all

# 3. 如果没有问题，确认提交
uv run scripts/commit_with_check.py "提交信息"

# 4. 推送
git push
```

### 自动流程（使用 Hook）

```bash
# 1. 添加文件
git add .

# 2. 提交（自动检查）
git commit -m "提交信息"

# 3. 如果检查失败，根据提示修复
# 4. 推送
git push
```

---

## 🚨 发现敏感信息怎么办？

### 1. 移除敏感信息

```python
# ❌ 错误：硬编码
API_KEY = "sk-xxxxxxxx"

# ✅ 正确：从环境变量读取
API_KEY = os.getenv("API_KEY")
```

### 2. 使用配置文件

```yaml
# config/secrets.yaml（不提交到 Git）
api_key: "sk-xxxxxxxx"
```

```python
# 从配置文件读取
import yaml
with open('config/secrets.yaml') as f:
    config = yaml.safe_load(f)
    api_key = config['api_key']
```

### 3. 添加到 .gitignore

```bash
# .gitignore
config/secrets.yaml
*.key
*.pem
.env
```

---

## 📊 检查报告示例

```bash
$ uv run scripts/check_secrets.py --all

🚨 发现 2 个潜在敏感信息，分布在 1 个文件中：

📁 scripts/feishu_push.py
   行 15: 飞书用户 ID
   匹配：ou_b6766...06877683
   行 20: 阿里云 API Key
   匹配：sk-sp-38...9c7f

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  提交被阻止

请执行以下操作：
  1. 检查上述文件中的敏感信息
  2. 移除或替换敏感信息
  3. 重新添加文件：git add <file>
  4. 重新提交：git commit
```

---

## ⚠️ 注意事项

### 必须检查的文件

- ✅ 所有 Python 脚本
- ✅ 配置文件（.yaml, .json）
- ✅ 文档文件（.md）
- ✅ Shell 脚本

### 自动跳过的文件

- ❌ `.git/` 目录
- ❌ `.venv/` 虚拟环境
- ❌ `__pycache__/` 缓存
- ❌ 二进制文件（.so, .dll）

---

## 🎯 最佳实践

### 1. 使用环境变量

```python
# ✅ 推荐
import os
API_KEY = os.getenv("API_KEY")
```

### 2. 使用配置管理

```python
# ✅ 推荐
from pathlib import Path
import json

config_file = Path.home() / ".openclaw" / "openclaw.json"
with open(config_file) as f:
    config = json.load(f)
    api_key = config['api_key']
```

### 3. 提供配置模板

```yaml
# config/api_keys.yaml.example（提交到 Git）
# 复制为 api_keys.yaml 并填入真实值
api_key: "your-api-key-here"
```

### 4. 定期更新检查规则

```bash
# 更新 check_secrets.py 中的检测规则
git pull origin main
```

---

## 📞 故障排查

### 问题 1：误报

**症状：** 正常代码被标记为敏感信息

**解决：** 添加到白名单
```python
WHITELIST_PATTERNS.append(r'你的规则')
```

### 问题 2：漏报

**症状：** 敏感信息未被检测到

**解决：** 添加新的检测规则
```python
SECRET_PATTERNS.append((r'新规则', '描述'))
```

### 问题 3：Hook 不工作

**症状：** git commit 时没有自动检查

**解决：**
```bash
# 检查 hook 权限
chmod +x .git/hooks/pre-commit

# 检查 hook 路径
ls -la .git/hooks/pre-commit
```

---

## 🔗 相关文档

- [Git 发布检查清单](PUBLISH_CHECKLIST.md)
- [.gitignore 配置](../.gitignore)
- [敏感信息迁移方案](../docs/)

---

**🦞 安全第一，提交前务必检查！**
