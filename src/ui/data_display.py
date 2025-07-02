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
        title_label.pack(pady=(0, 1))

        # 创建数据容器 - 水平布局
        data_container = ttk.Frame(self.parent)
        data_container.pack(fill='x', expand=False)

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
            ("计算励磁电流", "calculated_excitation_current", "A"),
            # 恶搞：把故障判断值也加进来
            ("故障判断值", "excitation_current_ratio", "%")
        ]

        # 创建数据行 - 每行显示5个数据项
        for i in range(0, len(data_items), 5):
            row_frame = ttk.Frame(data_container)
            row_frame.pack(fill='x', pady=2)
            for j in range(5):
                if i + j < len(data_items):
                    item = data_items[i + j]
                    self._create_data_item_horizontal(row_frame, item)

        # 均值 - 居中放大显示，紧跟data_items下方
        avg_ratio_frame = ttk.Frame(self.parent)
        avg_ratio_frame.pack(pady= 30)
        avg_ratio_title = ttk.Label(
            avg_ratio_frame,
            text="均值:",
            font=('Microsoft YaHei', 16, 'bold'),
            foreground='#1ABC9C',
            anchor='center',
            justify='center'
        )
        avg_ratio_title.pack(side='top')
        self.avg_ratio_value = ttk.Label(
            avg_ratio_frame,
            text="0.00%",
            font=('Microsoft YaHei', 22, 'bold'),
            foreground='#1ABC9C',
            anchor='center',
            justify='center'
        )
        self.avg_ratio_value.pack(side='left', padx=(8, 0))
        self.value_labels[f"motor{self.motor_id}_average_excitation_current_ratio"] = self.avg_ratio_value
    
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
        # 对于excitation_current_ratio，key要和data_items区分
        if attr_name == "excitation_current_ratio":
            self.value_labels[f"motor{self.motor_id}_excitation_current_ratio"] = value_label
        else:
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
        
        # 更新故障判断值（大号标签）
        ratio = motor_data.excitation_current_ratio * 100
        ratio_text = f"{ratio:.2f}%"
        dataitem_ratio_label = self.value_labels.get(f"motor{self.motor_id}_excitation_current_ratio")
        if dataitem_ratio_label:
            if abs(ratio) > 5:
                dataitem_ratio_label.config(text=ratio_text, foreground="red")
            else:
                dataitem_ratio_label.config(text=ratio_text, foreground="green")
        # 新增：更新均值显示
        avg_ratio = getattr(motor_data, 'average_excitation_current_ratio', None)
        if avg_ratio is None:
            avg_ratio = 0.0
        avg_ratio_text = f"{avg_ratio * 100:.2f}%"
        avg_label = self.value_labels.get(f"motor{self.motor_id}_average_excitation_current_ratio")
        if avg_label:
            avg_label.config(text=avg_ratio_text)
