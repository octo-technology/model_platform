// Model detail page: general info · metrics · model card (read-only)
// Mirrors AgentDetailPage. There's no single-model detail endpoint (unlike agent_infos),
// so this pulls the model's governance info out of the project's bulk governance
// response (same data source Governance/Audit & Compliance already renders per-version)
// plus its compliance metadata from model_infos.
const ModelDetailPage = (() => {

  function render(container, { project, name, version }) {
    container.innerHTML = loadingHTML();
    Promise.all([
      API.projects.governance(project),
      API.modelInfos.listForProject(project).catch(() => []),
    ])
      .then(([data, modelInfos]) => {
        const entries = data.project_governance || data.project_gouvernance || (Array.isArray(data) ? data : []);
        const info = entries
          .map(e => e.model_information)
          .find(m => m && (m.model_name || m.name) === name && String(m.version) === String(version));

        if (!info) {
          container.innerHTML = errorHTML(`Model version ${name} v${version} not found.`);
          return;
        }

        const complianceEntry = modelInfos.find(m => m.model_name === name && String(m.model_version) === String(version)) || {};
        renderDetail(container, project, name, version, info, complianceEntry);
      })
      .catch(err => { container.innerHTML = errorHTML(err.message); });
  }

  function renderDetail(container, project, name, version, info, compliance) {
    const tags = info.tags || {};
    const metrics = info.metrics || {};

    const title    = `${escHtml(name)} <span class="badge badge-neutral mono" style="font-size:13px;vertical-align:middle">v${escHtml(version)}</span>`;
    const riskHtml = `<span style="vertical-align:middle;display:inline-flex">${riskBadge(compliance.risk_level)}</span>`;

    const runName = tags['mlflow.runName'] || '—';
    const user    = tags['mlflow.user'] || '—';
    const created = info.creation_timestamp ? new Date(info.creation_timestamp).toLocaleString() : '—';

    const metricsHtml = Object.keys(metrics).length > 0
      ? `<div class="metric-chips">${Object.entries(metrics).map(([k, v]) =>
          `<span class="metric-chip"><span class="metric-chip-key">${escHtml(k)}</span>${escHtml(String(v))}</span>`
        ).join('')}</div>`
      : '—';

    const paramsEntries = Object.entries(info.params || {});
    const modelCard = compliance.model_card || tags['mlflow.note.content'] || null;

    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="breadcrumb">
              <a href="#projects" id="bc-projects">Projects</a>
              <span class="breadcrumb-sep">/</span>
              <a href="#project/${encodeURIComponent(project)}" id="bc-project">${escHtml(project)}</a>
              <span class="breadcrumb-sep">/</span>
              <span>Models</span>
              <span class="breadcrumb-sep">/</span>
              <span class="breadcrumb-current">${escHtml(name)}</span>
            </div>
            <h1 class="page-title">${title} ${riskHtml}</h1>
          </div>
        </div>

        <div class="page-content">

          <!-- General info -->
          <div class="card mb-4">
            <div class="card-header">
              <span class="card-title">General Information</span>
            </div>
            <div class="table-wrap">
              <table>
                <tbody>
                  ${infoRow('Run name', runName)}
                  ${infoRow('Owner', user)}
                  ${infoRow('Created', created)}
                  ${infoRow('Metrics', metricsHtml, true)}
                  ${infoRow('Risk level', riskBadge(compliance.risk_level), true)}
                  ${infoRow('Deterministic compliance', complianceBadge(compliance.deterministic_compliance), true)}
                  ${infoRow('LLM compliance', complianceBadge(compliance.llm_compliance), true)}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Model Card -->
          <div class="card mb-4">
            <div class="card-header">
              <span class="card-title">Model Card</span>
            </div>
            <div style="padding:16px 20px">
              ${modelCard
                ? `<div class="ai-act-md">${renderMarkdown(modelCard)}</div>`
                : `<span style="color:var(--text-2);font-size:13px">No model card configured.</span>`
              }
            </div>
          </div>

          <!-- Params -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">Parameters</span>
              <span class="section-count">${paramsEntries.length}</span>
            </div>
            ${paramsEntries.length === 0
              ? emptyHTML('No parameters logged', 'This model version does not log any hyperparameters.')
              : `<div class="table-wrap">
                   <table>
                     <thead>
                       <tr>
                         <th>Name</th>
                         <th>Value</th>
                       </tr>
                     </thead>
                     <tbody>
                       ${paramsEntries.map(([k, v]) => `
                         <tr>
                           <td class="font-bold mono">${escHtml(k)}</td>
                           <td class="mono" style="font-size:13px">${escHtml(String(v))}</td>
                         </tr>`).join('')}
                     </tbody>
                   </table>
                 </div>`
            }
          </div>

        </div>
      </div>
    `;

    // Breadcrumb navigation
    document.getElementById('bc-projects').addEventListener('click', e => {
      e.preventDefault();
      App.navigateTo('projects');
    });
    document.getElementById('bc-project').addEventListener('click', e => {
      e.preventDefault();
      App.navigateTo('project', { name: project });
    });
  }

  // ── Helpers ────────────────────────────────────────────────────

  function infoRow(label, valueHtml, raw = false) {
    const cell = raw ? valueHtml : escHtml(valueHtml);
    return `
      <tr>
        <td style="width:200px;color:var(--text-2);font-size:13px;padding:10px 20px">${escHtml(label)}</td>
        <td style="padding:10px 20px">${cell}</td>
      </tr>`;
  }

  function riskBadge(risk) {
    if (!risk) return `<span class="badge badge-neutral">—</span>`;
    const map = { unacceptable: 'badge-error', high: 'badge-red', limited: 'badge-orange', minimal: 'badge-green' };
    const cls = map[String(risk).toLowerCase()] || 'badge-neutral';
    return `<span class="badge ${cls}">${escHtml(risk)}</span>`;
  }

  function complianceBadge(status) {
    const colors = {
      compliant: 'badge-green',
      partially_compliant: 'badge-orange',
      non_compliant: 'badge-red',
      not_evaluated: 'badge-neutral',
    };
    const labels = {
      compliant: 'Compliant',
      partially_compliant: 'Partial',
      non_compliant: 'Non-compliant',
      not_evaluated: 'Not evaluated',
    };
    const s = status || 'not_evaluated';
    return `<span class="badge ${colors[s] || 'badge-neutral'}">${escHtml(labels[s] || s)}</span>`;
  }

  function renderMarkdown(md) {
    if (typeof marked === 'undefined') return `<pre style="white-space:pre-wrap">${escHtml(md)}</pre>`;
    let html = marked.parse(md, { breaks: false, gfm: true });
    return html
      .replace(/<hr\s*\/?>/g, '')
      .replace(/<table>/g, '<div class="ai-act-table-scroll"><table>')
      .replace(/<\/table>/g, '</table></div>');
  }

  function loadingHTML(text = 'Loading…') {
    return `<div class="loading-screen"><span class="spinner"></span><span>${text}</span></div>`;
  }

  function errorHTML(msg) {
    return `<div class="empty-state"><div class="empty-state-title" style="color:var(--red-light)">Error</div><div class="empty-state-desc">${escHtml(msg)}</div></div>`;
  }

  function emptyHTML(title, desc) {
    return `<div class="empty-state" style="padding:32px"><div class="empty-state-title">${title}</div><div class="empty-state-desc">${desc}</div></div>`;
  }

  return { render };
})();
