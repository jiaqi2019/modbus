#!/bin/bash

# 麒麟系统桌面快捷方式安装脚本
# 为Modbus客户端和WebSocket客户端创建桌面快捷方式

echo "=== 麒麟系统桌面快捷方式安装脚本 ==="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目目录: $SCRIPT_DIR"

# 检查是否为麒麟系统
if [[ "$(uname -s)" != "Linux" ]]; then
    echo "错误: 此脚本仅适用于Linux系统（包括麒麟系统）"
    exit 1
fi

# 检查用户权限
if [[ "$EUID" -eq 0 ]]; then
    echo "警告: 不建议以root用户运行此脚本"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 获取用户桌面目录
DESKTOP_DIR="$HOME/Desktop"
if [[ ! -d "$DESKTOP_DIR" ]]; then
    DESKTOP_DIR="$HOME/桌面"
fi

if [[ ! -d "$DESKTOP_DIR" ]]; then
    echo "错误: 无法找到桌面目录"
    echo "请手动将.desktop文件复制到桌面目录"
    exit 1
fi

echo "桌面目录: $DESKTOP_DIR"

# 给启动脚本添加执行权限
echo "设置启动脚本权限..."
chmod +x "$SCRIPT_DIR/src/modbus_client/launch_modbus_client.sh"
chmod +x "$SCRIPT_DIR/src/websocket_client/launch_websocket_client.sh"

# 更新.desktop文件中的路径
echo "更新桌面快捷方式文件..."

# Modbus客户端桌面文件
cat > "$SCRIPT_DIR/Modbus客户端.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Modbus客户端
Name[zh_CN]=Modbus客户端
Comment=电机监控系统 - Modbus客户端
Comment[zh_CN]=电机监控系统 - Modbus客户端
Exec=$SCRIPT_DIR/src/modbus_client/launch_modbus_client.sh
Icon=applications-internet
Terminal=true
Categories=Network;Development;
Keywords=modbus;motor;monitor;client;
StartupNotify=true
EOF

# WebSocket客户端桌面文件
cat > "$SCRIPT_DIR/WebSocket客户端.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=WebSocket客户端
Name[zh_CN]=WebSocket客户端
Comment=电机监控系统 - WebSocket客户端
Comment[zh_CN]=电机监控系统 - WebSocket客户端
Exec=$SCRIPT_DIR/src/websocket_client/launch_websocket_client.sh
Icon=applications-internet
Terminal=true
Categories=Network;Development;
Keywords=websocket;motor;monitor;client;
StartupNotify=true
EOF

# 复制桌面文件到桌面目录
echo "复制桌面快捷方式到桌面..."
cp "$SCRIPT_DIR/Modbus客户端.desktop" "$DESKTOP_DIR/"
cp "$SCRIPT_DIR/WebSocket客户端.desktop" "$DESKTOP_DIR/"

# 设置桌面文件权限
chmod +x "$DESKTOP_DIR/Modbus客户端.desktop"
chmod +x "$DESKTOP_DIR/WebSocket客户端.desktop"

# 更新桌面数据库
echo "更新桌面数据库..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo ""
echo "=== 安装完成 ==="
echo "桌面快捷方式已创建："
echo "1. Modbus客户端"
echo "2. WebSocket客户端"
echo ""
echo "现在你可以双击桌面上的图标来启动应用程序了！"
echo ""
echo "注意事项："
echo "1. 确保已安装Python3和必要的依赖包"
echo "2. 如果遇到权限问题，请检查文件权限"
echo "3. 如果快捷方式不工作，请检查终端输出信息" 