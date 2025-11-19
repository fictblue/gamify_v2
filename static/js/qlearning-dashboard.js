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
        if (!ctx) {
            console.warn('User state chart element not found');
            return;
        }

        const stateDist = userStates.state_distribution || [];
        const transitionMatrix = userStates.transition_matrix || [];
        
        // Prepare data for the chart
        const labels = stateDist.map(item => item.state__state_type || 'Unknown');
        const data = stateDist.map(item => item.count || 0);
        const totalUsers = data.reduce((sum, count) => sum + count, 0);
        
        // Generate colors based on number of states
        const backgroundColors = [
            'rgba(54, 162, 235, 0.7)',  // Blue
            'rgba(255, 99, 132, 0.7)',  // Red
            'rgba(75, 192, 192, 0.7)',  // Teal
            'rgba(255, 206, 86, 0.7)',  // Yellow
            'rgba(153, 102, 255, 0.7)', // Purple
            'rgba(255, 159, 64, 0.7)'   // Orange
        ].slice(0, Math.max(labels.length, 1));

        if (this.charts.userStateChart) {
            this.charts.userStateChart.destroy();
        }
        
        // Create the chart
        this.charts.userStateChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.length > 0 ? labels : ['No Data'],
                datasets: [{
                    data: data.length > 0 ? data : [1],
                    backgroundColor: data.length > 0 ? backgroundColors : ['rgba(200, 200, 200, 0.7)'],
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Level Kemampuan Pengguna',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `Total Pengguna: ${totalUsers}`,
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const percentage = totalUsers > 0 ? ((value / totalUsers) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%',
                animation: {
                    animateScale: true,
                    animateRotate: true
                }
            }
        });
        
        // Update transition matrix if element exists
        this.updateTransitionMatrix(transitionMatrix);
    }

    // 3.1.1.b Analisis Action - Distribusi tingkat kesulitan
    updateActionDistributionChart(actionData) {
        const ctx = document.getElementById('actionDistributionChart');
        if (!ctx) {
            console.warn('Action distribution chart element not found');
            return;
        }

        const actions = actionData.actions || [];
        const explorationRate = actionData.exploration_rate || 0;
        const totalActions = actionData.total_actions || 0;
        
        // Prepare data for the chart
        const labels = actions.map(item => {
            // Convert action_chosen to more readable format
            const actionMap = {
                'easy': 'Mudah',
                'medium': 'Sedang',
                'hard': 'Sulit',
                'hint': 'Petunjuk',
                'explanation': 'Penjelasan',
                'skip': 'Lewati'
            };
            return actionMap[item.action_chosen] || item.action_chosen;
        });
        
        const data = actions.map(item => item.count || 0);
        
        // Generate colors - use a color scale based on difficulty
        const backgroundColors = actions.map(item => {
            switch(item.action_chosen) {
                case 'easy': return 'rgba(75, 192, 192, 0.7)';  // Teal
                case 'medium': return 'rgba(255, 206, 86, 0.7)'; // Yellow
                case 'hard': return 'rgba(255, 99, 132, 0.7)';  // Red
                case 'hint': return 'rgba(153, 102, 255, 0.7)'; // Purple
                default: return 'rgba(201, 203, 207, 0.7)';    // Gray
            }
        });

        if (this.charts.actionDistributionChart) {
            this.charts.actionDistributionChart.destroy();
        }
        
        // Create the chart
        this.charts.actionDistributionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.length > 0 ? labels : ['Tidak Ada Data'],
                datasets: [{
                    label: 'Jumlah Aksi',
                    data: data.length > 0 ? data : [0],
                    backgroundColor: data.length > 0 ? backgroundColors : ['rgba(200, 200, 200, 0.7)'],
                    borderColor: data.length > 0 ? 
                        backgroundColors.map(color => color.replace('0.7', '1')) : 
                        ['rgba(200, 200, 200, 1)'],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Tingkat Kesulitan yang Diberikan',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `Total Aksi: ${totalActions} | Tingkat Eksplorasi: ${(explorationRate * 100).toFixed(1)}%`,
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw || 0;
                                const percentage = totalActions > 0 ? ((value / totalActions) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Aksi',
                            font: {
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            precision: 0,
                            stepSize: 1
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tingkat Kesulitan',
                            font: {
                                weight: 'bold'
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // 3.1.1.c Analisis Reward
    updateRewardAnalysisChart(rewardData) {
        const ctx = document.getElementById('rewardAnalysisChart');
        if (!ctx) {
            console.warn('Reward analysis chart element not found');
            return;
        }

        const stats = rewardData.stats || {};
        const distribution = rewardData.distribution || [];
        
        // Prepare data for the chart
        const rewardValues = distribution.map(item => parseFloat(item.reward) || 0);
        const rewardCounts = distribution.map(item => item.count || 0);
        const totalRewards = stats.total_rewards || 0;
        
        // Generate colors based on reward value (red for negative, green for positive)
        const backgroundColors = rewardValues.map(value => {
            if (value > 0) {
                // Green gradient for positive rewards
                const intensity = Math.min(1, value / (stats.max_reward || 1));
                return `rgba(75, 192, 192, ${0.5 + (intensity * 0.5)})`;
            } else if (value < 0) {
                // Red gradient for negative rewards
                const intensity = Math.min(1, Math.abs(value) / (Math.abs(stats.min_reward) || 1));
                return `rgba(255, 99, 132, ${0.5 + (intensity * 0.5)})`;
            } else {
                // Gray for zero
                return 'rgba(201, 203, 207, 0.7)';
            }
        });
        
        // Sort rewards for better visualization
        const sortedIndices = rewardValues.map((_, i) => i)
            .sort((a, b) => rewardValues[a] - rewardValues[b]);
        
        const sortedLabels = sortedIndices.map(i => `Reward ${rewardValues[i]}`);
        const sortedData = sortedIndices.map(i => rewardCounts[i]);
        const sortedColors = sortedIndices.map(i => backgroundColors[i]);

        if (this.charts.rewardAnalysisChart) {
            this.charts.rewardAnalysisChart.destroy();
        }

        this.charts.rewardAnalysisChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedLabels.length > 0 ? sortedLabels : ['Tidak Ada Data'],
                datasets: [{
                    label: 'Jumlah Pemberian',
                    data: sortedData.length > 0 ? sortedData : [0],
                    backgroundColor: sortedColors.length > 0 ? sortedColors : ['rgba(200, 200, 200, 0.7)'],
                    borderColor: sortedColors.length > 0 ? 
                        sortedColors.map(color => color.replace('0.7', '1')) : 
                        ['rgba(200, 200, 200, 1)'],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribusi Reward yang Diberikan',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `Rata-rata: ${(stats.avg_reward || 0).toFixed(2)} | Total: ${totalRewards} reward`,
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw || 0;
                                const percentage = totalRewards > 0 ? ((value / totalRewards) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                const rewardValue = parseFloat(context.label.replace('Reward ', '')) || 0;
                                if (rewardValue > 0) {
                                    return 'Reward Positif: Mendorong perilaku yang diinginkan';
                                } else if (rewardValue < 0) {
                                    return 'Reward Negatif: Mengurangi perilaku yang tidak diinginkan';
                                } else {
                                    return 'Netral: Tidak mempengaruhi perilaku';
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Pemberian',
                            font: {
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            precision: 0,
                            stepSize: 1
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Nilai Reward',
                            font: {
                                weight: 'bold'
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // 3.1.1.d Analisis Q-Table - Visualisasi nilai Q terpilih
    updateQTableHeatmap(qtableData) {
        const ctx = document.getElementById('qTableHeatmap');
        if (!ctx) {
            console.warn('Q-Table heatmap element not found');
            return;
        }

        const stats = qtableData.stats || {};
        const topActions = qtableData.top_actions || [];
        
        // Prepare data for the heatmap
        const heatmapData = topActions.map(item => ({
            x: item.state_hash ? `${item.state_hash.substring(0, 6)}...` : 'Unknown',
            y: item.action || 'Unknown',
            v: parseFloat(item.q_value) || 0
        }));
        
        // If no data, show a single cell with "No Data"
        if (heatmapData.length === 0) {
            heatmapData.push({ x: 'No Data', y: 'No Data', v: 0 });
        }
        
        // Get min/max values for color scaling
        const maxAbsValue = Math.max(
            Math.abs(stats.max_q || 1), 
            Math.abs(stats.min_q || 1)
        );

        if (this.charts.qTableHeatmap) {
            this.charts.qTableHeatmap.destroy();
        }
        
        // Create the heatmap
        this.charts.qTableHeatmap = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Nilai Q',
                    data: heatmapData,
                    backgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex].v;
                        const alpha = Math.min(1, Math.abs(value) / (maxAbsValue || 1));
                        return value >= 0 
                            ? `rgba(75, 192, 192, ${0.3 + (alpha * 0.7)})` 
                            : `rgba(255, 99, 132, ${0.3 + (alpha * 0.7)})`;
                    },
                    borderWidth: 1,
                    borderColor: 'rgba(0, 0, 0, 0.1)',
                    width: ({ chart }) => (chart.chartArea || {}).width / Math.min(10, heatmapData.length || 1) - 1 || 0,
                    height: ({ chart }) => (chart.chartArea || {}).height / Math.min(10, heatmapData.length || 1) - 1 || 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function() {
                                return 'Nilai Q';
                            },
                            label: function(context) {
                                const v = context.dataset.data[context.dataIndex];
                                if (v.x === 'No Data' && v.y === 'No Data') {
                                    return ['Tidak ada data yang tersedia'];
                                }
                                return [
                                    `State: ${v.x}`,
                                    `Aksi: ${v.y}`,
                                    `Nilai: ${v.v.toFixed(4)}`
                                ];
                            },
                            afterLabel: function(context) {
                                const v = context.dataset.data[context.dataIndex];
                                if (v.v > 0) {
                                    return 'Nilai positif: Aksi yang diinginkan untuk state ini';
                                } else if (v.v < 0) {
                                    return 'Nilai negatif: Hindari aksi ini untuk state ini';
                                } else if (v.v === 0) {
                                    return 'Nilai netral: Tidak ada preferensi untuk aksi ini';
                                }
                                return '';
                            }
                        }
                    },
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Nilai Q untuk State-Action Pairs',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `Rata-rata: ${(stats.avg_q || 0).toFixed(2)} | Entri: ${stats.total_entries || 0}`,
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        offset: true,
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'State (Hash)',
                            font: {
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            display: true,
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'category',
                        offset: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Aksi',
                            font: {
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            display: true
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // 3.1.2 Validasi & Umpan Balik
    updateValidationCharts(validationData) {
        console.log('Validation data received:', validationData);
        
        // Check if containers exist
        const expertChartEl = document.getElementById('expertValidationChart');
        const feedbackChartEl = document.getElementById('userFeedbackChart');
        
        console.log('Expert chart element:', expertChartEl);
        console.log('Feedback chart element:', feedbackChartEl);
        
        // Update user feedback chart with satisfaction data
        if (validationData.satisfaction || validationData.feedback_distribution) {
            console.log('Updating user feedback chart with data:', validationData);
            this.updateUserFeedbackChart(validationData);
        } else {
            console.warn('No user feedback data available');
        }
        
        // Since we don't have expert validation data, we'll show a message
        if (expertChartEl) {
            expertChartEl.parentElement.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-chart-line fa-3x text-muted mb-2"></i>
                    <h6>Expert Validation Data</h6>
                    <p class="small text-muted">No expert validation data available</p>
                </div>
            `;
        }
    }

    /**
     * 3.1.2.a Update Expert Validation Chart
     * Shows expert validation metrics in a radar chart with detailed scoring
     */
    updateExpertValidationChart(validationData) {
        console.log('Initializing expert validation chart...');
        const ctx = document.getElementById('expertValidationChart');
        if (!ctx) {
            console.error('Expert validation chart element not found');
            return;
        }
        
        // Ensure Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }
        
        // Default metrics with descriptions
        const defaultMetrics = [
            { 
                id: 'level_appropriateness',
                name: 'Kesesuaian Level',
                description: 'Tingkat kesesuaian level materi dengan kemampuan pengguna',
                weight: 1.2
            },
            { 
                id: 'content_relevance',
                name: 'Relevansi Materi',
                description: 'Keterkaitan materi dengan tujuan pembelajaran',
                weight: 1.1
            },
            { 
                id: 'difficulty',
                name: 'Tingkat Kesulitan',
                description: 'Tingkat kesesuaian tingkat kesulitan dengan target pengguna',
                weight: 1.0
            },
            { 
                id: 'feedback_quality',
                name: 'Kualitas Umpan Balik',
                description: 'Kualitas dan kebermanfaatan umpan balik yang diberikan',
                weight: 1.1
            },
            { 
                id: 'adaptation_effectiveness',
                name: 'Efektivitas Adaptasi',
                description: 'Tingkat keberhasilan sistem dalam beradaptasi',
                weight: 1.3
            },
            { 
                id: 'engagement',
                name: 'Tingkat Keterlibatan',
                description: 'Tingkat keterlibatan pengguna dengan sistem',
                weight: 1.0
            }
        ];
        
        // Process validation data
        const metrics = validationData.metrics || [];
        const labels = [];
        const scores = [];
        const backgroundColors = [];
        const descriptions = [];
        const weights = [];
        
        // Use actual data if available, otherwise use defaults with zero scores
        defaultMetrics.forEach(metric => {
            const metricData = metrics.find(m => m.id === metric.id) || { score: 0 };
            labels.push(metric.name);
            scores.push(metricData.score || 0);
            descriptions.push(metric.description);
            weights.push(metric.weight);
            
            // Generate color based on score (red to green gradient)
            const hue = (metricData.score / 5) * 120; // 0 (red) to 120 (green)
            backgroundColors.push(`hsla(${hue}, 70%, 60%, 0.6)`);
        });
        
        // Calculate weighted average score
        const totalScore = scores.reduce((sum, score, index) => 
            sum + (score * weights[index]), 0);
        const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
        const avgScore = totalWeight > 0 ? (totalScore / totalWeight).toFixed(1) : 0;

        // Destroy existing chart if it exists
        if (this.charts.expertValidationChart) {
            this.charts.expertValidationChart.destroy();
        }
        
        // Create the enhanced radar chart
        this.charts.expertValidationChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Skor Validasi',
                    data: scores,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    pointBackgroundColor: backgroundColors,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(75, 192, 192, 1)',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Hasil Validasi Ahli',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `Rata-rata Skor: ${avgScore}/5.0`,
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw}/5.0`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        pointLabels: {
                            font: {
                                size: 11
                            }
                        },
                        min: 0,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            display: false
                        },
                        suggestedMin: 0,
                        suggestedMax: 5
                    }
                },
                elements: {
                    line: {
                        borderWidth: 2
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    updateUserFeedbackChart(validationData) {
        console.log('Initializing user feedback chart...');
        const ctx = document.getElementById('userFeedbackChart');
        if (!ctx) {
            console.error('User feedback chart element not found');
            return;
        }
        
        // Ensure Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }

        // Get satisfaction data with defaults
        const satisfaction = {
            average_rating: validationData.satisfaction?.average_rating || 0,
            total_responses: validationData.satisfaction?.total_responses || 0,
            ...validationData.satisfaction
        };
        
        // Process feedback distribution
        const feedbackDist = Array.isArray(validationData.feedback_distribution) 
            ? validationData.feedback_distribution 
            : [];
            
        // If no feedback data, show a message
        if (satisfaction.total_responses === 0 && feedbackDist.length === 0) {
            ctx.parentElement.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-comment-alt fa-3x text-muted mb-2"></i>
                    <h6>User Feedback</h6>
                    <p class="small text-muted">No feedback data available yet</p>
                </div>
            `;
            return;
        }
        
        // Prepare data for the chart
        const ratingLabels = ['1 Bintang', '2 Bintang', '3 Bintang', '4 Bintang', '5 Bintang'];
        const ratingData = Array(5).fill(0);
        
        feedbackDist.forEach(item => {
            const rating = item.satisfaction_rating - 1; // Convert to 0-based index
            if (rating >= 0 && rating < 5) {
                ratingData[rating] = item.count || 0;
            }
        });
        
        const totalResponses = satisfaction.total_responses || 0;
        const avgSatisfaction = satisfaction.avg_satisfaction ? 
            parseFloat(satisfaction.avg_satisfaction).toFixed(1) : 0;
            
        const avgDifficulty = satisfaction.avg_difficulty ? 
            parseFloat(satisfaction.avg_difficulty).toFixed(1) : 0;

        // Generate colors from red to green
        const backgroundColors = [
            'rgba(255, 99, 132, 0.7)',   // Red
            'rgba(255, 159, 64, 0.7)',   // Orange
            'rgba(255, 206, 86, 0.7)',   // Yellow
            'rgba(54, 162, 235, 0.7)',   // Blue
            'rgba(75, 192, 192, 0.7)'    // Green
        ];

        if (this.charts.userFeedbackChart) {
            this.charts.userFeedbackChart.destroy();
        }
        
        // Create the pie/donut chart
        this.charts.userFeedbackChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ratingLabels,
                datasets: [{
                    data: ratingData,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                    borderWidth: 1,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tingkat Kepuasan Pengguna',
                        font: {
                            size: 14
                        }
                    },
                    subtitle: {
                        display: true,
                        text: [
                            `Rata-rata: ${avgSatisfaction}/5.0`,
                            `Tingkat Kesulitan: ${avgDifficulty}/5.0`
                        ],
                        font: {
                            style: 'italic',
                            size: 12
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const percentage = totalResponses > 0 ? 
                                    ((value / totalResponses) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                const rating = parseInt(context.label) || 0;
                                const comments = [
                                    'Sangat Tidak Puas',
                                    'Tidak Puas',
                                    'Netral',
                                    'Puas',
                                    'Sangat Puas'
                                ];
                                return comments[rating - 1] || '';
                            }
                        }
                    }
                },
                cutout: '60%',
                animation: {
                    animateScale: true,
                    animateRotate: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * 2.1.4.3 Update adaptation response chart
     * @param {Object} adaptationData - The adaptation response data
     */
    updateAdaptationResponseChart(adaptationData) {
        const ctx = document.getElementById('adaptationResponseChart');
        if (!ctx) {
            console.error('Adaptation response chart element not found');
            return;
        }

        // Destroy existing chart if it exists
        if (this.charts.adaptationResponse) {
            this.charts.adaptationResponse.destroy();
        }

        // Use real data from API
        const labels = adaptationData.labels || [];
        const beforeData = adaptationData.before_adaptation || [];
        const afterData = adaptationData.after_adaptation || [];
        const effectivenessRates = adaptationData.effectiveness_rates || [];

        // If no data, show a message
        if (labels.length === 0) {
            labels.push('No Data Available');
            beforeData.push(0);
            afterData.push(0);
            effectivenessRates.push(0);
        }

        this.charts.adaptationResponse = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sebelum Adaptasi',
                        data: beforeData,
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Setelah Adaptasi',
                        data: afterData,
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Efektivitas (%)',
                        data: effectivenessRates,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        type: 'line',
                        yAxisID: 'y1',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Performa (Q-Value)'
                        },
                        max: 1.0,
                        position: 'left'
                    },
                    y1: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Efektivitas (%)'
                        },
                        max: 100,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Respon Adaptasi Sistem Q-Learning'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (context.dataset.label.includes('%')) {
                                        label += context.parsed.y.toFixed(1) + '%';
                                    } else {
                                        label += context.parsed.y.toFixed(3);
                                    }
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    updateQLearningPerformanceChart(qLearningData) {
        const ctx = document.getElementById('qLearningPerformanceChart');
        if (!ctx) return;

        const labels = qLearningData.labels || [];
        const qValues = qLearningData.q_values || [];
        const bestQValues = qLearningData.best_q_values || [];
        const explorationRates = qLearningData.exploration_rates || [];
        const learningRates = qLearningData.learning_rates || [];

        if (labels.length === 0) {
            labels.push('No Data Available');
            qValues.push(0);
            bestQValues.push(0);
            explorationRates.push(0);
            learningRates.push(0);
        }

        if (this.charts.qLearningPerformance) {
            this.charts.qLearningPerformance.destroy();
        }

        this.charts.qLearningPerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Q-Value Rata-rata',
                        data: qValues,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Q-Value Terbaik',
                        data: bestQValues,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Tingkat Eksplorasi',
                        data: explorationRates,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Q-Value'
                        },
                        max: 1.0
                    },
                    y1: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tingkat Eksplorasi'
                        },
                        max: 1.0,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Kinerja Q-Learning'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    updateUserStateChart(userStateData) {
        const ctx = document.getElementById('userStateChart');
        if (!ctx) return;

        const stateDistribution = userStateData.state_distribution || [];
        const totalUsers = userStateData.total_users || 0;

        if (stateDistribution.length === 0) {
            stateDistribution.push({ state: 'No Data', count: 0, percentage: 100 });
        }

        if (this.charts.userState) {
            this.charts.userState.destroy();
        }

        this.charts.userState = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: stateDistribution.map(s => s.state),
                datasets: [{
                    data: stateDistribution.map(s => s.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Analisis State Pengguna (Total: ${totalUsers})`
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateDashboard(data) {
        try {
            if (!data) {
                console.warn('No data received from server');
                return;
            }

            console.log('Updating dashboard with data:', data);

            // 2.1.4.1 Keterlibatan Pengguna
            if (data.user_engagement) {
                console.log('Updating user engagement chart');
                this.updateEngagementChart(data.user_engagement);
            }

            // 2.1.4.2 Tingkat Keberhasilan
            if (data.success_rates) {
                console.log('Updating success rate chart');
                this.updateSuccessRateChart(data.success_rates);
            }

            // 2.1.4.3 Respon Adaptasi
            if (data.adaptation) {
                console.log('Updating adaptation response chart');
                this.updateAdaptationResponseChart(data.adaptation);
            }

            // 2.1.4.4 Kinerja Q-Learning
            if (data.q_learning) {
                console.log('Updating Q-Learning performance chart');
                this.updateQLearningPerformanceChart(data.q_learning);
            }

            // 3.1.1.a Analisis State
            if (data.user_states) {
                console.log('Updating user state analysis');
                this.updateUserStateChart(data.user_states);
            }

            // 3.1.1.b Analisis Action
            if (data.action_distribution) {
                console.log('Updating action distribution chart');
                this.updateActionDistributionChart(data.action_distribution);
            }
            
            // 3.1.1.c Analisis Reward
            if (data.reward_analysis) {
                console.log('Updating reward analysis chart');
                this.updateRewardAnalysisChart(data.reward_analysis);
            }
            
            // 3.1.1.d Analisis Q-Table
            if (data.qtable_analysis) {
                console.log('Updating Q-Table heatmap');
                this.updateQTableHeatmap(data.qtable_analysis);
            }
            
            // 3.1.2 Validasi & Umpan Balik
            if (data.validation) {
                console.log('Updating validation charts');
                this.updateValidationCharts(data.validation);
            }
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }

    // 2.1.4.1 Keterlibatan Pengguna
    updateEngagementChart(engagementData) {
        const ctx = document.getElementById('engagementChart');
        if (!ctx) {
            console.warn('Engagement chart element not found');
            return;
        }

        const dailyData = engagementData.daily_active_users || [];
        const labels = dailyData.map(item => item.date || 'N/A');
        const data = dailyData.map(item => item.count || 0);
        
        // Get session duration data if available
        const sessionData = engagementData.session_duration || {};
        const avgSessionDuration = sessionData.avg_duration ? (sessionData.avg_duration / 60).toFixed(1) : 0;
        
        // Update session duration display
        const durationElement = document.getElementById('avgSessionDuration');
        if (durationElement) {
            durationElement.textContent = `${avgSessionDuration} menit`;
        }

        if (this.charts.engagementChart) {
            this.charts.engagementChart.destroy();
        }

        this.charts.engagementChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Pengguna Aktif Harian',
                    data: data,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Keterlibatan Pengguna Harian'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Jumlah Pengguna'
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
