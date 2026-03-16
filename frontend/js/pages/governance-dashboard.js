// Governance Dashboard — platform-wide compliance overview
const GovernanceDashboardPage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Platform Overview</div>
            <h1 class="page-title">Governance Dashboard</h1>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-secondary btn-sm" id="dash-goto-governance">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              Project Governance
            </button>
            <button class="btn btn-primary btn-sm" id="dash-refresh-btn">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
              Refresh
            </button>
          </div>
        </div>
        <div class="page-content">
          <div id="dash-content">
            <div class="loading-screen"><span class="spinner"></span><span>Loading dashboard data...</span></div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('dash-goto-governance').addEventListener('click', () => App.navigateTo('governance'));
    document.getElementById('dash-refresh-btn').addEventListener('click', () => loadDashboard());

    loadDashboard();
  }

  async function loadDashboard() {
    const content = document.getElementById('dash-content');
    content.innerHTML = `<div class="loading-screen"><span class="spinner"></span><span>Loading dashboard data...</span></div>`;

    try {
      const data = await API.compliance.dashboard();
      renderDashboard(content, data);
    } catch (err) {
      content.innerHTML = `
        <div class="empty-state" style="padding:80px 0">
          <div class="empty-state-title" style="color:var(--red-light)">Unable to load dashboard</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>`;
    }
  }

  function renderDashboard(container, data) {
    const s = data.summary;
    const policyLabels = { strict: 'Strict', permissive: 'Permissive', disabled: 'Disabled' };
    const policyClass = { strict: 'gdash-policy--strict', permissive: 'gdash-policy--permissive', disabled: 'gdash-policy--disabled' };

    container.innerHTML = `
      <!-- KPI Hero -->
      <div class="gdash-hero">
        <div class="gdash-kpi-grid">
          ${kpiCard('Projects', s.total_projects, kpiIconProject())}
          ${kpiCard('Models', s.total_models, kpiIconModel())}
          ${kpiCard('Versions', s.total_versions, kpiIconVersion())}
          <div class="gdash-kpi gdash-kpi--policy">
            <div class="gdash-kpi__icon">${kpiIconPolicy()}</div>
            <div class="gdash-kpi__body">
              <div class="gdash-kpi__label">Gate Policy</div>
              <div class="gdash-kpi__value gdash-kpi__value--sm">
                <span class="gdash-policy-badge ${policyClass[data.gate_policy] || ''}">${escHtml(policyLabels[data.gate_policy] || data.gate_policy)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Distribution Charts -->
      <div class="gdash-charts-row">
        ${renderDonutCard('Risk Distribution', s.risk_distribution, riskPalette())}
        ${renderDonutCard('Deterministic Compliance', s.deterministic_distribution, compliancePalette())}
        ${renderDonutCard('LLM Compliance', s.llm_distribution, compliancePalette())}
      </div>

      <!-- Project Matrix -->
      <div class="gdash-section">
        <div class="gdash-section__header">
          <h2 class="gdash-section__title">Project Compliance Matrix</h2>
          <span class="gdash-section__count">${data.projects.length} project${data.projects.length !== 1 ? 's' : ''}</span>
        </div>
        <div class="gdash-matrix">
          ${data.projects.map((p, i) => renderProjectCard(p, i)).join('')}
        </div>
      </div>
    `;

    // Animate donut charts after render
    requestAnimationFrame(() => {
      container.querySelectorAll('.gdash-donut').forEach(el => {
        el.classList.add('gdash-donut--visible');
      });
    });
  }

  // ── KPI Cards ──────────────────────────────────────────────

  function kpiCard(label, value, icon) {
    return `
      <div class="gdash-kpi">
        <div class="gdash-kpi__icon">${icon}</div>
        <div class="gdash-kpi__body">
          <div class="gdash-kpi__label">${label}</div>
          <div class="gdash-kpi__value">${value}</div>
        </div>
      </div>`;
  }

  function kpiIconProject() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;
  }
  function kpiIconModel() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`;
  }
  function kpiIconVersion() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>`;
  }
  function kpiIconPolicy() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
  }

  // ── Donut Charts ───────────────────────────────────────────

  function riskPalette() {
    return {
      'minimal': { color: '#10B981', label: 'Minimal' },
      'limited': { color: '#F59E0B', label: 'Limited' },
      'high':    { color: '#F97316', label: 'High' },
      'unacceptable': { color: '#EF4444', label: 'Unacceptable' },
      'non renseigne': { color: '#6B84A8', label: 'Not set' },
    };
  }

  function compliancePalette() {
    return {
      'compliant':           { color: '#10B981', label: 'Compliant' },
      'partially_compliant': { color: '#F97316', label: 'Partial' },
      'non_compliant':       { color: '#EF4444', label: 'Non-compliant' },
      'not_evaluated':       { color: '#6B84A8', label: 'Not evaluated' },
    };
  }

  function renderDonutCard(title, distribution, palette) {
    const total = Object.values(distribution).reduce((a, b) => a + b, 0);
    if (total === 0) {
      return `
        <div class="gdash-chart-card">
          <div class="gdash-chart-card__title">${title}</div>
          <div class="gdash-chart-card__empty">No data</div>
        </div>`;
    }

    // Build conic-gradient segments
    const segments = [];
    let cumulative = 0;
    const entries = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
    for (const [key, count] of entries) {
      const pct = (count / total) * 100;
      const p = palette[key] || { color: '#6B84A8', label: key };
      segments.push(`${p.color} ${cumulative}% ${cumulative + pct}%`);
      cumulative += pct;
    }
    const gradient = `conic-gradient(${segments.join(', ')})`;

    const legend = entries.map(([key, count]) => {
      const p = palette[key] || { color: '#6B84A8', label: key };
      const pct = Math.round((count / total) * 100);
      return `
        <div class="gdash-legend-item">
          <span class="gdash-legend-dot" style="background:${p.color}"></span>
          <span class="gdash-legend-label">${escHtml(p.label)}</span>
          <span class="gdash-legend-value">${count}</span>
          <span class="gdash-legend-pct">${pct}%</span>
        </div>`;
    }).join('');

    return `
      <div class="gdash-chart-card">
        <div class="gdash-chart-card__title">${title}</div>
        <div class="gdash-chart-card__content">
          <div class="gdash-donut" style="--donut-gradient:${gradient}">
            <div class="gdash-donut__ring"></div>
            <div class="gdash-donut__center">
              <span class="gdash-donut__total">${total}</span>
              <span class="gdash-donut__label">total</span>
            </div>
          </div>
          <div class="gdash-legend">${legend}</div>
        </div>
      </div>`;
  }

  // ── Project Cards ──────────────────────────────────────────

  function renderProjectCard(project, index) {
    if (project.error) {
      return `
        <div class="gdash-project-card gdash-project-card--error" style="animation-delay:${index * 60}ms">
          <div class="gdash-project-card__header">
            <span class="gdash-project-card__name">${escHtml(project.name)}</span>
          </div>
          <div class="gdash-project-card__error">Registry unavailable</div>
        </div>`;
    }

    const detDist = project.deterministic_distribution || {};
    const llmDist = project.llm_distribution || {};
    const totalVersions = project.total_versions || 0;

    // Compute a "health score" — percentage of compliant + partial over total
    const detOk = (detDist['compliant'] || 0) + (detDist['partially_compliant'] || 0);
    const llmOk = (llmDist['compliant'] || 0) + (llmDist['partially_compliant'] || 0);
    const combined = totalVersions > 0 ? Math.round(((detOk + llmOk) / (totalVersions * 2)) * 100) : 0;

    const healthClass = combined >= 70 ? 'gdash-health--good' : combined >= 40 ? 'gdash-health--warn' : 'gdash-health--bad';

    const miniBar = (dist) => {
      const t = Object.values(dist).reduce((a, b) => a + b, 0);
      if (t === 0) return '<div class="gdash-minibar"><div class="gdash-minibar__empty"></div></div>';
      const c = dist['compliant'] || 0;
      const p = dist['partially_compliant'] || 0;
      const n = dist['non_compliant'] || 0;
      const ne = dist['not_evaluated'] || 0;
      return `
        <div class="gdash-minibar">
          ${c > 0 ? `<div class="gdash-minibar__seg" style="width:${(c/t)*100}%;background:#10B981" title="Compliant: ${c}"></div>` : ''}
          ${p > 0 ? `<div class="gdash-minibar__seg" style="width:${(p/t)*100}%;background:#F97316" title="Partial: ${p}"></div>` : ''}
          ${n > 0 ? `<div class="gdash-minibar__seg" style="width:${(n/t)*100}%;background:#EF4444" title="Non-compliant: ${n}"></div>` : ''}
          ${ne > 0 ? `<div class="gdash-minibar__seg" style="width:${(ne/t)*100}%;background:#6B84A8" title="Not evaluated: ${ne}"></div>` : ''}
        </div>`;
    };

    return `
      <div class="gdash-project-card" style="animation-delay:${index * 60}ms">
        <div class="gdash-project-card__header">
          <span class="gdash-project-card__name">${escHtml(project.name)}</span>
          <span class="gdash-project-card__health ${healthClass}">${combined}%</span>
        </div>
        <div class="gdash-project-card__stats">
          <div class="gdash-project-card__stat">
            <span class="gdash-project-card__stat-val">${project.total_models}</span>
            <span class="gdash-project-card__stat-lbl">models</span>
          </div>
          <div class="gdash-project-card__stat">
            <span class="gdash-project-card__stat-val">${project.total_versions}</span>
            <span class="gdash-project-card__stat-lbl">versions</span>
          </div>
        </div>
        <div class="gdash-project-card__bars">
          <div class="gdash-project-card__bar-group">
            <span class="gdash-project-card__bar-label">Deterministic</span>
            ${miniBar(detDist)}
          </div>
          <div class="gdash-project-card__bar-group">
            <span class="gdash-project-card__bar-label">LLM</span>
            ${miniBar(llmDist)}
          </div>
        </div>
      </div>`;
  }

  return { render };
})();
