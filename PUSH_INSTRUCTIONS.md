# 🚀 GitHub 推送指南

## ⚠️ Fine-grained Token 使用说明

你的 Token 是 **Fine-grained Personal Access Token**，不能直接在 URL 中使用。

---

## 🔧 推送方法

### 方法 1：使用 Git Credential（推荐）

```bash
# 1. 配置 Git 凭证存储
git config --global credential.helper store

# 2. 设置远程仓库
git remote add origin https://github.com/liuqun-a/lq.git

# 3. 推送（会提示输入凭证）
git push -u origin main

# 4. 输入凭证时：
# Username: liuqun-a
# Password: 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
```

**凭证会保存，下次推送无需再次输入。**

---

### 方法 2：使用 SSH（推荐用于长期）

```bash
# 1. 生成 SSH Key（如果没有）
ssh-keygen -t ed25519 -C "80503830@qq.com"

# 2. 添加 SSH Key 到 GitHub
# 访问：https://github.com/settings/keys
# 复制 ~/.ssh/id_ed25519.pub 的内容

# 3. 使用 SSH 远程仓库
git remote add origin git@github.com:liuqun-a/lq.git

# 4. 推送
git push -u origin main
```

---

### 方法 3：手动推送（一次性）

```bash
# 1. 克隆仓库（如果需要）
git clone https://github.com/liuqun-a/lq.git
cd lq

# 2. 复制文件
cp -r /home/admin/.openclaw/workspace/skills/stock-analyzer/* .

# 3. 添加并提交
git add .
git commit -m "Initial commit"

# 4. 推送（输入 Token 作为密码）
git push -u origin main
```

---

## 📝 快速推送命令

**在当前目录执行：**

```bash
cd /home/admin/.openclaw/workspace/skills/stock-analyzer

# 设置远程仓库
git remote add origin https://github.com/liuqun-a/lq.git

# 推送（手动输入 Token）
git push -u origin main

# 输入密码时粘贴：
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
```

---

## 🔐 Token 安全提示

- ✅ Token 已保存在 `config/github_config.yaml`（权限 600）
- ✅ 已加入 `.gitignore`，不会提交
- ❌ 不要在命令行直接显示 Token
- ❌ 不要分享 Token

---

## 🎯 完成推送后

**仓库地址：**
```
https://github.com/liuqun-a/lq
```

**查看仓库：**
```bash
# 浏览器访问
https://github.com/liuqun-a/lq
```

---

**🦞 推送成功后，记得在 GitHub 上查看仓库！**
