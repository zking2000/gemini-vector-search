#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行脚本，确保测试报告目录存在并正确捕获日志
"""
import os
import sys
import datetime
import subprocess
import logging

# 创建日志目录
reports_dir = os.path.join("tests", "reports")
os.makedirs(reports_dir, exist_ok=True)

# 设置当前时间戳
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = os.path.join(reports_dir, f"test_report_{timestamp}.html")
log_file = os.path.join(reports_dir, f"test_log_{timestamp}.log")

# 构建pytest命令
cmd = [
    "python", "-m", "pytest",
    "tests/test_api_complete.py",
    "-v",
    f"--html={report_file}",
    f"--log-file={log_file}",
    "--log-file-level=INFO",
    "--capture=tee-sys",  # 同时将输出发送到终端和日志文件
    "--show-capture=all"  # 捕获所有输出
]

print(f"运行测试命令: {' '.join(cmd)}")
result = subprocess.run(cmd)

print(f"测试完成，返回代码: {result.returncode}")
print(f"测试报告: {report_file}")
print(f"测试日志: {log_file}")

sys.exit(result.returncode) 