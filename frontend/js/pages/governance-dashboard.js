// Governance Dashboard — platform-wide compliance overview
const GovernanceDashboardPage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Governance</div>
            <h1 class="page-title">Governance overview</h1>
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
      <!-- KPI: same flat strip as the Monitoring page -->
      <h2 class="section-title" style="margin-bottom:8px">Platform KPI</h2>
      <div class="fleet-header">
        <div><div class="fleet-stat-label">Projects</div><div class="fleet-stat-value">${s.total_projects}</div></div>
        <div><div class="fleet-stat-label">Models</div><div class="fleet-stat-value">${s.total_models}</div></div>
        <div><div class="fleet-stat-label">Versions</div><div class="fleet-stat-value">${s.total_versions}</div></div>
        <div>
          <div class="fleet-stat-label">Gate policy</div>
          <div class="fleet-stat-value">
            <span class="gdash-policy-badge ${policyClass[data.gate_policy] || ''}">${escHtml(policyLabels[data.gate_policy] || data.gate_policy)}</span>
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

  // ── Donut Charts ───────────────────────────────────────────

  const TONE_COLORS = {
    ok:      'var(--status-ok-fg)',
    warn:    'var(--status-warn-fg)',
    error:   'var(--status-error-fg)',
    neutral: 'var(--status-neutral-fg)',
  };

  // Chart fills reuse the shared scales so a slice and a badge for the same
  // value are never two different colours.
  function riskPalette() {
    const step = key => ({ color: `var(--risk-${key}-fg)`, label: Status.label('risk', key) });
    return {
      'minimal':       step('minimal'),
      'limited':       step('limited'),
      'high':          step('high'),
      'unacceptable':  step('unacceptable'),
      'non renseigne': { color: 'var(--risk-unknown-fg)', label: 'Not set' },
    };
  }

  function compliancePalette() {
    const entry = key => ({ color: TONE_COLORS[Status.tone('compliance', key)], label: Status.label('compliance', key) });
    return {
      'compliant':           entry('compliant'),
      'partially_compliant': entry('partially_compliant'),
      'non_compliant':       entry('non_compliant'),
      'not_evaluated':       entry('not_evaluated'),
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
      const p = palette[key] || { color: TONE_COLORS.neutral, label: key };
      segments.push(`${p.color} ${cumulative}% ${cumulative + pct}%`);
      cumulative += pct;
    }
    const gradient = `conic-gradient(${segments.join(', ')})`;

    const legend = entries.map(([key, count]) => {
      const p = palette[key] || { color: TONE_COLORS.neutral, label: key };
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
          ${c > 0 ? `<div class="gdash-minibar__seg" style="width:${(c/t)*100}%;background:${TONE_COLORS.ok}" title="${Status.label('compliance', 'compliant')}: ${c}"></div>` : ''}
          ${p > 0 ? `<div class="gdash-minibar__seg" style="width:${(p/t)*100}%;background:${TONE_COLORS.warn}" title="${Status.label('compliance', 'partially_compliant')}: ${p}"></div>` : ''}
          ${n > 0 ? `<div class="gdash-minibar__seg" style="width:${(n/t)*100}%;background:${TONE_COLORS.error}" title="${Status.label('compliance', 'non_compliant')}: ${n}"></div>` : ''}
          ${ne > 0 ? `<div class="gdash-minibar__seg" style="width:${(ne/t)*100}%;background:${TONE_COLORS.neutral}" title="${Status.label('compliance', 'not_evaluated')}: ${ne}"></div>` : ''}
        </div>`;
    };

    return `
      <div class="gdash-project-card" style="animation-delay:${index * 60}ms">
        <div class="gdash-project-card__header">
          <span class="gdash-project-card__name">${escHtml(project.name)}</span>
          <span class="gdash-project-card__health ${healthClass}"
                title="Share of version evaluations (Deterministic + LLM) that are compliant or partial">${combined}% compliant</span>
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
