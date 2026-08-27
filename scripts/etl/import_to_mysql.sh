#!/bin/bash
# 数据导入MySQL脚本
# 将脑肿瘤检测数据从TXT导入MySQL

# MySQL配置
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASS="${MYSQL_PASS:-}"
MYSQL_DB="data"

if [ -z "$MYSQL_PASS" ]; then
    echo "请先设置 MySQL 密码环境变量：export MYSQL_PASS=<你的MySQL密码>"
    exit 1
fi

# 数据目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR"

# 创建临时MySQL配置文件（避免密码警告）
MYSQL_CONFIG=$(mktemp)
cat > "$MYSQL_CONFIG" << EOF
[client]
host=localhost
port=$MYSQL_PORT
user=$MYSQL_USER
password=$MYSQL_PASS
database=$MYSQL_DB
default-character-set=utf8mb4
EOF

# 清理临时文件
cleanup() {
    rm -f "$MYSQL_CONFIG"
}
trap cleanup EXIT

echo "============================================================"
echo "  数据导入MySQL"
echo "============================================================"
echo
echo "  MySQL主机: $MYSQL_HOST"
echo "  数据库: $MYSQL_DB"
echo "  数据目录: $DATA_DIR"
echo

# 检查数据目录
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ 数据目录不存在: $DATA_DIR"
    echo "请先运行 generate_output_data.py 生成数据"
    exit 1
fi

# 创建数据表
echo "[1/5] 创建数据表..."
mysql --defaults-file="$MYSQL_CONFIG" << EOF
-- 肿瘤检测统计表
CREATE TABLE IF NOT EXISTS tumor_detection_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_date DATE NOT NULL,
    total_scans INT DEFAULT 0,
    detected INT DEFAULT 0,
    positive_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 肿瘤类型分布表
CREATE TABLE IF NOT EXISTS tumor_type_distribution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tumor_type VARCHAR(50) NOT NULL,
    count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 检测置信度统计表
CREATE TABLE IF NOT EXISTS detection_confidence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    confidence_range VARCHAR(50) NOT NULL,
    count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 患者检测汇总表
CREATE TABLE IF NOT EXISTS patient_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    scan_date DATE NOT NULL,
    tumor_type VARCHAR(50),
    confidence DECIMAL(5,2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
echo "✅ 数据表创建完成"
echo

# 导入肿瘤检测统计
echo "[2/5] 导入肿瘤检测统计..."
if [ -f "$DATA_DIR/tumor_detection_stats.txt" ]; then
    mysql --defaults-file="$MYSQL_CONFIG" \
        -e "DELETE FROM tumor_detection_stats;"
    
    tail -n +2 "$DATA_DIR/tumor_detection_stats.txt" | while IFS=',' read -r date total detected rate; do
        mysql --defaults-file="$MYSQL_CONFIG" \
            -e "INSERT INTO tumor_detection_stats (scan_date, total_scans, detected, positive_rate) VALUES ('$date', $total, $detected, $rate);"
    done
    echo "✅ 肿瘤检测统计导入完成"
else
    echo "⚠️ 文件不存在: tumor_detection_stats.txt"
fi
echo

# 导入肿瘤类型分布
echo "[3/5] 导入肿瘤类型分布..."
if [ -f "$DATA_DIR/tumor_type_distribution.txt" ]; then
    mysql --defaults-file="$MYSQL_CONFIG" \
        -e "DELETE FROM tumor_type_distribution;"
    
    tail -n +2 "$DATA_DIR/tumor_type_distribution.txt" | while IFS=',' read -r type count pct; do
        mysql --defaults-file="$MYSQL_CONFIG" \
            -e "INSERT INTO tumor_type_distribution (tumor_type, count, percentage) VALUES ('$type', $count, $pct);"
    done
    echo "✅ 肿瘤类型分布导入完成"
else
    echo "⚠️ 文件不存在: tumor_type_distribution.txt"
fi
echo

# 导入检测置信度统计
echo "[4/5] 导入检测置信度统计..."
if [ -f "$DATA_DIR/detection_confidence.txt" ]; then
    mysql --defaults-file="$MYSQL_CONFIG" \
        -e "DELETE FROM detection_confidence;"
    
    tail -n +2 "$DATA_DIR/detection_confidence.txt" | while IFS=',' read -r range count pct; do
        mysql --defaults-file="$MYSQL_CONFIG" \
            -e "INSERT INTO detection_confidence (confidence_range, count, percentage) VALUES ('$range', $count, $pct);"
    done
    echo "✅ 检测置信度统计导入完成"
else
    echo "⚠️ 文件不存在: detection_confidence.txt"
fi
echo

# 导入患者汇总
echo "[5/5] 导入患者检测汇总..."
if [ -f "$DATA_DIR/patient_summary.txt" ]; then
    mysql --defaults-file="$MYSQL_CONFIG" \
        -e "DELETE FROM patient_summary;"
    
    tail -n +2 "$DATA_DIR/patient_summary.txt" | while IFS=',' read -r pid date type conf status; do
        mysql --defaults-file="$MYSQL_CONFIG" \
            -e "INSERT INTO patient_summary (patient_id, scan_date, tumor_type, confidence, status) VALUES ('$pid', '$date', '$type', $conf, '$status');"
    done
    echo "✅ 患者检测汇总导入完成"
else
    echo "⚠️ 文件不存在: patient_summary.txt"
fi
echo

echo "============================================================"
echo "  ✅ 数据导入完成！"
echo "============================================================"
echo
echo "  验证数据："
echo "  mysql -u root -p $MYSQL_DB"
echo "  SELECT * FROM tumor_detection_stats LIMIT 5;"
echo "  SELECT * FROM tumor_type_distribution;"
echo "  SELECT * FROM detection_confidence LIMIT 5;"
echo "  SELECT * FROM patient_summary LIMIT 5;"
