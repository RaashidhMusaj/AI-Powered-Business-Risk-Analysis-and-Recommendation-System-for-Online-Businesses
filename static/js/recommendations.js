/**
 * Recommendation Panel Component (Milestone 11.5)
 * Dynamically renders the Recommendation Engine report: Executive Summary, Key Insights, and Recommended Actions.
 */
const RecommendationManager = {
    renderRecommendationPanel(recommendationData) {
        const panelElem = document.getElementById('recommendationPanel');
        if (!panelElem) return;

        if (!recommendationData || !recommendationData.report) {
            panelElem.innerHTML = `
                <div class="alert alert-secondary text-center py-4 rounded-4">
                    <i class="fa-solid fa-lightbulb text-muted fa-2xl mb-2 d-block"></i>
                    No recommendation report generated for this analysis.
                </div>
            `;
            return;
        }

        const report = recommendationData.report || {};
        const metadata = recommendationData.metadata || {};

        const version = recommendationData.version || 'v1';
        const procTime = recommendationData.processingTimeMs ?? 0;
        const highestPriority = metadata.highestPriority || 'NORMAL';

        // 1. Executive Summary Header
        const summaryText = report.summary || 'Business risk evaluation completed. Review recommended actions below.';

        // 2. Insights List
        const insights = report.insights || [];
        const insightsHtml = insights.length > 0 ? insights.map(insight => {
            const isObj = typeof insight === 'object' && insight !== null;
            const aspect = (isObj ? (insight.aspect || 'GENERAL') : 'GENERAL').toUpperCase();
            const tagClass = this.getAspectTagClass(aspect);
            const text = isObj ? (insight.description || insight.title || JSON.stringify(insight)) : insight;
            return `
                <div class="p-3 bg-light rounded-3 border mb-2 d-flex align-items-start gap-2 shadow-sm">
                    <span class="badge ${tagClass} mt-1">${aspect}</span>
                    <div class="small text-dark">${text}</div>
                </div>
            `;
        }).join('') : '<div class="text-muted small">No specific aspect insights generated.</div>';

        // 3. Actions List (Sorted by Priority)
        const actions = report.actions || [];
        const sortedActions = [...actions].sort((a, b) => {
            const pOrder = { 'IMMEDIATE': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4, 'NORMAL': 4 };
            const pA = typeof a === 'object' && a ? (a.priority || 'NORMAL') : 'NORMAL';
            const pB = typeof b === 'object' && b ? (b.priority || 'NORMAL') : 'NORMAL';
            return (pOrder[pA] || 5) - (pOrder[pB] || 5);
        });

        const actionsHtml = sortedActions.length > 0 ? sortedActions.map(action => {
            const isObj = typeof action === 'object' && action !== null;
            const priority = (isObj ? (action.priority || 'NORMAL') : 'NORMAL').toUpperCase();
            const aspect = (isObj ? (action.aspect || 'GENERAL') : 'GENERAL').toUpperCase();
            const cardClass = this.getPriorityCardClass(priority);
            const badgeClass = this.getPriorityBadgeClass(priority);
            const tagClass = this.getAspectTagClass(aspect);

            const titleText = isObj ? (action.actionItem || action.title || action.action || 'Mitigation Action') : action;
            const descText = isObj ? (action.rationale || action.description || '') : '';
            const ruleIdText = isObj ? (action.ruleId || action.rule_id || 'RULE-01') : 'RECOMMENDATION';

            const actionableSteps = isObj ? (action.actionableSteps || action.actionable_steps || []) : [];
            const stepsHtml = Array.isArray(actionableSteps) && actionableSteps.length > 0 ? `
                <div class="mt-2 pt-2 border-top">
                    <div class="small font-weight-bold text-muted mb-1"><i class="fa-solid fa-list-check me-1"></i> Actionable Mitigation Steps:</div>
                    <ul class="mb-0 ps-3 small text-dark">
                        ${actionableSteps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                </div>
            ` : '';

            return `
                <div class="card bg-white shadow-sm rounded-3 mb-3 recommendation-card ${cardClass}">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <span class="badge ${badgeClass} px-3 py-1 font-weight-bold text-uppercase">${priority} PRIORITY</span>
                                <span class="badge ${tagClass}">${aspect}</span>
                            </div>
                            <small class="text-muted">ID: ${ruleIdText}</small>
                        </div>
                        <h6 class="font-weight-bold text-dark mb-1">${titleText}</h6>
                        ${descText ? `<p class="small text-muted mb-2">${descText}</p>` : ''}
                        ${stepsHtml}
                    </div>
                </div>
            `;
        }).join('') : '<div class="text-muted small">No recommended mitigation actions required. Maintain existing business controls.</div>';

        // Render Panel HTML
        panelElem.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4 mb-4 fade-in">
                <div class="card-header bg-dark text-white rounded-top-4 py-3 d-flex justify-content-between align-items-center">
                    <h5 class="mb-0 font-weight-bold d-flex align-items-center">
                        <i class="fa-solid fa-lightbulb text-warning me-2"></i> Recommendation Engine Report
                    </h5>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge ${this.getPriorityBadgeClass(highestPriority)} px-3 py-2 text-uppercase fs-6">
                            Highest Priority: ${highestPriority}
                        </span>
                        <span class="badge bg-secondary px-2 py-2 fs-6">Engine ${version} (${procTime}ms)</span>
                    </div>
                </div>
                <div class="card-body p-4">
                    <!-- Executive Summary Box -->
                    <div class="p-4 bg-primary-subtle rounded-4 border border-primary-subtle mb-4">
                        <h6 class="text-uppercase text-primary font-weight-bold tracking-wide mb-2">
                            <i class="fa-solid fa-file-contract me-1"></i> Executive Summary
                        </h6>
                        <p class="lead fs-6 text-dark mb-0 font-weight-medium">${summaryText}</p>
                    </div>

                    <!-- Key Insights Section -->
                    <div class="mb-4">
                        <h6 class="font-weight-bold text-dark mb-3">
                            <i class="fa-solid fa-magnifying-glass-chart text-info me-1"></i> Key Risk Insights
                        </h6>
                        ${insightsHtml}
                    </div>

                    <!-- Recommended Actions Section -->
                    <div>
                        <h6 class="font-weight-bold text-dark mb-3">
                            <i class="fa-solid fa-list-check text-success me-1"></i> Priority Action Recommendations
                        </h6>
                        ${actionsHtml}
                    </div>
                </div>
            </div>
        `;
    },

    getPriorityCardClass(priority) {
        const p = String(priority).toUpperCase();
        if (p === 'IMMEDIATE') return 'priority-immediate';
        if (p === 'HIGH') return 'priority-high';
        if (p === 'MEDIUM') return 'priority-medium';
        return 'priority-normal';
    },

    getPriorityBadgeClass(priority) {
        const p = String(priority).toUpperCase();
        if (p === 'IMMEDIATE') return 'badge-priority-immediate';
        if (p === 'HIGH') return 'badge-priority-high';
        if (p === 'MEDIUM') return 'badge-priority-medium';
        return 'badge-priority-normal';
    },

    getAspectTagClass(aspect) {
        const a = String(aspect).toUpperCase();
        if (a === 'QUALITY') return 'aspect-tag-quality';
        if (a === 'DELIVERY') return 'aspect-tag-delivery';
        if (a === 'TRUST') return 'aspect-tag-trust';
        return 'aspect-tag-general';
    }
};

window.RecommendationManager = RecommendationManager;
