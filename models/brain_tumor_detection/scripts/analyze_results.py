# -*- coding: utf-8 -*-
"""
训练结果分析
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_project_root():
    """获取项目根目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'scripts':
        return os.path.dirname(current_dir)
    return current_dir

def find_latest_run():
    """找到最新的训练运行"""
    project_root = get_project_root()
    
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
        
        for root, dirs, files in os.walk(search_dir):
            if 'results.csv' in files:
                mtime = os.path.getmtime(os.path.join(root, 'results.csv'))
                if mtime > latest_time:
                    latest_time = mtime
                    latest_run = root
    
    return latest_run

def analyze_results():
    """分析训练结果"""
    print("=" * 60)
    print("  训练结果分析")
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
    
    # 分析指标
    print("\n" + "=" * 60)
    print("  模型性能指标")
    print("=" * 60)
    
    # Precision
    if 'metrics/precision(B)' in df.columns:
        precision = df['metrics/precision(B)']
        print(f"\n【Precision】")
        print(f"  最佳值: {precision.max():.4f} (第{precision.idxmax() + 1}轮)")
        print(f"  最终值: {precision.iloc[-1]:.4f}")
        print(f"  平均值: {precision.mean():.4f}")
    
    # Recall
    if 'metrics/recall(B)' in df.columns:
        recall = df['metrics/recall(B)']
        print(f"\n【Recall】")
        print(f"  最佳值: {recall.max():.4f} (第{recall.idxmax() + 1}轮)")
        print(f"  最终值: {recall.iloc[-1]:.4f}")
        print(f"  平均值: {recall.mean():.4f}")
    
    # mAP50
    if 'metrics/mAP50(B)' in df.columns:
        map50 = df['metrics/mAP50(B)']
        print(f"\n【mAP50】")
        print(f"  最佳值: {map50.max():.4f} (第{map50.idxmax() + 1}轮)")
        print(f"  最终值: {map50.iloc[-1]:.4f}")
        print(f"  平均值: {map50.mean():.4f}")
    
    # mAP50-95
    if 'metrics/mAP50-95(B)' in df.columns:
        map50_95 = df['metrics/mAP50-95(B)']
        print(f"\n【mAP50-95】")
        print(f"  最佳值: {map50_95.max():.4f} (第{map50_95.idxmax() + 1}轮)")
        print(f"  最终值: {map50_95.iloc[-1]:.4f}")
        print(f"  平均值: {map50_95.mean():.4f}")
    
    # 绘制结果分析图
    print("\n" + "=" * 60)
    print("  绘制结果分析图")
    print("=" * 60)
    
    plot_results_analysis(df, run_dir)
    
    # 模型性能评估
    print("\n" + "=" * 60)
    print("  模型性能评估")
    print("=" * 60)
    
    evaluate_model_performance(df)
    
    return df

def plot_results_analysis(df, run_dir):
    """绘制结果分析图"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建画布
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Precision-Recall曲线
    ax = axes[0, 0]
    if 'metrics/precision(B)' in df.columns and 'metrics/recall(B)' in df.columns:
        ax.plot(df['metrics/recall(B)'], df['metrics/precision(B)'], 
                label='P-R Curve', color='blue', linewidth=2)
        ax.set_xlabel('Recall')
        ax.set_ylabel('Precision')
        ax.set_title('Precision-Recall Curve')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    
    # 2. 指标对比图
    ax = axes[0, 1]
    metrics = []
    values = []
    
    if 'metrics/precision(B)' in df.columns:
        metrics.append('Precision')
        values.append(df['metrics/precision(B)'].max())
    if 'metrics/recall(B)' in df.columns:
        metrics.append('Recall')
        values.append(df['metrics/recall(B)'].max())
    if 'metrics/mAP50(B)' in df.columns:
        metrics.append('mAP50')
        values.append(df['metrics/mAP50(B)'].max())
    if 'metrics/mAP50-95(B)' in df.columns:
        metrics.append('mAP50-95')
        values.append(df['metrics/mAP50-95(B)'].max())
    
    if metrics:
        colors = ['blue', 'red', 'green', 'orange']
        bars = ax.bar(metrics, values, color=colors[:len(metrics)])
        ax.set_ylabel('Value')
        ax.set_title('Best Metrics Comparison')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 3. 指标变化趋势
    ax = axes[1, 0]
    if 'metrics/precision(B)' in df.columns:
        ax.plot(df['metrics/precision(B)'], label='Precision', color='blue')
    if 'metrics/recall(B)' in df.columns:
        ax.plot(df['metrics/recall(B)'], label='Recall', color='red')
    if 'metrics/mAP50(B)' in df.columns:
        ax.plot(df['metrics/mAP50(B)'], label='mAP50', color='green')
    if 'metrics/mAP50-95(B)' in df.columns:
        ax.plot(df['metrics/mAP50-95(B)'], label='mAP50-95', color='orange')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Value')
    ax.set_title('Metrics Trend')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. 指标分布箱线图
    ax = axes[1, 1]
    data_to_plot = []
    labels = []
    
    if 'metrics/precision(B)' in df.columns:
        data_to_plot.append(df['metrics/precision(B)'].values)
        labels.append('Precision')
    if 'metrics/recall(B)' in df.columns:
        data_to_plot.append(df['metrics/recall(B)'].values)
        labels.append('Recall')
    if 'metrics/mAP50(B)' in df.columns:
        data_to_plot.append(df['metrics/mAP50(B)'].values)
        labels.append('mAP50')
    
    if data_to_plot:
        bp = ax.boxplot(data_to_plot, patch_artist=True)
        ax.set_xticklabels(labels)
        colors = ['blue', 'red', 'green']
        for patch, color in zip(bp['boxes'], colors[:len(data_to_plot)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.5)
        ax.set_ylabel('Value')
        ax.set_title('Metrics Distribution')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(run_dir, 'results_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✅ 已保存: {output_path}")
    
    plt.close()

def evaluate_model_performance(df):
    """评估模型性能"""
    # 获取最佳指标
    best_map50 = df['metrics/mAP50(B)'].max() if 'metrics/mAP50(B)' in df.columns else 0
    best_map50_95 = df['metrics/mAP50-95(B)'].max() if 'metrics/mAP50-95(B)' in df.columns else 0
    
    print("\n  性能评级:")
    
    if best_map50_95 >= 0.7:
        print("  🏆 优秀 (mAP50-95 >= 0.7)")
    elif best_map50_95 >= 0.5:
        print("  ✅ 良好 (mAP50-95 >= 0.5)")
    elif best_map50_95 >= 0.3:
        print("  ⚠️ 一般 (mAP50-95 >= 0.3)")
    else:
        print("  ❌ 需要改进 (mAP50-95 < 0.3)")
    
    print("\n  改进建议:")
    
    if best_map50_95 < 0.5:
        print("  1. 增加训练轮数")
        print("  2. 增加训练数据量")
        print("  3. 调整学习率")
        print("  4. 使用更强的数据增强")
    
    if 'metrics/precision(B)' in df.columns and 'metrics/recall(B)' in df.columns:
        precision = df['metrics/precision(B)'].max()
        recall = df['metrics/recall(B)'].max()
        
        if precision > recall + 0.1:
            print("  5. Precision偏高，可适当降低置信度阈值")
        elif recall > precision + 0.1:
            print("  5. Recall偏高，可适当提高置信度阈值")

def main():
    """主函数"""
    print("=" * 60)
    print("  训练结果分析")
    print("=" * 60)
    
    # 分析结果
    df = analyze_results()
    
    if df is not None:
        print("\n" + "=" * 60)
        print("  分析完成")
        print("=" * 60)
        print("  下一步：运行 save_model.py 保存模型")

if __name__ == "__main__":
    main()
