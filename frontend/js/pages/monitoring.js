// Monitoring page — simplified for clarity
const MonitoringPage = (() => {

  let allModels = [];
  let allMetrics = {};
  const GRAFANA_BASE_URL = 'http://grafana:3000';

  // Global helpers
  const safeMetrics = (m) => m ? {
    successRate: Number(m.successRate) || 0,
    errorRate: Number(m.errorRate) || 0,
    totalCalls: Number(m.totalCalls) || 0,
    totalErrors: Number(m.totalErrors) || 0
  } : { successRate: 0, errorRate: 0, totalCalls: 0, totalErrors: 0 };

  const PERIOD_LABELS = {
    '1d': 'Last 24h', '7d': 'Last 7d', '30d': 'Last 30d', '90d': 'Last 90d'
  };

  function render(container) {
    container.innerHTML = `
      <div class="page-header">
        <div class="page-title-group">
          <div class="page-eyebrow">Live Operations</div>
          <h1 class="page-title">Model Fleet Monitoring</h1>
        </div>
        <div class="page-header-meta">
          <div class="status-badge status-badge-live"><span class="status-pulse"></span>Live</div>
          <div class="monitoring-timestamp">Updated 30 sec ago</div>
        </div>
      </div>
      <div class="page-content">
        <div class="monitoring-filters">
          <button class="btn btn-ghost btn-xs" id="monitoring-refresh-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36M20.49 15a9 9 0 0 1-14.85 3.36"></path></svg> Refresh
          </button>
          <div class="filters-row">
            <div class="form-group"><label class="form-label">Project</label><select class="form-select" id="monitoring-project-filter"><option value="">All</option></select></div>
            <div class="form-group"><label class="form-label">Status</label><select class="form-select" id="monitoring-status-filter"><option value="">All</option><option value="healthy">Healthy</option><option value="caution">Caution</option><option value="alert">Alert</option></select></div>
            <div class="form-group"><label class="form-label">Sort</label><select class="form-select" id="monitoring-sort-filter"><option value="name">Name</option><option value="error-rate">Error Rate</option><option value="calls">Calls</option></select></div>
            <div class="form-group" style="margin-left: auto;"><label class="form-label">Period</label><select class="form-select" id="monitoring-period-filter"><option value="7d">7 Days</option><option value="1d">24h</option><option value="30d">30d</option><option value="90d">90d</option></select></div>
          </div>
        </div>
        <div id="monitoring-content"><div class="loading-screen"><span class="spinner"></span><span>Loading…</span></div></div>
      </div>
    `;

    loadAllModels();
    ['project', 'status', 'sort', 'period', 'refresh'].forEach(id => {
      const el = document.getElementById(`monitoring-${id}-filter`) || document.getElementById(`monitoring-${id}-btn`);
      if (el) el.addEventListener('change', () => filterAndRenderFleet());
      if (el && id === 'refresh') el.removeEventListener('change'), el.addEventListener('click', () => loadAllModels());
    });
  }

  async function loadAllModels() {
    const content = document.getElementById('monitoring-content');
    content.innerHTML = `<div class="loading-screen"><span class="spinner"></span><span>Loading…</span></div>`;
    try {
      await new Promise(r => setTimeout(r, 600));
      allModels = generateSampleModels();
      allMetrics = Object.fromEntries(allModels.map(m => [m.id, generateSampleMetrics(m.id)]));
      const projects = [...new Set(allModels.map(m => m.project))];
      document.getElementById('monitoring-project-filter').innerHTML = '<option value="">All</option>' +
        projects.map(p => `<option value="${escHtml(p)}">${escHtml(p)}</option>`).join('');
      filterAndRenderFleet();
    } catch (err) {
      content.innerHTML = `<div class="empty-state"><div class="empty-state-title" style="color:var(--status-red-light)">Error</div><div class="empty-state-desc">${escHtml(err.message)}</div></div>`;
    }
  }

  function filterAndRenderFleet() {
    const project = document.getElementById('monitoring-project-filter').value;
    const period = document.getElementById('monitoring-period-filter').value || '7d';
    const status = document.getElementById('monitoring-status-filter').value;
    const sortBy = document.getElementById('monitoring-sort-filter').value;

    let filtered = allModels.filter(m => {
      if (project && m.project !== project) return false;
      if (status && getModelStatus(safeMetrics(allMetrics[m.id]).errorRate) !== status) return false;
      return true;
    }).sort((a, b) => {
      const mA = safeMetrics(allMetrics[a.id]);
      const mB = safeMetrics(allMetrics[b.id]);
      switch(sortBy) {
        case 'error-rate': return mB.errorRate - mA.errorRate;
        case 'calls': return mB.totalCalls - mA.totalCalls;
        default: return a.name.localeCompare(b.name);
      }
    });

    const content = document.getElementById('monitoring-content');
    if (!filtered.length) {
      content.innerHTML = `<div class="empty-state"><div class="empty-state-title">No models found</div></div>`;
      return;
    }

    const grouped = {}, stats = { total: filtered.length, healthy: 0, caution: 0, alert: 0, totalCalls: 0 };
    filtered.forEach(m => {
      const st = getModelStatus(safeMetrics(allMetrics[m.id]).errorRate);
      stats[st]++;
      stats.totalCalls += safeMetrics(allMetrics[m.id]).totalCalls;
      if (!grouped[m.project]) grouped[m.project] = [];
      grouped[m.project].push(m);
    });

    content.innerHTML = `
      <div class="fleet-header">
        <div><div class="fleet-stat-value">${stats.total}</div><div class="fleet-stat-label">Total</div></div>
        <div><div class="fleet-stat-value">${stats.healthy}</div><div class="fleet-stat-label">Healthy</div></div>
        <div><div class="fleet-stat-value">${stats.caution}</div><div class="fleet-stat-label">Caution</div></div>
        <div><div class="fleet-stat-value">${stats.alert}</div><div class="fleet-stat-label">Alert</div></div>
        <div><div class="fleet-stat-value">${stats.totalCalls.toLocaleString()}</div><div class="fleet-stat-label">Calls<br><span style="font-size:9px">${PERIOD_LABELS[period]}</span></div></div>
      </div>
      <div class="projects-grid">
        ${Object.entries(grouped).map(([proj, models]) => {
          const pStats = { healthy: 0, caution: 0, alert: 0 };
          models.forEach(m => pStats[getModelStatus(safeMetrics(allMetrics[m.id]).errorRate)]++);
          return `
            <div class="project-box">
              <div class="project-box-header">
                <h2>${escHtml(proj)}</h2>
                <div class="project-box-stats">
                  <span class="badge healthy">${pStats.healthy}</span>
                  <span class="badge caution">${pStats.caution}</span>
                  <span class="badge alert">${pStats.alert}</span>
                </div>
              </div>
              <div class="models-list">
                ${models.map(m => {
                  const met = safeMetrics(allMetrics[m.id]);
                  const st = getModelStatus(met.errorRate);
                  return `
                    <div class="model-row">
                      <div class="model-row-header">
                        <div><div style="font-weight:600">${escHtml(m.name)}</div><div style="font-size:11px;color:var(--text-2)"
>v${m.version}</div></div>
                        <div class="model-row-actions">
                          <div class="status-dot status-${st}"></div>
                          <a href="${GRAFANA_BASE_URL}/d/model-${m.id}" target="_blank" rel="noopener" style="color:var(--text-2);text-decoration:none"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg></a>
                        </div>
                      </div>
                      <div class="model-row-metrics">
                        <div><div class="metric-label">Calls</div><div class="metric-value">${(met.totalCalls / 1000).toFixed(1)}k</div></div>
                        <div><div class="metric-label">Success</div><div class="metric-value">${Math.round(met.totalCalls * (met.successRate / 100))}</div></div>
                        <div><div class="metric-label">Errors</div><div class="metric-value" style="color:${met.totalErrors === 0 ? 'var(--status-green)' : met.totalErrors < 100 ? 'var(--status-orange)' : 'var(--status-red)'}">${met.totalErrors}</div></div>
                        <div><div class="metric-label">Rate</div><div class="metric-value">${met.successRate.toFixed(1)}%</div></div>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function getModelStatus(errorRate) {
    if (errorRate < 1) return 'healthy';
    if (errorRate < 5) return 'caution';
    return 'alert';
  }

  function generateSampleModels() {
    return [
      { id: 'credit-v2-prod', name: 'Credit Scoring', version: 2, project: 'Banking Finance' },
      { id: 'fraud-detection-v3', name: 'Fraud Detection', version: 3, project: 'Banking Finance' },
      { id: 'churn-prediction-v1', name: 'Churn Prediction', version: 1, project: 'Telecom Analytics' },
      { id: 'recommendation-v4', name: 'Recommendation Engine', version: 4, project: 'E-commerce' },
      { id: 'sentiment-analysis-v2', name: 'Sentiment Analysis', version: 2, project: 'Marketing AI' },
      { id: 'invoice-ocr-v3', name: 'Invoice OCR', version: 3, project: 'Finance Automation' }
    ];
  }

  function generateSampleMetrics(modelId) {
    const seed = modelId.charCodeAt(0);
    const rand = (min, max) => {
      const r = Math.sin(seed * 12.9898 + modelId.length * 78.233) * 43758.5453;
      return min + ((r - Math.floor(r)) * (max - min));
    };
    const sr = 94 + rand(-5, 8);
    const tc = 45000 + rand(-5000, 8000);
    return {
      successRate: sr,
      errorRate: 100 - sr,
      totalCalls: Math.floor(tc),
      totalErrors: Math.floor(tc * (100 - sr) / 100)
    };
  }

  return { render };
})();
