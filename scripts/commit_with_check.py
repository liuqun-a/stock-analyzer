#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全提交脚本
检查敏感信息并要求用户确认后才能提交 Git

使用方法：
    uv run scripts/commit_with_check.py "提交信息"
"""

import subprocess
import sys
from pathlib import Path
from check_secrets import SecretChecker


def get_staged_files():
    """获取暂存区文件列表"""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ 获取暂存区文件失败")
        return []
    
    files = result.stdout.strip().split('\n')
    return [f for f in files if f]


def check_secrets(files):
    """检查敏感信息"""
    checker = SecretChecker(verbose=False)
    all_findings = []
    
    for filepath in files:
        findings = checker.check_file(Path(filepath))
        if findings:
            all_findings.append((Path(filepath), findings))
    
    return all_findings


def print_findings(all_findings):
    """打印检查结果"""
    if not all_findings:
        print("✅ 敏感信息检查通过")
        return True
    
    print("\n🚨 发现潜在敏感信息：\n")
    
    for filepath, findings in all_findings:
        print(f"📁 {filepath}")
        for line_num, desc, matched in findings:
            if len(matched) > 20:
                masked = matched[:8] + "..." + matched[-8:]
            else:
                masked = matched
            print(f"   行 {line_num}: {desc}")
            print(f"   匹配：{masked}")
        print()
    
    return False


def confirm_commit():
    """要求用户确认"""
    print("\n" + "=" * 60)
    print("⚠️  提交前确认")
    print("=" * 60)
    print()
    print("请确认以下信息：")
    print("  1. ✅ 已检查敏感信息")
    print("  2. ✅ 已移除 API Key、密码等敏感信息")
    print("  3. ✅ 配置文件已添加到 .gitignore")
    print()
    
    response = input("确认提交？(y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        return True
    else:
        print("\n❌ 提交已取消")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法：uv run scripts/commit_with_check.py \"提交信息\"")
        sys.exit(1)
    
    commit_message = ' '.join(sys.argv[1:])
    
    # 获取暂存区文件
    print("🔍 获取暂存区文件...")
    files = get_staged_files()
    
    if not files:
        print("❌ 没有暂存的文件，请先 git add")
        sys.exit(1)
    
    print(f"📋 待提交文件：{len(files)} 个")
    
    # 检查敏感信息
    print("\n🔍 检查敏感信息...")
    findings = check_secrets(files)
    
    if not print_findings(findings):
        # 发现敏感信息
        print("\n" + "=" * 60)
        print("🚨 提交被阻止")
        print("=" * 60)
        print()
        print("发现敏感信息，请处理后再提交：")
        print("  1. 移除或替换敏感信息")
        print("  2. 重新添加文件：git add <file>")
        print("  3. 重新运行：uv run scripts/commit_with_check.py \"提交信息\"")
        print()
        
        # 询问是否强制提交
        response = input("\n⚠️  是否强制提交？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("\n❌ 提交已取消")
            sys.exit(1)
        # 如果强制提交，继续执行
    
    # 要求确认
    if not confirm_commit():
        sys.exit(0)
    
    # 执行提交
    print("\n📝 执行提交...")
    result = subprocess.run(
        ['git', 'commit', '-m', commit_message],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✅ 提交成功！")
        print(result.stdout)
    else:
        print("\n❌ 提交失败")
        print(result.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
