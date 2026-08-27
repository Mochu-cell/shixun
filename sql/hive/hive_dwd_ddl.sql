-- ============================================================
-- DWD层建表DDL — 参保+就诊+费用明细宽表
-- 数据库：dwd
-- ============================================================

CREATE DATABASE IF NOT EXISTS dwd
COMMENT 'DWD层-明细数据层，三表关联宽表'
LOCATION '/user/hive/warehouse/dwd.db';

USE dwd;

-- ============================================================
-- DWD层：参保+就诊+费用明细宽表
-- 由ODS三表JOIN + 字段衍生得到
-- ============================================================
DROP TABLE IF EXISTS dwd.dwd_insurance_detail;

CREATE TABLE IF NOT EXISTS dwd.dwd_insurance_detail (
    person_id           STRING         COMMENT '人员唯一标识',
    name                STRING         COMMENT '姓名(已脱敏)',
    gender              STRING         COMMENT '性别',
    age_group           STRING         COMMENT '年龄段(0-18/19-35/36-55/56-70/70+)',
    insurance_type      STRING         COMMENT '参保类型(标准化)',
    region              STRING         COMMENT '参保地区',
    enroll_date         STRING         COMMENT '参保登记日期',
    enroll_months       INT            COMMENT '参保月数',
    status              STRING         COMMENT '参保状态',
    record_id           STRING         COMMENT '就诊记录ID',
    hospital            STRING         COMMENT '就诊医院(标准化)',
    hospital_level      STRING         COMMENT '医院等级(根据名称推断)',
    department          STRING         COMMENT '科室',
    visit_date          STRING         COMMENT '就诊日期',
    visit_year          INT            COMMENT '就诊年份',
    visit_month         STRING         COMMENT '就诊月份(YYYY-MM)',
    visit_weekday       INT            COMMENT '就诊星期(1-7)',
    visit_type          STRING         COMMENT '就诊类型(门诊/住院/急诊)',
    diagnosis           STRING         COMMENT '诊断结果(标准化)',
    item_name           STRING         COMMENT '费用项目名称',
    item_category       STRING         COMMENT '费用项目类别',
    quantity            INT            COMMENT '数量',
    unit_price          DECIMAL(12,2)  COMMENT '单价',
    total_amount        DECIMAL(12,2)  COMMENT '总金额',
    reimbursable        STRING         COMMENT '是否可报销',
    reimbursed_amount   DECIMAL(12,2)  COMMENT '报销金额',
    self_paid_amount    DECIMAL(12,2)  COMMENT '自付金额',
    reimburse_rate      DECIMAL(10,4)   COMMENT '报销比例',
    etl_date            STRING         COMMENT 'ETL处理时间'
)
COMMENT 'DWD层-参保就诊费用明细宽表'
PARTITIONED BY (dt STRING COMMENT '按日分区')
STORED AS ORC;
