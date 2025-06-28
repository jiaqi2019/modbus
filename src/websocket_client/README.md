# WebSocket客户端

这是一个用于接收和显示电机数据的WebSocket客户端应用程序。

## 功能特性

- **实时数据接收**: 通过WebSocket连接接收服务器广播的电机数据
- **自动重连**: 连接断开时自动尝试重连
- **数据存储**: 将接收到的数据自动保存到SQLite数据库
- **实时显示**: 实时显示电机数据和故障检测趋势图
- **配置管理**: 支持配置WebSocket服务器地址和端口

## 主流程

1. **启动后初始化**
   - 初始化WebSocket客户端
   - 初始化数据库连接
   - 加载配置文件

2. **连接流程**
   - 如果有配置数据，自动尝试连接WebSocket服务器
   - 如果无配置数据或连接失败，等待用户修改配置
   - 用户点击重新连接后，重复连接流程

3. **数据监控**
   - 连接成功后，持续接收广播数据
   - 调用数据库模块，将数据存储到数据库
   - 插入data_display和chart_display组件展示数据

## 文件结构

```
websocket_client/
├── __init__.py              # 模块初始化文件
├── config.py                # 配置管理模块
├── websocket_client.py      # WebSocket客户端核心模块
├── data_processor.py        # 数据处理器
├── top_menu.py              # 顶部配置菜单UI组件
├── main_ui.py               # 主UI框架
├── run_client.py            # 启动脚本
└── README.md                # 使用说明
```

## 使用方法

### 1. 启动客户端

```bash
# 方法1: 使用启动脚本
python src/websocket_client/run_client.py

# 方法2: 直接运行主UI
python src/websocket_client/main_ui.py
```

### 2. 配置连接

1. 在顶部配置菜单中输入WebSocket服务器地址和端口
2. 点击"保存配置"按钮保存设置
3. 点击"连接"按钮建立连接

### 3. 监控数据

- 连接成功后，客户端会自动接收和显示电机数据
- 每个电机都有独立的数据显示区域和趋势图表
- 数据会自动保存到数据库中

## 配置说明

配置文件: `websocket_config.json`

```json
{
  "websocket": {
    "host": "localhost",
    "port": 8765
  },
  "database": {
    "path": "motor_data.db"
  },
  "ui": {
    "auto_connect": true,
    "auto_reconnect": true,
    "reconnect_interval": 5
  }
}
```

## 数据格式

WebSocket服务器发送的数据格式应为：

### 完整数据格式 (type: "motor_data")

```json
{
  "type": "motor_data",
  "data": [
    {
      "motor_id": 1,
      "phase_a_current": 10.5,
      "phase_b_current": 10.3,
      "phase_c_current": 10.4,
      "frequency": 50.0,
      "reactive_power": 100.0,
      "active_power": 500.0,
      "line_voltage": 6.0,
      "excitation_voltage": 220.0,
      "excitation_current": 5.0,
      "calculated_excitation_current": 5.1
    }
  ]
}
```

### 增量更新格式 (type: "motor_update")

```json
{
  "type": "motor_update",
  "data": [
    {
      "motor_id": 1,
      "phase_a_current": 10.6,
      "excitation_current": 5.2
    }
  ]
}
```

### 最新数据格式 (type: "latest_data")

```json
{
  "type": "latest_data",
  "data": [
    {
      "motor_id": 1,
      "phase_a_current": 10.7,
      "phase_b_current": 10.5,
      "excitation_current": 5.3
    }
  ]
}
```

### 状态消息格式 (type: "status")

```json
{
  "type": "status",
  "status": "connected"
}
```

## 支持的消息类型

- **motor_data**: 完整的电机数据，包含所有字段
- **motor_update**: 增量更新数据，只包含变化的字段
- **latest_data**: 最新数据更新，通常包含部分字段的最新值
- **status**: 状态消息，用于服务器状态通知

## 依赖要求

- Python 3.7+
- websockets==11.0.3
- matplotlib==3.7.2
- numpy==1.24.3
- scipy==1.11.1

## 故障排除

### 连接失败
1. 检查WebSocket服务器是否正在运行
2. 确认服务器地址和端口配置正确
3. 检查网络连接是否正常

### 数据显示异常
1. 检查数据格式是否符合要求
2. 查看日志文件获取详细错误信息
3. 确认数据库文件权限正确

### 界面显示问题
1. 确保安装了所有UI依赖包
2. 检查Python版本兼容性
3. 重启应用程序

## 日志文件

应用程序运行时会生成日志文件：
- `websocket_client.log`: 详细的运行日志
- 包含连接状态、数据处理、错误信息等

## 开发说明

如需修改或扩展功能：

1. **添加新的数据字段**: 修改`data_processor.py`中的`MotorData`类
2. **自定义UI组件**: 修改`main_ui.py`中的显示逻辑
3. **扩展数据处理**: 在`data_processor.py`中添加新的处理方法
4. **修改配置项**: 更新`config.py`中的配置结构
5. **添加新的消息类型**: 在`data_processor.py`的`process_websocket_message`方法中添加新的处理分支 