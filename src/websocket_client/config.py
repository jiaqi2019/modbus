import json
import os
import sys
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
    
    def _get_script_directory(self):
        """获取启动脚本的目录"""
        try:
            # 方法1: 通过sys.argv获取启动脚本路径
            if len(sys.argv) > 0:
                script_path = sys.argv[0]
                if os.path.isabs(script_path):
                    return os.path.dirname(script_path)
                else:
                    # 相对路径，转换为绝对路径
                    return os.path.dirname(os.path.abspath(script_path))
            
            # 方法2: 通过调用栈查找run_client.py
            if hasattr(sys, '_getframe'):
                frame = sys._getframe(1)
                while frame:
                    filename = frame.f_code.co_filename
                    if 'run_client.py' in filename or 'main.py' in filename:
                        script_dir = os.path.dirname(os.path.abspath(filename))
                        return script_dir
                    frame = frame.f_back
            
            # 方法3: 查找当前工作目录下的run_client.py
            cwd = os.getcwd()
            run_client_path = os.path.join(cwd, 'run_client.py')
            if os.path.exists(run_client_path):
                return cwd
            
            # 方法4: 查找src/websocket_client/run_client.py
            websocket_client_dir = os.path.join(cwd, 'src', 'websocket_client')
            if os.path.exists(websocket_client_dir):
                return websocket_client_dir
            
            # 备用方案：使用当前工作目录
            logger.warning("无法确定启动脚本目录，使用当前工作目录")
            return os.getcwd()
            
        except Exception as e:
            logger.error(f"获取脚本目录失败: {str(e)}，使用当前工作目录")
            return os.getcwd()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # logger.info(f"成功加载配置文件: {self.config_file}")
                    return config
            else:
                # logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            # logger.info(f"配置文件已保存: {self.config_file}")
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
        db_config = self.config.get("database", self.default_config["database"])
        
        # 解析数据库路径到脚本目录
        db_path = db_config.get("path", "motor_data.db")
        if not os.path.isabs(db_path):
            script_dir = self._get_script_directory()
            db_config["path"] = os.path.join(script_dir, db_path)
            # logger.info(f"数据库路径已解析为: {db_config['path']}")
        
        return db_config
    
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