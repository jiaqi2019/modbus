import logging
from pymodbus.client import ModbusTcpClient
from datetime import datetime
import sys
import importlib
import os
import json
import threading
import time
import asyncio
import websockets
from db.database import DatabaseManager

# 添加上级目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return (
            config['modbus']['host'],
            config['modbus']['port'],
            config['modbus']['motor_count'],
            bool(config['auto_update']['enabled']),  # 将数字转换为布尔值
            config['auto_update']['interval']
        )
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return "localhost", 5020, 12, False, 1  # 默认值

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
        self.phase_a_current = 0.0
        self.phase_b_current = 0.0
        self.phase_c_current = 0.0
        self.frequency = 0.0
        self.reactive_power = 0.0
        self.active_power = 0.0
        self.line_voltage = 0.0
        self.excitation_voltage = 0.0
        self.excitation_current = 0.0
        self.calculated_excitation_current = 0.0
        self.excitation_current_ratio = 0.0
        self.last_update = None

    def calculate_excitation(self, calc_module):
        # 准备计算所需的数据
        genmon = [
            0,  # 未使用
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
        
        # 调用计算模块
        self.calculated_excitation_current, self.excitation_current_ratio = calc_module.calculate(genmon)

    def to_dict(self):
        return {
            'motor_id': self.motor_id,
            'phase_a_current': self.phase_a_current,
            'phase_b_current': self.phase_b_current,
            'phase_c_current': self.phase_c_current,
            'frequency': self.frequency,
            'reactive_power': self.reactive_power,
            'active_power': self.active_power,
            'line_voltage': self.line_voltage,
            'excitation_voltage': self.excitation_voltage,
            'excitation_current': self.excitation_current,
            'calculated_excitation_current': self.calculated_excitation_current,
            'excitation_current_ratio': self.excitation_current_ratio,
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
            host, port, motor_count, _, _ = load_config()
            
        # 初始化指定数量的电机数据
        self.motor_count = motor_count
        self.motors = [MotorData(i+1) for i in range(motor_count)]
        self.client = ModbusTcpClient(host, port)
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager()
        
        # WebSocket服务器相关
        self.websocket_server = None
        self.websocket_clients = set()
        self.websocket_running = False
        
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
            success = self.parse_motor_data(data)
            if success:
                # 保存到数据库
                self.save_to_database()
                # 推送数据到WebSocket客户端
                self.broadcast_to_websocket_clients()
            return success
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
                motor.phase_a_current = self.to_float16(data[start_idx])
                motor.phase_b_current = self.to_float16(data[start_idx + 1])
                motor.phase_c_current = self.to_float16(data[start_idx + 2])
                
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
                module_name = f"calc.calc_{(i//2)*2+1}_{(i//2)*2+2}"
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

    def save_to_database(self):
        """保存数据到数据库"""
        try:
            self.db_manager.save_all_motors_data(self.motors)
            logger.info("数据已保存到数据库")
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {str(e)}")

    def broadcast_to_websocket_clients(self):
        """向WebSocket客户端广播数据"""
        if not self.websocket_clients:
            return
            
        # 准备数据
        data = {
            'type': 'motor_update',
            'timestamp': datetime.now().isoformat(),
            'motors': [motor.to_dict() for motor in self.motors]
        }
        
        # 广播给所有连接的客户端
        message = json.dumps(data, ensure_ascii=False)
        for client in self.websocket_clients.copy():
            try:
                asyncio.run(client.send(message))
            except Exception as e:
                logger.error(f"向WebSocket客户端发送数据失败: {str(e)}")
                self.websocket_clients.discard(client)

    def get_motors_data(self):
        """获取电机数据（供UI使用）"""
        return self.motors

    def request_data(self):
        """请求数据（UI接口兼容方法）"""
        return self.request_motor_data()

    def start_websocket_server(self, host='0.0.0.0', port=8765):
        """启动WebSocket服务器"""
        self.websocket_running = True
        self.websocket_server = asyncio.run(self._run_websocket_server(host, port))

    async def _run_websocket_server(self, host, port):
        """运行WebSocket服务器"""
        async def handle_client(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"WebSocket客户端连接，当前连接数: {len(self.websocket_clients)}")
            
            try:
                async for message in websocket:
                    # 处理客户端消息
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'ping':
                            await websocket.send(json.dumps({'type': 'pong'}))
                    except json.JSONDecodeError:
                        pass
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.discard(websocket)
                logger.info(f"WebSocket客户端断开，当前连接数: {len(self.websocket_clients)}")

        server = await websockets.serve(handle_client, host, port)
        logger.info(f"WebSocket服务器启动: ws://{host}:{port}")
        await server.wait_closed()

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

