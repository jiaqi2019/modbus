import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

class MotorMonitorUI:
    def __init__(self, title="电机监控系统", data_provider=None):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1200x900")
        self.root.minsize(1000, 900)
        
        # 数据提供者（可以是modbus客户端或websocket客户端）
        self.data_provider = data_provider
        
        # 设置样式
        style = ttk.Style()
        style.configure("TNotebook", padding=10)
        style.configure("TNotebook.Tab", padding=[10, 5], font=('Arial', 10))
        style.configure("TFrame", padding=10)
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10))
        
        # 初始化UI组件
        self.init_ui()
        
        # 自动更新相关
        self.auto_update = False
        self.update_interval = 1
        self.update_thread = None
        
    def init_ui(self):
        """初始化UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill='both')
        
        # 初始化值标签字典
        self.value_labels = {}
        
        # 创建电机显示页面（默认12台电机）
        self.create_motor_pages(12)
        
        # 创建控制按钮
        self.create_control_buttons()
        
    def create_motor_pages(self, motor_count):
        """创建电机显示页面"""
        for i in range(0, motor_count, 2):
            tab_frame = ttk.Frame(self.notebook)
            tab_title = f'电机{i+1}-{i+2}' if i+1 < motor_count else f'电机{i+1}'
            self.notebook.add(tab_frame, text=tab_title)
            
            # 创建第一个电机的显示
            motor1_frame = ttk.Frame(tab_frame)
            motor1_frame.pack(fill='x', pady=10)
            ttk.Label(motor1_frame, text=f"电机 {i+1}", font=('Arial', 14, 'bold')).pack(pady=5)
            self.create_motor_display(motor1_frame, i+1)
            
            # 如果还有第二个电机，创建第二个电机的显示
            if i+1 < motor_count:
                separator = ttk.Separator(tab_frame, orient='horizontal')
                separator.pack(fill='x', pady=10)
                
                motor2_frame = ttk.Frame(tab_frame)
                motor2_frame.pack(fill='x', pady=10)
                ttk.Label(motor2_frame, text=f"电机 {i+2}", font=('Arial', 14, 'bold')).pack(pady=5)
                self.create_motor_display(motor2_frame, i+2)
    
    def create_motor_display(self, parent, motor_id):
        """创建单个电机的显示界面"""
        # 2列5行常规数据
        labels = [
            ("A相电流 (A)", "phase_a_current"),
            ("B相电流 (A)", "phase_b_current"),
            ("C相电流 (A)", "phase_c_current"),
            ("频率 (Hz)", "frequency"),
            ("无功功率 (kVar)", "reactive_power"),
            ("有功功率 (kW)", "active_power"),
            ("AB相线电压 (kV)", "line_voltage"),
            ("励磁电压 (V)", "excitation_voltage"),
            ("励磁电流 (A)", "excitation_current"),
            ("计算得到的励磁电流 (A)", "calculated_excitation_current")
        ]
        table_labels = [
            labels[0], labels[5],
            labels[1], labels[6],
            labels[2], labels[7],
            labels[3], labels[8],
            labels[4], labels[9]
        ]
        for row in range(5):
            frame = ttk.Frame(parent)
            frame.pack(fill='x', pady=8)
            # 左列
            l_label, l_attr = table_labels[row*2]
            label_left = ttk.Label(frame, text=l_label, width=25, font=('Arial', 16, 'bold'))
            label_left.pack(side='left', padx=5)
            value_left = ttk.Label(frame, text="0", width=15, font=('Arial', 16, 'bold'))
            value_left.pack(side='left', padx=5)
            self.value_labels[f"motor{motor_id}_{l_attr}"] = value_left
            # 右列
            r_label, r_attr = table_labels[row*2+1]
            label_right = ttk.Label(frame, text=r_label, width=25, font=('Arial', 16, 'bold'))
            label_right.pack(side='left', padx=40)
            value_right = ttk.Label(frame, text="0", width=15, font=('Arial', 16, 'bold'))
            value_right.pack(side='left', padx=5)
            self.value_labels[f"motor{motor_id}_{r_attr}"] = value_right
        
        # 故障判断值单独一行，居中
        ratio_label = tk.Label(
            parent,
            text="故障判断值 (%) : 0.00%",
            font=("Arial", 18, "bold"),
            fg="green",
            bg=self.root.cget("bg"),
            anchor="center",
            justify="center"
        )
        ratio_label.pack(fill='x', pady=(16,2))
        self.value_labels[f"motor{motor_id}_excitation_current_ratio"] = ratio_label
        
        # 警告信息单独一行，居中
        warning_label = tk.Label(
            parent,
            text="",
            font=("Arial", 18, "bold"),
            fg="red",
            bg=self.root.cget("bg"),
            anchor="center",
            justify="center"
        )
        warning_label.pack(fill='x', pady=2)
        self.value_labels[f"motor{motor_id}_excitation_current_ratio_warning"] = warning_label
    
    def create_control_buttons(self):
        """创建控制按钮"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 左侧按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='left', padx=10)
        
        # 自动更新按钮
        self.auto_update_button = ttk.Button(
            button_frame,
            text="开始自动更新",
            command=self.toggle_auto_update,
            width=15
        )
        self.auto_update_button.pack(side='left', padx=5)
        
        # 右侧状态标签
        self.status_label = ttk.Label(control_frame, text="状态: 未连接", font=('Arial', 10))
        self.status_label.pack(side='right', padx=10)
    
    def format_current_value(self, value):
        """格式化电流值，小于10时乘以1000"""
        try:
            value = float(value)
            if value < 10:
                return f"{value * 1000:.2f}"
            else:
                return f"{value:.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def update_motor_values(self, motor_id, motor_data):
        """更新电机数据显示"""
        # 更新常规数据
        for attr in ['phase_a_current', 'phase_b_current', 'phase_c_current',
                    'frequency', 'reactive_power', 'active_power',
                    'line_voltage', 'excitation_voltage', 'excitation_current']:
            value = getattr(motor_data, attr)
            # 对电流相关属性进行特殊处理
            if 'current' in attr:
                formatted_value = self.format_current_value(value)
            else:
                formatted_value = str(value)
            self.value_labels[f"motor{motor_id}_{attr}"].config(text=formatted_value)
        
        # 更新计算值
        calculated_current = self.format_current_value(motor_data.calculated_excitation_current)
        self.value_labels[f"motor{motor_id}_calculated_excitation_current"].config(
            text=calculated_current)
        
        # 更新故障判断值
        ratio = motor_data.excitation_current_ratio * 100
        ratio_text = f"故障判断值 (%) : {ratio:.2f}%"
        label = self.value_labels[f"motor{motor_id}_excitation_current_ratio"]
        warning_label = self.value_labels[f"motor{motor_id}_excitation_current_ratio_warning"]
        if abs(ratio) > 5:
            label.config(text=ratio_text, fg="red")
            warning_label.config(text="警告：励磁电流偏差过大！", fg="red")
        else:
            label.config(text=ratio_text, fg="green")
            warning_label.config(text="")
    
    def update_display(self, motors_data):
        """更新显示的数据"""
        # 更新所有电机数据
        for i, motor in enumerate(motors_data):
            self.update_motor_values(i+1, motor)
    
    def request_data(self):
        """请求数据并更新显示"""
        if self.data_provider:
            try:
                if self.data_provider.request_data():
                    self.update_display(self.data_provider.get_motors_data())
                    self.status_label.config(text="状态: 数据已更新")
                else:
                    self.status_label.config(text="状态: 数据更新失败")
            except Exception as e:
                self.status_label.config(text=f"状态: 错误 - {str(e)}")
        else:
            self.status_label.config(text="状态: 无数据提供者")
    
    def toggle_auto_update(self):
        """切换自动更新状态"""
        if self.auto_update:
            self.stop_auto_update()
        else:
            self.start_auto_update()
    
    def start_auto_update(self):
        """开始自动更新"""
        if not self.data_provider:
            messagebox.showerror("错误", "无数据提供者")
            return
            
        self.auto_update = True
        self.auto_update_button.config(text="停止自动更新")
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()
        self.status_label.config(text="状态: 自动更新已启动")
    
    def stop_auto_update(self):
        """停止自动更新"""
        self.auto_update = False
        self.auto_update_button.config(text="开始自动更新")
        self.status_label.config(text="状态: 自动更新已停止")
    
    def auto_update_loop(self):
        """自动更新循环"""
        while self.auto_update:
            try:
                if self.data_provider and self.data_provider.request_data():
                    # 在主线程中更新UI
                    self.root.after(0, lambda: self.update_display(self.data_provider.get_motors_data()))
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"自动更新循环错误: {str(e)}")
                time.sleep(self.update_interval)
    
    def update_connection_status(self, status):
        """更新连接状态"""
        self.status_label.config(text=f"状态: {status}")
    
    def run(self):
        """运行UI"""
        try:
            self.root.mainloop()
        finally:
            # 清理资源
            self.stop_auto_update()
            if self.data_provider:
                self.data_provider.disconnect() 