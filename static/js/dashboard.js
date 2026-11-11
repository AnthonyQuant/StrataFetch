document.addEventListener('DOMContentLoaded', () => {
    let performanceChart = null;
    let qualityChart = null;

    const tabBtnProfiles = document.getElementById('tab-btn-profiles');
    const tabBtnLogs = document.getElementById('tab-btn-logs');
    const viewProfiles = document.getElementById('view-profiles');
    const viewLogs = document.getElementById('view-logs');

    if (tabBtnProfiles && tabBtnLogs) {
        tabBtnProfiles.addEventListener('click', () => {
            tabBtnProfiles.classList.add('active');
            tabBtnLogs.classList.remove('active');
            viewProfiles.style.display = 'block';
            viewLogs.style.display = 'none';
        });

        tabBtnLogs.addEventListener('click', () => {
            tabBtnLogs.classList.add('active');
            tabBtnProfiles.classList.remove('active');
            viewLogs.style.display = 'block';
            viewProfiles.style.display = 'none';
        });
    }

    async function fetchDashboardMetrics() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (!response.ok) return;

            const data = await response.json();

            // 1. Update KPI Values
            document.getElementById('kpi-last-run').innerText = data.kpis.last_run;
            document.getElementById('kpi-yield-rate').innerText = `${data.kpis.yield_rate}%`;
            document.getElementById('kpi-avg-latency').innerText = `${data.kpis.avg_latency_ms} ms`;
            document.getElementById('kpi-total-requests').innerText = data.kpis.total_requests;

            // 2. Update Sidebar Counters
            document.getElementById('sidebar-active-scrapers').innerText = data.sidebar_stats.active_scrapers_count;
            document.getElementById('sidebar-records-count').innerText = data.sidebar_stats.total_records_collected.toLocaleString();

            // 3. Render Profile Table & Audit Logs
            renderProfilesTable(data.recent_profiles);
            renderAuditLogsTable(data.recent_logs);
            updateFailureBreakdown(data.failure_breakdown);

            // 4. Render Dynamic Charts
            renderPerformanceChart(data.charts.performance);
            renderQualityChart(data.charts.quality);

        } catch (err) {
            console.error("Failed to load dashboard statistics:", err);
        }
    }

    function renderProfilesTable(profiles) {
        const tbody = document.getElementById('profiles-table-body');
        tbody.innerHTML = '';

        profiles.forEach(p => {
            const tr = document.createElement('tr');
            const badgeClass = p.status === 'Active' ? 'badge-active' : 'badge-idle';
            tr.innerHTML = `
                <td><strong>${p.name}</strong></td>
                <td><span class="badge ${badgeClass}">${p.status}</span></td>
                <td>${p.records.toLocaleString()}</td>
                <td>${p.updated}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderAuditLogsTable(logs) {
        const tbody = document.getElementById('logs-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No telemetry logs recorded yet.</td></tr>';
            return;
        }

        logs.forEach(l => {
            const tr = document.createElement('tr');
            const badgeClass = l.success ? 'badge-active' : 'badge-idle';
            const statusText = l.success ? `HTTP ${l.status_code}` : `ERR ${l.status_code}`;
            const errorDetail = l.error_message ? l.error_message.substring(0, 35) + '...' : 'OK';

            tr.innerHTML = `
                <td>${l.timestamp}</td>
                <td title="${l.target_url}"><code>${l.target_url.length > 25 ? l.target_url.substring(0, 25) + '...' : l.target_url}</code></td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
                <td>${l.response_time_ms} ms</td>
                <td style="font-size: 0.75rem; color: ${l.success ? '#94a3b8' : '#ef4444'};">${errorDetail}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function updateFailureBreakdown(breakdown) {
        if (!breakdown) return;
        document.getElementById('breakdown-ssrf').innerText = `${breakdown.ssrf_blocks || 0} requests blocked`;
        document.getElementById('breakdown-429').innerText = `${breakdown.rate_limited_429 || 0} requests backed off`;
        document.getElementById('breakdown-403').innerText = `${breakdown.forbidden_403 || 0} access violations`;
        document.getElementById('breakdown-5xx').innerText = `${breakdown.server_error_5xx || 0} upstream failures`;
    }

    function renderPerformanceChart(perfData) {
        const ctx = document.getElementById('scraperPerformanceChart').getContext('2d');
        if (performanceChart) performanceChart.destroy();

        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: perfData.labels,
                datasets: [
                    {
                        label: 'Successful Runs',
                        data: perfData.successful,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Warnings / 429',
                        data: perfData.warnings,
                        borderColor: '#f59e0b',
                        tension: 0.3
                    },
                    {
                        label: 'Failures / SSRF',
                        data: perfData.failures,
                        borderColor: '#ef4444',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#64748b' }, grid: { color: '#1f293d' } },
                    y: { ticks: { color: '#64748b' }, grid: { color: '#1f293d' } }
                }
            }
        });
    }

    function renderQualityChart(qData) {
        const ctx = document.getElementById('dataQualityChart').getContext('2d');
        if (qualityChart) qualityChart.destroy();

        qualityChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Valid Data', 'Duplicates', 'Failed Requests'],
                datasets: [{
                    data: [qData.valid_pct, qData.duplicates_pct, qData.invalid_pct],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } }
                }
            }
        });
    }

    fetchDashboardMetrics();
});