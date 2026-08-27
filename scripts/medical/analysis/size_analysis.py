#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脑肿瘤图像尺寸分析
功能：分析脑肿瘤图像的尺寸分布
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import defaultdict

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 收集图像尺寸信息
# ============================================================
def collect_image_sizes(data_dir='data'):
    """收集所有图像的尺寸信息"""
    print("=" * 60)
    print("1. 收集图像尺寸信息")
    print("=" * 60)
    
    size_data = defaultdict(list)
    
    for cat in os.listdir(data_dir):
        cat_dir = os.path.join(data_dir, cat)
        if os.path.isdir(cat_dir):
            for img_name in os.listdir(cat_dir):
                img_path = os.path.join(cat_dir, img_name)
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    size_data[cat].append((w, h))
    
    # 打印统计信息
    for cat, sizes in size_data.items():
        widths = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        print(f"\n  {cat}:")
        print(f"    数量: {len(sizes)}")
        print(f"    宽度范围: {min(widths)} - {max(widths)}")
        print(f"    高度范围: {min(heights)} - {max(heights)}")
        print(f"    平均宽度: {np.mean(widths):.1f}")
        print(f"    平均高度: {np.mean(heights):.1f}")
    
    return dict(size_data)

# ============================================================
# 2. 绘制尺寸分布直方图
# ============================================================
def plot_size_histogram(size_data, output_file='size_histogram.png'):
    """绘制尺寸分布直方图"""
    print("\n" + "=" * 60)
    print("2. 绘制尺寸分布直方图")
    print("=" * 60)
    
    # 收集所有尺寸
    all_widths = []
    all_heights = []
    for sizes in size_data.values():
        all_widths.extend([s[0] for s in sizes])
        all_heights.extend([s[1] for s in sizes])
    
    plt.figure(figsize=(12, 5))
    
    # 宽度分布
    plt.subplot(1, 2, 1)
    plt.hist(all_widths, bins=20, color='#4ECDC4', edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(all_widths), color='red', linestyle='--', 
                label=f'平均值: {np.mean(all_widths):.1f}')
    plt.xlabel('宽度 (像素)', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    plt.title('图像宽度分布', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # 高度分布
    plt.subplot(1, 2, 2)
    plt.hist(all_heights, bins=20, color='#FF6B6B', edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(all_heights), color='red', linestyle='--',
                label=f'平均值: {np.mean(all_heights):.1f}')
    plt.xlabel('高度 (像素)', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    plt.title('图像高度分布', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 3. 绘制各类别尺寸对比
# ============================================================
def plot_category_size_comparison(size_data, output_file='category_size_comparison.png'):
    """绘制各类别尺寸对比"""
    print("\n" + "=" * 60)
    print("3. 绘制各类别尺寸对比")
    print("=" * 60)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    
    categories = list(size_data.keys())
    cn_categories = [cn_names.get(c, c) for c in categories]
    
    # 计算各类别平均尺寸
    avg_widths = []
    avg_heights = []
    for cat in categories:
        sizes = size_data[cat]
        avg_widths.append(np.mean([s[0] for s in sizes]))
        avg_heights.append(np.mean([s[1] for s in sizes]))
    
    plt.figure(figsize=(12, 5))
    
    x = np.arange(len(categories))
    width = 0.35
    
    # 平均宽度
    plt.subplot(1, 2, 1)
    bars1 = plt.bar(x, avg_widths, width, label='平均宽度', color='#4ECDC4', edgecolor='black')
    plt.xlabel('肿瘤类别', fontsize=12)
    plt.ylabel('平均宽度 (像素)', fontsize=12)
    plt.title('各类别平均宽度对比', fontsize=14, fontweight='bold')
    plt.xticks(x, cn_categories)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}', ha='center', va='bottom', fontsize=10)
    
    # 平均高度
    plt.subplot(1, 2, 2)
    bars2 = plt.bar(x, avg_heights, width, label='平均高度', color='#FF6B6B', edgecolor='black')
    plt.xlabel('肿瘤类别', fontsize=12)
    plt.ylabel('平均高度 (像素)', fontsize=12)
    plt.title('各类别平均高度对比', fontsize=14, fontweight='bold')
    plt.xticks(x, cn_categories)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bar in bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 4. 绘制尺寸散点图
# ============================================================
def plot_size_scatter(size_data, output_file='size_scatter.png'):
    """绘制尺寸散点图"""
    print("\n" + "=" * 60)
    print("4. 绘制尺寸散点图")
    print("=" * 60)
    
    plt.figure(figsize=(10, 8))
    
    colors = {'glioma': '#FF6B6B', 'meningioma': '#4ECDC4', 'pituitary': '#45B7D1'}
    cn_names = {'glioma': '胶质瘤', 'meningioma': '脑膜瘤', 'pituitary': '垂体瘤'}
    
    for cat, sizes in size_data.items():
        widths = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        plt.scatter(widths, heights, c=colors.get(cat, 'gray'), 
                   label=cn_names.get(cat, cat), alpha=0.6, s=50)
    
    plt.xlabel('宽度 (像素)', fontsize=14)
    plt.ylabel('高度 (像素)', fontsize=14)
    plt.title('图像尺寸分布散点图', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  脑肿瘤图像尺寸分析")
    print("=" * 60)
    
    # 检查数据目录（复用脑肿瘤原始数据集：models/brain_tumor_detection/data/raw/Training）
    data_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..',
        'models', 'brain_tumor_detection', 'data', 'raw', 'Training'))
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在，请先运行 opencv_basics.py 生成示例数据")
        exit(1)
    
    # 收集尺寸信息
    size_data = collect_image_sizes(data_dir)
    
    # 绘制尺寸分布直方图
    plot_size_histogram(size_data)
    
    # 绘制各类别尺寸对比
    plot_category_size_comparison(size_data)
    
    # 绘制尺寸散点图
    plot_size_scatter(size_data)
    
    print("\n" + "=" * 60)
    print("  分析完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - size_histogram.png (尺寸分布直方图)")
    print("  - category_size_comparison.png (各类别尺寸对比)")
    print("  - size_scatter.png (尺寸散点图)")
