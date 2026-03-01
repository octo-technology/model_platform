// Governance page — model audit trail, version history, deployment events
const GovernancePage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Audit & Compliance</div>
            <h1 class="page-title">Governance</h1>
          </div>
        </div>

        <div class="page-content">
          <div class="flex items-center gap-3 mb-4" style="max-width:380px">
            <div style="flex:1" class="form-group">
              <label class="form-label">Select project</label>
              <select class="form-select" id="gov-project-select">
                <option value="">Loading projects…</option>
              </select>
            </div>
          </div>

          <div id="gov-content">
            <div class="empty-state" style="padding: 80px 0">
              <div class="empty-state-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div class="empty-state-title">Select a project</div>
              <div class="empty-state-desc">Choose a project above to view its governance data.</div>
            </div>
          </div>
        </div>
      </div>
    `;

    loadProjectList();

    document.getElementById('gov-project-select').addEventListener('change', e => {
      const proj = e.target.value;
      if (proj) loadGovernanceData(proj);
    });
  }

  async function loadProjectList() {
    const select = document.getElementById('gov-project-select');
    try {
      const projects = await API.projects.list();
      if (!projects || projects.length === 0) {
        select.innerHTML = '<option value="">No projects available</option>';
        return;
      }
      select.innerHTML = '<option value="">— Choose a project —</option>' +
        projects.map(p => {
          const name = p.name || p.Name || '';
          return `<option value="${escHtml(name)}">${escHtml(name)}</option>`;
        }).join('');
    } catch (err) {
      select.innerHTML = '<option value="">Failed to load projects</option>';
    }
  }

  async function loadGovernanceData(projectName) {
    const content = document.getElementById('gov-content');
    content.innerHTML = `<div class="loading-screen"><span class="spinner"></span><span>Loading governance data…</span></div>`;

    try {
      const data = await API.projects.governance(projectName);
      renderGovernance(projectName, data, content);
    } catch (err) {
      content.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--red-light)">Error loading data</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>`;
    }
  }

  function renderGovernance(projectName, data, content) {
    // Backend returns { project_governance: [ { model_information: {...}, events: [...] } ] }
    const entries = data.project_governance || data.project_gouvernance || (Array.isArray(data) ? data : []);

    // Flatten into display-friendly arrays
    const versions = entries.flatMap(e => {
      const info = e.model_information || e;
      return info ? [info] : [];
    });
    const deploymentEvents = entries.flatMap(e => e.events || []);

    // Group versions by model_name for per-model sections
    const modelGroups = {};
    versions.forEach(v => {
      const modelName = v.model_name || v.name || 'Unknown';
      if (!modelGroups[modelName]) modelGroups[modelName] = [];
      modelGroups[modelName].push(v);
    });

    const modelSections = Object.entries(modelGroups)
      .map(([modelName, versionList]) => renderModelSection(modelName, versionList))
      .join('');

    content.innerHTML = `
      <div class="flex items-center justify-between mb-4">
        <h2 style="font-family:var(--font-display);font-size:22px;letter-spacing:0.04em">${escHtml(projectName)}</h2>
        <button class="btn btn-secondary btn-sm" id="download-gov-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Download archive
        </button>
      </div>

      ${modelSections || `<div class="empty-state" style="padding:40px 0"><div class="empty-state-title">No model versions found</div></div>`}
      ${renderEventsSection(deploymentEvents)}
    `;

    document.getElementById('download-gov-btn').addEventListener('click', async () => {
      const btn = document.getElementById('download-gov-btn');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span> Downloading…';
      try {
        const blob = await API.projects.downloadGovernance(projectName);
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${projectName}-governance.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        Toast.success('Governance archive downloaded.');
      } catch (err) {
        Toast.error(`Download failed: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> Download archive`;
      }
    });
  }

  function renderModelSection(modelName, versions) {
    // Look for a model card note in any version's tags
    let modelCard = null;
    for (const v of versions) {
      const note = v.tags && v.tags['mlflow.note.content'];
      if (note) { modelCard = note; break; }
    }

    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">${escHtml(modelName)}</span>
          <span class="section-count">${versions.length}</span>
        </div>
        ${modelCard ? `
          <div style="padding:12px 20px;border-bottom:1px solid var(--border)">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-2);margin-bottom:6px">Model Card</div>
            <p style="color:var(--text-1);font-size:13px;white-space:pre-wrap;margin:0">${escHtml(modelCard)}</p>
          </div>
        ` : ''}
        ${renderVersionsSection(versions)}
      </div>`;
  }

  function renderVersionsSection(versions) {
    if (!versions || versions.length === 0) return '';

    const rows = versions.map(v => {
      const ver     = v.version || '—';
      const runName = (v.tags && v.tags['mlflow.runName']) || '—';
      const user    = (v.tags && v.tags['mlflow.user'])    || '—';
      const metrics = v.metrics ? Object.entries(v.metrics).map(([k, val]) => `${k}: ${val}`).join(', ') : '—';

      let created = '—';
      const historyRaw = v.tags && v.tags['mlflow.log-model.history'];
      if (historyRaw) {
        try {
          const history = JSON.parse(historyRaw);
          if (Array.isArray(history) && history[0] && history[0].utc_time_created) {
            created = formatDate(history[0].utc_time_created);
          }
        } catch {}
      }

      return `
        <tr>
          <td class="mono">${escHtml(String(ver))}</td>
          <td>${escHtml(runName)}</td>
          <td>${escHtml(user)}</td>
          <td style="white-space:nowrap">${escHtml(created)}</td>
          <td style="max-width:220px;color:var(--text-1);font-size:11px">${escHtml(metrics)}</td>
        </tr>`;
    }).join('');

    return `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Version</th><th>Run Name</th><th>User</th><th>Created</th><th>Metrics</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderEventsSection(events) {
    // Filter out placeholder epoch dates (1970-01-01)
    const validEvents = (events || []).filter(e => {
      const date = e.deployment_date || e.DeploymentDate || e.date || '';
      if (!date || date === '—') return true;
      return new Date(date).getFullYear() > 1970;
    });

    if (validEvents.length === 0) return '';

    const rows = validEvents.map(e => {
      const date    = e.deployment_date || e.DeploymentDate || e.date || '—';
      const dName   = e.deployment_name || e.DeploymentName || '—';
      const version = e.version         || e.Version        || '—';
      const project = e.project_name    || e.ProjectName    || '—';
      const model   = e.model_name      || e.ModelName      || '—';

      return `
        <tr>
          <td class="mono text-sm">${formatDate(date)}</td>
          <td class="mono">${escHtml(dName)}</td>
          <td class="mono">${escHtml(String(version))}</td>
          <td>${escHtml(project)}</td>
          <td class="font-bold">${escHtml(model)}</td>
        </tr>`;
    }).join('');

    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">Deployment Events</span>
          <span class="section-count">${validEvents.length}</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th><th>Deployment name</th><th>Version</th>
                <th>Project</th><th>Model</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>`;
  }

  function formatDate(raw) {
    if (!raw || raw === '—') return '—';
    try {
      const d = new Date(raw);
      if (isNaN(d)) return escHtml(String(raw));
      return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
        ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    } catch { return escHtml(String(raw)); }
  }

  return { render };
})();
