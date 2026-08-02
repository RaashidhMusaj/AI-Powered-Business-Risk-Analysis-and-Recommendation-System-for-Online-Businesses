/**
 * Charts & Visual Analytics Renderer Component (Milestone 11.4 & 11.6)
 * Renders Chart.js Radar, Doughnut, Bar, and Gauge visualizations.
 */
const ChartManager = {
    instances: {
        sentiment: null,
        aspect: null,
        radar: null
    },

    extractScore(val) {
        if (typeof val === 'number') return val;
        if (val && typeof val.score === 'number') return val.score;
        if (val && typeof val.risk_score === 'number') return val.risk_score;
        return parseFloat(val) || 0.0;
    },

    renderAllCharts(stats = {}, metrics = {}, risks = {}) {
        this.renderSentimentChart(stats, metrics);
        this.renderAspectBarChart(stats, risks);
        this.renderRadarChart(risks);
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

    renderAspectBarChart(stats, risks = {}) {
        const aspectCtx = document.getElementById('aspectChart');
        if (aspectCtx && window.Chart) {
            if (this.instances.aspect) this.instances.aspect.destroy();

            const qScore = this.extractScore(risks.qualityRisk ?? risks.quality_risk ?? risks.qualityRiskScore);
            const dScore = this.extractScore(risks.deliveryRisk ?? risks.delivery_risk ?? risks.deliveryRiskScore);
            const tScore = this.extractScore(risks.trustRisk ?? risks.trust_risk ?? risks.trustRiskScore);

            this.instances.aspect = new Chart(aspectCtx, {
                type: 'bar',
                data: {
                    labels: ['Quality Risk', 'Delivery Risk', 'Trust Risk'],
                    datasets: [{
                        label: 'Risk Score (0-100)',
                        data: [qScore, dScore, tScore],
                        backgroundColor: ['#0d6efd', '#0dcaf0', '#ffc107'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    },

    renderRadarChart(risks = {}) {
        const radarCtx = document.getElementById('radarChart');
        if (radarCtx && window.Chart) {
            if (this.instances.radar) this.instances.radar.destroy();

            const qScore = this.extractScore(risks.qualityRisk ?? risks.quality_risk ?? risks.qualityRiskScore);
            const dScore = this.extractScore(risks.deliveryRisk ?? risks.delivery_risk ?? risks.deliveryRiskScore);
            const tScore = this.extractScore(risks.trustRisk ?? risks.trust_risk ?? risks.trustRiskScore);
            const briVal = this.extractScore(risks.businessRiskIndex ?? risks.business_risk_index);

            this.instances.radar = new Chart(radarCtx, {
                type: 'radar',
                data: {
                    labels: ['Quality Risk', 'Delivery Risk', 'Trust Risk', 'Overall Business Index'],
                    datasets: [{
                        label: 'Risk Distribution Profile',
                        data: [qScore, dScore, tScore, briVal],
                        fill: true,
                        backgroundColor: 'rgba(13, 110, 253, 0.2)',
                        borderColor: '#0d6efd',
                        pointBackgroundColor: '#0d6efd',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#0d6efd'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { display: true },
                            suggestedMin: 0,
                            suggestedMax: 100
                        }
                    }
                }
            });
        }
    }
};

window.ChartManager = ChartManager;
