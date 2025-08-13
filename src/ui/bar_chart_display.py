import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import logging
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class MotorBarChart:
    """电机柱状图展示模块，负责显示电机的均值数据"""
    
    def __init__(self, parent, motor_id):
        self.parent = parent
        self.motor_id = motor_id
        
        # 图表相关
        self.chart = None
        self.current_value = 0
        
        # 创建图表界面
        self.create_chart_display()
    
    def create_chart_display(self):
        """创建图表显示界面"""
        # 创建标题
        title_label = ttk.Label(
            self.parent, 
            text=f"{self.motor_id}号发电机故障判断值", 
            font=('Microsoft YaHei', 10, 'bold'),
            foreground='#2E86AB'
        )
        title_label.pack(pady=(0, 5))
        
        # 创建matplotlib图形
        fig = Figure(figsize=(2, 3), dpi=100)  # 调整大小以适应右侧区域
        ax = fig.add_subplot(111)
        
        # 设置图表样式
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        # 设置刻度标签字体大小
        ax.tick_params(axis='both', which='major', labelsize=8)
        
        # 创建画布并添加到UI
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # 存储图表对象
        self.chart = {
            'fig': fig,
            'ax': ax,
            'canvas': canvas,
            'bar': None
        }
        
        # 初始化显示
        self.update_chart_display()
    
    def update_chart_display(self):
        """更新图表显示"""
        if not self.chart:
            return
            
        chart = self.chart
        
        # 清除旧数据
        chart['ax'].clear()
        
        # 重新设置图表样式
        chart['ax'].spines['top'].set_visible(False)
        chart['ax'].spines['right'].set_visible(False)
        chart['ax'].spines['left'].set_color('#cccccc')
        chart['ax'].spines['bottom'].set_color('#cccccc')
        chart['ax'].tick_params(axis='both', which='major', labelsize=8)
        
        # 绘制柱状图
        x = [0]  # 只有一个柱子
        height = [self.current_value]
        
        # 根据数值设置颜色
        color = '#1ABC9C' if self.current_value <= 5 else '#FF6B6B'
        
        # 绘制柱状图
        chart['bar'] = chart['ax'].bar(x, height, width=0.5, color=color, alpha=0.8)
        
        # 在柱子顶部显示数值
        for rect in chart['bar']:
            height = rect.get_height()
            chart['ax'].text(rect.get_x() + rect.get_width()/2., height,
                           f'{height:.2f}%',
                           ha='center', va='bottom', fontsize=8)
        
        # 设置y轴范围固定为0-100
        chart['ax'].set_ylim(0, 100)
        
        # 设置y轴标签
        chart['ax'].set_ylabel('故障检测值 (%)', fontsize=8, labelpad=5)
        
        # 添加警告线（5%）
        chart['ax'].axhline(y=5, color='#FF6B6B', linestyle='--', alpha=0.3, linewidth=1)
        
        # 隐藏x轴刻度
        chart['ax'].set_xticks([])
        
        # 重绘图表
        chart['canvas'].draw()
    
    def update_value(self, value):
        """更新数值并刷新显示"""
        try:
            self.current_value = float(value)
            self.update_chart_display()
        except (ValueError, TypeError) as e:
            logger.error(f"更新柱状图数值失败: {str(e)}")