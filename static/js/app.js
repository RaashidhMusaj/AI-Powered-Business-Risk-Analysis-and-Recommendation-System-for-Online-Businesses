/**
 * Main Application Orchestrator (Milestone 11.2, 11.7, 11.10)
 * Connects DOM events, user interactions, polling timers, and state machine transitions.
 */
document.addEventListener('DOMContentLoaded', () => {
    let currentAnalysisId = null;
    let pollInterval = null;

    // --- 1. Initialize App State ---
    initApp();

    async function initApp() {
        DashboardController.init();
        const token = API.getToken();
        if (token) {
            try {
                const res = await API.getProfile();
                if (res.success && res.data) {
                    API.setUserInfo(res.data);
                    DashboardController.setState('IDLE');
                    loadHistoryTable();
                    return;
                }
            } catch (err) {
                console.warn('Stored token is invalid or expired:', err);
                API.clearToken();
            }
        }
        DashboardController.setState('IDLE');
    }

    // --- 2. Top Bar Navigation Listeners ---
    const brandLogoBtn = document.getElementById('brandLogoBtn');
    if (brandLogoBtn) {
        brandLogoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            DashboardController.setState('IDLE');
        });
    }

    const btnHeroAnalyze = document.getElementById('btnHeroAnalyze');
    if (btnHeroAnalyze) {
        btnHeroAnalyze.addEventListener('click', () => {
            if (API.getToken()) {
                const input = document.getElementById('productUrlInput');
                if (input) input.focus();
            } else {
                DashboardController.openAuthModal('login');
                DashboardController.showAuthAlert('Please log in or register to analyze products.', 'info');
            }
        });
    }

    const btnNavWorkspace = document.getElementById('btnNavWorkspace');
    if (btnNavWorkspace) {
        btnNavWorkspace.addEventListener('click', () => {
            DashboardController.setState('IDLE');
            loadHistoryTable();
        });
    }

    const btnNavLogout = document.getElementById('btnNavLogout');
    if (btnNavLogout) {
        btnNavLogout.addEventListener('click', () => {
            API.clearToken();
            DashboardController.setState('IDLE');
            DashboardController.showAlert('You have been logged out.', 'success');
        });
    }

    // --- 3. Auth Form Event Handlers ---
    const btnSubmitLogin = document.getElementById('btnSubmitLogin');
    if (btnSubmitLogin) btnSubmitLogin.addEventListener('click', handleLoginSubmit);

    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', (e) => { e.preventDefault(); handleLoginSubmit(); });

    async function handleLoginSubmit() {
        const identifierElem = document.getElementById('loginIdentifier');
        const passwordElem = document.getElementById('loginPassword');
        const identifier = identifierElem ? identifierElem.value.trim() : '';
        const password = passwordElem ? passwordElem.value : '';

        if (!identifier || !password) {
            DashboardController.showAuthAlert('Please enter your email/username and password.', 'danger');
            return;
        }

        DashboardController.hideAuthAlert();
        btnSubmitLogin.disabled = true;
        btnSubmitLogin.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Logging in...';

        try {
            const res = await API.login(identifier, password);
            if (res.success && res.data) {
                DashboardController.closeAuthModal();
                DashboardController.setState('IDLE');
                DashboardController.showAlert(`Welcome back, ${res.data.username}!`, 'success');
                loadHistoryTable();
                if (identifierElem) identifierElem.value = '';
                if (passwordElem) passwordElem.value = '';
            } else {
                DashboardController.showAuthAlert(res.message || 'Login failed. Check credentials.', 'danger');
            }
        } catch (err) {
            DashboardController.showAuthAlert(err.message || 'Login failed.', 'danger');
        } finally {
            btnSubmitLogin.disabled = false;
            btnSubmitLogin.innerHTML = '<i class="fa-solid fa-right-to-bracket me-2"></i> Log In to Account';
        }
    }

    const btnSubmitRegister = document.getElementById('btnSubmitRegister');
    if (btnSubmitRegister) btnSubmitRegister.addEventListener('click', handleRegisterSubmit);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) registerForm.addEventListener('submit', (e) => { e.preventDefault(); handleRegisterSubmit(); });

    async function handleRegisterSubmit() {
        const fullNameElem = document.getElementById('registerFullName');
        const emailElem = document.getElementById('registerEmail');
        const usernameElem = document.getElementById('registerUsername');
        const passwordElem = document.getElementById('registerPassword');

        const fullName = fullNameElem ? fullNameElem.value.trim() : '';
        const email = emailElem ? emailElem.value.trim() : '';
        const username = usernameElem ? usernameElem.value.trim() : '';
        const password = passwordElem ? passwordElem.value : '';

        if (!email || !username || !password) {
            DashboardController.showAuthAlert('Please complete all required fields.', 'danger');
            return;
        }

        DashboardController.hideAuthAlert();
        btnSubmitRegister.disabled = true;
        btnSubmitRegister.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Creating account...';

        try {
            const res = await API.register({ email, username, password, fullName });
            if (res.success && res.data) {
                DashboardController.closeAuthModal();
                DashboardController.setState('IDLE');
                DashboardController.showAlert(`Account created! Welcome, ${res.data.username}.`, 'success');
                loadHistoryTable();
            } else {
                DashboardController.showAuthAlert(res.message || 'Registration failed.', 'danger');
            }
        } catch (err) {
            DashboardController.showAuthAlert(err.message || 'Registration failed.', 'danger');
        } finally {
            btnSubmitRegister.disabled = false;
            btnSubmitRegister.innerHTML = '<i class="fa-solid fa-user-plus me-2"></i> Create Account';
        }
    }

    // --- 4. Product Analysis Workflows ---
    const btnCheckProduct = document.getElementById('btnCheckProduct');
    if (btnCheckProduct) btnCheckProduct.addEventListener('click', handleCheckProduct);

    const btnClear = document.getElementById('btnClear');
    if (btnClear) btnClear.addEventListener('click', () => DashboardController.setState('IDLE'));

    const btnStartAnalysis = document.getElementById('btnStartAnalysis');
    if (btnStartAnalysis) btnStartAnalysis.addEventListener('click', handleStartAnalysis);

    const btnFinishScraping = document.getElementById('btnFinishScraping');
    if (btnFinishScraping) btnFinishScraping.addEventListener('click', handleFinishScraping);

    const btnRefreshHistory = document.getElementById('btnRefreshHistory');
    if (btnRefreshHistory) btnRefreshHistory.addEventListener('click', loadHistoryTable);

    // Check Product Preview
    async function handleCheckProduct() {
        const input = document.getElementById('productUrlInput');
        const url = input ? input.value.trim() : '';

        if (!url) {
            DashboardController.showAlert('Please enter a valid Daraz product URL.', 'danger');
            return;
        }

        btnCheckProduct.disabled = true;
        btnCheckProduct.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Fetching...';

        try {
            const res = await API.checkProduct(url);
            if (res.success && res.data) {
                const prod = res.data.product || res.data || {};
                
                const titleElem = document.getElementById('previewTitle');
                const sellerElem = document.getElementById('previewSeller');
                const ratingElem = document.getElementById('previewRating');
                const reviewsElem = document.getElementById('previewReviews');
                const categoryElem = document.getElementById('previewCategory');
                const visitBtn = document.getElementById('btnVisitProduct');
                const imageElem = document.getElementById('previewImage');

                const extractedTitle = prod.title || prod.productTitle || prod.product_name;
                const extractedSeller = prod.seller || prod.sellerName || prod.seller_name;
                const rawRating = prod.overallRating ?? prod.rating ?? prod.overall_rating;
                const ratingVal = typeof rawRating === 'number' ? rawRating : parseFloat(rawRating) || 0.0;
                const extractedReviews = prod.totalReviews ?? prod.reviewCount ?? prod.total_reviews ?? 0;
                const extractedCategory = prod.category || 'General';

                if (titleElem) titleElem.textContent = extractedTitle || 'Daraz Product';
                if (sellerElem) sellerElem.textContent = extractedSeller || 'Daraz Seller';
                if (ratingElem) ratingElem.textContent = ratingVal > 0 ? ratingVal.toFixed(1) : 'N/A';
                if (reviewsElem) reviewsElem.textContent = extractedReviews;
                if (categoryElem) categoryElem.textContent = `Category: ${extractedCategory}`;
                if (visitBtn) visitBtn.href = url;

                const fallbackImg = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80';
                if (imageElem) {
                    imageElem.classList.remove('d-none');
                    imageElem.src = prod.imageUrl || prod.image_url || fallbackImg;
                    imageElem.onerror = function () {
                        this.onerror = null;
                        this.src = fallbackImg;
                    };
                }

                DashboardController.setState('PREVIEW');
            } else {
                DashboardController.setState('ERROR', res.message || 'Unable to fetch product preview.');
            }
        } catch (err) {
            DashboardController.setState('ERROR', err.message || 'Product check failed.');
        } finally {
            btnCheckProduct.disabled = false;
            btnCheckProduct.innerHTML = '<i class="fa-solid fa-magnifying-glass me-2"></i> Check Product';
        }
    }

    // Start Analysis Job
    async function handleStartAnalysis() {
        const input = document.getElementById('productUrlInput');
        const url = input ? input.value.trim() : '';

        if (!url) return;

        DashboardController.setState('LOADING');

        try {
            const res = await API.startAnalysis(url);
            if (res.success && res.data && res.data.analysisId) {
                currentAnalysisId = res.data.analysisId;
                startPolling(currentAnalysisId);
            } else {
                DashboardController.setState('ERROR', res.message || 'Failed to start analysis job.');
            }
        } catch (err) {
            DashboardController.setState('ERROR', err.message || 'Failed to start analysis job.');
        }
    }

    // Stop Scraping & Force Proceed
    async function handleFinishScraping() {
        if (!currentAnalysisId) return;

        DashboardController.setFinishScrapingButtonState('PROCESSING');
        try {
            await API.finishScraping(currentAnalysisId);
        } catch (err) {
            console.warn('Finish scraping notice:', err);
        }
    }

    // Polling Loop for Job Status & Completion
    function startPolling(analysisId) {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const res = await API.getJobStatus(analysisId);
                if (res.success && res.data) {
                    const statusData = res.data;
                    const status = (statusData.status || '').toUpperCase();
                    const progress = statusData.progressPercentage ?? 0;
                    const stage = statusData.stage || status;
                    const logs = statusData.logs || [];

                    LoadingManager.updateProgress(progress, stage, `Pipeline Stage: ${stage}`);
                    LoadingManager.appendConsoleLogs(logs);

                    if (status === 'COMPLETED' || status === 'SUCCESS') {
                        clearInterval(pollInterval);
                        pollInterval = null;
                        fetchFinalResult(analysisId);
                    } else if (status === 'FAILED' || status === 'ERROR') {
                        clearInterval(pollInterval);
                        pollInterval = null;
                        DashboardController.setState('ERROR', statusData.errorMessage || 'Analysis processing failed.');
                    }
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 1000);
    }

    async function fetchFinalResult(analysisId) {
        try {
            const res = await API.getJobResult(analysisId);
            if (res.success && res.data) {
                DashboardController.setState('SUCCESS', res.data);
                loadHistoryTable();
            } else {
                DashboardController.setState('ERROR', res.message || 'Could not fetch final analysis result.');
            }
        } catch (err) {
            DashboardController.setState('ERROR', err.message || 'Error fetching analysis result.');
        }
    }

    // --- 5. Analysis History Table Loader ---
    async function loadHistoryTable() {
        const tbody = document.getElementById('historyTableBody');
        if (!tbody) return;

        try {
            const res = await API.getHistory(1, 10);
            if (res.success && res.data && Array.isArray(res.data.items)) {
                renderHistoryTable(res.data.items);
                if (window.TrendManager) {
                    TrendManager.loadTrendChart('all');
                    TrendManager.bindAspectToggles();
                }
                if (window.ComparisonManager) {
                    ComparisonManager.loadComparisonOptions(res.data.items);
                }
            } else {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No historical analyses found.</td></tr>';
            }
        } catch (err) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Unable to load history table.</td></tr>';
        }
    }

    function renderHistoryTable(items = []) {
        const tbody = document.getElementById('historyTableBody');
        if (!tbody) return;

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No analysis records stored.</td></tr>';
            return;
        }

        tbody.innerHTML = items.map(item => {
            const level = item.businessRiskLevel || item.riskLevel || 'MEDIUM';
            const badgeClass = DashboardController.getRiskBadgeClass(level);
            const pubId = item.analysisId || item.publicId || item.id || '-';
            const title = item.productTitle || item.title || 'Daraz Product';
            const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString() : 'Recent';

            return `
                <tr>
                    <td class="font-monospace small"><strong>${pubId.substring(0, 12)}...</strong></td>
                    <td><div class="text-truncate" style="max-width: 220px;" title="${title}">${title}</div></td>
                    <td><strong>${(item.businessRiskIndex ?? 0).toFixed(1)}</strong></td>
                    <td><span class="badge ${badgeClass}">${level}</span></td>
                    <td>${item.totalReviews ?? 0}</td>
                    <td class="small text-muted">${dateStr}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="window.loadHistoricalDetail('${pubId}')">
                            <i class="fa-solid fa-folder-open me-1"></i> View
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="window.deleteHistoricalDetail('${pubId}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    window.loadHistoricalDetail = async function(analysisId) {
        try {
            const res = await API.getHistoryDetail(analysisId);
            if (res.success && res.data) {
                DashboardController.setState('SUCCESS', res.data);
            }
        } catch (err) {
            DashboardController.showAlert('Failed to load analysis details.', 'danger');
        }
    };

    window.deleteHistoricalDetail = async function(analysisId) {
        if (!confirm('Are you sure you want to delete this historical analysis?')) return;
        try {
            await API.deleteHistory(analysisId);
            DashboardController.showAlert('Analysis record deleted.', 'success');
            loadHistoryTable();
        } catch (err) {
            DashboardController.showAlert('Failed to delete analysis record.', 'danger');
        }
    };

    // --- 6. Review Explorer Filters Event Wiring ---
    const sentTabs = document.querySelectorAll('#reviewSentimentTabs .nav-link');
    sentTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            sentTabs.forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            const sent = e.currentTarget.getAttribute('data-sentiment') || 'ALL';
            ReviewExplorerManager.setSentimentFilter(sent);
        });
    });

    const aspectSelect = document.getElementById('reviewAspectSelect');
    if (aspectSelect) {
        aspectSelect.addEventListener('change', (e) => {
            ReviewExplorerManager.setAspectFilter(e.target.value);
        });
    }
});
