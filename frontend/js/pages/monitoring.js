// Monitoring page — simplified for clarity
const MonitoringPage = (() => {

  let allModels = [];
  let allMetrics = {};
  let refreshTimer = null;
  const GRAFANA_QUERY_PARAMS = '?orgId=1&from=now-1h&to=now&timezone=utc';
  // API URL: read from data attribute or default to current origin
  const API_BASE_URL = (document.currentScript?.dataset?.apiUrl ||
                        document.documentElement.dataset?.apiUrl ||
                        window.__APP_CONFIG__?.apiUrl ||
                        window.location.origin).replace(/\/$/, '');

  // Global helpers
  const safeMetrics = (m) => m ? {
    successRate: Number(m.successRate) || 0,
    errorRate: Number(m.errorRate) || 0,
    totalCalls: Number(m.totalCalls) || 0,
    totalErrors: Number(m.totalErrors) || 0
  } : { successRate: 0, errorRate: 0, totalCalls: 0, totalErrors: 0 };

  const PERIOD_LABELS = {
    '15m': 'Last 15 min', '30m': 'Last 30 min', '1h': 'Last 1h',
    '6h': 'Last 6h', '1d': 'Last 24h', '7d': 'Last 7d', '30d': 'Last 30d'
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
          <button class="monitoring-refresh-btn" id="monitoring-refresh-btn" title="Click to refresh now">
            <span id="monitoring-timestamp">Updating…</span>
          </button>
        </div>
      </div>
      <div class="page-content">
        <div class="monitoring-filters">
          <div class="filters-row">
            <div class="form-group"><label class="form-label">Project</label><select class="form-select" id="monitoring-project-filter"><option value="">All</option></select></div>
            <div class="form-group"><label class="form-label">Status</label><select class="form-select" id="monitoring-status-filter"><option value="">All</option><option value="healthy">Healthy</option><option value="caution">Caution</option><option value="alert">Alert</option></select></div>
            <div class="form-group"><label class="form-label">Sort</label><select class="form-select" id="monitoring-sort-filter"><option value="name">Name</option><option value="error-rate">Error Rate</option><option value="calls">Calls</option></select></div>
            <div class="form-group" style="margin-left: auto;"><label class="form-label">Period</label><select class="form-select" id="monitoring-period-filter"><option value="15m">15 min</option><option value="30m">30 min</option><option value="1h">1h</option><option value="6h">6h</option><option value="1d">24h</option><option value="7d" selected>7d</option><option value="30d">30d</option></select></div>
          </div>
        </div>
        <div id="monitoring-content"><div class="loading-screen"><span class="spinner"></span><span>Loading…</span></div></div>
      </div>
    `;

    loadAllModels();

    // Attach event listeners
    const projectFilter = document.getElementById('monitoring-project-filter');
    const statusFilter = document.getElementById('monitoring-status-filter');
    const sortFilter = document.getElementById('monitoring-sort-filter');
    const periodFilter = document.getElementById('monitoring-period-filter');
    const refreshBtn = document.getElementById('monitoring-refresh-btn');

    if (projectFilter) projectFilter.addEventListener('change', () => filterAndRenderFleet());
    if (statusFilter) statusFilter.addEventListener('change', () => filterAndRenderFleet());
    if (sortFilter) sortFilter.addEventListener('change', () => filterAndRenderFleet());
    if (periodFilter) periodFilter.addEventListener('change', () => loadAllModels());
    if (refreshBtn) refreshBtn.addEventListener('click', () => loadAllModels());
  }

  async function loadAllModels() {
    const content = document.getElementById('monitoring-content');
    content.innerHTML = `<div class="loading-screen"><span class="spinner"></span><span>Loading metrics…</span></div>`;
    try {
      // Get model catalog (basic info: name, version, project) from backend
      allModels = await fetchRealModelsFromBackend();

      // Fetch real metrics from backend for each model
      const period = document.getElementById('monitoring-period-filter').value || '7d';
      allMetrics = await fetchMetricsForAllModels(allModels, period);

      // Update project filter
      const projects = [...new Set(allModels.map(m => m.project))];
      document.getElementById('monitoring-project-filter').innerHTML = '<option value="">All</option>' +
        projects.map(p => `<option value="${escHtml(p)}">${escHtml(p)}</option>`).join('');

      filterAndRenderFleet();
      startAutoRefresh();
    } catch (err) {
      console.error('Error loading models:', err);
      const errorMsg = err.message || 'Failed to fetch metrics from backend. Check if API is running.';
      content.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--status-red-light)">⚠️ Cannot Load Metrics</div>
          <div class="empty-state-desc" style="max-width:600px;text-align:left;white-space:pre-wrap;font-family:monospace;font-size:12px">${escHtml(errorMsg)}</div>
          <div style="margin-top:16px;font-size:12px;color:var(--text-2)">Debug Info: API URL = ${escHtml(API_BASE_URL)}</div>
        </div>
      `;
    }
  }

  async function fetchMetricsForAllModels(models, period) {
    const metrics = {};
    const errors = [];

    for (const model of models) {
      try {
        const url = `${API_BASE_URL}/metrics/models/${model.id}?period=${period}`;
        console.log(`Fetching: ${url}`);

        const response = await fetch(url, {
          headers: { 'Accept': 'application/json' },
          credentials: 'include'
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
        }

        const data = await response.json();

        // Map API response to internal format
        metrics[model.id] = {
          successRate: data.success_rate || 0,
          errorRate: data.error_rate || 0,
          totalCalls: data.total_calls || 0,
          totalErrors: data.total_errors || 0
        };
      } catch (err) {
        console.error(`Failed to fetch metrics for ${model.id}: ${err.message}`);
        errors.push(model.id);
      }
    }

    // If all models failed, log warning but continue with empty metrics
    if (errors.length === models.length) {
      console.warn(
        `No metrics available from ${API_BASE_URL}/metrics. ` +
        `Prometheus may be unavailable or not scraping model deployments. ` +
        `Dashboard will show models without metrics.`
      );
    } else if (errors.length > 0) {
      console.warn(`Missing metrics for ${errors.length} models: ${errors.join(', ')}`);
    }

    return metrics;
  }



  function filterAndRenderFleet() {
    const project = document.getElementById('monitoring-project-filter').value;
    const period = document.getElementById('monitoring-period-filter').value || '7d';
    const status = document.getElementById('monitoring-status-filter').value;
    const sortBy = document.getElementById('monitoring-sort-filter').value;

    let filtered = allModels.filter(m => {
      if (project && m.project !== project) return false;
      // Only filter by status if we have metrics for this model
      if (status && allMetrics[m.id]) {
        const modelStatus = getModelStatus(safeMetrics(allMetrics[m.id]).errorRate);
        if (modelStatus !== status) return false;
      }
      return true;
    }).sort((a, b) => {
      const mA = safeMetrics(allMetrics[a.id]);
      const mB = safeMetrics(allMetrics[b.id]);
      switch(sortBy) {
        case 'error-rate':
          // Sort by error rate if available, otherwise put models with metrics first
          const aHasMetrics = allMetrics[a.id] !== undefined;
          const bHasMetrics = allMetrics[b.id] !== undefined;
          if (aHasMetrics && !bHasMetrics) return -1;
          if (!aHasMetrics && bHasMetrics) return 1;
          if (aHasMetrics && bHasMetrics) return mB.errorRate - mA.errorRate;
          return a.name.localeCompare(b.name);
        case 'calls':
          return mB.totalCalls - mA.totalCalls;
        default:
          return a.name.localeCompare(b.name);
      }
    });

    const content = document.getElementById('monitoring-content');
    if (!filtered.length) {
      content.innerHTML = `<div class="empty-state"><div class="empty-state-title">No models found</div></div>`;
      return;
    }

    const grouped = {}, stats = { total: filtered.length, healthy: 0, caution: 0, alert: 0, totalCalls: 0, noMetrics: 0 };
    filtered.forEach(m => {
      if (allMetrics[m.id]) {
        const st = getModelStatus(safeMetrics(allMetrics[m.id]).errorRate);
        stats[st]++;
        stats.totalCalls += safeMetrics(allMetrics[m.id]).totalCalls;
      } else {
        stats.noMetrics++;
      }
      if (!grouped[m.project]) grouped[m.project] = [];
      grouped[m.project].push(m);
    });

    content.innerHTML = `
      <div class="fleet-header">
        <div><div class="fleet-stat-label">Total</div><div class="fleet-stat-value">${stats.total}</div></div>
        <div><div class="fleet-stat-label">Healthy</div><div class="fleet-stat-value">${stats.healthy}</div></div>
        <div><div class="fleet-stat-label">Caution</div><div class="fleet-stat-value">${stats.caution}</div></div>
        <div><div class="fleet-stat-label">Alert</div><div class="fleet-stat-value">${stats.alert}</div></div>
        ${stats.noMetrics > 0 ? `<div><div class="fleet-stat-label">No Metrics</div><div class="fleet-stat-value" style="color: var(--text-secondary);">${stats.noMetrics}</div></div>` : ''}
        <div><div class="fleet-stat-label">Calls</div><div class="fleet-stat-value">${stats.totalCalls.toLocaleString()}</div></div>
      </div>
      <div class="projects-grid">
        ${Object.entries(grouped).map(([proj, models]) => {
          const pStats = { healthy: 0, caution: 0, alert: 0 };
          models.forEach(m => pStats[getModelStatus(safeMetrics(allMetrics[m.id]).errorRate)]++);
          const worstStatus = pStats.alert > 0 ? 'alert' : pStats.caution > 0 ? 'caution' : 'healthy';
          const totalM = models.length;
          const phHealthy = ((pStats.healthy / totalM) * 100).toFixed(0);
          const phCaution = ((pStats.caution / totalM) * 100).toFixed(0);
          const phAlert   = ((pStats.alert   / totalM) * 100).toFixed(0);
          return `
            <div class="project-box project-status-${worstStatus}">
              <div class="project-box-header">
                <div class="project-header-top">
                  <h2 class="project-box-title">${escHtml(proj)}</h2>
                  <div class="project-box-stats">
                    ${pStats.healthy > 0 ? `<span class="project-stat-badge healthy">${pStats.healthy}</span>` : ''}
                    ${pStats.caution > 0 ? `<span class="project-stat-badge caution">${pStats.caution}</span>` : ''}
                    ${pStats.alert   > 0 ? `<span class="project-stat-badge alert">${pStats.alert}</span>`   : ''}
                  </div>
                </div>
                <div class="project-health-bar">
                  <div class="ph-seg ph-healthy" style="width:${phHealthy}%"></div>
                  <div class="ph-seg ph-caution" style="width:${phCaution}%"></div>
                  <div class="ph-seg ph-alert"   style="width:${phAlert}%"></div>
                </div>
              </div>
              <div class="models-list">
                ${models.map(m => {
                  const met = safeMetrics(allMetrics[m.id]);
                  const st = getModelStatus(met.errorRate);
                  const hasMetrics = allMetrics[m.id] !== undefined;
                  return `
                    <div class="model-row model-row-${hasMetrics ? st : 'unknown'}">
                      <div class="model-row-header">
                        <div class="model-row-info">
                          <div class="model-row-name">${escHtml(m.name)}</div>
                          <div class="model-row-version">v${m.version}</div>
                        </div>
                        <div class="model-row-actions">
                          <a href="${m.dashboard_url ? m.dashboard_url + GRAFANA_QUERY_PARAMS : '#'}" target="_blank" rel="noopener" class="model-row-link${!m.dashboard_url ? ' model-row-link-disabled' : ''}" title="Open Grafana dashboard"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg></a>
                        </div>
                      </div>
                      <div class="model-row-metrics">
                        ${hasMetrics ? `
                          <div><div class="metric-label">Calls</div><div class="metric-value">${(met.totalCalls / 1000).toFixed(1)}k</div></div>
                          <div><div class="metric-label">Success</div><div class="metric-value">${Math.round(met.totalCalls * (met.successRate / 100))}</div></div>
                          <div><div class="metric-label">Errors</div><div class="metric-value${met.totalErrors > 0 ? ' metric-value-error' : ''}">${met.totalErrors}</div></div>
                          <div><div class="metric-label">Rate</div><div class="metric-value">${met.successRate.toFixed(1)}%</div></div>
                        ` : `
                          <div class="model-row-no-metrics">⚠ Metrics unavailable</div>
                        `}
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

  function updateTimestamp(msg) {
    const el = document.getElementById('monitoring-timestamp');
    if (el) el.textContent = msg;
  }

  function startAutoRefresh() {
    clearInterval(refreshTimer);
    let countdown = 30;
    updateTimestamp('Updated just now');
    refreshTimer = setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        clearInterval(refreshTimer);
        loadAllModels();
      } else {
        updateTimestamp(`Refresh in ${countdown}s`);
      }
    }, 1000);
  }

  async function fetchRealModelsFromBackend() {
    // 1. Get projects the current user has access to
    const projects = await API.projects.list();

    // 2. For each project, fetch its deployed models
    const allModels = [];
    await Promise.all(projects.map(async (project) => {
      const projectName = project.name;
      try {
        const deployments = await API.deployedModels.list(projectName);
        deployments.forEach(d => {
          allModels.push({
            id: d.deployment_name,
            name: d.model_name,
            version: d.version || 1,
            project: projectName,
            deployment_name: d.deployment_name,
            status: d.status,
            dashboard_url: d.dashboard_url,
          });
        });
      } catch (err) {
        console.warn(`Could not fetch deployments for project ${projectName}: ${err.message}`);
      }
    }));

    console.log(`Fetched ${allModels.length} deployed models across ${projects.length} projects.`);
    return allModels;
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

  return { render };
})();
