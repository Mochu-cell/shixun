# -*- coding: utf-8 -*-
"""
脑肿瘤检测 - 数据集转换
功能：将原始数据集转换为YOLO格式
支持结构: data/raw/Training/类别/ 和 data/raw/Testing/类别/
"""

import os
import sys
import shutil
import random
import yaml

# 自动检测项目根目录
def get_project_root():
    """获取项目根目录"""
    # 如果当前目录是scripts，返回上一级
    if os.path.basename(os.getcwd()) == 'scripts':
        return os.path.dirname(os.getcwd())
    # 否则检查是否有scripts子目录
    if os.path.exists('scripts') and os.path.exists('data'):
        return os.getcwd()
    # 否则使用脚本所在目录的上一级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置项目根目录
PROJECT_ROOT = get_project_root()
os.chdir(PROJECT_ROOT)
print(f"  项目根目录: {PROJECT_ROOT}")

def convert_to_yolo_format(raw_dir, output_dir):
    """
    将原始数据集转换为YOLO格式
    
    原始结构:
        data/raw/
        ├── Training/
        │   ├── glioma/
        │   ├── meningioma/
        │   ├── notumor/
        │   └── pituitary/
        └── Testing/
            └── ...
    
    输出结构:
        data/brain_tumor_yolo/
        ├── images/
        │   ├── train/
        │   ├── val/
        │   └── test/
        ├── labels/
        │   ├── train/
        │   ├── val/
        │   └── test/
        └── data.yaml
    """
    print("=" * 60)
    print("  数据集转换：原始格式 → YOLO格式")
    print("=" * 60)
    
    # 检查原始目录
    if not os.path.exists(raw_dir):
        print(f"  ❌ 原始数据集目录不存在: {raw_dir}")
        return False
    
    # 类别映射（4个类别）
    class_names = ['glioma', 'meningioma', 'notumor', 'pituitary']
    class_to_id = {name: i for i, name in enumerate(class_names)}
    
    print(f"\n  原始目录: {raw_dir}")
    print(f"  输出目录: {output_dir}")
    print(f"  类别: {class_names}")
    
    # 创建输出目录
    dirs_to_create = [
        f'{output_dir}/images/train',
        f'{output_dir}/images/val',
        f'{output_dir}/images/test',
        f'{output_dir}/labels/train',
        f'{output_dir}/labels/val',
        f'{output_dir}/labels/test',
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
    
    print(f"\n  ✅ 输出目录已创建")
    
    # 收集Training目录的图片
    training_dir = os.path.join(raw_dir, 'Training')
    testing_dir = os.path.join(raw_dir, 'Testing')
    
    train_images = []
    test_images = []
    
    # 处理Training目录
    if os.path.exists(training_dir):
        print(f"\n  读取 Training 目录...")
        for class_name in class_names:
            class_dir = os.path.join(training_dir, class_name)
            
            if not os.path.exists(class_dir):
                print(f"    ⚠️ 目录不存在: {class_dir}")
                continue
            
            images = [f for f in os.listdir(class_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            print(f"    [{class_name}]: {len(images)} 张")
            
            for img_name in images:
                train_images.append({
                    'class_name': class_name,
                    'class_id': class_to_id[class_name],
                    'src_path': os.path.join(class_dir, img_name),
                    'img_name': img_name
                })
    
    # 处理Testing目录
    if os.path.exists(testing_dir):
        print(f"\n  读取 Testing 目录...")
        for class_name in class_names:
            class_dir = os.path.join(testing_dir, class_name)
            
            if not os.path.exists(class_dir):
                print(f"    ⚠️ 目录不存在: {class_dir}")
                continue
            
            images = [f for f in os.listdir(class_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            print(f"    [{class_name}]: {len(images)} 张")
            
            for img_name in images:
                test_images.append({
                    'class_name': class_name,
                    'class_id': class_to_id[class_name],
                    'src_path': os.path.join(class_dir, img_name),
                    'img_name': img_name
                })
    
    print(f"\n  统计:")
    print(f"    Training: {len(train_images)} 张")
    print(f"    Testing: {len(test_images)} 张")
    print(f"    总计: {len(train_images) + len(test_images)} 张")
    
    if len(train_images) == 0 and len(test_images) == 0:
        print("  ❌ 未找到任何图片")
        return False
    
    # 从Training中划分出验证集
    random.seed(42)
    random.shuffle(train_images)
    
    val_split = int(len(train_images) * 0.2)  # 20%作为验证集
    
    splits = {
        'train': train_images[val_split:],  # 80%训练
        'val': train_images[:val_split],    # 20%验证
        'test': test_images                 # Testing全部作为测试
    }
    
    print(f"\n  数据集划分:")
    print(f"    训练集: {len(splits['train'])} 张")
    print(f"    验证集: {len(splits['val'])} 张")
    print(f"    测试集: {len(splits['test'])} 张")
    
    # 复制图片并创建标注文件
    for split_name, images in splits.items():
        print(f"\n  处理 {split_name} 集 ({len(images)} 张)...")
        
        copied = 0
        for img_info in images:
            # 生成唯一文件名
            unique_name = f"{img_info['class_name']}_{img_info['img_name']}"
            
            # 复制图片
            src_img = img_info['src_path']
            dst_img = os.path.join(output_dir, 'images', split_name, unique_name)
            
            try:
                shutil.copy(src_img, dst_img)
                
                # 创建YOLO标注文件
                label_name = os.path.splitext(unique_name)[0] + '.txt'
                label_path = os.path.join(output_dir, 'labels', split_name, label_name)
                
                # 创建标注（中心点标注，用于分类任务）
                with open(label_path, 'w') as f:
                    f.write(f"{img_info['class_id']} 0.5 0.5 0.8 0.8\n")
                
                copied += 1
            except Exception as e:
                print(f"    ⚠️ 复制失败: {img_info['img_name']} - {e}")
        
        print(f"    ✅ 成功复制 {copied} 张")
    
    # 创建data.yaml配置文件
    create_data_yaml(output_dir, class_names)
    
    print("\n" + "=" * 60)
    print("  ✅ 数据集转换完成！")
    print("=" * 60)
    
    # 显示结果
    print("\n  输出目录结构:")
    for split in ['train', 'val', 'test']:
        img_dir = os.path.join(output_dir, 'images', split)
        lbl_dir = os.path.join(output_dir, 'labels', split)
        img_count = len([f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png'))])
        lbl_count = len([f for f in os.listdir(lbl_dir) if f.endswith('.txt')])
        print(f"    {split}: {img_count} 图片, {lbl_count} 标注")
    
    return True

def create_data_yaml(output_dir, class_names):
    """创建YOLO数据集配置文件"""
    config = {
        # 使用相对路径，保证项目目录迁移后依然可运行
        'path': output_dir,
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': len(class_names),
        'names': class_names
    }
    
    yaml_path = os.path.join(output_dir, 'data.yaml')
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"\n  ✅ 配置文件已创建: {yaml_path}")
    print(f"\n  配置内容:")
    print(f"    类别数: {len(class_names)}")
    print(f"    类别: {class_names}")

def main():
    """主函数"""
    raw_dir = 'data/raw'
    output_dir = 'data/brain_tumor_yolo'
    
    success = convert_to_yolo_format(raw_dir, output_dir)
    
    if success:
        print("\n  下一步: 运行 python scripts/env_setup.py 验证环境")
    else:
        print("\n  转换失败，请检查数据集目录")

if __name__ == "__main__":
    main()
