/**
 * 脑肿瘤智能检测系统 - 前端JavaScript
 */

// DOM元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const originalImage = document.getElementById('originalImage');
const resultImage = document.getElementById('resultImage');
const resultSection = document.getElementById('resultSection');
const detectionCount = document.getElementById('detectionCount');
const avgConfidence = document.getElementById('avgConfidence');
const detectionList = document.getElementById('detectionList');
const historyList = document.getElementById('historyList');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initUploadArea();
    loadHistory();
});

// 初始化上传区域
function initUploadArea() {
    // 点击上传
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// 处理文件选择
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件上传
function handleFile(file) {
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }
    
    // 显示原始图像预览
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
        previewContainer.style.display = 'flex';
    };
    reader.readAsDataURL(file);
    
    // 上传文件
    uploadFile(file);
}

// 上传文件到服务器
function uploadFile(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    // 显示加载状态
    uploadArea.innerHTML = '<div class="loading">正在检测中，请稍候...</div>';
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 恢复上传区域
        resetUploadArea();
        
        if (data.success) {
            // 显示结果
            displayResults(data);
            // 刷新历史
            loadHistory();
        } else {
            alert('检测失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        resetUploadArea();
        alert('上传失败: ' + error.message);
    });
}

// 重置上传区域
function resetUploadArea() {
    uploadArea.innerHTML = `
        <div class="upload-icon">📁</div>
        <p>点击或拖拽上传MRI图像</p>
        <p class="upload-hint">支持 PNG / JPG / JPEG / BMP 格式</p>
    `;
}

// 显示检测结果
function displayResults(data) {
    // 显示结果区域
    resultSection.style.display = 'block';
    
    // 显示结果图像
    resultImage.src = '/' + data.result_image.replace(/\\/g, '/');
    
    // 更新统计信息
    detectionCount.textContent = data.detection_count;
    
    if (data.detections.length > 0) {
        const avg = data.detections.reduce((sum, d) => sum + d.confidence, 0) / data.detections.length;
        avgConfidence.textContent = (avg * 100).toFixed(1) + '%';
    } else {
        avgConfidence.textContent = '0%';
    }
    
    // 显示检测列表
    detectionList.innerHTML = '';
    data.detections.forEach(det => {
        const item = document.createElement('div');
        item.className = `detection-item ${det.class_name}`;
        item.innerHTML = `
            <div class="class-name">${getClassNameCN(det.class_name)}</div>
            <div class="confidence">置信度: ${(det.confidence * 100).toFixed(1)}%</div>
            <div class="confidence">位置: [${det.bbox.map(b => Math.round(b)).join(', ')}]</div>
        `;
        detectionList.appendChild(item);
    });
    
    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 获取类别中文名
function getClassNameCN(className) {
    const names = {
        'glioma': '胶质瘤',
        'meningioma': '脑膜瘤',
        'pituitary': '垂体瘤',
        'notumor': '正常（无肿瘤）'
    };
    return names[className] || className;
}

// 加载历史记录
function loadHistory() {
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayHistory(data.history);
            }
        })
        .catch(error => {
            console.error('加载历史失败:', error);
            historyList.innerHTML = '<p class="loading">加载失败</p>';
        });
}

// 显示历史记录
function displayHistory(history) {
    if (!history || history.length === 0) {
        historyList.innerHTML = '<p class="loading">暂无检测记录</p>';
        return;
    }
    
    historyList.innerHTML = '';
    history.forEach(record => {
        const item = document.createElement('div');
        item.className = 'history-item';
        
        const time = new Date(record.timestamp).toLocaleString('zh-CN');
        const avgConf = (record.confidence_avg * 100).toFixed(1);
        
        item.innerHTML = `
            <img src="/${record.result_path.replace(/\\/g, '/')}" alt="检测结果" onerror="this.style.display='none'">
            <div class="info">
                <p><strong>检测数:</strong> ${record.detection_count}</p>
                <p><strong>平均置信度:</strong> ${avgConf}%</p>
                <p><strong>时间:</strong> ${time}</p>
            </div>
        `;
        historyList.appendChild(item);
    });
}
