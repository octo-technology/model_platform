// Agent detail page: general info · agent card · tools · guardrails (read-only)
const AgentDetailPage = (() => {

  function render(container, { project, name, version }) {
    container.innerHTML = loadingHTML();
    API.agentInfos.get(project, name, version)
      .then(agent => renderDetail(container, project, agent))
      .catch(err  => { container.innerHTML = errorHTML(err.message); });
  }

  function renderDetail(container, project, a) {
    const title      = `${escHtml(a.agent_name)} <span class="badge badge-neutral mono" style="font-size:13px;vertical-align:middle">v${escHtml(a.agent_version)}</span>`;
    const riskHtml   = riskBadge(a.risk_level);
    const tools      = a.tools || [];
    const guardrails = a.guardrails || null;

    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="breadcrumb">
              <a href="#projects" id="bc-projects">Projects</a>
              <span class="breadcrumb-sep">/</span>
              <a href="#project/${encodeURIComponent(project)}" id="bc-project">${escHtml(project)}</a>
              <span class="breadcrumb-sep">/</span>
              <span>Agents</span>
              <span class="breadcrumb-sep">/</span>
              <span class="breadcrumb-current">${escHtml(a.agent_name)}</span>
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
                  ${infoRow('Description',   a.description  || '—')}
                  ${infoRow('Agent type',    a.agent_type   ? `<span class="badge badge-neutral">${escHtml(a.agent_type)}</span>` : '—', true)}
                  ${infoRow('LLM provider',  a.llm_provider || '—')}
                  ${infoRow('LLM model',     a.llm_model    ? `<span class="mono">${escHtml(a.llm_model)}</span>` : '—', true)}
                  ${infoRow('Max iterations',a.max_iterations != null ? String(a.max_iterations) : '—')}
                  ${infoRow('Risk level',    riskBadge(a.risk_level), true)}
                  ${infoRow('Suggested risk',riskBadge(a.suggested_risk_level), true)}
                  ${infoRow('Deterministic compliance', complianceBadge(a.deterministic_compliance))}
                  ${infoRow('LLM compliance',           complianceBadge(a.llm_compliance))}
                  ${infoRow('ACT review',    a.act_review   ? `<span style="white-space:pre-wrap;font-size:12px">${escHtml(a.act_review)}</span>` : '—', true)}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Agent Card -->
          <div class="card mb-4">
            <div class="card-header">
              <span class="card-title">Agent Card</span>
            </div>
            <div style="padding:16px 20px">
              ${a.agent_card
                ? `<div class="ai-act-md">${renderMarkdown(a.agent_card)}</div>`
                : `<span style="color:var(--text-2);font-size:13px">No agent card configured.</span>`
              }
            </div>
          </div>

          <!-- Tools -->
          <div class="card mb-4">
            <div class="card-header">
              <span class="card-title">Tools</span>
              <span class="section-count">${tools.length}</span>
            </div>
            ${tools.length === 0
              ? emptyHTML('No tools configured', 'This agent does not declare any tools.')
              : `<div class="table-wrap">
                   <table>
                     <thead>
                       <tr>
                         <th>Name</th>
                         <th>Description</th>
                       </tr>
                     </thead>
                     <tbody>
                       ${tools.map(t => `
                         <tr>
                           <td class="font-bold mono">${escHtml(t.name || '—')}</td>
                           <td style="color:var(--text-2);font-size:13px">${escHtml(t.description || '—')}</td>
                         </tr>`).join('')}
                     </tbody>
                   </table>
                 </div>`
            }
          </div>

          <!-- Guardrails -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">Guardrails</span>
            </div>
            <div style="padding:16px 20px">
              ${guardrails
                ? `<pre style="margin:0;white-space:pre-wrap;font-family:var(--font-mono);font-size:13px;color:var(--text-1);background:var(--bg-1);padding:12px 16px;border-radius:6px;border:1px solid var(--border-0)">${escHtml(String(guardrails))}</pre>`
                : `<span style="color:var(--text-2);font-size:13px">No guardrails configured.</span>`
              }
            </div>
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
    if (!status || status === 'not_evaluated') return `<span class="badge badge-neutral">Not evaluated</span>`;
    if (status === 'compliant')           return `<span class="badge badge-green">Compliant</span>`;
    if (status === 'partially_compliant') return `<span class="badge badge-orange">Partial</span>`;
    if (status === 'non_compliant')       return `<span class="badge badge-red">Non-compliant</span>`;
    return `<span class="badge badge-neutral">${escHtml(status)}</span>`;
  }

  function renderMarkdown(md) {
    if (typeof marked === 'undefined') return `<pre style="white-space:pre-wrap">${escHtml(md)}</pre>`;
    return marked.parse(md, { breaks: false, gfm: true });
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
