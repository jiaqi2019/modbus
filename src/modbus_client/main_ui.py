import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import threading
import time
import logging
import sys
import os
import asyncio
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modbus_client import ModbusClient
from websocket_server.websocket_server import WebSocketServer
from db.database import DatabaseManager
from ui.data_display import MotorDataDisplay
from ui.chart_display import MotorChartDisplay
from ui.top_menu import TopMenu
from ui.connection_status import ConnectionStatus
from data_processor import DataProcessor

logger = logging.getLogger(__name__)

class MainUI:
    """主UI框架"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("电机监控系统")
        self.root.geometry("1400x900")
        
        # 初始化组件
        self.modbus_client = None
        self.websocket_server = None
        self.db_manager = None
        self.data_processor = None
        
        # 状态变量
        self.is_connected = False
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # 配置数据
        self.config = self.load_config()
        
        # 最新数据缓存
        self.latest_motors_data = []
        
        # 创建UI
        self.create_ui()
        
        # 启动初始化流程
        self.initialize_system()
    
    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {
                "modbus": {
                    "host": "localhost",
                    "port": 5020,
                    "motor_count": 12
                },
                "auto_update": {
                    "enabled": 1,
                    "interval": 1
                },
                "websocket": {
                    "host": "0.0.0.0",
                    "port": 8765
                }
            }
    
    def save_config(self):
        """保存配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")
    
    def create_ui(self):
        """创建UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建顶部区域（配置菜单和连接状态左右展示）
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 10))
        
        # 左侧：配置菜单
        self.top_menu = TopMenu(
            top_frame, 
            self.config,
            on_save_config=self.save_configuration,
            on_connect=self.connect_modbus,
            on_disconnect=self.disconnect_modbus,
            on_start_monitor=self.start_monitoring,
            on_stop_monitor=self.stop_monitoring
        )
        
        # 右侧：连接状态
        self.connection_status = ConnectionStatus(top_frame)
        
        # 创建主要内容区域
        self.create_main_content(main_frame)
    
    def create_main_content(self, parent):
        """创建主要内容区域"""
        # 创建notebook用于标签页
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)
        
        # 创建电机显示页面
        self.create_motor_display_page()
        
        # 创建系统信息页面
        self.create_system_info_page()
    
    def create_motor_display_page(self):
        """创建电机显示页面"""
        motor_frame = ttk.Frame(self.notebook)
        self.notebook.add(motor_frame, text="电机监控")
        
        # 创建电机分组notebook
        self.motor_notebook = ttk.Notebook(motor_frame)
        self.motor_notebook.pack(fill='both', expand=True)
        
        # 存储电机显示组件
        self.motor_displays = {}
        self.chart_displays = {}
        
        # 创建电机分组页面（初始为空，连接后动态创建）
        self.motor_container = self.motor_notebook
    
    def create_system_info_page(self):
        """创建系统信息页面"""
        info_frame = ttk.Notebook(self.notebook)
        self.notebook.add(info_frame, text="系统信息")
        
        # 系统信息显示
        info_text = tk.Text(info_frame, wrap='word', height=20)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.info_text = info_text
        
        # 更新系统信息
        self.update_system_info()
    
    def initialize_system(self):
        """初始化系统组件"""
        try:
            # 初始化数据库 - 使用脚本目录
            script_dir = self._get_script_directory()
            db_path = os.path.join(script_dir, "motor_data.db")
            self.db_manager = DatabaseManager(db_path)
            logger.info(f"数据库初始化完成: {db_path}")
            
            # 初始化数据处理器
            motor_count = self.config['modbus']['motor_count']
            self.data_processor = DataProcessor(motor_count)
            logger.info(f"数据处理器初始化完成，支持 {motor_count} 台电机")
            
            # 初始化WebSocket服务器
            ws_host = self.config['websocket']['host']
            ws_port = self.config['websocket']['port']
            self.websocket_server = WebSocketServer(self, host=ws_host, port=ws_port)
            self.websocket_server.start()
            logger.info(f"WebSocket服务器启动完成 - {ws_host}:{ws_port}")
            
            # 设置初始配置编辑状态（未连接时允许编辑）
            self.set_config_editable(True)
            
            # 不再自动连接，需要用户手动点击连接按钮
            
        except Exception as e:
            logger.error(f"系统初始化失败: {str(e)}")
            messagebox.showerror("初始化错误", f"系统初始化失败: {str(e)}")
    
    def _get_script_directory(self):
        """获取启动脚本的目录"""
        try:
            # 方法1: 通过sys.argv获取启动脚本路径
            if len(sys.argv) > 0:
                script_path = sys.argv[0]
                if os.path.isabs(script_path):
                    return os.path.dirname(script_path)
                else:
                    # 相对路径，转换为绝对路径
                    return os.path.dirname(os.path.abspath(script_path))
            
            # 方法2: 通过调用栈查找main.py
            if hasattr(sys, '_getframe'):
                frame = sys._getframe(1)
                while frame:
                    filename = frame.f_code.co_filename
                    if 'main.py' in filename:
                        script_dir = os.path.dirname(os.path.abspath(filename))
                        return script_dir
                    frame = frame.f_back
            
            # 方法3: 查找当前工作目录下的main.py
            cwd = os.getcwd()
            main_path = os.path.join(cwd, 'main.py')
            if os.path.exists(main_path):
                return cwd
            
            # 方法4: 查找src/modbus_client/main_ui.py
            modbus_client_dir = os.path.join(cwd, 'src', 'modbus_client')
            if os.path.exists(modbus_client_dir):
                return modbus_client_dir
            
            # 备用方案：使用当前工作目录
            logger.warning("无法确定启动脚本目录，使用当前工作目录")
            return os.getcwd()
            
        except Exception as e:
            logger.error(f"获取脚本目录失败: {str(e)}，使用当前工作目录")
            return os.getcwd()
    
    def save_configuration(self):
        """保存配置"""
        try:
            # 从top_menu组件获取配置值
            config_values = self.top_menu.get_config_values()
            
            # 更新配置数据
            self.config['modbus'] = config_values['modbus']
            self.config['auto_update']['interval'] = config_values['auto_update']['interval']
            self.config['websocket'] = config_values['websocket']
            
            # 保存到文件
            self.save_config()
            
            messagebox.showinfo("成功", "配置保存成功")
            
            # 保存配置后，根据当前连接状态重新设置配置编辑状态
            self.set_config_editable(not self.is_connected)
            
        except ValueError as e:
            messagebox.showerror("错误", "请输入有效的数值")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def connect_modbus(self):
        """连接Modbus服务器"""
        try:
            # 从top_menu组件获取配置
            config_values = self.top_menu.get_config_values()
            host = config_values['modbus']['host']
            port = config_values['modbus']['port']
            motor_count = config_values['modbus']['motor_count']
            
            # 创建Modbus客户端
            self.modbus_client = ModbusClient(host, port, motor_count)
            
            # 尝试连接
            if self.modbus_client.connect():
                self.is_connected = True
                self.update_connection_status()
                self.create_motor_displays(motor_count)
                logger.info("Modbus连接成功")
            else:
                self.is_connected = False
                self.update_connection_status()
                messagebox.showerror("错误", "Modbus连接失败")
                logger.error("Modbus连接失败")
                
        except Exception as e:
            logger.error(f"连接Modbus失败: {str(e)}")
            messagebox.showerror("错误", f"连接失败: {str(e)}")
    
    def disconnect_modbus(self):
        """断开Modbus连接"""
        try:
            logger.info("开始断开Modbus连接")
            if self.modbus_client:
                self.modbus_client.disconnect()
                self.is_connected = False
                logger.info(f"断开连接后，is_connected={self.is_connected}")
                self.update_connection_status()
                logger.info("Modbus连接已断开")
        except Exception as e:
            logger.error(f"断开连接失败: {str(e)}")
    
    def create_motor_displays(self, motor_count):
        """创建电机显示组件"""
        # 清除现有显示
        for widget in self.motor_notebook.winfo_children():
            widget.destroy()
        
        self.motor_displays = {}
        self.chart_displays = {}
        
        # 计算需要多少个分组tab
        group_count = (motor_count + 1) // 2  # 向上取整
        
        logger.info(f"创建 {motor_count} 台电机的显示，分为 {group_count} 个组")
        
        # 为每个分组创建tab
        for group_id in range(group_count):
            start_motor = group_id * 2 + 1
            end_motor = min(start_motor + 1, motor_count)
            
            # 创建分组页面
            group_frame = ttk.Frame(self.motor_notebook)
            tab_title = f"电机 {start_motor}-{end_motor}"
            self.motor_notebook.add(group_frame, text=tab_title)
            
            # 为这个分组中的每个电机创建显示
            for motor_id in range(start_motor, end_motor + 1):
                # 创建电机框架
                motor_frame = ttk.LabelFrame(group_frame, text=f"电机 {motor_id}", padding=5)
                motor_frame.pack(fill='both', expand=True, padx=10, pady=5)
                
                # 创建左右分栏 - 左侧图表80%，右侧数据20%
                left_right_frame = ttk.Frame(motor_frame)
                left_right_frame.pack(fill='both', expand=True, padx=5, pady=5)

                # 左侧图表区域 - 80%
                chart_frame = ttk.Frame(left_right_frame)
                chart_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

                # 右侧数据区域 - 20%
                data_frame = ttk.Frame(left_right_frame, width=200)
                data_frame.pack(side='right', fill='y', padx=(5, 0))
                data_frame.pack_propagate(False)  # 固定宽度

                # 创建图表显示（左侧，占用80%空间）
                chart_display = MotorChartDisplay(chart_frame, motor_id)
                self.chart_displays[motor_id] = chart_display

                # 创建数据显示（右侧，占用20%空间，可滚动）
                data_display = MotorDataDisplay(data_frame, motor_id)
                self.motor_displays[motor_id] = data_display

                logger.info(f"创建电机 {motor_id} 的显示组件")
        
        logger.info(f"电机显示组件创建完成，共 {len(self.motor_displays)} 个数据显示，{len(self.chart_displays)} 个图表显示")
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_connected:
            messagebox.showerror("错误", "请先连接Modbus服务器")
            return
        
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # 更新按钮状态
        self.top_menu.update_connection_status(self.is_connected, self.is_monitoring)
        
        logger.info("开始监控")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        
        # 更新按钮状态
        self.top_menu.update_connection_status(self.is_connected, self.is_monitoring)
        
        logger.info("停止监控")
    
    def monitoring_loop(self):
        """监控循环"""
        interval = int(self.top_menu.get_config_values()['auto_update']['interval'])
        
        while self.is_monitoring and self.is_connected:
            try:
                # 步骤2: 获取Modbus数据
                raw_data = self.modbus_client.request_motor_data()
                
                if raw_data:
                    # 处理数据
                    motors_data = self.data_processor.process_motor_data(raw_data)
                    
                    # 更新最新数据缓存
                    self.latest_motors_data = motors_data
                    
                    # 步骤3: 广播数据（使用线程安全的方式）
                    if self.websocket_server:
                        # 在新线程中运行异步广播
                        broadcast_thread = threading.Thread(
                            target=self.broadcast_data_async, 
                            args=(motors_data,), 
                            daemon=True
                        )
                        broadcast_thread.start()
                    
                    # 步骤4: 保存到数据库
                    if self.db_manager:
                        self.db_manager.save_all_motors_data(motors_data)
                    
                    # 步骤5: 更新UI显示
                    self.root.after(0, self.update_motor_displays, motors_data)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")
                time.sleep(interval)
    
    def broadcast_data_async(self, motors_data):
        """异步广播数据"""
        try:
            logger.debug(f"开始广播数据，数据类型: {type(motors_data)}, 长度: {len(motors_data)}")
            
            # 将MotorData对象列表转换为字典列表
            formatted_data = []
            for i, motor_data in enumerate(motors_data):
                logger.debug(f"处理第 {i+1} 个电机数据，类型: {type(motor_data)}")
                if hasattr(motor_data, 'to_dict'):
                    formatted_motor_data = motor_data.to_dict()
                    formatted_data.append(formatted_motor_data)
                    logger.debug(f"电机 {motor_data.motor_id} 数据格式化成功")
                else:
                    logger.warning(f"电机数据对象缺少to_dict方法: {type(motor_data)}")
                    continue
            
            if not formatted_data:
                logger.warning("没有可广播的格式化数据")
                return
            
            logger.debug(f"格式化完成，共 {len(formatted_data)} 条数据")
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行广播
            loop.run_until_complete(self.websocket_server.broadcast_data(formatted_data))
            
            # 打印广播数据中所有电机的excitation_current_ratio值
            logger.info("广播完成，电机excitation_current_ratio值:")
            for motor_data in motors_data:
                logger.info(f"电机 {motor_data.motor_id}: excitation_current_ratio = {motor_data.excitation_current_ratio:.2f}")
            
            
        except Exception as e:
            logger.error(f"广播数据失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
        finally:
            loop.close()
    
    def update_motor_displays(self, motors_data):
        """更新电机显示"""
        try:
            for motor_data in motors_data:
                motor_id = motor_data.motor_id
                
                # 更新数据显示
                if motor_id in self.motor_displays:
                    self.motor_displays[motor_id].update_motor_values(motor_data)
                
                # 更新图表显示
                if motor_id in self.chart_displays:
                    self.chart_displays[motor_id].add_chart_data_point(
                        motor_data.last_update, 
                        motor_data.excitation_current_ratio * 100
                    )
        except Exception as e:
            logger.error(f"更新电机显示失败: {str(e)}")
    
    def set_config_editable(self, editable=True):
        """设置配置输入框的编辑状态"""
        self.top_menu.set_config_editable(editable)
    
    def update_connection_status(self):
        """更新连接状态显示"""
        logger.info(f"更新连接状态: is_connected={self.is_connected}")
        
        # 更新top_menu组件的连接状态
        self.top_menu.update_connection_status(self.is_connected, self.is_monitoring)
        
        # 更新connection_status组件
        if self.is_connected:
            # 显示连接信息
            if self.modbus_client:
                info = self.modbus_client.get_connection_info()
                self.connection_status.update_status(True, info)
        else:
            self.connection_status.update_status(False)
    
    def update_system_info(self):
        """更新系统信息"""
        try:
            # 更新WebSocket客户端数量
            if self.websocket_server:
                client_count = self.websocket_server.get_client_count()
                self.connection_status.update_websocket_client_count(client_count)
            
            info = f"""
系统信息:
========

数据库路径: {self.db_manager.db_path if self.db_manager else '未初始化'}

Modbus配置:
- 主机: {self.config['modbus']['host']}
- 端口: {self.config['modbus']['port']}
- 电机数量: {self.config['modbus']['motor_count']}

更新配置:
- 自动更新: {'启用' if self.config['auto_update']['enabled'] else '禁用'}
- 更新间隔: {self.config['auto_update']['interval']} 秒

WebSocket服务器:
- 主机: {self.config['websocket']['host']}
- 端口: {self.config['websocket']['port']}
- 状态: {'运行中' if self.websocket_server else '未启动'}
- 客户端数量: {self.websocket_server.get_client_count() if self.websocket_server else 0}

连接状态:
- Modbus: {'已连接' if self.is_connected else '未连接'}
- 监控状态: {'运行中' if self.is_monitoring else '已停止'}

最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
            
        except Exception as e:
            logger.error(f"更新系统信息失败: {str(e)}")
    
    def get_latest_motors_data(self):
        """获取最新电机数据（供WebSocket服务器使用）"""
        return self.latest_motors_data
    
    def run(self):
        """运行主UI"""
        # 定期更新系统信息
        def update_info():
            self.update_system_info()
            self.root.after(5000, update_info)  # 每5秒更新一次
        
        update_info()
        
        # 运行主循环
        self.root.mainloop()
        
        # 清理资源
        self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_monitoring()
            
            if self.modbus_client:
                self.modbus_client.disconnect()
            
            if self.websocket_server:
                self.websocket_server.stop()
                
            logger.info("系统资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # 创建并运行主UI
    app = MainUI()
    app.run() 