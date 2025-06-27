import sqlite3
import os
from datetime import datetime
import argparse

def view_database_stats(db_path="motor_data.db"):
    """查看数据库统计信息"""
    try:
        with sqlite3.connect(db_path) as conn:
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
            
            print("=== 数据库统计信息 ===")
            print(f"总记录数: {total_records}")
            print(f"电机数量: {motor_count}")
            if time_range[0] and time_range[1]:
                print(f"数据时间范围: {time_range[0]} 到 {time_range[1]}")
            print("=====================")
            
    except Exception as e:
        print(f"查看数据库统计信息失败: {str(e)}")

def view_motor_data(motor_id, limit=10, db_path="motor_data.db"):
    """查看指定电机的数据"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT motor_id, timestamp, phase_a_current, phase_b_current, 
                       phase_c_current, frequency, reactive_power, active_power,
                       line_voltage, excitation_voltage, excitation_current,
                       calculated_excitation_current, excitation_current_ratio
                FROM motor_data 
                WHERE motor_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (motor_id, limit))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"电机 {motor_id} 没有数据")
                return
            
            print(f"=== 电机 {motor_id} 最新 {len(rows)} 条数据 ===")
            print("时间戳 | A相电流 | B相电流 | C相电流 | 频率 | 无功功率 | 有功功率 | 线电压 | 励磁电压 | 励磁电流 | 计算励磁电流 | 励磁电流比值")
            print("-" * 150)
            
            for row in rows:
                print(f"{row[1]} | {row[2]:.2f} | {row[3]:.2f} | {row[4]:.2f} | {row[5]:.2f} | {row[6]:.2f} | {row[7]:.2f} | {row[8]:.2f} | {row[9]:.2f} | {row[10]:.2f} | {row[11]:.2f} | {row[12]*100:.2f}%")
            
            print("=" * 150)
            
    except Exception as e:
        print(f"查看电机 {motor_id} 数据失败: {str(e)}")

def view_all_motors_latest(db_path="motor_data.db"):
    """查看所有电机的最新数据"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 获取所有电机的最新数据
            cursor.execute('''
                SELECT motor_id, timestamp, phase_a_current, phase_b_current, 
                       phase_c_current, frequency, reactive_power, active_power,
                       line_voltage, excitation_voltage, excitation_current,
                       calculated_excitation_current, excitation_current_ratio
                FROM motor_data m1
                WHERE timestamp = (
                    SELECT MAX(timestamp) 
                    FROM motor_data m2 
                    WHERE m2.motor_id = m1.motor_id
                )
                ORDER BY motor_id
            ''')
            
            rows = cursor.fetchall()
            
            if not rows:
                print("数据库中没有数据")
                return
            
            print("=== 所有电机最新数据 ===")
            print("电机ID | 时间戳 | A相电流 | B相电流 | C相电流 | 频率 | 无功功率 | 有功功率 | 线电压 | 励磁电压 | 励磁电流 | 计算励磁电流 | 励磁电流比值")
            print("-" * 160)
            
            for row in rows:
                print(f"{row[0]} | {row[1]} | {row[2]:.2f} | {row[3]:.2f} | {row[4]:.2f} | {row[5]:.2f} | {row[6]:.2f} | {row[7]:.2f} | {row[8]:.2f} | {row[9]:.2f} | {row[10]:.2f} | {row[11]:.2f} | {row[12]*100:.2f}%")
            
            print("=" * 160)
            
    except Exception as e:
        print(f"查看所有电机最新数据失败: {str(e)}")

def export_data_to_csv(motor_id, output_file, db_path="motor_data.db"):
    """导出指定电机的数据到CSV文件"""
    try:
        import csv
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT motor_id, timestamp, phase_a_current, phase_b_current, 
                       phase_c_current, frequency, reactive_power, active_power,
                       line_voltage, excitation_voltage, excitation_current,
                       calculated_excitation_current, excitation_current_ratio
                FROM motor_data 
                WHERE motor_id = ? 
                ORDER BY timestamp ASC
            ''', (motor_id,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"电机 {motor_id} 没有数据可导出")
                return
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                writer.writerow([
                    '电机ID', '时间戳', 'A相电流', 'B相电流', 'C相电流', 
                    '频率', '无功功率', '有功功率', '线电压', '励磁电压', 
                    '励磁电流', '计算励磁电流', '励磁电流比值'
                ])
                
                # 写入数据
                for row in rows:
                    writer.writerow([
                        row[0], row[1], row[2], row[3], row[4], row[5], 
                        row[6], row[7], row[8], row[9], row[10], row[11], 
                        f"{row[12]*100:.2f}%"
                    ])
            
            print(f"电机 {motor_id} 的数据已导出到 {output_file}，共 {len(rows)} 条记录")
            
    except Exception as e:
        print(f"导出数据失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='电机数据数据库查看工具')
    parser.add_argument('--db', default='motor_data.db', help='数据库文件路径')
    parser.add_argument('--stats', action='store_true', help='查看数据库统计信息')
    parser.add_argument('--motor', type=int, help='查看指定电机的数据')
    parser.add_argument('--limit', type=int, default=10, help='显示记录数量限制')
    parser.add_argument('--all', action='store_true', help='查看所有电机的最新数据')
    parser.add_argument('--export', type=int, help='导出指定电机的数据到CSV')
    parser.add_argument('--output', help='CSV输出文件名')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"数据库文件 {args.db} 不存在")
        return
    
    if args.stats:
        view_database_stats(args.db)
    elif args.motor:
        view_motor_data(args.motor, args.limit, args.db)
    elif args.all:
        view_all_motors_latest(args.db)
    elif args.export:
        if not args.output:
            args.output = f"motor_{args.export}_data.csv"
        export_data_to_csv(args.export, args.output, args.db)
    else:
        # 默认显示统计信息
        view_database_stats(args.db)

if __name__ == "__main__":
    main() 