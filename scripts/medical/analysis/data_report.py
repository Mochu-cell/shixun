#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脑肿瘤影像数据分析报告
功能：生成Markdown和HTML格式的数据分析报告
"""

import cv2
import numpy as np
import os
from collections import defaultdict
from datetime import datetime

# ============================================================
# 1. 收集所有统计数据
# ============================================================
def collect_all_stats(data_dir='data'):
    """收集所有统计数据"""
    print("=" * 60)
    print("1. 收集所有统计数据")
    print("=" * 60)
    
    # 类别分布
    category_counts = defaultdict(int)
    # 尺寸数据
    size_data = defaultdict(list)
    # 位置数据
    position_data = defaultdict(list)
    # 面积数据
    area_data = defaultdict(list)
    
    for cat in os.listdir(data_dir):
        cat_dir = os.path.join(data_dir, cat)
        if os.path.isdir(cat_dir):
            for img_name in os.listdir(cat_dir):
                img_path = os.path.join(cat_dir, img_name)
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    category_counts[cat] += 1
                    size_data[cat].append((w, h))
                    
                    # 检测肿瘤位置
                    if len(img.shape) == 3:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = img
                    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
                    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        largest_contour = max(contours, key=cv2.contourArea)
                        M = cv2.moments(largest_contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            position_data[cat].append({
                                'norm_x': cx / w,
                                'norm_y': cy / h
                            })
                            area = cv2.contourArea(largest_contour)
                            area_data[cat].append(area / (h * w))
    
    total_images = sum(category_counts.values())
    print(f"  总图像数: {total_images}")
    print(f"  类别数: {len(category_counts)}")
    
    return {
        'category_counts': dict(category_counts),
        'size_data': dict(size_data),
        'position_data': dict(position_data),
        'area_data': dict(area_data),
        'total_images': total_images
    }

# ============================================================
# 2. 生成Markdown报告
# ============================================================
def generate_markdown_report(stats, output_file='data_analysis_report.txt'):
    """生成Markdown格式的数据分析报告"""
    print("\n" + "=" * 60)
    print("2. 生成Markdown报告")
    print("=" * 60)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    
    report = []
    report.append("# 脑肿瘤影像数据分析报告")
    report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n" + "=" * 50)
    
    # 1. 数据概览
    report.append("\n## 1. 数据概览")
    report.append(f"\n- **总图像数量**: {stats['total_images']} 张")
    report.append(f"- **类别数量**: {len(stats['category_counts'])} 类")
    report.append("\n### 各类别数量分布")
    report.append("\n| 类别 | 英文名称 | 数量 | 占比 |")
    report.append("|------|----------|------|------|")
    for cat, count in stats['category_counts'].items():
        cn_name = cn_names.get(cat, cat)
        percentage = count / stats['total_images'] * 100
        report.append(f"| {cn_name} | {cat} | {count} | {percentage:.1f}% |")
    
    # 2. 图像尺寸分析
    report.append("\n## 2. 图像尺寸分析")
    all_widths = []
    all_heights = []
    for sizes in stats['size_data'].values():
        all_widths.extend([s[0] for s in sizes])
        all_heights.extend([s[1] for s in sizes])
    
    report.append(f"\n- **宽度范围**: {min(all_widths)} - {max(all_widths)} 像素")
    report.append(f"- **高度范围**: {min(all_heights)} - {max(all_heights)} 像素")
    report.append(f"- **平均宽度**: {np.mean(all_widths):.1f} 像素")
    report.append(f"- **平均高度**: {np.mean(all_heights):.1f} 像素")
    
    # 3. 肿瘤位置分析
    report.append("\n## 3. 肿瘤位置分析")
    all_positions = []
    for positions in stats['position_data'].values():
        all_positions.extend([(p['norm_x'], p['norm_y']) for p in positions])
    
    if all_positions:
        xs = [p[0] for p in all_positions]
        ys = [p[1] for p in all_positions]
        report.append(f"\n- **肿瘤中心X范围**: {min(xs):.2f} - {max(xs):.2f}")
        report.append(f"- **肿瘤中心Y范围**: {min(ys):.2f} - {max(ys):.2f}")
        report.append(f"- **平均中心X**: {np.mean(xs):.2f}")
        report.append(f"- **平均中心Y**: {np.mean(ys):.2f}")
        
        # 9宫格分布
        grid_counts = np.zeros((3, 3), dtype=int)
        for x, y in all_positions:
            col = min(int(x * 3), 2)
            row = min(int(y * 3), 2)
            grid_counts[row, col] += 1
        
        report.append("\n### 9宫格位置分布")
        report.append("\n```\n      左    中    右")
        for i, row_name in enumerate(['上', '中', '下']):
            row_str = f"{row_name}  "
            for j in range(3):
                row_str += f"{grid_counts[i, j]:4d}"
            report.append(row_str)
        report.append("```")
    
    # 4. 肿瘤面积分析
    report.append("\n## 4. 肿瘤面积分析")
    all_areas = []
    for areas in stats['area_data'].values():
        all_areas.extend(areas)
    
    if all_areas:
        report.append(f"\n- **平均相对面积**: {np.mean(all_areas):.4f}")
        report.append(f"- **面积标准差**: {np.std(all_areas):.4f}")
        report.append(f"- **最小面积**: {min(all_areas):.4f}")
        report.append(f"- **最大面积**: {max(all_areas):.4f}")
        
        report.append("\n### 各类别平均面积")
        report.append("\n| 类别 | 平均相对面积 | 标准差 |")
        report.append("|------|--------------|--------|")
        for cat, areas in stats['area_data'].items():
            cn_name = cn_names.get(cat, cat)
            avg_area = np.mean(areas)
            std_area = np.std(areas)
            report.append(f"| {cn_name} | {avg_area:.4f} | {std_area:.4f} |")
    
    # 5. 结论与建议
    report.append("\n## 5. 结论与建议")
    report.append("\n### 主要发现")
    
    # 类别不平衡分析
    counts = list(stats['category_counts'].values())
    imbalance_ratio = max(counts) / min(counts) if min(counts) > 0 else 0
    if imbalance_ratio > 1.5:
        report.append(f"\n1. **类别不平衡**: 最大类别与最小类别的比例为 {imbalance_ratio:.2f}:1，建议进行数据增强")
    else:
        report.append(f"\n1. **类别平衡**: 各类别数量相对均衡（比例 {imbalance_ratio:.2f}:1）")
    
    # 位置分布
    if all_positions:
        xs = [p[0] for p in all_positions]
        ys = [p[1] for p in all_positions]
        report.append(f"\n2. **位置分布**: 肿瘤主要集中在图像中心区域（X={np.mean(xs):.2f}, Y={np.mean(ys):.2f}）")
    
    # 面积分布
    if all_areas:
        report.append(f"\n3. **面积分布**: 肿瘤平均相对面积为 {np.mean(all_areas):.4f}，存在一定变异（标准差 {np.std(all_areas):.4f}）")
    
    report.append("\n### 后续工作建议")
    report.append("\n1. 进行数据增强以平衡类别分布")
    report.append("2. 使用YOLO模型进行目标检测训练")
    report.append("3. 评估模型在不同类别上的检测性能")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 已保存: {output_file}")

# ============================================================
# 3. 生成HTML报告
# ============================================================
def generate_html_report(stats, output_file='data_analysis_report.html'):
    """生成HTML格式的数据分析报告"""
    print("\n" + "=" * 60)
    print("3. 生成HTML报告")
    print("=" * 60)
    
    # 中文类别名映射
    cn_names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤'
    }
    
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html lang='zh-CN'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <title>脑肿瘤影像数据分析报告</title>")
    html.append("    <style>")
    html.append("        body { font-family: 'Microsoft YaHei', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }")
    html.append("        h1 { color: #333; border-bottom: 2px solid #4ECDC4; padding-bottom: 10px; }")
    html.append("        h2 { color: #555; margin-top: 30px; }")
    html.append("        table { border-collapse: collapse; width: 100%; margin: 15px 0; }")
    html.append("        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }")
    html.append("        th { background-color: #4ECDC4; color: white; }")
    html.append("        tr:nth-child(even) { background-color: #f9f9f9; }")
    html.append("        .highlight { background-color: #FFE66D; padding: 10px; border-radius: 5px; margin: 10px 0; }")
    html.append("        code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }")
    html.append("    </style>")
    html.append("</head>")
    html.append("<body>")
    
    html.append(f"<h1>脑肿瘤影像数据分析报告</h1>")
    html.append(f"<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    
    # 1. 数据概览
    html.append("<h2>1. 数据概览</h2>")
    html.append(f"<p><strong>总图像数量</strong>: {stats['total_images']} 张</p>")
    html.append(f"<p><strong>类别数量</strong>: {len(stats['category_counts'])} 类</p>")
    
    html.append("<h3>各类别数量分布</h3>")
    html.append("<table>")
    html.append("    <tr><th>类别</th><th>英文名称</th><th>数量</th><th>占比</th></tr>")
    for cat, count in stats['category_counts'].items():
        cn_name = cn_names.get(cat, cat)
        percentage = count / stats['total_images'] * 100
        html.append(f"    <tr><td>{cn_name}</td><td>{cat}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>")
    html.append("</table>")
    
    # 2. 图像尺寸分析
    html.append("<h2>2. 图像尺寸分析</h2>")
    all_widths = []
    all_heights = []
    for sizes in stats['size_data'].values():
        all_widths.extend([s[0] for s in sizes])
        all_heights.extend([s[1] for s in sizes])
    
    html.append(f"<p><strong>宽度范围</strong>: {min(all_widths)} - {max(all_widths)} 像素</p>")
    html.append(f"<p><strong>高度范围</strong>: {min(all_heights)} - {max(all_heights)} 像素</p>")
    html.append(f"<p><strong>平均宽度</strong>: {np.mean(all_widths):.1f} 像素</p>")
    html.append(f"<p><strong>平均高度</strong>: {np.mean(all_heights):.1f} 像素</p>")
    
    # 3. 肿瘤面积分析
    html.append("<h2>3. 肿瘤面积分析</h2>")
    all_areas = []
    for areas in stats['area_data'].values():
        all_areas.extend(areas)
    
    if all_areas:
        html.append(f"<p><strong>平均相对面积</strong>: {np.mean(all_areas):.4f}</p>")
        html.append(f"<p><strong>面积标准差</strong>: {np.std(all_areas):.4f}</p>")
        
        html.append("<h3>各类别平均面积</h3>")
        html.append("<table>")
        html.append("    <tr><th>类别</th><th>平均相对面积</th><th>标准差</th></tr>")
        for cat, areas in stats['area_data'].items():
            cn_name = cn_names.get(cat, cat)
            avg_area = np.mean(areas)
            std_area = np.std(areas)
            html.append(f"    <tr><td>{cn_name}</td><td>{avg_area:.4f}</td><td>{std_area:.4f}</td></tr>")
        html.append("</table>")
    
    # 4. 结论与建议
    html.append("<h2>4. 结论与建议</h2>")
    html.append("<div class='highlight'>")
    html.append("<h3>主要发现</h3>")
    
    counts = list(stats['category_counts'].values())
    imbalance_ratio = max(counts) / min(counts) if min(counts) > 0 else 0
    if imbalance_ratio > 1.5:
        html.append(f"<p><strong>类别不平衡</strong>: 最大类别与最小类别的比例为 {imbalance_ratio:.2f}:1，建议进行数据增强</p>")
    else:
        html.append(f"<p><strong>类别平衡</strong>: 各类别数量相对均衡（比例 {imbalance_ratio:.2f}:1）</p>")
    
    if all_areas:
        html.append(f"<p><strong>面积分布</strong>: 肿瘤平均相对面积为 {np.mean(all_areas):.4f}，存在一定变异</p>")
    
    html.append("<h3>后续工作建议</h3>")
    html.append("<ol>")
    html.append("    <li>进行数据增强以平衡类别分布</li>")
    html.append("    <li>使用YOLO模型进行目标检测训练</li>")
    html.append("    <li>评估模型在不同类别上的检测性能</li>")
    html.append("</ol>")
    html.append("</div>")
    
    html.append("</body>")
    html.append("</html>")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    
    print(f"✅ 已保存: {output_file}")

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  脑肿瘤影像数据分析报告")
    print("=" * 60)
    
    # 检查数据目录（复用脑肿瘤原始数据集：models/brain_tumor_detection/data/raw/Training）
    data_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..',
        'models', 'brain_tumor_detection', 'data', 'raw', 'Training'))
    if not os.path.exists(data_dir):
        print(f"数据目录 {data_dir} 不存在，请先运行 opencv_basics.py 生成示例数据")
        exit(1)
    
    # 收集统计数据
    stats = collect_all_stats(data_dir)
    
    # 生成Markdown报告
    generate_markdown_report(stats)
    
    # 生成HTML报告
    generate_html_report(stats)
    
    print("\n" + "=" * 60)
    print("  报告生成完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - data_analysis_report.txt (文本报告)")
    print("  - data_analysis_report.html (HTML报告)")
