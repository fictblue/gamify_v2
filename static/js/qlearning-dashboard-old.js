// Q-Learning Dashboard Visualization
// Check if QLearningDashboard is not already defined
if (typeof QLearningDashboard === 'undefined') {
    window.QLearningDashboard = class QLearningDashboard {
    constructor() {
        this.charts = {};
        this.timeRange = 30; // days
        this.initEventListeners();
        this.loadMetrics();
        setInterval(() => this.loadMetrics(), 300000); // Update every 5 minutes
    }

    initEventListeners() {
        // Time range selector
        document.querySelectorAll('.time-range-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.timeRange = parseInt(e.target.dataset.days);
                document.querySelectorAll('.time-range-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.loadMetrics();
            });
        });
    }

    async loadMetrics() {
        try {
            const response = await fetch(`/qlearning/api/metrics/?days=${this.timeRange}`);
            const data = await response.json();
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    // 2.1.4.4 Kinerja Q-Learning
    updateQLearningPerformanceChart(qLearningData) {
        const ctx = document.getElementById('qLearningPerformanceChart');
        if (!ctx) return;

        const labels = qLearningData.labels || [];
        const qValues = qLearningData.q_values || [];
        const learningRates = qLearningData.learning_rates || [];
        const explorationRates = qLearningData.exploration_rates || [];

        if (this.charts.qLearningPerformanceChart) {
            this.charts.qLearningPerformanceChart.destroy();
        }

        this.charts.qLearningPerformanceChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Nilai Q Rata-rata',
                        data: qValues,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Tingkat Eksplorasi',
                        data: explorationRates,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Kinerja Algoritma Q-Learning'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(4);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Nilai Q Rata-rata'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                        title: {
                            display: true,
                            text: 'Tingkat Eksplorasi'
                        },
                        min: 0,
                        max: 1
                    }
                }
            }
        });
    }

    // 3.1.1.a Analisis State - Distribusi level kemampuan pengguna
    updateUserStateChart(userStates) {
        const ctx = document.getElementById('userStateChart');
        if (!ctx) return;

        const labels = Object.keys(userStates);
        const data = Object.values(userStates);
        const backgroundColors = [
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 205, 86, 0.6)',
            'rgba(153, 102, 255, 0.6)'
        ];

        if (this.charts.userStateChart) {
            this.charts.userStateChart.destroy();
        }

        this.charts.userStateChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Level Kemampuan Pengguna'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // 3.1.1.b Analisis Action - Distribusi tingkat kesulitan
    updateActionDistributionChart(actionData) {
        const ctx = document.getElementById('actionDistributionChart');
        if (!ctx) return;

        const labels = Object.keys(actionData);
        const data = Object.values(actionData);

        if (this.charts.actionDistributionChart) {
            this.charts.actionDistributionChart.destroy();
        }

        this.charts.actionDistributionChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Jumlah Aksi',
                    data: data,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Tingkat Kesulitan yang Diberikan'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Aksi'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tingkat Kesulitan'
                        }
                    }
                }
            }
        });
    }

    // 3.1.1.c Analisis Reward - Distribusi reward
    updateRewardAnalysisChart(rewardData) {
        const ctx = document.getElementById('rewardAnalysisChart');
        if (!ctx) return;

        const labels = Object.keys(rewardData);
        const data = Object.values(rewardData);

        if (this.charts.rewardAnalysisChart) {
            this.charts.rewardAnalysisChart.destroy();
        }

        this.charts.rewardAnalysisChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Jumlah Reward',
                    data: data,
                    backgroundColor: 'rgba(255, 159, 64, 0.6)',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Reward yang Diberikan'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tipe Reward'
                        }
                    }
                }
            }
        });
    }

    // 3.1.1.d Analisis Q-Table - Visualisasi nilai Q terpilih
    updateQTableHeatmap(qTableData) {
        const ctx = document.getElementById('qTableHeatmap');
        if (!ctx) return;

        // Prepare data for heatmap
        const states = Object.keys(qTableData);
        const actions = new Set();
        
        // Get all unique actions
        states.forEach(state => {
            Object.keys(qTableData[state]).forEach(action => {
                actions.add(action);
            });
        });
        
        const actionList = Array.from(actions);
        const data = [];
        
        // Create data matrix
        states.forEach(state => {
            const row = [];
            actionList.forEach(action => {
                row.push(qTableData[state][action] || 0);
            });
            data.push({
                x: state,
                y: row
            });
        });

        if (this.charts.qTableHeatmap) {
            this.charts.qTableHeatmap.destroy();
        }

        this.charts.qTableHeatmap = new Chart(ctx.getContext('2d'), {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Nilai Q',
                    data: data,
                    backgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex].y[context.column];
                        const alpha = Math.min(0.9, Math.abs(value) * 0.8 + 0.1);
                        return value < 0 ? 
                            `rgba(255, 99, 132, ${alpha})` : 
                            `rgba(75, 192, 192, ${alpha})`;
                    },
                    borderWidth: 1,
                    borderColor: 'rgba(0, 0, 0, 0.1)',
                    width: ({chart}) => (chart.chartArea || {}).width / actionList.length - 1,
                    height: ({chart}) => (chart.chartArea || {}).height / states.length - 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `State: ${context[0].label}`;
                            },
                            label: function(context) {
                                return `Aksi: ${actionList[context.dataIndex]}, Nilai Q: ${context.raw.y[context.dataIndex].toFixed(4)}`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Visualisasi Nilai Q-Table'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: actionList,
                        offset: true,
                        ticks: {
                            display: true
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'category',
                        labels: states,
                        offset: true,
                        ticks: {
                            display: true
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // 3.1.2 Validasi & Umpan Balik
    updateValidationCharts(validationData) {
        // Update expert validation chart
        if (validationData.expert_validation) {
            this.updateExpertValidationChart(validationData.expert_validation);
        }
        
        // Update user feedback chart
        if (validationData.user_feedback) {
            this.updateUserFeedbackChart(validationData.user_feedback);
        }
    }

    updateExpertValidationChart(validationData) {
        const ctx = document.getElementById('expertValidationChart');
        if (!ctx) return;

        const labels = Object.keys(validationData);
        const data = Object.values(validationData);

        if (this.charts.expertValidationChart) {
            this.charts.expertValidationChart.destroy();
        }

        this.charts.expertValidationChart = new Chart(ctx.getContext('2d'), {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nilai Validasi',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Hasil Validasi Ahli'
                    },
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        suggestedMin: 0,
                        suggestedMax: 5
                    }
                }
            }
        });
    }

    updateUserFeedbackChart(feedbackData) {
        const ctx = document.getElementById('userFeedbackChart');
        if (!ctx) return;

        const labels = Object.keys(feedbackData);
        const data = Object.values(feedbackData);

        if (this.charts.userFeedbackChart) {
            this.charts.userFeedbackChart.destroy();
        }

        this.charts.userFeedbackChart = new Chart(ctx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(255, 205, 86, 0.6)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(153, 102, 255, 0.6)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 205, 86, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Respon Pengguna'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
    // 2.1.4.1 Keterlibatan Pengguna
    updateEngagementChart(data) {
        const ctx = document.getElementById('engagementChart');
        if (!ctx) return;
        
        const labels = data.map(item => item.date);
        const loginCounts = data.map(item => item.login_count);
        const questionCounts = data.map(item => item.questions_answered);
        const sessionDurations = data.map(item => item.avg_session_duration);
        
        if (this.charts.engagementChart) {
            this.charts.engagementChart.destroy();
        }

        this.charts.engagementChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Jumlah Login',
                        data: loginCounts,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y',
                        tension: 0.3
                    },
                    {
                        label: 'Soal Dijawab',
                        data: questionCounts,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y1',
                        tension: 0.3
                    },
                    {
                        label: 'Durasi Rata-rata (menit)',
                        data: sessionDurations,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y2',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Jumlah Login' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Soal Dijawab' }
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        offset: true,
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Durasi (menit)' }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (label.includes('Durasi')) {
                                        label += context.parsed.y.toFixed(1) + ' menit';
                                    } else {
                                        label += context.parsed.y;
                                    }
                                }
                                return label;
                            }
                        }
                    },
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: 0,
                                yMax: 0,
                                borderColor: 'rgb(255, 99, 132)',
                                borderWidth: 2,
                                borderDash: [6, 6],
                            }
                        }
                    }
                },
                maintainAspectRatio: false,
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const index = context.dataIndex;
                            return `Level: ${context.raw.toFixed(2)} (${data[index].count} siswa)`;
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Level Pembelajaran Rata-rata'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tanggal'
                        }
                    }
                }
            }
        });
    }

    updateStateDistributionChart(data) {
        const ctx = document.getElementById('stateDistributionChart').getContext('2d');
        const labels = data.map(item => `State ${item.state}`);
        const values = data.map(item => item.count);
        const avgQValues = data.map(item => item.avg_q_value);

        if (this.charts.stateDistribution) {
            this.charts.stateDistribution.destroy();
        }

        this.charts.stateDistribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Jumlah State',
                    data: values,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Nilai Q Rata-rata',
                    data: avgQValues,
                    type: 'line',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi State Q-Learning'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                if (context.datasetIndex === 0) {
                                    return `Jumlah: ${context.raw}`;
                                } else {
                                    return `Nilai Q: ${context.raw.toFixed(4)}`;
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Jumlah State'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Nilai Q Rata-rata'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'State'
                        }
                    }
                }
            }
        });
    }

    updateEngagementChart(data) {
        const ctx = document.getElementById('engagementChart').getContext('2d');
        const labels = data.map(item => item.date);
        const values = data.map(item => item.count);

        if (this.charts.engagement) {
            this.charts.engagement.destroy();
        }

        this.charts.engagement = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Pengguna Aktif Harian',
                    data: values,
                    backgroundColor: 'rgba(153, 102, 255, 0.6)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tingkat Keterlibatan Pengguna'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.raw} pengguna aktif`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Pengguna'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tanggal'
                        }
                    }
                }
            }
        });
    }

    updateSuccessRateChart(data) {
        const ctx = document.getElementById('successRateChart');
        if (!ctx) {
            console.error('Success rate chart element not found');
            return;
        }
        
        // Ensure data is an array and has items
        if (!Array.isArray(data) || data.length === 0) {
            console.warn('No success rate data available');
            // Optionally show a message or placeholder
            ctx.parentElement.innerHTML = '<p class="text-muted">Tidak ada data kinerja kuis yang tersedia</p>';
            return;
        }

        const labels = data.map(item => {
            const level = item.question__difficulty || 'Unknown';
            return level.charAt(0).toUpperCase() + level.slice(1);
        });
        
        const successRates = data.map(item => {
            const rate = parseFloat(item.success_rate) || 0;
            return Math.min(100, Math.max(0, rate)); // Ensure rate is between 0-100
        });
        
        const totalAttempts = data.map(item => parseInt(item.total) || 0);

        if (this.charts.successRate) {
            this.charts.successRate.destroy();
        }

        this.charts.successRate = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tingkat Keberhasilan (%)',
                    data: successRates,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Total Percobaan',
                    data: totalAttempts,
                    type: 'line',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tingkat Keberhasilan Berdasarkan Tingkat Kesulitan'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const index = context.dataIndex;
                                return `Total Percobaan: ${totalAttempts[index]}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Tingkat Keberhasilan (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Total Percobaan'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tingkat Kesulitan'
                        }
                    }
                }
            }
        });
    }

    updateTransitionMatrix(transitions) {
        const ctx = document.getElementById('transitionMatrixChart');
        if (!ctx) return;
        
        // Create a matrix from transitions
        const states = new Set();
        transitions.forEach(t => {
            states.add(t.from);
            states.add(t.to);
        });
        
        const stateList = Array.from(states).sort();
        const matrix = Array(stateList.length).fill().map(() => Array(stateList.length).fill(0));
        
        transitions.forEach(t => {
            const fromIdx = stateList.indexOf(t.from);
            const toIdx = stateList.indexOf(t.to);
            if (fromIdx >= 0 && toIdx >= 0) {
                matrix[fromIdx][toIdx] = t.count;
            }
        });

        // Normalize for better visualization
        const maxVal = Math.max(...matrix.flat());
        const normalizedMatrix = matrix.map(row => 
            row.map(val => maxVal > 0 ? (val / maxVal) * 100 : 0)
        );

        if (this.charts.transitionMatrix) {
            this.charts.transitionMatrix.destroy();
        }

        this.charts.transitionMatrix = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    data: (() => {
                        const result = [];
                        // Initialize matrix with zeros if not already done
                        if (!matrix || !Array.isArray(matrix)) {
                            matrix = Array(stateList.length).fill().map(() => Array(stateList.length).fill(0));
                        }
                        
                        for (let i = 0; i < stateList.length; i++) {
                            for (let j = 0; j < stateList.length; j++) {
                                // Ensure we have a valid number
                                const value = matrix[i] && matrix[i][j] ? matrix[i][j] : 0;
                                result.push({
                                    x: stateList[j],
                                    y: stateList[i],
                                    v: value
                                });
                            }
                        }
                        return result;
                    })(),
                    backgroundColor: (context) => {
                        try {
                            const dataPoint = context.dataset.data[context.dataIndex];
                            if (!dataPoint || typeof dataPoint.v === 'undefined' || dataPoint.v === null) {
                                return 'rgba(200, 200, 200, 0.1)'; // Default color for missing data
                            }
                            const value = Number(dataPoint.v) || 0;
                            const alpha = maxVal > 0 ? (value / maxVal * 0.8) + 0.2 : 0.2; // Ensure minimum visibility
                            return `rgba(54, 162, 235, ${alpha})`;
                        } catch (e) {
                            console.error('Error in backgroundColor function:', e);
                            return 'rgba(200, 200, 200, 0.1)';
                        }
                    },
                    borderWidth: 1,
                    borderColor: '#fff',
                    width: ({ chart }) => (chart.chartArea || {}).width / stateList.length - 1 || 0,
                    height: ({ chart }) => (chart.chartArea || {}).height / stateList.length - 1 || 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: () => '',
                            label: (context) => {
                                const v = context.dataset.data[context.dataIndex];
                                return [
                                    `Dari: State ${v.y}`,
                                    `Ke: State ${v.x}`,
                                    `Jumlah: ${v.v} transisi`
                                ];
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Matriks Transisi State'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: stateList,
                        offset: true,
                        title: {
                            display: true,
                            text: 'State Tujuan'
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'category',
                        labels: stateList,
                        offset: true,
                        title: {
                            display: true,
                            text: 'State Asal'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    updateSystemHealth(healthData) {
        // Update recent errors
        const errorsList = document.getElementById('recentErrorsList');
        if (errorsList) {
            errorsList.innerHTML = healthData.recent_errors
                .map(error => `
                    <div class="error-item">
                        <span class="error-message">${error.error_message}</span>
                        <span class="error-count">${error.count}x</span>
                    </div>
                `)
                .join('') || '<div class="text-muted">Tidak ada error dalam 24 jam terakhir</div>';
        }

        // Update request stats chart
        const ctx = document.getElementById('requestStatsChart');
        if (!ctx) return;

        const labels = healthData.request_stats.map(stat => `${stat.hour}:00`);
        const values = healthData.request_stats.map(stat => stat.count);

        if (this.charts.requestStats) {
            this.charts.requestStats.destroy();
        }

        this.charts.requestStats = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Permintaan per Jam',
                    data: values,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tren Permintaan Sistem'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Permintaan'
                        },
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Jam'
                        }
                    }
                }
            }
        });
    }

    updateTransitionMatrix(transitions) {
        const ctx = document.getElementById('transitionMatrixChart');
        if (!ctx) return;

        // Get unique states from transitions
        const states = new Set();
        transitions.forEach(t => {
            states.add(t.from);
            states.add(t.to);
        });
        
        const stateList = Array.from(states).sort();
        const matrix = Array(stateList.length).fill().map(() => Array(stateList.length).fill(0));
        
        // Populate transition matrix
        transitions.forEach(t => {
            const fromIdx = stateList.indexOf(t.from);
            const toIdx = stateList.indexOf(t.to);
            if (fromIdx >= 0 && toIdx >= 0) {
                matrix[fromIdx][toIdx] = (matrix[fromIdx][toIdx] || 0) + (t.count || 1);
            }
        });

        // Normalize for better visualization
        const maxVal = Math.max(...matrix.flat());
        const normalizedMatrix = matrix.map(row => 
            row.map(val => maxVal > 0 ? (val / maxVal) * 100 : 0)
        );

        if (this.charts.transitionMatrix) {
            this.charts.transitionMatrix.destroy();
        }

    this.charts.transitionMatrix = new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                data: (() => {
                    const result = [];
                    // Initialize matrix with zeros if not already done
                    if (!matrix || !Array.isArray(matrix)) {
                        matrix = Array(stateList.length).fill().map(() => Array(stateList.length).fill(0));
                    }
                    
                    for (let i = 0; i < stateList.length; i++) {
                        for (let j = 0; j < stateList.length; j++) {
                            // Ensure we have a valid number
                            const value = matrix[i] && matrix[i][j] ? matrix[i][j] : 0;
                            result.push({
                                x: stateList[j],
                                y: stateList[i],
                                v: value
                            });
                        }
                    }
                    return result;
                })(),
                backgroundColor: (context) => {
                    try {
                        const dataPoint = context.dataset.data[context.dataIndex];
                        if (!dataPoint || typeof dataPoint.v === 'undefined' || dataPoint.v === null) {
                            return 'rgba(200, 200, 200, 0.1)'; // Default color for missing data
                        }
                        const value = Number(dataPoint.v) || 0;
                        const alpha = maxVal > 0 ? (value / maxVal * 0.8) + 0.2 : 0.2; // Ensure minimum visibility
                        return `rgba(54, 162, 235, ${alpha})`;
                    } catch (e) {
                        console.error('Error in backgroundColor function:', e);
                        return 'rgba(200, 200, 200, 0.1)';
                    }
                },
                borderWidth: 1,
                borderColor: '#fff',
                width: ({ chart }) => (chart.chartArea || {}).width / stateList.length - 1 || 0,
                height: ({ chart }) => (chart.chartArea || {}).height / stateList.length - 1 || 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        title: () => '',
                        label: (context) => {
                            const v = context.dataset.data[context.dataIndex];
                            return [
                                `Dari: State ${v.y}`,
                                `Ke: State ${v.x}`,
                                `Jumlah: ${v.v} transisi`
                            ];
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Matriks Transisi State'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: stateList,
                    offset: true,
                    title: {
                        display: true,
                        text: 'State Tujuan'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: stateList,
                    offset: true,
                    title: {
                        display: true,
                        text: 'State Asal'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

updateSystemHealth(healthData) {
    // Update recent errors
    const errorsList = document.getElementById('recentErrorsList');
    if (errorsList) {
        errorsList.innerHTML = healthData.recent_errors
            .map(error => `
                <div class="error-item">
                    <span class="error-message">${error.error_message}</span>
                    <span class="error-count">${error.count}x</span>
                </div>
            `)
            .join('') || '<div class="text-muted">Tidak ada error dalam 24 jam terakhir</div>';
    }

    // Update request stats chart
    const ctx = document.getElementById('requestStatsChart');
    if (!ctx) return;

    const labels = healthData.request_stats.map(stat => `${stat.hour}:00`);
    const values = healthData.request_stats.map(stat => stat.count);

    if (this.charts.requestStats) {
        this.charts.requestStats.destroy();
    }

    this.charts.requestStats = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Permintaan per Jam',
                data: values,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Tren Permintaan Sistem'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Jumlah Permintaan'
                    },
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Jam'
                    }
                }
            }
        }
    });
}
    };
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the dashboard page
    const metricsSection = document.querySelector('.qlearning-metrics-section');
    if (metricsSection) {
        try {
            // Check if already initialized
            if (!window.qLearningDashboard) {
                window.qLearningDashboard = new QLearningDashboard();
            }
        } catch (error) {
            console.error('Error initializing QLearningDashboard:', error);
        }
    }
});
