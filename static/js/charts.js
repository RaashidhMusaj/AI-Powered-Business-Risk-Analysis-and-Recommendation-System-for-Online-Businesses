/**
 * Charts & Visual Analytics Renderer Component (Milestone 11.4, 11.6, FR 38 & FR 39)
 * Renders Chart.js Radar, Doughnut, Bar, Gauge, and Multi-Aspect Time-Series Line Visualizations.
 */
const ChartManager = {
    instances: {
        sentiment: null,
        aspect: null,
        radar: null,
        trend: null
    },

    extractScore(val) {
        if (typeof val === 'number') return val;
        if (val && typeof val.score === 'number') return val.score;
        if (val && typeof val.risk_score === 'number') return val.risk_score;
        return parseFloat(val) || 0.0;
    },

    renderAllCharts(stats = {}, metrics = {}, risks = {}) {
        this.renderSentimentChart(stats, metrics);
    },

    renderSentimentChart(stats, metrics) {
        const sentStats = stats.sentimentStatistics || stats.reviewStatistics || {};
        const posCount = metrics.totalPositiveReviews ?? sentStats.positive_reviews ?? sentStats.positive ?? 0;
        const negCount = metrics.totalNegativeReviews ?? sentStats.negative_reviews ?? sentStats.negative ?? 0;
        const neuCount = metrics.totalNeutralReviews ?? sentStats.neutral_reviews ?? sentStats.neutral ?? 0;

        const sentCtx = document.getElementById('sentimentChart');
        if (sentCtx && window.Chart) {
            if (this.instances.sentiment) this.instances.sentiment.destroy();

            this.instances.sentiment = new Chart(sentCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Positive Sentiment', 'Negative Sentiment', 'Neutral Sentiment'],
                    datasets: [{
                        data: [posCount, negCount, neuCount],
                        backgroundColor: ['#198754', '#dc3545', '#ffc107'],
                        borderWidth: 2,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12 } }
                    }
                }
            });
        }
    },

    /**
     * Renders Multi-Aspect Time-Series Trend Line Chart (FR 38 & FR 39)
     * Consumes array of objects: [{"date": "...", "delivery": 52, "quality": 41, "trust": 33, "bri": 44}]
     */
    renderMultiAspectTrendChart(trendPoints = []) {
        const trendCtx = document.getElementById('multiAspectTrendChart');
        if (!trendCtx || !window.Chart) return;

        if (this.instances.trend) {
            this.instances.trend.destroy();
        }

        const labels = trendPoints.map(p => p.date || p.analysisId || 'Run');
        const deliveryData = trendPoints.map(p => p.delivery ?? 0);
        const qualityData = trendPoints.map(p => p.quality ?? 0);
        const trustData = trendPoints.map(p => p.trust ?? 0);
        const briData = trendPoints.map(p => p.bri ?? 0);

        this.instances.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Delivery Risk',
                        data: deliveryData,
                        borderColor: '#0dcaf0',
                        backgroundColor: 'rgba(13, 202, 240, 0.1)',
                        tension: 0.3,
                        pointRadius: 5,
                        hidden: false
                    },
                    {
                        label: 'Quality Risk',
                        data: qualityData,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        pointRadius: 5,
                        hidden: false
                    },
                    {
                        label: 'Trust Risk',
                        data: trustData,
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.3,
                        pointRadius: 5,
                        hidden: false
                    },
                    {
                        label: 'BRI Index',
                        data: briData,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.15)',
                        borderDash: [5, 5],
                        borderWidth: 3,
                        tension: 0.3,
                        pointRadius: 6,
                        hidden: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { title: { display: true, text: 'Analysis Timeline' } },
                    y: { beginAtZero: true, max: 100, title: { display: true, text: 'Risk Score (0-100)' } }
                },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { enabled: true }
                }
            }
        });
    },

    toggleTrendDataset(index, visible) {
        if (this.instances.trend && this.instances.trend.data.datasets[index]) {
            this.instances.trend.data.datasets[index].hidden = !visible;
            this.instances.trend.update();
        }
    }
};

window.ChartManager = ChartManager;
