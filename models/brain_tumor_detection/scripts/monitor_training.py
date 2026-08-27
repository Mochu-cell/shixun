# -*- coding: utf-8 -*-
"""
训练监控
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

# 自动检测项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

def find_latest_run():
    """找到最新的训练运行"""
    # 搜索多个可能的目录
    search_dirs = [
        'runs/train',
        'runs/detect',
        'runs/detect/runs/train',  # ultralytics可能创建的嵌套路径
    ]
    
    latest_run = None
    latest_time = 0
    
    for project_dir in search_dirs:
        if not os.path.exists(project_dir):
            continue
        
        # 递归查找包含 results.csv 的目录
        for root, dirs, files in os.walk(project_dir):
            if 'results.csv' in files:
                mtime = os.path.getmtime(os.path.join(root, 'results.csv'))
                if mtime > latest_time:
                    latest_time = mtime
                    latest_run = root
    
    return latest_run

def monitor_training():
    """监控训练过程"""
    print("=" * 60)
    print("  训练过程监控")
    print("=" * 60)
    
    # 找到最新的训练运行
    run_dir = find_latest_run()
    
    if run_dir is None:
        print("  ❌ 未找到训练运行记录")
        print("  请先运行 start_training.py 开始训练")
        return
    
    print(f"  训练目录: {run_dir}")
    
    # 检查训练是否完成
    results_file = os.path.join(run_dir, 'results.csv')
    
    if not os.path.exists(results_file):
        print("  ⚠️ 训练尚未开始或正在进行中")
        return
    
    # 读取训练结果
    df = pd.read_csv(results_file)
    
    print("\n" + "=" * 60)
    print("  训练进度")
    print("=" * 60)
    
    # 显示训练信息
    print(f"  总轮数: {len(df)}")
    print(f"  当前轮数: {len(df)}")
    
    # 显示最新的Loss值
    if len(df) > 0:
        latest = df.iloc[-1]
        print("\n  最新Loss值:")
        if 'train/box_loss' in df.columns:
            print(f"    - train/box_loss: {latest['train/box_loss']:.4f}")
        if 'train/cls_loss' in df.columns:
            print(f"    - train/cls_loss: {latest['train/cls_loss']:.4f}")
        if 'train/dfl_loss' in df.columns:
            print(f"    - train/dfl_loss: {latest['train/dfl_loss']:.4f}")
        
        # 显示指标
        print("\n  最新指标:")
        if 'metrics/precision(B)' in df.columns:
            print(f"    - Precision: {latest['metrics/precision(B)']:.4f}")
        if 'metrics/recall(B)' in df.columns:
            print(f"    - Recall: {latest['metrics/recall(B)']:.4f}")
        if 'metrics/mAP50(B)' in df.columns:
            print(f"    - mAP50: {latest['metrics/mAP50(B)']:.4f}")
        if 'metrics/mAP50-95(B)' in df.columns:
            print(f"    - mAP50-95: {latest['metrics/mAP50-95(B)']:.4f}")
    
    # 绘制训练曲线
    print("\n" + "=" * 60)
    print("  绘制训练曲线")
    print("=" * 60)
    
    plot_training_curves(df, run_dir)
    
    return df

def plot_training_curves(df, run_dir):
    """绘制训练曲线"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建画布
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 总Loss曲线
    ax = axes[0, 0]
    if 'train/box_loss' in df.columns:
        ax.plot(df['train/box_loss'], label='Box Loss', color='red')
    if 'train/cls_loss' in df.columns:
        ax.plot(df['train/cls_loss'], label='Cls Loss', color='blue')
    if 'train/dfl_loss' in df.columns:
        ax.plot(df['train/dfl_loss'], label='DFL Loss', color='green')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Training Loss Curves')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. 精度曲线
    ax = axes[0, 1]
    if 'metrics/precision(B)' in df.columns:
        ax.plot(df['metrics/precision(B)'], label='Precision', color='blue')
    if 'metrics/recall(B)' in df.columns:
        ax.plot(df['metrics/recall(B)'], label='Recall', color='red')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Value')
    ax.set_title('Precision & Recall')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. mAP曲线
    ax = axes[1, 0]
    if 'metrics/mAP50(B)' in df.columns:
        ax.plot(df['metrics/mAP50(B)'], label='mAP50', color='blue')
    if 'metrics/mAP50-95(B)' in df.columns:
        ax.plot(df['metrics/mAP50-95(B)'], label='mAP50-95', color='red')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('mAP')
    ax.set_title('mAP Curves')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. 学习率曲线
    ax = axes[1, 1]
    if 'lr/pg0' in df.columns:
        ax.plot(df['lr/pg0'], label='Learning Rate', color='green')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.set_title('Learning Rate Schedule')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(run_dir, 'training_curves.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✅ 已保存: {output_path}")
    
    plt.close()

def main():
    """主函数"""
    print("=" * 60)
    print("  训练监控")
    print("=" * 60)
    
    # 监控训练
    df = monitor_training()
    
    if df is not None:
        print("\n" + "=" * 60)
        print("  监控完成")
        print("=" * 60)
        print("  下一步：运行 analyze_loss.py 分析Loss变化")

if __name__ == "__main__":
    main()
