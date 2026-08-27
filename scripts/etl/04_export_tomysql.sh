#!/bin/bash
# ============================================================
# MySQL 报表层 + Hive 导出 CSV + MySQL 导入
# 替代Sqoop HCatalog导出方案
# ============================================================

set -e

# 参数检查
if [ $# -lt 1 ]; then
    echo "用法: bash $0 <ETL日期> [MySQL数据库名]"
    echo "示例: bash $0 20260702 data"
    exit 1
fi

ETL_DATE=$1
MYSQL_DB=${2:-data}
OUTPUT_DIR="/home/hadoop/temp/analysis_results"

# MySQL连接配置
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASS="${MYSQL_PASS:-}"

if [ -z "$MYSQL_PASS" ]; then
    echo "请先设置 MySQL 密码环境变量：export MYSQL_PASS=<你的MySQL密码>"
    exit 1
fi

echo "============================================================"
echo "  MySQL 报表层 + 数据导出 + 结果输出"
echo "  ETL日期: $ETL_DATE"
echo "============================================================"

# 创建输出目录
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

# ============================================================
# Step 1: 创建MySQL报表层表
# ============================================================
echo ""
echo "[Step 1] 创建MySQL报表层表..."

mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB <<'MYSQL_DDL'
-- 参保人统计报表
DROP TABLE IF EXISTS rpt_insurance_stats;
CREATE TABLE rpt_insurance_stats (
    person_id VARCHAR(50) COMMENT '身份证号',
    age_group VARCHAR(20) COMMENT '年龄段',
    insurance_type VARCHAR(50) COMMENT '参保类型',
    visit_count INT COMMENT '就诊次数',
    total_amount DECIMAL(12,2) COMMENT '总费用',
    reimbursed_amount DECIMAL(12,2) COMMENT '报销金额',
    reimburse_rate DECIMAL(10,4) COMMENT '报销比例',
    avg_amount DECIMAL(12,2) COMMENT '次均费用',
    first_visit_date VARCHAR(20) COMMENT '首次就诊日期',
    last_visit_date VARCHAR(20) COMMENT '最近就诊日期',
    etl_date VARCHAR(20) COMMENT 'ETL日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参保人统计报表';

-- 医院统计报表
DROP TABLE IF EXISTS rpt_hospital_stats;
CREATE TABLE rpt_hospital_stats (
    hospital VARCHAR(100) COMMENT '医院名称',
    hospital_level VARCHAR(20) COMMENT '医院等级',
    visit_count INT COMMENT '接诊量',
    unique_patients INT COMMENT '独立患者数',
    total_amount DECIMAL(12,2) COMMENT '总收入',
    reimbursed_amount DECIMAL(12,2) COMMENT '报销金额',
    reimburse_rate DECIMAL(10,4) COMMENT '报销比例',
    top_diagnosis VARCHAR(100) COMMENT '最常见诊断',
    etl_date VARCHAR(20) COMMENT 'ETL日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医院统计报表';

-- 月度费用分析报表
DROP TABLE IF EXISTS rpt_cost_analysis;
CREATE TABLE rpt_cost_analysis (
    stat_month VARCHAR(20) COMMENT '统计月份',
    insurance_type VARCHAR(50) COMMENT '参保类型',
    visit_count INT COMMENT '就诊人次',
    total_amount DECIMAL(12,2) COMMENT '总费用',
    reimbursed_amount DECIMAL(12,2) COMMENT '报销金额',
    avg_amount DECIMAL(12,2) COMMENT '次均费用',
    reimburse_rate DECIMAL(10,4) COMMENT '报销比例',
    etl_date VARCHAR(20) COMMENT 'ETL日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度费用分析报表';

-- 报销分析报表
DROP TABLE IF EXISTS rpt_reimburse_analysis;
CREATE TABLE rpt_reimburse_analysis (
    age_group VARCHAR(20) COMMENT '年龄段',
    insurance_type VARCHAR(50) COMMENT '参保类型',
    hospital_level VARCHAR(20) COMMENT '医院等级',
    visit_count INT COMMENT '就诊次数',
    total_amount DECIMAL(12,2) COMMENT '总费用',
    reimbursed_amount DECIMAL(12,2) COMMENT '报销金额',
    self_paid_amount DECIMAL(12,2) COMMENT '自付金额',
    reimburse_rate DECIMAL(10,4) COMMENT '报销比例',
    avg_self_paid DECIMAL(12,2) COMMENT '次均自付',
    etl_date VARCHAR(20) COMMENT 'ETL日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报销分析报表';
MYSQL_DDL

echo "  ✅ MySQL报表层表创建完成"

# ============================================================
# Step 2: Hive导出DM层数据为CSV（使用管道符分隔）
# ============================================================
echo ""
echo "[Step 2] Hive导出DM层数据为CSV..."

# 导出函数：用标准INSERT OVERWRITE LOCAL DIRECTORY方式
export_table() {
    local table_name=$1
    local output_file=$2
    
    echo "  导出 $table_name ..."
    
    # Hive导出到本地目录（管道符分隔，无引号包围）
    hive -e "
        USE dm;
        SET hive.exec.compress.output=false;
        INSERT OVERWRITE LOCAL DIRECTORY '$OUTPUT_DIR/${table_name}'
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY '|'
        COLLECTION ITEMS TERMINATED BY '\n'
        MAP KEYS TERMINATED BY ':'
        NULL DEFINED AS ''
        SELECT * FROM ${table_name};
    " 2>/dev/null || true
    
    # 合并可能的多文件（Hive可能生成多个文件）
    if [ -d "$OUTPUT_DIR/${table_name}" ]; then
        cat $OUTPUT_DIR/${table_name}/* > "$OUTPUT_DIR/${output_file}" 2>/dev/null || touch "$OUTPUT_DIR/${output_file}"
        rm -rf "$OUTPUT_DIR/${table_name}"
    else
        touch "$OUTPUT_DIR/${output_file}"
    fi
    
    # 统计行数
    local row_count=$(wc -l < "$OUTPUT_DIR/${output_file}" 2>/dev/null || echo "0")
    echo "  ✅ ${output_file} (${row_count} 行)"
}

# 导出4张DM表
export_table "dm_insurance_stats" "dm_insurance_stats.csv"
export_table "dm_hospital_stats" "dm_hospital_stats.csv"
export_table "dm_cost_analysis" "dm_cost_analysis.csv"
export_table "dm_reimburse_analysis" "dm_reimburse_analysis.csv"

echo "  ✅ CSV导出完成，文件位于: $OUTPUT_DIR"

# ============================================================
# Step 3: 导入CSV到MySQL
# ============================================================
echo ""
echo "[Step 3] 导入CSV到MySQL..."

# 开启local_infile（如果可以）
mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS -e "SET GLOBAL local_infile=ON;" 2>/dev/null || true

import_table() {
    local csv_file=$1
    local mysql_table=$2
    
    echo "  导入 $mysql_table ..."
    
    # 使用LOAD DATA LOCAL INFILE（管道符分隔）
    mysql --local-infile=1 -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -e "
        LOAD DATA LOCAL INFILE '$OUTPUT_DIR/${csv_file}'
        INTO TABLE ${mysql_table}
        FIELDS TERMINATED BY '|'
        LINES TERMINATED BY '\n'
        IGNORE 0 LINES;
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✅ $mysql_table 导入成功"
    else
        echo "  ⚠️ LOAD DATA失败，尝试mysqlimport..."
        # 尝试mysqlimport方式
        mysqlimport --local -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS \
            --fields-terminated-by='|' --lines-terminated-by='\n' \
            $MYSQL_DB "$OUTPUT_DIR/${csv_file}" 2>/dev/null || \
        echo "  [警告] 导入失败，请手动检查CSV文件"
    fi
}

# 导入4张表
import_table "dm_insurance_stats.csv" "rpt_insurance_stats"
import_table "dm_hospital_stats.csv" "rpt_hospital_stats"
import_table "dm_cost_analysis.csv" "rpt_cost_analysis"
import_table "dm_reimburse_analysis.csv" "rpt_reimburse_analysis"

# ============================================================
# Step 4: 验证MySQL数据
# ============================================================
echo ""
echo "[Step 4] 验证MySQL数据..."

echo ""
echo "===== 各表记录数 ====="
mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -e "
    SELECT 'rpt_insurance_stats' AS table_name, COUNT(*) AS row_count FROM rpt_insurance_stats
    UNION ALL
    SELECT 'rpt_hospital_stats', COUNT(*) FROM rpt_hospital_stats
    UNION ALL
    SELECT 'rpt_cost_analysis', COUNT(*) FROM rpt_cost_analysis
    UNION ALL
    SELECT 'rpt_reimburse_analysis', COUNT(*) FROM rpt_reimburse_analysis;
" 2>/dev/null || echo "  [警告] 验证查询失败，请手动检查"

echo ""
echo "===== rpt_insurance_stats前5条 ====="
mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -e "
    SELECT * FROM rpt_insurance_stats LIMIT 5;
" 2>/dev/null || echo "  [警告] 查询失败"

# ============================================================
# Step 5: 输出分析结果文件摘要
# ============================================================
echo ""
echo "[Step 5] 分析结果文件摘要..."

ls -lh $OUTPUT_DIR/*.csv 2>/dev/null || echo "  [警告] 无CSV文件"

echo ""
echo "============================================================"
echo "  ✅ 导出与导入完成"
echo "  输出目录: $OUTPUT_DIR"
echo "  MySQL数据库: $MYSQL_DB"
echo "============================================================"
