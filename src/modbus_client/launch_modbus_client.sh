#!/bin/bash

# Modbus客户端启动脚本
# 麒麟系统桌面快捷方式启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 启动Modbus客户端
echo "正在启动Modbus客户端..."
python3 "$SCRIPT_DIR/main_ui.py"

# 如果启动失败，显示错误信息
if [ $? -ne 0 ]; then
    echo "启动失败！请检查："
    echo "1. 是否已安装Python3"
    echo "2. 是否已安装依赖包: pip3 install -r requirements.txt"
    echo "3. 是否有权限访问相关文件"
    read -p "按任意键退出..."
fi 