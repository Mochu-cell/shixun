#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保数据分析可视化仪表盘（Flask + ECharts）
Flask + ECharts 实现交互式数据可视化

运行方式：
  cd dashboard && python app.py
  访问 http://localhost:5000

数据源：MySQL数据库（远程连接虚拟机）
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import pymysql
import os
import json

app = Flask(__name__)

# MySQL连接配置：优先环境变量，其次 config/local_config.py（不入库），默认 localhost
import sys as _sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)
try:
    from config import local_config
except Exception:
    local_config = None

def _db_cfg(name, default):
    value = os.environ.get(name)
    if value:
        return value
    return getattr(local_config, name, None) if local_config else None or default

MYSQL_CONFIG = {
    'host': _db_cfg('MYSQL_HOST', 'localhost'),
    'port': int(_db_cfg('MYSQL_PORT', '3306')),
    'user': _db_cfg('MYSQL_USER', 'root'),
    'password': _db_cfg('MYSQL_PASSWORD', ''),
    'database': _db_cfg('MYSQL_DATABASE', 'data'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def find_column(df, possible_names, default=None):
    """根据可能的列名列表，找到实际存在的列名"""
    if df is None:
        return default
    for name in possible_names:
        if name in df.columns:
            return name
    return default

def load_data_from_mysql():
    """从MySQL加载所有数据"""
    conn = get_db_connection()
    if conn is None:
        return None, None, None, None
    
    try:
        # 加载参保人统计数据
        insurance_data = pd.read_sql("SELECT * FROM rpt_insurance_stats", conn)
        print(f"rpt_insurance_stats 列名: {list(insurance_data.columns)}")
        
        # 加载月度费用分析数据
        cost_data = pd.read_sql("SELECT * FROM rpt_cost_analysis", conn)
        print(f"rpt_cost_analysis 列名: {list(cost_data.columns)}")
        
        # 加载医院统计数据
        hospital_data = pd.read_sql("SELECT * FROM rpt_hospital_stats", conn)
        print(f"rpt_hospital_stats 列名: {list(hospital_data.columns)}")
        
        # 加载报销分析数据
        reimburse_data = pd.read_sql("SELECT * FROM rpt_reimburse_analysis", conn)
        print(f"rpt_reimburse_analysis 列名: {list(reimburse_data.columns)}")
        
        return insurance_data, cost_data, hospital_data, reimburse_data
    except Exception as e:
        print(f"数据加载失败: {e}")
        return None, None, None, None
    finally:
        conn.close()

# ============================================================
# 路由定义
# ============================================================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/kpi')
def api_kpi():
    """获取KPI数据"""
    insurance_data, cost_data, hospital_data, reimburse_data = load_data_from_mysql()
    
    if insurance_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_person_id = find_column(insurance_data, ['person_id', '参保人ID', 'id'])
    col_visit_count = find_column(insurance_data, ['visit_count', '就诊次数', 'visit_cnt'])
    col_total_amount = find_column(insurance_data, ['total_amount', '总费用', 'total_cost'])
    col_reimburse_rate = find_column(insurance_data, ['reimburse_rate', '报销比例', '报销率'])
    col_hospital = find_column(hospital_data, ['hospital', '医院名称', '医院']) if hospital_data is not None else None
    
    kpi = {
        'total_persons': int(insurance_data[col_person_id].nunique()) if col_person_id else 0,
        'visit_count': int(insurance_data[col_visit_count].sum()) if col_visit_count else 0,
        'total_amount': float(insurance_data[col_total_amount].sum()) if col_total_amount else 0,
        'avg_reimburse_rate': float(insurance_data[col_reimburse_rate].mean()) if col_reimburse_rate else 0,
        'hospital_count': int(hospital_data[col_hospital].nunique()) if hospital_data is not None and col_hospital else 0,
        'abnormal_count': 0  # 异常预警数，暂时为0
    }
    
    return jsonify(kpi)

@app.route('/api/insurance_type')
def api_insurance_type():
    """获取各参保类型统计"""
    insurance_data, _, _, _ = load_data_from_mysql()
    
    if insurance_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_insurance_type = find_column(insurance_data, ['insurance_type', '参保类型'])
    col_person_id = find_column(insurance_data, ['person_id', '参保人ID', 'id'])
    col_total_amount = find_column(insurance_data, ['total_amount', '总费用', 'total_cost'])
    col_visit_count = find_column(insurance_data, ['visit_count', '就诊次数', 'visit_cnt'])
    col_reimburse_rate = find_column(insurance_data, ['reimburse_rate', '报销比例', '报销率'])
    
    if not all([col_insurance_type, col_person_id, col_total_amount, col_visit_count, col_reimburse_rate]):
        return jsonify({'error': '缺少必要列名'}), 500
    
    agg_dict = {
        col_person_id: 'count',
        col_total_amount: 'sum',
        col_visit_count: 'sum',
        col_reimburse_rate: 'mean'
    }
    
    stats = insurance_data.groupby(col_insurance_type).agg(agg_dict).reset_index()
    
    # 返回前端期望的格式
    return jsonify({
        'types': stats[col_insurance_type].tolist(),
        'total_amount': stats[col_total_amount].tolist(),
        'visit_count': stats[col_visit_count].tolist(),
        'person_count': stats[col_person_id].tolist(),
        'avg_reimburse_rate': stats[col_reimburse_rate].tolist()
    })

@app.route('/api/monthly')
def api_monthly():
    """获取月度趋势数据"""
    _, cost_data, _, _ = load_data_from_mysql()
    
    if cost_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_stat_month = find_column(cost_data, ['stat_month', '统计月份', 'month'])
    col_total_amount = find_column(cost_data, ['total_amount', '总费用', 'total_cost'])
    col_visit_count = find_column(cost_data, ['visit_count', '就诊次数', 'visit_cnt'])
    col_avg_amount = find_column(cost_data, ['avg_amount', '次均费用', 'avg_cost'])
    
    if not all([col_stat_month, col_total_amount]):
        return jsonify({'error': '缺少必要列名'}), 500
    
    agg_dict = {col_total_amount: 'sum'}
    if col_visit_count:
        agg_dict[col_visit_count] = 'sum'
    if col_avg_amount:
        agg_dict[col_avg_amount] = 'mean'
    
    monthly = cost_data.groupby(col_stat_month).agg(agg_dict).reset_index()
    monthly = monthly.sort_values(col_stat_month)
    
    # 返回前端期望的格式
    return jsonify({
        'months': monthly[col_stat_month].tolist(),
        'total_amount': monthly[col_total_amount].tolist(),
        'avg_amount': monthly[col_avg_amount].tolist() if col_avg_amount else [],
        'visit_count': monthly[col_visit_count].tolist() if col_visit_count else []
    })

@app.route('/api/expense_structure')
def api_expense_structure():
    """获取费用结构数据"""
    _, cost_data, _, _ = load_data_from_mysql()
    
    if cost_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_insurance_type = find_column(cost_data, ['insurance_type', '参保类型'])
    col_total_amount = find_column(cost_data, ['total_amount', '总费用', 'total_cost'])
    
    if not all([col_insurance_type, col_total_amount]):
        return jsonify({'error': '缺少必要列名'}), 500
    
    stats = cost_data.groupby(col_insurance_type)[col_total_amount].sum().reset_index()
    
    # 返回前端期望的格式
    return jsonify({
        'categories': stats[col_insurance_type].tolist(),
        'amounts': stats[col_total_amount].tolist()
    })

@app.route('/api/hospital_heatmap')
def api_hospital_heatmap():
    """获取医院热力图数据"""
    _, _, hospital_data, _ = load_data_from_mysql()
    
    if hospital_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_hospital = find_column(hospital_data, ['hospital', '医院名称', '医院'])
    col_total_amount = find_column(hospital_data, ['total_amount', '总费用', 'total_cost'])
    col_visit_count = find_column(hospital_data, ['visit_count', '就诊次数', 'visit_cnt'])
    
    if not all([col_hospital, col_total_amount]):
        return jsonify({'error': '缺少必要列名'}), 500
    
    # 取TOP10医院
    top_hospitals = hospital_data.nlargest(10, col_total_amount)
    
    # 返回前端期望的格式
    hospitals = top_hospitals[col_hospital].tolist()
    data = []
    max_value = 0
    
    for i, (_, row) in enumerate(top_hospitals.iterrows()):
        amount = float(row[col_total_amount])
        data.append([0, i, amount])  # [科室索引, 医院索引, 费用]
        if amount > max_value:
            max_value = amount
    
    return jsonify({
        'hospitals': hospitals,
        'departments': ['门诊'],  # 简化为单科室
        'data': data,
        'max_value': max_value
    })

@app.route('/api/age_distribution')
def api_age_distribution():
    """获取年龄分布数据"""
    insurance_data, _, _, _ = load_data_from_mysql()
    
    if insurance_data is None:
        return jsonify({'error': '数据加载失败'}), 500
    
    # 动态匹配列名
    col_age_group = find_column(insurance_data, ['age_group', '年龄段'])
    col_person_id = find_column(insurance_data, ['person_id', '参保人ID', 'id'])
    col_total_amount = find_column(insurance_data, ['total_amount', '总费用', 'total_cost'])
    col_visit_count = find_column(insurance_data, ['visit_count', '就诊次数', 'visit_cnt'])
    
    if not all([col_age_group, col_person_id, col_total_amount, col_visit_count]):
        return jsonify({'error': '缺少必要列名'}), 500
    
    agg_dict = {
        col_person_id: 'count',
        col_total_amount: 'sum',
        col_visit_count: 'sum'
    }
    
    stats = insurance_data.groupby(col_age_group).agg(agg_dict).reset_index()
    
    # 返回前端期望的格式
    return jsonify({
        'age_groups': stats[col_age_group].tolist(),
        'counts': stats[col_person_id].tolist(),
        'total_amount': stats[col_total_amount].tolist(),
        'visit_count': stats[col_visit_count].tolist()
    })

@app.route('/api/abnormal_list')
def api_abnormal_list():
    """获取异常列表"""
    # 返回前端期望的格式
    return jsonify({
        'records': []
    })

@app.route('/api/high_risk_count')
def api_high_risk_count():
    """获取高风险人数KPI"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': '数据库连接失败'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM high_risk_person WHERE risk_level='高风险'")
        count = cursor.fetchone()[0]
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/high_risk_list')
def api_high_risk_list():
    """获取高风险人员名单（支持分页）"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': '数据库连接失败'}), 500
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        offset = (page - 1) * page_size

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM high_risk_person WHERE risk_level='高风险'")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT user_id, user_name, age_group, abnormal_type, abnormal_amount, 
                   detection_date, abnormal_desc
            FROM high_risk_person 
            WHERE risk_level='高风险'
            ORDER BY abnormal_prob DESC
            LIMIT %s OFFSET %s
        """, (page_size, offset))

        records = []
        for row in cursor.fetchall():
            records.append({
                'user_id': row[0],
                'user_name': row[1],
                'age_group': row[2],
                'abnormal_type': row[3],
                'abnormal_amount': float(row[4]),
                'detection_date': row[5],
                'abnormal_desc': row[6]
            })

        return jsonify({'records': records, 'total': total, 'page': page, 'page_size': page_size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("  医保数据分析可视化仪表盘")
    print("=" * 60)
    print(f"  MySQL服务器: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    print(f"  数据库: {MYSQL_CONFIG['database']}")
    print("-" * 60)
    
    # 测试数据库连接
    conn = get_db_connection()
    if conn:
        print("  ✅ 数据库连接成功")
        conn.close()
    else:
        print("  ❌ 数据库连接失败，请检查配置")
        exit(1)
    
    print("-" * 60)
    print("  启动Web服务器...")
    print("  访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
