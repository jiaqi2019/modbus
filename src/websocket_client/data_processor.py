import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MotorData:
    """电机数据结构"""
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
    last_update: Optional[datetime] = None
    
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

class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.motors_data: Dict[int, MotorData] = {}
        self.on_data_updated = None
        
        # logger.info("数据处理器初始化完成")
    
    def set_data_updated_callback(self, callback):
        """设置数据更新回调函数"""
        self.on_data_updated = callback
    
    def process_websocket_message(self, message: Dict[str, Any]) -> Optional[List[MotorData]]:
        """处理WebSocket消息"""
        try:
            # 记录原始消息内容
            # # logger.info(f"收到WebSocket消息: {message}")
            
            # 检查消息类型
            message_type = message.get("type", "")
            
            if message_type == "motor_data":
                return self._process_motor_data(message)
            elif message_type == "motor_update":
                return self._process_motor_update(message)
            elif message_type == "latest_data":
                return self._process_latest_data(message)
            elif message_type == "status":
                return self._process_status_message(message)
            else:
                logger.warning(f"未知消息类型: {message_type}")
                return None
                
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")
            return None
    
    def _process_motor_data(self, message: Dict[str, Any]) -> List[MotorData]:
        """处理电机数据消息"""
        try:
            motors_data = message.get("data", [])
            updated_motors = []
            
            # # logger.info(f"处理motor_data消息，数据条数: {len(motors_data)}")
            
            for motor_data in motors_data:
                motor_id = motor_data.get("motor_id")
                if motor_id is None:
                    logger.warning("电机数据缺少motor_id字段")
                    continue
                
                # 创建或更新电机数据
                motor = self.motors_data.get(motor_id)
                if motor is None:
                    motor = MotorData(motor_id=motor_id)
                    self.motors_data[motor_id] = motor
                    # logger.info(f"创建新电机数据对象: {motor_id}")
                
                # 更新数据
                motor.phase_a_current = motor_data.get("phase_a_current", 0.0)
                motor.phase_b_current = motor_data.get("phase_b_current", 0.0)
                motor.phase_c_current = motor_data.get("phase_c_current", 0.0)
                motor.frequency = motor_data.get("frequency", 0.0)
                motor.reactive_power = motor_data.get("reactive_power", 0.0)
                motor.active_power = motor_data.get("active_power", 0.0)
                motor.line_voltage = motor_data.get("line_voltage", 0.0)
                motor.excitation_voltage = motor_data.get("excitation_voltage", 0.0)
                motor.excitation_current = motor_data.get("excitation_current", 0.0)
                motor.calculated_excitation_current = motor_data.get("calculated_excitation_current", 0.0)
                
                # 使用原始数据中的时间戳，如果没有则使用当前时间
                if "last_update" in motor_data:
                    # 如果原始数据包含时间戳，尝试解析
                    try:
                        if isinstance(motor_data["last_update"], str):
                            motor.last_update = datetime.fromisoformat(motor_data["last_update"])
                        else:
                            motor.last_update = motor_data["last_update"]
                    except Exception as e:
                        logger.warning(f"解析时间戳失败，使用当前时间: {str(e)}")
                        motor.last_update = datetime.now()
                else:
                    # 原始数据没有时间戳，使用当前时间
                    motor.last_update = datetime.now()
                
                updated_motors.append(motor)
            
            # 触发数据更新回调
            if self.on_data_updated and updated_motors:
                # logger.info(f"触发数据更新回调，电机数量: {len(updated_motors)}")
                self.on_data_updated(updated_motors)
            else:
                logger.warning(f"数据更新回调未设置或无更新数据，回调函数: {self.on_data_updated is not None}")
            
            return updated_motors
            
        except Exception as e:
            logger.error(f"处理电机数据失败: {str(e)}")
            return []
    
    def _process_motor_update(self, message: Dict[str, Any]) -> List[MotorData]:
        """处理电机更新消息"""
        try:
            # 获取data字段
            data = message.get("data", {})
            motors_data = []
            
            # # logger.info(f"处理motor_update消息，data类型: {type(data)}")
            # logger.debug(f"motor_update消息内容: {message}")
            
            # 处理不同的数据格式
            if isinstance(data, list):
                # 如果data是列表，直接使用
                motors_data = data
                # # logger.info(f"data是列表格式，电机数量: {len(motors_data)}")
                # 记录每个电机的详细数据
                for i, motor_data in enumerate(motors_data):
                    logger.debug(f"电机 {i+1} 原始数据: {motor_data}")
            elif isinstance(data, dict):
                # 如果data是字典，检查是否包含电机数据
                if "motor_id" in data:
                    # 单个电机数据
                    motors_data = [data]
                elif data:
                    # 字典格式的多个电机数据
                    motors_data = list(data.values())
                else:
                    # 空字典，尝试从消息根级别获取数据
                    # logger.info("data字段为空字典，尝试从消息根级别获取电机数据")
                    for key, value in message.items():
                        if key not in ["type", "timestamp"]:
                            if isinstance(value, dict) and "motor_id" in value:
                                motors_data = [value]
                                break
                            elif isinstance(value, list) and len(value) > 0 and "motor_id" in value[0]:
                                motors_data = value
                                break
            else:
                logger.warning(f"未知的data格式: {type(data)}")
                return []
            
            updated_motors = []
            
            for motor_data in motors_data:
                motor_id = motor_data.get("motor_id")
                if motor_id is None:
                    logger.warning(f"电机数据缺少motor_id字段: {motor_data}")
                    continue
                
                # 创建或更新电机数据
                motor = self.motors_data.get(motor_id)
                if motor is None:
                    motor = MotorData(motor_id=motor_id)
                    self.motors_data[motor_id] = motor
                    # logger.info(f"创建新电机数据对象: {motor_id}")
                
                # 更新数据 - 支持部分字段更新
                if "phase_a_current" in motor_data:
                    motor.phase_a_current = motor_data.get("phase_a_current", 0.0)
                if "phase_b_current" in motor_data:
                    motor.phase_b_current = motor_data.get("phase_b_current", 0.0)
                if "phase_c_current" in motor_data:
                    motor.phase_c_current = motor_data.get("phase_c_current", 0.0)
                if "frequency" in motor_data:
                    motor.frequency = motor_data.get("frequency", 0.0)
                if "reactive_power" in motor_data:
                    motor.reactive_power = motor_data.get("reactive_power", 0.0)
                if "active_power" in motor_data:
                    motor.active_power = motor_data.get("active_power", 0.0)
                if "line_voltage" in motor_data:
                    motor.line_voltage = motor_data.get("line_voltage", 0.0)
                if "excitation_voltage" in motor_data:
                    motor.excitation_voltage = motor_data.get("excitation_voltage", 0.0)
                if "excitation_current" in motor_data:
                    motor.excitation_current = motor_data.get("excitation_current", 0.0)
                if "calculated_excitation_current" in motor_data:
                    motor.calculated_excitation_current = motor_data.get("calculated_excitation_current", 0.0)
                if "excitation_current_ratio" in motor_data:
                    motor.excitation_current_ratio = motor_data.get("excitation_current_ratio", 0.0)
                    logger.debug(f"电机 {motor_id} 接收到比值: {motor.excitation_current_ratio}")
                else:
                    logger.warning(f"电机 {motor_id} 数据中缺少 excitation_current_ratio 字段")
                
                # 使用原始数据中的时间戳，如果没有则使用当前时间
                if "last_update" in motor_data:
                    # 如果原始数据包含时间戳，尝试解析
                    try:
                        if isinstance(motor_data["last_update"], str):
                            motor.last_update = datetime.fromisoformat(motor_data["last_update"])
                        else:
                            motor.last_update = motor_data["last_update"]
                    except Exception as e:
                        logger.warning(f"解析时间戳失败，使用当前时间: {str(e)}")
                        motor.last_update = datetime.now()
                else:
                    # 原始数据没有时间戳，使用当前时间
                    motor.last_update = datetime.now()
                
                updated_motors.append(motor)
            
            # 触发数据更新回调
            if self.on_data_updated and updated_motors:
                # logger.info(f"触发数据更新回调，电机数量: {len(updated_motors)}")
                self.on_data_updated(updated_motors)
            else:
                logger.warning(f"数据更新回调未设置或无更新数据，回调函数: {self.on_data_updated is not None}")
            
            return updated_motors
            
        except Exception as e:
            logger.error(f"处理电机更新失败: {str(e)}")
            return []
    
    def _process_latest_data(self, message: Dict[str, Any]) -> List[MotorData]:
        """处理最新数据消息"""
        try:
            # 获取data字段
            data = message.get("data", {})
            motors_data = []
            
            # logger.info(f"处理latest_data消息，data类型: {type(data)}")
            logger.debug(f"latest_data消息内容: {message}")
            
            # 处理不同的数据格式
            if isinstance(data, list):
                # 如果data是列表，直接使用
                motors_data = data
                # logger.info(f"data是列表格式，电机数量: {len(motors_data)}")
            elif isinstance(data, dict):
                # 如果data是字典，检查是否包含电机数据
                if "motor_id" in data:
                    # 单个电机数据
                    motors_data = [data]
                elif data:
                    # 字典格式的多个电机数据
                    motors_data = list(data.values())
                else:
                    # 空字典，尝试从消息根级别获取数据
                    # logger.info("data字段为空字典，尝试从消息根级别获取电机数据")
                    for key, value in message.items():
                        if key not in ["type", "timestamp"]:
                            if isinstance(value, dict) and "motor_id" in value:
                                motors_data = [value]
                                break
                            elif isinstance(value, list) and len(value) > 0 and "motor_id" in value[0]:
                                motors_data = value
                                break
            else:
                logger.warning(f"未知的data格式: {type(data)}")
                return []
            
            updated_motors = []
            
            for motor_data in motors_data:
                motor_id = motor_data.get("motor_id")
                if motor_id is None:
                    logger.warning(f"电机数据缺少motor_id字段: {motor_data}")
                    continue
                
                # 创建或更新电机数据
                motor = self.motors_data.get(motor_id)
                if motor is None:
                    motor = MotorData(motor_id=motor_id)
                    self.motors_data[motor_id] = motor
                    # logger.info(f"创建新电机数据对象: {motor_id}")
                
                # 更新数据 - 支持部分字段更新
                if "phase_a_current" in motor_data:
                    motor.phase_a_current = motor_data.get("phase_a_current", 0.0)
                if "phase_b_current" in motor_data:
                    motor.phase_b_current = motor_data.get("phase_b_current", 0.0)
                if "phase_c_current" in motor_data:
                    motor.phase_c_current = motor_data.get("phase_c_current", 0.0)
                if "frequency" in motor_data:
                    motor.frequency = motor_data.get("frequency", 0.0)
                if "reactive_power" in motor_data:
                    motor.reactive_power = motor_data.get("reactive_power", 0.0)
                if "active_power" in motor_data:
                    motor.active_power = motor_data.get("active_power", 0.0)
                if "line_voltage" in motor_data:
                    motor.line_voltage = motor_data.get("line_voltage", 0.0)
                if "excitation_voltage" in motor_data:
                    motor.excitation_voltage = motor_data.get("excitation_voltage", 0.0)
                if "excitation_current" in motor_data:
                    motor.excitation_current = motor_data.get("excitation_current", 0.0)
                if "calculated_excitation_current" in motor_data:
                    motor.calculated_excitation_current = motor_data.get("calculated_excitation_current", 0.0)
                if "excitation_current_ratio" in motor_data:
                    motor.excitation_current_ratio = motor_data.get("excitation_current_ratio", 0.0)
                    logger.debug(f"电机 {motor_id} 接收到比值: {motor.excitation_current_ratio}")
                else:
                    logger.warning(f"电机 {motor_id} 数据中缺少 excitation_current_ratio 字段")
                
                # 使用原始数据中的时间戳，如果没有则使用当前时间
                if "last_update" in motor_data:
                    # 如果原始数据包含时间戳，尝试解析
                    try:
                        if isinstance(motor_data["last_update"], str):
                            motor.last_update = datetime.fromisoformat(motor_data["last_update"])
                        else:
                            motor.last_update = motor_data["last_update"]
                    except Exception as e:
                        logger.warning(f"解析时间戳失败，使用当前时间: {str(e)}")
                        motor.last_update = datetime.now()
                else:
                    # 原始数据没有时间戳，使用当前时间
                    motor.last_update = datetime.now()
                
                updated_motors.append(motor)
                # # logger.info(f"更新电机 {motor_id} 数据 (latest_data)")
            
            # 触发数据更新回调
            if self.on_data_updated and updated_motors:
                # logger.info(f"触发数据更新回调，电机数量: {len(updated_motors)}")
                self.on_data_updated(updated_motors)
            else:
                logger.warning(f"数据更新回调未设置或无更新数据，回调函数: {self.on_data_updated is not None}")
            
            return updated_motors
            
        except Exception as e:
            logger.error(f"处理最新数据失败: {str(e)}")
            return []
    
    def _process_status_message(self, message: Dict[str, Any]) -> List[MotorData]:
        """处理状态消息"""
        try:
            status = message.get("status", "")
            # logger.info(f"收到状态消息: {status}")
            return []
        except Exception as e:
            logger.error(f"处理状态消息失败: {str(e)}")
            return []
    
    def get_motor_data(self, motor_id: int) -> Optional[MotorData]:
        """获取指定电机的数据"""
        return self.motors_data.get(motor_id)
    
    def get_all_motors_data(self) -> List[MotorData]:
        """获取所有电机数据"""
        return list(self.motors_data.values())
    
    def get_motor_ids(self) -> List[int]:
        """获取所有电机ID"""
        return list(self.motors_data.keys())
    
    def clear_data(self):
        """清除所有数据"""
        self.motors_data.clear()
        # logger.info("所有电机数据已清除")
    
    def validate_motor_data(self, motor_data: Dict[str, Any]) -> bool:
        """验证电机数据格式"""
        required_fields = ["motor_id"]
        numeric_fields = [
            "phase_a_current", "phase_b_current", "phase_c_current",
            "frequency", "reactive_power", "active_power",
            "line_voltage", "excitation_voltage", "excitation_current",
            "calculated_excitation_current"
        ]
        
        try:
            # 检查必需字段
            for field in required_fields:
                if field not in motor_data:
                    logger.warning(f"电机数据缺少必需字段: {field}")
                    return False
            
            # 检查数值字段
            for field in numeric_fields:
                if field in motor_data:
                    value = motor_data[field]
                    if not isinstance(value, (int, float)) and value is not None:
                        logger.warning(f"电机数据字段 {field} 不是数值类型: {type(value)}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证电机数据失败: {str(e)}")
            return False 