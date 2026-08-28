#!/bin/bash
# ============================================================
# Hive ODS层初始化 — 建表 + 数据导入
# 用法: bash 01_hive_ods_init.sh [etl_date]
# 示例: bash 01_hive_ods_init.sh 20260702
# ============================================================

set -e

ETL_DATE=${1:-$(date +%Y%m%d)}
CSV_DIR="/home/hadoop/temp"

echo "============================================================"
echo "  ODS层初始化 — 建表 + 数据导入"
echo "  ETL日期: $ETL_DATE"
echo "  CSV目录: $CSV_DIR"
echo "============================================================"

# ============================================================
# Step 1: 检查CSV文件是否存在
# ============================================================
echo ""
echo "[Step 1] 检查CSV文件..."

for f in insurance_info.csv medical_record.csv expense_detail.csv; do
    if [ ! -f "$CSV_DIR/$f" ]; then
        echo "  ❌ 文件不存在: $CSV_DIR/$f"
        exit 1
    fi
    lines=$(wc -l < "$CSV_DIR/$f")
    echo "  ✅ $f ($lines 行)"
done

# ============================================================
# Step 2: 去掉CSV表头行，生成无表头文件
# ============================================================
echo ""
echo "[Step 2] 去掉CSV表头行（Hive LOAD不跳过表头）..."

HEADERLESS_DIR="/home/hadoop/temp/headerless"
mkdir -p $HEADERLESS_DIR

for f in insurance_info.csv medical_record.csv expense_detail.csv; do
    tail -n +2 "$CSV_DIR/$f" > "$HEADERLESS_DIR/$f"
    lines=$(wc -l < "$HEADERLESS_DIR/$f")
    echo "  ✅ $f → $lines 行数据（已去掉表头）"
done

# ============================================================
# Step 3: 创建ODS数据库和3张表
# ============================================================
echo ""
echo "[Step 3] 创建ODS数据库和3张表..."

hive -e "
CREATE DATABASE IF NOT EXISTS ods
COMMENT 'ODS层-原始数据层，与CSV 1:1映射'
LOCATION '/user/hive/warehouse/ods.db';
"

hive -f sql/hive/hive_ods_ddl.sql

echo "  ✅ ODS层表创建完成"

# ============================================================
# Step 4: LOAD DATA LOCAL INPATH 导入数据
# ============================================================
echo ""
echo "[Step 4] LOAD DATA LOCAL INPATH 导入数据..."

# --- 导入参保人员表 ---
echo "  导入 ods_insurance_info ..."
hive --hivevar etl_date=$ETL_DATE -e "
LOAD DATA LOCAL INPATH '$HEADERLESS_DIR/insurance_info.csv'
OVERWRITE INTO TABLE ods.ods_insurance_info
PARTITION (dt='$ETL_DATE');
"

# --- 导入就诊记录表 ---
echo "  导入 ods_medical_record ..."
hive --hivevar etl_date=$ETL_DATE -e "
LOAD DATA LOCAL INPATH '$HEADERLESS_DIR/medical_record.csv'
OVERWRITE INTO TABLE ods.ods_medical_record
PARTITION (dt='$ETL_DATE');
"

# --- 导入费用明细表 ---
echo "  导入 ods_expense_detail ..."
hive --hivevar etl_date=$ETL_DATE -e "
LOAD DATA LOCAL INPATH '$HEADERLESS_DIR/expense_detail.csv'
OVERWRITE INTO TABLE ods.ods_expense_detail
PARTITION (dt='$ETL_DATE');
"

echo "  ✅ 数据导入完成"

# ============================================================
# Step 5: 验证导入结果
# ============================================================
echo ""
echo "[Step 5] 验证导入结果..."

hive -e "
USE ods;
SELECT 'ods_insurance_info' AS tbl, COUNT(*) AS rows FROM ods_insurance_info WHERE dt='$ETL_DATE';
SELECT 'ods_medical_record' AS tbl, COUNT(*) AS rows FROM ods_medical_record WHERE dt='$ETL_DATE';
SELECT 'ods_expense_detail' AS tbl, COUNT(*) AS rows FROM ods_expense_detail WHERE dt='$ETL_DATE';
"

echo ""
echo "============================================================"
echo "  ✅ ODS层初始化完成！"
echo "  ETL日期: $ETL_DATE"
echo "============================================================"
