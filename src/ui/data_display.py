import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class MotorDataDisplay:
    """电机数据展示模块，负责显示电机的基本数据"""
    
    def __init__(self, parent, motor_id):
        self.parent = parent
        self.motor_id = motor_id
        self.value_labels = {}
        
        # 创建数据显示界面
        self.create_data_display()
    
    def create_data_display(self):
        """创建数据显示界面"""
        # 创建标题
        title_label = ttk.Label(
            self.parent, 
            text=f"电机 {self.motor_id} 数据", 
            font=('Microsoft YaHei', 10, 'bold'),
            foreground='#2E86AB'
        )
        title_label.pack(pady=(0, 5))

        # 创建数据容器 - 水平布局
        data_container = ttk.Frame(self.parent)
        data_container.pack(fill='x', expand=True)

        # 定义数据项 - 使用水平布局
        data_items = [
            ("A相电流", "phase_a_current", "A"),
            ("B相电流", "phase_b_current", "A"),
            ("C相电流", "phase_c_current", "A"),
            ("频率", "frequency", "Hz"),
            ("无功功率", "reactive_power", "kVar"),
            ("有功功率", "active_power", "kW"),
            ("线电压", "line_voltage", "kV"),
            ("励磁电压", "excitation_voltage", "V"),
            ("励磁电流", "excitation_current", "A"),
            ("计算励磁电流", "calculated_excitation_current", "A")
        ]

        # 创建数据行 - 每行显示5个数据项
        for i in range(0, len(data_items), 5):
            row_frame = ttk.Frame(data_container)
            row_frame.pack(fill='x', pady=2)
            for j in range(5):
                if i + j < len(data_items):
                    item = data_items[i + j]
                    self._create_data_item_horizontal(row_frame, item)

        # 创建分隔线
        separator = ttk.Separator(self.parent, orient='horizontal')
        separator.pack(fill='x', pady=5)

        # 故障判断值 - 使用更醒目的样式
        ratio_frame = ttk.Frame(self.parent)
        ratio_frame.pack(fill='x', pady=2)
        ratio_title = ttk.Label(
            ratio_frame,
            text="故障判断值:",
            font=('Microsoft YaHei', 9, 'bold'),
            foreground='#2E86AB'
        )
        ratio_title.pack(side='left', padx=(0, 10))
        self.ratio_value = ttk.Label(
            ratio_frame,
            text="0.00%",
            font=('Microsoft YaHei', 12, 'bold'),
            foreground='green'
        )
        self.ratio_value.pack(side='left')
        self.value_labels[f"motor{self.motor_id}_excitation_current_ratio"] = self.ratio_value

        # 警告信息
        self.warning_label = ttk.Label(
            self.parent,
            text="",
            font=('Microsoft YaHei', 9, 'bold'),
            foreground='red',
            wraplength=400
        )
        self.warning_label.pack(pady=2)
        self.value_labels[f"motor{self.motor_id}_excitation_current_ratio_warning"] = self.warning_label
    
    def _create_data_item_horizontal(self, parent, item):
        """创建单个数据项 - 水平布局"""
        label_text, attr_name, unit = item
        
        # 创建数据项容器
        item_frame = ttk.Frame(parent)
        item_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        # 标签
        label = ttk.Label(
            item_frame,
            text=f"{label_text}:",
            font=('Microsoft YaHei', 8),
            foreground='#666666'
        )
        label.pack(anchor='w')
        
        # 数值
        value_label = ttk.Label(
            item_frame,
            text="0",
            font=('Microsoft YaHei', 9, 'bold'),
            foreground='#2E86AB'
        )
        value_label.pack(anchor='w')
        
        # 单位
        unit_label = ttk.Label(
            item_frame,
            text=unit,
            font=('Microsoft YaHei', 7),
            foreground='#999999'
        )
        unit_label.pack(anchor='w')
        
        # 存储值标签引用
        self.value_labels[f"motor{self.motor_id}_{attr_name}"] = value_label
    
    def format_current_value(self, value):
        """格式化电流值，小于10时乘以1000"""
        try:
            value = float(value)
            if value < 10:
                return f"{value * 1000:.1f}"
            else:
                return f"{value:.1f}"
        except (ValueError, TypeError):
            return str(value)
    
    def update_motor_values(self, motor_data):
        """更新电机数据显示"""
        logger.debug(f"更新电机 {self.motor_id} 的数据")
        
        # 更新常规数据
        for attr in ['phase_a_current', 'phase_b_current', 'phase_c_current',
                    'frequency', 'reactive_power', 'active_power',
                    'line_voltage', 'excitation_voltage', 'excitation_current']:
            value = getattr(motor_data, attr)
            # 对电流相关属性进行特殊处理
            if 'current' in attr:
                formatted_value = self.format_current_value(value)
            else:
                formatted_value = f"{value:.1f}"
            
            label_key = f"motor{self.motor_id}_{attr}"
            if label_key in self.value_labels:
                self.value_labels[label_key].config(text=formatted_value)
                logger.debug(f"更新 {label_key}: {formatted_value}")
            else:
                logger.warning(f"找不到标签 {label_key}")
        
        # 更新计算值
        calculated_current = self.format_current_value(motor_data.calculated_excitation_current)
        label_key = f"motor{self.motor_id}_calculated_excitation_current"
        if label_key in self.value_labels:
            self.value_labels[label_key].config(text=calculated_current)
            logger.debug(f"更新 {label_key}: {calculated_current}")
        
        # 更新故障判断值
        ratio = motor_data.excitation_current_ratio * 100
        ratio_text = f"{ratio:.2f}%"
        label = self.value_labels[f"motor{self.motor_id}_excitation_current_ratio"]
        warning_label = self.value_labels[f"motor{self.motor_id}_excitation_current_ratio_warning"]
        
        if abs(ratio) > 5:
            label.config(text=ratio_text, foreground="red")
            warning_label.config(text="励磁电流偏差过大！", foreground="red")
        else:
            label.config(text=ratio_text, foreground="green")
            warning_label.config(text="")
