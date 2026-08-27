/**
 * 医疗大数据与脑肿瘤影像智能检测系统
 * 仪表盘前端脚本
 */

// 初始化图表
const monthlyChart = echarts.init(document.getElementById('monthly_chart'));
const tumorTypeChart = echarts.init(document.getElementById('tumor_type_chart'));
const detectionTrendChart = echarts.init(document.getElementById('detection_trend_chart'));
const confidenceChart = echarts.init(document.getElementById('confidence_chart'));
const insuranceTypeChart = echarts.init(document.getElementById('insurance_type_chart'));

// 加载KPI数据
async function loadKPI() {
    try {
        const response = await fetch('/api/kpi');
        const data = await response.json();
        
        document.getElementById('total_persons').textContent = data.total_persons?.toLocaleString() || '0';
        document.getElementById('total_cost').textContent = ((data.total_cost || 0) / 10000).toFixed(2);
        document.getElementById('reimburse_rate').textContent = ((data.reimburse_rate || 0) * 100).toFixed(1) + '%';
        document.getElementById('total_detections').textContent = data.total_detections?.toLocaleString() || '0';
        document.getElementById('tumor_detected').textContent = data.tumor_detected?.toLocaleString() || '0';
        document.getElementById('positive_rate').textContent = (data.positive_rate || 0).toFixed(1) + '%';
    } catch (error) {
        console.error('KPI加载失败:', error);
    }
}

// 加载月度趋势
async function loadMonthly() {
    try {
        const response = await fetch('/api/monthly');
        const data = await response.json();
        
        if (data.error || !data.months) {
            monthlyChart.clear();
            return;
        }
        
        monthlyChart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['总费用', '次均费用'] },
            xAxis: { type: 'category', data: data.months },
            yAxis: { type: 'value', name: '金额(元)' },
            series: [
                { name: '总费用', type: 'bar', data: data.total_amount, itemStyle: { color: '#5470c6' } },
                { name: '次均费用', type: 'line', data: data.avg_amount, itemStyle: { color: '#91cc75' } }
            ]
        });
    } catch (error) {
        console.error('月度数据加载失败:', error);
    }
}

// 加载肿瘤类型分布
async function loadTumorType() {
    try {
        const response = await fetch('/api/tumor_type');
        const data = await response.json();
        
        if (!data || data.length === 0) {
            tumorTypeChart.clear();
            return;
        }
        
        const types = data.map(d => d.type);
        const counts = data.map(d => d.count);
        
        tumorTypeChart.setOption({
            tooltip: { trigger: 'item' },
            legend: { orient: 'vertical', left: 'left' },
            series: [{
                name: '肿瘤类型',
                type: 'pie',
                radius: '60%',
                data: data.map(d => ({ name: d.type, value: d.count })),
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }]
        });
    } catch (error) {
        console.error('肿瘤类型数据加载失败:', error);
    }
}

// 加载检测趋势
async function loadDetectionTrend() {
    try {
        const response = await fetch('/api/detection_trend');
        const data = await response.json();
        
        if (!data || data.length === 0) {
            detectionTrendChart.clear();
            return;
        }
        
        const dates = data.map(d => d.date);
        const totals = data.map(d => d.total);
        const detected = data.map(d => d.detected);
        
        detectionTrendChart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['总检测数', '检出数'] },
            xAxis: { type: 'category', data: dates },
            yAxis: { type: 'value', name: '数量' },
            series: [
                { name: '总检测数', type: 'line', data: totals, smooth: true, itemStyle: { color: '#5470c6' } },
                { name: '检出数', type: 'line', data: detected, smooth: true, itemStyle: { color: '#ee6666' } }
            ]
        });
    } catch (error) {
        console.error('检测趋势数据加载失败:', error);
    }
}

// 加载置信度分布
async function loadConfidence() {
    try {
        const response = await fetch('/api/confidence');
        const data = await response.json();
        
        if (!data || data.length === 0) {
            confidenceChart.clear();
            return;
        }
        
        const ranges = data.map(d => d.range);
        const counts = data.map(d => d.count);
        
        confidenceChart.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ranges },
            yAxis: { type: 'value', name: '数量' },
            series: [{
                type: 'bar',
                data: counts,
                itemStyle: {
                    color: function(params) {
                        const colors = ['#91cc75', '#5470c6', '#ee6666'];
                        return colors[params.dataIndex % colors.length];
                    }
                }
            }]
        });
    } catch (error) {
        console.error('置信度数据加载失败:', error);
    }
}

// 加载参保类型
async function loadInsuranceType() {
    try {
        const response = await fetch('/api/insurance_type');
        const data = await response.json();
        
        if (data.error || !data.types) {
            insuranceTypeChart.clear();
            return;
        }
        
        insuranceTypeChart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['总费用', '就诊次数'] },
            xAxis: { type: 'category', data: data.types },
            yAxis: [
                { type: 'value', name: '费用(元)' },
                { type: 'value', name: '次数' }
            ],
            series: [
                { name: '总费用', type: 'bar', data: data.total_amount, itemStyle: { color: '#5470c6' } },
                { name: '就诊次数', type: 'line', yAxisIndex: 1, data: data.visit_count, itemStyle: { color: '#91cc75' } }
            ]
        });
    } catch (error) {
        console.error('参保类型数据加载失败:', error);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadKPI();
    loadMonthly();
    loadTumorType();
    loadDetectionTrend();
    loadConfidence();
    loadInsuranceType();
});

// 窗口大小改变时重新调整图表
window.addEventListener('resize', function() {
    monthlyChart.resize();
    tumorTypeChart.resize();
    detectionTrendChart.resize();
    confidenceChart.resize();
    insuranceTypeChart.resize();
});
