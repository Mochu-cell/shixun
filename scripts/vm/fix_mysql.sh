#!/bin/bash
# 添加 local-infile=1 并重启 MySQL
sed -i '/^bind-address/ a local-infile=1' /etc/my.cnf
systemctl restart mysqld
sleep 2
echo "Config added:"
grep local-infile /etc/my.cnf
echo "MySQL status:"
systemctl status mysqld | grep Active
