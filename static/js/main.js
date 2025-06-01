document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const uploadButton = document.querySelector('button[type="submit"]');
    const spinner = document.getElementById('uploadSpinner');
    // Show spinner and disable button
    spinner.classList.remove('d-none');
    uploadButton.disabled = true;
    uploadButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (result.success) {
            document.getElementById('analysisResults').classList.remove('d-none');
            // Stats with badges
            const statsDisplay = document.getElementById('statsDisplay');
            statsDisplay.innerHTML = `
                <div class="mb-2"><span class="fw-bold">Total Logs:</span> <span class="badge badge-info">${result.stats.total_logs}</span></div>
                <div class="mb-2"><span class="fw-bold">Log Levels:</span> ${Object.entries(result.stats.log_levels).map(([level, count]) =>
                    `<span class="badge ${badgeClass(level)} me-1">${level}: ${count}</span>`).join('')}</div>
                <div class="mb-2"><span class="fw-bold">Time Range:</span> <span class="badge badge-secondary">${result.stats.time_range.start} to ${result.stats.time_range.end}</span></div>
            `;
            // Get and display plots & advanced analytics
            const plotsResp = await fetch(`/get_stats/${result.filename}`);
            let plots;
            try {
                plots = await plotsResp.json();
            } catch (err) {
                showAlert('danger', 'Server returned invalid JSON. Check backend logs for errors.');
                return;
            }
            if (plots.error) {
                showAlert('danger', plots.error);
                return;
            }
            if (plots.level_distribution) Plotly.newPlot('levelDistribution', JSON.parse(plots.level_distribution));
            if (plots.logs_per_hour) Plotly.newPlot('logsPerHour', JSON.parse(plots.logs_per_hour));
            if (plots.level_pie) Plotly.newPlot('levelPie', JSON.parse(plots.level_pie));
            if (plots.top_errors) renderTable('topErrorsTable', plots.top_errors, ['Message', 'Count']);
            if (plots.unique_messages) renderList('uniqueMessages', plots.unique_messages);
            if (plots.active_users) renderList('activeUsers', plots.active_users);
            if (plots.idle_periods) renderTable('idlePeriods', plots.idle_periods, ['Start', 'End', 'Duration (min)']);
            showAlert('success', 'Log file uploaded and analyzed successfully!');
        } else {
            throw new Error(result.error || 'Failed to upload file');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('danger', error.message || 'An error occurred while processing the file');
    } finally {
        spinner.classList.add('d-none');
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fa-solid fa-cloud-arrow-up me-1"></i>Upload';
    }
});

function badgeClass(level) {
    switch (level.toUpperCase()) {
        case 'ERROR': return 'badge-danger';
        case 'CRITICAL': return 'badge-danger';
        case 'WARNING': return 'badge-warning';
        case 'INFO': return 'badge-info';
        case 'DEBUG': return 'badge-secondary';
        default: return 'badge-secondary';
    }
}

function renderTable(containerId, data, headers) {
    const container = document.getElementById(containerId);
    if (!data || !data.length) { container.innerHTML = '<p class="text-muted">None</p>'; return; }
    let html = `<table class="table table-custom table-sm"><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>`;
    data.forEach(row => {
        html += `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function renderList(containerId, data) {
    const container = document.getElementById(containerId);
    if (!data || !data.length) { container.innerHTML = '<p class="text-muted">None</p>'; return; }
    container.innerHTML = `<ul class="list-group list-group-flush">${data.map(item => `<li class="list-group-item">${item}</li>`).join('')}</ul>`;
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    const form = document.getElementById('uploadForm');
    form.parentNode.insertBefore(alertDiv, form);
}
