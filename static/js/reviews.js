/**
 * Interactive Review Explorer Component (Milestone 11.7)
 * Allows filtering customer reviews by sentiment (Positive, Negative, Neutral), aspect (Quality, Delivery, Trust), and search keyword.
 */
const ReviewExplorerManager = {
    allReviews: [],
    currentSentimentFilter: 'ALL',
    currentAspectFilter: 'ALL',

    init(resultData) {
        this.allReviews = this.extractReviews(resultData);
        this.currentSentimentFilter = 'ALL';
        this.currentAspectFilter = 'ALL';
        this.render();
    },

    extractReviews(resultData) {
        if (!resultData) return [];

        let reviews = [];

        if (resultData.reviews && Array.isArray(resultData.reviews)) {
            reviews = resultData.reviews;
        } else if (resultData.negativeReviews && Array.isArray(resultData.negativeReviews)) {
            reviews = resultData.negativeReviews.map(r => typeof r === 'string' ? { reviewText: r, sentiment: 'NEGATIVE', aspect: 'GENERAL' } : r);
        }

        return reviews.map((r, idx) => {
            const rawAspect = r.aspect || (r.aspects && r.aspects.aspect) || (r.aspects && r.aspects.detected && r.aspects.detected[0]) || r.aspect_category || 'GENERAL';
            const confVal = typeof r.confidenceScore === 'number' ? r.confidenceScore : (typeof r.confidence_score === 'number' ? r.confidence_score : (typeof r.confidence === 'number' ? r.confidence : 0.85));

            return {
                id: r.id || `rev-${idx + 1}`,
                text: r.reviewText || r.review_text || (typeof r === 'string' ? r : 'No review content'),
                sentiment: (r.sentiment || 'NEUTRAL').toUpperCase(),
                aspect: String(rawAspect).toUpperCase(),
                confidence: confVal
            };
        });
    },

    setSentimentFilter(sentiment) {
        this.currentSentimentFilter = String(sentiment).toUpperCase();
        this.render();
    },

    setAspectFilter(aspect) {
        this.currentAspectFilter = String(aspect).toUpperCase();
        this.render();
    },

    getFilteredReviews() {
        const matchesFilter = (r) => {
            // Aspect Filter
            if (this.currentAspectFilter !== 'ALL') {
                if (!r.aspect.includes(this.currentAspectFilter) && !r.text.toUpperCase().includes(this.currentAspectFilter)) {
                    return false;
                }
            }

            return true;
        };

        if (this.currentSentimentFilter !== 'ALL') {
            const classFilter = this.currentSentimentFilter;
            const matching = this.allReviews.filter(r => {
                if (!matchesFilter(r)) return false;
                if (classFilter === 'POSITIVE' && !r.sentiment.includes('POS')) return false;
                if (classFilter === 'NEGATIVE' && !r.sentiment.includes('NEG')) return false;
                if (classFilter === 'NEUTRAL' && !r.sentiment.includes('NEU')) return false;
                return true;
            });

            matching.sort((a, b) => b.confidence - a.confidence);
            return matching.slice(0, 5);
        } else {
            // ALL Sentiments selected: extract max 5 reviews for EACH sentiment class
            const pos = [];
            const neg = [];
            const neu = [];

            this.allReviews.forEach(r => {
                if (!matchesFilter(r)) return;
                if (r.sentiment.includes('POS')) pos.push(r);
                else if (r.sentiment.includes('NEG')) neg.push(r);
                else neu.push(r);
            });

            pos.sort((a, b) => b.confidence - a.confidence);
            neg.sort((a, b) => b.confidence - a.confidence);
            neu.sort((a, b) => b.confidence - a.confidence);

            const topPos = pos.slice(0, 5);
            const topNeg = neg.slice(0, 5);
            const topNeu = neu.slice(0, 5);

            // Interleave round-robin so all sentiment classes are visibly represented
            const combined = [];
            const maxLen = Math.max(topPos.length, topNeg.length, topNeu.length);
            for (let i = 0; i < maxLen; i++) {
                if (i < topPos.length) combined.push(topPos[i]);
                if (i < topNeg.length) combined.push(topNeg[i]);
                if (i < topNeu.length) combined.push(topNeu[i]);
            }

            return combined;
        }
    },

    render() {
        const listElem = document.getElementById('reviewExplorerList');
        if (!listElem) return;

        const filtered = this.getFilteredReviews();

        if (filtered.length === 0) {
            listElem.innerHTML = `
                <div class="text-center text-muted py-4 bg-light rounded-3">
                    <i class="fa-solid fa-comment-slash fa-2xl mb-2 d-block"></i>
                    No customer reviews match your active filters.
                </div>
            `;
            return;
        }

        listElem.innerHTML = filtered.map(rev => {
            const isPos = rev.sentiment.includes('POS');
            const isNeg = rev.sentiment.includes('NEG');
            const borderClass = isPos ? 'border-start border-success border-4' : (isNeg ? 'border-start border-danger border-4' : 'border-start border-warning border-4');
            const badgeClass = isPos ? 'bg-success' : (isNeg ? 'bg-danger' : 'bg-warning text-dark');
            const icon = isPos ? 'fa-thumbs-up' : (isNeg ? 'fa-thumbs-down' : 'fa-minus');

            return `
                <div class="p-3 bg-white rounded-3 border ${borderClass} mb-2 shadow-sm review-item">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge ${badgeClass}"><i class="fa-solid ${icon} me-1"></i>${rev.sentiment}</span>
                            <span class="badge bg-light text-dark border">${rev.aspect}</span>
                        </div>
                        <small class="text-muted">Confidence: ${(rev.confidence * 100).toFixed(0)}%</small>
                    </div>
                    <div class="small text-dark mt-2">${rev.text}</div>
                </div>
            `;
        }).join('');
    }
};

window.ReviewExplorerManager = ReviewExplorerManager;
