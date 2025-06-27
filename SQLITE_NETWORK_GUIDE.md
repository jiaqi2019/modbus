# SQLite网络访问解决方案

## 概述

由于SQLite本身不支持网络协议，我们通过HTTP API的方式实现了多设备访问SQLite数据库的功能。

## 架构设计

```
设备1 (数据写入)    设备2-6 (数据读取)
     ↓                    ↑
  SQLite服务器 (HTTP API)
     ↓
  SQLite数据库文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 启动服务器（数据写入设备）

在数据写入设备上运行：

```bash
python src/sqlite_server.py --host 0.0.0.0 --port 5000
```

参数说明：
- `--host`: 服务器地址，0.0.0.0表示监听所有网络接口
- `--port`: 服务器端口，默认5000
- `--debug`: 启用调试模式

### 2. 客户端访问（其他设备）

在其他设备上使用客户端访问：

```python
from src.sqlite_client import SQLiteClient

# 连接到服务器
client = SQLiteClient("http://192.168.1.100:5000")  # 替换为实际服务器IP

# 获取所有电机数据
motors = client.get_all_motors()

# 获取特定电机数据
motor_data = client.get_motor_data(1, limit=100)

# 获取最新数据
latest = client.get_motor_latest(1)
```

## API接口

### 基础接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 获取服务器状态 |
| `/api/motors` | GET | 获取所有电机数据 |
| `/api/motors/{id}` | GET | 获取指定电机数据 |
| `/api/motors/{id}/latest` | GET | 获取指定电机最新数据 |
| `/api/motors/{id}/range` | GET | 获取时间范围数据 |
| `/api/stats` | GET | 获取数据库统计 |
| `/api/cleanup` | POST | 清理旧数据 |
| `/api/optimize` | POST | 优化数据库 |

### 示例请求

```bash
# 获取服务器状态
curl http://192.168.1.100:5000/api/status

# 获取电机1的数据
curl http://192.168.1.100:5000/api/motors/1?limit=10

# 获取电机1最近1小时数据
curl "http://192.168.1.100:5000/api/motors/1/range?start=2024-01-01T10:00:00&end=2024-01-01T11:00:00"
```

## 配置说明

### 服务器配置 (server_config.json)

```json
{
    "server": {
        "host": "0.0.0.0",        // 监听地址
        "port": 5000,             // 监听端口
        "debug": false,           // 调试模式
        "max_connections": 100    // 最大连接数
    },
    "database": {
        "path": "motor_data.db",  // 数据库文件路径
        "backup_enabled": true,   // 启用备份
        "cleanup_enabled": true,  // 启用自动清理
        "cleanup_days": 90        // 保留天数
    }
}
```

## 性能优化

### 1. 数据库优化

```python
# 定期清理旧数据
client.cleanup_data(days=90)

# 优化数据库
client.optimize_database()
```

### 2. 网络优化

- 使用内网连接，避免公网延迟
- 设置合适的超时时间
- 使用连接池复用连接

### 3. 缓存策略

```python
# 客户端缓存示例
import time

class CachedClient(SQLiteClient):
    def __init__(self, server_url, cache_timeout=60):
        super().__init__(server_url)
        self.cache = {}
        self.cache_timeout = cache_timeout
    
    def get_motor_latest(self, motor_id):
        cache_key = f"motor_{motor_id}_latest"
        now = time.time()
        
        # 检查缓存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if now - timestamp < self.cache_timeout:
                return cached_data
        
        # 获取新数据
        data = super().get_motor_latest(motor_id)
        if data:
            self.cache[cache_key] = (data, now)
        
        return data
```

## 安全考虑

### 1. 网络安全

- 使用防火墙限制访问IP
- 配置HTTPS（生产环境）
- 设置访问白名单

### 2. 数据安全

- 定期备份数据库
- 监控磁盘空间
- 设置数据保留策略

## 故障排除

### 1. 连接问题

```bash
# 检查网络连通性
ping 192.168.1.100

# 检查端口是否开放
telnet 192.168.1.100 5000
```

### 2. 性能问题

```python
# 检查数据库大小
stats = client.get_stats()
print(f"数据库大小: {stats['stats']['file_size_mb']} MB")
print(f"记录数: {stats['stats']['total_records']}")
```

### 3. 日志查看

```bash
# 查看服务器日志
tail -f server.log
```

## 扩展功能

### 1. 数据导出

```python
# 导出CSV格式
import csv

def export_to_csv(client, motor_id, filename):
    data = client.get_motor_data(motor_id, limit=10000)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Motor_ID', 'Timestamp', 'Phase_A_Current', ...])
        for row in data['data']:
            writer.writerow(row)
```

### 2. 实时监控

```python
# 实时数据监控
import time

def monitor_motor(client, motor_id, interval=5):
    while True:
        data = client.get_motor_latest(motor_id)
        if data:
            print(f"电机{motor_id}: {data['data']}")
        time.sleep(interval)
```

## 总结

通过HTTP API的方式，我们成功实现了多设备访问SQLite数据库的需求。这种方案具有以下优势：

1. **简单易用**：基于HTTP协议，易于理解和实现
2. **跨平台**：支持各种编程语言和平台
3. **可扩展**：可以轻松添加新功能和接口
4. **性能良好**：适合中小规模的数据访问需求

对于大规模或高并发场景，建议考虑使用专业的数据库服务器（如PostgreSQL、MySQL等）。 