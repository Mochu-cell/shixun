#!/bin/bash
# Re-import high-risk data from real spark output
INPUT_DIR="/home/hadoop/temp/analysis_results/abnormal_results"
OUTPUT_FILE="/home/hadoop/temp/analysis_results/high_risk_input.csv"
MYSQL_DB="data"
MYSQL_PASS="${MYSQL_PASS:-}"

if [ -z "$MYSQL_PASS" ]; then
    echo "请先设置 MySQL 密码环境变量：export MYSQL_PASS=<你的MySQL密码>"
    exit 1
fi

# 1. Truncate table
mysql -uroot -p$MYSQL_PASS $MYSQL_DB -e "TRUNCATE TABLE high_risk_person;" 2>/dev/null
echo "Table truncated"

# 2. Preprocess CSV using python3
/export/servers/python38/bin/python3 << 'PYEND'
import csv, os
INPUT_DIR = "/home/hadoop/temp/analysis_results/abnormal_results"
OUTPUT_FILE = "/home/hadoop/temp/analysis_results/high_risk_input.csv"
rows = 0
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for fn in sorted(os.listdir(INPUT_DIR)):
        if fn.startswith("part-") and fn.endswith(".csv"):
            with open(os.path.join(INPUT_DIR, fn), "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("risk_level","") != "高风险":
                        continue
                    uid = row.get("person_id","")
                    vc = int(float(row.get("visit_count",0)))
                    ava = float(row.get("avg_visit_amount",0))
                    ta = float(row.get("total_amount",0))
                    ap = float(row.get("abnormal_prob",0))
                    ats = []
                    if vc > 12: ats.append("频繁就诊")
                    if ava > 6000: ats.append("高额次均费用")
                    if ta > 50000: ats.append("总费用异常")
                    at = "综合异常"
                    if len(ats) == 1: at = ats[0]
                    elif ats: at = "、".join(ats)
                    desc = "就诊%d次；次均%.0f元；总计%.0f元" % (vc, ava, ta)
                    line = "|".join([uid, uid, at, "%.2f"%ta, "高风险", "%.4f"%ap, "2026-07-05", desc, row.get("age_group",""), row.get("insurance_type",""), str(vc)])
                    out.write(line + "\n")
                    rows += 1
print("Preprocessed: %d high-risk records" % rows)
PYEND

echo "Preprocessing done"

# 3. LOAD DATA into MySQL
mysql --local-infile=1 -uroot -p$MYSQL_PASS $MYSQL_DB -e "
    SET NAMES utf8mb4;
    LOAD DATA LOCAL INFILE '$OUTPUT_FILE'
    INTO TABLE high_risk_person
    CHARACTER SET utf8mb4
    FIELDS TERMINATED BY '|'
    LINES TERMINATED BY '\n'
    (user_id, user_name, abnormal_type, abnormal_amount, risk_level, abnormal_prob, detection_date, abnormal_desc, age_group, insurance_type, visit_count);
" 2>/dev/null

echo "LOAD DATA done"

# 4. Verify
mysql -uroot -p$MYSQL_PASS $MYSQL_DB -e "SELECT COUNT(1) AS high_risk_count FROM high_risk_person WHERE risk_level='高风险';"
mysql -uroot -p$MYSQL_PASS $MYSQL_DB -e "SELECT user_id, abnormal_type, abnormal_amount FROM high_risk_person LIMIT 5;"

echo "All done!"
