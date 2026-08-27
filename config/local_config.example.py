# -*- coding: utf-8 -*-
"""
本地敏感配置模板（提交到 Git 的占位版本，不包含真实凭据）

使用方法：
1. 复制本文件为 config/local_config.py（该文件已被 .gitignore 忽略，不会提交）
2. 填写你本机/虚拟机的真实 IP 与密码
3. 所有脚本会优先读取环境变量，其次读取本文件，最后使用默认占位值

也可通过环境变量覆盖：
  MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE
  VM_HOST / VM_PORT / VM_USER / VM_PASSWORD
"""

import os

# ============ MySQL 连接配置 ============
MYSQL_HOST = os.environ.get("MYSQL_HOST", "<你的MySQL地址>")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "<你的MySQL密码>")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "data")

# ============ 虚拟机 SSH 配置 ============
VM_HOST = os.environ.get("VM_HOST", "<虚拟机IP>")
VM_PORT = int(os.environ.get("VM_PORT", "22"))
VM_USER = os.environ.get("VM_USER", "root")
VM_PASSWORD = os.environ.get("VM_PASSWORD", "<SSH密码>")
