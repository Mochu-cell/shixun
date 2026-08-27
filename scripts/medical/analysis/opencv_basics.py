#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCV 基础操作
功能：图像读取、显示、颜色空间转换、批量读取
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 图像读取与显示
# ============================================================
def demo_image_read():
    """演示图像读取与显示"""
    print("=" * 60)
    print("1. 图像读取与显示")
    print("=" * 60)
    
    # 创建示例图像（如果没有真实数据）
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    img[50:200, 50:200] = [128, 128, 128]  # 灰色方块模拟肿瘤
    cv2.circle(img, (128, 128), 50, (0, 255, 0), -1)  # 绿色圆形
    
    print(f"图像形状: {img.shape}")
    print(f"图像数据类型: {img.dtype}")
    print(f"图像尺寸: {img.shape[1]}x{img.shape[0]}")
    
    # 显示图像
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 3, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title('原始图像 (BGR)')
    plt.axis('off')
    
    # 灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    plt.subplot(1, 3, 2)
    plt.imshow(gray, cmap='gray')
    plt.title('灰度图')
    plt.axis('off')
    
    # 边缘检测
    edges = cv2.Canny(gray, 50, 150)
    plt.subplot(1, 3, 3)
    plt.imshow(edges, cmap='gray')
    plt.title('Canny边缘检测')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('demo_image_processing.png', dpi=150, bbox_inches='tight')
    print("✅ 已保存: demo_image_processing.png")
    plt.close()

# ============================================================
# 2. 颜色空间转换
# ============================================================
def demo_color_space():
    """演示颜色空间转换"""
    print("\n" + "=" * 60)
    print("2. 颜色空间转换")
    print("=" * 60)
    
    # 创建示例图像
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    img[50:200, 50:200] = [100, 150, 200]
    
    # 不同颜色空间
    bgr = img.copy()
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    print(f"BGR值 (128,128): {bgr[128, 128]}")
    print(f"RGB值 (128,128): {rgb[128, 128]}")
    print(f"HSV值 (128,128): {hsv[128, 128]}")
    print(f"灰度值 (128,128): {gray[128, 128]}")
    
    # 显示不同颜色空间
    plt.figure(figsize=(12, 3))
    
    plt.subplot(1, 4, 1)
    plt.imshow(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    plt.title('BGR (OpenCV默认)')
    plt.axis('off')
    
    plt.subplot(1, 4, 2)
    plt.imshow(rgb)
    plt.title('RGB')
    plt.axis('off')
    
    plt.subplot(1, 4, 3)
    plt.imshow(hsv)
    plt.title('HSV')
    plt.axis('off')
    
    plt.subplot(1, 4, 4)
    plt.imshow(gray, cmap='gray')
    plt.title('灰度图')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('demo_color_space.png', dpi=150, bbox_inches='tight')
    print("✅ 已保存: demo_color_space.png")
    plt.close()

# ============================================================
# 3. 图像基本操作
# ============================================================
def demo_image_operations():
    """演示图像基本操作"""
    print("\n" + "=" * 60)
    print("3. 图像基本操作")
    print("=" * 60)
    
    # 创建示例图像
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (200, 200), (0, 255, 0), 2)
    cv2.circle(img, (128, 128), 50, (255, 0, 0), -1)
    
    # 图像操作
    print(f"图像形状: {img.shape}")
    print(f"图像大小: {img.size} 像素")
    print(f"图像通道数: {img.shape[2] if len(img.shape) > 2 else 1}")
    
    # 裁剪
    crop = img[50:150, 50:150]
    print(f"裁剪后形状: {crop.shape}")
    
    # 缩放
    resized = cv2.resize(img, (128, 128))
    print(f"缩放后形状: {resized.shape}")
    
    # 旋转
    M = cv2.getRotationMatrix2D((128, 128), 45, 1.0)
    rotated = cv2.warpAffine(img, M, (256, 256))
    
    # 显示
    plt.figure(figsize=(12, 3))
    
    plt.subplot(1, 4, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title('原始图像')
    plt.axis('off')
    
    plt.subplot(1, 4, 2)
    plt.imshow(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    plt.title('裁剪')
    plt.axis('off')
    
    plt.subplot(1, 4, 3)
    plt.imshow(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
    plt.title('缩放')
    plt.axis('off')
    
    plt.subplot(1, 4, 4)
    plt.imshow(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))
    plt.title('旋转45°')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('demo_image_operations.png', dpi=150, bbox_inches='tight')
    print("✅ 已保存: demo_image_operations.png")
    plt.close()

# ============================================================
# 4. 批量读取图像
# ============================================================
def demo_batch_read(data_dir=None):
    """演示批量读取图像"""
    print("\n" + "=" * 60)
    print("4. 批量读取图像")
    print("=" * 60)
    
    # 默认在脚本目录下生成示例数据，避免污染原始数据集
    if data_dir is None:
        data_dir = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'sample_data'))
    
    # 创建示例数据目录
    os.makedirs(data_dir, exist_ok=True)
    
    # 生成示例图像
    categories = ['glioma', 'meningioma', 'pituitary']
    for cat in categories:
        cat_dir = os.path.join(data_dir, cat)
        os.makedirs(cat_dir, exist_ok=True)
        
        for i in range(3):
            img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            cv2.circle(img, (128, 128), 50 + i * 10, (0, 255, 0), -1)
            cv2.imwrite(os.path.join(cat_dir, f'{cat}_{i}.jpg'), img)
    
    print(f"已创建示例数据目录: {data_dir}")
    
    # 批量读取
    image_list = []
    label_list = []
    
    for cat in categories:
        cat_dir = os.path.join(data_dir, cat)
        for img_name in os.listdir(cat_dir):
            img_path = os.path.join(cat_dir, img_name)
            img = cv2.imread(img_path)
            if img is not None:
                image_list.append(img)
                label_list.append(cat)
    
    print(f"\n批量读取完成:")
    print(f"  总图像数: {len(image_list)}")
    print(f"  类别数: {len(set(label_list))}")
    print(f"  各类别数量: {dict(zip(*np.unique(label_list, return_counts=True)))}")
    
    # 显示部分图像
    plt.figure(figsize=(12, 4))
    for i in range(min(6, len(image_list))):
        plt.subplot(2, 3, i + 1)
        plt.imshow(cv2.cvtColor(image_list[i], cv2.COLOR_BGR2RGB))
        plt.title(f'{label_list[i]}')
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('demo_batch_read.png', dpi=150, bbox_inches='tight')
    print("✅ 已保存: demo_batch_read.png")
    plt.close()

# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  OpenCV 基础操作")
    print("=" * 60)
    
    # 运行所有演示
    demo_image_read()
    demo_color_space()
    demo_image_operations()
    demo_batch_read()
    
    print("\n" + "=" * 60)
    print("  所有演示完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - demo_image_processing.png")
    print("  - demo_color_space.png")
    print("  - demo_image_operations.png")
    print("  - demo_batch_read.png")
    print("  - data/ (示例数据目录)")
