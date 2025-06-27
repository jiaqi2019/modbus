import threading
import sys
import time
import random
import struct
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

class ModbusServer:
    def __init__(self, host="localhost", port=5020):
        self.host = host
        self.port = port
        
        # 初始化寄存器数据 (12个电机，每个9个浮点数，每个浮点数2个寄存器，总共216个寄存器)
        self.registers = [0] * 216
        
        # 设置初始电机数据 - 使用更合理的数值
        motor_data = [
            # 电机1: A相电流, B相电流, C相电流, 频率, 无功功率, 有功功率, 线电压, 励磁电压, 励磁电流
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机2
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0],
            # 电机3
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机4
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0],
            # 电机5
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机6
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0],
            # 电机7
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机8
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0],
            # 电机9
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机10
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0],
            # 电机11
            [1201.0, 1202.0, 1203.0, 50.0, -100.0, 200.0, 20.0, 400.0, 2000.0],
            # 电机12
            [1501.0, 1502.0, 1503.0, 50.0, 100.0, 300.0, 26.0, 440.0, 3000.0]
        ]
        
        # 将电机数据写入寄存器
        for i, motor in enumerate(motor_data):
            start_idx = i * 18  # 每个电机需要18个寄存器（9个浮点数 * 2个寄存器）
            for j, value in enumerate(motor):
                reg_idx = start_idx + (j * 2)
                high, low = self.float_to_registers(value)
                self.registers[reg_idx] = high
                self.registers[reg_idx + 1] = low
        
        # 创建数据存储
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*200),  # 离散输入
            co=ModbusSequentialDataBlock(0, [0]*200),  # 线圈
            hr=ModbusSequentialDataBlock(0, self.registers),  # 保持寄存器
            ir=ModbusSequentialDataBlock(0, [0]*200)   # 输入寄存器
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)
        
        # 启动数据更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self._update_data)
        self.update_thread.daemon = True

    def start(self):
        """启动服务器"""
        print(f"启动 Modbus 服务器在 {self.host}:{self.port}")
        print(f"总共 {len(self.registers)} 个寄存器")
        self.update_thread.start()
        StartTcpServer(context=self.context, address=(self.host, self.port))

    def stop(self):
        """停止服务器"""
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()
        print("Modbus 服务器已停止")

    def _update_data(self):
        """定期更新模拟数据"""
        while self.running:
            try:
                # 更新所有电机数据
                for i in range(12):
                    start_idx = i * 18  # 每个电机18个寄存器
                    
                    def generate_float_value(base, variation=0.1):
                        """生成带随机变化的浮点数"""
                        value = base + random.uniform(-base * variation, base * variation)
                        # 确保值在合理范围内
                        if abs(value) > 1e6:  # 如果值太大，重置为基准值
                            value = base
                        return value
                    
                    # 生成随机数据
                    if i % 2 == 0:  # 偶数电机
                        base_values = [
                            generate_float_value(1201.0),  # A相电流
                            generate_float_value(1202.0),  # B相电流
                            generate_float_value(1203.0),  # C相电流
                            generate_float_value(50.0),    # 频率
                            generate_float_value(-100.0),  # 无功功率
                            generate_float_value(200.0),   # 有功功率
                            generate_float_value(20.0),    # AB相线电压
                            generate_float_value(400.0),   # 励磁电压
                            generate_float_value(2000.0),  # 励磁电流
                        ]
                    else:  # 奇数电机
                        base_values = [
                            generate_float_value(1501.0),  # A相电流
                            generate_float_value(1502.0),  # B相电流
                            generate_float_value(1503.0),  # C相电流
                            generate_float_value(50.0),    # 频率
                            generate_float_value(100.0),   # 无功功率
                            generate_float_value(300.0),   # 有功功率
                            generate_float_value(26.0),    # AB相线电压
                            generate_float_value(440.0),   # 励磁电压
                            generate_float_value(3000.0),  # 励磁电流
                        ]
                    
                    # 将浮点数值转换为寄存器值并写入
                    for j, value in enumerate(base_values):
                        reg_idx = start_idx + (j * 2)
                        high, low = self.float_to_registers(value)
                        self.store.setValues(3, reg_idx, [high, low])

                time.sleep(1)  # 每秒更新一次数据

            except Exception as e:
                print(f"更新数据时出错: {str(e)}")
                time.sleep(1)

    def float_to_registers(self, value):
        """将浮点数转换为两个16位寄存器值"""
        try:
            # 确保值是有效的浮点数
            if not isinstance(value, (int, float)) or abs(value) > 1e6:
                value = 0.0
            
            packed = struct.pack('!f', float(value))
            return struct.unpack('!HH', packed)
        except Exception as e:
            print(f"转换浮点数 {value} 时出错: {str(e)}")
            return (0, 0)

def main():
    try:
        server = ModbusServer()
        server.start()
    except KeyboardInterrupt:
        print("收到停止信号")
        server.stop()
    except Exception as e:
        print(f"服务器错误: {str(e)}")

if __name__ == "__main__":
    main() 