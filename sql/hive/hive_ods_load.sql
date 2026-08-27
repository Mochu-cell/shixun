-- ============================================================
-- ODS 层数据导入 SQL
-- 功能：从本地CSV文件直接加载数据到Hive ODS层分区表
-- 前置条件：CSV文件在 /home/hadoop/temp/ 目录下
-- 执行方式：hive --hivevar etl_date=2025-07-10 -f hive_ods_load.sql
--
-- ★ CSV文件位置：/home/hadoop/temp/
--   - insurance_info.csv
--   - medical_record.csv
--   - expense_detail.csv
-- ★ 使用 LOAD DATA LOCAL INPATH 从本地文件系统读取（不上传HDFS）
-- ★ 注意：hivevar变量值不要加引号，Hive会自动作为字符串处理
-- ============================================================

USE ods;

-- ============================================================
-- 1. 加载参保人员信息（从本地CSV直接加载）
-- ============================================================
LOAD DATA LOCAL INPATH '/home/hadoop/temp/insurance_info.csv'
OVERWRITE INTO TABLE ods_insurance_info
PARTITION (dt='${hivevar:etl_date}');

-- 验证导入
SELECT '参保人员表导入结果：' AS info;
SELECT COUNT(*) AS total_rows FROM ods_insurance_info WHERE dt='${hivevar:etl_date}';
SELECT * FROM ods_insurance_info WHERE dt='${hivevar:etl_date}' LIMIT 3;

-- ============================================================
-- 2. 加载就诊记录（从本地CSV直接加载）
-- ============================================================
LOAD DATA LOCAL INPATH '/home/hadoop/temp/medical_record.csv'
OVERWRITE INTO TABLE ods_medical_record
PARTITION (dt='${hivevar:etl_date}');

-- 验证导入
SELECT '就诊记录表导入结果：' AS info;
SELECT COUNT(*) AS total_rows FROM ods_medical_record WHERE dt='${hivevar:etl_date}';
SELECT * FROM ods_medical_record WHERE dt='${hivevar:etl_date}' LIMIT 3;

-- ============================================================
-- 3. 加载费用明细（从本地CSV直接加载）
-- ============================================================
LOAD DATA LOCAL INPATH '/home/hadoop/temp/expense_detail.csv'
OVERWRITE INTO TABLE ods_expense_detail
PARTITION (dt='${hivevar:etl_date}');

-- 验证导入
SELECT '费用明细表导入结果：' AS info;
SELECT COUNT(*) AS total_rows FROM ods_expense_detail WHERE dt='${hivevar:etl_date}';
SELECT * FROM ods_expense_detail WHERE dt='${hivevar:etl_date}' LIMIT 3;

-- ============================================================
-- 4. ODS层数据质量校验
-- ============================================================
SELECT '===== ODS层数据质量校验 =====' AS info;

-- 各表记录数
SELECT 'ods_insurance_info' AS table_name, COUNT(*) AS row_count FROM ods_insurance_info WHERE dt='${hivevar:etl_date}'
UNION ALL
SELECT 'ods_medical_record', COUNT(*) FROM ods_medical_record WHERE dt='${hivevar:etl_date}'
UNION ALL
SELECT 'ods_expense_detail', COUNT(*) FROM ods_expense_detail WHERE dt='${hivevar:etl_date}';

-- 各表缺失值统计
SELECT '参保人员-姓名缺失' AS check_item, COUNT(*) AS missing_count
FROM ods_insurance_info WHERE dt='${hivevar:etl_date}' AND (name IS NULL OR TRIM(name)='' OR name='nan')
UNION ALL
SELECT '参保人员-年龄缺失', COUNT(*) FROM ods_insurance_info WHERE dt='${hivevar:etl_date}' AND age IS NULL
UNION ALL
SELECT '就诊记录-医院缺失', COUNT(*) FROM ods_medical_record WHERE dt='${hivevar:etl_date}' AND (hospital IS NULL OR TRIM(hospital)='')
UNION ALL
SELECT '费用明细-金额缺失', COUNT(*) FROM ods_expense_detail WHERE dt='${hivevar:etl_date}' AND total_amount IS NULL;
