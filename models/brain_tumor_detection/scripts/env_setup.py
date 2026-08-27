# -*- coding: utf-8 -*-
"""
YOLOv11 训练环境配置与验证
"""

import sys
import subprocess
import importlib
import os

# 自动检测项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)
print(f"  项目根目录: {PROJECT_ROOT}")

def check_python_version():
    """检查Python版本"""
    print("=" * 60)
    print("1. 检查Python版本")
    print("=" * 60)
    version = sys.version_info
    print(f"  当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("  ✅ Python版本满足要求 (>= 3.8)")
        return True
    else:
        print("  ❌ Python版本不满足要求，需要 >= 3.8")
        return False

def check_cuda():
    """检查CUDA可用性"""
    print("\n" + "=" * 60)
    print("2. 检查CUDA")
    print("=" * 60)
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        print(f"  CUDA可用: {cuda_available}")
        
        if cuda_available:
            print(f"  CUDA版本: {torch.version.cuda}")
            print(f"  GPU设备: {torch.cuda.get_device_name(0)}")
            print(f"  GPU数量: {torch.cuda.device_count()}")
            
            # 测试GPU计算
            x = torch.randn(3, 3).cuda()
            y = torch.randn(3, 3).cuda()
            z = torch.mm(x, y)
            print("  ✅ GPU计算测试通过")
        else:
            print("  ⚠️ CUDA不可用，将使用CPU训练")
            print("  建议安装CUDA以加速训练")
        
        return cuda_available
    except ImportError:
        print("  ❌ PyTorch未安装")
        return False

def check_ultralytics():
    """检查ultralytics库"""
    print("\n" + "=" * 60)
    print("3. 检查ultralytics库")
    print("=" * 60)
    
    try:
        import ultralytics
        from ultralytics import YOLO
        
        print(f"  ultralytics版本: {ultralytics.__version__}")
        
        # 测试模型加载
        print("  测试加载YOLOv11模型...")
        model = YOLO('yolo11n.pt')
        print("  ✅ 模型加载成功")
        
        # 显示模型信息
        print(f"  模型类型: {model.model_name}")
        
        return True
    except ImportError:
        print("  ❌ ultralytics未安装")
        print("  安装命令: pip install ultralytics")
        return False
    except Exception as e:
        print(f"  ❌ 模型加载失败: {e}")
        return False

def check_opencv():
    """检查OpenCV"""
    print("\n" + "=" * 60)
    print("4. 检查OpenCV")
    print("=" * 60)
    
    try:
        import cv2
        print(f"  OpenCV版本: {cv2.__version__}")
        print("  ✅ OpenCV已安装")
        return True
    except ImportError:
        print("  ❌ OpenCV未安装")
        print("  安装命令: pip install opencv-python")
        return False

def check_numpy():
    """检查NumPy"""
    print("\n" + "=" * 60)
    print("5. 检查NumPy")
    print("=" * 60)
    
    try:
        import numpy as np
        print(f"  NumPy版本: {np.__version__}")
        print("  ✅ NumPy已安装")
        return True
    except ImportError:
        print("  ❌ NumPy未安装")
        print("  安装命令: pip install numpy")
        return False

def check_dataset():
    """检查数据集"""
    print("\n" + "=" * 60)
    print("6. 检查数据集")
    print("=" * 60)
    
    import os
    
    dataset_path = "data/brain_tumor_yolo"
    
    if not os.path.exists(dataset_path):
        print(f"  ❌ 数据集目录不存在: {dataset_path}")
        print("  请先运行 python scripts/convert_dataset.py 转换数据集")
        return False
    
    # 检查目录结构
    required_dirs = ['images/train', 'images/val', 'images/test', 'labels/train', 'labels/val', 'labels/test']
    all_exist = True
    
    for dir_name in required_dirs:
        dir_path = os.path.join(dataset_path, dir_name)
        if os.path.exists(dir_path):
            # 统计文件数量
            files = [f for f in os.listdir(dir_path) if f.endswith(('.jpg', '.png', '.txt'))]
            print(f"  ✅ {dir_name}: {len(files)} 个文件")
        else:
            print(f"  ❌ {dir_name} 不存在")
            all_exist = False
    
    # 检查YAML配置文件
    yaml_path = "data/brain_tumor_yolo/data.yaml"
    if os.path.exists(yaml_path):
        print(f"  ✅ 数据集配置文件: {yaml_path}")
    else:
        print(f"  ❌ 数据集配置文件不存在: {yaml_path}")
        all_exist = False
    
    return all_exist

def print_summary(results):
    """打印检查结果汇总"""
    print("\n" + "=" * 60)
    print("环境检查汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！可以开始训练")
    else:
        print("⚠️ 部分检查未通过，请修复后再开始训练")
    print("=" * 60)

def main():
    """主函数"""
    print("=" * 60)
    print("  YOLOv11训练环境配置与验证")
    print("=" * 60)
    
    results = {}
    
    # 执行各项检查
    results['Python版本'] = check_python_version()
    results['CUDA'] = check_cuda()
    results['ultralytics'] = check_ultralytics()
    results['OpenCV'] = check_opencv()
    results['NumPy'] = check_numpy()
    results['数据集'] = check_dataset()
    
    # 打印汇总
    print_summary(results)
    
    # 提供安装命令
    print("\n" + "=" * 60)
    print("一键安装命令")
    print("=" * 60)
    print("pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    print("pip install ultralytics opencv-python numpy")

if __name__ == "__main__":
    main()
