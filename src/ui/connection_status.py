import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class ConnectionStatus:
    """连接状态显示组件"""
    
    def __init__(self, parent):
        """
        初始化连接状态组件
        
        Args:
            parent: 父容器
        """
        self.parent = parent
        self.create_ui()
    
    def create_ui(self):
        """创建UI界面"""
        status_frame = ttk.LabelFrame(self.parent, text="连接状态", padding=10)
        status_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="未连接", foreground="red", font=('Microsoft YaHei', 12, 'bold'))
        self.status_label.pack(pady=(0, 10))
        
        # 连接信息
        self.connection_info = ttk.Label(status_frame, text="", font=('Microsoft YaHei', 10))
        self.connection_info.pack(pady=(0, 10))
        
        # WebSocket客户端数量
        self.ws_client_count = ttk.Label(status_frame, text="WebSocket客户端: 0", font=('Microsoft YaHei', 10))
        self.ws_client_count.pack()
    
    def update_status(self, is_connected, connection_info=None):
        """
        更新连接状态
        
        Args:
            is_connected: 是否已连接
            connection_info: 连接信息字典，包含host, port, motor_count等
        """
        if is_connected:
            self.status_label.config(text="已连接", foreground="green")
            if connection_info:
                info_text = f"主机: {connection_info.get('host', 'N/A')}:{connection_info.get('port', 'N/A')}, 电机数量: {connection_info.get('motor_count', 'N/A')}"
                self.connection_info.config(text=info_text)
        else:
            self.status_label.config(text="未连接", foreground="red")
            self.connection_info.config(text="")
    
    def update_websocket_client_count(self, count):
        """
        更新WebSocket客户端数量
        
        Args:
            count: 客户端数量
        """
        self.ws_client_count.config(text=f"WebSocket客户端: {count}")
    
    def clear_connection_info(self):
        """清除连接信息"""
        self.connection_info.config(text="") 