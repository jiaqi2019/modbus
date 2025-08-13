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
# from db.database import DatabaseManager
from ui.data_display import MotorDataDisplay
from ui.chart_display import MotorChartDisplay
from ui.bar_chart_display import MotorBarChart

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
        # db_config = self.config.get_database_config()
        # self.db_manager = DatabaseManager(db_config.get("path"))
        
        # 简化的数据通信队列
        self.ui_update_queue = queue.Queue()
        self.data_thread = None
        self.data_thread_running = False
        
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
        
        # 启动UI更新循环
        self.start_ui_update_loop()
    
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
    
    def create_motor_display_page(self):
        """创建电机显示页面"""
        motor_frame = ttk.Frame(self.notebook)
        self.notebook.add(motor_frame, text="电机监控")
        
        # 创建可滚动的框架
        self.create_scrollable_frame(motor_frame)
        
        # 创建电机分组notebook（放在可滚动框架内）
        self.motor_notebook = ttk.Notebook(self.scrollable_frame)
        self.motor_notebook.pack(fill='both', expand=True)
        
        # 存储电机显示组件
        self.motor_displays = {}
        self.motor_charts = {}
        self.bar_charts = {}
        
        # 创建电机分组页面（初始为空，连接后动态创建）
        self.motor_container = self.motor_notebook
        
        # 绑定tab切换事件
        self.motor_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_scrollable_frame(self, parent):
        """创建可滚动的框架"""
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(parent, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # 将scrollable_frame放入Canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 绑定事件
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 布局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.pack(side="right", fill="y")
    
    def _on_canvas_configure(self, event):
        """Canvas大小改变时的处理"""
        # 更新scrollable_frame的宽度以匹配Canvas的宽度
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def _on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        # 只有当鼠标在Canvas区域内时才滚动
        if self.canvas.winfo_containing(event.x_root, event.y_root) == self.canvas:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def setup_callbacks(self):
        """设置回调函数"""
        # 数据处理器回调
        self.data_processor.set_data_updated_callback(self.on_data_updated)
    
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
            
            # 启动数据处理线程
            self.start_data_thread()
            
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
    
    def start_data_thread(self):
        """启动数据处理线程"""
        if self.data_thread_running:
            return
            
        self.data_thread_running = True
        
        def data_processing_loop():
            """数据处理主循环"""
            while self.data_thread_running:
                try:
                    # 简化处理逻辑，避免复杂的检查
                    time.sleep(0.1)  # 100ms检查一次
                    
                except Exception as e:
                    logger.error(f"数据处理线程错误: {str(e)}")
                    time.sleep(1)  # 出错时等待1秒
        
        self.data_thread = threading.Thread(target=data_processing_loop, daemon=True)
        self.data_thread.start()
    
    def stop_data_thread(self):
        """停止数据处理线程"""
        self.data_thread_running = False
        if self.data_thread:
            self.data_thread.join(timeout=2)
    
    def start_ui_update_loop(self):
        """启动UI更新循环"""
        def ui_update_loop():
            try:
                # 检查UI更新队列
                while True:
                    try:
                        updated_motors = self.ui_update_queue.get_nowait()
                        self.update_current_tab_only(updated_motors)
                    except queue.Empty:
                        break
            except Exception as e:
                logger.error(f"UI更新循环错误: {str(e)}")
            
            # 继续循环
            self.root.after(50, ui_update_loop)
        
        # 启动UI更新循环
        self.root.after(50, ui_update_loop)
    
    def update_current_tab_only(self, motors: List[MotorData]):
        """只更新当前激活的tab"""
        try:
            if not motors:
                return
                
            # 获取当前激活的tab index
            current_tab_index = self.motor_notebook.index(self.motor_notebook.select())
            
            # 根据tab index计算电机ID范围（每个tab包含2台电机）
            start_id = current_tab_index * 2 + 1
            end_id = start_id + 1
            motor_ids = range(start_id, end_id + 1)
            
            # 只更新当前tab下的电机
            updated_count = 0
            for motor_data in motors:
                if motor_data.motor_id in motor_ids:
                    # 更新数据显示
                    if motor_data.motor_id in self.motor_displays:
                        self.motor_displays[motor_data.motor_id].update_motor_values(motor_data)
                        updated_count += 1
                    
                    # 更新图表显示
                    if motor_data.motor_id in self.motor_charts:
                        self.motor_charts[motor_data.motor_id].add_chart_data_point(
                            motor_data.last_update, 
                            motor_data.excitation_current_ratio * 100
                        )
                        
                    # 更新柱状图显示
                    if motor_data.motor_id in self.bar_charts:
                        self.bar_charts[motor_data.motor_id].update_value(
                            motor_data.average_excitation_current_ratio * 100
                        )
            
            if updated_count > 0:
                logger.debug(f"更新当前tab电机显示，成功更新 {updated_count} 台电机")
                
        except Exception as e:
            logger.error(f"更新当前tab失败: {str(e)}")
    
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
            
            # 停止数据处理线程
            self.stop_data_thread()
            
            # 停止WebSocket客户端
            if self.websocket_client:
                self.websocket_client.stop()
                self.websocket_client = None
            
            # 更新状态
            self.is_connected = False
            self.is_monitoring = False
            
            # 清理UI组件
            self.clear_motor_components()
            
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
        
        # 创建所有电机的UI组件
        self.create_all_motor_components()
        
        # 开始监控
        self.start_monitoring()
    
    def on_websocket_disconnect(self):
        """WebSocket断开连接回调"""
        # logger.info("WebSocket连接断开")
        self.is_connected = False
        self.is_monitoring = False
        
        # 清理UI组件
        self.root.after(0, lambda: self.clear_motor_components())
        
        # 更新UI状态
        self.root.after(0, lambda: self.top_menu.update_connection_status(False))
    
    def on_websocket_message(self, message: Dict[str, Any]):
        """WebSocket消息回调 - 直接处理数据"""
        try:
            # 直接处理数据，不放入队列
            updated_motors = self.data_processor.process_websocket_message(message)
            if updated_motors:
                # 将更新放入UI队列
                self.ui_update_queue.put(updated_motors)
                
        except Exception as e:
            logger.error(f"WebSocket消息处理失败: {str(e)}")
    
    def on_websocket_error(self, error: str):
        """WebSocket错误回调"""
        logger.error(f"WebSocket错误: {error}")
        self.root.after(0, lambda: self.top_menu.show_error_message(f"连接错误: {error}"))
    
    def on_data_updated(self, motors: List[MotorData]):
        """数据更新回调 - 不再使用"""
        # 这个回调现在由on_websocket_message直接处理
        pass
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_connected:
            return
        
        self.is_monitoring = True
        # # logger.info("开始监控电机数据")
    
    def create_all_motor_components(self):
        """创建所有电机的UI组件"""
        try:
            # 创建12个电机的UI组件（根据calc目录的文件数量）
            motor_ids = list(range(1, 13))  # 电机1-12
            
            for motor_id in motor_ids:
                self.create_motor_displays_for_motor(motor_id)
            
            logger.info(f"已创建所有电机UI组件，共 {len(motor_ids)} 台电机")
            
        except Exception as e:
            logger.error(f"创建所有电机UI组件失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def clear_motor_components(self):
        """清理所有电机UI组件"""
        try:
            # 清空电机显示和图表组件字典
            self.motor_displays.clear()
            self.motor_charts.clear()
            
            # 清空notebook中的所有页面
            for i in range(self.motor_notebook.index('end') - 1, -1, -1):
                self.motor_notebook.forget(i)
            
            logger.info("已清理所有电机UI组件")
            
        except Exception as e:
            logger.error(f"清理电机UI组件失败: {str(e)}")
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
            group_tab_title = f"{start_motor}-{end_motor}号发电机"
            
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

            # 左侧图表区域 - 60%
            chart_frame = ttk.Frame(left_right_frame)
            chart_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

            # 中间柱状图区域 - 20%
            bar_frame = ttk.Frame(left_right_frame, width=300)
            bar_frame.pack(side='left', fill='y', padx=5)
            bar_frame.pack_propagate(False)  # 固定宽度

            # 右侧数据区域 - 20%
            data_frame = ttk.Frame(left_right_frame, width=200)
            data_frame.pack(side='right', fill='y', padx=(5, 0))
            data_frame.pack_propagate(False)  # 固定宽度

            # 创建图表显示（左侧，占用60%空间）
            chart_display = MotorChartDisplay(chart_frame, motor_id)
            self.motor_charts[motor_id] = chart_display

            # 创建柱状图显示（中间，占用20%空间）
            bar_chart = MotorBarChart(bar_frame, motor_id)
            self.bar_charts[motor_id] = bar_chart

            # 创建数据显示（右侧，占用20%空间，可滚动）
            data_display = MotorDataDisplay(data_frame, motor_id)
            self.motor_displays[motor_id] = data_display

            # logger.info(f"创建电机 {motor_id} 的显示组件，分组: {group_tab_title}")
            
        except Exception as e:
            logger.error(f"创建电机 {motor_id} 显示组件失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def on_tab_changed(self, event):
        """tab切换时刷新最近20条数据"""
        try:
            # 获取当前tab的index
            current_tab_index = event.widget.index(event.widget.select())
            
            # 根据tab index计算电机ID范围（每个tab包含2台电机）
            start_id = current_tab_index * 2 + 1
            end_id = start_id + 1
            motor_ids = range(start_id, end_id + 1)
            
            # 获取最近20条数据并刷新显示
            for motor_id in motor_ids:
                motor_data = self.data_processor.get_motor_data(motor_id)
                if motor_data and motor_id in self.motor_displays:
                    # 刷新数据显示
                    self.motor_displays[motor_id].update_motor_values(motor_data)
                
                                    # 刷新图表显示
                    if motor_id in self.motor_charts:
                        history_data = self.data_processor.get_motor_history(motor_id, 20)
                        if history_data:
                            # 使用set_data_history方法刷新图表
                            self.motor_charts[motor_id].set_data_history(history_data)
                            
                            # 更新柱状图显示
                            if motor_id in self.bar_charts and history_data:
                                latest_data = history_data[-1]
                                self.bar_charts[motor_id].update_value(
                                    latest_data.average_excitation_current_ratio * 100
                                )
                        
        except Exception as e:
            logger.error(f"tab切换刷新数据失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def run(self):
        """运行主程序"""
        try:
            # logger.info("启动WebSocket客户端UI")
            
            self.root.mainloop()
        except Exception as e:
            logger.error(f"运行UI失败: {str(e)}")
        finally:
            # 清理资源
            self.stop_data_thread()
            if self.websocket_client:
                self.websocket_client.stop()
            
            # 解绑鼠标滚轮事件
            try:
                if hasattr(self, 'canvas'):
                    self.canvas.unbind_all("<MouseWheel>")
            except:
                pass

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