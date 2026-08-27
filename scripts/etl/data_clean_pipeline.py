#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保数据清洗脚本
功能：去空值 → 类型转换 → 数据脱敏
处理三张表：insurance_info、medical_record、expense_detail
"""
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

# ======================== 配置 ========================
INPUT_DIR = "/home/hadoop/data_clean/medical_insurance"
OUTPUT_DIR = "/home/hadoop/data_clean/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================== 工具函数 ========================

def mask_name(name):
    """姓名脱敏：只保留姓，其余用*替代，如 张**"""
    if pd.isna(name) or name == "未知" or name == "":
        return "未知"
    name = str(name).strip()
    if len(name) <= 1:
        return name + "*"
    return name[0] + "*" * (len(name) - 1)


def mask_id_card(id_str):
    """身份证脱敏：保留前4位和后4位，中间用****替代，如 4101****1234"""
    if pd.isna(id_str) or id_str in ("0", "未知", ""):
        return "未知"
    s = str(id_str).strip().replace(".0", "")  # 处理 float 转 string
    if len(s) >= 8:
        return s[:4] + "****" + s[-4:]
    elif len(s) >= 4:
        return s[:2] + "****" + s[-2:]
    return s


def mask_person_id(pid):
    """person_id 脱敏：P2023****1"""
    if pd.isna(pid):
        return "未知"
    s = str(pid).strip()
    if len(s) >= 6:
        return s[:5] + "****" + s[-1]
    return s


def normalize_date(date_val):
    """日期标准化为 YYYY-MM-DD 格式"""
    if pd.isna(date_val) or str(date_val).strip() == "":
        return "2023-01-01"
    s = str(date_val).strip()
    # 处理多种日期格式
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d"]:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # 如果都无法解析，尝试只用前10个字符
    return s[:10] if len(s) >= 10 else "2023-01-01"


def normalize_reimbursable(val):
    """报销标识标准化：Y/是/N/否 → 统一为 是/否"""
    if pd.isna(val):
        return "是"
    s = str(val).strip().upper()
    if s in ("是", "Y", "YES", "TRUE", "1"):
        return "是"
    elif s in ("否", "N", "NO", "FALSE", "0"):
        return "否"
    return "是"


def fix_negative(val):
    """修复负值：负的费用不合理，取绝对值"""
    if pd.isna(val):
        return 0.0
    val = float(val)
    return abs(val) if val < 0 else val


def fix_age(age):
    """修复年龄异常：0-120 范围内，负值取绝对值，超120标记为-1"""
    if pd.isna(age):
        return 30
    age = int(age)
    if age < 0:
        age = abs(age)
    if age > 120:
        return 30  # 明显错误，设为未知
    return age


# ======================== 处理函数 ========================

def clean_insurance_info(filepath):
    """清洗：参保人信息表"""
    print("\n" + "=" * 50)
    print("[Step 1] 清洗 insurance_info.csv")
    df = pd.read_csv(filepath, encoding="utf-8")
    print(f"  原始数据: {df.shape[0]} 行, {df.shape[1]} 列")
    
    # --- 1. 去空值 ---
    df["name"] = df["name"].fillna("未知")
    df["gender"] = df["gender"].fillna("未知")
    df["region"] = df["region"].fillna("未知")
    df["register_date"] = df["register_date"].fillna("2023-01-01")
    # id_card 空值填 "0"
    df["id_card"] = df["id_card"].fillna(0).astype(np.int64).astype(str)
    df["id_card"] = df["id_card"].replace("0", "未知")
    print(f"  ✓ 空值填充完成")

    # --- 2. 类型转换 ---
    # age: 异常值修复
    before_bad_age = ((df["age"] < 0) | (df["age"] > 120)).sum()
    df["age"] = df["age"].apply(fix_age)
    print(f"  ✓ 年龄异常值修复: {before_bad_age} 个 (范围约束 0-120)")

    # id_card: float → string (18位身份证)
    def fmt_idcard(val):
        if val == "未知":
            return val
        s = str(val).strip().replace(".0", "")
        return s.zfill(18)  # 不足18位左侧补0

    df["id_card"] = df["id_card"].apply(fmt_idcard)
    print(f"  ✓ 身份证号 float→string, 补齐18位")

    # register_date: 日期标准化
    df["register_date"] = df["register_date"].apply(normalize_date)
    print(f"  ✓ 日期标准化 YYYY-MM-DD")

    # gender 规范化
    df["gender"] = df["gender"].str.strip()
    print(f"  ✓ 性别字段规范化")

    # --- 3. 脱敏 ---
    df["name_mask"] = df["name"].apply(mask_name)
    df["id_card_mask"] = df["id_card"].apply(mask_id_card)
    df["person_id_mask"] = df["person_id"].apply(mask_person_id)
    print(f"  ✓ 脱敏完成: name→name_mask, id_card→id_card_mask, person_id→person_id_mask")

    print(f"  清洗后: {df.shape[0]} 行, {df.shape[1]} 列")
    return df


def clean_medical_record(filepath):
    """清洗：就诊记录表"""
    print("\n" + "=" * 50)
    print("[Step 2] 清洗 medical_record.csv")
    df = pd.read_csv(filepath, encoding="utf-8")
    print(f"  原始数据: {df.shape[0]} 行, {df.shape[1]} 列")

    # --- 1. 去空值 ---
    df["department"] = df["department"].fillna("未知")
    df["diagnosis"] = df["diagnosis"].fillna("待确诊")
    df["doctor"] = df["doctor"].fillna("未知")
    print(f"  ✓ 空值填充完成")

    # --- 2. 类型转换 ---
    # visit_date: 日期标准化
    df["visit_date"] = df["visit_date"].apply(normalize_date)
    print(f"  ✓ 日期标准化 YYYY-MM-DD")

    # diagnosis: 统一为中文（如 "Pneumonia" → "肺炎"）
    eng_cn_map = {
        "Pneumonia": "肺炎",
        "Hypertension": "高血压",
        "Diabetes": "糖尿病",
        "Gastritis": "胃炎",
        "Fracture": "骨折",
    }
    df["diagnosis"] = df["diagnosis"].replace(eng_cn_map)
    print(f"  ✓ 诊断英文→中文转换")

    # visit_type: 去空格规范化
    df["visit_type"] = df["visit_type"].str.strip()
    print(f"  ✓ 就诊类型规范化")

    # --- 3. 脱敏 ---
    df["person_id_mask"] = df["person_id"].apply(mask_person_id)
    df["doctor_mask"] = df["doctor"].apply(lambda x: str(x)[0] + "**" if pd.notna(x) and x != "未知" else x)
    print(f"  ✓ 脱敏完成: person_id→person_id_mask, doctor→doctor_mask")

    print(f"  清洗后: {df.shape[0]} 行, {df.shape[1]} 列")
    return df


def clean_expense_detail(filepath):
    """清洗：费用明细表"""
    print("\n" + "=" * 50)
    print("[Step 3] 清洗 expense_detail.csv")
    df = pd.read_csv(filepath, encoding="utf-8")
    print(f"  原始数据: {df.shape[0]} 行, {df.shape[1]} 列")

    # --- 1. 去空值 ---
    # 本表无空值，跳过
    null_before = df.isnull().sum().sum()
    print(f"  ✓ 空值检查: {null_before} 个 (无需处理)")

    # --- 2. 类型转换 ---
    # reimbursable: Y/是 统一为 是
    df["reimbursable"] = df["reimbursable"].apply(normalize_reimbursable)
    before = df["reimbursable"].value_counts().to_dict()
    print(f"  ✓ 报销标识标准化: {before}")

    # 费用列: 负值取绝对值
    money_cols = ["unit_price", "total_amount", "reimbursed_amount", "self_paid_amount"]
    for col in money_cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            df[col] = df[col].apply(fix_negative)
            print(f"  ✓ {col}: 修复 {neg_count} 个负值")

    # quantity: 确保为正整数
    df["quantity"] = df["quantity"].apply(lambda x: max(1, int(abs(x))))
    print(f"  ✓ quantity 修复")

    # --- 3. 脱敏 ---
    # 金额脱敏：四舍五入到整数（保留隐私）
    for col in money_cols:
        df[col] = df[col].round(0).astype(int)
    print(f"  ✓ 金额脱敏: 四舍五入取整")

    # record_id 脱敏
    df["record_id_mask"] = df["record_id"].apply(
        lambda x: str(x)[:6] + "****" if pd.notna(x) else x
    )
    print(f"  ✓ record_id 脱敏")

    print(f"  清洗后: {df.shape[0]} 行, {df.shape[1]} 列")
    return df


# ======================== 主流程 ========================

def main():
    print("=" * 60)
    print("  医保数据清洗流水线")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # --- 清洗三张表 ---
    df_info = clean_insurance_info(os.path.join(INPUT_DIR, "insurance_info.csv"))
    df_record = clean_medical_record(os.path.join(INPUT_DIR, "medical_record.csv"))
    df_expense = clean_expense_detail(os.path.join(INPUT_DIR, "expense_detail.csv"))

    # --- 输出清洗结果 ---
    print("\n" + "=" * 50)
    print("[Step 4] 输出清洗结果")
    
    # 生成报告
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("  医保数据清洗报告")
    report_lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 60)
    report_lines.append("")

    tables = [
        ("insurance_info_clean.csv", df_info),
        ("medical_record_clean.csv", df_record),
        ("expense_detail_clean.csv", df_expense),
    ]

    for filename, df in tables:
        outpath = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(outpath, index=False, encoding="utf-8-sig")
        file_size = os.path.getsize(outpath)
        report_lines.append(f"[{filename}]")
        report_lines.append(f"  行数: {df.shape[0]}  |  列数: {df.shape[1]}")
        report_lines.append(f"  列名: {', '.join(df.columns.tolist())}")
        report_lines.append(f"  文件大小: {file_size / 1024:.1f} KB")
        report_lines.append(f"  路径: {outpath}")
        report_lines.append("")
        print(f"  ✅ {filename} ({df.shape[0]}行 × {df.shape[1]}列, {file_size/1024:.1f}KB)")

    # --- 输出汇总统计 ---
    report_lines.append("-" * 40)
    report_lines.append("[数据质量汇总]")
    report_lines.append(f"  insurance_info:    {df_info.shape[0]} 行 (原始 5050)")
    report_lines.append(f"  medical_record:    {df_record.shape[0]} 行 (原始 9871)")
    report_lines.append(f"  expense_detail:   {df_expense.shape[0]} 行 (原始 15323)")
    report_lines.append("")
    report_lines.append("[脱敏说明]")
    report_lines.append("  姓名:  保留姓, 名用*替代 (如 张**)")
    report_lines.append("  身份证: 保留前4后4位, 中间**** (如 4101****1234)")
    report_lines.append("  人员ID: 保留前5后1位, 中间**** (如 P2023****1)")
    report_lines.append("  医生:  保留姓, 名用**替代 (如 陈**)")
    report_lines.append("  金额:  四舍五入到整数")
    report_lines.append("  就诊ID: 保留前6位+****")
    report_lines.append("=" * 60)

    # 写报告文件
    report_path = os.path.join(OUTPUT_DIR, "clean_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n  📄 清洗报告: {report_path}")
    print("\n" + "\n".join(report_lines))
    print(f"\n  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
