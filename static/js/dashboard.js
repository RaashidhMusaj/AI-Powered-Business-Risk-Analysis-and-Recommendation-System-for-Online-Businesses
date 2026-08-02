/**
 * Dashboard Controller & State Machine Component (Milestone 11.10)
 * Centralizes UI states: IDLE -> PREVIEW -> LOADING -> SUCCESS -> ERROR.
 */
const DashboardController = {
    state: 'IDLE', // States: 'IDLE', 'PREVIEW', 'LOADING', 'SUCCESS', 'ERROR'
    currentAnalysisData: null,

    init() {
        this.setState('IDLE');
        this.updateAuthNavbar(API.getUserInfo());
    },

    setState(newState, payload = null) {
        this.state = newState;
        console.log(`[DashboardController] Transitioned to State: ${newState}`);

        const landing = document.getElementById('landingHeroSection');
        const workspace = document.getElementById('analysisWorkspaceContainer');
        const previewCard = document.getElementById('previewCard');
        const progressCard = document.getElementById('progressCard');
        const resultsCard = document.getElementById('resultsCard');

        const btnCheck = document.getElementById('btnCheckProduct');
        const btnStart = document.getElementById('btnStartAnalysis');

        const isLoggedIn = !!API.getToken();

        // 1. Manage Hero Landing vs Authenticated Workspace visibility
        if (isLoggedIn) {
            if (landing) landing.classList.add('d-none');
            if (workspace) workspace.classList.remove('d-none');
        } else {
            if (landing) landing.classList.remove('d-none');
            if (workspace) workspace.classList.add('d-none');
        }

        // 2. Manage Workspace Inner State Cards
        if (newState === 'IDLE') {
            if (previewCard) previewCard.classList.add('d-none');
            if (progressCard) progressCard.classList.add('d-none');
            if (resultsCard) resultsCard.classList.add('d-none');

            if (btnCheck) btnCheck.disabled = false;
            if (btnStart) btnStart.disabled = true;
            LoadingManager.resetConsole();
            LoadingManager.stopTimer();

        } else if (newState === 'PREVIEW') {
            if (previewCard) previewCard.classList.remove('d-none');
            if (progressCard) progressCard.classList.add('d-none');
            if (resultsCard) resultsCard.classList.add('d-none');

            if (btnCheck) btnCheck.disabled = true;
            if (btnStart) btnStart.disabled = false;

        } else if (newState === 'LOADING') {
            if (previewCard) previewCard.classList.add('d-none');
            if (progressCard) progressCard.classList.remove('d-none');
            if (resultsCard) resultsCard.classList.add('d-none');

            if (btnCheck) btnCheck.disabled = true;
            if (btnStart) btnStart.disabled = true;

            LoadingManager.startTimer();
            this.setFinishScrapingButtonState('STOP_SCRAPING');

        } else if (newState === 'SUCCESS') {
            if (previewCard) previewCard.classList.add('d-none');
            if (progressCard) progressCard.classList.add('d-none');
            if (resultsCard) resultsCard.classList.remove('d-none');

            if (btnCheck) btnCheck.disabled = false;
            if (btnStart) btnStart.disabled = true;

            LoadingManager.stopTimer();
            this.setFinishScrapingButtonState('DONE');

            if (payload) {
                this.currentAnalysisData = payload;
                this.renderDashboardResults(payload);
            }

        } else if (newState === 'ERROR') {
            if (btnCheck) btnCheck.disabled = false;
            if (btnStart) btnStart.disabled = false;
            LoadingManager.stopTimer();
            this.setFinishScrapingButtonState('DISABLED');
            if (payload && typeof payload === 'string') {
                this.showAlert(payload, 'danger');
            }
        }

        this.updateAuthNavbar(API.getUserInfo());
    },

    setFinishScrapingButtonState(btnState) {
        const btn = document.getElementById('btnFinishScraping');
        if (!btn) return;

        if (btnState === 'STOP_SCRAPING') {
            btn.disabled = false;
            btn.className = 'btn btn-outline-warning w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-hand me-2"></i> Finish Scraping (Proceed to AI Processing)';
        } else if (btnState === 'PROCESSING') {
            btn.disabled = true;
            btn.className = 'btn btn-warning w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Processing AI Predictions...';
        } else if (btnState === 'DONE') {
            btn.disabled = true;
            btn.className = 'btn btn-success w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i> Analysis Complete';
        } else {
            btn.disabled = true;
            btn.className = 'btn btn-outline-secondary w-100 py-2 font-weight-bold border-2';
            btn.innerHTML = '<i class="fa-solid fa-hand me-2"></i> Finish Scraping';
        }
    },

    extractScore(val, altScoreKey = 'score') {
        if (typeof val === 'number') return val;
        if (val && typeof val[altScoreKey] === 'number') return val[altScoreKey];
        if (val && typeof val.score === 'number') return val.score;
        if (val && typeof val.risk_score === 'number') return val.risk_score;
        return parseFloat(val) || 0.0;
    },

    extractLevel(val) {
        if (typeof val === 'string') return val;
        if (val && typeof val.level === 'string') return val.level;
        return 'MEDIUM';
    },

    renderDashboardResults(resultData) {
        if (!resultData) return;

        const risks = resultData.risks || {};
        const stats = resultData.statistics || {};
        const metrics = resultData.metrics || {};
        const revStats = stats.reviewStatistics || stats.sentimentStatistics || {};

        const briVal = this.extractScore(risks.businessRiskIndex ?? risks.business_risk_index);
        const briLevel = this.extractLevel(risks.overallRiskLevel || risks.businessRiskLevel || risks.business_risk_level);

        const briElem = document.getElementById('businessRiskIndexVal');
        const badgeElem = document.getElementById('businessRiskLevelBadge');

        if (briElem) briElem.textContent = typeof briVal === 'number' ? briVal.toFixed(1) : parseFloat(briVal).toFixed(1);
        if (badgeElem) {
            badgeElem.textContent = `${briLevel} RISK`;
            badgeElem.className = `badge fs-5 px-4 py-2 text-uppercase ${this.getRiskBadgeClass(briLevel)}`;
        }

        // Summary Counts
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

        // Individual Aspect Risk Cards
        const qScore = this.extractScore(risks.qualityRisk ?? risks.quality_risk ?? risks.qualityRiskScore);
        const qLevel = this.extractLevel(risks.qualityRisk ?? risks.quality_risk);
        const dScore = this.extractScore(risks.deliveryRisk ?? risks.delivery_risk ?? risks.deliveryRiskScore);
        const dLevel = this.extractLevel(risks.deliveryRisk ?? risks.delivery_risk);
        const tScore = this.extractScore(risks.trustRisk ?? risks.trust_risk ?? risks.trustRiskScore);
        const tLevel = this.extractLevel(risks.trustRisk ?? risks.trust_risk);

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

        // Render Visual Charts
        ChartManager.renderAllCharts(stats, metrics, risks);

        // Render Recommendation Panel
        RecommendationManager.renderRecommendationPanel(resultData.recommendation);

        // Render Interactive Review Explorer
        ReviewExplorerManager.init(resultData);
    },

    getRiskBadgeClass(level) {
        const lvl = String(level || '').toUpperCase();
        if (lvl === 'VERY_LOW' || lvl === 'LOW') return 'bg-success text-white';
        if (lvl === 'MEDIUM') return 'bg-warning text-dark';
        if (lvl === 'HIGH' || lvl === 'CRITICAL') return 'bg-danger text-white';
        return 'bg-secondary text-white';
    },

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

    onUnauthorized() {
        this.setState('IDLE');
        this.openAuthModal('login');
        this.showAuthAlert('Session expired or authentication required. Please log in.', 'danger');
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
    }
};

window.DashboardController = DashboardController;
