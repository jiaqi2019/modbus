# 电机监控系统

这是一个基于 Modbus TCP 的电机监控系统，可以实时监控多台电机的运行参数，并将数据保存到 SQLite 数据库中。

## 功能特性

- 实时监控多台电机的运行参数
- 自动计算励磁电流和故障判断值
- 数据自动保存到 SQLite 数据库
- 支持自动更新数据（可配置）
- 图形化用户界面
- 数据导出功能

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

编辑 `src/config.json` 文件：

```json
{
    "modbus": {
        "host": "localhost",
        "port": 5020,
        "motor_count": 12
    },
    "auto_update": {
        "enabled": 1,
        "interval": 5
    }
}
```

- `host`: Modbus 服务器地址
- `port`: Modbus 服务器端口
- `motor_count`: 电机数量
- `auto_update.enabled`: 是否启用自动更新（1=启用，0=禁用）
- `auto_update.interval`: 自动更新间隔（秒）

## 运行

### 启动监控系统

```bash
python src/run_main.py
```

### 查看数据库数据

```bash
# 查看数据库统计信息
python src/db/db_viewer.py --stats

# 查看指定电机的最新数据
python src/db/db_viewer.py --motor 1 --limit 10

# 查看所有电机的最新数据
python src/db/db_viewer.py --all

# 导出指定电机的数据到CSV
python src/db/db_viewer.py --export 1 --output motor_1_data.csv
```

## 数据库结构

系统会自动创建 `motor_data.db` SQLite 数据库文件，包含以下表结构：

### motor_data 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| motor_id | INTEGER | 电机ID |
| timestamp | DATETIME | 数据时间戳 |
| phase_a_current | REAL | A相电流 (A) |
| phase_b_current | REAL | B相电流 (A) |
| phase_c_current | REAL | C相电流 (A) |
| frequency | REAL | 频率 (Hz) |
| reactive_power | REAL | 无功功率 (kVar) |
| active_power | REAL | 有功功率 (kW) |
| line_voltage | REAL | AB相线电压 (kV) |
| excitation_voltage | REAL | 励磁电压 (V) |
| excitation_current | REAL | 励磁电流 (A) |
| calculated_excitation_current | REAL | 计算得到的励磁电流 (A) |
| excitation_current_ratio | REAL | 励磁电流比值 |
| created_at | DATETIME | 记录创建时间 |

## 数据流程

1. 系统启动时连接到 Modbus 服务器
2. 如果配置了自动更新，系统会自动开始定期请求数据
3. 接收到数据后，系统会：
   - 解析电机参数
   - 计算励磁电流和故障判断值
   - 保存数据到 SQLite 数据库
   - 保存数据到 JSON 日志文件
   - 更新图形界面显示

## 故障判断

系统会根据励磁电流比值进行故障判断：
- 比值 > 5%: 显示红色警告
- 比值 ≤ 5%: 显示绿色正常

## 文件结构

```
qilin/
├── README.md
├── requirements.txt
├── src/
│   ├── run_main.py          # 主程序启动脚本
│   ├── config.json          # 配置文件
│   ├── server_config.json   # 服务器配置
│   ├── websocket_server.py  # WebSocket服务器
│   ├── modbus-client/       # Modbus客户端模块
│   │   ├── __init__.py
│   │   ├── main.py          # 主程序
│   │   └── modbus_client.py # Modbus客户端
│   ├── modbus-server/       # Modbus服务器模块
│   │   └── modbus_server.py
│   ├── db/                  # 数据库模块
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库管理
│   │   └── db_viewer.py     # 数据库查看工具
│   ├── calc/                # 计算模块
│   │   ├── __init__.py
│   │   ├── calc_1_2.py      # 电机1-2计算模块
│   │   ├── calc_3_4.py      # 电机3-4计算模块
│   │   ├── calc_5_6.py      # 电机5-6计算模块
│   │   ├── calc_7_8.py      # 电机7-8计算模块
│   │   ├── calc_9_10.py     # 电机9-10计算模块
│   │   └── calc_11_12.py    # 电机11-12计算模块
│   └── websocket-client/    # WebSocket客户端
└── vb/                      # Visual Basic 计算模块
    ├── 1-2.vb
    ├── 3-4.vb
    ├── 5-6.vb
    ├── 7-8.vb
    ├── 9-10.vb
    └── 11-12.vb
```

## 注意事项

- 确保 Modbus 服务器正在运行并可访问
- 数据库文件会自动创建在程序运行目录下
- 自动更新功能需要配置 `auto_update.enabled` 为 1
- 数据会同时保存到数据库和 JSON 日志文件中

