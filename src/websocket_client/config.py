import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WebSocketConfig:
    """WebSocket客户端配置管理"""
    
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config_file = config_path
        self.default_config = {
            "websocket": {
                "host": "localhost",
                "port": 8765
            },
            "database": {
                "path": "motor_data.db"
            },
            "ui": {
                "auto_connect": False,
                "auto_reconnect": True,
                "reconnect_interval": 5
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"成功加载配置文件: {self.config_file}")
                    return config
            else:
                logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件已保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """获取WebSocket配置"""
        return self.config.get("websocket", self.default_config["websocket"])
    
    def set_websocket_config(self, host: str, port: int) -> bool:
        """设置WebSocket配置"""
        try:
            self.config["websocket"] = {
                "host": host,
                "port": port
            }
            return self.save_config()
        except Exception as e:
            logger.error(f"设置WebSocket配置失败: {str(e)}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.config.get("database", self.default_config["database"])
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self.config.get("ui", self.default_config["ui"])
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.config.update(new_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False 