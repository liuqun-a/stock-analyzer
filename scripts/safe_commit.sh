#!/bin/bash
# 安全提交脚本 - 强制遵守规则
# 用法：./scripts/safe_commit.sh "提交信息"

set -e

MESSAGE=$1

if [ -z "$MESSAGE" ]; then
    echo "❌ 用法：./scripts/safe_commit.sh \"提交信息\""
    echo ""
    echo "示例:"
    echo "  ./scripts/safe_commit.sh \"fix: 修复 ETF 价格错误\""
    echo "  ./scripts/safe_commit.sh \"feat: 添加新功能\""
    exit 1
fi

echo "============================================================"
echo "🔍 股票分析 Skill - 安全提交"
echo "============================================================"
echo ""

# 🔴 步骤 1: 敏感信息检查
echo "📋 步骤 1: 敏感信息检查"
echo "------------------------------------------------------------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! uv run python3 "$SCRIPT_DIR/check_secrets.py" --all 2>&1; then
    echo ""
    echo "============================================================"
    echo "🚨 敏感信息检查失败！"
    echo "============================================================"
    echo ""
    echo "⚠️  提交被阻止，原因：文件中包含敏感信息"
    echo ""
    echo "📝 请处理后再提交"
    echo "============================================================"
    exit 1
fi

echo "✅ 敏感信息检查通过"
echo ""

# 🔴 步骤 2: 显示提交内容
echo "📋 步骤 2: 当前变更"
echo "------------------------------------------------------------"
git status --short
echo ""

# 🔴 步骤 3: 强制确认
echo "============================================================"
echo "⚠️  提交前确认"
echo "============================================================"
echo ""
echo "提交信息：$MESSAGE"
echo ""
echo "规则："
echo "  ✅ 已通过敏感信息检查"
echo "  ✅ 新 Skill 使用独立仓库"
echo "  ✅ 仓库名已确认"
echo ""
read -p "确认提交？(y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "❌ 提交已取消"
    exit 1
fi

echo ""

# 🔴 步骤 4: 执行提交
echo "📋 步骤 4: 执行提交"
echo "------------------------------------------------------------"

git add .
git commit -m "$MESSAGE"

if [ $? -eq 0 ]; then
    echo "✅ 提交成功"
    echo ""
    
    # 🔴 步骤 5: 询问是否推送
    echo "============================================================"
    read -p "是否立即推送？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "📋 推送中..."
        git push
        
        if [ $? -eq 0 ]; then
            echo "✅ 推送成功"
        else
            echo "❌ 推送失败"
            exit 1
        fi
    else
        echo ""
        echo "💡 提示：稍后可以手动 git push"
    fi
else
    echo "❌ 提交失败"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ 提交流程完成"
echo "============================================================"
