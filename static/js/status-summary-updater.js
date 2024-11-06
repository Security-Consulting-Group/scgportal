class StatusSummaryUpdater {
    constructor() {
        this.isRefreshing = false;
        this.initializeListeners();
        // Load initial data once
        this.refreshStatusCounts();
    }

    initializeListeners() {
        document.addEventListener('statusUpdated', (event) => {
            if (!this.isRefreshing) {
                this.refreshStatusCounts();
            }
        });
    }

    async refreshStatusCounts() {
        if (this.isRefreshing) return;

        try {
            this.isRefreshing = true;
            const url = new URL(window.location.href);
            url.searchParams.set('counts_only', 'true');
            
            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            this.updateSummaryTable(data.status_summary);
        } catch (error) {
            console.error('Error refreshing status counts:', error);
        } finally {
            this.isRefreshing = false;
        }
    }

    updateSummaryTable(statusSummary) {
        const tbody = document.querySelector('.status-summary tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        Object.entries(statusSummary).forEach(([status, data]) => {
            if (data.count > 0) {
                const row = document.createElement('tr');
                row.dataset.status = status;
                row.innerHTML = `
                    <td>
                        <span class="status-${status} status-badge">${data.label}</span>
                    </td>
                    <td class="text-end status-summary-count" data-status="${status}">${data.count}</td>
                `;
                tbody.appendChild(row);
            }
        });
    }
}

// Only create one instance
window.statusUpdater = new StatusSummaryUpdater();