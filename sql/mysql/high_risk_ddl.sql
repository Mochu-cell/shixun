-- ============================================================
-- 高风险人员表 DDL
-- 数据库: data
-- ============================================================

DROP TABLE IF EXISTS high_risk_person;

CREATE TABLE high_risk_person (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_id VARCHAR(50) COMMENT '人员ID',
    user_name VARCHAR(50) COMMENT '姓名',
    abnormal_type VARCHAR(100) COMMENT '异常类型',
    abnormal_amount DECIMAL(12,2) COMMENT '异常金额',
    risk_level VARCHAR(20) COMMENT '风险等级',
    abnormal_prob DECIMAL(10,4) COMMENT '异常概率',
    detection_date VARCHAR(20) COMMENT '检测日期',
    abnormal_desc VARCHAR(500) COMMENT '异常说明',
    age_group VARCHAR(20) COMMENT '年龄段',
    insurance_type VARCHAR(50) COMMENT '参保类型',
    visit_count INT COMMENT '就诊次数'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='高风险人员名单';

-- 查看高风险人数
SELECT COUNT(1) AS high_risk_count FROM high_risk_person WHERE risk_level='高风险';

-- 查看前10条
SELECT user_id, user_name, abnormal_type, abnormal_amount, detection_date, abnormal_desc 
FROM high_risk_person WHERE risk_level='高风险' LIMIT 10;
