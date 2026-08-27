-- ============================================================
-- Spark SQL 聚合分析与关联分析（12个主题）
-- 执行: spark-sql --hivevar etl_date=20260702 -f spark_analysis.hql
-- 注意: Spark SQL不支持中文列别名，所有别名使用英文
-- ============================================================

-- ============================================================
-- 主题1：各参保类型就诊分布
-- ============================================================
SELECT
    insurance_type AS insurance_type_name,
    COUNT(DISTINCT person_id) AS patient_count,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(SUM(total_amount), 2) AS total_cost,
    ROUND(AVG(total_amount), 2) AS avg_cost
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY insurance_type
ORDER BY total_cost DESC;

-- ============================================================
-- 主题2：高费用就诊TOP10
-- ============================================================
SELECT
    person_id,
    hospital,
    department,
    diagnosis,
    total_amount,
    reimbursed_amount,
    ROUND(reimburse_rate, 4) AS reimburse_ratio
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
ORDER BY total_amount DESC
LIMIT 10;

-- ============================================================
-- 主题3：医院接诊排名
-- ============================================================
SELECT
    hospital,
    hospital_level,
    COUNT(DISTINCT record_id) AS visit_count,
    COUNT(DISTINCT person_id) AS patient_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(SUM(reimbursed_amount), 2) AS reimbursed_amount
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY hospital, hospital_level
ORDER BY visit_count DESC
LIMIT 15;

-- ============================================================
-- 主题4：不同医院等级费用对比
-- ============================================================
SELECT
    hospital_level,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(SUM(total_amount), 2) AS total_cost,
    ROUND(AVG(total_amount), 2) AS avg_cost,
    ROUND(AVG(reimburse_rate) * 100, 1) AS avg_reimburse_rate_pct
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY hospital_level
ORDER BY avg_cost DESC;

-- ============================================================
-- 主题5：月度费用趋势
-- ============================================================
SELECT
    visit_month,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(SUM(total_amount), 2) AS total_cost,
    ROUND(SUM(reimbursed_amount), 2) AS reimbursed_amount,
    ROUND(AVG(reimburse_rate) * 100, 1) AS avg_reimburse_rate_pct
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY visit_month
ORDER BY visit_month;

-- ============================================================
-- 主题6：月度环比增长率
-- ============================================================
SELECT
    visit_month,
    monthly_total,
    LAG(monthly_total, 1) OVER (ORDER BY visit_month) AS prev_month_total,
    CASE
        WHEN LAG(monthly_total, 1) OVER (ORDER BY visit_month) > 0
        THEN ROUND((monthly_total - LAG(monthly_total, 1) OVER (ORDER BY visit_month))
             / LAG(monthly_total, 1) OVER (ORDER BY visit_month) * 100, 2)
        ELSE NULL
    END AS growth_rate_pct
FROM (
    SELECT visit_month, SUM(total_amount) AS monthly_total
    FROM dwd.dwd_insurance_detail
    WHERE dt = '${hivevar:etl_date}'
    GROUP BY visit_month
) t
ORDER BY visit_month;

-- ============================================================
-- 主题7：参保类型×医院等级 报销率矩阵
-- ============================================================
SELECT
    insurance_type,
    hospital_level,
    ROUND(AVG(reimburse_rate) * 100, 1) AS reimburse_rate_pct,
    COUNT(*) AS record_count
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY insurance_type, hospital_level
ORDER BY insurance_type, hospital_level;

-- ============================================================
-- 主题8：自付比例分析
-- ============================================================
SELECT
    insurance_type,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(SUM(total_amount), 2) AS total_cost,
    ROUND(SUM(reimbursed_amount), 2) AS reimbursed_amount,
    ROUND(SUM(total_amount) - SUM(reimbursed_amount), 2) AS total_self_paid,
    ROUND((SUM(total_amount) - SUM(reimbursed_amount)) / SUM(total_amount) * 100, 1) AS self_paid_rate_pct
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY insurance_type
ORDER BY self_paid_rate_pct DESC;

-- ============================================================
-- 主题9：年龄段×参保类型交叉分析
-- ============================================================
SELECT
    age_group,
    insurance_type,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(AVG(total_amount), 2) AS avg_cost,
    ROUND(AVG(reimburse_rate) * 100, 1) AS reimburse_rate_pct
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY age_group, insurance_type
ORDER BY age_group, insurance_type;

-- ============================================================
-- 主题10：费用类别结构分析
-- ============================================================
SELECT
    item_category,
    COUNT(*) AS detail_count,
    ROUND(SUM(total_amount), 2) AS total_amount,
    ROUND(SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER (), 2) AS amount_pct
FROM ods.ods_expense_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY item_category
ORDER BY total_amount DESC;

-- ============================================================
-- 主题11：科室排名
-- ============================================================
SELECT
    department,
    COUNT(DISTINCT record_id) AS visit_count,
    ROUND(SUM(total_amount), 2) AS total_cost,
    ROUND(AVG(reimburse_rate) * 100, 1) AS reimburse_rate_pct
FROM dwd.dwd_insurance_detail
WHERE dt = '${hivevar:etl_date}'
GROUP BY department
ORDER BY total_cost DESC
LIMIT 15;

-- ============================================================
-- 主题12：医院费用帕累托分析（累计占比）
-- ============================================================
SELECT
    hospital,
    hospital_total,
    ROUND(hospital_total * 100.0 / SUM(hospital_total) OVER (), 2) AS revenue_pct,
    ROUND(SUM(hospital_total) OVER (ORDER BY hospital_total DESC) * 100.0
          / SUM(hospital_total) OVER (), 2) AS cumulative_pct
FROM (
    SELECT hospital, SUM(total_amount) AS hospital_total
    FROM dwd.dwd_insurance_detail
    WHERE dt = '${hivevar:etl_date}'
    GROUP BY hospital
) t
ORDER BY hospital_total DESC;
