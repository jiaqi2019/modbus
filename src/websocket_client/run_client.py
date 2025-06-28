#!/usr/bin/env python3
"""
WebSocket客户端启动脚本
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('websocket_client.log', encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("启动WebSocket客户端...")
    
    try:
        # 导入并运行主UI
        from src.websocket_client.main_ui import WebSocketClientUI
        
        app = WebSocketClientUI()
        app.run()
        
    except ImportError as e:
        logger.error(f"导入模块失败: {str(e)}")
        print(f"错误: 无法导入必要的模块 - {str(e)}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        print(f"错误: 启动失败 - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 