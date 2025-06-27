import asyncio
import threading
import time
import json
import os
from websocket_client import WebSocketClient
from ui.motor_monitor_ui import MotorMonitorUI

class WebSocketClientWithUI:
    def __init__(self, server_url="ws://localhost:8765"):
        # 初始化WebSocket客户端
        self.websocket_client = WebSocketClient(server_url)
        
        # 初始化UI
        self.ui = MotorMonitorUI(title="WebSocket电机监控系统", data_provider=self.websocket_client)
        
        # 启动WebSocket客户端
        self.start_websocket_client()
        
    def start_websocket_client(self):
        """启动WebSocket客户端"""
        try:
            # 在新线程中启动WebSocket客户端
            websocket_thread = threading.Thread(
                target=self._run_websocket_client,
                daemon=True
            )
            websocket_thread.start()
            print(f"WebSocket客户端已启动，连接到: {self.websocket_client.server_url}")
        except Exception as e:
            print(f"启动WebSocket客户端失败: {str(e)}")
    
    def _run_websocket_client(self):
        """在新线程中运行WebSocket客户端"""
        try:
            asyncio.run(self.websocket_client.run())
        except Exception as e:
            print(f"WebSocket客户端运行错误: {str(e)}")
    
    def run(self):
        """运行程序"""
        try:
            self.ui.run()
        finally:
            # 清理资源
            if self.websocket_client:
                asyncio.run(self.websocket_client.disconnect())

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket电机监控客户端')
    parser.add_argument('--server', default='ws://localhost:8765', help='WebSocket服务器地址')
    
    args = parser.parse_args()
    
    app = WebSocketClientWithUI(args.server)
    app.run()

if __name__ == "__main__":
    main() 