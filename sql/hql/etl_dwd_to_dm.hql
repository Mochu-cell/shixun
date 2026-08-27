-- ============================================================
-- ETL: DWD → DM — 4张聚合统计表
-- 使用Spark SQL引擎执行: spark-sql -f etl_dwd_to_dm.hql
-- ============================================================

SET spark.sql.shuffle.partitions=8;

-- ============================================================
-- DM-1：参保人维度统计表
-- ============================================================
INSERT OVERWRITE TABLE dm.dm_insurance_stats
SELECT
    person_id,
    age_group,
    insurance_type,
    COUNT(DISTINCT record_id) AS visit_count,
    SUM(total_amount) AS total_amount,
    SUM(reimbursed_amount) AS total_reimburse,
    CASE
        WHEN SUM(total_amount) > 0
        THEN ROUND(SUM(reimbursed_amount) / SUM(total_amount), 4)
        ELSE 0
    END AS reimburse_rate,
    ROUND(SUM(total_amount) / COUNT(DISTINCT record_id), 2) AS avg_visit_amount,
    MIN(visit_date) AS first_visit_date,
    MAX(visit_date) AS last_visit_date,
    '${hivevar:etl_date}' AS etl_date
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY person_id, age_group, insurance_type;

-- ============================================================
-- DM-2：医院维度统计表
-- ============================================================
INSERT OVERWRITE TABLE dm.dm_hospital_stats
SELECT
    hospital,
    hospital_level,
    COUNT(DISTINCT record_id) AS visit_count,
    COUNT(DISTINCT person_id) AS unique_patients,
    SUM(total_amount) AS total_amount,
    SUM(reimbursed_amount) AS total_reimburse,
    CASE
        WHEN SUM(total_amount) > 0
        THEN ROUND(SUM(reimbursed_amount) / SUM(total_amount), 4)
        ELSE 0
    END AS reimburse_rate,
    -- 最常见诊断
    diagnosis AS top_diagnosis,
    '${hivevar:etl_date}' AS etl_date
FROM (
    SELECT
        hospital,
        hospital_level,
        record_id,
        person_id,
        total_amount,
        reimbursed_amount,
        diagnosis,
        ROW_NUMBER() OVER (PARTITION BY hospital ORDER BY cnt DESC) AS rn
    FROM (
        SELECT
            hospital,
            hospital_level,
            record_id,
            person_id,
            total_amount,
            reimbursed_amount,
            diagnosis,
            COUNT(*) OVER (PARTITION BY hospital, diagnosis) AS cnt
        FROM dwd.dwd_insurance_detail
        WHERE dt = '${hivevar:etl_date}'
    ) t1
) t2
WHERE rn = 1
GROUP BY hospital, hospital_level, diagnosis;

-- ============================================================
-- DM-3：月度费用分析表
-- ============================================================
INSERT OVERWRITE TABLE dm.dm_cost_analysis
SELECT
    visit_month AS stat_month,
    insurance_type,
    COUNT(DISTINCT record_id) AS visit_count,
    SUM(total_amount) AS total_amount,
    SUM(reimbursed_amount) AS total_reimburse,
    ROUND(SUM(total_amount) / COUNT(DISTINCT record_id), 2) AS avg_amount,
    CASE
        WHEN SUM(total_amount) > 0
        THEN ROUND(SUM(reimbursed_amount) / SUM(total_amount), 4)
        ELSE 0
    END AS reimburse_rate,
    '${hivevar:etl_date}' AS etl_date
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY visit_month, insurance_type;

-- ============================================================
-- DM-4：报销分析表
-- ============================================================
INSERT OVERWRITE TABLE dm.dm_reimburse_analysis
SELECT
    insurance_type,
    hospital_level,
    COUNT(DISTINCT record_id) AS visit_count,
    SUM(total_amount) AS total_amount,
    SUM(reimbursed_amount) AS total_reimburse,
    SUM(self_paid_amount) AS total_self_pay,
    CASE
        WHEN SUM(total_amount) > 0
        THEN ROUND(SUM(reimbursed_amount) / SUM(total_amount), 4)
        ELSE 0
    END AS reimburse_rate,
    ROUND(SUM(self_paid_amount) / COUNT(DISTINCT record_id), 2) AS avg_self_pay,
    '${hivevar:etl_date}' AS etl_date
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY insurance_type, hospital_level;
