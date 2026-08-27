/**
 * 医保数据分析可视化仪表盘
 * ECharts图表渲染逻辑
 */

// 图表颜色配置
const COLORS = {
    primary: '#3498db',
    secondary: '#e74c3c',
    success: '#2ecc71',
    warning: '#f39c12',
    purple: '#9b59b6',
    teal: '#1abc9c',
    gradient: ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
};

// ============================================================
// 页面初始化
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // 更新时间
    updateTime();
    
    // 加载KPI数据
    loadKPI();
    
    // 初始化图表
    initCharts();
});

// 更新当前时间
function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('update-time').textContent = timeStr;
}

// ============================================================
// KPI数据加载
// ============================================================

function loadKPI() {
    fetch('/api/kpi')
        .then(response => response.json())
        .then(data => {
            // 总费用
            document.getElementById('kpi-total-amount').textContent = 
                formatNumber(data.total_amount);
            
            // 总就诊量
            document.getElementById('kpi-visit-count').textContent = 
                formatNumber(data.visit_count);
            
            // 异常预警
            document.getElementById('kpi-abnormal-count').textContent = 
                data.abnormal_count || 0;
            
            // 平均报销率
            document.getElementById('kpi-reimburse-rate').textContent = 
                (data.avg_reimburse_rate * 100).toFixed(1);
        })
        .catch(error => {
            console.error('加载KPI数据失败:', error);
        });
    
    // 加载高风险人数KPI
    fetch('/api/high_risk_count')
        .then(response => response.json())
        .then(data => {
            document.getElementById('kpi-high-risk-count').textContent = 
                data.count || 0;
        })
        .catch(error => {
            console.error('加载高风险人数失败:', error);
        });
}

// 数字格式化
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString('zh-CN');
}

// ============================================================
// 图表初始化
// ============================================================

let charts = {};

function initCharts() {
    // 月度趋势图
    charts.monthly = echarts.init(document.getElementById('chart-monthly'));
    loadMonthlyData();
    
    // 参保类型柱状图
    charts.type = echarts.init(document.getElementById('chart-type'));
    loadInsuranceTypeData();
    
    // 费用结构饼图
    charts.pie = echarts.init(document.getElementById('chart-pie'));
    loadExpenseStructureData();
    
    // 热力图
    charts.heatmap = echarts.init(document.getElementById('chart-heatmap'));
    loadHeatmapData();
    
    // 年龄分布图
    charts.age = echarts.init(document.getElementById('chart-age'));
    loadAgeDistributionData();
    
    // 次均费用趋势图（独立）
    charts.avgCost = echarts.init(document.getElementById('chart-avg-cost'));
    loadAvgCostData();
    
    // 窗口大小变化时重新调整图表
    window.addEventListener('resize', function() {
        Object.values(charts).forEach(chart => {
            chart && chart.resize();
        });
    });
}

// ============================================================
// 月度趋势图
// ============================================================

function loadMonthlyData() {
    fetch('/api/monthly')
        .then(response => response.json())
        .then(data => {
            const option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross'
                    }
                },
                legend: {
                    data: ['总费用', '次均费用', '就诊人次'],
                    bottom: 0
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '15%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: data.months
                },
                yAxis: [
                    {
                        type: 'value',
                        name: '费用(元)',
                        position: 'left'
                    },
                    {
                        type: 'value',
                        name: '人次',
                        position: 'right'
                    }
                ],
                series: [
                    {
                        name: '总费用',
                        type: 'line',
                        smooth: true,
                        data: data.total_amount,
                        itemStyle: { color: COLORS.primary },
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: 'rgba(52, 152, 219, 0.3)' },
                                { offset: 1, color: 'rgba(52, 152, 219, 0.05)' }
                            ])
                        }
                    },
                    {
                        name: '次均费用',
                        type: 'line',
                        smooth: true,
                        data: data.avg_amount,
                        itemStyle: { color: COLORS.secondary }
                    },
                    {
                        name: '就诊人次',
                        type: 'bar',
                        data: data.visit_count,
                        itemStyle: { color: COLORS.success },
                        yAxisIndex: 1
                    }
                ]
            };
            
            charts.monthly.setOption(option);
        });
}

// ============================================================
// 次均费用趋势图（独立）
// ============================================================

function loadAvgCostData() {
    fetch('/api/monthly')
        .then(response => response.json())
        .then(data => {
            const option = {
                tooltip: {
                    trigger: 'axis',
                    formatter: function(params) {
                        return params[0].axisValue + '<br/>' +
                               params[0].marker + '次均费用: ' + params[0].value.toFixed(2) + ' 元';
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: data.months
                },
                yAxis: {
                    type: 'value',
                    name: '费用(元)'
                },
                series: [{
                    name: '次均费用',
                    type: 'line',
                    smooth: true,
                    data: data.avg_amount,
                    itemStyle: { color: COLORS.secondary },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(231, 76, 60, 0.3)' },
                            { offset: 1, color: 'rgba(231, 76, 60, 0.05)' }
                        ])
                    },
                    markLine: {
                        silent: true,
                        data: [{
                            type: 'average',
                            name: '平均值',
                            lineStyle: { color: '#e74c3c', type: 'dashed' }
                        }]
                    }
                }]
            };
            
            charts.avgCost.setOption(option);
        });
}

// ============================================================
// 参保类型柱状图
// ============================================================

function loadInsuranceTypeData() {
    fetch('/api/insurance_type')
        .then(response => response.json())
        .then(data => {
            const option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: ['总费用', '就诊人次'],
                    bottom: 0
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '15%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.types
                },
                yAxis: [
                    {
                        type: 'value',
                        name: '费用(元)'
                    },
                    {
                        type: 'value',
                        name: '人次',
                        position: 'right'
                    }
                ],
                series: [
                    {
                        name: '总费用',
                        type: 'bar',
                        data: data.total_amount,
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: COLORS.primary },
                                { offset: 1, color: '#2980b9' }
                            ])
                        },
                        label: {
                            show: true,
                            position: 'top',
                            formatter: '{c}'
                        }
                    },
                    {
                        name: '就诊人次',
                        type: 'bar',
                        data: data.visit_count,
                        itemStyle: { color: COLORS.success },
                        yAxisIndex: 1
                    }
                ]
            };
            
            charts.type.setOption(option);
        });
}

// ============================================================
// 费用结构饼图
// ============================================================

function loadExpenseStructureData() {
    fetch('/api/expense_structure')
        .then(response => response.json())
        .then(data => {
            const pieData = data.categories.map((cat, i) => ({
                name: cat,
                value: data.amounts[i]
            }));
            
            const option = {
                tooltip: {
                    trigger: 'item',
                    formatter: '{b}: {c}元 ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    right: '5%',
                    top: 'center'
                },
                series: [
                    {
                        name: '费用结构',
                        type: 'pie',
                        radius: ['40%', '70%'],  // 环形饼图
                        center: ['40%', '50%'],
                        avoidLabelOverlap: false,
                        itemStyle: {
                            borderRadius: 10,
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        label: {
                            show: true,
                            formatter: '{b}: {d}%'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 14,
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: true
                        },
                        data: pieData,
                        color: COLORS.gradient
                    }
                ]
            };
            
            charts.pie.setOption(option);
        });
}

// ============================================================
// 热力图
// ============================================================

function loadHeatmapData() {
    fetch('/api/hospital_heatmap')
        .then(response => response.json())
        .then(data => {
            const option = {
                tooltip: {
                    position: 'top',
                    formatter: function(params) {
                        return `${data.hospitals[params.data[1]]} - ${data.departments[params.data[0]]}<br/>费用: ${params.data[2]}元`;
                    }
                },
                grid: {
                    height: '70%',
                    top: '10%',
                    left: '15%'
                },
                xAxis: {
                    type: 'category',
                    data: data.departments,
                    splitArea: {
                        show: true
                    },
                    axisLabel: {
                        rotate: 30
                    }
                },
                yAxis: {
                    type: 'category',
                    data: data.hospitals,
                    splitArea: {
                        show: true
                    }
                },
                visualMap: {
                    min: 0,
                    max: data.max_value,
                    calculable: true,
                    orient: 'horizontal',
                    left: 'center',
                    bottom: '5%',
                    inRange: {
                        color: ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']
                    }
                },
                series: [{
                    name: '费用',
                    type: 'heatmap',
                    data: data.data,
                    label: {
                        show: true,
                        formatter: function(params) {
                            return formatNumber(params.data[2]);
                        }
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            };
            
            charts.heatmap.setOption(option);
        });
}

// ============================================================
// 年龄分布图
// ============================================================

function loadAgeDistributionData() {
    fetch('/api/age_distribution')
        .then(response => response.json())
        .then(data => {
            const option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: ['参保人数', '总费用'],
                    bottom: 0
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '15%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.age_groups
                },
                yAxis: [
                    {
                        type: 'value',
                        name: '人数'
                    },
                    {
                        type: 'value',
                        name: '费用(元)',
                        position: 'right'
                    }
                ],
                series: [
                    {
                        name: '参保人数',
                        type: 'bar',
                        data: data.counts,
                        itemStyle: { color: COLORS.purple },
                        label: {
                            show: true,
                            position: 'top'
                        }
                    },
                    {
                        name: '总费用',
                        type: 'line',
                        data: data.total_amount,
                        itemStyle: { color: COLORS.warning },
                        yAxisIndex: 1,
                        smooth: true
                    }
                ]
            };
            
            charts.age.setOption(option);
        });
}

// ============================================================
// 图表联动功能（可选）
// ============================================================

// 点击参保类型柱状图，联动更新其他图表
charts.type && charts.type.on('click', function(params) {
    console.log('点击参保类型:', params.name);
    // 可以在这里实现图表联动
});

// ============================================================
// 定时刷新数据（可选）
// ============================================================

// 每5分钟刷新一次数据
// setInterval(function() {
//     loadKPI();
//     Object.values(charts).forEach(chart => {
//         chart && chart.clear();
//     });
//     initCharts();
//     loadAbnormalList();
//     updateTime();
// }, 300000);

// ============================================================
// 高风险人员名单
// ============================================================

var currentPage = 1;
var totalPages = 1;

function loadHighRiskPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    
    fetch(`/api/high_risk_list?page=${page}&page_size=10`)
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#high-risk-table tbody');
            tbody.innerHTML = '';
            
            if (data.records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading-text">暂无高风险记录</td></tr>';
                return;
            }
            
            data.records.forEach(record => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${record.user_id}</td>
                    <td>${record.user_name}</td>
                    <td>${record.age_group}</td>
                    <td><span class="risk-high">${record.abnormal_type}</span></td>
                    <td style="text-align:right;">${record.abnormal_amount.toFixed(2)}</td>
                    <td>${record.detection_date}</td>
                    <td>${record.abnormal_desc}</td>
                `;
                tbody.appendChild(tr);
            });
            
            totalPages = Math.ceil(data.total / data.page_size);
            document.getElementById('high-risk-total').textContent = `${data.total}条`;
            document.getElementById('page-info').textContent = `第${currentPage}页 / 共${totalPages}页`;
            document.getElementById('btn-prev').disabled = (currentPage <= 1);
            document.getElementById('btn-next').disabled = (currentPage >= totalPages);
        })
        .catch(error => {
            console.error('加载高风险名单失败:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    loadHighRiskPage(1);
});