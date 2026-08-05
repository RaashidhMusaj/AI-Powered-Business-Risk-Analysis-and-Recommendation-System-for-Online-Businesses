/**
 * API Service Client Module (Milestone 11.1)
 * Encapsulates backend REST endpoints, JWT authorization tokens, and request handling.
 */
const API = {
    getToken() {
        return localStorage.getItem('access_token');
    },

    setToken(token) {
        localStorage.setItem('access_token', token);
    },

    clearToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
    },

    getUserInfo() {
        try {
            return JSON.parse(localStorage.getItem('user_info') || 'null');
        } catch (e) {
            return null;
        }
    },

    setUserInfo(user) {
        localStorage.setItem('user_info', JSON.stringify(user));
    },

    async request(url, options = {}) {
        const token = this.getToken();
        const headers = options.headers || {};

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        options.headers = headers;

        try {
            const response = await fetch(url, options);
            const data = await response.json().catch(() => ({}));

            if (response.status === 401) {
                this.clearToken();
                if (window.DashboardController && typeof window.DashboardController.onUnauthorized === 'function') {
                    window.DashboardController.onUnauthorized();
                }
            }

            if (!response.ok) {
                const errMsg = data.message || (data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `HTTP ${response.status} Error`);
                throw new Error(errMsg);
            }

            return data;
        } catch (err) {
            throw err;
        }
    },

    // --- Authentication REST Endpoints ---
    async login(emailOrUsername, password) {
        const res = await this.request('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ emailOrUsername, password })
        });
        if (res.success && res.data && res.data.accessToken) {
            this.setToken(res.data.accessToken);
            this.setUserInfo({
                id: res.data.userId,
                username: res.data.username,
                email: res.data.email
            });
        }
        return res;
    },

    async register(data) {
        const res = await this.request('/api/v1/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (res.success && res.data && res.data.accessToken) {
            this.setToken(res.data.accessToken);
            this.setUserInfo({
                id: res.data.userId,
                username: res.data.username,
                email: res.data.email
            });
        }
        return res;
    },

    async forgotPassword(email) {
        return await this.request('/api/v1/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    },

    async resetPassword(email, otpCode, newPassword) {
        const res = await this.request('/api/v1/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ email, otpCode, newPassword })
        });
        if (res.success && res.data && res.data.accessToken) {
            this.setToken(res.data.accessToken);
            this.setUserInfo({
                id: res.data.userId,
                username: res.data.username,
                email: res.data.email
            });
        }
        return res;
    },

    async getProfile() {
        return await this.request('/api/v1/profile');
    },

    // --- Business Risk Analysis REST Endpoints ---
    async checkProduct(productUrl) {
        return await this.request('/api/v1/analysis/check-product', {
            method: 'POST',
            body: JSON.stringify({ productUrl })
        });
    },

    async startAnalysis(productUrl) {
        return await this.request('/api/v1/analysis/start', {
            method: 'POST',
            body: JSON.stringify({ productUrl, options: { saveHistory: true } })
        });
    },

    async finishScraping(analysisId) {
        return await this.request('/api/v1/analysis/stop', {
            method: 'POST',
            body: JSON.stringify({ analysisId })
        });
    },

    async getJobStatus(analysisId) {
        return await this.request(`/api/v1/analysis/status/${analysisId}`);
    },

    async getJobResult(analysisId) {
        return await this.request(`/api/v1/analysis/result/${analysisId}`);
    },

    // --- Historical Analyses Endpoints ---
    async getHistory(page = 1, limit = 10) {
        return await this.request(`/api/v1/history?page=${page}&limit=${limit}`);
    },

    async getHistoryDetail(analysisId) {
        return await this.request(`/api/v1/history/${analysisId}`);
    },

    async deleteHistory(analysisId) {
        return await this.request(`/api/v1/history/${analysisId}`, {
            method: 'DELETE'
        });
    },

    // --- Products & Trend Analytics Endpoints (Phase 12) ---
    async getProducts(page = 1, limit = 20) {
        return await this.request(`/api/v1/products?page=${page}&limit=${limit}`);
    },

    async getProductTrend(productId, limit = 20) {
        return await this.request(`/api/v1/products/${productId}/trend?limit=${limit}`);
    },

    async compareAnalyses(productId, fromId, toId) {
        return await this.request(`/api/v1/products/${productId}/compare?from=${fromId}&to=${toId}`);
    }
};

window.API = API;
