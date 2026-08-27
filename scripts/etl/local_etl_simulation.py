"""
============================================================
本地 ETL 流水线模拟（无需 Hadoop 环境）
功能：用Pandas模拟 ODS→DWD→DM 的ETL流程
执行：python local_etl_simulation.py
============================================================
适用场景：
  - 本地开发环境无Hadoop/Spark时使用
  - 理解ETL分层逻辑后再迁移到Hive/Spark
  - 快速验证数据转换逻辑的正确性
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ============ 自动查找项目根目录 ============
def _find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(current, 'data')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

PROJECT_ROOT = _find_project_root()
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'medical_insurance')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'warehouse')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'ods'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'dwd'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'dm'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'analysis'), exist_ok=True)

ETL_DATE = datetime.now().strftime('%Y-%m-%d')
print("=" * 60)
print("  本地ETL模拟 — 医保数据数仓分层")
print(f"  ETL日期: {ETL_DATE}")
print(f"  数据目录: {DATA_DIR}")
print("=" * 60)

# ================================================================
# ODS层：原始数据加载（与CSV 1:1映射，增加etl_date）
# ================================================================
print("\n" + "=" * 60)
print("  ODS层：原始数据加载")
print("=" * 60)

print("\n[1] 加载参保人员表...")
df_person = pd.read_csv(os.path.join(DATA_DIR, 'insurance_info.csv'))
df_person['etl_date'] = ETL_DATE
print(f"  行数: {len(df_person)}, 列数: {len(df_person.columns)}")
print(f"  字段: {list(df_person.columns)}")

print("\n[2] 加载就诊记录表...")
df_record = pd.read_csv(os.path.join(DATA_DIR, 'medical_record.csv'))
df_record['etl_date'] = ETL_DATE
print(f"  行数: {len(df_record)}, 列数: {len(df_record.columns)}")

print("\n[3] 加载费用明细表...")
df_expense = pd.read_csv(os.path.join(DATA_DIR, 'expense_detail.csv'))
df_expense['etl_date'] = ETL_DATE
print(f"  行数: {len(df_expense)}, 列数: {len(df_expense.columns)}")

# ODS层保存
df_person.to_csv(os.path.join(OUTPUT_DIR, 'ods', 'ods_insurance_info.csv'), index=False)
df_record.to_csv(os.path.join(OUTPUT_DIR, 'ods', 'ods_medical_record.csv'), index=False)
df_expense.to_csv(os.path.join(OUTPUT_DIR, 'ods', 'ods_expense_detail.csv'), index=False)
print("\n  ✅ ODS层数据保存完成")

# ODS层数据质量校验
print("\n  --- ODS层数据质量校验 ---")
print(f"  参保人员-年龄异常: {len(df_person[(df_person['age'] < 0) | (df_person['age'] > 120)])} 条")
print(f"  就诊记录-医院缺失: {df_record['hospital'].isna().sum()} 条")
print(f"  费用明细-金额异常: {len(df_expense[df_expense['total_amount'] < 0])} 条")


# ================================================================
# DWD层：三表JOIN + 衍生字段 + 数据标准化
# ================================================================
print("\n" + "=" * 60)
print("  DWD层：宽表构建（三表JOIN + 衍生字段）")
print("=" * 60)

# --- 衍生字段：参保人信息 ---
print("\n[1] 参保人字段衍生...")

# 年龄段
def age_to_group(age):
    if pd.isna(age) or age < 0: return '未知'
    if age < 19: return '0-18'
    if age < 36: return '19-35'
    if age < 56: return '36-55'
    if age < 71: return '56-70'
    return '70+'

df_person['age_group'] = df_person['age'].apply(age_to_group)

# 参保类型标准化
type_map = {'城镇职工': '城镇职工', '城职': '城镇职工',
            '城乡居民': '城乡居民', '城乡': '城乡居民',
            '灵活就业': '灵活就业', '灵活': '灵活就业'}
df_person['insurance_type_std'] = df_person['insurance_type'].map(type_map).fillna('其他')

# 是否在保标准化（字段名可能为status或is_active）
status_col = 'status' if 'status' in df_person.columns else 'is_active'
active_map = {'是': '是', 'Y': '是', '1': '是', '在保': '是', 'active': '是',
              '否': '否', 'N': '否', '0': '否', '停保': '否', 'inactive': '否'}
df_person['is_active_std'] = df_person[status_col].map(active_map).fillna('未知')

# 参保月数（字段名可能为register_date或enroll_date）
date_col = 'register_date' if 'register_date' in df_person.columns else 'enroll_date'
df_person[date_col] = pd.to_datetime(df_person[date_col], format='mixed', errors='coerce')
df_person['enroll_months'] = ((pd.Timestamp('2025-07-10') - df_person[date_col]).dt.days / 30).round().astype('float').astype('Int64')

print(f"  年龄段分布:\n{df_person['age_group'].value_counts().to_string()}")
print(f"  参保类型标准化后:\n{df_person['insurance_type_std'].value_counts().to_string()}")

# --- 衍生字段：就诊记录 ---
print("\n[2] 就诊记录字段衍生...")

# 医院名称标准化
def standardize_hospital(name):
    if pd.isna(name): return '未知'
    if '第一人民医院' in name: return '市第一人民医院'
    if '第二人民医院' in name: return '市第二人民医院'
    if '中心医院' in name: return '市中心医院'
    if '人民医院' in name: return '市人民医院'
    return name

df_record['hospital_std'] = df_record['hospital'].apply(standardize_hospital)

# 医院等级推断
def infer_hospital_level(name):
    if pd.isna(name): return '未分级'
    if '三甲' in name or '第一人民' in name: return '三级甲等'
    if '三乙' in name or '中心' in name: return '三级乙等'
    if '二甲' in name or '第二人民' in name: return '二级甲等'
    if '二乙' in name: return '二级乙等'
    if '社区' in name or '卫生' in name: return '一级'
    return '未分级'

df_record['hospital_level'] = df_record['hospital'].apply(infer_hospital_level)

# 就诊日期衍生
df_record['visit_date'] = pd.to_datetime(df_record['visit_date'], format='mixed', errors='coerce')
df_record['visit_year'] = df_record['visit_date'].dt.year
df_record['visit_month'] = df_record['visit_date'].dt.strftime('%Y-%m')
df_record['visit_weekday'] = df_record['visit_date'].dt.dayofweek + 1  # 1=周一, 7=周日

# 诊断标准化
diag_map = {'hypertension': '高血压', 'Hypertension': '高血压',
            'diabetes': '糖尿病', 'Diabetes': '糖尿病',
            'pneumonia': '肺炎', 'Pneumonia': '肺炎',
            'coronary heart disease': '冠心病',
            'cold': '感冒', 'fracture': '骨折'}
df_record['diagnosis_std'] = df_record['diagnosis'].replace(diag_map)

# 是否报销从费用明细推导（有报销金额>0则报销）
if 'is_reimbursed' in df_record.columns:
    reimbursed_map = {'是': '是', 'Y': '是', '1': '是', '否': '否', 'N': '否', '0': '否'}
    df_record['is_reimbursed_std'] = df_record['is_reimbursed'].map(reimbursed_map).fillna('未知')
else:
    # 从费用明细推导
    _reimb_col = 'reimbursed_amount' if 'reimbursed_amount' in df_expense.columns else 'reimburse_amount'
    has_reimburse = df_expense.groupby('record_id')[_reimb_col].sum() > 0
    df_record = df_record.merge(
        has_reimburse.reset_index().rename(columns={_reimb_col: '_has_reimburse'}),
        on='record_id', how='left'
    )
    df_record['is_reimbursed_std'] = df_record['_has_reimburse'].map({True: '是', False: '否'}).fillna('未知')

print(f"  医院等级分布:\n{df_record['hospital_level'].value_counts().to_string()}")

# --- 费用按就诊记录聚合 ---
print("\n[3] 费用按就诊记录聚合...")
# 费用按就诊记录聚合（字段名适配）
amount_col = 'total_amount'
reimburse_col = 'reimbursed_amount' if 'reimbursed_amount' in df_expense.columns else 'reimburse_amount'
df_expense_by_record = df_expense.groupby('record_id').agg(
    total_visit_amount=(amount_col, 'sum'),
    total_reimburse=(reimburse_col, 'sum')
).reset_index()
df_expense_by_record['reimburse_rate'] = np.where(
    df_expense_by_record['total_visit_amount'] > 0,
    (df_expense_by_record['total_reimburse'] / df_expense_by_record['total_visit_amount']).round(4),
    0
)
print(f"  聚合后费用记录数: {len(df_expense_by_record)}")

# --- 三表JOIN构建DWD宽表 ---
print("\n[4] 三表JOIN构建DWD宽表...")

# 参保人 + 就诊记录
df_dwd = df_record.merge(
    df_person[['person_id', 'name', 'gender', 'age_group', 'insurance_type_std',
               'enroll_months', 'is_active_std']],
    on='person_id', how='left'
)

# + 费用聚合
df_dwd = df_dwd.merge(df_expense_by_record, on='record_id', how='left')

# 选择DWD层字段
# 选择DWD层字段（适配实际CSV列名）
dwd_cols = {
    'person_id': 'person_id', 'name': 'name', 'gender': 'gender',
    'age_group': 'age_group', 'insurance_type_std': 'insurance_type',
    'enroll_months': 'enroll_months', 'is_active_std': 'is_active',
    'record_id': 'record_id', 'hospital_std': 'hospital',
    'hospital_level': 'hospital_level', 'department': 'department',
    'visit_date': 'visit_date', 'visit_year': 'visit_year',
    'visit_month': 'visit_month', 'visit_weekday': 'visit_weekday',
    'diagnosis_std': 'diagnosis', 'is_reimbursed_std': 'is_reimbursed',
    'total_visit_amount': 'total_visit_amount',
    'total_reimburse': 'total_reimburse', 'reimburse_rate': 'reimburse_rate'
}
df_dwd_final = df_dwd[list(dwd_cols.keys())].rename(columns=dwd_cols).copy()
df_dwd_final['etl_date'] = ETL_DATE

# 保存DWD层
df_dwd_final.to_csv(os.path.join(OUTPUT_DIR, 'dwd', 'dwd_insurance_detail.csv'), index=False)
print(f"  DWD宽表行数: {len(df_dwd_final)}")
print(f"  DWD宽表列数: {len(df_dwd_final.columns)}")
print("  ✅ DWD层保存完成")


# ================================================================
# DM层：四张统计维度表
# ================================================================
print("\n" + "=" * 60)
print("  DM层：四维聚合统计")
print("=" * 60)

# 过滤有效记录
df_valid = df_dwd_final[df_dwd_final['record_id'].notna()].copy()

# --- DM1: 参保人维度统计 ---
print("\n[1] DM参保人维度统计...")
dm_insurance = df_valid.groupby(['person_id', 'age_group', 'insurance_type']).agg(
    visit_count=('record_id', 'nunique'),
    total_amount=('total_visit_amount', 'sum'),
    total_reimburse=('total_reimburse', 'sum'),
    first_visit_date=('visit_date', 'min'),
    last_visit_date=('visit_date', 'max')
).reset_index()

dm_insurance['reimburse_rate'] = np.where(
    dm_insurance['total_amount'] > 0,
    (dm_insurance['total_reimburse'] / dm_insurance['total_amount']).round(4), 0
)
dm_insurance['avg_visit_amount'] = np.where(
    dm_insurance['visit_count'] > 0,
    (dm_insurance['total_amount'] / dm_insurance['visit_count']).round(2), 0
)
dm_insurance['etl_date'] = ETL_DATE

print(f"  行数: {len(dm_insurance)}")
dm_insurance.to_csv(os.path.join(OUTPUT_DIR, 'dm', 'dm_insurance_stats.csv'), index=False)

# --- DM2: 医院维度统计 ---
print("\n[2] DM医院维度统计...")
dm_hospital = df_valid.groupby(['hospital', 'hospital_level']).agg(
    visit_count=('record_id', 'count'),
    unique_patients=('person_id', 'nunique'),
    total_amount=('total_visit_amount', 'sum'),
    total_reimburse=('total_reimburse', 'sum'),
    top_diagnosis=('diagnosis', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '未知')
).reset_index()

dm_hospital['reimburse_rate'] = np.where(
    dm_hospital['total_amount'] > 0,
    (dm_hospital['total_reimburse'] / dm_hospital['total_amount']).round(4), 0
)
dm_hospital['etl_date'] = ETL_DATE

print(f"  行数: {len(dm_hospital)}")
dm_hospital.to_csv(os.path.join(OUTPUT_DIR, 'dm', 'dm_hospital_stats.csv'), index=False)

# --- DM3: 月度费用分析 ---
print("\n[3] DM月度费用分析...")
dm_cost = df_valid.groupby(['visit_month', 'insurance_type']).agg(
    visit_count=('record_id', 'count'),
    total_amount=('total_visit_amount', 'sum'),
    total_reimburse=('total_reimburse', 'sum')
).reset_index()

dm_cost['avg_amount'] = np.where(
    dm_cost['visit_count'] > 0,
    (dm_cost['total_amount'] / dm_cost['visit_count']).round(2), 0
)
dm_cost['reimburse_rate'] = np.where(
    dm_cost['total_amount'] > 0,
    (dm_cost['total_reimburse'] / dm_cost['total_amount']).round(4), 0
)
dm_cost['etl_date'] = ETL_DATE
dm_cost = dm_cost.rename(columns={'visit_month': 'stat_month'})

print(f"  行数: {len(dm_cost)}")
dm_cost.to_csv(os.path.join(OUTPUT_DIR, 'dm', 'dm_cost_analysis.csv'), index=False)

# --- DM4: 报销分析 ---
print("\n[4] DM报销分析...")
dm_reimburse = df_valid.groupby(['insurance_type', 'hospital_level']).agg(
    visit_count=('record_id', 'count'),
    total_amount=('total_visit_amount', 'sum'),
    total_reimburse=('total_reimburse', 'sum')
).reset_index()

dm_reimburse['self_pay'] = (dm_reimburse['total_amount'] - dm_reimburse['total_reimburse']).round(2)
dm_reimburse['reimburse_rate'] = np.where(
    dm_reimburse['total_amount'] > 0,
    (dm_reimburse['total_reimburse'] / dm_reimburse['total_amount']).round(4), 0
)
dm_reimburse['self_pay_rate'] = np.where(
    dm_reimburse['total_amount'] > 0,
    (dm_reimburse['self_pay'] / dm_reimburse['total_amount']).round(4), 0
)
dm_reimburse['etl_date'] = ETL_DATE

print(f"  行数: {len(dm_reimburse)}")
dm_reimburse.to_csv(os.path.join(OUTPUT_DIR, 'dm', 'dm_reimburse_analysis.csv'), index=False)

print("\n  ✅ DM层四张表保存完成")


# ================================================================
# 聚合分析：12个主题
# ================================================================
print("\n" + "=" * 60)
print("  聚合分析：12个分析主题")
print("=" * 60)

analysis_results = {}

# 主题1：参保类型分布与费用对比
a1 = df_valid.groupby('insurance_type').agg(
    参保人数=('person_id', 'nunique'),
    就诊人次=('record_id', 'count'),
    总费用=('total_visit_amount', 'sum'),
    次均费用=('total_visit_amount', 'mean'),
    平均报销率=('reimburse_rate', 'mean')
).round(2)
print("\n【主题1】参保类型分布与费用对比:")
print(a1.to_string())
analysis_results['主题1_参保类型分布'] = a1

# 主题2：高费用TOP10
a2 = dm_insurance.nlargest(10, 'total_amount')[
    ['person_id', 'age_group', 'insurance_type', 'visit_count', 'total_amount', 'reimburse_rate']
]
print("\n【主题2】高费用参保人TOP10:")
print(a2.to_string())
analysis_results['主题2_高费用TOP10'] = a2

# 主题3：医院接诊量TOP10
a3 = dm_hospital.nlargest(10, 'visit_count')[
    ['hospital', 'hospital_level', 'visit_count', 'unique_patients', 'total_amount', 'reimburse_rate']
]
print("\n【主题3】医院接诊量TOP10:")
print(a3.to_string())
analysis_results['主题3_医院接诊TOP10'] = a3

# 主题4：不同等级医院费用对比
a4 = df_valid.groupby('hospital_level').agg(
    就诊人次=('record_id', 'count'),
    总费用=('total_visit_amount', 'sum'),
    次均费用=('total_visit_amount', 'mean'),
    平均报销率=('reimburse_rate', 'mean')
).round(4)
print("\n【主题4】不同等级医院费用对比:")
print(a4.to_string())
analysis_results['主题4_医院等级对比'] = a4

# 主题5：月度费用趋势
a5 = dm_cost[dm_cost['insurance_type'] == '城镇职工'][
    ['stat_month', 'visit_count', 'total_amount', 'avg_amount', 'reimburse_rate']
].sort_values('stat_month')
print("\n【主题5】城镇职工月度费用趋势:")
print(a5.to_string())
analysis_results['主题5_月度趋势'] = a5

# 主题6：月度环比增长
a6_monthly = df_valid.groupby('visit_month').agg(
    visit_count=('record_id', 'count'),
    total_amount=('total_visit_amount', 'sum')
).sort_index()
a6_monthly['上月人次'] = a6_monthly['visit_count'].shift(1)
a6_monthly['上月费用'] = a6_monthly['total_amount'].shift(1)
a6_monthly['人次环比增长率'] = ((a6_monthly['visit_count'] - a6_monthly['上月人次']) / a6_monthly['上月人次'] * 100).round(2)
a6_monthly['费用环比增长率'] = ((a6_monthly['total_amount'] - a6_monthly['上月费用']) / a6_monthly['上月费用'] * 100).round(2)
print("\n【主题6】月度环比增长分析:")
print(a6_monthly.round(2).to_string())
analysis_results['主题6_环比增长'] = a6_monthly

# 主题7：报销率矩阵
a7 = dm_reimburse[['insurance_type', 'hospital_level', 'visit_count', 'reimburse_rate', 'self_pay_rate']].copy()
a7['报销率%'] = (a7['reimburse_rate'] * 100).round(2)
a7['自付率%'] = (a7['self_pay_rate'] * 100).round(2)
print("\n【主题7】参保类型×医院等级 报销率矩阵:")
print(a7[['insurance_type', 'hospital_level', 'visit_count', '报销率%', '自付率%']].to_string())
analysis_results['主题7_报销率矩阵'] = a7

# 主题9：年龄段×参保类型交叉
a9 = df_valid.groupby(['age_group', 'insurance_type']).agg(
    参保人数=('person_id', 'nunique'),
    就诊人次=('record_id', 'count'),
    次均费用=('total_visit_amount', 'mean'),
    平均报销率=('reimburse_rate', 'mean')
).round(4)
print("\n【主题9】年龄段×参保类型交叉分析:")
print(a9.to_string())
analysis_results['主题9_交叉分析'] = a9

# 主题11：科室排名TOP10
a11 = df_valid.groupby('department').agg(
    就诊人次=('record_id', 'count'),
    独立患者数=('person_id', 'nunique'),
    总费用=('total_visit_amount', 'sum'),
    平均报销率=('reimburse_rate', 'mean')
).round(4).nlargest(10, '就诊人次')
print("\n【主题11】科室排名TOP10:")
print(a11.to_string())
analysis_results['主题11_科室排名'] = a11

# 保存分析结果
for name, df_result in analysis_results.items():
    filepath = os.path.join(OUTPUT_DIR, 'analysis', f'{name}.csv')
    df_result.to_csv(filepath, encoding='utf-8-sig')
    print(f"\n  💾 已保存: {name}.csv")

print("\n" + "=" * 60)
print("  ✅ 全流程完成！")
print(f"  ODS层: {os.path.join(OUTPUT_DIR, 'ods')}/")
print(f"  DWD层: {os.path.join(OUTPUT_DIR, 'dwd')}/")
print(f"  DM层:  {os.path.join(OUTPUT_DIR, 'dm')}/")
print(f"  分析结果: {os.path.join(OUTPUT_DIR, 'analysis')}/")
print("=" * 60)
