#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肿瘤面积分析
功能：分析肿瘤目标面积分布
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
# 1. 检测肿瘤并计算面积
# ============================================================
def detect_tumor_area(img):
    """检测肿瘤并计算面积"""
    # 转灰度图
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # 阈值分割
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    
    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # 找到最大轮廓（假设是肿瘤）
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        return area, largest_contour
    
    return 0, None

# ============================================================
# 2. 收集肿瘤面积数据
# ============================================================
def collect_tumor_areas(data_dir='data'):
    """收集所有肿瘤的面积信息"""
    print("=" * 60)
    print("1. 收集肿瘤面积数据")
    print("=" * 60)
    
    area_data = defaultdict(list)
    
    for cat in os.listdir(data_dir):
        cat_dir = os.path.join(data_dir, cat)
        if os.path.isdir(cat_dir):
            for img_name in os.listdir(cat_dir):
                img_path = os.path.join(cat_dir, img_name)
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    total_pixels = h * w
                    area, contour = detect_tumor_area(img)
                    if area > 0:
                        # 计算相对面积（占图像总面积的比例）
                        relative_area = area / total_pixels
                        area_data[cat].append({
                            'area': area,
                            'relative_area': relative_area,
                            'total_pixels': total_pixels
                        })
    
    # 打印统计信息
    for cat, areas in area_data.items():
        relative_areas = [a['relative_area'] for a in areas]
        print(f"\n  {cat}: {len(areas)} 张图像")
        print(f"    相对面积范围: {min(relative_areas):.4f} - {max(relative_areas):.4f}")
        print(f"    平均相对面积: {np.mean(relative_areas):.4f}")
        print(f"    面积标准差: {np.std(relative_areas):.4f}")
    
    return dict(area_data)

# ============================================================
# 3. 绘制面积分布直方图
# ============================================================
def plot_area_histogram(area_data, output_file='area_histogram.png'):
    """绘制面积分布直方图"""
    print("\n" + "=" * 60)
    print("2. 绘制面积分布直方图")
    print("=" * 60)
    
    # 收集所有相对面积
    all_relative_areas = []
    for areas in area_data.values():
        all_relative_areas.extend([a['relative_area'] for a in areas])
    
    plt.figure(figsize=(10, 6))
    
    plt.hist(all_relative_areas, bins=20, color='#96CEB4', edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(all_relative_areas), color='red', linestyle='--',
                label=f'平均值: {np.mean(all_relative_areas):.4f}')
    
    plt.xlabel('肿瘤相对面积', fontsize=14)
    plt.ylabel('频数', fontsize=14)
    plt.title('肿瘤面积分布直方图', fontsize=16, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 4. 绘制各类别面积对比
# ============================================================
def plot_category_area_comparison(area_data, output_file='category_area_comparison.png'):
    """绘制各类别面积对比"""
    print("\n" + "=" * 60)
    print("3. 绘制各类别面积对比")
    print("=" * 60)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    
    categories = list(area_data.keys())
    cn_categories = [cn_names.get(c, c) for c in categories]
    
    # 计算各类别平均相对面积
    avg_areas = []
    std_areas = []
    for cat in categories:
        areas = area_data[cat]
        relative_areas = [a['relative_area'] for a in areas]
        avg_areas.append(np.mean(relative_areas))
        std_areas.append(np.std(relative_areas))
    
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(categories))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    bars = plt.bar(x, avg_areas, yerr=std_areas, capsize=5,
                   color=colors, edgecolor='black', linewidth=1.5)
    
    # 添加数值标签
    for bar, avg, std in zip(bars, avg_areas, std_areas):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{avg:.4f}\n±{std:.4f}',
                ha='center', va='bottom', fontsize=10)
    
    plt.xlabel('肿瘤类别', fontsize=14)
    plt.ylabel('平均相对面积', fontsize=14)
    plt.title('各类别肿瘤面积对比', fontsize=16, fontweight='bold')
    plt.xticks(x, cn_categories)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 5. 绘制面积箱线图
# ============================================================
def plot_area_boxplot(area_data, output_file='area_boxplot.png'):
    """绘制面积箱线图"""
    print("\n" + "=" * 60)
    print("4. 绘制面积箱线图")
    print("=" * 60)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    
    categories = list(area_data.keys())
    cn_categories = [cn_names.get(c, c) for c in categories]
    
    # 收集各类别相对面积
    data_to_plot = []
    for cat in categories:
        areas = area_data[cat]
        relative_areas = [a['relative_area'] for a in areas]
        data_to_plot.append(relative_areas)
    
    plt.figure(figsize=(10, 6))
    
    bp = plt.boxplot(data_to_plot, patch_artist=True)
    plt.xticks(range(1, len(cn_categories) + 1), cn_categories)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.xlabel('肿瘤类别', fontsize=14)
    plt.ylabel('相对面积', fontsize=14)
    plt.title('各类别肿瘤面积分布箱线图', fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  肿瘤面积分析")
    print("=" * 60)
    
    # 检查数据目录（复用脑肿瘤原始数据集：models/brain_tumor_detection/data/raw/Training）
    data_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..',
        'models', 'brain_tumor_detection', 'data', 'raw', 'Training'))
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在，请先运行 opencv_basics.py 生成示例数据")
        exit(1)
    
    # 收集面积数据
    area_data = collect_tumor_areas(data_dir)
    
    # 绘制面积分布直方图
    plot_area_histogram(area_data)
    
    # 绘制各类别面积对比
    plot_category_area_comparison(area_data)
    
    # 绘制面积箱线图
    plot_area_boxplot(area_data)
    
    print("\n" + "=" * 60)
    print("  分析完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - area_histogram.png (面积分布直方图)")
    print("  - category_area_comparison.png (各类别面积对比)")
    print("  - area_boxplot.png (面积箱线图)")
