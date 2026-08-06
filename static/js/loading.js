/**
 * Loading Controller Component (Milestone 11.3)
 * Manages step-by-step pipeline progress checklist, stepper UI, progress bar, and live terminal logs.
 */
const LoadingManager = {
    renderedLogsCount: 0,
    startTime: null,
    timerInterval: null,

    startTimer() {
        this.startTime = Date.now();
        const elapsedElem = document.getElementById('elapsedTimeText');
        if (this.timerInterval) clearInterval(this.timerInterval);

        this.timerInterval = setInterval(() => {
            if (!this.startTime || !elapsedElem) return;
            const diffSec = Math.floor((Date.now() - this.startTime) / 1000);
            const mins = String(Math.floor(diffSec / 60)).padStart(2, '0');
            const secs = String(diffSec % 60).padStart(2, '0');
            elapsedElem.textContent = `00:${mins}:${secs}`;
        }, 1000);
    },

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    },

    resetConsole() {
        const consoleElem = document.getElementById('processingConsole');
        if (consoleElem) {
            consoleElem.innerHTML = '<div class="text-muted mb-1">[SYSTEM] Analysis Job Initialized.</div>';
        }
        this.renderedLogsCount = 0;
    },

    updateChecklist(stepIndex) {
        // Steps: 1 = Scraper, 2 = XLM-R Sentiment AI, 3 = Fuzzy FIS Risk, 4 = Recommendations
        for (let i = 1; i <= 4; i++) {
            const stepCol = document.getElementById(`step${i}`);
            const iconElem = document.getElementById(`stepIcon${i}`);
            if (!stepCol) continue;

            if (i < stepIndex) {
                stepCol.className = 'col stepper-step completed text-success';
                if (iconElem) iconElem.className = 'fa-solid fa-check';
            } else if (i === stepIndex) {
                stepCol.className = 'col stepper-step active text-primary';
                if (iconElem) {
                    if (i === 1) iconElem.className = 'fa-solid fa-spider fa-spin';
                    else if (i === 2) iconElem.className = 'fa-solid fa-brain fa-pulse';
                    else if (i === 3) iconElem.className = 'fa-solid fa-diagram-project fa-spin';
                    else iconElem.className = 'fa-solid fa-lightbulb fa-beat';
                }
            } else {
                stepCol.className = 'col stepper-step text-muted';
                if (iconElem) {
                    if (i === 1) iconElem.className = 'fa-solid fa-spider';
                    else if (i === 2) iconElem.className = 'fa-solid fa-brain';
                    else if (i === 3) iconElem.className = 'fa-solid fa-diagram-project';
                    else iconElem.className = 'fa-solid fa-lightbulb';
                }
            }
        }
    },

    updateProgress(progressPercent, stageName, currentText) {
        const pBar = document.getElementById('progressBar');
        const stageBadge = document.getElementById('stageBadge');
        const stepText = document.getElementById('currentStepText');

        if (pBar) {
            pBar.style.width = `${progressPercent}%`;
            pBar.textContent = `${Math.round(progressPercent)}%`;
            pBar.setAttribute('aria-valuenow', progressPercent);
        }

        if (stageBadge && stageName) stageBadge.textContent = stageName.toUpperCase();
        if (stepText && currentText) stepText.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-1 text-primary"></i> ${currentText}`;

        // Map percentage to step index
        if (progressPercent < 40) this.updateChecklist(1);
        else if (progressPercent < 75) this.updateChecklist(2);
        else if (progressPercent < 95) this.updateChecklist(3);
        else this.updateChecklist(4);
    },

    appendConsoleLogs(logs = []) {
        const consoleElem = document.getElementById('processingConsole');
        if (!consoleElem || !Array.isArray(logs)) return;

        if (logs.length > this.renderedLogsCount) {
            const newLogs = logs.slice(this.renderedLogsCount);
            newLogs.forEach(log => {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'mb-1';
                if (log.includes('[ERROR]')) lineDiv.className = 'text-danger font-weight-bold mb-1';
                else if (log.includes('[SCRAPER]')) lineDiv.className = 'text-info mb-1';
                else if (log.includes('[AI_ENGINE]')) lineDiv.className = 'text-warning mb-1';
                else if (log.includes('[FIS]')) lineDiv.className = 'text-success mb-1';
                else if (log.includes('[RECOMMENDATION]')) lineDiv.className = 'text-primary font-weight-bold mb-1';
                lineDiv.textContent = log;
                consoleElem.appendChild(lineDiv);
            });
            this.renderedLogsCount = logs.length;
            consoleElem.scrollTop = consoleElem.scrollHeight;
        }
    }
};

window.LoadingManager = LoadingManager;
