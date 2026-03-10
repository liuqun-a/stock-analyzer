#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感信息检查脚本
用于 Git 提交前检查代码中是否包含敏感信息

使用方法：
    uv run scripts/check_secrets.py [file1] [file2] ...
    uv run scripts/check_secrets.py --all  # 检查所有文件
"""

import re
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional


# 敏感信息检测规则
SECRET_PATTERNS = [
    # API Keys
    (r'sk-[a-zA-Z0-9]{32,}', '阿里云 DashScope API Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
    (r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}', 'Slack Token'),
    
    # 飞书配置
    (r'cli_[a-zA-Z0-9]{16}', '飞书 App ID'),
    (r'ou_[a-zA-Z0-9]{32}', '飞书用户 ID'),
    
    # 密钥/密码
    (r'[A-Za-z0-9+/]{40,}={0,2}', 'Base64 编码的密钥'),
    (r'password\s*[:=]\s*["\'][^"\']+["\']', '硬编码密码'),
    (r'passwd\s*[:=]\s*["\'][^"\']+["\']', '硬编码密码'),
    (r'secret\s*[:=]\s*["\'][^"\']+["\']', '硬编码密钥'),
    
    # 数据库连接
    (r'mongodb(\+srv)?://[^"\s]+', 'MongoDB 连接字符串'),
    (r'postgres(ql)?://[^"\s]+', 'PostgreSQL 连接字符串'),
    (r'mysql://[^"\s]+', 'MySQL 连接字符串'),
    
    # 云服务
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'AIza[0-9A-Za-z\-_]{35}', 'Google API Key'),
    
    # 私钥
    (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', '私钥文件'),
    
    # JWT Token
    (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', 'JWT Token'),
]

# 白名单（允许的模式）
WHITELIST_PATTERNS = [
    r'example\.com',
    r'your[_-]?username',
    r'YOUR[_-]?USERNAME',
    r'your[_-]?token',
    r'YOUR[_-]?TOKEN',
    r'xxx+',
    r'\*+',
    r'<placeholder>',
    r'\{\{.*\}\}',  # 模板变量
    r'openclaw.*searxng',  # 本地路径
    r'cn/funds.*code',  # 基金代码 URL
    r'mysql://',  # 正则表达式中的 MySQL 模式
]


class SecretChecker:
    """敏感信息检查器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in SECRET_PATTERNS
        ]
        self.whitelist_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in WHITELIST_PATTERNS
        ]
    
    def is_whitelisted(self, line: str, match: str) -> bool:
        """检查是否在白名单中"""
        for pattern in self.whitelist_patterns:
            if pattern.search(line) or pattern.search(match):
                return True
        return False
    
    def check_line(self, line: str, line_num: int) -> List[Tuple[int, str, str]]:
        """检查单行是否包含敏感信息"""
        findings = []
        
        for pattern, description in self.compiled_patterns:
            matches = pattern.finditer(line)
            for match in matches:
                matched_text = match.group()
                
                # 检查白名单
                if self.is_whitelisted(line, matched_text):
                    continue
                
                findings.append((line_num, description, matched_text))
        
        return findings
    
    def check_file(self, filepath: Path) -> List[Tuple[int, str, str]]:
        """检查单个文件"""
        findings = []
        
        try:
            # 跳过二进制文件
            if filepath.suffix in ['.pyc', '.so', '.dll', '.exe']:
                return findings
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_findings = self.check_line(line, line_num)
                    findings.extend(line_findings)
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  读取文件失败 {filepath}: {e}")
        
        return findings
    
    def check_directory(self, dirpath: Path, exclude_dirs: List[str] = None) -> List[Tuple[Path, List[Tuple[int, str, str]]]]:
        """检查目录中的所有文件"""
        if exclude_dirs is None:
            exclude_dirs = ['.git', '.venv', 'venv', 'node_modules', '__pycache__', '.openclaw']
        
        all_findings = []
        
        for filepath in dirpath.rglob('*'):
            # 跳过排除的目录
            if any(exclude in str(filepath) for exclude in exclude_dirs):
                continue
            
            # 只检查代码和文档文件
            if filepath.is_file() and filepath.suffix in [
                '.py', '.md', '.txt', '.yaml', '.yml', '.json',
                '.js', '.ts', '.sh', '.bash', '.zsh',
                '.toml', '.ini', '.cfg', '.conf'
            ]:
                findings = self.check_file(filepath)
                if findings:
                    all_findings.append((filepath, findings))
        
        return all_findings
    
    def print_findings(self, all_findings: List[Tuple[Path, List[Tuple[int, str, str]]]]):
        """打印检查结果"""
        if not all_findings:
            print("✅ 未发现敏感信息")
            return
        
        total_files = len(all_findings)
        total_findings = sum(len(findings) for _, findings in all_findings)
        
        print(f"\n🚨 发现 {total_findings} 个潜在敏感信息，分布在 {total_files} 个文件中：\n")
        
        for filepath, findings in all_findings:
            print(f"📁 {filepath}")
            for line_num, desc, matched in findings:
                # 隐藏敏感信息（只显示前后部分）
                if len(matched) > 20:
                    masked = matched[:8] + "..." + matched[-8:]
                else:
                    masked = matched
                
                print(f"   行 {line_num}: {desc}")
                print(f"   匹配：{masked}")
            print()
    
    def generate_report(self, all_findings: List[Tuple[Path, List[Tuple[int, str, str]]]]) -> dict:
        """生成检查报告"""
        report = {
            'total_files': len(all_findings),
            'total_findings': sum(len(findings) for _, findings in all_findings),
            'files': []
        }
        
        for filepath, findings in all_findings:
            file_report = {
                'path': str(filepath),
                'findings': [
                    {'line': line_num, 'type': desc, 'matched': matched}
                    for line_num, desc, matched in findings
                ]
            }
            report['files'].append(file_report)
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='敏感信息检查工具')
    parser.add_argument('files', nargs='*', help='要检查的文件')
    parser.add_argument('--all', action='store_true', help='检查当前目录所有文件')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式报告')
    parser.add_argument('--quiet', action='store_true', help='静默模式（只返回状态码）')
    
    args = parser.parse_args()
    
    checker = SecretChecker(verbose=not args.quiet)
    
    all_findings = []
    
    if args.all:
        # 检查当前目录
        all_findings = checker.check_directory(Path('.'))
    elif args.files:
        # 检查指定文件
        for filepath in args.files:
            findings = checker.check_file(Path(filepath))
            if findings:
                all_findings.append((Path(filepath), findings))
    else:
        # 默认检查 scripts/ 目录
        scripts_dir = Path(__file__).parent
        all_findings = checker.check_directory(scripts_dir)
    
    # 输出结果
    if args.json:
        report = checker.generate_report(all_findings)
        print(json.dumps(report, indent=2))
    else:
        if not args.quiet:
            checker.print_findings(all_findings)
    
    # 返回状态码
    if all_findings:
        sys.exit(1)  # 发现敏感信息
    else:
        sys.exit(0)  # 安全


if __name__ == '__main__':
    main()
