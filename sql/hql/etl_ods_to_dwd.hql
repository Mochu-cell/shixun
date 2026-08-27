-- ============================================================
-- ETL: ODS → DWD — 三表JOIN + 字段衍生 + 标准化
-- 使用Spark SQL引擎执行: spark-sql -f etl_ods_to_dwd.hql
-- ============================================================

-- 跨库引用已使用库名前缀，无需USE

SET spark.sql.shuffle.partitions=8;

-- ============================================================
-- DWD宽表：三表关联 + 字段衍生
-- ODS列名完全对应CSV:
--   insurance_info: person_id,name,gender,age,id_card,insurance_type,region,register_date,status
--   medical_record: record_id,person_id,visit_date,hospital,department,diagnosis,doctor,visit_type
--   expense_detail: detail_id,record_id,item_name,item_category,quantity,unit_price,
--                   total_amount,reimbursable,reimbursed_amount,self_paid_amount
-- ============================================================

INSERT OVERWRITE TABLE dwd.dwd_insurance_detail PARTITION (dt='${hivevar:etl_date}')
SELECT
    -- 参保人信息
    ins.person_id,
    ins.name,
    ins.gender,
    -- 年龄段衍生
    CASE
        WHEN CAST(ins.age AS INT) < 19 THEN '0-18'
        WHEN CAST(ins.age AS INT) < 36 THEN '19-35'
        WHEN CAST(ins.age AS INT) < 56 THEN '36-55'
        WHEN CAST(ins.age AS INT) < 71 THEN '56-70'
        ELSE '70+'
    END AS age_group,
    -- 参保类型标准化
    CASE ins.insurance_type
        WHEN '城镇职工' THEN '城镇职工'
        WHEN '城职' THEN '城镇职工'
        WHEN '城乡居民' THEN '城乡居民'
        WHEN '城居' THEN '城乡居民'
        WHEN '灵活就业' THEN '灵活就业'
        ELSE '其他'
    END AS insurance_type,
    ins.region,
    ins.register_date AS enroll_date,
    -- 参保月数衍生
    CAST(
        MONTHS_BETWEEN(
            CURRENT_DATE(),
            CASE
                WHEN ins.register_date LIKE '%/%' THEN
                    TO_DATE(CONCAT(SUBSTR(ins.register_date,1,4),'-',
                                   SUBSTR(ins.register_date,6,2),'-',
                                   SUBSTR(ins.register_date,9,2)))
                ELSE TO_DATE(ins.register_date)
            END
        ) AS INT
    ) AS enroll_months,
    ins.status,
    -- 就诊信息
    med.record_id,
    med.hospital,
    -- 医院等级推断
    CASE
        WHEN med.hospital LIKE '%省%' OR med.hospital LIKE '%大学%' THEN '三甲'
        WHEN med.hospital LIKE '%市中心%' OR med.hospital LIKE '%市第一%' THEN '三甲'
        WHEN med.hospital LIKE '%市第二%' OR med.hospital LIKE '%市人民%' THEN '三乙'
        WHEN med.hospital LIKE '%区%' OR med.hospital LIKE '%县%' THEN '二级'
        WHEN med.hospital LIKE '%社区%' OR med.hospital LIKE '%乡镇%' THEN '一级'
        ELSE '二级'
    END AS hospital_level,
    med.department,
    med.visit_date,
    -- 就诊日期维度衍生
    YEAR(
        CASE
            WHEN med.visit_date LIKE '%/%' THEN
                TO_DATE(CONCAT(SUBSTR(med.visit_date,1,4),'-',
                               SUBSTR(med.visit_date,6,2),'-',
                               SUBSTR(med.visit_date,9,2)))
            ELSE TO_DATE(med.visit_date)
        END
    ) AS visit_year,
    SUBSTR(
        CASE
            WHEN med.visit_date LIKE '%/%' THEN
                CONCAT(SUBSTR(med.visit_date,1,4),'-',
                       SUBSTR(med.visit_date,6,2))
            ELSE SUBSTR(med.visit_date,1,7)
        END, 1, 7
    ) AS visit_month,
    DAYOFWEEK(
        CASE
            WHEN med.visit_date LIKE '%/%' THEN
                TO_DATE(CONCAT(SUBSTR(med.visit_date,1,4),'-',
                               SUBSTR(med.visit_date,6,2),'-',
                               SUBSTR(med.visit_date,9,2)))
            ELSE TO_DATE(med.visit_date)
        END
    ) AS visit_weekday,
    med.visit_type,
    med.diagnosis,
    -- 费用信息
    exp.item_name,
    exp.item_category,
    exp.quantity,
    exp.unit_price,
    exp.total_amount,
    exp.reimbursable,
    exp.reimbursed_amount,
    exp.self_paid_amount,
    -- 报销比例衍生
    CASE
        WHEN exp.total_amount > 0 AND exp.reimbursed_amount IS NOT NULL
        THEN ROUND(exp.reimbursed_amount / exp.total_amount, 4)
        ELSE 0
    END AS reimburse_rate,
    '${hivevar:etl_date}' AS etl_date
FROM ods.ods_insurance_info ins
INNER JOIN ods.ods_medical_record med
    ON ins.person_id = med.person_id
    AND ins.dt = '${hivevar:etl_date}'
    AND med.dt = '${hivevar:etl_date}'
INNER JOIN ods.ods_expense_detail exp
    ON med.record_id = exp.record_id
    AND exp.dt = '${hivevar:etl_date}';
