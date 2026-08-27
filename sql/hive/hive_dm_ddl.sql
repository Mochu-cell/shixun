-- ============================================================
-- DM层建表DDL — 4张聚合统计表
-- 数据库：dm
-- ============================================================

CREATE DATABASE IF NOT EXISTS dm
COMMENT 'DM层-数据集市层，面向分析主题的聚合表'
LOCATION '/user/hive/warehouse/dm.db';

USE dm;

-- ============================================================
-- DM-1：参保人维度统计表
-- ============================================================
DROP TABLE IF EXISTS dm.dm_insurance_stats;

CREATE TABLE IF NOT EXISTS dm.dm_insurance_stats (
    person_id           STRING         COMMENT '人员唯一标识',
    age_group           STRING         COMMENT '年龄段',
    insurance_type      STRING         COMMENT '参保类型',
    visit_count         INT            COMMENT '总就诊次数',
    total_amount        DECIMAL(12,2)  COMMENT '总费用',
    total_reimburse     DECIMAL(12,2)  COMMENT '总报销金额',
    reimburse_rate      DECIMAL(10,4)   COMMENT '综合报销比例',
    avg_visit_amount    DECIMAL(12,2)  COMMENT '次均费用',
    first_visit_date    STRING         COMMENT '首次就诊日期',
    last_visit_date     STRING         COMMENT '最近就诊日期',
    etl_date            STRING         COMMENT 'ETL处理时间'
)
COMMENT 'DM层-参保人维度统计'
STORED AS ORC;

-- ============================================================
-- DM-2：医院维度统计表
-- ============================================================
DROP TABLE IF EXISTS dm.dm_hospital_stats;

CREATE TABLE IF NOT EXISTS dm.dm_hospital_stats (
    hospital            STRING         COMMENT '医院名称',
    hospital_level      STRING         COMMENT '医院等级',
    visit_count         INT            COMMENT '接诊量',
    unique_patients     INT            COMMENT '独立患者数',
    total_amount        DECIMAL(12,2)  COMMENT '总收入',
    total_reimburse     DECIMAL(12,2)  COMMENT '总报销金额',
    reimburse_rate      DECIMAL(10,4)   COMMENT '报销比例',
    top_diagnosis       STRING         COMMENT '最常见诊断',
    etl_date            STRING         COMMENT 'ETL处理时间'
)
COMMENT 'DM层-医院维度统计'
STORED AS ORC;

-- ============================================================
-- DM-3：月度费用分析表
-- ============================================================
DROP TABLE IF EXISTS dm.dm_cost_analysis;

CREATE TABLE IF NOT EXISTS dm.dm_cost_analysis (
    stat_month          STRING         COMMENT '统计月份(YYYY-MM)',
    insurance_type      STRING         COMMENT '参保类型',
    visit_count         INT            COMMENT '就诊人次',
    total_amount        DECIMAL(12,2)  COMMENT '总费用',
    total_reimburse     DECIMAL(12,2)  COMMENT '总报销',
    avg_amount          DECIMAL(12,2)  COMMENT '次均费用',
    reimburse_rate      DECIMAL(10,4)   COMMENT '报销比例',
    etl_date            STRING         COMMENT 'ETL处理时间'
)
COMMENT 'DM层-月度费用分析'
STORED AS ORC;

-- ============================================================
-- DM-4：报销分析表
-- ============================================================
DROP TABLE IF EXISTS dm.dm_reimburse_analysis;

CREATE TABLE IF NOT EXISTS dm.dm_reimburse_analysis (
    insurance_type      STRING         COMMENT '参保类型',
    hospital_level      STRING         COMMENT '医院等级',
    visit_count         INT            COMMENT '就诊人次',
    total_amount        DECIMAL(12,2)  COMMENT '总费用',
    total_reimburse     DECIMAL(12,2)  COMMENT '总报销',
    total_self_pay      DECIMAL(12,2)  COMMENT '总自付',
    reimburse_rate      DECIMAL(10,4)   COMMENT '报销比例',
    avg_self_pay        DECIMAL(12,2)  COMMENT '次均自付',
    etl_date            STRING         COMMENT 'ETL处理时间'
)
COMMENT 'DM层-报销分析'
STORED AS ORC;
