import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from modbus_client import ModbusClient
from ui.motor_monitor_ui import MotorMonitorUI

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return (
            config['modbus']['host'],
            config['modbus']['port'],
            config['modbus']['motor_count'],
            bool(config['auto_update']['enabled']),
            config['auto_update']['interval']
        )
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return "localhost", 5020, 12, False, 1

class ModbusClientWithUI:
    def __init__(self):
        # 从配置文件加载设置
        host, port, motor_count, auto_update_enabled, update_interval = load_config()
        
        # 初始化Modbus客户端
        self.modbus_client = ModbusClient(host, port, motor_count)
        
        # 初始化UI
        self.ui = MotorMonitorUI(title="Modbus电机监控系统", data_provider=self.modbus_client)
        
        # 设置自动更新
        if auto_update_enabled:
            self.ui.update_interval = update_interval
        
        # 初始化连接
        self.initialize_connection()
        
        # 启动WebSocket服务器
        self.start_websocket_server()

    def initialize_connection(self):
        """初始化连接"""
        try:
            if self.modbus_client.connect():
                self.ui.update_connection_status("已连接到Modbus服务器")
                # 如果配置中启用了自动更新，则启动后自动开始更新
                if hasattr(self, 'auto_update_enabled') and self.auto_update_enabled:
                    # 延迟一秒后开始自动更新，确保UI完全加载
                    self.ui.root.after(1000, self.ui.start_auto_update)
            else:
                self.ui.update_connection_status("无法连接到Modbus服务器")
                messagebox.showerror("连接错误", "无法连接到Modbus服务器")
        except Exception as e:
            self.ui.update_connection_status(f"连接错误: {str(e)}")
            messagebox.showerror("连接错误", f"连接失败: {str(e)}")

    def start_websocket_server(self):
        """启动WebSocket服务器"""
        try:
            # 在新线程中启动WebSocket服务器
            websocket_thread = threading.Thread(
                target=self.modbus_client.start_websocket_server,
                args=('0.0.0.0', 8765),
                daemon=True
            )
            websocket_thread.start()
            print("WebSocket服务器已启动: ws://0.0.0.0:8765")
        except Exception as e:
            print(f"启动WebSocket服务器失败: {str(e)}")

    def run(self):
        """运行程序"""
        try:
            self.ui.run()
        finally:
            # 清理资源
            if self.modbus_client:
                self.modbus_client.disconnect()

def main():
    app = ModbusClientWithUI()
    app.run()

if __name__ == "__main__":
    main() 