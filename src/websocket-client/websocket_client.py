import asyncio
import websockets
import json
import logging
import threading
import time
from datetime import datetime
from db.database import DatabaseManager

logger = logging.getLogger(__name__)

class MotorData:
    """电机数据类，用于存储从WebSocket接收的数据"""
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

    def from_dict(self, data):
        """从字典数据更新电机数据"""
        self.phase_a_current = data.get('phase_a_current', 0.0)
        self.phase_b_current = data.get('phase_b_current', 0.0)
        self.phase_c_current = data.get('phase_c_current', 0.0)
        self.frequency = data.get('frequency', 0.0)
        self.reactive_power = data.get('reactive_power', 0.0)
        self.active_power = data.get('active_power', 0.0)
        self.line_voltage = data.get('line_voltage', 0.0)
        self.excitation_voltage = data.get('excitation_voltage', 0.0)
        self.excitation_current = data.get('excitation_current', 0.0)
        self.calculated_excitation_current = data.get('calculated_excitation_current', 0.0)
        self.excitation_current_ratio = data.get('excitation_current_ratio', 0.0)
        self.last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))

    def to_dict(self):
        """转换为字典"""
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

class WebSocketClient:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.motors = []
        self.db_manager = DatabaseManager()
        self.running = False
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            logger.info(f"已连接到WebSocket服务器: {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"连接WebSocket服务器失败: {str(e)}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("已断开WebSocket连接")
    
    async def send_message(self, message):
        """发送消息到服务器"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
    
    async def receive_messages(self):
        """接收服务器消息"""
        if not self.connected or not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.error("无效的JSON消息")
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
            self.connected = False
        except Exception as e:
            logger.error(f"接收消息时出错: {str(e)}")
            self.connected = False
    
    async def handle_message(self, data):
        """处理接收到的消息"""
        msg_type = data.get('type')
        
        if msg_type == 'motor_update':
            # 处理电机数据更新
            await self.handle_motor_update(data)
        elif msg_type == 'pong':
            # 心跳响应
            logger.debug("收到心跳响应")
    
    async def handle_motor_update(self, data):
        """处理电机数据更新"""
        try:
            motors_data = data.get('motors', [])
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            # 更新本地电机数据
            self.motors = []
            for motor_data in motors_data:
                motor = MotorData(motor_data.get('motor_id', 1))
                motor.from_dict(motor_data)
                self.motors.append(motor)
            
            # 保存到数据库
            if self.motors:
                self.db_manager.save_all_motors_data(self.motors)
                logger.info(f"已保存 {len(self.motors)} 台电机的数据到数据库")
            
        except Exception as e:
            logger.error(f"处理电机数据更新失败: {str(e)}")
    
    def get_motors_data(self):
        """获取电机数据（供UI使用）"""
        return self.motors
    
    def request_data(self):
        """请求数据（模拟，实际是通过WebSocket接收）"""
        # WebSocket客户端不需要主动请求数据，数据会自动推送
        return self.connected and len(self.motors) > 0
    
    async def start_heartbeat(self):
        """启动心跳检测"""
        while self.running and self.connected:
            try:
                await self.send_message({'type': 'ping'})
                await asyncio.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"发送心跳失败: {str(e)}")
                break
    
    async def run(self):
        """运行WebSocket客户端"""
        self.running = True
        
        # 连接服务器
        if not await self.connect():
            return
        
        # 启动心跳检测
        heartbeat_task = asyncio.create_task(self.start_heartbeat())
        
        try:
            # 接收消息
            await self.receive_messages()
        finally:
            self.running = False
            heartbeat_task.cancel()
            await self.disconnect()

def run_websocket_client(server_url="ws://localhost:8765"):
    """运行WebSocket客户端的便捷函数"""
    client = WebSocketClient(server_url)
    asyncio.run(client.run())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket客户端')
    parser.add_argument('--server', default='ws://localhost:8765', help='WebSocket服务器地址')
    
    args = parser.parse_args()
    
    try:
        run_websocket_client(args.server)
    except KeyboardInterrupt:
        print("客户端已停止") 