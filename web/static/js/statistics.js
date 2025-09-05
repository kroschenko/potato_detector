class StatisticsManager {
    constructor() {
        this.charts = {};
        this.statisticsData = {
            detectionRateData: [],
            qualityData: { good: 0, defected: 0 }
        };
        this.lastChartUpdate = 0;
        this.chartUpdateInterval = 5000;
        
        this.initializeCharts();
        this.requestStatisticsUpdate();
        this.subscribeToEvents();
    }
    
    initializeCharts() {
        this.initializeDetectionChart();
        this.initializeQualityChart();
    }
    
    initializeDetectionChart() {
        const ctx = document.getElementById('detection-chart');
        if (!ctx) return;
        
        this.charts.detection = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Картофелин в минуту',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e2e8f0'
                        },
                        ticks: {
                            color: '#64748b',
                            maxTicksLimit: 5
                        }
                    },
                    x: {
                        grid: {
                            color: '#e2e8f0'
                        },
                        ticks: {
                            color: '#64748b',
                            maxTicksLimit: 6
                        }
                    }
                }
            }
        });
    }
    
    initializeQualityChart() {
        const ctx = document.getElementById('quality-chart');
        if (!ctx) return;
        
        this.charts.quality = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Хороший картофель', 'Дефектный картофель'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: [
                        '#059669',
                        '#dc2626'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                animation: {
                    duration: 0
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 10,
                            usePointStyle: true,
                            color: '#374151',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateStatistics(data) {
        this.updateStatisticValues(data);
        this.updateCharts(data);
    }
    
    updateStatisticValues(data) {
        const elements = {
            'total-potatoes': data.total_potatoes || 0,
            'defected-potatoes': data.defected_potatoes || 0,
            'defect-rate': `${data.defect_rate || 0}%`,
            'processing-rate': data.potatoes_per_minute || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                this.animateValue(element);
            }
        });
    }
    
    updateCharts(data) {
        const now = Date.now();
        if (now - this.lastChartUpdate >= this.chartUpdateInterval) {
            this.updateDetectionChart(data);
            this.lastChartUpdate = now;
        }
        this.updateQualityChart(data);
    }
    
    updateDetectionChart(data) {
        if (!this.charts.detection) return;
        
        const now = new Date();
        const timeLabel = now.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
        });
        
        const chart = this.charts.detection;
        const maxDataPoints = 12;
        
        chart.data.labels.push(timeLabel);
        chart.data.datasets[0].data.push(data.potatoes_per_minute || 0);
        
        while (chart.data.labels.length > maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        
        chart.update('none');
    }
    
    updateQualityChart(data) {
        if (!this.charts.quality) return;
        
        const totalPotatoes = data.total_potatoes || 0;
        const defectedPotatoes = data.defected_potatoes || 0;
        const goodPotatoes = totalPotatoes - defectedPotatoes;
        
        const chart = this.charts.quality;
        chart.data.datasets[0].data = [goodPotatoes, defectedPotatoes];
        chart.update('none');
    }
    
    animateValue(element) {
        element.style.transform = 'scale(1.05)';
        element.style.transition = 'transform 0.2s ease';
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
    
    requestStatisticsUpdate() {
        if (window.tabManager && window.tabManager.getSocket()) {
            window.tabManager.getSocket().emit('request_statistics');
        }
    }
    
    refresh() {
        this.requestStatisticsUpdate();
    }
    
    subscribeToEvents() {
        const { eventBus } = window.__pdCore || {};
        if (!eventBus) return;
        eventBus.on('stats:update', data => this.updateStatistics(data));
    }
    
}

document.addEventListener('DOMContentLoaded', () => {
    window.statisticsManager = new StatisticsManager();
});
