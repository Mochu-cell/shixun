#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脑肿瘤图像类别分布分析
功能：统计脑肿瘤图像类别分布，绘制柱状图和饼图
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 类别分布统计
# ============================================================
def count_categories(data_dir='data'):
    """统计各类别图像数量"""
    print("=" * 60)
    print("1. 类别分布统计")
    print("=" * 60)
    
    categories = []
    
    for cat in os.listdir(data_dir):
        cat_dir = os.path.join(data_dir, cat)
        if os.path.isdir(cat_dir):
            count = len([f for f in os.listdir(cat_dir) if f.endswith(('.jpg', '.png'))])
            categories.append((cat, count))
            print(f"  {cat}: {count} 张")
    
    return dict(categories)

# ============================================================
# 2. 绘制类别分布柱状图
# ============================================================
def plot_category_bar(category_counts, output_file='category_bar.png'):
    """绘制类别分布柱状图"""
    print("\n" + "=" * 60)
    print("2. 绘制类别分布柱状图")
    print("=" * 60)
    
    categories = list(category_counts.keys())
    counts = list(category_counts.values())
    total = sum(counts)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    cn_categories = [cn_names.get(c, c) for c in categories]
    
    plt.figure(figsize=(10, 6))
    
    # 绘制柱状图
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = plt.bar(cn_categories, counts, color=colors, edgecolor='black', linewidth=1.5)
    
    # 添加数值标签
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}\n({count/total*100:.1f}%)',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.xlabel('肿瘤类别', fontsize=14)
    plt.ylabel('图像数量', fontsize=14)
    plt.title(f'脑肿瘤图像类别分布\n总计: {total} 张', fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 3. 绘制类别分布饼图
# ============================================================
def plot_category_pie(category_counts, output_file='category_pie.png'):
    """绘制类别分布饼图"""
    print("\n" + "=" * 60)
    print("3. 绘制类别分布饼图")
    print("=" * 60)
    
    categories = list(category_counts.keys())
    counts = list(category_counts.values())
    total = sum(counts)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    cn_categories = [cn_names.get(c, c) for c in categories]
    
    plt.figure(figsize=(10, 8))
    
    # 绘制饼图
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    explode = [0.05] * len(categories)
    
    wedges, texts, autotexts = plt.pie(
        counts,
        labels=cn_categories,
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100.*total)}张)',
        startangle=90,
        colors=colors,
        explode=explode,
        shadow=True,
        textprops={'fontsize': 12}
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.title('脑肿瘤图像类别占比', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 4. 类别不平衡分析
# ============================================================
def analyze_imbalance(category_counts):
    """分析类别不平衡情况"""
    print("\n" + "=" * 60)
    print("4. 类别不平衡分析")
    print("=" * 60)
    
    counts = list(category_counts.values())
    max_count = max(counts)
    min_count = min(counts)
    
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    
    print(f"  最大类别数量: {max_count}")
    print(f"  最小类别数量: {min_count}")
    print(f"  不平衡比例: {imbalance_ratio:.2f}:1")
    
    if imbalance_ratio > 2:
        print("  ⚠️ 存在类别不平衡，建议采用以下策略:")
        print("     - 数据增强 (Data Augmentation)")
        print("     - 过采样 (Oversampling)")
        print("     - 欠采样 (Undersampling)")
        print("     - 类别权重 (Class Weight)")
    else:
        print("  ✅ 类别分布相对均衡")

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  脑肿瘤图像类别分布分析")
    print("=" * 60)
    
    # 检查数据目录（复用脑肿瘤原始数据集：models/brain_tumor_detection/data/raw/Training）
    data_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..',
        'models', 'brain_tumor_detection', 'data', 'raw', 'Training'))
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在，请先运行 opencv_basics.py 生成示例数据")
        exit(1)
    
    # 统计类别分布
    category_counts = count_categories(data_dir)
    
    # 绘制柱状图
    plot_category_bar(category_counts)
    
    # 绘制饼图
    plot_category_pie(category_counts)
    
    # 分析不平衡
    analyze_imbalance(category_counts)
    
    print("\n" + "=" * 60)
    print("  分析完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - category_bar.png (类别分布柱状图)")
    print("  - category_pie.png (类别分布饼图)")
