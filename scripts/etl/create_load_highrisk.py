#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高风险人员数据建表 + 导入MySQL
替代 Shell 版本，使用 Python 实现

运行方式（在虚拟机上）：
  python3 01_create_load_highrisk.py
"""

import pymysql
import csv
import os

# ============================================================
# MySQL 连接配置
# 优先环境变量，其次 config/local_config.py（不入库），默认 localhost
# ============================================================
import sys as _sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)
try:
    from config import local_config
except Exception:
    local_config = None

def _db_cfg(name, default):
    value = os.environ.get(name)
    if value:
        return value
    return getattr(local_config, name, None) if local_config else None or default

MYSQL_CONFIG = {
    'host': _db_cfg('MYSQL_HOST', 'localhost'),
    'port': int(_db_cfg('MYSQL_PORT', '3306')),
    'user': _db_cfg('MYSQL_USER', 'root'),
    'password': _db_cfg('MYSQL_PASSWORD', ''),
    'database': _db_cfg('MYSQL_DATABASE', 'data'),
    'charset': 'utf8mb4'
}

INPUT_DIR = "/home/hadoop/temp/analysis_results/abnormal_results"
OUTPUT_FILE = "/home/hadoop/temp/analysis_results/high_risk_input.csv"

# ============================================================
# Step 1: 建表 DDL
# ============================================================
print("=" * 60)
print("  高风险人员数据导入MySQL")
print("=" * 60)

print("\n[Step 1] 创建高风险人员表...")

DDL = """
DROP TABLE IF EXISTS high_risk_person;
CREATE TABLE high_risk_person (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_id VARCHAR(50) COMMENT '人员ID',
    user_name VARCHAR(50) COMMENT '姓名',
    abnormal_type VARCHAR(100) COMMENT '异常类型',
    abnormal_amount DECIMAL(12,2) COMMENT '异常金额',
    risk_level VARCHAR(20) COMMENT '风险等级',
    abnormal_prob DECIMAL(10,4) COMMENT '异常概率',
    detection_date VARCHAR(20) COMMENT '检测日期',
    abnormal_desc VARCHAR(500) COMMENT '异常说明',
    age_group VARCHAR(20) COMMENT '年龄段',
    insurance_type VARCHAR(50) COMMENT '参保类型',
    visit_count INT COMMENT '就诊次数'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='高风险人员名单';
"""

conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor()
for statement in DDL.strip().split(';'):
    stmt = statement.strip()
    if stmt:
        cursor.execute(stmt)
conn.commit()
cursor.close()
conn.close()
print("  建表完成")

# ============================================================
# Step 2: 预处理CSV - Spark逗号分隔 → 管道符分隔 + 衍生字段
# ============================================================
print("\n[Step 2] 预处理CSV数据...")

output_rows = []
for fname in os.listdir(INPUT_DIR):
    if fname.startswith("part-") and fname.endswith(".csv"):
        fpath = os.path.join(INPUT_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('risk_level', '') != '高风险':
                    continue

                user_id = row.get('person_id', '')
                visit_count = int(float(row.get('visit_count', 0)))
                avg_visit_amount = float(row.get('avg_visit_amount', 0))
                total_amount = float(row.get('total_amount', 0))
                abnormal_prob = float(row.get('abnormal_prob', 0))

                # 推断异常类型
                abnormal_types = []
                if visit_count > 12:
                    abnormal_types.append("频繁就诊")
                if avg_visit_amount > 6000:
                    abnormal_types.append("高额次均费用")
                if total_amount > 50000:
                    abnormal_types.append("总费用异常")
                abnormal_type = "、".join(abnormal_types) if abnormal_types else "综合异常"

                # 异常说明
                desc_parts = []
                desc_parts.append(f"就诊{visit_count}次")
                desc_parts.append(f"次均{avg_visit_amount:.0f}元")
                desc_parts.append(f"总计{total_amount:.0f}元")
                abnormal_desc = "；".join(desc_parts)

                output_rows.append([
                    user_id,
                    user_id,
                    abnormal_type,
                    f"{total_amount:.2f}",
                    row.get('risk_level', '高风险'),
                    f"{abnormal_prob:.4f}",
                    "2026-07-05",
                    abnormal_desc,
                    row.get('age_group', ''),
                    row.get('insurance_type', ''),
                    str(visit_count)
                ])

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for row in output_rows:
        f.write('|'.join(row) + '\n')

print(f"  预处理完成: {len(output_rows)} 条高风险记录")
print(f"  输出文件: {OUTPUT_FILE}")

# ============================================================
# Step 3: LOAD DATA 导入MySQL
# ============================================================
print("\n[Step 3] 导入数据到MySQL...")

conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor()

# 开启 local_infile
cursor.execute("SET GLOBAL local_infile=ON")

LOAD_SQL = """
    LOAD DATA LOCAL INFILE '{}'
    INTO TABLE high_risk_person
    CHARACTER SET utf8mb4
    FIELDS TERMINATED BY '|'
    LINES TERMINATED BY '\\n'
    (user_id, user_name, abnormal_type, abnormal_amount, risk_level,
     abnormal_prob, detection_date, abnormal_desc, age_group,
     insurance_type, visit_count)
""".format(OUTPUT_FILE)

cursor.execute(LOAD_SQL)
conn.commit()
print("  数据导入成功")
cursor.close()
conn.close()

# ============================================================
# Step 4: 验证
# ============================================================
print("\n[Step 4] 验证数据...")

conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(1) FROM high_risk_person WHERE risk_level='高风险'")
count = cursor.fetchone()[0]
print(f"\n  高风险人数: {count}")

print("\n  高风险人员前10条:")
cursor.execute("""
    SELECT user_id, abnormal_type, abnormal_amount, detection_date, abnormal_desc
    FROM high_risk_person WHERE risk_level='高风险' LIMIT 10
""")
for row in cursor.fetchall():
    print(f"    {row[0]} | {row[1]} | {row[2]:.2f} | {row[3]} | {row[4]}")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("  数据导入完成")
print("  表: data.high_risk_person")
print("=" * 60)
