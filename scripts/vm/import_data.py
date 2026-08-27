import pymysql, csv, os, sys

# 敏感配置优先环境变量，其次 config/local_config.py（不入库）
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
try:
    from config import local_config
except Exception:
    local_config = None

MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD") or (getattr(local_config, "MYSQL_PASSWORD", None) if local_config else None) or ""
MYSQL_HOST = os.environ.get("MYSQL_HOST") or (getattr(local_config, "MYSQL_HOST", None) if local_config else None) or "127.0.0.1"

conn = pymysql.connect(host=MYSQL_HOST, user='root', password=MYSQL_PASSWORD, database='data', charset='utf8mb4', local_infile=False)
cur = conn.cursor()

# Check tables exist
cur.execute("SHOW TABLES LIKE 'tumor_%'")
tables = [r[0] for r in cur.fetchall()]
print(f"Existing tables: {tables}")

# Drop old data if exists and recreate tables
for tbl in ['tumor_detection_stats', 'tumor_type_distribution', 'detection_confidence', 'patient_summary']:
    cur.execute(f"DROP TABLE IF EXISTS data.{tbl}")

cur.execute("""CREATE TABLE data.tumor_detection_stats (
    id INT AUTO_INCREMENT PRIMARY KEY, scan_date DATE NOT NULL, total_scans INT DEFAULT 0,
    detected INT DEFAULT 0, positive_rate DECIMAL(5,2) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""")

cur.execute("""CREATE TABLE data.tumor_type_distribution (
    id INT AUTO_INCREMENT PRIMARY KEY, tumor_type VARCHAR(50) NOT NULL, count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""")

cur.execute("""CREATE TABLE data.detection_confidence (
    id INT AUTO_INCREMENT PRIMARY KEY, confidence_range VARCHAR(50) NOT NULL, count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""")

cur.execute("""CREATE TABLE data.patient_summary (
    id INT AUTO_INCREMENT PRIMARY KEY, patient_id VARCHAR(20) NOT NULL, scan_date DATE NOT NULL,
    tumor_type VARCHAR(50), confidence DECIMAL(5,2), status VARCHAR(20), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""")

conn.commit()

# Import data
data_dir = '/home/hadoop/temp/tomysql'

with open(f'{data_dir}/tumor_detection_stats.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("INSERT INTO data.tumor_detection_stats (scan_date,total_scans,detected,positive_rate) VALUES (%s,%s,%s,%s)",
                    (row['date'], int(row['total_scans']), int(row['detected']), float(row['positive_rate'])))
conn.commit()
cur.execute("SELECT COUNT(1) FROM data.tumor_detection_stats")
print(f"tumor_detection_stats: {cur.fetchone()[0]} rows")

with open(f'{data_dir}/tumor_type_distribution.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("INSERT INTO data.tumor_type_distribution (tumor_type,count,percentage) VALUES (%s,%s,%s)",
                    (row['tumor_type'], int(row['count']), float(row['percentage'])))
conn.commit()
cur.execute("SELECT COUNT(1) FROM data.tumor_type_distribution")
print(f"tumor_type_distribution: {cur.fetchone()[0]} rows")

with open(f'{data_dir}/detection_confidence.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("INSERT INTO data.detection_confidence (confidence_range,count,percentage) VALUES (%s,%s,%s)",
                    (row['confidence_range'], int(row['count']), float(row['percentage'])))
conn.commit()
cur.execute("SELECT COUNT(1) FROM data.detection_confidence")
print(f"detection_confidence: {cur.fetchone()[0]} rows")

with open(f'{data_dir}/patient_summary.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("INSERT INTO data.patient_summary (patient_id,scan_date,tumor_type,confidence,status) VALUES (%s,%s,%s,%s,%s)",
                    (row['patient_id'], row['scan_date'], row['tumor_type'], float(row['confidence']), row['status']))
conn.commit()
cur.execute("SELECT COUNT(1) FROM data.patient_summary")
print(f"patient_summary: {cur.fetchone()[0]} rows")

cur.close()
conn.close()
print("Done!")
