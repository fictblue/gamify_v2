// Admin Dashboard Charts Configuration
document.addEventListener('DOMContentLoaded', function() {
    // Chart.js Configuration
    const chartColors = {
        primary: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),
        secondary: getComputedStyle(document.documentElement).getPropertyValue('--secondary').trim(),
        success: getComputedStyle(document.documentElement).getPropertyValue('--success').trim(),
        warning: getComputedStyle(document.documentElement).getPropertyValue('--warning').trim(),
        error: getComputedStyle(document.documentElement).getPropertyValue('--error').trim(),
    };

    // User Growth Chart
    const userGrowthCtx = document.getElementById('userGrowthChart');
    let userGrowthChart = null;
    
    // Function to update the chart with new data
    function updateUserGrowthChart(range = 'week') {
        const chartContainer = document.querySelector('.user-growth-container');
        const loadingIndicator = document.getElementById('userGrowthLoading');
        const errorMessage = document.getElementById('userGrowthError');
        
        // Show loading state
        chartContainer.classList.add('loading');
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (errorMessage) errorMessage.style.display = 'none';
        
        // Fetch data from the API
        fetch(`/dashboard/api/user-growth/?range=${range}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if (!data.success) throw new Error('Failed to load data');
                
                const chartData = data.data;
                const dataset = chartData.datasets[0];
                
                // Update the chart if it exists, or create a new one
                if (userGrowthChart) {
                    userGrowthChart.data.labels = chartData.labels;
                    userGrowthChart.data.datasets[0].data = dataset.data;
                    userGrowthChart.update();
                } else {
                    userGrowthChart = createUserGrowthChart(userGrowthCtx, {
                        labels: chartData.labels,
                        data: dataset.data,
                        totalUsers: dataset.total_users
                    });
                }
                
                // Update the date range display
                const dateRangeElement = document.getElementById('userGrowthDateRange');
                if (dateRangeElement) {
                    dateRangeElement.textContent = `Showing data from ${dataset.start_date} to ${dataset.end_date}`;
                }
                
                // Update active button state
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.range === range);
                });
                
                // Hide loading state
                chartContainer.classList.remove('loading');
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            })
            .catch(error => {
                console.error('Error fetching user growth data:', error);
                if (errorMessage) {
                    errorMessage.textContent = 'Failed to load user growth data. Please try again.';
                    errorMessage.style.display = 'block';
                }
                chartContainer.classList.remove('loading');
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            });
    }
    
    // Function to create the chart
    function createUserGrowthChart(ctx, { labels, data, totalUsers }) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'New Users',
                    data: data,
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: chartColors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: chartColors.primary,
                    pointHoverBorderWidth: 3,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        borderRadius: 8,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return `New Users: ${context.raw}`;
                            },
                            footer: function(tooltipItems) {
                                return `Total Users: ${totalUsers}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            precision: 0, // Only show whole numbers
                            callback: function(value) {
                                if (Number.isInteger(value)) {
                                    return value;
                                }
                                return '';
                            },
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    // Quiz Performance Chart
    const quizPerfCtx = document.getElementById('quizPerformanceChart');
    if (quizPerfCtx) {
        try {
            // Get data from data attributes with fallback to 0
            const easyCount = parseInt(quizPerfCtx.dataset.easyCount) || 0;
            const mediumCount = parseInt(quizPerfCtx.dataset.mediumCount) || 0;
            const hardCount = parseInt(quizPerfCtx.dataset.hardCount) || 0;

            console.log('Quiz Performance Data:', { easyCount, mediumCount, hardCount });

            // Only create chart if we have data
            if (easyCount > 0 || mediumCount > 0 || hardCount > 0) {
                new Chart(quizPerfCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Easy', 'Medium', 'Hard'],
                        datasets: [{
                            data: [easyCount, mediumCount, hardCount],
                            backgroundColor: [
                                chartColors.success,
                                chartColors.warning,
                                chartColors.error
                            ],
                            borderWidth: 0,
                            hoverOffset: 10
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 20,
                                    font: {
                                        size: 13,
                                        weight: '600'
                                    },
                                    usePointStyle: true,
                                    pointStyle: 'circle'
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                borderRadius: 8,
                                titleFont: {
                                    size: 14,
                                    weight: 'bold'
                                },
                                bodyFont: {
                                    size: 13
                                },
                                callbacks: {
                                    label: function(context) {
                                        let label = context.label || '';
                                        let value = context.parsed || 0;
                                        let total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        let percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        },
                        cutout: '70%'
                    }
                });
            } else {
                console.warn('No quiz performance data available');
                if (quizPerfCtx.parentElement) {
                    quizPerfCtx.parentElement.innerHTML = '<div class="alert alert-info">No quiz performance data available</div>';
                }
            }
        } catch (error) {
            console.error('Error initializing quiz performance chart:', error);
            if (quizPerfCtx && quizPerfCtx.parentElement) {
                quizPerfCtx.parentElement.innerHTML = '<div class="alert alert-danger">Error loading quiz performance chart</div>';
            }
        }
    }

    // Filter buttons functionality
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from siblings
            this.parentElement.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.remove('active');
            });
            // Add active class to clicked button
            this.classList.add('active');
            
            // Show toast notification
            showXPToast('Chart Updated', `Showing ${this.textContent.toLowerCase()} data`, 'fa-chart-line');
        });
    });

    // Export data function
    window.exportData = function() {
        showXPToast('Exporting Data', 'Preparing your export...', 'fa-download');
        
        setTimeout(() => {
            window.location.href = document.getElementById('export-data-url').dataset.url;
            showXPToast('Export Complete', 'Data exported successfully', 'fa-check');
        }, 1000);
    };

    // Auto-refresh timestamp
    function updateTimestamp() {
        const now = new Date();
        const timestamp = now.toLocaleTimeString();
        const timestampElement = document.getElementById('last-updated-timestamp');
        if (timestampElement) {
            timestampElement.textContent = `Last updated: ${timestamp}`;
        }
    }

    // Initialize the user growth chart if the element exists
    if (userGrowthCtx) {
        // Add event listeners for range filter buttons
        document.querySelectorAll('.filter-btn[data-range]').forEach(button => {
            button.addEventListener('click', (e) => {
                const range = e.currentTarget.dataset.range;
                updateUserGrowthChart(range);
            });
        });
        
        // Initial load with default range (week)
        updateUserGrowthChart('week');
        
        // Auto-refresh data every 5 minutes
        setInterval(() => updateUserGrowthChart(
            document.querySelector('.filter-btn.active')?.dataset.range || 'week'
        ), 5 * 60 * 1000);
    }
    
    setInterval(updateTimestamp, 1000);
    updateTimestamp();
});
