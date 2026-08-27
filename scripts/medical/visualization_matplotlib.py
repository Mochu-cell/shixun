#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保数据可视化图表绘制（Matplotlib）
从MySQL数据库读取分析结果，生成可视化图表
"""

import os
import sys
import platform
import shutil
import tempfile

# Set matplotlib config directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
mpl_config_dir = os.path.join(tempfile.gettempdir(), 'mplconfig_shixun')
os.environ['MPLCONFIGDIR'] = mpl_config_dir

# Clear font cache to force rescan
cache_dir = os.path.join(mpl_config_dir, 'fontlist-v330.json')
if os.path.exists(cache_dir):
    os.remove(cache_dir)
    print("  Cleared font cache")

import matplotlib
matplotlib.use('Agg')

# Disable font warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import numpy as np
import pymysql

# Set font after importing pyplot
# Use SimSun (宋体) which is available on the system
plt.rcParams['font.sans-serif'] = ['SimSun', 'SimHei', 'Microsoft YaHei', 'sans-serif']
print("  Using font: SimSun (宋体)")

plt.rcParams['axes.unicode_minus'] = False

# MySQL连接配置：优先环境变量，其次 config/local_config.py（不入库），默认 localhost
import sys as _sys
_REPO_ROOT = os.path.abspath(os.path.join(script_dir, '..', '..'))
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

# Output directory
OUTPUT_DIR = os.path.join(project_root, 'reports', '医保分析')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_column(df, possible_names, default=None):
    """根据可能的列名列表，找到实际存在的列名"""
    for name in possible_names:
        if name in df.columns:
            return name
    return default

# ============================================================
# Step 1: Configure Chinese display and styles
# ============================================================
print("=" * 60)
print("  医保数据可视化图表绘制（Matplotlib）")
print("=" * 60)

print("\n[Step 1] 配置中文显示和样式...")
print(f"  当前字体配置: {plt.rcParams['font.sans-serif']}")
print("  ✅ 中文字体配置完成")
print(f"  图表输出目录: {OUTPUT_DIR}")

# ============================================================
# Step 2: Connect to MySQL database
# ============================================================
print("\n[Step 2] 连接MySQL数据库...")

try:
    conn = pymysql.connect(**MYSQL_CONFIG)
    print("  ✅ MySQL连接成功")
except Exception as e:
    print(f"  ❌ MySQL连接失败: {e}")
    print("  请检查网络连接和MySQL配置")
    exit(1)

# ============================================================
# Step 3: Load data from MySQL
# ============================================================
print("\n[Step 3] 从MySQL加载数据...")

# Load insurance stats
try:
    insurance_data = pd.read_sql("SELECT * FROM rpt_insurance_stats", conn)
    print(f"  ✅ 加载rpt_insurance_stats: {len(insurance_data)}条记录")
    print(f"     列名: {list(insurance_data.columns)}")
except Exception as e:
    print(f"  ❌ 加载rpt_insurance_stats失败: {e}")
    insurance_data = None

# Load cost analysis
try:
    cost_data = pd.read_sql("SELECT * FROM rpt_cost_analysis", conn)
    print(f"  ✅ 加载rpt_cost_analysis: {len(cost_data)}条记录")
    print(f"     列名: {list(cost_data.columns)}")
except Exception as e:
    print(f"  ❌ 加载rpt_cost_analysis失败: {e}")
    cost_data = None

# Load hospital stats
try:
    hospital_data = pd.read_sql("SELECT * FROM rpt_hospital_stats", conn)
    print(f"  ✅ 加载rpt_hospital_stats: {len(hospital_data)}条记录")
    print(f"     列名: {list(hospital_data.columns)}")
except Exception as e:
    print(f"  ❌ 加载rpt_hospital_stats失败: {e}")
    hospital_data = None

# Load reimburse analysis
try:
    reimburse_data = pd.read_sql("SELECT * FROM rpt_reimburse_analysis", conn)
    print(f"  ✅ 加载rpt_reimburse_analysis: {len(reimburse_data)}条记录")
    print(f"     列名: {list(reimburse_data.columns)}")
except Exception as e:
    print(f"  ❌ 加载rpt_reimburse_analysis失败: {e}")
    reimburse_data = None

conn.close()
print("  MySQL连接已关闭")

if insurance_data is None or len(insurance_data) == 0:
    print("\n  ⚠️ 没有可用数据，请检查MySQL数据库中是否有数据")
    exit(0)

# ============================================================
# Step 3: Bar Chart - Insurance Type Statistics
# ============================================================
print("\n[Step 3] 绘制柱状图 - 各参保类型费用统计...")

col_insurance_type = find_column(insurance_data, ['insurance_type', 'ins_type'])
col_total_amount = find_column(insurance_data, ['total_amount', 'total_cost'])
col_visit_count = find_column(insurance_data, ['visit_count', 'visits'])
col_reimburse_rate = find_column(insurance_data, ['reimburse_rate', 'reimburse'])
col_person_id = find_column(insurance_data, ['person_id', 'id'])

if col_insurance_type and col_total_amount:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    type_stats = insurance_data.groupby(col_insurance_type).agg({
        col_total_amount: 'sum',
        col_visit_count: 'sum' if col_visit_count else 'count'
    }).reset_index()
    
    x = np.arange(len(type_stats))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, type_stats[col_total_amount] / 10000, width, 
                   label='总费用(万元)', color='#4C72B0')
    
    if col_visit_count:
        bars2 = ax.bar(x + width/2, type_stats[col_visit_count] / 100, width, 
                       label='就诊人次(百人)', color='#55A868')
    
    ax.set_xlabel('参保类型', fontsize=12)
    ax.set_ylabel('数值', fontsize=12)
    ax.set_title('各参保类型费用统计', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(type_stats[col_insurance_type])
    ax.legend()
    
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_bar_insurance_type.png', dpi=150, bbox_inches='tight')
    print(f"  已保存: {OUTPUT_DIR}/01_bar_insurance_type.png")
    plt.close()
else:
    print("  ⚠️ 缺少必要列，跳过柱状图")

# ============================================================
# Step 4: Line Chart - Monthly Cost Trend
# ============================================================
print("\n[Step 4] 绘制折线图 - 月度医保费用趋势...")

if cost_data is not None and len(cost_data) > 0:
    col_stat_month = find_column(cost_data, ['stat_month', 'month'])
    col_cost_total = find_column(cost_data, ['total_amount', 'total_cost'])
    col_cost_reimburse = find_column(cost_data, ['reimbursed_amount', 'reimburse_amount', 'reimburse'])
    col_cost_visit = find_column(cost_data, ['visit_count', 'visits'])
    
    if col_stat_month and col_cost_total:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        agg_dict = {col_cost_total: 'sum'}
        if col_cost_visit:
            agg_dict[col_cost_visit] = 'sum'
        
        monthly_stats = cost_data.groupby(col_stat_month).agg(agg_dict).reset_index()
        monthly_stats = monthly_stats.sort_values(col_stat_month)
        
        ax.plot(monthly_stats[col_stat_month], monthly_stats[col_cost_total] / 10000, 
                marker='o', linewidth=2, label='总费用(万元)', color='#4C72B0')
        
        if col_cost_reimburse:
            reimburse_monthly = cost_data.groupby(col_stat_month)[col_cost_reimburse].sum().reset_index()
            reimburse_monthly = reimburse_monthly.sort_values(col_stat_month)
            ax.plot(reimburse_monthly[col_stat_month], reimburse_monthly[col_cost_reimburse] / 10000, 
                    marker='s', linewidth=2, label='报销金额(万元)', color='#55A868')
        
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('金额(万元)', fontsize=12)
        ax.set_title('月度医保费用趋势', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{OUTPUT_DIR}/02_line_monthly_trend.png', dpi=150, bbox_inches='tight')
        print(f"  已保存: {OUTPUT_DIR}/02_line_monthly_trend.png")
        plt.close()
    else:
        print("  ⚠️ 缺少必要列，跳过折线图")

# ============================================================
# Step 5: Pie Chart - Insurance Type Distribution
# ============================================================
print("\n[Step 5] 绘制饼图 - 各参保类型人数占比...")

if col_insurance_type and col_total_amount:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    if col_person_id:
        type_count = insurance_data.groupby(col_insurance_type)[col_person_id].count().reset_index()
        type_count.columns = [col_insurance_type, 'count']
        
        colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2']
        wedges1, texts1, autotexts1 = ax1.pie(type_count['count'], labels=type_count[col_insurance_type], 
                autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('各参保类型人数占比', fontsize=12, fontweight='bold')
    
    type_amount = insurance_data.groupby(col_insurance_type)[col_total_amount].sum().reset_index()
    type_amount.columns = [col_insurance_type, 'amount']
    
    wedges2, texts2, autotexts2 = ax2.pie(type_amount['amount'], labels=type_amount[col_insurance_type], 
            autopct='%1.1f%%', colors=colors, startangle=90)
    ax2.set_title('各参保类型费用占比', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_pie_insurance_distribution.png', dpi=150, bbox_inches='tight')
    print(f"  已保存: {OUTPUT_DIR}/03_pie_insurance_distribution.png")
    plt.close()
else:
    print("  ⚠️ 缺少必要列，跳过饼图")

# ============================================================
# Step 6: Heatmap - Hospital Cost Heatmap
# ============================================================
print("\n[Step 6] 绘制热力图 - 医院费用热力图...")

if hospital_data is not None and len(hospital_data) > 0:
    col_hospital = find_column(hospital_data, ['hospital', 'hospital_name'])
    col_hosp_total = find_column(hospital_data, ['total_amount', 'total_cost', 'total_income'])
    col_hosp_visit = find_column(hospital_data, ['visit_count', 'visits'])
    col_hosp_patients = find_column(hospital_data, ['unique_patients', 'patients'])
    
    if col_hospital and col_hosp_total:
        top_hospitals = hospital_data.nlargest(10, col_hosp_total)
        
        heatmap_data = []
        labels = []
        for _, row in top_hospitals.iterrows():
            labels.append(str(row[col_hospital])[:15])
            values = []
            if col_hosp_total:
                values.append(row[col_hosp_total] / 10000)
            if col_hosp_visit:
                values.append(row[col_hosp_visit] / 100)
            if col_hosp_patients:
                values.append(row[col_hosp_patients] / 10)
            heatmap_data.append(values)
        
        if heatmap_data:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            heatmap_array = np.array(heatmap_data)
            sns.heatmap(heatmap_array, annot=True, fmt='.1f', 
                       xticklabels=['总费用(万)', '就诊(百)', '患者(十)'],
                       yticklabels=labels,
                       cmap='YlOrRd', ax=ax)
            
            ax.set_title('TOP10医院费用热力图', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(f'{OUTPUT_DIR}/04_heatmap_hospital.png', dpi=150, bbox_inches='tight')
            print(f"  已保存: {OUTPUT_DIR}/04_heatmap_hospital.png")
            plt.close()
    else:
        print("  ⚠️ 缺少必要列，跳过热力图")

# ============================================================
# Step 7: Scatter Plot - Cost vs Reimbursement Rate
# ============================================================
print("\n[Step 7] 绘制散点图 - 费用与报销率关系...")

if col_total_amount and col_reimburse_rate:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    insurance_data[col_reimburse_rate] = pd.to_numeric(insurance_data[col_reimburse_rate], errors='coerce')
    insurance_data[col_total_amount] = pd.to_numeric(insurance_data[col_total_amount], errors='coerce')
    
    scatter_data = insurance_data[[col_total_amount, col_reimburse_rate]].dropna()
    
    if len(scatter_data) > 0:
        if col_insurance_type and col_insurance_type in scatter_data.columns:
            for i, ins_type in enumerate(scatter_data[col_insurance_type].unique()):
                subset = scatter_data[scatter_data[col_insurance_type] == ins_type]
                ax.scatter(subset[col_total_amount], subset[col_reimburse_rate] * 100, 
                          alpha=0.6, label=ins_type, s=50)
        else:
            ax.scatter(scatter_data[col_total_amount], scatter_data[col_reimburse_rate] * 100, 
                      alpha=0.6, s=50)
        
        ax.set_xlabel('总费用', fontsize=12)
        ax.set_ylabel('报销率(%)', fontsize=12)
        ax.set_title('费用与报销率关系散点图', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{OUTPUT_DIR}/05_scatter_cost_reimburse.png', dpi=150, bbox_inches='tight')
        print(f"  已保存: {OUTPUT_DIR}/05_scatter_cost_reimburse.png")
        plt.close()
else:
    print("  ⚠️ 缺少必要列，跳过散点图")

# ============================================================
# Step 8: Combined Chart - Multi-dimensional Analysis
# ============================================================
print("\n[Step 8] 绘制组合图 - 多维度分析...")

if col_insurance_type and col_total_amount and col_visit_count and col_reimburse_rate:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    type_stats = insurance_data.groupby(col_insurance_type).agg({
        col_total_amount: 'sum',
        col_visit_count: 'sum',
        col_reimburse_rate: 'mean'
    }).reset_index()
    
    # Subplot 1: Total Amount Bar Chart
    axes[0, 0].bar(type_stats[col_insurance_type], type_stats[col_total_amount] / 10000, 
                   color='#4C72B0')
    axes[0, 0].set_title('各参保类型总费用', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('参保类型')
    axes[0, 0].set_ylabel('金额(万元)')
    
    # Subplot 2: Visit Count Bar Chart
    axes[0, 1].bar(type_stats[col_insurance_type], type_stats[col_visit_count], 
                   color='#55A868')
    axes[0, 1].set_title('各参保类型就诊人次', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('参保类型')
    axes[0, 1].set_ylabel('就诊人次')
    
    # Subplot 3: Average Reimbursement Rate Bar Chart
    axes[1, 0].bar(type_stats[col_insurance_type], type_stats[col_reimburse_rate] * 100, 
                   color='#C44E52')
    axes[1, 0].set_title('各参保类型平均报销率', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('参保类型')
    axes[1, 0].set_ylabel('报销率(%)')
    
    # Subplot 4: Cost Distribution Boxplot
    insurance_data.boxplot(column=col_total_amount, by=col_insurance_type, ax=axes[1, 1])
    axes[1, 1].set_title('各参保类型费用分布', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('参保类型')
    axes[1, 1].set_ylabel('费用')
    plt.suptitle('')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_combined_multi_analysis.png', dpi=150, bbox_inches='tight')
    print(f"  已保存: {OUTPUT_DIR}/06_combined_multi_analysis.png")
    plt.close()
else:
    print("  ⚠️ 缺少必要列，跳过组合图")

print("\n" + "=" * 60)
print("  所有图表绘制完成！")
print(f"  输出目录: {OUTPUT_DIR}")
print("=" * 60)
