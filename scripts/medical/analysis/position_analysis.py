#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肿瘤位置分析
功能：分析肿瘤目标位置分布
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
# 1. 检测肿瘤位置
# ============================================================
def detect_tumor_position(img):
    """检测肿瘤位置（简化版：使用阈值分割）"""
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
        
        # 计算中心点
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return cx, cy, largest_contour
    
    return None, None, None

# ============================================================
# 2. 收集肿瘤位置数据
# ============================================================
def collect_tumor_positions(data_dir='data'):
    """收集所有肿瘤的位罝信息"""
    print("=" * 60)
    print("1. 收集肿瘤位置数据")
    print("=" * 60)
    
    position_data = defaultdict(list)
    
    for cat in os.listdir(data_dir):
        cat_dir = os.path.join(data_dir, cat)
        if os.path.isdir(cat_dir):
            for img_name in os.listdir(cat_dir):
                img_path = os.path.join(cat_dir, img_name)
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    cx, cy, contour = detect_tumor_position(img)
                    if cx is not None:
                        # 归一化坐标到 [0, 1]
                        norm_x = cx / w
                        norm_y = cy / h
                        position_data[cat].append({
                            'x': cx, 'y': cy,
                            'norm_x': norm_x, 'norm_y': norm_y,
                            'width': w, 'height': h,
                            'contour': contour
                        })
    
    # 打印统计信息
    for cat, positions in position_data.items():
        print(f"\n  {cat}: {len(positions)} 张图像")
        if positions:
            norm_xs = [p['norm_x'] for p in positions]
            norm_ys = [p['norm_y'] for p in positions]
            print(f"    中心X范围: {min(norm_xs):.2f} - {max(norm_xs):.2f}")
            print(f"    中心Y范围: {min(norm_ys):.2f} - {max(norm_ys):.2f}")
    
    return dict(position_data)

# ============================================================
# 3. 绘制位置分布散点图
# ============================================================
def plot_position_scatter(position_data, output_file='position_scatter.png'):
    """绘制肿瘤位置分布散点图"""
    print("\n" + "=" * 60)
    print("2. 绘制位置分布散点图")
    print("=" * 60)
    
    plt.figure(figsize=(10, 8))
    
    colors = {'glioma': '#FF6B6B', 'meningioma': '#4ECDC4', 'pituitary': '#45B7D1'}
    cn_names = {'glioma': '胶质瘤', 'meningioma': '脑膜瘤', 'pituitary': '垂体瘤'}
    
    for cat, positions in position_data.items():
        norm_xs = [p['norm_x'] for p in positions]
        norm_ys = [p['norm_y'] for p in positions]
        plt.scatter(norm_xs, norm_ys, c=colors.get(cat, 'gray'),
                   label=cn_names.get(cat, cat), alpha=0.6, s=50)
    
    plt.xlabel('归一化X坐标', fontsize=14)
    plt.ylabel('归一化Y坐标', fontsize=14)
    plt.title('肿瘤位置分布散点图', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(alpha=0.3)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.gca().invert_yaxis()  # Y轴反转，使原点在左上角
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 4. 绘制位置热力图
# ============================================================
def plot_position_heatmap(position_data, output_file='position_heatmap.png'):
    """绘制肿瘤位置热力图"""
    print("\n" + "=" * 60)
    print("3. 绘制位置热力图")
    print("=" * 60)
    
    # 收集所有位置
    all_positions = []
    for positions in position_data.values():
        all_positions.extend([(p['norm_x'], p['norm_y']) for p in positions])
    
    if not all_positions:
        print("没有位置数据")
        return
    
    xs = [p[0] for p in all_positions]
    ys = [p[1] for p in all_positions]
    
    plt.figure(figsize=(10, 8))
    
    # 绘制热力图
    plt.hist2d(xs, ys, bins=20, cmap='hot_r', range=[[0, 1], [0, 1]])
    plt.colorbar(label='肿瘤数量')
    
    plt.xlabel('归一化X坐标', fontsize=14)
    plt.ylabel('归一化Y坐标', fontsize=14)
    plt.title('肿瘤位置热力图', fontsize=16, fontweight='bold')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 5. 绘制9宫格位置分布
# ============================================================
def plot_grid_distribution(position_data, output_file='grid_distribution.png'):
    """绘制9宫格位置分布"""
    print("\n" + "=" * 60)
    print("4. 绘制9宫格位置分布")
    print("=" * 60)
    
    # 收集所有位置
    all_positions = []
    for positions in position_data.values():
        all_positions.extend([(p['norm_x'], p['norm_y']) for p in positions])
    
    if not all_positions:
        print("没有位置数据")
        return
    
    # 统计9宫格分布
    grid_counts = np.zeros((3, 3), dtype=int)
    for x, y in all_positions:
        col = min(int(x * 3), 2)
        row = min(int(y * 3), 2)
        grid_counts[row, col] += 1
    
    print("\n  9宫格分布:")
    for i in range(3):
        row_str = "    "
        for j in range(3):
            row_str += f"{grid_counts[i, j]:3d} "
        print(row_str)
    
    plt.figure(figsize=(10, 8))
    
    # 绘制热力图
    im = plt.imshow(grid_counts, cmap='YlOrRd', aspect='equal')
    plt.colorbar(label='肿瘤数量')
    
    # 添加数值标注
    for i in range(3):
        for j in range(3):
            plt.text(j, i, str(grid_counts[i, j]),
                    ha='center', va='center', fontsize=20, fontweight='bold',
                    color='white' if grid_counts[i, j] > grid_counts.max()/2 else 'black')
    
    # 设置标签
    plt.xticks([0, 1, 2], ['左', '中', '右'], fontsize=14)
    plt.yticks([0, 1, 2], ['上', '中', '下'], fontsize=14)
    plt.title('肿瘤位置9宫格分布', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 已保存: {output_file}")
    plt.close()

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  肿瘤位置分析")
    print("=" * 60)
    
    # 检查数据目录（复用脑肿瘤原始数据集：models/brain_tumor_detection/data/raw/Training）
    data_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..',
        'models', 'brain_tumor_detection', 'data', 'raw', 'Training'))
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在，请先运行 opencv_basics.py 生成示例数据")
        exit(1)
    
    # 收集位置数据
    position_data = collect_tumor_positions(data_dir)
    
    # 绘制位置分布散点图
    plot_position_scatter(position_data)
    
    # 绘制位置热力图
    plot_position_heatmap(position_data)
    
    # 绘制9宫格分布
    plot_grid_distribution(position_data)
    
    print("\n" + "=" * 60)
    print("  分析完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - position_scatter.png (位置分布散点图)")
    print("  - position_heatmap.png (位置热力图)")
    print("  - grid_distribution.png (9宫格分布)")
