import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
import sys
import os
import queue
from typing import Dict, Any, List
from datetime import datetime

# 添加父目录到路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from config import WebSocketConfig
from websocket_client import WebSocketClient
from data_processor import DataProcessor, MotorData
from top_menu import WebSocketTopMenu
from db.database import DatabaseManager
from ui.data_display import MotorDataDisplay
from ui.chart_display import MotorChartDisplay

logger = logging.getLogger(__name__)

class WebSocketClientUI:
    """WebSocket客户端主UI框架"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WebSocket客户端 - 电机数据监控")
        self.root.geometry("1200x800")
        
        # 设置日志级别，减少不必要的输出
        logging.getLogger('websocket_client').setLevel(logging.WARNING)
        logging.getLogger('data_processor').setLevel(logging.INFO)
        
        # 初始化组件
        self.config = WebSocketConfig()
        self.websocket_client = None
        self.data_processor = DataProcessor()
        
        # 使用配置中的数据库路径
        db_config = self.config.get_database_config()
        self.db_manager = DatabaseManager(db_config.get("path"))
        
        # 消息队列，用于异步处理WebSocket消息
        self.message_queue = queue.Queue()
        self.message_processing = False
        
        # UI组件
        self.top_menu = None
        self.motor_displays = {}  # 电机数据显示组件
        self.motor_charts = {}    # 电机图表组件
        
        # 状态变量
        self.is_connected = False
        self.is_monitoring = False
        
        # 初始化UI
        self.init_ui()
        
        # 设置回调函数
        self.setup_callbacks()
        
        # 启动消息处理线程
        self.start_message_processor()
    
    def init_ui(self):
        """初始化UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建顶部菜单
        self.top_menu = WebSocketTopMenu(
            main_frame, 
            self.config.config,
            on_save_config=self.on_save_config,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect
        )
        
        # 创建主要内容区域
        self.create_main_content(main_frame)
        
        # logger.info("UI界面初始化完成")
    
    def create_main_content(self, parent):
        """创建主要内容区域"""
        # 创建notebook用于标签页
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True, pady=5)
        
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
        self.motor_charts = {}
        
        # 创建电机分组页面（初始为空，连接后动态创建）
        self.motor_container = self.motor_notebook
    
    def create_system_info_page(self):
        """创建系统信息页面"""
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="系统信息")
        
        # 系统信息显示
        info_text = tk.Text(info_frame, wrap='word', height=20)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.info_text = info_text
        
        # 更新系统信息
        self.update_system_info()
    
    def update_system_info(self):
        """更新系统信息"""
        try:
            info = f"""
系统信息:
========

数据库路径: {self.db_manager.db_path if self.db_manager else '未初始化'}

WebSocket配置:
- 主机: {self.config.get_websocket_config()['host']}
- 端口: {self.config.get_websocket_config()['port']}

连接状态:
- WebSocket: {'已连接' if self.is_connected else '未连接'}
- 监控状态: {'运行中' if self.is_monitoring else '已停止'}

电机数据:
- 已显示电机数量: {len(self.motor_displays)}

最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
            
        except Exception as e:
            logger.error(f"更新系统信息失败: {str(e)}")
    
    def setup_callbacks(self):
        """设置回调函数"""
        # 数据处理器回调
        self.data_processor.set_data_updated_callback(self.on_data_updated)
        
        # WebSocket客户端回调 - 在创建客户端时设置
        # 注意：这里不设置，因为在connect_to_websocket中设置
    
    def connect_to_websocket(self, host: str, port: int):
        """连接到WebSocket服务器"""
        try:
            # 如果已有连接，先断开
            if self.websocket_client:
                # logger.info("检测到已有连接，先断开")
                self.websocket_client.stop()
                self.websocket_client = None
                # 等待一下确保完全断开
                import time
                time.sleep(1)
            
            # 重新启动消息处理线程
            self.start_message_processor()
            
            # 创建WebSocket客户端
            self.websocket_client = WebSocketClient(host, port)
            
            # 设置回调函数
            self.websocket_client.set_callbacks(
                on_connect=self.on_websocket_connect,
                on_disconnect=self.on_websocket_disconnect,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error
            )
            
            # 启动客户端
            self.websocket_client.start()
            
            # logger.info(f"正在连接到WebSocket服务器: {host}:{port}")
            
        except Exception as e:
            logger.error(f"连接WebSocket失败: {str(e)}")
            self.top_menu.show_error_message(f"连接失败: {str(e)}")
    
    def on_save_config(self):
        """保存配置回调"""
        try:
            config_values = self.top_menu.get_config_values()
            ws_config = config_values['websocket']
            
            # 保存配置
            success = self.config.set_websocket_config(ws_config['host'], ws_config['port'])
            
            if success:
                self.top_menu.show_info_message("配置已保存")
                # logger.info("配置已保存")
            else:
                self.top_menu.show_error_message("保存配置失败")
                
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            self.top_menu.show_error_message(f"保存配置失败: {str(e)}")
    
    def on_connect(self):
        """连接按钮回调"""
        try:
            config_values = self.top_menu.get_config_values()
            ws_config = config_values['websocket']
            
            self.connect_to_websocket(ws_config['host'], ws_config['port'])
            
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
            self.top_menu.show_error_message(f"连接失败: {str(e)}")
    
    def on_disconnect(self):
        """断开连接按钮回调"""
        try:
            # logger.info("用户请求断开连接")
            
            # 停止消息处理线程
            self.stop_message_processor()
            
            # 停止WebSocket客户端
            if self.websocket_client:
                self.websocket_client.stop()
                self.websocket_client = None
            
            # 更新状态
            self.is_connected = False
            self.is_monitoring = False
            
            # 更新UI状态
            self.root.after(0, lambda: self.top_menu.update_connection_status(False))
            
            # logger.info("断开连接完成")
            
        except Exception as e:
            logger.error(f"断开连接失败: {str(e)}")
            self.top_menu.show_error_message(f"断开连接失败: {str(e)}")
    
    def on_websocket_connect(self):
        """WebSocket连接成功回调"""
        # logger.info("WebSocket连接成功")
        self.is_connected = True
        
        # 更新UI状态
        self.root.after(0, lambda: self.top_menu.update_connection_status(True))
        
        # 开始监控
        self.start_monitoring()
    
    def on_websocket_disconnect(self):
        """WebSocket断开连接回调"""
        # logger.info("WebSocket连接断开")
        self.is_connected = False
        self.is_monitoring = False
        
        # 更新UI状态
        self.root.after(0, lambda: self.top_menu.update_connection_status(False))
    
    def on_websocket_message(self, message: Dict[str, Any]):
        """WebSocket消息回调"""
        try:
            # 将消息放入队列，由后台线程处理
            self.message_queue.put(message)
            logger.debug("消息已加入处理队列")
                
        except Exception as e:
            logger.error(f"WebSocket消息处理失败: {str(e)}")
    
    def on_websocket_error(self, error: str):
        """WebSocket错误回调"""
        logger.error(f"WebSocket错误: {error}")
        self.root.after(0, lambda: self.top_menu.show_error_message(f"连接错误: {error}"))
    
    def on_data_updated(self, motors: List[MotorData]):
        """数据更新回调"""
        try:
            # # logger.info(f"数据更新回调被触发，电机数量: {len(motors)}")
            
            # 记录每个电机的详细信息（减少日志输出）
            for motor in motors:
                logger.debug(f"电机 {motor.motor_id}: 时间={motor.last_update}, 比值={motor.excitation_current_ratio}")
            
            # 在后台线程中保存数据库，避免阻塞UI
            def save_data_async():
                try:
                    self.db_manager.save_all_motors_data(motors)
                    logger.debug("数据已保存到数据库")
                except Exception as e:
                    logger.error(f"保存数据到数据库失败: {str(e)}")
            
            # 启动后台线程保存数据
            import threading
            save_thread = threading.Thread(target=save_data_async, daemon=True)
            save_thread.start()
            
            # 批量检查并创建缺失的显示组件
            missing_components = []
            for motor in motors:
                motor_id = motor.motor_id
                if motor_id not in self.motor_displays:
                    missing_components.append(motor_id)
            
            # 如果有缺失的组件，批量创建
            if missing_components:
                def create_components_async():
                    try:
                        for motor_id in missing_components:
                            # # logger.info(f"创建电机 {motor_id} 显示组件")
                            # 在主线程中创建UI组件
                            self.root.after(0, lambda mid=motor_id: self.create_motor_displays_for_motor(mid))
                    except Exception as e:
                        logger.error(f"创建显示组件失败: {str(e)}")
                
                # 启动后台线程检查组件
                component_thread = threading.Thread(target=create_components_async, daemon=True)
                component_thread.start()
            
            # 立即更新UI显示（使用after_idle避免阻塞）
            self.root.after_idle(lambda: self.update_motor_displays(motors))
            logger.debug("UI更新已安排")
            
        except Exception as e:
            logger.error(f"更新数据显示失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_connected:
            return
        
        self.is_monitoring = True
        # # logger.info("开始监控电机数据")
    
    def update_motor_displays(self, motors: List[MotorData]):
        """更新电机显示"""
        try:
            logger.debug(f"开始更新电机显示，电机数量: {len(motors)}")
            
            updated_count = 0
            for motor_data in motors:
                motor_id = motor_data.motor_id
                
                # 更新数据显示
                if motor_id in self.motor_displays:
                    self.motor_displays[motor_id].update_motor_values(motor_data)
                    updated_count += 1
                
                # 更新图表显示
                if motor_id in self.motor_charts:
                    self.motor_charts[motor_id].add_chart_data_point(
                        motor_data.last_update, 
                        motor_data.excitation_current_ratio * 100
                    )
            
            logger.debug(f"电机显示更新完成，成功更新 {updated_count} 台电机")
            
        except Exception as e:
            logger.error(f"更新电机显示失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def create_motor_displays_for_motor(self, motor_id: int):
        """为指定电机创建显示组件"""
        try:
            # 计算电机应该属于哪个分组
            group_id = (motor_id - 1) // 2  # 每2个电机一组
            start_motor = group_id * 2 + 1
            end_motor = start_motor + 1
            
            # 创建分组页面标题
            group_tab_title = f"电机 {start_motor}-{end_motor}"
            
            # 检查分组页面是否已存在
            group_frame = None
            for i in range(self.motor_notebook.index('end')):
                if self.motor_notebook.tab(i, 'text') == group_tab_title:
                    # 获取对应的frame
                    group_frame = self.motor_notebook.winfo_children()[i]
                    break
            
            # 如果分组页面不存在，创建新的
            if group_frame is None:
                group_frame = ttk.Frame(self.motor_notebook)
                self.motor_notebook.add(group_frame, text=group_tab_title)
                # logger.info(f"创建新的分组页面: {group_tab_title}")
            
            # 检查电机框架是否已存在
            existing_motor_frame = None
            for child in group_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and child.cget('text') == f"电机 {motor_id}":
                    existing_motor_frame = child
                    break
            
            if existing_motor_frame:
                # logger.info(f"电机 {motor_id} 的显示组件已存在")
                return
            
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
            self.motor_charts[motor_id] = chart_display

            # 创建数据显示（右侧，占用20%空间，可滚动）
            data_display = MotorDataDisplay(data_frame, motor_id)
            self.motor_displays[motor_id] = data_display

            # logger.info(f"创建电机 {motor_id} 的显示组件，分组: {group_tab_title}")
            
        except Exception as e:
            logger.error(f"创建电机 {motor_id} 显示组件失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    def run(self):
        """运行主程序"""
        try:
            # logger.info("启动WebSocket客户端UI")
            
            # 定期更新系统信息
            def update_info():
                self.update_system_info()
                self.root.after(5000, update_info)  # 每5秒更新一次
            
            update_info()
            
            self.root.mainloop()
        except Exception as e:
            logger.error(f"运行UI失败: {str(e)}")
        finally:
            # 清理资源
            self.stop_message_processor()
            if self.websocket_client:
                self.websocket_client.stop()
    
    def start_message_processor(self):
        """启动消息处理线程"""
        def process_messages():
            while True:
                try:
                    # 从队列中获取消息，设置超时避免无限等待
                    message = self.message_queue.get(timeout=1.0)
                    if message is None:  # 停止信号
                        break
                    
                    # 处理消息
                    self.process_message_sync(message)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"消息处理线程错误: {str(e)}")
        
        self.message_processing = True
        message_thread = threading.Thread(target=process_messages, daemon=True)
        message_thread.start()
        # logger.info("消息处理线程已启动")
    
    def process_message_sync(self, message: Dict[str, Any]):
        """同步处理消息"""
        try:
            updated_motors = self.data_processor.process_websocket_message(message)
            
            if updated_motors:
                # # logger.info(f"处理消息完成，电机数量: {len(updated_motors)}")
                # 在主线程中触发UI更新
                self.root.after(0, lambda: self.on_data_updated(updated_motors))
            else:
                logger.debug("处理消息但无电机数据更新")
                
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")
    
    def stop_message_processor(self):
        """停止消息处理线程"""
        self.message_processing = False
        self.message_queue.put(None)  # 发送停止信号
        # logger.info("消息处理线程已停止")

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行UI
    app = WebSocketClientUI()
    app.run()

if __name__ == "__main__":
    main() 