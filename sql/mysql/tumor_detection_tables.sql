CREATE TABLE IF NOT EXISTS data.tumor_detection_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_date DATE NOT NULL,
    total_scans INT DEFAULT 0,
    detected INT DEFAULT 0,
    positive_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data.tumor_type_distribution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tumor_type VARCHAR(50) NOT NULL,
    count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data.detection_confidence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    confidence_range VARCHAR(50) NOT NULL,
    count INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data.patient_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    scan_date DATE NOT NULL,
    tumor_type VARCHAR(50),
    confidence DECIMAL(5,2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

LOAD DATA LOCAL INFILE '/home/hadoop/temp/tomysql/tumor_detection_stats.txt'
INTO TABLE data.tumor_detection_stats
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(scan_date, total_scans, detected, positive_rate);

LOAD DATA LOCAL INFILE '/home/hadoop/temp/tomysql/tumor_type_distribution.txt'
INTO TABLE data.tumor_type_distribution
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(tumor_type, count, percentage);

LOAD DATA LOCAL INFILE '/home/hadoop/temp/tomysql/detection_confidence.txt'
INTO TABLE data.detection_confidence
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(confidence_range, count, percentage);

LOAD DATA LOCAL INFILE '/home/hadoop/temp/tomysql/patient_summary.txt'
INTO TABLE data.patient_summary
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(patient_id, scan_date, tumor_type, confidence, status);
