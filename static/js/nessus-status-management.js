document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    function addStatusChangeListener(selector, bulkType) {
        document.querySelectorAll(selector).forEach(function(select) {
            select.addEventListener('change', function() {
                var data = {
                    status: this.value,
                    bulk_type: bulkType
                };
                if (bulkType === 'risk_factor') {
                    data.risk_factor = this.closest('.accordion-item').querySelector('.accordion-button').textContent.split('(')[0].trim();
                } else {
                    data.vulnerability_id = this.dataset.vulnerabilityId;
                }
                updateStatus(data);
            });
        });
    }

    addStatusChangeListener('.status-select', 'individual');
    addStatusChangeListener('.bulk-action-select', 'risk_factor');
    addStatusChangeListener('.bulk-action-vuln-select', 'vulnerability');

    function updateStatus(data) {
        const formData = new FormData();
        Object.keys(data).forEach(key => formData.append(key, data[key]));

        fetch(window.location.pathname, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updateUI(data.updated_vulnerabilities);
            } else {
                alert('Failed to update status: ' + data.error);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred while updating the status');
        });
    }

    function updateUI(updatedVulnerabilities) {
        updatedVulnerabilities.forEach(vuln => {
            const statusSelect = document.querySelector(`.status-select[data-vulnerability-id="${vuln.id}"]`);
            if (statusSelect) {
                statusSelect.value = vuln.status;
                statusSelect.classList.remove('status-not_started', 'status-in_review', 'status-monitoring', 'status-mitigated', 'status-fixed', 'status-risk_accepted');
                statusSelect.classList.add(`status-${vuln.status}`);

                if (statusBadge) {
                    statusBadge.className = `status-badge status-${vuln.status}`;
                    statusBadge.textContent = vuln.status.split('_').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                    ).join(' ');
                }

                // Simplified event dispatch
                document.dispatchEvent(new CustomEvent('statusUpdated'));
                
                const row = statusSelect.closest('tr');
                if (row) {
                    const changedByCell = row.querySelector('td:nth-child(3)');
                    const changedAtCell = row.querySelector('td:nth-child(4)');
                    if (changedByCell) changedByCell.textContent = vuln.changed_by;
                    if (changedAtCell) changedAtCell.textContent = formatDate(vuln.changed_at);
                }
            }
        });
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    }
});