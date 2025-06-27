# 电机故障监控系统

这是一个基于Modbus协议的电机故障监控系统，支持实时数据采集、故障判断、数据存储、图表生成和UDP数据同步。

## 功能特性

- **实时数据采集**: 通过Modbus协议采集电机运行数据
- **故障判断**: 基于励磁电流比值进行故障判断
- **数据库存储**: 使用SQLite数据库存储历史数据
- **图表生成**: 自动生成故障判断值趋势图
- **UDP数据同步**: 支持向其他设备发送数据
- **电流数据处理**: 自动处理不同量级的电流数据

## 安装步骤

### 1. 安装 Python 和 pip

```bash
# 更新包列表
sudo apt update

# 安装 Python3
sudo apt install python3

# 安装 pip3
sudo apt install python3-pip

# 验证安装
python3 --version
pip3 --version
```

Windows:
```bash
python --version
pip --version
```

### 2. 安装依赖包

```bash
# 安装所有依赖包
pip install -r requirements.txt
```

或者手动安装：
```bash
# 安装 Modbus 通信库
pip install pymodbus>=3.0.0

# 安装图表生成库
pip install matplotlib>=3.7.0

# 安装数值计算库
pip install numpy>=1.24.0

# 安装 tkinter (如果尚未安装)
# Ubuntu/Debian:
sudo apt-get install python3-tk

# Windows:
# tkinter 通常随 Python 一起安装，如果没有，请重新安装 Python 并确保选中 tkinter 选项
```

## 系统架构

### 核心模块

1. **modbus_client.py**: Modbus客户端，负责数据采集和解析
2. **database_manager.py**: 数据库管理器，负责数据存储和查询
3. **udp_sender.py**: UDP发送器，负责数据同步
4. **calc_*.py**: 故障计算模块，用于不同电机的故障判断

### 数据库结构

- **fault_records**: 存储故障判断值记录
- **daily_averages**: 存储每日平均值（可选，用于提高查询性能）

## 使用方法

### 1. 基本数据采集

```python
from modbus_client import ModbusClient

# 创建Modbus客户端
client = ModbusClient()

# 连接并采集数据
if client.connect():
    client.request_motor_data()
    client.disconnect()
```

### 2. 生成故障判断值曲线图

```python
from database_manager import DatabaseManager
from datetime import date, timedelta

# 创建数据库管理器
db_manager = DatabaseManager()

# 生成最近7天的图表
end_date = date.today()
start_date = end_date - timedelta(days=7)

db_manager.generate_fault_curve(
    start_date=start_date,
    end_date=end_date,
    motor_ids=[1, 2, 3, 4, 5, 6],
    save_path="fault_trend_chart.png"
)
```

### 3. UDP数据发送

```python
from udp_sender import UDPSender

# 配置目标设备
target_devices = [
    {'ip': '192.168.1.100', 'name': '设备1'},
    {'ip': '192.168.1.101', 'name': '设备2'},
    {'ip': '192.168.1.102', 'name': '设备3'},
    {'ip': '192.168.1.103', 'name': '设备4'}
]

# 创建UDP发送器
sender = UDPSender(target_devices, port=8888, interval=3600)

# 启动发送服务
sender.start()

# 立即发送一次数据
sender.send_immediate(days=7)
```

### 4. UDP数据接收

```python
from udp_sender import UDPReceiver

# 创建UDP接收器
receiver = UDPReceiver(host='0.0.0.0', port=8888)

# 设置数据接收回调函数
def handle_received_data(data, addr):
    print(f"接收到来自 {addr[0]}:{addr[1]} 的数据")
    print(f"数据时间范围: {data.get('data_range', {})}")
    print(f"电机数量: {len(data.get('motors', {}))}")

receiver.set_data_callback(handle_received_data)

# 启动接收服务
receiver.start()
```

### 5. 运行示例

```bash
# 运行完整示例
python src/example_usage.py
```

## 配置说明

### 配置文件 (config.json)

```json
{
  "modbus": {
    "host": "localhost",
    "port": 5020,
    "motor_count": 12
  }
}
```

### 数据库配置

- 默认数据库文件: `motor_fault_data.db`
- 自动创建表结构和索引
- 支持数据清理（默认保留90天数据）

## 数据格式

### 故障判断值

- 范围: 0-1
- 单位: 比值（百分比）
- 存储: 每日平均值

### UDP数据格式

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "data_range": {
    "start_date": "2023-12-25",
    "end_date": "2024-01-01"
  },
  "motors": {
    "motor_1": {
      "daily_averages": [
        {
          "date": "2023-12-25",
          "avg_fault_value": 0.75,
          "record_count": 24
        }
      ],
      "overall_avg": 0.78
    }
  }
}
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查文件权限
   - 确保磁盘空间充足

2. **图表生成失败**
   - 检查matplotlib安装
   - 确保有中文字体支持

3. **UDP发送失败**
   - 检查网络连接
   - 确认目标设备IP地址正确
   - 检查防火墙设置

### 日志查看

系统会生成详细的日志信息，包括：
- 数据采集状态
- 数据库操作记录
- UDP发送/接收状态
- 错误信息

## 性能优化

1. **数据库优化**
   - 定期清理旧数据
   - 使用索引提高查询性能

2. **网络优化**
   - 调整UDP发送间隔
   - 使用数据压缩（可选）

3. **内存优化**
   - 限制图表显示的数据量
   - 及时释放不需要的数据

## 扩展功能

- 支持更多电机类型
- 添加Web界面
- 实现数据备份和恢复
- 支持多种图表类型
- 添加告警功能

