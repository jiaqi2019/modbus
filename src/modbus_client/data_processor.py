import sys
import os
import importlib
import logging
import struct
from datetime import datetime
from dataclasses import dataclass
from typing import List

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

@dataclass
class MotorData:
    """电机数据类"""
    motor_id: int
    phase_a_current: float = 0.0
    phase_b_current: float = 0.0
    phase_c_current: float = 0.0
    frequency: float = 0.0
    reactive_power: float = 0.0
    active_power: float = 0.0
    line_voltage: float = 0.0
    excitation_voltage: float = 0.0
    excitation_current: float = 0.0
    calculated_excitation_current: float = 0.0
    excitation_current_ratio: float = 0.0
    last_update: datetime = None
    
    def to_dict(self):
        """转换为字典格式"""
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
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

    def calculate_excitation(self, calc_module):
        """使用计算模块计算励磁电流"""
        try:
            # 准备数据列表，按照calc模块期望的格式
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
            
            # logger.info(f"电机 {self.motor_id} 计算开始: {genmon}")
            # 计算励磁电流和比值
            calculated_current, ratio = calc_module.calculate(genmon)
            
            self.calculated_excitation_current = calculated_current
            self.excitation_current_ratio = ratio
            
            # logger.info(f"电机 {self.motor_id} 计算完成:")
            # logger.info(f"计算得到的励磁电流: {calculated_current:.2f}")
            # logger.info(f"励磁电流比值: {ratio*100:.2f}%")
            
        except Exception as e:
            logger.error(f"电机 {self.motor_id} 励磁电流计算失败: {str(e)}")
            self.calculated_excitation_current = 0.0
            self.excitation_current_ratio = 0.0

    def __str__(self):
        return f"电机 {self.motor_id} 数据 (更新时间: {self.last_update}):\n" + \
               f"A相电流: {self.phase_a_current:.4f} (原始值)\n" + \
               f"B相电流: {self.phase_b_current:.4f} (原始值)\n" + \
               f"C相电流: {self.phase_c_current:.4f} (原始值)\n" + \
               f"频率: {self.frequency:.4f} (原始值)\n" + \
               f"无功功率: {self.reactive_power:.4f} (原始值)\n" + \
               f"有功功率: {self.active_power:.4f} (原始值)\n" + \
               f"AB相线电压: {self.line_voltage:.4f} (原始值)\n" + \
               f"励磁电压: {self.excitation_voltage:.4f} (原始值)\n" + \
               f"励磁电流: {self.excitation_current:.4f} (原始值)\n" + \
               f"计算得到的励磁电流: {self.calculated_excitation_current:.4f}\n" + \
               f"励磁电流比值: {self.excitation_current_ratio*100:.4f}%"

class DataProcessor:
    """数据处理器，负责处理Modbus原始数据"""
    
    def __init__(self, motor_count=12):
        self.motor_count = motor_count
        self.motors = [MotorData(i+1) for i in range(motor_count)]
        # logger.info(f"数据处理器初始化完成，支持 {motor_count} 台电机")
    
    def to_signed_int(self, value):
        """将16位寄存器值转换为有符号整数"""
        return value - 65536 if value > 32767 else value
    
    def to_float(self, high, low):
        """将两个16位寄存器转换为32位浮点数"""
        # 将两个16位值组合成32位值
        combined = (high << 16) | low
        # 使用struct模块将32位值转换为浮点数，并保留4位小数
        return round(struct.unpack('!f', struct.pack('!I', combined))[0], 4)
    
    def to_float16(self, value):
        """将16位寄存器值转换为浮点数"""
        try:
            # 处理负数（16位有符号整数）
            if value > 32767:
                value = value - 65536
            
            # 转换为浮点数
            return float(value)
        except Exception as e:
            logger.error(f"转换寄存器值 {value} 失败: {str(e)}")
            return 0.0
    
    def parse_motor_data(self, data):
        """解析电机数据，使用1.py中的逻辑"""
        try:
            if len(data) < self.motor_count * 18:
                logger.error(f"数据长度不足: 期望 {self.motor_count * 18} 个寄存器，实际收到 {len(data)} 个")
                return False

            # logger.info(f"开始解析数据，原始数据: {' '.join([f'{x:04X}' for x in data])}")

            # 解析所有电机数据
            for i in range(self.motor_count):
                start_idx = i * 18  # 每个电机18个寄存器
                motor = self.motors[i]
                
                try:
                    # logger.info(f"开始解析电机{i+1}数据...")
                    # 每两个寄存器组合成一个浮点数
                    motor.phase_a_current = self.to_float(data[start_idx], data[start_idx + 1])
                    motor.phase_b_current = self.to_float(data[start_idx + 2], data[start_idx + 3])
                    motor.phase_c_current = self.to_float(data[start_idx + 4], data[start_idx + 5])
                    motor.frequency = self.to_float(data[start_idx + 6], data[start_idx + 7])
                    motor.reactive_power = self.to_float(data[start_idx + 8], data[start_idx + 9])
                    motor.active_power = self.to_float(data[start_idx + 10], data[start_idx + 11])
                    motor.line_voltage = self.to_float(data[start_idx + 12], data[start_idx + 13])
                    motor.excitation_voltage = self.to_float(data[start_idx + 14], data[start_idx + 15])
                    motor.excitation_current = self.to_float(data[start_idx + 16], data[start_idx + 17])
                    motor.last_update = datetime.now()
                    
                    # 根据电机编号选择对应的计算模块
                    module_name = f"calc.calc_{(i//2)*2+1}_{(i//2)*2+2}"
                    try:
                        calc_module = importlib.import_module(module_name)
                        # 计算励磁电流
                        motor.calculate_excitation(calc_module)
                    except ImportError as e:
                        # 尝试直接导入
                        try:
                            import calc.calc_1_2 as test_module
                        except Exception as test_e:
                            logger.error(f"测试导入失败: {str(test_e)}")
                    except Exception as e:
                        logger.error(f"计算电机{i+1}励磁电流失败: {str(e)}")
                        import traceback
                        logger.error(f"详细错误: {traceback.format_exc()}")
                    
                except Exception as e:
                    continue

            # 打印解析后的数据
            # logger.info("\n=== 电机数据更新 ===")
            # for motor in self.motors:
            #     logger.info(str(motor))
            # logger.info("==================\n")

            return True

        except Exception as e:
            logger.error(f"解析电机数据失败: {str(e)}")
            return False
    
    def process_motor_data(self, raw_data: List[int]) -> List[MotorData]:
        """
        处理Modbus原始数据，转换为电机数据对象列表
        
        Args:
            raw_data: Modbus寄存器原始数据列表
            
        Returns:
            电机数据对象列表
        """
        try:
            if not raw_data:
                logger.warning("收到空的原始数据")
                return []
            
            # 使用新的解析方法
            success = self.parse_motor_data(raw_data)
            if success:
                return self.motors.copy()
            else:
                return []
            
        except Exception as e:
            logger.error(f"处理电机数据失败: {str(e)}")
            return []
    
    def get_motor_data(self, motor_id: int) -> MotorData:
        """获取指定电机的数据"""
        if 1 <= motor_id <= self.motor_count:
            return self.motors[motor_id - 1]
        else:
            logger.warning(f"无效的电机ID: {motor_id}")
            return None
    
    def get_all_motor_data(self) -> List[MotorData]:
        """获取所有电机数据"""
        return self.motors.copy() 