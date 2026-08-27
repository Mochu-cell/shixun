# -*- coding: utf-8 -*-
"""
Loss 分析
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_project_root():
    """获取项目根目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 如果在scripts目录下，返回上一级
    if os.path.basename(current_dir) == 'scripts':
        return os.path.dirname(current_dir)
    return current_dir

def find_latest_run():
    """找到最新的训练运行"""
    project_root = get_project_root()
    
    # 搜索多个可能的目录
    search_dirs = [
        os.path.join(project_root, 'runs/train'),
        os.path.join(project_root, 'runs/detect'),
        os.path.join(project_root, 'runs/detect/runs/train'),
        os.path.join(project_root, 'runs'),
    ]
    
    latest_run = None
    latest_time = 0
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        
        # 递归查找包含 results.csv 的目录
        for root, dirs, files in os.walk(search_dir):
            if 'results.csv' in files:
                mtime = os.path.getmtime(os.path.join(root, 'results.csv'))
                if mtime > latest_time:
                    latest_time = mtime
                    latest_run = root
    
    return latest_run

def analyze_loss():
    """分析Loss变化"""
    print("=" * 60)
    print("  Loss分析")
    print("=" * 60)
    
    # 找到最新的训练运行
    run_dir = find_latest_run()
    
    if run_dir is None:
        print("  ❌ 未找到训练运行记录")
        return
    
    print(f"  训练目录: {run_dir}")
    
    # 读取训练结果
    results_file = os.path.join(run_dir, 'results.csv')
    
    if not os.path.exists(results_file):
        print("  ❌ results.csv 不存在")
        return
    
    df = pd.read_csv(results_file)
    
    print(f"  总轮数: {len(df)}")
    
    # 分析Loss
    print("\n" + "=" * 60)
    print("  Loss分析结果")
    print("=" * 60)
    
    # 1. Box Loss分析
    if 'train/box_loss' in df.columns:
        box_loss = df['train/box_loss']
        print("\n【Box Loss】")
        print(f"  初始值: {box_loss.iloc[0]:.4f}")
        print(f"  最终值: {box_loss.iloc[-1]:.4f}")
        print(f"  最小值: {box_loss.min():.4f} (第{box_loss.idxmin() + 1}轮)")
        print(f"  下降率: {(box_loss.iloc[0] - box_loss.iloc[-1]) / box_loss.iloc[0] * 100:.2f}%")
    
    # 2. Classification Loss分析
    if 'train/cls_loss' in df.columns:
        cls_loss = df['train/cls_loss']
        print("\n【Classification Loss】")
        print(f"  初始值: {cls_loss.iloc[0]:.4f}")
        print(f"  最终值: {cls_loss.iloc[-1]:.4f}")
        print(f"  最小值: {cls_loss.min():.4f} (第{cls_loss.idxmin() + 1}轮)")
        print(f"  下降率: {(cls_loss.iloc[0] - cls_loss.iloc[-1]) / cls_loss.iloc[0] * 100:.2f}%")
    
    # 3. DFL Loss分析
    if 'train/dfl_loss' in df.columns:
        dfl_loss = df['train/dfl_loss']
        print("\n【DFL Loss】")
        print(f"  初始值: {dfl_loss.iloc[0]:.4f}")
        print(f"  最终值: {dfl_loss.iloc[-1]:.4f}")
        print(f"  最小值: {dfl_loss.min():.4f} (第{dfl_loss.idxmin() + 1}轮)")
        print(f"  下降率: {(dfl_loss.iloc[0] - dfl_loss.iloc[-1]) / dfl_loss.iloc[0] * 100:.2f}%")
    
    # 4. 总Loss分析
    if all(col in df.columns for col in ['train/box_loss', 'train/cls_loss', 'train/dfl_loss']):
        total_loss = df['train/box_loss'] + df['train/cls_loss'] + df['train/dfl_loss']
        print("\n【Total Loss】")
        print(f"  初始值: {total_loss.iloc[0]:.4f}")
        print(f"  最终值: {total_loss.iloc[-1]:.4f}")
        print(f"  最小值: {total_loss.min():.4f} (第{total_loss.idxmin() + 1}轮)")
        print(f"  下降率: {(total_loss.iloc[0] - total_loss.iloc[-1]) / total_loss.iloc[0] * 100:.2f}%")
    
    # 绘制Loss分析图
    print("\n" + "=" * 60)
    print("  绘制Loss分析图")
    print("=" * 60)
    
    plot_loss_analysis(df, run_dir)
    
    # 判断训练状态
    print("\n" + "=" * 60)
    print("  训练状态判断")
    print("=" * 60)
    
    judge_training_status(df)
    
    return df

def plot_loss_analysis(df, run_dir):
    """绘制Loss分析图"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建画布
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 各Loss分量对比
    ax = axes[0, 0]
    if 'train/box_loss' in df.columns:
        ax.plot(df['train/box_loss'], label='Box Loss', color='red')
    if 'train/cls_loss' in df.columns:
        ax.plot(df['train/cls_loss'], label='Cls Loss', color='blue')
    if 'train/dfl_loss' in df.columns:
        ax.plot(df['train/dfl_loss'], label='DFL Loss', color='green')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Loss Components')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. 总Loss曲线
    ax = axes[0, 1]
    if all(col in df.columns for col in ['train/box_loss', 'train/cls_loss', 'train/dfl_loss']):
        total_loss = df['train/box_loss'] + df['train/cls_loss'] + df['train/dfl_loss']
        ax.plot(total_loss, label='Total Loss', color='purple', linewidth=2)
        ax.axhline(y=total_loss.min(), color='r', linestyle='--', label=f'Min: {total_loss.min():.4f}')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Total Loss')
    ax.set_title('Total Loss Curve')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Loss下降率
    ax = axes[1, 0]
    if all(col in df.columns for col in ['train/box_loss', 'train/cls_loss', 'train/dfl_loss']):
        box_loss = df['train/box_loss']
        cls_loss = df['train/cls_loss']
        dfl_loss = df['train/dfl_loss']
        
        box_drop = (box_loss.iloc[0] - box_loss) / box_loss.iloc[0] * 100
        cls_drop = (cls_loss.iloc[0] - cls_loss) / cls_loss.iloc[0] * 100
        dfl_drop = (dfl_loss.iloc[0] - dfl_loss) / dfl_loss.iloc[0] * 100
        
        ax.plot(box_drop, label='Box Loss Drop', color='red')
        ax.plot(cls_drop, label='Cls Loss Drop', color='blue')
        ax.plot(dfl_drop, label='DFL Loss Drop', color='green')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Drop Rate (%)')
    ax.set_title('Loss Drop Rate')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Loss分布直方图
    ax = axes[1, 1]
    if all(col in df.columns for col in ['train/box_loss', 'train/cls_loss', 'train/dfl_loss']):
        ax.hist(df['train/box_loss'], bins=20, alpha=0.5, label='Box Loss', color='red')
        ax.hist(df['train/cls_loss'], bins=20, alpha=0.5, label='Cls Loss', color='blue')
        ax.hist(df['train/dfl_loss'], bins=20, alpha=0.5, label='DFL Loss', color='green')
    ax.set_xlabel('Loss Value')
    ax.set_ylabel('Frequency')
    ax.set_title('Loss Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(run_dir, 'loss_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✅ 已保存: {output_path}")
    
    plt.close()

def judge_training_status(df):
    """判断训练状态"""
    # 检查是否有过拟合
    if all(col in df.columns for col in ['train/box_loss', 'val/box_loss']):
        train_loss = df['train/box_loss'].iloc[-10:].mean()
        val_loss = df['val/box_loss'].iloc[-10:].mean()
        
        if val_loss > train_loss * 1.5:
            print("  ⚠️ 可能存在过拟合")
            print(f"     训练Loss: {train_loss:.4f}")
            print(f"     验证Loss: {val_loss:.4f}")
        elif val_loss < train_loss * 0.8:
            print("  ✅ 训练状态良好")
            print(f"     训练Loss: {train_loss:.4f}")
            print(f"     验证Loss: {val_loss:.4f}")
        else:
            print("  ⚠️ 训练状态一般")
            print(f"     训练Loss: {train_loss:.4f}")
            print(f"     验证Loss: {val_loss:.4f}")
    
    # 检查Loss是否收敛
    if 'train/box_loss' in df.columns:
        recent_loss = df['train/box_loss'].iloc[-5:]
        if recent_loss.std() < 0.01:
            print("  ✅ Loss已收敛")
        else:
            print("  ⚠️ Loss可能还未完全收敛")

def main():
    """主函数"""
    print("=" * 60)
    print("  Loss 分析")
    print("=" * 60)
    
    # 分析Loss
    df = analyze_loss()
    
    if df is not None:
        print("\n" + "=" * 60)
        print("  分析完成")
        print("=" * 60)
        print("  下一步：运行 analyze_results.py 分析训练结果")

if __name__ == "__main__":
    main()
