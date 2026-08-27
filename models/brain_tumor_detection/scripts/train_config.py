# -*- coding: utf-8 -*-
"""
训练配置
"""

import yaml
import os
import sys

# 自动检测项目根目录
def get_project_root():
    """获取项目根目录"""
    if os.path.basename(os.getcwd()) == 'scripts':
        return os.path.dirname(os.getcwd())
    if os.path.exists('scripts') and os.path.exists('data'):
        return os.getcwd()
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置项目根目录
PROJECT_ROOT = get_project_root()
os.chdir(PROJECT_ROOT)

def check_cuda():
    """检查CUDA是否可用"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def create_training_config():
    """创建训练配置文件"""
    print("=" * 60)
    print("  创建训练配置文件")
    print("=" * 60)
    
    # 自动检测设备
    cuda_available = check_cuda()
    device = '0' if cuda_available else 'cpu'
    
    print(f"  CUDA可用: {cuda_available}")
    print(f"  使用设备: {device}")
    
    # 训练配置（CPU优化参数）
    config = {
        # 基础配置
        'model': 'yolo11n.pt',  # 预训练模型
        'data': 'data/brain_tumor_yolo/data.yaml',  # 数据集配置
        'epochs': 5,  # 训练轮数（CPU训练用5轮，约15-30分钟）
        'imgsz': 320,  # 输入图像尺寸（320加快训练速度）
        'batch': 4,  # CPU用小batch，减少内存占用
        
        # 学习率配置
        'lr0': 0.01,  # 初始学习率
        'lrf': 0.01,  # 最终学习率系数
        'momentum': 0.937,  # SGD动量
        'weight_decay': 0.0005,  # 权重衰减
        
        # 数据增强配置
        'hsv_h': 0.015,  # 色调增强
        'hsv_s': 0.7,  # 饱和度增强
        'hsv_v': 0.4,  # 亮度增强
        'degrees': 0.0,  # 旋转角度
        'translate': 0.1,  # 平移
        'scale': 0.5,  # 缩放
        'flipud': 0.0,  # 上下翻转概率
        'fliplr': 0.5,  # 左右翻转概率
        
        # 训练配置
        'workers': 4,  # 数据加载线程数
        'patience': 20,  # 早停耐心值
        'save': True,  # 保存模型
        'save_period': 10,  # 每N轮保存一次
        'device': device,  # 自动选择设备
        
        # 输出配置
        'project': 'runs/train',  # 输出目录
        'name': 'brain_tumor_exp',  # 实验名称
        'exist_ok': False,  # 是否覆盖已有实验
    }
    
    # 保存配置文件
    config_path = 'configs/training_config.yaml'
    os.makedirs('configs', exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"  ✅ 配置文件已保存: {config_path}")
    
    # 打印配置信息
    print("\n" + "=" * 60)
    print("  训练配置详情")
    print("=" * 60)
    
    print("\n【基础配置】")
    print(f"  预训练模型: {config['model']}")
    print(f"  数据集配置: {config['data']}")
    print(f"  训练轮数: {config['epochs']}")
    print(f"  图像尺寸: {config['imgsz']}")
    print(f"  批次大小: {config['batch']}")
    
    print("\n【学习率配置】")
    print(f"  初始学习率: {config['lr0']}")
    print(f"  最终学习率系数: {config['lrf']}")
    print(f"  SGD动量: {config['momentum']}")
    print(f"  权重衰减: {config['weight_decay']}")
    
    print("\n【数据增强配置】")
    print(f"  色调增强: {config['hsv_h']}")
    print(f"  饱和度增强: {config['hsv_s']}")
    print(f"  亮度增强: {config['hsv_v']}")
    print(f"  旋转角度: {config['degrees']}")
    print(f"  平移: {config['translate']}")
    print(f"  缩放: {config['scale']}")
    print(f"  左右翻转概率: {config['fliplr']}")
    
    print("\n【训练配置】")
    print(f"  数据加载线程数: {config['workers']}")
    print(f"  早停耐心值: {config['patience']}")
    print(f"  保存模型: {config['save']}")
    print(f"  保存周期: 每{config['save_period']}轮")
    print(f"  GPU设备: {config['device']}")
    
    print("\n【输出配置】")
    print(f"  输出目录: {config['project']}")
    print(f"  实验名称: {config['name']}")
    
    return config

def main():
    """主函数"""
    print("=" * 60)
    print("  训练配置")
    print("=" * 60)
    
    # 检查数据集配置是否存在
    data_yaml = 'data/brain_tumor_yolo/data.yaml'
    if not os.path.exists(data_yaml):
        print(f"\n  ⚠️ 数据集配置文件不存在: {data_yaml}")
        print("  请先运行 convert_dataset.py 转换数据集")
        return
    
    print(f"\n  ✅ 检测到数据集配置: {data_yaml}")
    
    # 创建训练配置
    training_config = create_training_config()
    
    print("\n" + "=" * 60)
    print("  配置完成")
    print("=" * 60)
    print("  下一步：运行 start_training.py 开始训练")

if __name__ == "__main__":
    main()
