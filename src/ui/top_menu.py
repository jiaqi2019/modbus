import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

class TopMenu:
    """顶部配置菜单组件"""
    
    def __init__(self, parent, config, on_save_config=None, on_connect=None, on_disconnect=None, on_start_monitor=None, on_stop_monitor=None):
        """
        初始化顶部菜单
        
        Args:
            parent: 父容器
            config: 配置字典
            on_save_config: 保存配置回调函数
            on_connect: 连接回调函数
            on_disconnect: 断开连接回调函数
            on_start_monitor: 开始监控回调函数
            on_stop_monitor: 停止监控回调函数
        """
        self.parent = parent
        self.config = config
        self.on_save_config = on_save_config
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_start_monitor = on_start_monitor
        self.on_stop_monitor = on_stop_monitor
        
        # 创建UI变量
        self.host_var = tk.StringVar(value=config['modbus']['host'])
        self.port_var = tk.StringVar(value=str(config['modbus']['port']))
        self.motor_count_var = tk.StringVar(value=str(config['modbus']['motor_count']))
        self.interval_var = tk.StringVar(value=str(config['auto_update']['interval']))
        self.ws_host_var = tk.StringVar(value=config['websocket']['host'])
        self.ws_port_var = tk.StringVar(value=str(config['websocket']['port']))
        
        # 创建UI组件
        self.create_ui()
    
    def create_ui(self):
        """创建UI界面"""
        config_frame = ttk.LabelFrame(self.parent, text="配置菜单", padding=10)
        config_frame.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # 第一行：Modbus配置和更新配置
        config_frame_inner = ttk.Frame(config_frame)
        config_frame_inner.pack(fill='x', pady=5)
        
        ttk.Label(config_frame_inner, text="Modbus服务器:").pack(side='left', padx=(0, 5))
        self.host_entry = ttk.Entry(config_frame_inner, textvariable=self.host_var, width=12)
        self.host_entry.pack(side='left', padx=(0, 8))
        
        ttk.Label(config_frame_inner, text="端口:").pack(side='left', padx=(0, 5))
        self.port_entry = ttk.Entry(config_frame_inner, textvariable=self.port_var, width=6)
        self.port_entry.pack(side='left', padx=(0, 8))
        
        ttk.Label(config_frame_inner, text="电机数量:").pack(side='left', padx=(0, 5))
        self.motor_count_entry = ttk.Entry(config_frame_inner, textvariable=self.motor_count_var, width=6)
        self.motor_count_entry.pack(side='left', padx=(0, 15))
        
        ttk.Label(config_frame_inner, text="更新间隔(秒):").pack(side='left', padx=(0, 5))
        self.interval_entry = ttk.Entry(config_frame_inner, textvariable=self.interval_var, width=6)
        self.interval_entry.pack(side='left', padx=(0, 15))
        
        # 第二行：WebSocket配置
        ws_frame = ttk.Frame(config_frame)
        ws_frame.pack(fill='x', pady=5)
        
        ttk.Label(ws_frame, text="WebSocket服务器:").pack(side='left', padx=(0, 5))
        self.ws_host_entry = ttk.Entry(ws_frame, textvariable=self.ws_host_var, width=12)
        self.ws_host_entry.pack(side='left', padx=(0, 8))
        
        ttk.Label(ws_frame, text="端口:").pack(side='left', padx=(0, 5))
        self.ws_port_entry = ttk.Entry(ws_frame, textvariable=self.ws_port_var, width=6)
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
        
        self.start_monitor_btn = ttk.Button(button_frame, text="开始监控", command=self._on_start_monitor, state='disabled')
        self.start_monitor_btn.pack(side='left', padx=(0, 8))
        
        self.stop_monitor_btn = ttk.Button(button_frame, text="停止监控", command=self._on_stop_monitor, state='disabled')
        self.stop_monitor_btn.pack(side='left')
    
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
    
    def _on_start_monitor(self):
        """开始监控回调"""
        if self.on_start_monitor:
            self.on_start_monitor()
    
    def _on_stop_monitor(self):
        """停止监控回调"""
        if self.on_stop_monitor:
            self.on_stop_monitor()
    
    def get_config_values(self):
        """获取配置值"""
        return {
            'modbus': {
                'host': self.host_var.get(),
                'port': int(self.port_var.get()),
                'motor_count': int(self.motor_count_var.get())
            },
            'auto_update': {
                'interval': int(self.interval_var.get())
            },
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
        self.host_entry.config(state=state)
        self.port_entry.config(state=state)
        self.motor_count_entry.config(state=state)
        self.interval_entry.config(state=state)
        self.ws_host_entry.config(state=state)
        self.ws_port_entry.config(state=state)
        
        # 设置保存配置按钮的状态
        self.save_config_btn.config(state=state)
        
        # 强制更新UI
        self.parent.update_idletasks()
        
        logger.info(f"配置编辑状态设置完成: {state}")
    
    def update_connection_status(self, is_connected, is_monitoring=False):
        """更新连接状态"""
        if is_connected:
            self.connect_btn.config(state='disabled')
            # 断开按钮始终可用
            self.disconnect_btn.config(state='normal')
            self.start_monitor_btn.config(state='normal')
            
            # 连接时禁用配置编辑
            self.set_config_editable(False)
        else:
            self.connect_btn.config(state='normal')
            # 断开按钮始终可用
            self.disconnect_btn.config(state='normal')
            self.start_monitor_btn.config(state='disabled')
            self.stop_monitor_btn.config(state='disabled')
            
            # 断开时启用配置编辑
            self.set_config_editable(True)
        
        # 更新监控按钮状态
        if is_connected:
            if is_monitoring:
                self.start_monitor_btn.config(state='disabled')
                self.stop_monitor_btn.config(state='normal')
            else:
                self.start_monitor_btn.config(state='normal')
                self.stop_monitor_btn.config(state='disabled') 