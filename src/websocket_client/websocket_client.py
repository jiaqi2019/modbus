import asyncio
import websockets
import json
import logging
import threading
import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketClient:
    """WebSocket客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        
        # 连接状态
        self.is_connected = False
        self.is_connecting = False
        self.should_reconnect = True
        self.reconnect_interval = 5  # 重连间隔（秒）
        
        # 回调函数
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # WebSocket连接对象
        self.websocket = None
        
        # 事件循环
        self.loop = None
        self.thread = None
        
        logger.info(f"WebSocket客户端初始化完成: {self.uri}")
    
    def set_callbacks(self, on_connect=None, on_disconnect=None, on_message=None, on_error=None):
        """设置回调函数"""
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message
        self.on_error = on_error
    
    def start(self):
        """启动WebSocket客户端"""
        if self.thread and self.thread.is_alive():
            logger.warning("WebSocket客户端已在运行")
            return
        
        self.should_reconnect = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        logger.info("WebSocket客户端已启动")
    
    def stop(self):
        """停止WebSocket客户端"""
        logger.info("正在停止WebSocket客户端...")
        
        # 设置停止标志
        self.should_reconnect = False
        self.is_connected = False
        
        # 等待线程自然结束，而不是强制停止事件循环
        if self.thread and self.thread.is_alive():
            logger.info("等待WebSocket线程结束...")
            # 给线程一些时间来自然结束
            self.thread.join(timeout=3.0)
            
            if self.thread.is_alive():
                logger.warning("WebSocket线程未能在3秒内结束")
        
        logger.info("WebSocket客户端已停止")
    
    def _run_event_loop(self):
        """在独立线程中运行事件循环"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"事件循环运行失败: {str(e)}")
        finally:
            # 确保事件循环正确关闭
            try:
                if self.loop and not self.loop.is_closed():
                    # 取消所有待处理的任务
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    
                    # 等待所有任务完成
                    if pending:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    
                    self.loop.close()
            except Exception as e:
                logger.error(f"关闭事件循环时出错: {str(e)}")
    
    async def _stop_loop(self):
        """停止事件循环"""
        if self.loop and not self.loop.is_closed():
            self.loop.stop()
    
    async def _connect_and_listen(self):
        """连接并监听消息"""
        while self.should_reconnect:
            try:
                if not self.is_connected and not self.is_connecting:
                    await self._connect()
                
                if self.is_connected and self.websocket:
                    await self._listen_for_messages()
                
                # 如果连接断开且不需要重连，退出循环
                if not self.should_reconnect:
                    break
                    
            except Exception as e:
                logger.error(f"WebSocket连接错误: {str(e)}")
                if self.on_error:
                    self.on_error(str(e))
                
                self.is_connected = False
                self.is_connecting = False
                
                if self.should_reconnect:
                    logger.info(f"等待 {self.reconnect_interval} 秒后重连...")
                    await asyncio.sleep(self.reconnect_interval)
                else:
                    break
    
    async def _connect(self):
        """建立WebSocket连接"""
        try:
            self.is_connecting = True
            logger.info(f"正在连接WebSocket服务器: {self.uri}")
            
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            self.is_connecting = False
            
            logger.info("WebSocket连接成功")
            
            if self.on_connect:
                self.on_connect()
                
        except Exception as e:
            self.is_connecting = False
            logger.error(f"WebSocket连接失败: {str(e)}")
            raise
    
    async def _listen_for_messages(self):
        """监听WebSocket消息"""
        try:
            async for message in self.websocket:
                if not self.should_reconnect:
                    logger.info("收到停止信号，退出消息监听")
                    break
                
                try:
                    # 解析JSON消息
                    data = json.loads(message)
                    logger.debug(f"收到消息: {data}")
                    
                    if self.on_message:
                        self.on_message(data)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"消息格式错误: {str(e)}")
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
            self.is_connected = False
            if self.on_disconnect:
                self.on_disconnect()
        except Exception as e:
            logger.error(f"监听消息失败: {str(e)}")
            self.is_connected = False
            if self.on_disconnect:
                self.on_disconnect()
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息到服务器"""
        if not self.is_connected or not self.websocket:
            logger.warning("WebSocket未连接，无法发送消息")
            return False
        
        try:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug(f"发送消息: {message}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "is_connected": self.is_connected,
            "is_connecting": self.is_connecting,
            "should_reconnect": self.should_reconnect,
            "uri": self.uri,
            "host": self.host,
            "port": self.port
        }
    
    def update_config(self, host: str, port: int):
        """更新连接配置"""
        was_connected = self.is_connected
        
        if was_connected:
            self.stop()
        
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        
        logger.info(f"WebSocket配置已更新: {self.uri}")
        
        if was_connected:
            time.sleep(1)  # 等待停止完成
            self.start() 