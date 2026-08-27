#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脑肿瘤智能检测系统 - Flask Web应用
基于YOLOv11模型，实现MRI图像上传、检测、结果可视化
"""

import os
import sys
import cv2
import json
import sqlite3
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# 自动检测项目根目录
def get_project_root():
    """获取项目根目录"""
    current = os.path.dirname(os.path.abspath(__file__))
    # 从 web 目录向上查找，直到找到包含 data 和 scripts 的目录
    for _ in range(5):
        if os.path.exists(os.path.join(current, 'data')) and os.path.exists(os.path.join(current, 'scripts')):
            return current
        current = os.path.dirname(current)
    # 如果没找到，返回 web 目录的上级（scripts）的上级
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = get_project_root()

# 配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'results')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
DATABASE = os.path.join(os.path.dirname(__file__), 'detection_history.db')

# 自动查找模型路径
def find_model_path():
    """自动查找训练好的模型"""
    print(f"  项目根目录: {PROJECT_ROOT}")
    
    # 1. 首先查找 models/brain_tumor_detection/scripts/models 目录
    models_dir = os.path.join(PROJECT_ROOT, 'models', 'brain_tumor_detection', 'scripts', 'models')
    print(f"  检查模型目录: {models_dir}")
    print(f"  目录存在: {os.path.exists(models_dir)}")
    
    if os.path.exists(models_dir):
        # 列出目录内容
        print(f"  目录内容: {os.listdir(models_dir)}")
        # 查找 best_model.pt
        best_model = os.path.join(models_dir, 'best_model.pt')
        if os.path.exists(best_model):
            return best_model
        # 查找 last_model.pt
        last_model = os.path.join(models_dir, 'last_model.pt')
        if os.path.exists(last_model):
            return last_model
    
    # 2. 递归搜索 YOLO 子工程的 runs 目录
    runs_dir = os.path.join(PROJECT_ROOT, 'models', 'brain_tumor_detection', 'runs')
    print(f"  检查runs目录: {runs_dir}")
    print(f"  runs目录存在: {os.path.exists(runs_dir)}")
    
    if os.path.exists(runs_dir):
        # 查找 best.pt
        for root, dirs, files in os.walk(runs_dir):
            if 'best.pt' in files:
                return os.path.join(root, 'best.pt')
        # 查找 best_model.pt
        for root, dirs, files in os.walk(runs_dir):
            if 'best_model.pt' in files:
                return os.path.join(root, 'best_model.pt')
        # 查找 last.pt
        for root, dirs, files in os.walk(runs_dir):
            if 'last.pt' in files:
                return os.path.join(root, 'last.pt')
    
    return None

MODEL_PATH = find_model_path()

# 创建Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['MODEL_PATH'] = MODEL_PATH

# 全局模型变量
model = None


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            result_path TEXT,
            detections TEXT,
            confidence_avg REAL,
            detection_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def load_model():
    """加载YOLO模型"""
    global model
    if model is None:
        try:
            from ultralytics import YOLO
            print(f"  查找模型路径: {MODEL_PATH}")
            if MODEL_PATH:
                print(f"  模型文件存在: {os.path.exists(MODEL_PATH)}")
            if MODEL_PATH and os.path.exists(MODEL_PATH):
                model = YOLO(MODEL_PATH)
                print(f"✅ 模型加载成功: {MODEL_PATH}")
            else:
                print(f"⚠️ 模型文件不存在: {MODEL_PATH}")
                print("  请先运行训练脚本生成模型")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
    return model


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def draw_detections(image, detections, class_names):
    """在图像上绘制检测结果"""
    img_copy = image.copy()
    
    # 定义颜色（BGR格式）
    colors = {
        'glioma': (0, 0, 255),      # 红色
        'meningioma': (0, 255, 0),  # 绿色
        'pituitary': (255, 0, 0),   # 蓝色
        'notumor': (128, 128, 128)  # 灰色
    }
    
    for det in detections:
        x1, y1, x2, y2 = [int(c) for c in det['bbox']]
        class_name = det['class_name']
        confidence = det['confidence']
        color = colors.get(class_name, (255, 255, 255))
        
        # 绘制检测框
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        
        # 绘制标签背景
        label = f"{class_name}: {confidence:.2f}"
        font_scale = 0.6
        thickness = 2
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        cv2.rectangle(img_copy, (x1, y1 - label_height - 10),
                      (x1 + label_width + 5, y1), color, -1)
        
        # 绘制标签文字
        cv2.putText(img_copy, label, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    return img_copy


def save_history(image_path, result_path, detections):
    """保存检测历史"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    confidence_avg = np.mean([d['confidence'] for d in detections]) if detections else 0
    
    c.execute('''
        INSERT INTO history (image_path, result_path, detections, confidence_avg, detection_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (image_path, result_path, json.dumps(detections), float(confidence_avg), len(detections)))
    
    conn.commit()
    conn.close()


def get_history(limit=20):
    """获取检测历史"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'image_path': row[1],
            'result_path': row[2],
            'detections': json.loads(row[3]) if row[3] else [],
            'confidence_avg': row[4],
            'detection_count': row[5],
            'timestamp': row[6]
        })
    return history


# ==================== 路由 ====================

@app.route('/favicon.ico')
def favicon():
    """返回空图标，避免404错误"""
    return '', 204


@app.route('/')
def index():
    """主页"""
    model_info = {
        'loaded': model is not None,
        'path': MODEL_PATH
    }
    return render_template('index.html', model_info=model_info)


@app.route('/upload', methods=['POST'])
def upload_file():
    """处理图像上传和检测"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if not (file and allowed_file(file.filename)):
        return jsonify({'success': False, 'error': '不支持的文件格式，请上传 PNG/JPG/JPEG/BMP 图片'})
    
    # 检查模型
    if model is None:
        return jsonify({'success': False, 'error': '模型未加载，请检查模型文件是否存在'})
    
    # 保存上传文件
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # 进行推理
    results = model(filepath)
    
    # 解析结果
    detections = []
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
                detections.append({
                    'class_id': cls_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox
                })
    
    # 绘制结果
    img = cv2.imread(filepath)
    if img is not None:
        img_result = draw_detections(img, detections, model.names)
        result_filename = f"result_{filename}"
        result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
        cv2.imwrite(result_path, img_result)
        
        # 保存历史
        save_history(filepath, result_path, detections)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'result_image': result_path,
            'detections': detections,
            'detection_count': len(detections)
        })
    else:
        return jsonify({'success': False, 'error': '图像读取失败'})


@app.route('/history')
def history():
    """获取检测历史"""
    records = get_history(20)
    return jsonify({'success': True, 'history': records})


@app.route('/model_info')
def model_info():
    """获取模型信息"""
    info = {
        'loaded': model is not None,
        'path': MODEL_PATH,
        'classes': model.names if model else [],
        'class_count': len(model.names) if model else 0
    }
    return jsonify({'success': True, 'info': info})


@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory('static', filename)


# ==================== 主程序 ====================

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    # 加载模型
    load_model()
    
    # 打印系统信息
    print("\n" + "=" * 60)
    print("  脑肿瘤智能检测系统")
    print("=" * 60)
    print(f"  项目根目录: {PROJECT_ROOT}")
    print(f"  模型路径: {MODEL_PATH or '未找到'}")
    print(f"  模型状态: {'已加载' if model else '未加载'}")
    if model:
        print(f"  检测类别: {list(model.names.values())}")
    print("-" * 60)
    print(f"  访问地址: http://localhost:5001")
    print("=" * 60 + "\n")
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5001)
