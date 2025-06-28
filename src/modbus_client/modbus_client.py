import logging
from pymodbus.client import ModbusTcpClient
import sys
import os
import json
import time

# 添加上级目录到Python路径（必须在导入其他模块之前）
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

class ModbusClient:
    """Modbus客户端，只负责与Modbus服务器通信"""
    
    def __init__(self, host=None, port=None, motor_count=None):
        logger.info("初始化 Modbus 客户端...")
        # 如果没有提供host和port，从配置文件读取
        if host is None or port is None or motor_count is None:
            host, port, motor_count, _, _ = load_config()
            
        self.host = host
        self.port = port
        self.motor_count = motor_count
        self.client = ModbusTcpClient(host, port)
        
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

    def request_motor_data(self):
        """请求电机数据，返回原始寄存器数据"""
        try:
            # 读取保持寄存器数据 (每个电机9个浮点数，每个浮点数2个寄存器，总共18个寄存器)
            all_data = []
            # 每个电机读取18个寄存器，分12次读取
            for i in range(self.motor_count):
                start_addr = i * 18  # 每个电机的起始地址
                result = self.client.read_holding_registers(start_addr, 18)
                if result.isError():
                    logger.error(f"读取电机{i+1}数据错误: {result}")
                    return None
                all_data.extend(result.registers)
            
            # logger.info(f"收到数据: {' '.join([f'{x:04X}' for x in all_data])}")
            
            return all_data
        except Exception as e:
            logger.error(f"请求数据时出错: {str(e)}")
            return None

    def get_connection_info(self):
        """获取连接信息"""
        return {
            'host': self.host,
            'port': self.port,
            'connected': self.is_connected(),
            'motor_count': self.motor_count
        }

if __name__ == "__main__":
    pass

