import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="motor_data.db"):
        """初始化数据库管理器"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建电机数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS motor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        motor_id INTEGER NOT NULL,
                        timestamp DATETIME NOT NULL,
                        phase_a_current REAL,
                        phase_b_current REAL,
                        phase_c_current REAL,
                        frequency REAL,
                        reactive_power REAL,
                        active_power REAL,
                        line_voltage REAL,
                        excitation_voltage REAL,
                        excitation_current REAL,
                        calculated_excitation_current REAL,
                        excitation_current_ratio REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_motor_data_motor_id 
                    ON motor_data(motor_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_motor_data_timestamp 
                    ON motor_data(timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_motor_data_motor_timestamp 
                    ON motor_data(motor_id, timestamp)
                ''')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def save_motor_data(self, motor_data):
        """保存单个电机数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO motor_data (
                        motor_id, timestamp, phase_a_current, phase_b_current, 
                        phase_c_current, frequency, reactive_power, active_power,
                        line_voltage, excitation_voltage, excitation_current,
                        calculated_excitation_current, excitation_current_ratio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    motor_data.motor_id,
                    motor_data.last_update.isoformat() if motor_data.last_update else datetime.now().isoformat(),
                    motor_data.phase_a_current,
                    motor_data.phase_b_current,
                    motor_data.phase_c_current,
                    motor_data.frequency,
                    motor_data.reactive_power,
                    motor_data.active_power,
                    motor_data.line_voltage,
                    motor_data.excitation_voltage,
                    motor_data.excitation_current,
                    motor_data.calculated_excitation_current,
                    motor_data.excitation_current_ratio
                ))
                
                conn.commit()
                logger.info(f"电机 {motor_data.motor_id} 数据已保存到数据库")
                
        except Exception as e:
            logger.error(f"保存电机 {motor_data.motor_id} 数据失败: {str(e)}")
    
    def save_all_motors_data(self, motors):
        """保存所有电机数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for motor in motors:
                    cursor.execute('''
                        INSERT INTO motor_data (
                            motor_id, timestamp, phase_a_current, phase_b_current, 
                            phase_c_current, frequency, reactive_power, active_power,
                            line_voltage, excitation_voltage, excitation_current,
                            calculated_excitation_current, excitation_current_ratio
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        motor.motor_id,
                        motor.last_update.isoformat() if motor.last_update else datetime.now().isoformat(),
                        motor.phase_a_current,
                        motor.phase_b_current,
                        motor.phase_c_current,
                        motor.frequency,
                        motor.reactive_power,
                        motor.active_power,
                        motor.line_voltage,
                        motor.excitation_voltage,
                        motor.excitation_current,
                        motor.calculated_excitation_current,
                        motor.excitation_current_ratio
                    ))
                
                conn.commit()
                logger.info(f"所有电机数据已保存到数据库，共 {len(motors)} 台电机")
                
        except Exception as e:
            logger.error(f"保存所有电机数据失败: {str(e)}")
    
    def get_motor_data(self, motor_id, limit=100):
        """获取指定电机的历史数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM motor_data 
                    WHERE motor_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (motor_id, limit))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取电机 {motor_id} 数据失败: {str(e)}")
            return []
    
    def get_latest_motor_data(self, motor_id):
        """获取指定电机的最新数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM motor_data 
                    WHERE motor_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (motor_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            logger.error(f"获取电机 {motor_id} 最新数据失败: {str(e)}")
            return None
    
    def get_data_by_time_range(self, motor_id, start_time, end_time):
        """获取指定时间范围内的电机数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM motor_data 
                    WHERE motor_id = ? AND timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                ''', (motor_id, start_time.isoformat(), end_time.isoformat()))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取电机 {motor_id} 时间范围数据失败: {str(e)}")
            return []
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取总记录数
                cursor.execute('SELECT COUNT(*) FROM motor_data')
                total_records = cursor.fetchone()[0]
                
                # 获取电机数量
                cursor.execute('SELECT COUNT(DISTINCT motor_id) FROM motor_data')
                motor_count = cursor.fetchone()[0]
                
                # 获取数据时间范围
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM motor_data')
                time_range = cursor.fetchone()
                
                # 获取数据库文件大小
                file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # 获取每个电机的记录数
                cursor.execute('''
                    SELECT motor_id, COUNT(*) as record_count 
                    FROM motor_data 
                    GROUP BY motor_id 
                    ORDER BY motor_id
                ''')
                motor_records = cursor.fetchall()
                
                return {
                    'total_records': total_records,
                    'motor_count': motor_count,
                    'time_range': time_range,
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'motor_records': motor_records,
                    'avg_record_size_bytes': round(file_size / total_records, 2) if total_records > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days_to_keep=90):
        """清理指定天数之前的数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 计算截止日期
                from datetime import timedelta
                cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
                
                # 删除旧数据
                cursor.execute('''
                    DELETE FROM motor_data 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"清理了 {deleted_count} 条旧数据（保留最近 {days_to_keep} 天）")
                return deleted_count
                
        except Exception as e:
            logger.error(f"清理旧数据失败: {str(e)}")
            return 0
    
    def optimize_database(self):
        """优化数据库（压缩和重建索引）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取优化前的文件大小
                size_before = os.path.getsize(self.db_path)
                
                # 执行VACUUM命令压缩数据库
                cursor.execute('VACUUM')
                
                # 重新分析表统计信息
                cursor.execute('ANALYZE')
                
                # 获取优化后的文件大小
                size_after = os.path.getsize(self.db_path)
                size_saved = size_before - size_after
                
                logger.info(f"数据库优化完成，节省空间: {size_saved} 字节 ({round(size_saved/1024/1024, 2)} MB)")
                return size_saved
                
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
            return 0
    
    def get_storage_recommendations(self):
        """获取存储建议"""
        stats = self.get_database_stats()
        
        if not stats:
            return "无法获取数据库统计信息"
        
        recommendations = []
        
        # 文件大小建议
        if stats['file_size_mb'] > 1000:  # 超过1GB
            recommendations.append("数据库文件超过1GB，建议进行数据归档或清理")
        
        # 记录数建议
        if stats['total_records'] > 1000000:  # 超过100万条
            recommendations.append("记录数超过100万条，查询性能可能下降，建议优化索引")
        
        # 平均记录大小分析
        avg_size = stats['avg_record_size_bytes']
        if avg_size > 500:
            recommendations.append(f"平均记录大小较大({avg_size}字节)，建议检查数据类型")
        
        if not recommendations:
            recommendations.append("数据库状态良好，无需特殊优化")
        
        return recommendations 