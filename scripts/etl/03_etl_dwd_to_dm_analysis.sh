#!/bin/bash
# ============================================================
# DWD → DM 层 ETL + Spark SQL 聚合分析
# 用法: bash 03_etl_dwd_to_dm_analysis.sh [etl_date]
# 示例: sh 03_etl_dwd_to_dm_analysis.sh 20260702
# ============================================================

set -e

ETL_DATE=${1:-$(date +%Y%m%d)}
START_TIME=$(date +%s)

echo "============================================================"
echo "  DWD → DM 层ETL + Spark SQL聚合分析"
echo "  ETL日期: $ETL_DATE"
echo "============================================================"

# ============================================================
# Step 1: 创建DM数据库和4张统计表
# ============================================================
echo ""
echo "[Step 1] 创建DM数据库和4张统计表..."

hive -e "
CREATE DATABASE IF NOT EXISTS dm
COMMENT 'DM层-汇总数据层，聚合统计表'
LOCATION '/user/hive/warehouse/dm.db';
"

hive -f sql/hive_dm_ddl.sql

echo "  ✅ DM层表创建完成"

# ============================================================
# Step 2: 执行DWD→DM ETL
# ============================================================
echo ""
echo "[Step 2] 执行DWD→DM ETL（Spark引擎）..."

spark-sql \
    --hivevar etl_date=$ETL_DATE \
    --conf spark.sql.shuffle.partitions=8 \
    --conf spark.hadoop.hive.exec.dynamic.partition=true \
    --conf spark.hadoop.hive.exec.dynamic.partition.mode=nonstrict \
    -f hql/etl_dwd_to_dm.hql

echo "  ✅ DWD→DM ETL完成"

# ============================================================
# Step 3: 验证DM层数据
# ============================================================
echo ""
echo "[Step 3] 验证DM层数据..."

hive -e "
USE dm;
SELECT 'dm_insurance_stats' AS tbl, CAST(COUNT(*) AS STRING) AS row_count FROM dm_insurance_stats;
SELECT 'dm_hospital_stats' AS tbl, CAST(COUNT(*) AS STRING) AS row_count FROM dm_hospital_stats;
SELECT 'dm_cost_analysis' AS tbl, CAST(COUNT(*) AS STRING) AS row_count FROM dm_cost_analysis;
SELECT 'dm_reimburse_analysis' AS tbl, CAST(COUNT(*) AS STRING) AS row_count FROM dm_reimburse_analysis;
"

# ============================================================
# Step 4: Spark SQL聚合分析
# ============================================================
echo ""
echo "[Step 4] 执行Spark SQL聚合分析..."

spark-sql \
    --hivevar etl_date=$ETL_DATE \
    --conf spark.sql.shuffle.partitions=8 \
    -f hql/spark_analysis.hql

END_TIME=$(date +%s)
echo ""
echo "============================================================"
echo "  ✅ DWD → DM ETL + 聚合分析 完成！"
echo "  ETL日期: $ETL_DATE"
echo "  总耗时: $((END_TIME - START_TIME))秒"
echo "============================================================"
