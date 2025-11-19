/**
 * Real-Time Dashboard Manager
 * Manages all real-time updates for the admin dashboard
 */

class RealTimeDashboardManager {
    constructor(options = {}) {
        this.updateIntervals = {
            fast: options.fastInterval || 10000,      // 10 seconds - for critical stats
            medium: options.mediumInterval || 30000,  // 30 seconds - for charts
            slow: options.slowInterval || 60000       // 60 seconds - for heavy data
        };
        
        this.intervals = {};
        this.charts = {};
        this.previousData = {};
        this.isVisible = true;
        
        this.init();
    }
    
    init() {
        console.log('Initializing Real-Time Dashboard Manager...');
        
        // Setup visibility change detection
        this.setupVisibilityDetection();
        
        // Start all update cycles
        this.startStatisticsUpdates();
        this.startUserGrowthUpdates();
        this.startLoginActivityUpdates();
        this.startRecentActivityUpdates();
        this.startQLearningUpdates();
        
        console.log('Real-Time Dashboard Manager initialized successfully');
    }
    
    /**
     * Detect when user switches tabs to pause/resume updates
     */
    setupVisibilityDetection() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            
            if (this.isVisible) {
                console.log('Dashboard visible - resuming updates');
                this.resumeAllUpdates();
            } else {
                console.log('Dashboard hidden - pausing updates');
                this.pauseAllUpdates();
            }
        });
    }
    
    /**
     * Update main statistics cards (Total Students, Active Profiles, etc.)
     */
    startStatisticsUpdates() {
        const updateStats = async () => {
            if (!this.isVisible) return;
            
            try {
                const response = await fetch('/api/dashboard/statistics/');
                const data = await response.json();
                
                if (data.success) {
                    this.updateStatCard('total_students', data.total_students, data.students_trend);
                    this.updateStatCard('total_profiles', data.total_profiles, data.profiles_trend);
                    this.updateStatCard('avg_progress', data.avg_progress, data.progress_trend);
                    this.updateStatCard('system_status', data.system_status);
                }
            } catch (error) {
                console.error('Error updating statistics:', error);
            }
        };
        
        // Initial update
        updateStats();
        
        // Schedule regular updates
        this.intervals.statistics = setInterval(updateStats, this.updateIntervals.fast);
    }
    
    /**
     * Update a single stat card with animation
     */
    updateStatCard(cardId, newValue, trend = null) {
        const valueElement = document.querySelector(`[data-stat="${cardId}"] .stat-value`);
        const trendElement = document.querySelector(`[data-stat="${cardId}"] .stat-trend`);
        
        if (!valueElement) return;
        
        // Animate value change
        const oldValue = parseFloat(valueElement.textContent) || 0;
        if (oldValue !== newValue) {
            this.animateValue(valueElement, oldValue, newValue, 500);
            
            // Flash effect
            valueElement.classList.add('value-updated');
            setTimeout(() => valueElement.classList.remove('value-updated'), 1000);
        }
        
        // Update trend indicator
        if (trend !== null && trendElement) {
            const trendValue = parseFloat(trend);
            trendElement.innerHTML = `
                <i class="fas fa-arrow-${trendValue >= 0 ? 'up' : 'down'}"></i>
                ${trendValue >= 0 ? '+' : ''}${trendValue.toFixed(1)}%
            `;
            trendElement.className = `stat-trend ${trendValue >= 0 ? 'up' : 'down'}`;
        }
    }
    
    /**
     * Animate number changes
     */
    animateValue(element, start, end, duration) {
        const startTime = performance.now();
        const isFloat = end % 1 !== 0;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (end - start) * this.easeOutQuad(progress);
            element.textContent = isFloat ? current.toFixed(1) : Math.round(current);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    easeOutQuad(t) {
        return t * (2 - t);
    }
    
    /**
     * Update User Growth Chart
     */
    startUserGrowthUpdates() {
        const updateChart = async () => {
            if (!this.isVisible) return;
            
            try {
                const range = document.querySelector('.filter-btn.active')?.dataset.range || 'week';
                const response = await fetch(`/api/dashboard/user-growth/?range=${range}`);
                const data = await response.json();
                
                if (data.success) {
                    this.updateUserGrowthChart(data.data);
                    this.updateTimestamp('userGrowthDateRange', data.data.start_date, data.data.end_date);
                }
            } catch (error) {
                console.error('Error updating user growth chart:', error);
                this.showError('userGrowthError');
            }
        };
        
        // Initial update
        updateChart();
        
        // Schedule regular updates
        this.intervals.userGrowth = setInterval(updateChart, this.updateIntervals.medium);
        
        // Update on filter change
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                updateChart();
            });
        });
    }
    
    /**
     * Update the User Growth Chart
     */
    updateUserGrowthChart(data) {
        const ctx = document.getElementById('userGrowthChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.userGrowth) {
            this.charts.userGrowth.destroy();
        }
        
        // Create new chart
        this.charts.userGrowth = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'New Users',
                    data: data.datasets[0].data,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
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
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: (context) => `${context.parsed.y} new users`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    /**
     * Update Login Activity Logs
     */
    startLoginActivityUpdates() {
        const updateLogs = async () => {
            if (!this.isVisible) return;
            
            try {
                const response = await fetch('/qlearning/api/login-activity/');
                const data = await response.json();
                
                if (data.activities && data.activities.length > 0) {
                    this.updateLoginActivityTable(data.activities);
                    this.updateLogsCount(data.activities.length);
                }
            } catch (error) {
                console.error('Error updating login activity:', error);
            }
        };
        
        // Initial update
        updateLogs();
        
        // Schedule regular updates
        this.intervals.loginActivity = setInterval(updateLogs, this.updateIntervals.fast);
    }
    
    /**
     * Update Login Activity Table with smooth transitions
     */
    updateLoginActivityTable(activities) {
        const tbody = document.getElementById('loginLogsBody');
        if (!tbody) return;
        
        // Check for new activities
        const newActivityIds = activities.map(a => a.id);
        const existingIds = Array.from(tbody.querySelectorAll('tr')).map(tr => tr.dataset.activityId);
        
        const hasNewActivities = newActivityIds.some(id => !existingIds.includes(id));
        
        if (hasNewActivities) {
            // Clear existing rows
            tbody.innerHTML = '';
            
            // Add new rows with animation
            activities.forEach((log, index) => {
                const row = this.createLoginActivityRow(log);
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
                tbody.appendChild(row);
                
                // Stagger animation
                setTimeout(() => {
                    row.style.transition = 'all 0.3s ease';
                    row.style.opacity = '1';
                    row.style.transform = 'translateX(0)';
                }, index * 50);
            });
        }
    }
    
    /**
     * Create a login activity row
     */
    createLoginActivityRow(log) {
        const row = document.createElement('tr');
        row.dataset.activityId = log.id;
        
        const isActive = !log.logout_time;
        const loginTime = this.formatDate(log.login_time);
        const duration = this.formatDuration(log.duration);
        
        row.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="activity-avatar" style="width: 32px; height: 32px; font-size: 0.75rem; background-color: ${isActive ? 'var(--primary)' : 'var(--light)'}; color: ${isActive ? 'white' : 'var(--dark)'};">
                        ${log.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div style="font-weight: 600;">${log.username}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">
                            ${log.ip_address || 'No IP'}
                        </div>
                    </div>
                </div>
            </td>
            <td>
                <div>
                    <div>${loginTime}</div>
                    ${log.logout_time ? 
                        `<div style="font-size: 0.75rem; color: var(--text-secondary);">${this.formatDate(log.logout_time)}</div>` : 
                        ''
                    }
                </div>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <i class="far fa-clock" style="color: var(--text-secondary);"></i>
                    <span>${duration}</span>
                </div>
            </td>
            <td>
                <span style="font-family: monospace;">${log.ip_address || 'N/A'}</span>
            </td>
            <td>
                <span class="badge ${isActive ? 'badge-success' : 'badge-light'}" style="font-weight: 500;">
                    <i class="fas fa-${isActive ? 'check-circle' : 'sign-out-alt'}"></i>
                    ${isActive ? 'Active Now' : 'Completed'}
                </span>
            </td>
        `;
        
        return row;
    }
    
    /**
     * Update Recent Activity Feed
     */
    startRecentActivityUpdates() {
        const updateActivity = async () => {
            if (!this.isVisible) return;
            
            try {
                const response = await fetch('/api/dashboard/recent-activity/');
                const data = await response.json();
                
                if (data.success) {
                    this.updateRecentActivityFeed(data.activities);
                }
            } catch (error) {
                console.error('Error updating recent activity:', error);
            }
        };
        
        // Initial update
        updateActivity();
        
        // Schedule regular updates
        this.intervals.recentActivity = setInterval(updateActivity, this.updateIntervals.medium);
    }
    
    /**
     * Update Recent Activity Feed with smooth transitions
     */
    updateRecentActivityFeed(activities) {
        const feed = document.querySelector('.activity-feed');
        if (!feed) return;
        
        // Check for new activities
        const newActivityIds = activities.map(a => a.id);
        const existingIds = Array.from(feed.querySelectorAll('.activity-item')).map(item => item.dataset.activityId);
        
        const hasNewActivities = newActivityIds.some(id => !existingIds.includes(id));
        
        if (hasNewActivities) {
            // Add new activities at the top
            activities.slice(0, 10).reverse().forEach(activity => {
                if (!existingIds.includes(activity.id.toString())) {
                    const item = this.createActivityItem(activity);
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(-10px)';
                    feed.insertBefore(item, feed.firstChild);
                    
                    // Animate in
                    setTimeout(() => {
                        item.style.transition = 'all 0.3s ease';
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 50);
                    
                    // Remove oldest items if more than 10
                    const items = feed.querySelectorAll('.activity-item');
                    if (items.length > 10) {
                        items[items.length - 1].remove();
                    }
                }
            });
        }
    }
    
    /**
     * Create an activity item
     */
    createActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.dataset.activityId = activity.id;
        
        item.innerHTML = `
            <div class="activity-avatar">
                ${activity.username.charAt(0).toUpperCase()}
            </div>
            <div class="activity-content">
                <div class="activity-user">${activity.username}</div>
                <div class="activity-action">
                    ${activity.action}
                </div>
                <div class="activity-time">
                    <i class="fas fa-clock"></i>
                    ${this.getTimeAgo(activity.timestamp)}
                </div>
            </div>
            <span class="activity-badge ${activity.is_correct ? 'success' : 'error'}">
                <i class="fas fa-${activity.is_correct ? 'check' : 'times'}"></i>
                ${activity.is_correct ? 'Correct' : 'Wrong'}
            </span>
        `;
        
        return item;
    }
    
    /**
     * Update Q-Learning metrics
     */
    startQLearningUpdates() {
        const updateMetrics = async () => {
            if (!this.isVisible) return;
            
            try {
                const days = document.querySelector('.time-range-btn.active')?.dataset.days || 30;
                const response = await fetch(`/qlearning/api/metrics/?days=${days}`);
                const data = await response.json();
                
                if (data) {
                    // Trigger QLearningDashboard update if it exists
                    if (window.qLearningDashboard) {
                        window.qLearningDashboard.updateDashboard(data);
                    }
                }
            } catch (error) {
                console.error('Error updating Q-Learning metrics:', error);
            }
        };
        
        // Initial update
        updateMetrics();
        
        // Schedule regular updates (less frequent for heavy data)
        this.intervals.qlearning = setInterval(updateMetrics, this.updateIntervals.slow);
    }
    
    /**
     * Utility: Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('id-ID', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    /**
     * Utility: Format duration
     */
    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    /**
     * Utility: Get time ago
     */
    getTimeAgo(timestamp) {
        const now = new Date();
        const date = new Date(timestamp);
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }
    
    /**
     * Update timestamp display
     */
    updateTimestamp(elementId, startDate, endDate) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = `${startDate} - ${endDate}`;
        }
    }
    
    /**
     * Update logs count badge
     */
    updateLogsCount(count) {
        const badge = document.getElementById('logsCount');
        if (badge) {
            badge.textContent = count;
        }
    }
    
    /**
     * Show error message
     */
    showError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    }
    
    /**
     * Pause all updates
     */
    pauseAllUpdates() {
        Object.keys(this.intervals).forEach(key => {
            if (this.intervals[key]) {
                clearInterval(this.intervals[key]);
            }
        });
    }
    
    /**
     * Resume all updates
     */
    resumeAllUpdates() {
        // Restart all interval-based updates
        this.startStatisticsUpdates();
        this.startUserGrowthUpdates();
        this.startLoginActivityUpdates();
        this.startRecentActivityUpdates();
        this.startQLearningUpdates();
    }
    
    /**
     * Destroy manager and clean up
     */
    destroy() {
        this.pauseAllUpdates();
        
        // Destroy all charts
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                this.charts[key].destroy();
            }
        });
        
        console.log('Real-Time Dashboard Manager destroyed');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the real-time dashboard manager
    window.realtimeDashboard = new RealTimeDashboardManager({
        fastInterval: 10000,   // 10 seconds for critical stats
        mediumInterval: 30000, // 30 seconds for charts
        slowInterval: 60000    // 60 seconds for heavy data
    });
    
    // Add custom styles for animations
    const style = document.createElement('style');
    style.textContent = `
        .value-updated {
            animation: pulse 0.5s ease-in-out;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); color: var(--primary); }
        }
        
        .activity-item {
            transition: all 0.3s ease;
        }
        
        .activity-item.new {
            background: rgba(75, 192, 192, 0.1);
        }
    `;
    document.head.appendChild(style);
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.realtimeDashboard) {
        window.realtimeDashboard.destroy();
    }
});