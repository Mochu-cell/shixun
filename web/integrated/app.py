#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗大数据与脑肿瘤影像智能检测系统
整合医保数据分析 + 脑肿瘤检测数据

整合医保数据分析与脑肿瘤检测数据
"""

from flask import Flask, render_template, jsonify
import pandas as pd
import pymysql
import os
import time

app = Flask(__name__)

# 数据缓存
_data_cache = None
_data_last_load = 0
_data_cache_ttl = 60  # 缓存60秒

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
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 30
}

def get_db_connection():
    """获取数据库连接（每次创建新连接）"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def find_column(df, possible_names, default=None):
    """根据可能的列名列表，找到实际存在的列名"""
    if df is None:
        return default
    for name in possible_names:
        if name in df.columns:
            return name
    return default

def load_data_from_mysql(force_reload=False):
    """从MySQL加载所有数据（带缓存）"""
    global _data_cache, _data_last_load
    
    current_time = time.time()
    
    if not force_reload and _data_cache is not None:
        if current_time - _data_last_load < _data_cache_ttl:
            return _data_cache
    
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        print("📊 开始加载数据...")
        
        # 加载医保数据（如果表存在）
        insurance_data = None
        cost_data = None
        
        try:
            insurance_data = pd.read_sql("SELECT * FROM rpt_insurance_stats", conn)
            print(f"  ✅ rpt_insurance_stats: {len(insurance_data)} 条")
        except Exception as e:
            print(f"  ⚠️ rpt_insurance_stats 表不存在或查询失败: {e}")
            insurance_data = pd.DataFrame()
        
        try:
            cost_data = pd.read_sql("SELECT * FROM rpt_cost_analysis", conn)
            print(f"  ✅ rpt_cost_analysis: {len(cost_data)} 条")
        except Exception as e:
            print(f"  ⚠️ rpt_cost_analysis 表不存在或查询失败: {e}")
            cost_data = pd.DataFrame()
        
        # 加载脑肿瘤检测数据（如果表存在）
        tumor_stats = None
        tumor_type = None
        detection_conf = None
        patient_summary = None
        
        try:
            tumor_stats = pd.read_sql("SELECT * FROM tumor_detection_stats", conn)
            print(f"  ✅ tumor_detection_stats: {len(tumor_stats)} 条")
        except:
            print("  ⚠️ tumor_detection_stats 表不存在")
        
        try:
            tumor_type = pd.read_sql("SELECT * FROM tumor_type_distribution", conn)
            print(f"  ✅ tumor_type_distribution: {len(tumor_type)} 条")
        except:
            print("  ⚠️ tumor_type_distribution 表不存在")
        
        try:
            detection_conf = pd.read_sql("SELECT * FROM detection_confidence", conn)
            print(f"  ✅ detection_confidence: {len(detection_conf)} 条")
        except:
            print("  ⚠️ detection_confidence 表不存在")
        
        try:
            patient_summary = pd.read_sql("SELECT * FROM patient_summary", conn)
            print(f"  ✅ patient_summary: {len(patient_summary)} 条")
        except:
            print("  ⚠️ patient_summary 表不存在")
        
        _data_cache = {
            'insurance_data': insurance_data,
            'cost_data': cost_data,
            'tumor_stats': tumor_stats,
            'tumor_type': tumor_type,
            'detection_conf': detection_conf,
            'patient_summary': patient_summary
        }
        _data_last_load = current_time
        
        print("✅ 数据加载完成")
        return _data_cache
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None
    finally:
        # 确保连接关闭
        if conn:
            try:
                conn.close()
                print("🔒 数据库连接已关闭")
            except:
                pass

# ============================================================
# 路由定义
# ============================================================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ============================================================
# 医保数据API
# ============================================================

@app.route('/api/kpi')
def api_kpi():
    """获取KPI数据（医保 + 脑肿瘤）"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify({'error': '数据加载失败'}), 500
        
        insurance_data = data['insurance_data']
        tumor_stats = data['tumor_stats']
        
        # 动态匹配列名
        col_person_id = find_column(insurance_data, ['person_id', '参保人ID', 'id'])
        col_total_amount = find_column(insurance_data, ['total_amount', '总费用', 'total_cost'])
        col_reimbursed = find_column(insurance_data, ['reimbursed_amount', '报销金额'])
        
        # 医保KPI
        total_persons = insurance_data[col_person_id].nunique() if col_person_id else len(insurance_data)
        total_cost = float(insurance_data[col_total_amount].sum()) if col_total_amount else 0
        total_reimburse = float(insurance_data[col_reimbursed].sum()) if col_reimbursed else 0
        reimburse_rate = total_reimburse / total_cost if total_cost > 0 else 0
        
        # 脑肿瘤检测KPI
        total_detections = 0
        tumor_detected = 0
        positive_rate = 0
        
        if tumor_stats is not None and len(tumor_stats) > 0:
            col_total_scans = find_column(tumor_stats, ['total_scans', '总检测数'])
            col_detected = find_column(tumor_stats, ['detected', '检出数'])
            col_positive_rate = find_column(tumor_stats, ['positive_rate', '阳性率'])
            
            if col_total_scans:
                total_detections = int(tumor_stats[col_total_scans].sum())
            if col_detected:
                tumor_detected = int(tumor_stats[col_detected].sum())
            if col_positive_rate:
                positive_rate = float(tumor_stats[col_positive_rate].mean())
        
        result = {
            'total_persons': int(total_persons),
            'total_cost': total_cost,
            'total_reimburse': total_reimburse,
            'reimburse_rate': float(reimburse_rate),
            'total_detections': total_detections,
            'tumor_detected': tumor_detected,
            'positive_rate': positive_rate
        }
        return jsonify(result)
    except Exception as e:
        print(f"❌ API /api/kpi 错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly')
def api_monthly():
    """获取月度趋势数据"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify({'error': '数据加载失败'}), 500
        
        cost_data = data['cost_data']
        
        col_stat_month = find_column(cost_data, ['stat_month', '月份', 'month'])
        col_total_amount = find_column(cost_data, ['total_amount', '总费用', 'amount'])
        col_avg_amount = find_column(cost_data, ['avg_amount', '次均费用'])
        col_visit_count = find_column(cost_data, ['visit_count', '就诊人次'])
        
        if col_stat_month is None or col_total_amount is None:
            return jsonify({'error': '找不到必要的列'}), 500
        
        monthly = cost_data.groupby(col_stat_month).agg({
            col_total_amount: 'sum',
            col_avg_amount: 'mean' if col_avg_amount else 'first',
            col_visit_count: 'sum' if col_visit_count else 'count'
        }).reset_index()
        
        result = {
            'months': monthly[col_stat_month].tolist(),
            'total_amount': monthly[col_total_amount].tolist(),
            'avg_amount': monthly[col_avg_amount].tolist() if col_avg_amount else [],
            'visit_count': monthly[col_visit_count].tolist() if col_visit_count else []
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/insurance_type')
def api_insurance_type():
    """获取参保类型统计"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify({'error': '数据加载失败'}), 500
        
        insurance_data = data['insurance_data']
        
        col_insurance_type = find_column(insurance_data, ['insurance_type', '参保类型', 'type'])
        col_total_amount = find_column(insurance_data, ['total_amount', '总费用', 'amount'])
        col_visit_count = find_column(insurance_data, ['visit_count', '就诊次数'])
        
        if col_insurance_type is None or col_total_amount is None:
            return jsonify({'error': '找不到必要的列'}), 500
        
        agg_dict = {col_total_amount: 'sum'}
        if col_visit_count:
            agg_dict[col_visit_count] = 'sum'
        
        type_stats = insurance_data.groupby(col_insurance_type).agg(agg_dict).reset_index()
        
        result = {
            'types': type_stats[col_insurance_type].tolist(),
            'total_amount': type_stats[col_total_amount].tolist(),
            'visit_count': type_stats[col_visit_count].tolist() if col_visit_count else []
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 脑肿瘤检测数据API（新增）
# ============================================================

@app.route('/api/tumor_type')
def api_tumor_type():
    """获取肿瘤类型分布"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify([])
        
        tumor_type = data['tumor_type']
        if tumor_type is None:
            return jsonify([])
        
        col_type = find_column(tumor_type, ['tumor_type', '肿瘤类型', 'type'])
        col_count = find_column(tumor_type, ['count', '数量', 'num'])
        col_percentage = find_column(tumor_type, ['percentage', '百分比', 'rate'])
        
        if col_type is None:
            return jsonify([])
        
        result = []
        for _, row in tumor_type.iterrows():
            result.append({
                'type': row[col_type],
                'count': int(row[col_count]) if col_count else 0,
                'percentage': float(row[col_percentage]) if col_percentage else 0
            })
        return jsonify(result)
    except Exception as e:
        return jsonify([])

@app.route('/api/detection_trend')
def api_detection_trend():
    """获取检测趋势"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify([])
        
        tumor_stats = data['tumor_stats']
        if tumor_stats is None:
            return jsonify([])
        
        col_date = find_column(tumor_stats, ['scan_date', '检测日期', 'date'])
        col_total = find_column(tumor_stats, ['total_scans', '总检测数'])
        col_detected = find_column(tumor_stats, ['detected', '检出数'])
        
        if col_date is None:
            return jsonify([])
        
        result = []
        for _, row in tumor_stats.iterrows():
            result.append({
                'date': str(row[col_date]),
                'total': int(row[col_total]) if col_total else 0,
                'detected': int(row[col_detected]) if col_detected else 0
            })
        return jsonify(result)
    except Exception as e:
        return jsonify([])

@app.route('/api/confidence')
def api_confidence():
    """获取置信度分布"""
    try:
        data = load_data_from_mysql()
        if data is None:
            return jsonify([])
        
        detection_conf = data['detection_conf']
        if detection_conf is None:
            return jsonify([])
        
        col_range = find_column(detection_conf, ['confidence_range', '置信度范围', 'range'])
        col_count = find_column(detection_conf, ['count', '数量', 'num'])
        
        if col_range is None:
            return jsonify([])
        
        result = []
        for _, row in detection_conf.iterrows():
            result.append({
                'range': row[col_range],
                'count': int(row[col_count]) if col_count else 0
            })
        return jsonify(result)
    except Exception as e:
        return jsonify([])

# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    print('=' * 60)
    print('  医疗大数据与脑肿瘤影像智能检测系统')
    print('=' * 60)
    print()
    print(f'  数据库: {MYSQL_CONFIG["host"]}:{MYSQL_CONFIG["port"]}/{MYSQL_CONFIG["database"]}')
    print()
    print('  访问地址: http://localhost:5002')
    print('=' * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
