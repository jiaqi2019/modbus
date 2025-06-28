import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

logger = logging.getLogger(__name__)

class WebSocketServer:
    """
    WebSocket服务器
    用于将电机数据广播给连接的WebSocket客户端
    """
    
    def __init__(self, data_source, host='0.0.0.0', port=8765):
        """
        初始化WebSocket服务器
        
        Args:
            data_source: 数据源对象，需要提供get_latest_motors_data()方法
            host: 服务器主机地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.clients = set()  # 连接的客户端集合
        self.data_source = data_source  # 数据源
        self.running = False
        self.server = None
        
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
            logger.info("开始获取最新数据...")
            motors_data = self.data_source.get_latest_motors_data()
            logger.info(f"获取到数据: {type(motors_data)}, 长度: {len(motors_data) if motors_data else 0}")
            
            if motors_data:
                # 确保数据是字典格式
                formatted_data = self._format_motors_data(motors_data)
                logger.info(f"格式化后数据长度: {len(formatted_data)}")
                
                message = {
                    'type': 'latest_data',
                    'data': formatted_data,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"发送消息: {message['type']}, 数据条数: {len(formatted_data)}")
                await websocket.send(json.dumps(message, ensure_ascii=False))
                logger.info("数据发送成功")
            else:
                logger.warning("没有获取到电机数据")
        except Exception as e:
            logger.error(f"发送数据失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _format_motors_data(self, motors_data):
        """格式化电机数据，确保是字典格式"""
        try:
            logger.info(f"开始格式化数据，原始数据类型: {type(motors_data)}")
            formatted_data = []
            
            for i, motor_data in enumerate(motors_data):
                logger.info(f"处理第 {i+1} 个电机数据，类型: {type(motor_data)}")
                
                if hasattr(motor_data, 'to_dict'):
                    # 如果是MotorData对象，转换为字典
                    logger.info(f"MotorData对象，转换为字典")
                    formatted_data.append(motor_data.to_dict())
                elif isinstance(motor_data, dict):
                    # 如果已经是字典，直接使用
                    logger.info(f"字典类型，直接使用")
                    formatted_data.append(motor_data)
                else:
                    # 其他类型，尝试转换为字典
                    logger.warning(f"未知的电机数据类型: {type(motor_data)}")
                    continue
            
            logger.info(f"格式化完成，共 {len(formatted_data)} 条数据")
            return formatted_data
        except Exception as e:
            logger.error(f"格式化电机数据失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return []
    
    async def broadcast_data(self, data):
        """
        向所有客户端广播数据
        
        Args:
            data: 要广播的数据（列表格式）
        """
        if not self.clients:
            return
        
        if not data:
            logger.warning("数据为空，跳过广播")
            return
        
        try:
            # 验证数据格式
            logger.debug(f"广播数据，数据类型: {type(data)}, 长度: {len(data)}")
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        logger.error(f"数据项 {i} 不是字典格式: {type(item)}")
                        return
            else:
                logger.error(f"数据不是列表格式: {type(data)}")
                return
            
            message = {
                'type': 'motor_update',
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            message_json = json.dumps(message, ensure_ascii=False)
            logger.debug(f"消息序列化成功，长度: {len(message_json)}")
            
        except Exception as e:
            logger.error(f"准备广播数据失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return
        
        # 创建发送任务列表
        tasks = []
        disconnected_clients = []
        
        for client in self.clients:
            try:
                task = asyncio.create_task(client.send(message_json))
                tasks.append(task)
            except Exception as e:
                logger.error(f"发送数据到客户端失败: {str(e)}")
                disconnected_clients.append(client)
        
        # 移除断开的客户端
        for client in disconnected_clients:
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
                motors_data = self.data_source.get_latest_motors_data()
                if motors_data:
                    for motor_data in motors_data:
                        # 确保能正确获取motor_id
                        current_motor_id = None
                        if hasattr(motor_data, 'motor_id'):
                            current_motor_id = motor_data.motor_id
                        elif isinstance(motor_data, dict):
                            current_motor_id = motor_data.get('motor_id')
                        
                        if current_motor_id == motor_id:
                            # 确保数据是字典格式
                            if hasattr(motor_data, 'to_dict'):
                                formatted_data = motor_data.to_dict()
                            elif isinstance(motor_data, dict):
                                formatted_data = motor_data
                            else:
                                logger.warning(f"无法格式化电机数据: {type(motor_data)}")
                                continue
                            
                            await websocket.send(json.dumps({
                                'type': 'motor_data',
                                'motor_id': motor_id,
                                'data': formatted_data,
                                'timestamp': datetime.now().isoformat()
                            }))
                            break
    
    def start_data_monitoring(self):
        """启动数据监控线程"""
        def monitor_loop():
            last_data = []
            logger.info("数据监控线程开始运行")
            
            while self.running:
                try:
                    logger.debug("检查数据源...")
                    motors_data = self.data_source.get_latest_motors_data()
                    logger.debug(f"数据源返回: {type(motors_data)}, 长度: {len(motors_data) if motors_data else 0}")
                    
                    if motors_data:
                        # 直接使用列表格式的数据
                        current_data = []
                        for i, motor_data in enumerate(motors_data):
                            logger.debug(f"处理第 {i+1} 个电机数据: {type(motor_data)}")
                            
                            # 确保数据是字典格式
                            if hasattr(motor_data, 'to_dict'):
                                formatted_motor_data = motor_data.to_dict()
                            elif isinstance(motor_data, dict):
                                formatted_motor_data = motor_data
                            else:
                                logger.warning(f"无法格式化电机数据: {type(motor_data)}")
                                continue
                            
                            current_data.append(formatted_motor_data)
                            logger.debug(f"添加电机数据到列表")
                        
                        logger.debug(f"当前数据: {len(current_data)} 台电机")
                        
                        # 检查是否有新数据
                        has_new_data = False
                        if not last_data:
                            has_new_data = bool(current_data)
                            logger.info(f"首次数据: {len(current_data)} 台电机")
                        else:
                            # 简单的长度比较，如果有变化就认为有新数据
                            if len(current_data) != len(last_data):
                                has_new_data = True
                                logger.info(f"电机数量变化: {len(last_data)} -> {len(current_data)}")
                            else:
                                # 比较数据内容
                                for i, (current, last) in enumerate(zip(current_data, last_data)):
                                    if current != last:
                                        has_new_data = True
                                        logger.info(f"发现新数据，电机 {current.get('motor_id', i)}")
                                        break
                        
                        # 如果有新数据，广播给所有客户端
                        if has_new_data and self.clients:
                            logger.info(f"广播新数据给 {len(self.clients)} 个客户端")
                            asyncio.run(self.broadcast_data(current_data))
                        elif has_new_data:
                            logger.info("有新数据但没有连接的客户端")
                        else:
                            logger.debug("没有新数据")
                        
                        last_data = current_data
                    else:
                        logger.debug("没有获取到电机数据")
                    
                    time.sleep(1)  # 每秒检查一次
                    
                except Exception as e:
                    logger.error(f"数据监控错误: {str(e)}")
                    import traceback
                    logger.error(f"详细错误: {traceback.format_exc()}")
                    time.sleep(5)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("数据监控线程已启动")
    
    async def start_server(self):
        """启动WebSocket服务器"""
        self.running = True
        # 注释掉数据监控线程，避免与Modbus客户端的直接广播冲突
        # self.start_data_monitoring()
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"WebSocket服务器启动: ws://{self.host}:{self.port}")
        
        try:
            await self.server.wait_closed()
        except KeyboardInterrupt:
            logger.info("服务器关闭")
        finally:
            self.running = False
    
    def start(self):
        """在后台线程中启动服务器"""
        def run_server():
            asyncio.run(self.start_server())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("WebSocket服务器已在后台启动")
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server:
            self.server.close()
        logger.info("WebSocket服务器已停止")
    
    def get_client_count(self):
        """获取当前连接的客户端数量"""
        return len(self.clients) 