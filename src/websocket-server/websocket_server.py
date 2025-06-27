import asyncio
import websockets
import json
import logging
from datetime import datetime
from db.database import DatabaseManager
import threading
import time

logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.db_manager = DatabaseManager()
        self.running = False
        
    async def register(self, websocket):
        """注册新的WebSocket客户端"""
        self.clients.add(websocket)
        logger.info(f"客户端连接，当前连接数: {len(self.clients)}")
        
        # 发送当前所有电机的最新数据
        await self.send_latest_data_to_client(websocket)
    
    async def unregister(self, websocket):
        """注销WebSocket客户端"""
        self.clients.discard(websocket)
        logger.info(f"客户端断开，当前连接数: {len(self.clients)}")
    
    async def send_latest_data_to_client(self, websocket):
        """向指定客户端发送最新数据"""
        try:
            # 获取所有电机的最新数据
            stats = self.db_manager.get_database_stats()
            motor_count = stats.get('motor_count', 0)
            
            motors_data = []
            for motor_id in range(1, motor_count + 1):
                latest_data = self.db_manager.get_latest_motor_data(motor_id)
                if latest_data:
                    motors_data.append({
                        'motor_id': motor_id,
                        'data': latest_data,
                        'timestamp': datetime.now().isoformat()
                    })
            
            message = {
                'type': 'latest_data',
                'data': motors_data,
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"发送数据失败: {str(e)}")
    
    async def broadcast_data(self, data):
        """向所有客户端广播数据"""
        if not self.clients:
            return
            
        message = {
            'type': 'motor_update',
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        message_json = json.dumps(message, ensure_ascii=False)
        
        # 创建发送任务列表
        tasks = []
        for client in self.clients.copy():
            try:
                task = asyncio.create_task(client.send(message_json))
                tasks.append(task)
            except Exception as e:
                logger.error(f"发送数据到客户端失败: {str(e)}")
                await self.unregister(client)
        
        # 等待所有发送任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("无效的JSON消息")
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def handle_message(self, websocket, data):
        """处理客户端消息"""
        msg_type = data.get('type')
        
        if msg_type == 'ping':
            # 心跳检测
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            }))
        
        elif msg_type == 'get_latest':
            # 获取最新数据
            await self.send_latest_data_to_client(websocket)
        
        elif msg_type == 'subscribe':
            # 订阅特定电机数据
            motor_id = data.get('motor_id')
            if motor_id:
                latest_data = self.db_manager.get_latest_motor_data(motor_id)
                if latest_data:
                    await websocket.send(json.dumps({
                        'type': 'motor_data',
                        'motor_id': motor_id,
                        'data': latest_data,
                        'timestamp': datetime.now().isoformat()
                    }))
    
    def start_data_monitoring(self):
        """启动数据监控线程"""
        def monitor_loop():
            last_data = {}
            
            while self.running:
                try:
                    # 检查是否有新数据
                    stats = self.db_manager.get_database_stats()
                    motor_count = stats.get('motor_count', 0)
                    
                    current_data = {}
                    has_new_data = False
                    
                    for motor_id in range(1, motor_count + 1):
                        latest_data = self.db_manager.get_latest_motor_data(motor_id)
                        if latest_data:
                            current_data[motor_id] = latest_data
                            
                            # 检查是否有新数据
                            if motor_id not in last_data or last_data[motor_id] != latest_data:
                                has_new_data = True
                    
                    # 如果有新数据，广播给所有客户端
                    if has_new_data and self.clients:
                        asyncio.run(self.broadcast_data(current_data))
                    
                    last_data = current_data
                    time.sleep(1)  # 每秒检查一次
                    
                except Exception as e:
                    logger.error(f"数据监控错误: {str(e)}")
                    time.sleep(5)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("数据监控线程已启动")
    
    async def start_server(self):
        """启动WebSocket服务器"""
        self.running = True
        self.start_data_monitoring()
        
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"WebSocket服务器启动: ws://{self.host}:{self.port}")
        
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            logger.info("服务器关闭")
        finally:
            self.running = False
