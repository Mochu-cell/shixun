# -*- coding: utf-8 -*-
"""
启动训练
"""

import os
import yaml
from ultralytics import YOLO

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

def load_config():
    """加载训练配置"""
    config_path = 'configs/training_config.yaml'
    
    if not os.path.exists(config_path):
        print(f"  ❌ 配置文件不存在: {config_path}")
        print("  请先运行 train_config.py 创建配置")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

def start_training():
    """启动训练"""
    print("=" * 60)
    print("  启动脑肿瘤检测模型训练")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if config is None:
        return
    
    # 加载预训练模型
    print("\n[1/4] 加载预训练模型...")
    model = YOLO(config['model'])
    print(f"  ✅ 模型加载成功: {config['model']}")
    
    # 检查数据集
    print("\n[2/4] 检查数据集...")
    dataset_path = config['data']
    if not os.path.exists(dataset_path):
        print(f"  ❌ 数据集配置文件不存在: {dataset_path}")
        return
    print(f"  ✅ 数据集配置: {dataset_path}")
    
    # 开始训练
    print("\n[3/4] 开始训练...")
    print("  训练参数:")
    print(f"    - epochs: {config['epochs']}")
    print(f"    - imgsz: {config['imgsz']}")
    print(f"    - batch: {config['batch']}")
    print(f"    - device: {config['device']}")
    
    # 训练
    results = model.train(
        data=config['data'],
        epochs=config['epochs'],
        imgsz=config['imgsz'],
        batch=config['batch'],
        workers=config['workers'],
        patience=config['patience'],
        save=config['save'],
        save_period=config['save_period'],
        device=config['device'],
        project=config['project'],
        name=config['name'],
        exist_ok=config['exist_ok'],
        lr0=config['lr0'],
        lrf=config['lrf'],
        momentum=config['momentum'],
        weight_decay=config['weight_decay'],
        hsv_h=config['hsv_h'],
        hsv_s=config['hsv_s'],
        hsv_v=config['hsv_v'],
        degrees=config['degrees'],
        translate=config['translate'],
        scale=config['scale'],
        flipud=config['flipud'],
        fliplr=config['fliplr'],
    )
    
    print("\n[4/4] 训练完成")
    print(f"  ✅ 训练结果已保存")
    
    return results

def main():
    """主函数"""
    print("=" * 60)
    print("  启动训练")
    print("=" * 60)
    
    # 启动训练
    results = start_training()
    
    if results:
        print("\n" + "=" * 60)
        print("  训练完成！")
        print("=" * 60)
        print("  下一步：运行 monitor_training.py 监控训练过程")

if __name__ == "__main__":
    main()
