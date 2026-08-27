-- ============================================================
-- ODS层建表DDL — 完全匹配CSV文件列名和列顺序
-- 数据库：ods
-- 注意：列名、列顺序必须与CSV文件1:1对应
-- ============================================================

CREATE DATABASE IF NOT EXISTS ods
COMMENT 'ODS层-原始数据层，与CSV 1:1映射'
LOCATION '/user/hive/warehouse/ods.db';

USE ods;

-- ============================================================
-- 1. 参保人员信息表
-- CSV列：person_id,name,gender,age,id_card,insurance_type,region,register_date,status
-- ============================================================
DROP TABLE IF EXISTS ods.ods_insurance_info;

CREATE TABLE IF NOT EXISTS ods.ods_insurance_info (
    person_id       STRING    COMMENT '人员唯一标识',
    name            STRING    COMMENT '姓名',
    gender          STRING    COMMENT '性别',
    age             INT       COMMENT '年龄',
    id_card         STRING    COMMENT '身份证号',
    insurance_type  STRING    COMMENT '参保类型(城镇职工/城乡居民/灵活就业)',
    region          STRING    COMMENT '参保地区',
    register_date   STRING    COMMENT '参保登记日期',
    status          STRING    COMMENT '参保状态(在保/停保)',
    etl_date        STRING    COMMENT 'ETL导入时间'
)
COMMENT 'ODS层-参保人员信息表（与CSV 1:1映射）'
PARTITIONED BY (dt STRING COMMENT '按日分区,格式yyyyMMdd')
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
STORED AS TEXTFILE
TBLPROPERTIES ('skip.header.line.count'='1');

-- ============================================================
-- 2. 就诊记录表
-- CSV列：record_id,person_id,visit_date,hospital,department,diagnosis,doctor,visit_type
-- ============================================================
DROP TABLE IF EXISTS ods.ods_medical_record;

CREATE TABLE IF NOT EXISTS ods.ods_medical_record (
    record_id       STRING    COMMENT '就诊记录ID',
    person_id       STRING    COMMENT '患者标识',
    visit_date      STRING    COMMENT '就诊日期',
    hospital        STRING    COMMENT '就诊医院',
    department      STRING    COMMENT '科室',
    diagnosis       STRING    COMMENT '诊断结果',
    doctor          STRING    COMMENT '主治医生',
    visit_type      STRING    COMMENT '就诊类型(门诊/住院/急诊)',
    etl_date        STRING    COMMENT 'ETL导入时间'
)
COMMENT 'ODS层-就诊记录表（与CSV 1:1映射）'
PARTITIONED BY (dt STRING COMMENT '按日分区,格式yyyyMMdd')
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
TBLPROPERTIES ('skip.header.line.count'='1');

-- ============================================================
-- 3. 费用明细表
-- CSV列：detail_id,record_id,item_name,item_category,quantity,unit_price,total_amount,reimbursable,reimbursed_amount,self_paid_amount
-- ============================================================
DROP TABLE IF EXISTS ods.ods_expense_detail;

CREATE TABLE IF NOT EXISTS ods.ods_expense_detail (
    detail_id           STRING         COMMENT '费用明细ID',
    record_id           STRING         COMMENT '关联就诊记录ID',
    item_name           STRING         COMMENT '费用项目名称',
    item_category       STRING         COMMENT '费用项目类别',
    quantity            INT            COMMENT '数量',
    unit_price          DECIMAL(12,2)  COMMENT '单价',
    total_amount        DECIMAL(12,2)  COMMENT '总金额',
    reimbursable        STRING         COMMENT '是否可报销(Y/N)',
    reimbursed_amount   DECIMAL(12,2)  COMMENT '报销金额',
    self_paid_amount    DECIMAL(12,2)  COMMENT '自付金额',
    etl_date            STRING         COMMENT 'ETL导入时间'
)
COMMENT 'ODS层-费用明细表（与CSV 1:1映射）'
PARTITIONED BY (dt STRING COMMENT '按日分区,格式yyyyMMdd')
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
TBLPROPERTIES ('skip.header.line.count'='1');
