/**
 * UI Controller and State Machine for AI Business Risk Analysis System.
 */
const UI = {
    charts: {
        sentiment: null,
        aspect: null
    },
    renderedLogsCount: 0,

    // --- Authentication UI State Switchers ---
    updateAuthNavbar(user) {
        const unauthNav = document.getElementById('unauthNavControls');
        const authNav = document.getElementById('authNavControls');
        const navUsername = document.getElementById('navUsername');

        if (user && user.username) {
            if (unauthNav) unauthNav.classList.add('d-none');
            if (authNav) authNav.classList.remove('d-none');
            if (navUsername) navUsername.textContent = user.username;
        } else {
            if (unauthNav) unauthNav.classList.remove('d-none');
            if (authNav) authNav.classList.add('d-none');
        }
    },

    showLandingPage() {
        const landing = document.getElementById('landingHeroSection');
        const workspace = document.getElementById('analysisWorkspaceContainer');
        if (landing) landing.classList.remove('d-none');
        if (workspace) workspace.classList.add('d-none');
        this.updateAuthNavbar(API.getUserInfo());
    },

    showAnalysisWorkspace() {
        const landing = document.getElementById('landingHeroSection');
        const workspace = document.getElementById('analysisWorkspaceContainer');
        if (landing) landing.classList.add('d-none');
        if (workspace) workspace.classList.remove('d-none');
        this.updateAuthNavbar(API.getUserInfo());
    },

    onUnauthorized() {
        this.showLandingPage();
        this.openAuthModal('login');
        this.showAuthAlert('Session expired or authentication required. Please log in.', 'danger');
    },

    switchAuthTab(tab = 'login') {
        this.hideAuthAlert();
        const loginBtn = document.getElementById('loginTabBtn');
        const regBtn = document.getElementById('registerTabBtn');
        const loginTab = document.getElementById('loginTab');
        const regTab = document.getElementById('registerTab');

        if (tab === 'register') {
            if (loginBtn) loginBtn.classList.remove('active');
            if (regBtn) regBtn.classList.add('active');
            if (loginTab) loginTab.classList.remove('show', 'active');
            if (regTab) regTab.classList.add('show', 'active');
        } else {
            if (regBtn) regBtn.classList.remove('active');
            if (loginBtn) loginBtn.classList.add('active');
            if (regTab) regTab.classList.remove('show', 'active');
            if (loginTab) loginTab.classList.add('show', 'active');
        }
    },

    openAuthModal(tab = 'login') {
        this.switchAuthTab(tab);
        const modalElem = document.getElementById('authModal');
        if (modalElem && window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalElem);
            modal.show();
        }
    },

    closeAuthModal() {
        const modalElem = document.getElementById('authModal');
        if (modalElem && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalElem);
            if (modal) modal.hide();
        }
    },

    showAuthAlert(message, type = 'danger') {
        const alertElem = document.getElementById('authModalAlert');
        if (!alertElem) return;
        alertElem.className = `alert alert-${type} py-2 small mb-3`;
        alertElem.textContent = message;
        alertElem.classList.remove('d-none');
    },

    hideAuthAlert() {
        const alertElem = document.getElementById('authModalAlert');
        if (alertElem) alertElem.classList.add('d-none');
    },

    // --- State Machine Enforcer ---
    setFinishScrapingState(state) {
        const btn = document.getElementById('btnFinishScraping');
        if (!btn) return;

        if (state === 'STOP_SCRAPING') {
            btn.disabled = false;
            btn.className = 'btn btn-outline-warning w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-hand me-2"></i> Finish Scraping (Proceed to AI Processing)';
        } else if (state === 'PROCESSING') {
            btn.disabled = true;
            btn.className = 'btn btn-warning w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Processing AI Predictions...';
        } else if (state === 'DONE') {
            btn.disabled = true;
            btn.className = 'btn btn-success w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i> Analysis Complete';
        } else {
            btn.disabled = true;
            btn.className = 'btn btn-outline-secondary w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-hand me-2"></i> Finish Scraping';
        }
    },

    setInitialState() {
        const btnCheck = document.getElementById('btnCheckProduct');
        const btnStart = document.getElementById('btnStartAnalysis');
        if (btnCheck) btnCheck.disabled = false;
        if (btnStart) btnStart.disabled = true;

        this.setFinishScrapingState('DISABLED');

        const previewCard = document.getElementById('previewCard');
        const progressCard = document.getElementById('progressCard');
        const resultsCard = document.getElementById('resultsCard');

        if (previewCard) previewCard.classList.add('d-none');
        if (progressCard) progressCard.classList.add('d-none');
        if (resultsCard) resultsCard.classList.add('d-none');
        this.resetConsole();
    },

    setProductCheckedState() {
        const btnCheck = document.getElementById('btnCheckProduct');
        const btnStart = document.getElementById('btnStartAnalysis');
        if (btnCheck) btnCheck.disabled = true;
        if (btnStart) btnStart.disabled = false;

        const previewCard = document.getElementById('previewCard');
        const progressCard = document.getElementById('progressCard');
        const resultsCard = document.getElementById('resultsCard');

        if (previewCard) previewCard.classList.remove('d-none');
        if (progressCard) progressCard.classList.add('d-none');
        if (resultsCard) resultsCard.classList.add('d-none');
    },

    setScrapingState() {
        const btnCheck = document.getElementById('btnCheckProduct');
        const btnStart = document.getElementById('btnStartAnalysis');
        if (btnCheck) btnCheck.disabled = true;
        if (btnStart) btnStart.disabled = true;

        this.setFinishScrapingState('STOP_SCRAPING');

        const progressCard = document.getElementById('progressCard');
        const resultsCard = document.getElementById('resultsCard');

        if (progressCard) progressCard.classList.remove('d-none');
        if (resultsCard) resultsCard.classList.add('d-none');
    },

    setCompletedState() {
        const btnCheck = document.getElementById('btnCheckProduct');
        const btnStart = document.getElementById('btnStartAnalysis');
        if (btnCheck) btnCheck.disabled = false;
        if (btnStart) btnStart.disabled = true;

        this.setFinishScrapingState('DONE');

        const progressCard = document.getElementById('progressCard');
        const resultsCard = document.getElementById('resultsCard');

        if (progressCard) progressCard.classList.add('d-none');
        if (resultsCard) resultsCard.classList.remove('d-none');
    },

    // --- Notifications ---
    showAlert(message, type = 'info') {
        const banner = document.getElementById('alertBanner');
        const icon = document.getElementById('alertIcon');
        const msg = document.getElementById('alertMessage');
        if (!banner || !msg) return;

        banner.className = `alert alert-${type} alert-dismissible fade show shadow-sm mb-4`;
        msg.textContent = message;

        if (icon) {
            if (type === 'danger') icon.className = 'fa-solid fa-triangle-exclamation me-2 fa-lg';
            else if (type === 'success') icon.className = 'fa-solid fa-circle-check me-2 fa-lg';
            else icon.className = 'fa-solid fa-circle-info me-2 fa-lg';
        }

        banner.classList.remove('d-none');
    },

    hideAlert() {
        const banner = document.getElementById('alertBanner');
        if (banner) banner.classList.add('d-none');
    },

    // --- Product Preview Renderer ---
    renderPreview(preview) {
        if (!preview) return;

        const title = preview.title || preview.productTitle || preview.product_name || 'N/A';
        const seller = preview.seller || preview.seller_name || preview.sellerName || 'N/A';
        const rawRating = preview.overallRating ?? preview.overall_rating ?? preview.rating ?? 0.0;
        const ratingVal = typeof rawRating === 'number' ? rawRating : parseFloat(rawRating) || 0.0;
        const rating = ratingVal > 0 ? ratingVal.toFixed(1) : 'N/A';
        const reviews = preview.totalReviews ?? preview.total_reviews ?? preview.reviewCount ?? 0;
        const platform = preview.platform || 'Daraz';
        const category = preview.category || 'N/A';
        const imageUrl = preview.imageUrl || preview.image_url || '';

        const elemTitle = document.getElementById('previewTitle');
        const elemSeller = document.getElementById('previewSeller');
        const elemRating = document.getElementById('previewRating');
        const elemReviews = document.getElementById('previewReviews');
        const elemPlatform = document.getElementById('previewPlatform');
        const elemCat = document.getElementById('previewCategory');

        if (elemTitle) elemTitle.textContent = title;
        if (elemSeller) elemSeller.textContent = seller;
        if (elemRating) elemRating.textContent = rating;
        if (elemReviews) elemReviews.textContent = reviews;
        if (elemPlatform) elemPlatform.textContent = platform;
        if (elemCat) elemCat.textContent = `Category: ${category}`;

        const fallbackImg = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80';
        const imgElem = document.getElementById('previewImage');
        if (imgElem) {
            imgElem.classList.remove('d-none');
            imgElem.src = imageUrl || fallbackImg;
            imgElem.onerror = function () {
                this.onerror = null;
                this.src = fallbackImg;
            };
            imgElem.alt = title;
        }

        const visitBtn = document.getElementById('btnVisitProduct');
        if (visitBtn && (preview.productUrl || preview.url)) {
            visitBtn.href = preview.productUrl || preview.url;
        }
    },

    // --- Progress Card & Stepper Renderer ---
    updateProgress(statusData) {
        const progressBar = document.getElementById('progressBar');
        const stepText = document.getElementById('currentStepText');
        const timeText = document.getElementById('elapsedTimeText');
        const badge = document.getElementById('stageBadge');
        const spinner = document.getElementById('progressSpinner');

        const pct = statusData.progress || 0;
        if (progressBar) {
            progressBar.style.width = `${pct}%`;
            progressBar.textContent = `${pct}%`;
        }

        if (stepText) stepText.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-1"></i> ${statusData.currentStep || 'Processing...'}`;
        if (timeText) timeText.textContent = statusData.elapsedTime || '00:00:00';

        if (statusData.status === 'SCRAPING') {
            if (badge) {
                badge.className = 'badge bg-primary px-3 py-2 text-uppercase fs-6';
                badge.textContent = 'Scraping';
            }
            if (spinner) spinner.className = 'fa-solid fa-spinner fa-spin text-primary me-2';
        } else if (statusData.status === 'AI_ANALYSIS') {
            if (badge) {
                badge.className = 'badge bg-info text-dark px-3 py-2 text-uppercase fs-6';
                badge.textContent = 'AI Analysis';
            }
            if (spinner) spinner.className = 'fa-solid fa-brain fa-beat text-info me-2';
            this.setFinishScrapingState('PROCESSING');
        } else if (statusData.status === 'COMPLETED' || pct >= 100) {
            if (badge) {
                badge.className = 'badge bg-success px-3 py-2 text-uppercase fs-6';
                badge.textContent = 'Completed';
            }
            if (spinner) spinner.className = 'fa-solid fa-circle-check text-success me-2';
            if (progressBar) {
                progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                progressBar.classList.add('bg-success');
            }
            this.setFinishScrapingState('DONE');
        } else if (statusData.status === 'FAILED') {
            if (badge) {
                badge.className = 'badge bg-danger px-3 py-2 text-uppercase fs-6';
                badge.textContent = 'Failed';
            }
            if (spinner) spinner.className = 'fa-solid fa-triangle-exclamation text-danger me-2';
            if (progressBar) {
                progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                progressBar.classList.add('bg-danger');
            }
        }

        this.updateStepper(statusData.status, pct);
        if (statusData.logs) {
            this.appendConsoleLogs(statusData.logs);
        }
    },

    updateStepper(status, progressPct) {
        const step1 = document.getElementById('step1');
        const step2 = document.getElementById('step2');
        const step3 = document.getElementById('step3');
        const step4 = document.getElementById('step4');

        if (!step1) return;

        [step1, step2, step3, step4].forEach(s => { if (s) s.className = 'col stepper-step text-muted'; });

        if (status === 'SCRAPING') {
            step1.className = 'col stepper-step active';
        } else if (status === 'AI_ANALYSIS') {
            step1.className = 'col stepper-step completed';
            step2.className = 'col stepper-step active';
            step3.className = 'col stepper-step active';
        } else if (status === 'COMPLETED' || progressPct >= 100) {
            step1.className = 'col stepper-step completed';
            step2.className = 'col stepper-step completed';
            step3.className = 'col stepper-step completed';
            step4.className = 'col stepper-step completed';
        }
    },

    resetConsole() {
        const consoleElem = document.getElementById('processingConsole');
        if (consoleElem) {
            consoleElem.innerHTML = '<div class="text-muted mb-1">[SYSTEM] Analysis Job Initialized.</div>';
        }
        this.renderedLogsCount = 0;
    },

    appendConsoleLogs(logs) {
        const consoleElem = document.getElementById('processingConsole');
        if (!consoleElem || !logs || !Array.isArray(logs)) return;

        if (logs.length > this.renderedLogsCount) {
            const newLogs = logs.slice(this.renderedLogsCount);
            newLogs.forEach(log => {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'mb-1';
                if (log.includes('[ERROR]')) lineDiv.className = 'text-danger font-weight-bold mb-1';
                else if (log.includes('[SCRAPER]')) lineDiv.className = 'text-info mb-1';
                else if (log.includes('[AI_ENGINE]')) lineDiv.className = 'text-warning mb-1';
                else if (log.includes('[FIS]')) lineDiv.className = 'text-success mb-1';
                lineDiv.textContent = log;
                consoleElem.appendChild(lineDiv);
            });
            this.renderedLogsCount = logs.length;
            consoleElem.scrollTop = consoleElem.scrollHeight;
        }
    },

    // --- Risk Results Dashboard Renderer ---
    renderResults(resultData) {
        if (!resultData) return;

        this.setCompletedState();

        const risks = resultData.risks || {};
        const stats = resultData.statistics || {};
        const metrics = resultData.metrics || {};
        const revStats = stats.reviewStatistics || stats.sentimentStatistics || {};

        const briVal = risks.businessRiskIndex ?? 0.0;
        const briLevel = risks.overallRiskLevel || risks.businessRiskLevel || 'MEDIUM';

        const briElem = document.getElementById('businessRiskIndexVal');
        const badgeElem = document.getElementById('businessRiskLevelBadge');

        if (briElem) briElem.textContent = typeof briVal === 'number' ? briVal.toFixed(1) : parseFloat(briVal).toFixed(1);
        if (badgeElem) {
            badgeElem.textContent = `${briLevel} RISK`;
            badgeElem.className = `badge fs-5 px-4 py-2 text-uppercase ${this.getRiskBadgeClass(briLevel)}`;
        }

        // Render Review Count Metrics Summary Cards
        const totalCount = metrics.totalReviews ?? revStats.total_reviews ?? (resultData.product ? (resultData.product.reviewCount || resultData.product.totalReviews) : 0);
        const posCount = metrics.totalPositiveReviews ?? revStats.positive_reviews ?? revStats.positive ?? 0;
        const negCount = metrics.totalNegativeReviews ?? revStats.negative_reviews ?? revStats.negative ?? 0;
        const neuCount = metrics.totalNeutralReviews ?? revStats.neutral_reviews ?? revStats.neutral ?? 0;

        const elTotal = document.getElementById('statTotalReviews');
        const elPos = document.getElementById('statPositiveReviews');
        const elNeg = document.getElementById('statNegativeReviews');
        const elNeu = document.getElementById('statNeutralReviews');

        if (elTotal) elTotal.textContent = totalCount;
        if (elPos) elPos.textContent = posCount;
        if (elNeg) elNeg.textContent = negCount;
        if (elNeu) elNeu.textContent = neuCount;

        // Individual Risk Cards
        const qScore = (risks.qualityRisk || {}).score ?? risks.qualityRiskScore ?? 0.0;
        const qLevel = (risks.qualityRisk || {}).level ?? 'MEDIUM';
        const dScore = (risks.deliveryRisk || {}).score ?? risks.deliveryRiskScore ?? 0.0;
        const dLevel = (risks.deliveryRisk || {}).level ?? 'MEDIUM';
        const tScore = (risks.trustRisk || {}).score ?? risks.trustRiskScore ?? 0.0;
        const tLevel = (risks.trustRisk || {}).level ?? 'MEDIUM';

        const qElem = document.getElementById('qualityRiskScore');
        const qLvlElem = document.getElementById('qualityRiskLevel');
        if (qElem) qElem.textContent = typeof qScore === 'number' ? qScore.toFixed(1) : parseFloat(qScore).toFixed(1);
        if (qLvlElem) { qLvlElem.textContent = qLevel; qLvlElem.className = `badge ${this.getRiskBadgeClass(qLevel)}`; }

        const dElem = document.getElementById('deliveryRiskScore');
        const dLvlElem = document.getElementById('deliveryRiskLevel');
        if (dElem) dElem.textContent = typeof dScore === 'number' ? dScore.toFixed(1) : parseFloat(dScore).toFixed(1);
        if (dLvlElem) { dLvlElem.textContent = dLevel; dLvlElem.className = `badge ${this.getRiskBadgeClass(dLevel)}`; }

        const tElem = document.getElementById('trustRiskScore');
        const tLvlElem = document.getElementById('trustRiskLevel');
        if (tElem) tElem.textContent = typeof tScore === 'number' ? tScore.toFixed(1) : parseFloat(tScore).toFixed(1);
        if (tLvlElem) { tLvlElem.textContent = tLevel; tLvlElem.className = `badge ${this.getRiskBadgeClass(tLevel)}`; }

        // Render Charts
        this.renderCharts(stats, metrics);

        // Render Key Customer Concerns & Negative Reviews List
        this.renderCustomerConcerns(resultData);
    },

    renderCustomerConcerns(resultData) {
        const listElem = document.getElementById('negativeReviewsList');
        if (!listElem) return;

        let negList = [];
        if (resultData.negativeReviews && Array.isArray(resultData.negativeReviews)) {
            negList = resultData.negativeReviews;
        } else if (resultData.reviews && Array.isArray(resultData.reviews)) {
            negList = resultData.reviews
                .filter(r => (r.sentiment || '').toUpperCase().includes('NEG'))
                .map(r => r.reviewText || r.review_text);
        }

        if (!negList || negList.length === 0) {
            listElem.innerHTML = `
                <div class="text-success small p-3 bg-success-subtle rounded-3 border border-success-subtle">
                    <i class="fa-solid fa-circle-check me-1"></i> No major negative customer concerns detected. Product customer sentiment is predominantly positive!
                </div>
            `;
        } else {
            listElem.innerHTML = negList.slice(0, 20).map(revText => `
                <div class="p-3 bg-light rounded-3 border-start border-danger border-4 small text-dark d-flex align-items-start gap-2 shadow-sm">
                    <i class="fa-solid fa-circle-exclamation text-danger mt-1"></i>
                    <div>${revText}</div>
                </div>
            `).join('');
        }
    },

    getRiskBadgeClass(level) {
        const lvl = String(level || '').toUpperCase();
        if (lvl === 'VERY_LOW' || lvl === 'LOW') return 'bg-success text-white';
        if (lvl === 'MEDIUM') return 'bg-warning text-dark';
        if (lvl === 'HIGH' || lvl === 'CRITICAL') return 'bg-danger text-white';
        return 'bg-secondary text-white';
    },

    renderCharts(stats, metrics = {}) {
        const sentStats = stats.sentimentStatistics || stats.reviewStatistics || {};
        const aspectStats = stats.aspectStatistics || {};

        const posCount = metrics.totalPositiveReviews ?? sentStats.positive_reviews ?? sentStats.positive ?? 0;
        const negCount = metrics.totalNegativeReviews ?? sentStats.negative_reviews ?? sentStats.negative ?? 0;
        const neuCount = metrics.totalNeutralReviews ?? sentStats.neutral_reviews ?? sentStats.neutral ?? 0;

        // 1. Sentiment Doughnut Chart
        const sentCtx = document.getElementById('sentimentChart');
        if (sentCtx && window.Chart) {
            if (this.charts.sentiment) this.charts.sentiment.destroy();

            this.charts.sentiment = new Chart(sentCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Positive', 'Negative', 'Neutral'],
                    datasets: [{
                        data: [posCount, negCount, neuCount],
                        backgroundColor: ['#198754', '#dc3545', '#ffc107'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // 2. Aspect Risk Bar Chart
        const aspectCtx = document.getElementById('aspectChart');
        if (aspectCtx && window.Chart) {
            if (this.charts.aspect) this.charts.aspect.destroy();

            const aspectLabels = ['Quality', 'Delivery', 'Trust'];
            const qScore = (aspectStats.quality || {}).risk_score ?? 35.0;
            const dScore = (aspectStats.delivery || {}).risk_score ?? 40.0;
            const tScore = (aspectStats.trust || {}).risk_score ?? 25.0;

            this.charts.aspect = new Chart(aspectCtx, {
                type: 'bar',
                data: {
                    labels: aspectLabels,
                    datasets: [{
                        label: 'Risk Score (0-100)',
                        data: [qScore, dScore, tScore],
                        backgroundColor: ['#0d6efd', '#0dcaf0', '#ffc107'],
                        borderRadius: 6
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

    // --- Analysis History Table Renderer ---
    renderHistoryTable(items = [], onSelect, onDelete) {
        const tbody = document.getElementById('historyTableBody');
        if (!tbody) return;

        if (!items || items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fa-solid fa-folder-open fa-2x mb-2 d-block"></i>
                        No previous risk analyses recorded. Enter a URL above to start your first analysis.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = items.map(item => {
            const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleString() : 'N/A';
            const riskLvl = item.businessRiskLevel || 'MEDIUM';
            const riskIdx = typeof item.businessRiskIndex === 'number' ? item.businessRiskIndex.toFixed(1) : item.businessRiskIndex;
            const title = item.productTitle || 'Daraz Product';

            return `
                <tr>
                    <td><code class="text-primary font-weight-bold">${item.analysisId}</code></td>
                    <td class="text-truncate" style="max-width: 220px;" title="${title}">${title}</td>
                    <td class="font-weight-bold">${riskIdx}</td>
                    <td><span class="badge ${this.getRiskBadgeClass(riskLvl)}">${riskLvl}</span></td>
                    <td>${item.totalReviews || 0}</td>
                    <td class="small text-muted">${dateStr}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="UI._handleHistorySelect('${item.analysisId}')">
                            <i class="fa-solid fa-eye"></i> View
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="UI._handleHistoryDelete('${item.analysisId}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        this._onSelectHistory = onSelect;
        this._onDeleteHistory = onDelete;
    },

    _handleHistorySelect(id) {
        if (typeof this._onSelectHistory === 'function') {
            this._onSelectHistory(id);
        }
    },

    _handleHistoryDelete(id) {
        if (typeof this._onDeleteHistory === 'function') {
            this._onDeleteHistory(id);
        }
    }
};

window.UI = UI;
