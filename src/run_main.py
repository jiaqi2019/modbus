#!/usr/bin/env python3
"""
电机监控系统主程序启动脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行主程序
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modbus-client'))
from main import main

if __name__ == "__main__":
    main() 