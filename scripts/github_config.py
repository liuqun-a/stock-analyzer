#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 配置管理工具
保存和管理 GitHub 账号、仓库信息

使用方法：
    uv run scripts/github_config.py setup      # 初始化配置
    uv run scripts/github_config.py show       # 查看配置
    uv run scripts/github_config.py test       # 测试连接
    uv run scripts/github_config.py publish    # 发布到 GitHub
"""

import yaml
import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Dict


class GitHubConfig:
    """GitHub 配置管理器"""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "config" / "github_config.yaml"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_file.exists():
            return {}
        
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def save_config(self, config: Dict):
        """保存配置文件"""
        self.config_file.parent.mkdir(exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        # 设置文件权限
        os.chmod(self.config_file, 0o600)
        print(f"✅ 配置已保存：{self.config_file}")
    
    def setup_interactive(self):
        """交互式配置"""
        print("=" * 60)
        print("🔧 GitHub 配置向导")
        print("=" * 60)
        print()
        
        config = {}
        
        # GitHub 账号
        print("📛 GitHub 账号信息")
        print("-" * 60)
        config['github'] = {}
        
        # 用户名
        username = input("GitHub 用户名：").strip()
        if not username:
            print("❌ 用户名不能为空")
            return False
        config['github']['username'] = username
        
        # 邮箱
        email = input("GitHub 邮箱：").strip()
        if not email:
            print("❌ 邮箱不能为空")
            return False
        config['github']['email'] = email
        
        # Token
        print()
        print("🔑 GitHub Token 配置")
        print("-" * 60)
        print("生成 Token：https://github.com/settings/tokens")
        print("需要的权限：repo, workflow")
        print()
        token = input("GitHub Token：").strip()
        if not token:
            print("⚠️  Token 为空，后续推送可能需要手动输入密码")
        config['github']['token'] = token
        
        # 仓库配置
        print()
        print("📦 仓库配置")
        print("-" * 60)
        config['repository'] = {}
        
        # 仓库名
        repo_name = input("仓库名称：").strip()
        if not repo_name:
            repo_name = "stock-analyzer"
        config['repository']['name'] = repo_name
        
        # 描述
        description = input("仓库描述：").strip()
        if not description:
            description = "A 股/港股智能分析系统"
        config['repository']['description'] = description
        
        # 可见性
        visibility = input("可见性 (public/private) [public]: ").strip().lower()
        if visibility not in ['public', 'private']:
            visibility = 'public'
        config['repository']['visibility'] = visibility
        
        # 许可证
        license_type = input("许可证 (MIT/Apache-2.0/GPL-3.0) [MIT]: ").strip()
        if not license_type:
            license_type = 'MIT'
        config['repository']['license'] = license_type
        
        # 主题标签
        print()
        print("🏷️  主题标签（逗号分隔）")
        topics_input = input("例如：stock,python,openclaw [stock,python,ai]: ").strip()
        if not topics_input:
            topics_input = "stock,python,openclaw,ai,quant"
        config['repository']['topics'] = [t.strip() for t in topics_input.split(',')]
        
        # Git 配置
        config['git'] = {
            'default_branch': 'main',
            'remote_name': 'origin'
        }
        
        # 发布配置
        config['publish'] = {
            'auto_release': False,
            'auto_push': True,
            'pre_commit_check': True
        }
        
        # 保存配置
        print()
        print("=" * 60)
        save = input("保存配置？(y/N): ").strip().lower()
        if save in ['y', 'yes']:
            self.save_config(config)
            print()
            print("✅ 配置已保存！")
            print()
            print("下次使用：uv run scripts/github_config.py show")
            print("发布仓库：uv run scripts/github_config.py publish")
            return True
        else:
            print()
            print("❌ 配置已取消")
            return False
    
    def show_config(self):
        """显示当前配置"""
        if not self.config:
            print("⚠️  配置未初始化")
            print()
            print("运行以下命令初始化：")
            print("  uv run scripts/github_config.py setup")
            return False
        
        print("=" * 60)
        print("📋 GitHub 配置")
        print("=" * 60)
        print()
        
        # GitHub 账号
        github = self.config.get('github', {})
        print("📛 GitHub 账号")
        print(f"  用户名：{github.get('username', '未配置')}")
        print(f"  邮箱：{github.get('email', '未配置')}")
        print(f"  Token: {'已配置' if github.get('token') else '未配置'}")
        print()
        
        # 仓库配置
        repo = self.config.get('repository', {})
        print("📦 仓库配置")
        print(f"  名称：{repo.get('name', '未配置')}")
        print(f"  描述：{repo.get('description', '未配置')}")
        print(f"  可见性：{repo.get('visibility', 'public')}")
        print(f"  许可证：{repo.get('license', 'MIT')}")
        print(f"  主题：{', '.join(repo.get('topics', []))}")
        print()
        
        # Git 配置
        git = self.config.get('git', {})
        print("🔧 Git 配置")
        print(f"  默认分支：{git.get('default_branch', 'main')}")
        print(f"  远程名称：{git.get('remote_name', 'origin')}")
        print()
        
        # 远程 URL
        if github.get('username') and repo.get('name'):
            remote_url = f"https://github.com/{github['username']}/{repo['name']}.git"
            print(f"🌐 远程仓库：{remote_url}")
        
        print()
        print("=" * 60)
        return True
    
    def test_connection(self):
        """测试 GitHub 连接"""
        print("🔍 测试 GitHub 连接...")
        print()
        
        github = self.config.get('github', {})
        token = github.get('token')
        username = github.get('username')
        
        if not username:
            print("❌ 用户名未配置")
            return False
        
        if not token:
            print("⚠️  Token 未配置，使用 HTTPS 测试")
            # 测试基本连接
            result = subprocess.run(
                ['git', 'ls-remote', f'https://github.com/{username}'],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ GitHub 连接正常（用户：{username}）")
                return True
            else:
                print(f"❌ GitHub 连接失败")
                return False
        
        # 使用 Token 测试
        import requests
        
        url = "https://api.github.com/user"
        
        # 尝试两种认证方式（兼容 classic 和 fine-grained token）
        if token.startswith('github_pat_'):
            # Fine-grained Personal Access Token
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            }
        else:
            # Classic Personal Access Token
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                user_data = resp.json()
                print(f"✅ GitHub 连接正常")
                print(f"   用户：{user_data.get('login')}")
                print(f"   邮箱：{user_data.get('email')}")
                return True
            else:
                print(f"❌ GitHub 连接失败：{resp.status_code}")
                print(f"   请检查 Token 是否正确")
                return False
        except Exception as e:
            print(f"❌ 连接异常：{e}")
            return False
    
    def get_remote_url(self) -> str:
        """获取远程仓库 URL"""
        github = self.config.get('github', {})
        repo = self.config.get('repository', {})
        
        username = github.get('username', '')
        repo_name = repo.get('name', '')
        token = github.get('token', '')
        
        if token:
            # 使用 Token 的 URL（用于推送）
            return f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        else:
            # 普通 HTTPS URL
            return f"https://github.com/{username}/{repo_name}.git"
    
    def publish(self):
        """发布到 GitHub"""
        print("=" * 60)
        print("🚀 发布到 GitHub")
        print("=" * 60)
        print()
        
        # 检查配置
        if not self.config:
            print("❌ 配置未初始化")
            print()
            print("运行以下命令初始化：")
            print("  uv run scripts/github_config.py setup")
            return False
        
        # 测试连接
        print("1️⃣  测试 GitHub 连接...")
        if not self.test_connection():
            print()
            print("⚠️  GitHub 连接失败，请检查配置")
            return False
        print()
        
        # 检查 Git 仓库
        print("2️⃣  检查 Git 仓库...")
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True)
        if result.returncode != 0:
            print("❌ 当前目录不是 Git 仓库")
            print()
            print("初始化 Git：")
            print("  git init")
            print("  git add .")
            print("  git commit -m 'Initial commit'")
            return False
        print("✅ Git 仓库正常")
        print()
        
        # 获取远程 URL
        remote_url = self.get_remote_url()
        print(f"3️⃣  远程仓库：{remote_url}")
        print()
        
        # 确认发布
        print("=" * 60)
        print("⚠️  发布确认")
        print("=" * 60)
        print()
        print("即将执行以下操作：")
        print(f"  1. 添加远程仓库：{remote_url}")
        print(f"  2. 推送到 GitHub")
        print()
        
        confirm = input("确认发布？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print()
            print("❌ 发布已取消")
            return False
        
        # 添加远程仓库
        print()
        print("📝 添加远程仓库...")
        git_config = self.config.get('git', {})
        remote_name = git_config.get('remote_name', 'origin')
        
        result = subprocess.run(
            ['git', 'remote', 'add', remote_name, remote_url],
            capture_output=True
        )
        if result.returncode != 0 and 'already exists' not in result.stderr.decode():
            print(f"❌ 添加远程仓库失败：{result.stderr.decode()}")
            return False
        print(f"✅ 远程仓库已添加：{remote_name}")
        print()
        
        # 推送
        print("🚀 推送到 GitHub...")
        default_branch = git_config.get('default_branch', 'main')
        
        result = subprocess.run(
            ['git', 'push', '-u', remote_name, default_branch],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ 推送成功！")
            print()
            repo = self.config.get('repository', {})
            repo_url = f"https://github.com/{self.config['github']['username']}/{repo['name']}"
            print(f"🌐 查看仓库：{repo_url}")
            return True
        else:
            print(f"❌ 推送失败：{result.stderr.decode()}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub 配置管理工具')
    parser.add_argument('command', choices=['setup', 'show', 'test', 'publish'],
                       help='命令：setup(初始化), show(查看), test(测试), publish(发布)')
    
    args = parser.parse_args()
    
    config = GitHubConfig()
    
    if args.command == 'setup':
        success = config.setup_interactive()
    elif args.command == 'show':
        success = config.show_config()
    elif args.command == 'test':
        success = config.test_connection()
    elif args.command == 'publish':
        success = config.publish()
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
