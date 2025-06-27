import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from modbus_client import ModbusClient

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return (
            config['modbus']['host'],
            config['modbus']['port'],
            config['modbus']['motor_count'],
            config['auto_update']['enabled'],
            config['auto_update']['interval']
        )
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return "localhost", 5020, 12, False, 1  # 默认值

class MotorMonitorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("电机监控系统")
        self.root.geometry("1200x900")  # 增加初始高度
        self.root.minsize(1000, 900)    # 设置最小尺寸，确保所有控件可见
        
        # 设置样式
        style = ttk.Style()
        style.configure("TNotebook", padding=10)
        style.configure("TNotebook.Tab", padding=[10, 5], font=('Arial', 10))
        style.configure("TFrame", padding=10)
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10))
        
        # 从配置文件加载设置
        host, port, motor_count, auto_update_enabled, update_interval = load_config()
        print(f"从配置文件加载的自动更新状态: {auto_update_enabled}")  # 调试信息
        
        # 保存连接参数供重连使用
        self.connection_params = (host, port, motor_count)
        
        # 设置自动更新状态和间隔
        self.auto_update = auto_update_enabled  # 使用配置文件中的值
        self.update_interval = update_interval
        self.update_thread = None
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill='both')
        
        # 初始化值标签字典
        self.value_labels = {}
        
        # 根据配置创建对应数量的电机标签页，每页显示两个电机
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
        
        # 创建控制按钮
        self.create_control_buttons()
        
        # 初始化Modbus客户端
        self.client = None
        self.initialize_connection()

    def initialize_connection(self):
        """初始化或重新初始化连接"""
        try:
            if self.client:
                self.client.disconnect()
            
            host, port, motor_count = self.connection_params
            self.client = ModbusClient(host, port, motor_count)
            if not self.client.connect():
                self.show_connection_error()
            else:
                self.update_connection_status("已连接")
                # 连接成功后隐藏重连按钮
                if hasattr(self, 'reconnect_button'):
                    self.reconnect_button.pack_forget()
        except Exception as e:
            self.show_connection_error(str(e))

    def show_connection_error(self, error_msg="无法连接到Modbus服务器"):
        """显示连接错误并添加重连按钮"""
        messagebox.showerror("连接错误", error_msg)
        self.update_connection_status("未连接")
        
        # 如果重连按钮不存在，创建它
        if not hasattr(self, 'reconnect_button'):
            self.reconnect_button = ttk.Button(
                self.status_label.master,
                text="重新连接",
                command=self.start_reconnect,
                width=15
            )
            self.reconnect_button.pack(side='right', padx=10)
        else:
            self.reconnect_button.pack(side='right', padx=10)

    def start_reconnect(self):
        """开始重新连接过程"""
        # 禁用重连按钮并显示加载状态
        self.reconnect_button.config(text="连接中...", state='disabled')
        self.root.update()  # 立即更新UI
        
        # 在新线程中执行连接
        threading.Thread(target=self._reconnect_thread, daemon=True).start()

    def _reconnect_thread(self):
        """在新线程中执行重连"""
        try:
            self.initialize_connection()
        finally:
            # 恢复按钮状态
            self.root.after(0, self._reset_reconnect_button)

    def _reset_reconnect_button(self):
        """重置重连按钮状态"""
        if hasattr(self, 'reconnect_button'):
            self.reconnect_button.config(text="重新连接", state='normal')

    def update_connection_status(self, status):
        """更新连接状态"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"状态: {status}")
            if status == "已连接" and hasattr(self, 'reconnect_button'):
                self.reconnect_button.pack_forget()

    def create_control_buttons(self):
        """创建控制按钮"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 左侧按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='left', padx=10)
        
        # 请求数据按钮
        self.request_button = ttk.Button(
            button_frame, 
            text="请求数据", 
            command=self.request_data,
            width=15
        )
        self.request_button.pack(side='left', padx=5)
        
        # 自动更新按钮和间隔设置（仅在配置启用时显示）
        print(f"配置的自动更新状态: {self.auto_update}")  # 调试信息
        if self.auto_update:
            # 自动更新按钮
            self.auto_update_button = ttk.Button(
                button_frame,
                text="开始自动更新",
                command=self.toggle_auto_update,
                width=15
            )
            self.auto_update_button.pack(side='left', padx=5)
            
            # 更新间隔设置
            interval_frame = ttk.Frame(button_frame)
            interval_frame.pack(side='left', padx=10)
            
            ttk.Label(interval_frame, text="更新间隔(秒):", font=('Arial', 10)).pack(side='left')
            self.interval_var = tk.StringVar(value=str(self.update_interval))
            interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=8)
            interval_entry.pack(side='left', padx=5)
        
        # 右侧状态标签
        self.status_label = ttk.Label(control_frame, text="状态: 未连接", font=('Arial', 10))
        self.status_label.pack(side='right', padx=10)

    def create_motor_display(self, parent, motor_id):
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

    def request_data(self):
        """请求数据并更新显示"""
        try:
            if not self.client or not self.client.is_connected():
                self.show_connection_error("未连接到服务器")
                return
                
            if self.client.request_motor_data():
                self.update_display()
                self.status_label.config(text="状态: 数据已更新")
            else:
                self.status_label.config(text="状态: 数据更新失败")
        except Exception as e:
            self.status_label.config(text=f"状态: 错误 - {str(e)}")
            self.show_connection_error(f"请求数据失败: {str(e)}")

    def update_display(self):
        """更新显示的数据"""
        # 更新所有电机数据
        for i, motor in enumerate(self.client.motors):
            self.update_motor_values(i+1, motor)

    def update_motor_values(self, motor_id, motor_data):
        # 更新常规数据
        for attr in ['phase_a_current', 'phase_b_current', 'phase_c_current',
                    'frequency', 'reactive_power', 'active_power',
                    'line_voltage', 'excitation_voltage', 'excitation_current']:
            value = getattr(motor_data, attr)
            self.value_labels[f"motor{motor_id}_{attr}"].config(text=str(value))
        # 更新计算值，保留4位小数
        self.value_labels[f"motor{motor_id}_calculated_excitation_current"].config(
            text=f"{motor_data.calculated_excitation_current:.4f}")
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

    def toggle_auto_update(self):
        """切换自动更新状态"""
        self.auto_update = not self.auto_update
        if self.auto_update:
            try:
                # 更新间隔时间
                new_interval = float(self.interval_var.get())
                if new_interval < 0.1:  # 最小间隔0.1秒
                    raise ValueError("更新间隔不能小于0.1秒")
                self.update_interval = new_interval
                
                self.auto_update_button.config(text="停止自动更新")
                self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
                self.update_thread.start()
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                self.auto_update = False
                self.interval_var.set(str(self.update_interval))
        else:
            self.auto_update_button.config(text="开始自动更新")
            if self.update_thread:
                self.update_thread = None

    def auto_update_loop(self):
        """自动更新循环"""
        while self.auto_update:
            self.request_data()
            time.sleep(self.update_interval)  # 使用配置的更新间隔

    def run(self):
        """运行UI"""
        try:
            self.root.mainloop()
        finally:
            # 清理资源
            self.auto_update = False
            if self.client:
                self.client.disconnect()

def main():
    ui = MotorMonitorUI()
    ui.run()

if __name__ == "__main__":
    main() 