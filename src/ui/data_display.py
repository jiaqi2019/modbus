import tkinter as tk
from tkinter import ttk
import logging
import json
import os

logger = logging.getLogger(__name__)

class MotorDataDisplay:
    """电机数据展示模块，负责显示电机的基本数据"""
    
    def __init__(self, parent, motor_id):
        self.parent = parent
        self.motor_id = motor_id
        self.value_labels = {}
        
        # 加载电机显示配置
        self.display_config = self.load_display_config()
        
        # 创建数据显示界面
        self.create_data_display()
    
    def load_display_config(self):
        """加载电机显示配置"""
        try:
            # 查找配置文件路径
            config_path = None
            # 先尝试在modbus_client目录下查找
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "modbus_client", "config.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "src", "modbus_client", "config.json"),
                "src/modbus_client/config.json"
            ]
            
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    config_path = abs_path
                    break
            
            if not config_path:
                logger.warning("未找到配置文件，使用默认倍数")
                return self.get_default_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            motor_config_key = f"motor{self.motor_id}"
            display_config = config.get("motor_display_config", {}).get(motor_config_key, {})
            
            if not display_config:
                logger.warning(f"未找到电机 {self.motor_id} 的显示配置，使用默认倍数")
                return self.get_default_config()
            
            logger.info(f"成功加载电机 {self.motor_id} 的显示配置")
            return display_config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认的显示配置"""
        return {
            "phase_a_current": 1.0,
            "phase_b_current": 1.0,
            "phase_c_current": 1.0,
            "frequency": 1.0,
            "reactive_power": 1.0,
            "active_power": 1.0,
            "line_voltage": 1.0,
            "excitation_voltage": 1.0,
            "excitation_current": 1.0,
            "calculated_excitation_current": 1.0,
            "excitation_current_ratio": 100.0,
            "average_excitation_current_ratio": 100.0
        }
    
    def create_data_display(self):
        """创建数据显示界面"""
        # 创建标题
        title_label = ttk.Label(
            self.parent, 
            text=f" {self.motor_id}号发电机数据", 
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
            ("无功功率", "reactive_power", "MVar"),
            ("有功功率", "active_power", "MW"),
            ("线电压", "line_voltage", "kV"),
            ("励磁电压", "excitation_voltage", "V"),
            ("励磁电流", "excitation_current", "A"),
            ("计算励磁电流", "calculated_excitation_current", "A"),
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
    
    def format_value(self, value, attr_name):
        """根据配置格式化数值"""
        try:
            value = float(value)
            multiplier = self.display_config.get(attr_name, 1.0)
            formatted_value = value * multiplier
            return f"{formatted_value:.1f}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_current_value(self, value):
        """格式化电流值（保留向后兼容性）"""
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
        
        # 更新常规数据，使用配置的倍数
        for attr in ['phase_a_current', 'phase_b_current', 'phase_c_current',
                    'frequency', 'reactive_power', 'active_power',
                    'line_voltage', 'excitation_voltage', 'excitation_current']:
            value = getattr(motor_data, attr)
            formatted_value = self.format_value(value, attr)
            
            label_key = f"motor{self.motor_id}_{attr}"
            if label_key in self.value_labels:
                self.value_labels[label_key].config(text=formatted_value)
                logger.debug(f"更新 {label_key}: {formatted_value} (倍数: {self.display_config.get(attr, 1.0)})")
            else:
                logger.warning(f"找不到标签 {label_key}")
        
        # 更新计算值，使用配置的倍数
        calculated_current = self.format_value(motor_data.calculated_excitation_current, 'calculated_excitation_current')
        label_key = f"motor{self.motor_id}_calculated_excitation_current"
        if label_key in self.value_labels:
            self.value_labels[label_key].config(text=calculated_current)
            logger.debug(f"更新 {label_key}: {calculated_current}")
        
        # 更新故障判断值（使用配置的倍数）
        ratio_multiplier = self.display_config.get('excitation_current_ratio', 100.0)
        ratio = motor_data.excitation_current_ratio * ratio_multiplier
        ratio_text = f"{ratio:.2f}%"
        dataitem_ratio_label = self.value_labels.get(f"motor{self.motor_id}_excitation_current_ratio")
        if dataitem_ratio_label:
            if abs(ratio) > 5:
                dataitem_ratio_label.config(text=ratio_text, foreground="red")
            else:
                dataitem_ratio_label.config(text=ratio_text, foreground="green")
        
        # 更新均值显示（使用配置的倍数）
        avg_ratio = getattr(motor_data, 'average_excitation_current_ratio', None)
        if avg_ratio is None:
            avg_ratio = 0.0
        avg_multiplier = self.display_config.get('average_excitation_current_ratio', 100.0)
        avg_ratio_value = avg_ratio * avg_multiplier
        avg_ratio_text = f"{avg_ratio_value:.2f}%"
        avg_label = self.value_labels.get(f"motor{self.motor_id}_average_excitation_current_ratio")
        if avg_label:
            avg_label.config(text=avg_ratio_text)
