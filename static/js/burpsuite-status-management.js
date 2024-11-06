document.addEventListener('DOMContentLoaded', function() {
    // Decode base64 request data
    document.querySelectorAll('.request-data pre').forEach(function(pre) {
        var encodedData = pre.textContent.trim();
        if (encodedData) {
            try {
                var decodedData = atob(encodedData);
                pre.textContent = decodedData;
            } catch (e) {
                console.error("Error decoding base64:", e);
            }
        }
    });
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    function addStatusChangeListener(selector, bulkType) {
        document.querySelectorAll(selector).forEach(function(select) {
            select.addEventListener('change', function() {
                var data = {
                    status: this.value,
                    bulk_type: bulkType,
                    vulnerability_id: this.dataset.vulnerabilityId
                };
                updateStatus(data);
            });
        });
    }

    addStatusChangeListener('.status-select', 'individual');
    addStatusChangeListener('.bulk-status-update', 'signature');

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
                
                const accordionItem = statusSelect.closest('.accordion-item');
                if (accordionItem) {
                    const instanceTags = accordionItem.querySelector('.instance-tags');
                    if (instanceTags) {
                        // Find or create status badge
                        let statusBadge = instanceTags.querySelector('.status-badge');
                        if (!statusBadge) {
                            statusBadge = document.createElement('span');
                            statusBadge.classList.add('status-badge', 'ms-2');
                            instanceTags.appendChild(statusBadge);
                        }
                        
                        // Update status badge
                        statusBadge.classList.remove('status-not_started', 'status-in_review', 'status-monitoring', 'status-mitigated', 'status-fixed', 'status-risk_accepted');
                        statusBadge.classList.add(`status-${vuln.status}`);
                        statusBadge.textContent = vuln.status.split('_')
                            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                            .join(' ');
                    }
                }

                // Simplified event dispatch
                document.dispatchEvent(new CustomEvent('statusUpdated'));
                
                // Update last changed info
                const changedBySpan = document.querySelector(`.changed-by-${vuln.id}`);
                const changedAtSpan = document.querySelector(`.changed-at-${vuln.id}`);
                if (changedBySpan) changedBySpan.textContent = vuln.changed_by;
                if (changedAtSpan) changedAtSpan.textContent = vuln.changed_at;
            }
        });
    }
});