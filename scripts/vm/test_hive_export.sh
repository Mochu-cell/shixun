#!/bin/bash
# 测试 hive INSERT OVERWRITE LOCAL DIRECTORY
export HADOOP_HOME=/export/servers/hadoop
export PATH=$HADOOP_HOME/bin:$PATH

rm -rf /tmp/hive_test_export

su - hadoop -c "hive -e \"
USE dm;
INSERT OVERWRITE LOCAL DIRECTORY '/tmp/hive_test_export/dm_hospital_stats'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '|'
NULL DEFINED AS ''
SELECT * FROM dm_hospital_stats;
\"" 2>&1 | tail -10

echo ""
echo "=== 输出 ==="
ls -la /tmp/hive_test_export/dm_hospital_stats/ 2>&1
cat /tmp/hive_test_export/dm_hospital_stats/* 2>&1 | head -5
