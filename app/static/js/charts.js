// PingBot Charts - Chart.js initialization

let responseOverTimeChart = null;
let responseDistChart = null;
let heatmapChart = null;

function getDays() {
    const select = document.getElementById('days-filter');
    return select ? select.value : 30;
}

async function fetchJSON(url) {
    const resp = await fetch(url);
    return resp.json();
}

async function loadOverview() {
    const days = getDays();
    const data = await fetchJSON(`/stats/api/overview?days=${days}`);
    document.getElementById('stat-sent').textContent = data.total_sent;
    document.getElementById('stat-responded').textContent = data.total_responded;
    document.getElementById('stat-rate').textContent = data.response_rate + '%';
    document.getElementById('stat-time').textContent = data.avg_response_time_minutes + ' min';
}

async function loadResponseOverTime() {
    const days = getDays();
    const data = await fetchJSON(`/stats/api/response-over-time?days=${days}`);

    const ctx = document.getElementById('responseOverTimeChart');
    if (!ctx) return;

    if (responseOverTimeChart) responseOverTimeChart.destroy();

    responseOverTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Sent',
                    data: data.sent,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'Responded',
                    data: data.responded,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    fill: true,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } },
                x: {
                    ticks: {
                        maxTicksLimit: 10,
                        maxRotation: 45,
                    },
                },
            },
            plugins: {
                legend: { position: 'top' },
            },
        },
    });
}

async function loadResponseDistribution() {
    const data = await fetchJSON('/stats/api/response-distribution');
    const ctx = document.getElementById('responseDistChart');
    if (!ctx) return;

    if (responseDistChart) responseDistChart.destroy();

    // Aggregate all responses
    const allResponses = {};
    for (const msg of data.messages) {
        for (const [key, val] of Object.entries(msg.responses)) {
            allResponses[key] = (allResponses[key] || 0) + val;
        }
    }

    const labels = Object.keys(allResponses);
    const values = Object.values(allResponses);
    const colors = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1', '#0dcaf0'];

    responseDistChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
            },
        },
    });
}

async function loadHeatmap() {
    const days = getDays();
    const data = await fetchJSON(`/stats/api/activity-heatmap?days=${days}`);
    const ctx = document.getElementById('heatmapChart');
    if (!ctx) return;

    if (heatmapChart) heatmapChart.destroy();

    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const hours = Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}:00`);

    // Build a grid: 7 datasets (one per day), 24 data points (hours)
    const grid = Array.from({length: 7}, () => new Array(24).fill(0));
    for (const point of data.data) {
        grid[point.day][point.hour] = point.count;
    }

    const datasets = dayNames.map((name, idx) => ({
        label: name,
        data: grid[idx],
        backgroundColor: `rgba(13, 110, 253, ${0.15 + idx * 0.1})`,
    }));

    heatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 } },
            },
            plugins: {
                legend: { position: 'top' },
            },
        },
    });
}

function loadAll() {
    loadOverview();
    loadResponseOverTime();
    loadResponseDistribution();
    loadHeatmap();
}

document.addEventListener('DOMContentLoaded', loadAll);

const daysFilter = document.getElementById('days-filter');
if (daysFilter) {
    daysFilter.addEventListener('change', loadAll);
}
