import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

class WebSocketTopMenu:
    """WebSocket客户端顶部配置菜单组件"""
    
    def __init__(self, parent, config, on_save_config=None, on_connect=None, on_disconnect=None):
        """
        初始化顶部菜单
        
        Args:
            parent: 父容器
            config: 配置字典
            on_save_config: 保存配置回调函数
            on_connect: 连接回调函数
            on_disconnect: 断开连接回调函数
        """
        self.parent = parent
        self.config = config
        self.on_save_config = on_save_config
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        
        # 创建UI变量
        self.ws_host_var = tk.StringVar(value=config['websocket']['host'])
        self.ws_port_var = tk.StringVar(value=str(config['websocket']['port']))
        
        # 创建UI组件
        self.create_ui()
    
    def create_ui(self):
        """创建UI界面"""
        config_frame = ttk.LabelFrame(self.parent, text="WebSocket配置", padding=10)
        config_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        # 第一行：WebSocket服务器配置
        server_frame = ttk.Frame(config_frame)
        server_frame.pack(fill='x', pady=5)
        
        ttk.Label(server_frame, text="WebSocket服务器:").pack(side='left', padx=(0, 5))
        self.ws_host_entry = ttk.Entry(server_frame, textvariable=self.ws_host_var, width=15)
        self.ws_host_entry.pack(side='left', padx=(0, 8))
        
        ttk.Label(server_frame, text="端口:").pack(side='left', padx=(0, 5))
        self.ws_port_entry = ttk.Entry(server_frame, textvariable=self.ws_port_var, width=8)
        self.ws_port_entry.pack(side='left', padx=(0, 15))
        
        # 按钮区域
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill='x', pady=5)
        
        self.save_config_btn = ttk.Button(button_frame, text="保存配置", command=self._on_save_config)
        self.save_config_btn.pack(side='left', padx=(0, 8))
        
        self.connect_btn = ttk.Button(button_frame, text="连接", command=self._on_connect)
        self.connect_btn.pack(side='left', padx=(0, 8))
        
        self.disconnect_btn = ttk.Button(button_frame, text="断开", command=self._on_disconnect, state='normal')
        self.disconnect_btn.pack(side='left', padx=(0, 8))
        
        # 连接状态显示
        self.status_label = ttk.Label(button_frame, text="未连接", foreground="red")
        self.status_label.pack(side='right', padx=(0, 10))
    
    def _on_save_config(self):
        """保存配置回调"""
        if self.on_save_config:
            self.on_save_config()
    
    def _on_connect(self):
        """连接回调"""
        if self.on_connect:
            self.on_connect()
    
    def _on_disconnect(self):
        """断开连接回调"""
        if self.on_disconnect:
            self.on_disconnect()
    
    def get_config_values(self):
        """获取配置值"""
        return {
            'websocket': {
                'host': self.ws_host_var.get(),
                'port': int(self.ws_port_var.get())
            }
        }
    
    def set_config_editable(self, editable=True):
        """设置配置输入框的编辑状态"""
        state = 'normal' if editable else 'disabled'
        
        logger.info(f"设置配置编辑状态: {state}")
        
        # 设置所有配置输入框的状态
        self.ws_host_entry.config(state=state)
        self.ws_port_entry.config(state=state)
        
        # 设置保存配置按钮的状态
        self.save_config_btn.config(state=state)
        
        # 强制更新UI
        self.parent.update_idletasks()
        
        logger.info(f"配置编辑状态设置完成: {state}")
    
    def update_connection_status(self, is_connected, is_connecting=False):
        """更新连接状态"""
        if is_connecting:
            self.status_label.config(text="连接中...", foreground="orange")
            self.connect_btn.config(state='disabled')
            # 断开按钮在连接中时也保持可用
            self.disconnect_btn.config(state='normal')
        elif is_connected:
            self.status_label.config(text="已连接", foreground="green")
            self.connect_btn.config(state='disabled')
            # 断开按钮始终可用
            self.disconnect_btn.config(state='normal')
            
            # 连接时禁用配置编辑
            self.set_config_editable(False)
        else:
            self.status_label.config(text="未连接", foreground="red")
            self.connect_btn.config(state='normal')
            # 断开按钮始终可用
            self.disconnect_btn.config(state='normal')
            
            # 断开时启用配置编辑
            self.set_config_editable(True)
    
    def show_error_message(self, message):
        """显示错误消息"""
        messagebox.showerror("连接错误", message)
    
    def show_info_message(self, message):
        """显示信息消息"""
        messagebox.showinfo("提示", message) 