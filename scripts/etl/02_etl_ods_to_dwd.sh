#!/bin/bash
# ============================================================
# ODS → DWD 层 ETL
# 用法: bash 02_etl_ods_to_dwd.sh [etl_date]
# 示例: bash 02_etl_ods_to_dwd.sh 20260702
# ============================================================

set -e

ETL_DATE=${1:-$(date +%Y%m%d)}
START_TIME=$(date +%s)

echo "============================================================"
echo "  ODS → DWD 层ETL"
echo "  ETL日期: $ETL_DATE"
echo "============================================================"

# ============================================================
# Step 1: 创建DWD数据库和宽表
# ============================================================
echo ""
echo "[Step 1] 创建DWD数据库和宽表..."

hive -e "
CREATE DATABASE IF NOT EXISTS dwd
COMMENT 'DWD层-明细数据层，三表关联宽表'
LOCATION '/user/hive/warehouse/dwd.db';
"

hive -f sql/hive_dwd_ddl.sql

echo "  ✅ DWD层表创建完成"

# ============================================================
# Step 2: 执行ODS→DWD ETL（Spark引擎）
# ============================================================
echo ""
echo "[Step 2] 执行ODS→DWD ETL（Spark引擎）..."
echo "  预计耗时：2-5分钟"

spark-sql \
    --hivevar etl_date=$ETL_DATE \
    --conf spark.sql.shuffle.partitions=8 \
    --conf spark.hadoop.hive.exec.dynamic.partition=true \
    --conf spark.hadoop.hive.exec.dynamic.partition.mode=nonstrict \
    -f hql/etl_ods_to_dwd.hql

ETL_END=$(date +%s)
echo "  ✅ ODS→DWD ETL完成 (耗时: $((ETL_END - START_TIME))秒)"

# ============================================================
# Step 3: 验证DWD层数据
# ============================================================
echo ""
echo "[Step 3] 验证DWD层数据..."

hive -e "
USE dwd;
SELECT 'DWD宽表总记录数' AS metric, CAST(COUNT(*) AS STRING) AS value FROM dwd_insurance_detail WHERE dt='$ETL_DATE';
SELECT '年龄段分布' AS metric, CONCAT(age_group, ':', COUNT(*)) AS value FROM dwd_insurance_detail WHERE dt='$ETL_DATE' GROUP BY age_group ORDER BY age_group;
"

echo ""
echo "============================================================"
echo "  ✅ ODS → DWD ETL 完成！"
echo "  ETL日期: $ETL_DATE"
echo "============================================================"
