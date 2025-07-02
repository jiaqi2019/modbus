import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import make_interp_spline
import logging
import matplotlib
import sys
import os

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class MotorChartDisplay:
    """电机图表展示模块，负责显示电机的图表数据"""
    
    def __init__(self, parent, motor_id):
        self.parent = parent
        self.motor_id = motor_id
        
        # 图表相关
        self.chart = None
        self.chart_data = {
            'timestamps': [],
            'ratios': []
        }
        
        # 创建图表界面
        self.create_chart_display()
        # 数据由外部通过 add_chart_data_point 添加
    
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
            
            # 方法2: 通过调用栈查找启动脚本
            if hasattr(sys, '_getframe'):
                frame = sys._getframe(1)
                while frame:
                    filename = frame.f_code.co_filename
                    if 'run_client.py' in filename or 'main.py' in filename:
                        script_dir = os.path.dirname(os.path.abspath(filename))
                        return script_dir
                    frame = frame.f_back
            
            # 方法3: 查找当前工作目录下的启动脚本
            cwd = os.getcwd()
            run_client_path = os.path.join(cwd, 'run_client.py')
            main_path = os.path.join(cwd, 'main.py')
            if os.path.exists(run_client_path):
                return cwd
            if os.path.exists(main_path):
                return cwd
            
            # 方法4: 查找src目录下的启动脚本
            websocket_client_dir = os.path.join(cwd, 'src', 'websocket_client')
            modbus_client_dir = os.path.join(cwd, 'src', 'modbus_client')
            if os.path.exists(websocket_client_dir):
                return websocket_client_dir
            if os.path.exists(modbus_client_dir):
                return modbus_client_dir
            
            # 备用方案：使用当前工作目录
            logger.warning("无法确定启动脚本目录，使用当前工作目录")
            return os.getcwd()
            
        except Exception as e:
            logger.error(f"获取脚本目录失败: {str(e)}，使用当前工作目录")
            return os.getcwd()
    
    def create_chart_display(self):
        """创建图表显示界面"""
        # 创建标题
        title_label = ttk.Label(
            self.parent, 
            text=f"电机 {self.motor_id} 故障检测趋势", 
            font=('Microsoft YaHei', 11, 'bold'),
            foreground='#2E86AB'
        )
        title_label.pack(pady=(0, 5))
        
        # 创建图表
        self.create_motor_chart()
    
    def create_motor_chart(self):
        """为指定电机创建图表"""
        # 创建matplotlib图形 - 优化尺寸以适应上方70%空间
        fig = Figure(figsize=(10, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # 设置图表标题和标签 - 使用中文
        ax.set_title(f'电机 {self.motor_id} 故障检测比值趋势', fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('时间', fontsize=10)
        ax.set_ylabel('故障检测比值 (%)', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 设置图表样式
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        # 设置刻度标签字体大小
        ax.tick_params(axis='both', which='major', labelsize=9)
        
        # 创建画布并添加到UI
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # 存储图表对象
        self.chart = {
            'fig': fig,
            'ax': ax,
            'canvas': canvas,
            'line': None
        }
    
    def update_chart_display(self):
        """更新图表显示"""
        if not self.chart:
            return
            
        chart = self.chart
        data = self.chart_data
        
        # 清除旧数据
        chart['ax'].clear()
        
        # 重新设置图表样式
        chart['ax'].spines['top'].set_visible(False)
        chart['ax'].spines['right'].set_visible(False)
        chart['ax'].spines['left'].set_color('#cccccc')
        chart['ax'].spines['bottom'].set_color('#cccccc')
        chart['ax'].tick_params(axis='both', which='major', labelsize=9)
        
        if data['timestamps'] and data['ratios']:
            # 过滤掉无效数据（inf, nan）
            valid_data = []
            for i, (timestamp, ratio) in enumerate(zip(data['timestamps'], data['ratios'])):
                if not (np.isnan(ratio) or np.isinf(ratio)):
                    valid_data.append((timestamp, ratio))
            
            if not valid_data:
                # 没有有效数据，显示空图表
                chart['ax'].set_title(f'电机 {self.motor_id} 故障检测比值趋势', fontsize=12, fontweight='bold', pad=10)
                chart['ax'].set_xlabel('时间', fontsize=10)
                chart['ax'].set_ylabel('故障检测比值 (%)', fontsize=10)
                chart['ax'].grid(True, alpha=0.3, linestyle='--')
                chart['ax'].text(0.5, 0.5, '暂无数据', transform=chart['ax'].transAxes, 
                               ha='center', va='center', fontsize=12, color='#999999')
                chart['canvas'].draw()
                return
            
            # 解包有效数据
            timestamps, ratios = zip(*valid_data)
            
            # 绘制平滑曲线图
            if len(timestamps) > 1:
                # 使用样条插值创建平滑曲线
                time_nums = mdates.date2num(timestamps)
                
                # 创建平滑的曲线
                if len(time_nums) >= 3:
                    try:
                        # 使用样条插值创建平滑曲线
                        spline = make_interp_spline(time_nums, ratios, k=min(3, len(time_nums)-1))
                        time_smooth = np.linspace(time_nums.min(), time_nums.max(), 300)
                        ratio_smooth = spline(time_smooth)
                        
                        # 转换回datetime对象
                        time_smooth_dt = mdates.num2date(time_smooth)
                        
                        # 绘制平滑曲线 - 使用更美观的颜色和样式
                        chart['ax'].plot(time_smooth_dt, ratio_smooth, color='#2E86AB', linewidth=2.5, alpha=0.8)
                        
                        # 在原始数据点位置添加标记
                        chart['ax'].scatter(timestamps, ratios, c='#A23B72', s=40, alpha=0.8, zorder=5, edgecolors='white', linewidth=1)
                    except Exception as e:
                        # 如果样条插值失败，使用简单折线
                        logger.warning(f"样条插值失败，使用折线图: {str(e)}")
                        chart['ax'].plot(timestamps, ratios, color='#2E86AB', linewidth=2.5, marker='o', markersize=6, markerfacecolor='#A23B72', markeredgecolor='white', markeredgewidth=1)
                else:
                    # 数据点太少，直接绘制折线
                    chart['ax'].plot(timestamps, ratios, color='#2E86AB', linewidth=2.5, marker='o', markersize=6, markerfacecolor='#A23B72', markeredgecolor='white', markeredgewidth=1)
            else:
                # 只有一个数据点，绘制散点图
                chart['ax'].scatter(timestamps, ratios, c='#2E86AB', s=80, alpha=0.8, edgecolors='white', linewidth=2)
            
            # 设置图表格式
            chart['ax'].set_title(f'电机 {self.motor_id} 故障检测比值趋势 (最近20个数据点)', fontsize=12, fontweight='bold', pad=10)
            chart['ax'].set_xlabel('时间', fontsize=10)
            chart['ax'].set_ylabel('故障检测比值 (%)', fontsize=10)
            chart['ax'].grid(True, alpha=0.3, linestyle='--', color='#cccccc')
            
            # 格式化x轴时间显示
            chart['ax'].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            chart['ax'].xaxis.set_major_locator(mdates.AutoDateLocator())
            
            # 自动调整布局
            chart['fig'].autofmt_xdate()
            
            # 设置y轴范围
            if ratios:
                min_ratio = min(ratios)
                max_ratio = max(ratios)
                margin = (max_ratio - min_ratio) * 0.1 if max_ratio != min_ratio else 1
                chart['ax'].set_ylim(min_ratio - margin, max_ratio + margin)
                
                # 添加零线参考
                if min_ratio < 0 and max_ratio > 0:
                    chart['ax'].axhline(y=0, color='#999999', linestyle='-', alpha=0.5, linewidth=1)
                
                # 添加警告线（±5%）
                chart['ax'].axhline(y=5, color='#FF6B6B', linestyle='--', alpha=0.7, linewidth=1)
                chart['ax'].axhline(y=-5, color='#FF6B6B', linestyle='--', alpha=0.7, linewidth=1)
        else:
            # 没有数据，显示空图表
            chart['ax'].set_title(f'电机 {self.motor_id} 故障检测比值趋势', fontsize=12, fontweight='bold', pad=10)
            chart['ax'].set_xlabel('时间', fontsize=10)
            chart['ax'].set_ylabel('故障检测比值 (%)', fontsize=10)
            chart['ax'].grid(True, alpha=0.3, linestyle='--')
            chart['ax'].text(0.5, 0.5, '暂无数据', transform=chart['ax'].transAxes, 
                           ha='center', va='center', fontsize=12, color='#999999')
        
        # 重绘图表
        chart['canvas'].draw()
    
    def add_chart_data_point(self, timestamp, ratio):
        """添加新的数据点到图表"""
        # 验证数据有效性
        if np.isnan(ratio) or np.isinf(ratio):
            logger.debug(f"跳过无效数据点: motor_id={self.motor_id}, ratio={ratio}")
            return
        
        # 检查是否已经有相同时间戳的数据点
        if self.chart_data['timestamps']:
            # 将时间戳转换为秒精度进行比较
            new_timestamp_sec = timestamp.replace(microsecond=0)
            last_timestamp_sec = self.chart_data['timestamps'][-1].replace(microsecond=0)
            
            if new_timestamp_sec == last_timestamp_sec:
                logger.debug(f"跳过重复时间戳的数据点: motor_id={self.motor_id}, timestamp={timestamp}")
                return
        
        # 添加新数据点
        self.chart_data['timestamps'].append(timestamp)
        self.chart_data['ratios'].append(ratio)
        
        # 限制数据点数量为20个
        if len(self.chart_data['timestamps']) > 20:
            # 移除最旧的数据点（向左移动视口）
            self.chart_data['timestamps'].pop(0)
            self.chart_data['ratios'].pop(0)
        
        # 更新图表显示
        self.update_chart_display()

    def set_data_history(self, history_list):
        """设置历史数据，history_list为MotorData对象列表，刷新图表"""
        # 清空现有数据
        self.chart_data['timestamps'] = []
        self.chart_data['ratios'] = []
        
        # 添加历史数据
        for motor_data in history_list:
            if motor_data.last_update:
                self.chart_data['timestamps'].append(motor_data.last_update)
                self.chart_data['ratios'].append(motor_data.excitation_current_ratio * 100)
        
        # 更新图表显示
        self.update_chart_display()

    