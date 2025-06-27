#!/usr/bin/env python3
"""
WebSocket电机监控客户端启动脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行WebSocket客户端
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'websocket-client'))
from main import main

if __name__ == '__main__':
    main() 