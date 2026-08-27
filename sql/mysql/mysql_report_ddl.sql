-- ============================================================
-- MySQL报表层建表DDL — 对应DM层4张表
-- 注意：此文件由Shell脚本调用，数据库名由Shell参数传入
-- Shell用法: mysql -u... -p... $MYSQL_DB < mysql_report_ddl.sql
-- ============================================================

-- 不在此文件创建数据库，由Shell脚本决定目标数据库
-- 如果需要单独执行，先执行: USE data; 或 USE medical_report;

-- ============================================================
-- 报表1：参保人维度统计
-- ============================================================
DROP TABLE IF EXISTS rpt_insurance_stats;

CREATE TABLE rpt_insurance_stats (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    person_id           VARCHAR(50)    NOT NULL COMMENT '人员唯一标识',
    age_group           VARCHAR(20)    DEFAULT NULL COMMENT '年龄段',
    insurance_type      VARCHAR(30)    DEFAULT NULL COMMENT '参保类型',
    visit_count         INT            DEFAULT 0 COMMENT '总就诊次数',
    total_amount        DECIMAL(12,2)  DEFAULT 0 COMMENT '总费用',
    reimbursed_amount   DECIMAL(12,2)  DEFAULT 0 COMMENT '总报销金额',
    reimburse_rate      DECIMAL(10,4)  DEFAULT 0 COMMENT '综合报销比例',
    avg_amount          DECIMAL(12,2)  DEFAULT 0 COMMENT '次均费用',
    first_visit_date    VARCHAR(20)    DEFAULT NULL COMMENT '首次就诊日期',
    last_visit_date     VARCHAR(20)    DEFAULT NULL COMMENT '最近就诊日期',
    etl_date            VARCHAR(20)    DEFAULT NULL COMMENT 'ETL处理时间',
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_person_id (person_id),
    INDEX idx_age_group (age_group),
    INDEX idx_insurance_type (insurance_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='参保人维度统计报表';

-- ============================================================
-- 报表2：医院维度统计
-- ============================================================
DROP TABLE IF EXISTS rpt_hospital_stats;

CREATE TABLE rpt_hospital_stats (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    hospital            VARCHAR(100)   NOT NULL COMMENT '医院名称',
    hospital_level      VARCHAR(20)    DEFAULT NULL COMMENT '医院等级',
    visit_count         INT            DEFAULT 0 COMMENT '接诊量',
    unique_patients     INT            DEFAULT 0 COMMENT '独立患者数',
    total_amount        DECIMAL(12,2)  DEFAULT 0 COMMENT '总收入',
    reimbursed_amount   DECIMAL(12,2)  DEFAULT 0 COMMENT '总报销金额',
    reimburse_rate      DECIMAL(10,4)  DEFAULT 0 COMMENT '报销比例',
    top_diagnosis       VARCHAR(100)   DEFAULT NULL COMMENT '最常见诊断',
    etl_date            VARCHAR(20)    DEFAULT NULL COMMENT 'ETL处理时间',
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_hospital (hospital),
    INDEX idx_hospital_level (hospital_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医院维度统计报表';

-- ============================================================
-- 报表3：月度费用分析
-- ============================================================
DROP TABLE IF EXISTS rpt_cost_analysis;

CREATE TABLE rpt_cost_analysis (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    stat_month          VARCHAR(20)    NOT NULL COMMENT '统计月份',
    insurance_type      VARCHAR(30)    DEFAULT NULL COMMENT '参保类型',
    visit_count         INT            DEFAULT 0 COMMENT '就诊人次',
    total_amount        DECIMAL(12,2)  DEFAULT 0 COMMENT '总费用',
    reimbursed_amount   DECIMAL(12,2)  DEFAULT 0 COMMENT '总报销金额',
    avg_amount          DECIMAL(12,2)  DEFAULT 0 COMMENT '次均费用',
    reimburse_rate      DECIMAL(10,4)  DEFAULT 0 COMMENT '报销比例',
    etl_date            VARCHAR(20)    DEFAULT NULL COMMENT 'ETL处理时间',
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_stat_month (stat_month),
    INDEX idx_insurance_type (insurance_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度费用分析报表';

-- ============================================================
-- 报表4：报销分析
-- ============================================================
DROP TABLE IF EXISTS rpt_reimburse_analysis;

CREATE TABLE rpt_reimburse_analysis (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    age_group           VARCHAR(20)    DEFAULT NULL COMMENT '年龄段',
    insurance_type      VARCHAR(30)    DEFAULT NULL COMMENT '参保类型',
    hospital_level      VARCHAR(20)    DEFAULT NULL COMMENT '医院等级',
    visit_count         INT            DEFAULT 0 COMMENT '就诊次数',
    total_amount        DECIMAL(12,2)  DEFAULT 0 COMMENT '总费用',
    reimbursed_amount   DECIMAL(12,2)  DEFAULT 0 COMMENT '报销金额',
    self_paid_amount    DECIMAL(12,2)  DEFAULT 0 COMMENT '自付金额',
    reimburse_rate      DECIMAL(10,4)  DEFAULT 0 COMMENT '报销比例',
    avg_self_paid       DECIMAL(12,2)  DEFAULT 0 COMMENT '次均自付',
    etl_date            VARCHAR(20)    DEFAULT NULL COMMENT 'ETL处理时间',
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_age_group (age_group),
    INDEX idx_insurance_type (insurance_type),
    INDEX idx_hospital_level (hospital_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报销分析报表';

-- ============================================================
-- 完成
-- ============================================================
-- 执行完成后可验证：
-- SELECT table_name, table_rows FROM information_schema.tables 
-- WHERE table_schema = DATABASE() AND table_name LIKE 'rpt_%';