import logging
from pymodbus.client import ModbusTcpClient
from datetime import datetime
import threading
import sys
import importlib
import os
import json

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config['modbus']['host'], config['modbus']['port'], config['modbus']['motor_count']
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return "localhost", 5020, 12  # 默认值

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MotorData:
    def __init__(self, motor_id):
        self.motor_id = motor_id
        self.phase_a_current = 0  # A相电流
        self.phase_b_current = 0  # B相电流
        self.phase_c_current = 0  # C相电流
        self.frequency = 0        # 频率
        self.reactive_power = 0   # 无功功率
        self.active_power = 0     # 有功功率
        self.line_voltage = 0     # AB相线电压
        self.excitation_voltage = 0  # 励磁电压
        self.excitation_current = 0  # 励磁电流
        self.last_update = None
        self.calculated_excitation_current = 0  # 计算得到的励磁电流
        self.excitation_current_ratio = 0  # 励磁电流比值

    def calculate_excitation(self, calc_module):
        # 准备计算所需的数据
        genmon = [            0,  # 未使用
            0,  # 未使用
            0,  # 未使用
            0,  # 未使用
            0,  # 未使用
            self.reactive_power,  # 无功功率
            self.active_power,    # 有功功率
            self.line_voltage * 1000,    # 线电压
            0,  # 未使用
            self.excitation_current  # 实际励磁电流
        ]
        
        logger.info(f"电机 {genmon} 计算开始:")
        # 计算励磁电流和比值
        self.calculated_excitation_current, self.excitation_current_ratio = calc_module.calculate(genmon)
        logger.info(f"电机 {self.motor_id} 计算完成:")
        logger.info(f"计算得到的励磁电流: {self.calculated_excitation_current:.2f}")
        logger.info(f"励磁电流比值: {self.excitation_current_ratio*100:.2f}%")

    def to_dict(self):
        return {
            'phase_a_current': self.phase_a_current,
            'phase_b_current': self.phase_b_current,
            'phase_c_current': self.phase_c_current,
            'frequency': self.frequency,
            'reactive_power': self.reactive_power,
            'active_power': self.active_power,
            'line_voltage': self.line_voltage,
            'excitation_voltage': self.excitation_voltage,
            'excitation_current': self.excitation_current,
            'last_update': self.last_update
        }

    def __str__(self):
        return f"电机 {self.motor_id} 数据 (更新时间: {self.last_update}):\n" + \
               f"A相电流: {self.phase_a_current} (原始值)\n" + \
               f"B相电流: {self.phase_b_current} (原始值)\n" + \
               f"C相电流: {self.phase_c_current} (原始值)\n" + \
               f"频率: {self.frequency} (原始值)\n" + \
               f"无功功率: {self.reactive_power} (原始值)\n" + \
               f"有功功率: {self.active_power} (原始值)\n" + \
               f"AB相线电压: {self.line_voltage} (原始值)\n" + \
               f"励磁电压: {self.excitation_voltage} (原始值)\n" + \
               f"励磁电流: {self.excitation_current} (原始值)\n" + \
               f"计算得到的励磁电流: {self.calculated_excitation_current:.2f}\n" + \
               f"励磁电流比值: {self.excitation_current_ratio*100:.2f}%"

class ModbusClient:
    def __init__(self, host=None, port=None, motor_count=None):
        logger.info("初始化 Modbus 客户端...")
        # 如果没有提供host和port，从配置文件读取
        if host is None or port is None or motor_count is None:
            host, port, motor_count = load_config()
            
        # 初始化指定数量的电机数据
        self.motor_count = motor_count
        self.motors = [MotorData(i+1) for i in range(motor_count)]
        self.client = ModbusTcpClient(host, port)
        
        # 创建电机数据日志目录
        self.data_log_dir = "motor_data_logs"
        if not os.path.exists(self.data_log_dir):
            os.makedirs(self.data_log_dir)
        
        # 创建当天的日志文件
        self.current_log_file = os.path.join(
            self.data_log_dir, 
            f"motor_data_{datetime.now().strftime('%Y%m%d')}.json"
        )
        logger.info(f"Modbus 客户端初始化完成，监控 {motor_count} 台电机")

    def connect(self):
        """连接到Modbus服务器"""
        return self.client.connect()

    def is_connected(self):
        """检查是否已连接到服务器"""
        return self.client.connected

    def disconnect(self):
        """断开与Modbus服务器的连接"""
        self.client.close()

    def to_signed_int(self, value):
        return value - 65536 if value > 32767 else value

    def to_float16(self, value):
        """将2字节数据转换为float16格式"""
        # 将16位整数转换为二进制字符串
        binary = format(value, '016b')
        
        # 解析IEEE 754 half-precision格式
        sign = -1 if binary[0] == '1' else 1
        exponent = int(binary[1:6], 2)
        fraction = int(binary[6:], 2)
        
        # 处理特殊情况
        if exponent == 0:
            if fraction == 0:
                return 0.0
            else:
                # 非规格化数
                return sign * (fraction / 1024.0) * (2 ** -14)
        elif exponent == 31:
            if fraction == 0:
                return float('inf') if sign == 1 else float('-inf')
            else:
                return float('nan')
        
        # 正常情况
        return sign * (1.0 + fraction / 1024.0) * (2 ** (exponent - 15))

    def request_motor_data(self):
        """请求电机数据"""
        try:
            # 读取保持寄存器数据 (每个电机9个寄存器)
            register_count = self.motor_count * 9
            result = self.client.read_holding_registers(0, register_count)
            if result.isError():
                logger.error(f"读取数据错误: {result}")
                return False

            data = result.registers
            logger.info(f"收到数据: {' '.join([f'{x:04X}' for x in data])}")
            
            # 解析数据
            return self.parse_motor_data(data)
        except Exception as e:
            logger.error(f"请求数据时出错: {str(e)}")
            return False

    def parse_motor_data(self, data):
        try:
            logger.info(f"开始解析数据，原始数据: {' '.join([f'{x:04X}' for x in data])}")

            # 解析所有电机数据
            for i in range(self.motor_count):
                start_idx = i * 9
                motor = self.motors[i]
                
                logger.info(f"开始解析电机{i+1}数据...")
                
                # 处理电流数据：如果小于10则乘以1000
                phase_a_raw = self.to_float16(data[start_idx])
                motor.phase_a_current = phase_a_raw * 1000 if phase_a_raw < 10 else phase_a_raw
                
                phase_b_raw = self.to_float16(data[start_idx + 1])
                motor.phase_b_current = phase_b_raw * 1000 if phase_b_raw < 10 else phase_b_raw
                
                phase_c_raw = self.to_float16(data[start_idx + 2])
                motor.phase_c_current = phase_c_raw * 1000 if phase_c_raw < 10 else phase_c_raw
                
                motor.frequency = self.to_float16(data[start_idx + 3])
                motor.reactive_power = self.to_float16(data[start_idx + 4])
                motor.active_power = self.to_float16(data[start_idx + 5])
                motor.line_voltage = self.to_float16(data[start_idx + 6])
                motor.excitation_voltage = self.to_float16(data[start_idx + 7])
                
                # 处理励磁电流：如果小于10则乘以1000
                excitation_current_raw = self.to_float16(data[start_idx + 8])
                motor.excitation_current = excitation_current_raw * 1000 if excitation_current_raw < 10 else excitation_current_raw
                
                motor.last_update = datetime.now()
                
                # 根据电机编号选择对应的计算模块
                module_name = f"calc_{(i//2)*2+1}_{(i//2)*2+2}"
                calc_module = importlib.import_module(module_name)
                # 计算励磁电流
                motor.calculate_excitation(calc_module)
                logger.info(f"电机{i+1}数据解析完成: {motor}")

            # 打印解析后的数据
            logger.info("\n=== 电机数据更新 ===")
            for motor in self.motors:
                logger.info(str(motor))
            logger.info("==================\n")

            # 保存数据到日志文件
            self.save_data_to_log()

            return True
        except Exception as error:
            logger.error(f"数据解析错误: {str(error)}")
            return False

    def save_data_to_log(self):
        """保存当前数据到日志文件"""
        try:
            data_to_save = {
                'timestamp': datetime.now().isoformat(),
                'motors': {}
            }
            
            # 保存所有电机数据
            for motor in self.motors:
                data_to_save['motors'][f'motor{motor.motor_id}'] = {
                    'reactive_power': f"{motor.reactive_power} kVar",
                    'active_power': f"{motor.active_power} kW",
                    'line_voltage': f"{motor.line_voltage} V",
                    'excitation_current': f"{motor.excitation_current} A",
                    'calculated_excitation_current': f"{motor.calculated_excitation_current:.2f} A",
                    'excitation_current_ratio': f"{motor.excitation_current_ratio*100:.2f}%"
                }
            
            # 如果文件不存在，创建新文件
            if not os.path.exists(self.current_log_file):
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    json.dump([data_to_save], f, ensure_ascii=False, indent=2)
            else:
                # 读取现有数据
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
                
                # 添加新数据
                existing_data.append(data_to_save)
                
                # 保存更新后的数据
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                    
            logger.info(f"数据已保存到日志文件: {self.current_log_file}")
                    
        except Exception as e:
            logger.error(f"保存数据到日志文件时出错: {str(e)}")

if __name__ == "__main__":
    pass

