document.addEventListener('DOMContentLoaded', function() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    function updateVulnerabilityStatus(vulnerabilityId, newStatus, bulkType, riskFactor) {
        const reportId = document.getElementById('report-id').dataset.reportId;
        const customerId = document.getElementById('customer-id').dataset.customerId;
        
        fetch(`/reports/${customerId}/${reportId}/update_status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `vulnerability_id=${vulnerabilityId}&status=${newStatus}&bulk_type=${bulkType}&risk_factor=${riskFactor}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatusInUI(data.updated_vulnerabilities);
            } else {
                console.error('Error updating status:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function updateStatusInUI(updatedVulnerabilities) {
        updatedVulnerabilities.forEach(vuln => {
            const statusElement = document.getElementById(`status-${vuln.id}`);
            const changedByElement = document.getElementById(`changed-by-${vuln.id}`);
            const changedAtElement = document.getElementById(`changed-at-${vuln.id}`);
            
            if (statusElement) statusElement.textContent = vuln.status;
            if (changedByElement) changedByElement.textContent = vuln.changed_by;
            if (changedAtElement) changedAtElement.textContent = vuln.changed_at;
        });
    }

    // Add event listeners for status change selects
    document.querySelectorAll('.vulnerability-status-select').forEach(select => {
        select.addEventListener('change', function() {
            const vulnerabilityId = this.dataset.vulnerabilityId;
            const newStatus = this.value;
            updateVulnerabilityStatus(vulnerabilityId, newStatus, 'single', null);
        });
    });

    // Add event listeners for bulk status changes
    document.querySelectorAll('.bulk-status-select').forEach(select => {
        select.addEventListener('change', function() {
            const bulkType = this.dataset.bulkType;
            const newStatus = this.value;
            const riskFactor = this.dataset.riskFactor;
            updateVulnerabilityStatus(null, newStatus, bulkType, riskFactor);
        });
    });
});