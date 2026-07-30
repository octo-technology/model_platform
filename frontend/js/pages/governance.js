// Governance page — model & agent audit trail, version history, deployment events
const GovernancePage = (() => {

  // Metrics chips only surface these core scoring metrics — the rest (dataset
  // sizing, per-split default rates, etc.) is noise in this compact table view.
  const DISPLAYED_METRIC_KEYS = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc'];

  // Per-kind adapters so the AI Act / review / risk-suggestion UI works for both
  // models and agents without duplicating the modal logic.
  const ENTITY_ADAPTERS = {
    model: {
      label: 'Model',
      aiActCard:        (proj, name, ver) => API.modelInfos.aiActCard(proj, name, ver),
      actReview:        (proj, name, ver) => API.ai.actReview(proj, name, ver),
      suggestRiskLevel: (proj, name, ver) => API.ai.suggestRiskLevel(proj, name, ver),
      acceptRiskLevel:  (proj, name, ver, level) => API.modelInfos.acceptRiskLevel(proj, name, ver, level),
      evaluateCompliance: (proj) => API.compliance.evaluateProject(proj),
    },
    agent: {
      label: 'Agent',
      aiActCard:        (proj, name, ver) => API.agentInfos.aiActCard(proj, name, ver),
      actReview:        (proj, name, ver) => API.ai.agentActReview(proj, name, ver),
      suggestRiskLevel: (proj, name, ver) => API.ai.agentSuggestRiskLevel(proj, name, ver),
      acceptRiskLevel:  (proj, name, ver, level) => API.agentInfos.acceptRiskLevel(proj, name, ver, level),
      evaluateCompliance: (proj) => API.agentInfos.evaluateCompliance(proj),
    },
  };

  let aiAvailable = false;
  let aiCache = { model: {}, agent: {} }; // kind → "name:version" → { actReview, llmCompliance, deterministicCompliance }
  let modelCardCache = {}; // key: "modelName:version" → markdown string (models only)
  let agentCardCache = {}; // key: "agentName:version" → markdown string (agents only)
  let riskCache = { model: {}, agent: {} }; // kind → "name:version" → { riskLevel, suggestedRiskLevel }

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Governance</div>
            <h1 class="page-title">Audit & Compliance</h1>
          </div>
        </div>

        <div class="page-content">

          <div class="compliance-report-banner">
            <div class="compliance-report-banner__icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <div class="compliance-report-banner__body">
              <div class="compliance-report-banner__title">Platform Compliance Report</div>
              <div class="compliance-report-banner__desc">
                Generate a full audit PDF covering all projects and models on the platform:
                executive summary, risk level distribution, deterministic &amp; LLM compliance statuses,
                AI Act cards, and technical metadata annexes.
              </div>
            </div>
            <div class="compliance-report-banner__action">
              <button class="btn compliance-report-btn" id="download-compliance-report-btn">
                <span class="compliance-report-btn__idle">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  <span>Download</span>
                  <span class="compliance-report-btn__badge">PDF</span>
                </span>
                <span class="compliance-report-btn__loading" style="display:none">
                  <span class="compliance-report-spinner"></span>
                  <span>Generating&hellip;</span>
                </span>
              </button>
            </div>
          </div>

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

    // Check AI availability once per page render
    API.ai.status().then(s => { aiAvailable = s.available; });

    loadProjectList();
    bindPlatformReportButton();

    document.getElementById('gov-project-select').addEventListener('change', e => {
      const proj = e.target.value;
      if (proj) loadGovernanceData(proj);
    });
  }

  function bindPlatformReportButton() {
    const reportBtn = document.getElementById('download-compliance-report-btn');
    if (!reportBtn) return;
    reportBtn.addEventListener('click', async () => {
      const idle = reportBtn.querySelector('.compliance-report-btn__idle');
      const loading = reportBtn.querySelector('.compliance-report-btn__loading');
      reportBtn.disabled = true;
      idle.style.display = 'none';
      loading.style.display = '';
      try {
        const blob = await API.compliance.downloadPlatformReport();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'platform_compliance_report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        Toast.success('Report downloaded.');
      } catch (err) {
        Toast.error('Failed to generate report: ' + err.message);
      } finally {
        reportBtn.disabled = false;
        idle.style.display = '';
        loading.style.display = 'none';
      }
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
      const [data, list, agentList] = await Promise.all([
        API.projects.governance(projectName),
        API.modelInfos.listForProject(projectName).catch(() => []),
        API.agentInfos.listForProject(projectName).catch(() => []),
      ]);

      aiCache = { model: {}, agent: {} };
      riskCache = { model: {}, agent: {} };
      for (const item of list) {
        const k = `${item.model_name}:${item.model_version}`;
        aiCache.model[k] = {
          actReview: item.act_review,
          deterministicCompliance: item.deterministic_compliance || 'not_evaluated',
          llmCompliance: item.llm_compliance || 'not_evaluated',
        };
        riskCache.model[k] = {
          riskLevel: item.risk_level || null,
          suggestedRiskLevel: item.suggested_risk_level || null,
        };
        if (item.model_card) {
          modelCardCache[k] = item.model_card;
        }
      }
      for (const item of agentList) {
        const k = `${item.agent_name}:${item.agent_version}`;
        aiCache.agent[k] = {
          actReview: item.act_review,
          deterministicCompliance: item.deterministic_compliance || 'not_evaluated',
          llmCompliance: item.llm_compliance || 'not_evaluated',
        };
        riskCache.agent[k] = {
          riskLevel: item.risk_level || null,
          suggestedRiskLevel: item.suggested_risk_level || null,
        };
      }

      renderGovernance(projectName, data, agentList, content);
    } catch (err) {
      content.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--red-light)">Error loading data</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>`;
    }
  }

  function renderGovernance(projectName, data, agentList, content) {
    const entries = data.project_governance || data.project_gouvernance || (Array.isArray(data) ? data : []);

    const versions = entries.flatMap(e => {
      const info = e.model_information || (e.agent_information ? null : e);
      return info ? [info] : [];
    });
    const deploymentEvents = entries.flatMap(e => e.events || []);

    modelCardCache = {};
    const modelGroups = {};
    versions.forEach(v => {
      const modelName = v.model_name || v.name || 'Unknown';
      if (!modelGroups[modelName]) modelGroups[modelName] = [];
      modelGroups[modelName].push(v);
      const note = v.tags && v.tags['mlflow.note.content'];
      if (note) modelCardCache[`${modelName}:${v.version}`] = note;
    });

    Object.values(modelGroups).forEach(versionList => versionList.sort((a, b) => Number(b.version) - Number(a.version)));

    const modelSections = Object.entries(modelGroups)
      .map(([modelName, versionList]) => renderModelSection(modelName, versionList, projectName, aiCache.model))
      .join('');

    const agentGovernanceInfo = {};
    entries.forEach(e => {
      const info = e.agent_information;
      if (!info) return;
      const key = `${info.agent_name}:${info.agent_version}`;
      agentGovernanceInfo[key] = {
        createdAt: info.creation_timestamp || null,
        owner: (info.run_tags && info.run_tags['mlflow.user']) || null,
      };
    });

    agentCardCache = {};
    const agentGroups = {};
    (agentList || []).forEach(a => {
      if (!agentGroups[a.agent_name]) agentGroups[a.agent_name] = [];
      agentGroups[a.agent_name].push(a);
      if (a.agent_card) {
        agentCardCache[`${a.agent_name}:${a.agent_version}`] = a.agent_card;
      }
    });

    Object.values(agentGroups).forEach(versionList => versionList.sort((a, b) => Number(b.agent_version) - Number(a.agent_version)));

    const agentSections = Object.entries(agentGroups)
      .map(([agentName, versionList]) => renderAgentSection(agentName, versionList, projectName, agentGovernanceInfo))
      .join('');

    content.innerHTML = `
      <div class="flex items-center justify-between mb-4">
        <h2 style="font-family:var(--font-display);font-size:22px;letter-spacing:0.04em">${escHtml(projectName)}</h2>
        <div class="flex gap-2">
          <button class="btn btn-primary btn-sm" id="evaluate-compliance-btn">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Re-evaluate compliance
          </button>
          <button class="btn btn-secondary btn-sm" id="download-gov-btn">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            Download archive
          </button>
        </div>
      </div>

      <div class="page-eyebrow" style="margin-bottom:8px">Models</div>
      ${modelSections || `<div class="empty-state" style="padding:40px 0"><div class="empty-state-title">No model versions found</div></div>`}

      <div class="page-eyebrow" style="margin:28px 0 8px">Agents</div>
      ${agentSections || `<div class="empty-state" style="padding:40px 0"><div class="empty-state-title">No agent versions found</div></div>`}

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

    document.getElementById('evaluate-compliance-btn').addEventListener('click', async () => {
      const btn = document.getElementById('evaluate-compliance-btn');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span> Evaluating…';
      try {
        await Promise.all([
          ENTITY_ADAPTERS.model.evaluateCompliance(projectName),
          ENTITY_ADAPTERS.agent.evaluateCompliance(projectName),
        ]);
        Toast.success('Compliance re-evaluated.');
        loadGovernanceData(projectName);
      } catch (err) {
        Toast.error(`Error: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Re-evaluate compliance`;
      }
    });

    // Delegate clicks on action buttons
    content.addEventListener('click', async e => {
      const modelCardBtn = e.target.closest('.model-card-btn');
      if (modelCardBtn) {
        openModelCardModal(modelCardBtn.dataset.project, modelCardBtn.dataset.model, modelCardBtn.dataset.version);
        return;
      }

      const agentCardBtn = e.target.closest('.agent-card-btn');
      if (agentCardBtn) {
        openAgentCardModal(agentCardBtn.dataset.project, agentCardBtn.dataset.model, agentCardBtn.dataset.version);
        return;
      }

      const aiActBtn = e.target.closest('.ai-act-btn');
      if (aiActBtn) {
        openAiActModal(aiActBtn.dataset.kind, aiActBtn.dataset.project, aiActBtn.dataset.model, aiActBtn.dataset.version);
        return;
      }

      const directReviewBtn = e.target.closest('.ai-direct-review-btn');
      if (directReviewBtn) {
        openDirectReviewModal(directReviewBtn.dataset.kind, directReviewBtn.dataset.project, directReviewBtn.dataset.model, directReviewBtn.dataset.version);
        return;
      }

      const suggestRiskBtn = e.target.closest('.suggest-risk-btn');
      if (suggestRiskBtn) {
        runSuggestRiskLevel(suggestRiskBtn.dataset.kind, suggestRiskBtn.dataset.project, suggestRiskBtn.dataset.model, suggestRiskBtn.dataset.version);
        return;
      }

      const acceptRiskBtn = e.target.closest('.accept-risk-btn');
      if (acceptRiskBtn) {
        acceptRiskLevel(acceptRiskBtn.dataset.kind, acceptRiskBtn.dataset.project, acceptRiskBtn.dataset.model, acceptRiskBtn.dataset.version, acceptRiskBtn.dataset.level);
        return;
      }

    });
  }

  // ── Model Card Modal ─────────────────────────────────────────

  function openModelCardModal(projectName, modelName, version) {
    const cardContent = modelCardCache[`${modelName}:${version}`];
    const bodyHtml = cardContent
      ? `<div class="ai-act-md">${renderMarkdown(cardContent)}</div>`
      : `<p style="color:var(--text-2)">No model card available for this version.</p>`;

    Modal.open({
      title: `Model Card — ${modelName} v${version}`,
      body: bodyHtml,
      footer: cardContent ? `
        <button class="btn btn-secondary btn-sm" id="model-card-dl-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Download .md
        </button>` : '',
    });

    const dlBtn = document.getElementById('model-card-dl-btn');
    if (dlBtn) {
      dlBtn.addEventListener('click', () => downloadMarkdown(cardContent, `model-card-${modelName}-v${version}.md`));
    }
  }

  // ── Agent Card Modal ──────────────────────────────────────────

  function openAgentCardModal(projectName, agentName, version) {
    const cardContent = agentCardCache[`${agentName}:${version}`];
    const bodyHtml = cardContent
      ? `<div class="ai-act-md">${renderMarkdown(cardContent)}</div>`
      : `<p style="color:var(--text-2)">No agent card available for this version.</p>`;

    Modal.open({
      title: `Agent Card — ${agentName} v${version}`,
      body: bodyHtml,
      footer: cardContent ? `
        <button class="btn btn-secondary btn-sm" id="agent-card-dl-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Download .md
        </button>` : '',
    });

    const dlBtn = document.getElementById('agent-card-dl-btn');
    if (dlBtn) {
      dlBtn.addEventListener('click', () => downloadMarkdown(cardContent, `agent-card-${agentName}-v${version}.md`));
    }
  }

  // ── AI Act Modal ──────────────────────────────────────────────

  async function openAiActModal(kind, projectName, modelName, version) {
    const { close } = Modal.open({
      title: `AI Act Card — ${modelName} v${version}`,
      body: `<div class="ai-act-loading"><span class="spinner"></span><span>Generating card…</span></div>`,
      footer: `
        <button class="btn btn-secondary" id="ai-act-download" disabled>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Download .md
        </button>`,
    });

    let markdownContent = '';
    try {
      const data = await ENTITY_ADAPTERS[kind].aiActCard(projectName, modelName, version);
      markdownContent = data.markdown || '';
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) {
        bodyEl.innerHTML = '';

        // Render markdown into a wrapper
        const mdWrapper = document.createElement('div');
        mdWrapper.className = 'ai-act-md';
        mdWrapper.innerHTML = renderMarkdown(markdownContent);
        bodyEl.appendChild(mdWrapper);

        // Build a TOC from the top-level numbered h2 headings only (e.g. "3. Description et..."),
        // skipping unnumbered h2 sub-headings so the bar doesn't turn into a pill dump.
        const h2s = Array.from(mdWrapper.querySelectorAll('h2'))
          .filter(h2 => /^\d+\.\s+/.test(h2.textContent.trim()));
        if (h2s.length > 1) {
          const toc = document.createElement('div');
          toc.className = 'ai-act-toc';
          h2s.forEach((h2, i) => {
            h2.id = `ai-act-s${i}`;
            const fullLabel = h2.textContent.trim();
            const btn = document.createElement('button');
            btn.className = 'ai-act-toc-btn';
            btn.textContent = fullLabel;
            btn.addEventListener('click', () => h2.scrollIntoView({ behavior: 'smooth', block: 'start' }));
            toc.appendChild(btn);
          });
          bodyEl.insertBefore(toc, mdWrapper);
        }
      }

      const dlBtn = document.getElementById('ai-act-download');
      if (dlBtn) {
        dlBtn.disabled = false;
        dlBtn.addEventListener('click', () => downloadMarkdown(markdownContent, `ia-act-${projectName}-${modelName}-v${version}.md`));
      }

    } catch (err) {
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = `<p style="color:var(--red-light)">Error: ${escHtml(err.message)}</p>`;
    }
  }

  // ── Direct Review Modal (row button) ─────────────────────────

  async function openDirectReviewModal(kind, projectName, modelName, version) {
    const key = `${modelName}:${version}`;
    const cached = aiCache[kind][key];
    const hasCache = !!(cached && cached.actReview);

    const aiIconSvg = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;
    const rerunIconSvg = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`;
    const dlIconSvg = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>`;

    const badge = `<div class="ai-output-badge">${aiIconSvg} AI Act compliance analysis by Claude</div>`;
    const loadingHtml = `${badge}<div class="ai-act-loading"><span class="spinner"></span><span>Analysis in progress…</span></div>`;
    const reviewHtml = (text) => `${badge}<div class="ai-act-md">${renderMarkdown(text)}</div>`;

    const { close } = Modal.open({
      title: `AI Act Compliance — ${modelName} v${version}`,
      body: hasCache ? reviewHtml(cached.actReview) : loadingHtml,
      footer: `
        <button class="btn btn-secondary btn-sm" id="direct-review-dl-btn" ${hasCache ? '' : 'disabled'}>
          ${dlIconSvg} Download .md
        </button>
        <button class="btn btn-ai btn-sm" id="direct-review-rerun-btn" ${hasCache ? '' : 'disabled'}>
          ${rerunIconSvg} Re-analyze
        </button>`,
    });

    let currentReview = hasCache ? cached.actReview : '';

    const rerunBtn = () => document.getElementById('direct-review-rerun-btn');
    const dlBtn    = () => document.getElementById('direct-review-dl-btn');

    // Wire download button once — reads currentReview via closure
    const dl = dlBtn();
    if (dl) dl.addEventListener('click', () => {
      if (currentReview) downloadMarkdown(currentReview, `conformite-ia-act-${projectName}-${modelName}-v${version}.md`);
    });

    const runReview = async () => {
      const btn = rerunBtn();
      const dl  = dlBtn();
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner spinner-sm"></span> Analyzing…'; }
      if (dl)  dl.disabled = true;
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = loadingHtml;

      try {
        const data = await ENTITY_ADAPTERS[kind].actReview(projectName, modelName, version);
        const review = data.review || '';
        currentReview = review;
        aiCache[kind][key] = aiCache[kind][key] || { actReview: null };
        aiCache[kind][key].actReview = review;
        if (data.llm_compliance) {
          aiCache[kind][key].llmCompliance = data.llm_compliance;
          refreshLlmBadge(kind, modelName, version);
        }
        if (bodyEl) bodyEl.innerHTML = reviewHtml(review);
        const dl2 = dlBtn();
        if (dl2) dl2.disabled = false;
      } catch (err) {
        if (bodyEl) bodyEl.innerHTML = `${badge}<p style="color:var(--red-light)">Error: ${escHtml(err.message)}</p>`;
        Toast.error(`Analysis error: ${escHtml(err.message)}`);
      } finally {
        const btn2 = rerunBtn();
        if (btn2) { btn2.disabled = false; btn2.innerHTML = `${rerunIconSvg} Re-analyze`; }
      }
    };

    const btn = rerunBtn();
    if (btn) btn.addEventListener('click', runReview);

    if (!hasCache) runReview();
  }

  // ── Markdown renderer ─────────────────────────────────────────

  function renderMarkdown(md) {
    if (typeof marked === 'undefined') return `<pre style="white-space:pre-wrap">${escHtml(md)}</pre>`;
    let html = marked.parse(md, { breaks: false, gfm: true });
    html = html
      .replace(/<hr\s*\/?>/g, '')
      .replace(/<table>/g, '<div class="ai-act-table-scroll"><table>')
      .replace(/<\/table>/g, '</table></div>');
    return wrapStatusSections(html);
  }

  function wrapStatusSections(html) {
    // Split on every <h2>/<h3> opening tag; lookahead keeps the tag in the next part.
    // <h2> (numbered section titles like "1. Classification...") must be its own split
    // point too, otherwise it gets swallowed into the previous <h3> status div.
    const parts = html.split(/(?=<h2>|<h3>)/);
    if (parts.length <= 1) return html;
    return parts.map((part, i) => {
      if (i === 0) return part;
      if (part.startsWith('<h2>')) return part;
      // Inspect only the few chars right after <h3> to detect status emojis
      const head = part.slice(4, 12);
      let sectionCls = '';
      if (head.includes('✅'))      sectionCls = 'ai-act-section ai-act-section-ok';
      else if (head.includes('⚠')) sectionCls = 'ai-act-section ai-act-section-warn';
      else if (head.includes('❌')) sectionCls = 'ai-act-section ai-act-section-error';
      if (!sectionCls) return part;
      return `<div class="${sectionCls}">${part}</div>`;
    }).join('');
  }

  // ── Risk Level Suggestion ────────────────────────────────────

  function riskBadge(level) {
    const meta = {
      unacceptable: { cls: 'risk-unacceptable', label: 'Unacceptable' },
      high:         { cls: 'risk-high',         label: 'High' },
      limited:      { cls: 'risk-limited',      label: 'Limited' },
      minimal:      { cls: 'risk-minimal',      label: 'Minimal' },
    };
    const m = meta[(level || '').toLowerCase()];
    if (!m) return `<span class="risk-badge risk-unknown">${escHtml(level || '—')}</span>`;
    return `<span class="risk-badge ${m.cls}">${m.label}</span>`;
  }

  function renderRiskCell(kind, modelName, version, projectName) {
    const key = `${modelName}:${version}`;
    const cached = riskCache[kind][key];
    const riskLevel = cached ? cached.riskLevel : null;
    const suggested = cached ? cached.suggestedRiskLevel : null;

    const safeProj  = escHtml(projectName);
    const safeModel = escHtml(modelName);
    const safeVer   = escHtml(String(version));

    let html = '';
    if (riskLevel) {
      html += riskBadge(riskLevel);
    } else if (suggested) {
      html += `<span class="risk-suggestion" title="AI suggestion — not validated">${riskBadge(suggested)}<span class="risk-suggestion-tag">suggestion</span></span>`;
      html += `
        <button class="btn btn-secondary btn-xs accept-risk-btn"
          data-kind="${kind}"
          data-project="${safeProj}"
          data-model="${safeModel}"
          data-version="${safeVer}"
          data-level="${escHtml(suggested)}"
          title="Accept this risk level">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Accept
        </button>`;
    } else {
      html += `<span class="risk-badge risk-unknown">—</span>`;
    }

    if (aiAvailable && !riskLevel) {
      html += `
        <button class="btn btn-ai btn-xs suggest-risk-btn"
          data-kind="${kind}"
          data-project="${safeProj}"
          data-model="${safeModel}"
          data-version="${safeVer}"
          title="Suggest risk level with Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
          Suggest
        </button>`;
    }

    return html;
  }

  async function runSuggestRiskLevel(kind, projectName, modelName, version) {
    const key = `${modelName}:${version}`;
    const cell = document.querySelector(`[data-risk-cell="${modelName}:${version}"]`);
    const btn = cell ? cell.querySelector('.suggest-risk-btn') : null;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span>';
    }

    try {
      const data = await ENTITY_ADAPTERS[kind].suggestRiskLevel(projectName, modelName, version);
      const level = data.suggested_risk_level;
      const justification = data.justification || '';

      if (level) {
        riskCache[kind][key] = riskCache[kind][key] || { riskLevel: null, suggestedRiskLevel: null };
        riskCache[kind][key].suggestedRiskLevel = level;
      }

      if (cell) {
        cell.innerHTML = renderRiskCell(kind, modelName, version, projectName);
      }

      if (level && justification) {
        Toast.success(`Suggested risk: ${level.toUpperCase()}`);
        openRiskSuggestionModal(kind, projectName, modelName, version, level, justification);
      } else {
        Toast.warning('Unable to determine risk level.');
      }
    } catch (err) {
      Toast.error(`Error: ${err.message}`);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg> Suggest`;
      }
    }
  }

  async function acceptRiskLevel(kind, projectName, modelName, version, level) {
    const key = `${modelName}:${version}`;
    const cell = document.querySelector(`[data-risk-cell="${modelName}:${version}"]`);
    const btn = cell ? cell.querySelector('.accept-risk-btn') : null;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span>';
    }

    try {
      await ENTITY_ADAPTERS[kind].acceptRiskLevel(projectName, modelName, version, level);
      riskCache[kind][key] = riskCache[kind][key] || { riskLevel: null, suggestedRiskLevel: null };
      riskCache[kind][key].riskLevel = level;
      if (cell) {
        cell.innerHTML = renderRiskCell(kind, modelName, version, projectName);
      }
      Toast.success(`Risk level accepted: ${level.toUpperCase()}`);
      // Close modal if open
      const modalClose = document.querySelector('#modal-container .modal-close');
      if (modalClose) modalClose.click();
    } catch (err) {
      Toast.error(`Error: ${err.message}`);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Accept`;
      }
    }
  }

  function openRiskSuggestionModal(kind, projectName, modelName, version, level, justification) {
    const levelMeta = {
      unacceptable: { icon: '🚫', title: 'Unacceptable', desc: 'Prohibited system (Art. 5)', cls: 'risk-unacceptable' },
      high:         { icon: '⚠️', title: 'High', desc: 'Mandatory compliance (Art. 6 + Annex III)', cls: 'risk-high' },
      limited:      { icon: '📋', title: 'Limited', desc: 'Transparency obligations (Art. 50)', cls: 'risk-limited' },
      minimal:      { icon: '✅', title: 'Minimal', desc: 'No specific obligations', cls: 'risk-minimal' },
    };
    const meta = levelMeta[level] || levelMeta.minimal;

    Modal.open({
      title: `Risk Suggestion — ${modelName} v${version}`,
      body: `
        <div class="risk-suggestion-result">
          <div class="risk-suggestion-result__level">
            <div class="risk-suggestion-result__icon">${meta.icon}</div>
            <div>
              <div class="risk-suggestion-result__title">${meta.title}</div>
              <div class="risk-suggestion-result__subtitle">${meta.desc}</div>
            </div>
            <span class="risk-badge ${meta.cls}" style="margin-left:auto">${meta.title}</span>
          </div>
          <div class="risk-suggestion-result__justification">
            <div class="risk-suggestion-result__justification-label">Justification</div>
            <div class="risk-suggestion-result__justification-text">${escHtml(justification)}</div>
          </div>
          <div class="risk-suggestion-result__notice">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            This suggestion is indicative only. Review the justification before accepting.
          </div>
        </div>`,
      footer: `
        <button class="btn btn-primary btn-sm" id="modal-accept-risk-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Accept Risk Level
        </button>`,
    });

    const acceptBtn = document.getElementById('modal-accept-risk-btn');
    if (acceptBtn) {
      acceptBtn.addEventListener('click', () => acceptRiskLevel(kind, projectName, modelName, version, level));
    }
  }

  // ── Render helpers ────────────────────────────────────────────

  function complianceBadge(status, label) {
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
    const cls = colors[status] || 'badge-neutral';
    const text = labels[status] || status;
    return `<span class="badge ${cls}" title="${escHtml(label)}: ${escHtml(text)}">${escHtml(text)}</span>`;
  }

  function refreshLlmBadge(kind, modelName, version) {
    const cell = document.querySelector(`[data-llm-badge="${modelName}:${version}"]`);
    if (!cell) return;
    const cached = aiCache[kind][`${modelName}:${version}`];
    const status = cached ? cached.llmCompliance : 'not_evaluated';
    cell.innerHTML = complianceBadge(status, 'LLM');
  }

  function renderModelSection(modelName, versions, projectName, cache) {
    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">${escHtml(modelName)}</span>
          <span class="section-count">${versions.length}</span>
        </div>
        ${renderVersionsSection(versions, modelName, projectName, cache)}
      </div>`;
  }

  function renderVersionsSection(versions, modelName, projectName, cache) {
    if (!versions || versions.length === 0) return '';

    const rows = versions.map(v => {
      const ver     = v.version || '—';
      const user    = (v.tags && v.tags['mlflow.user'])    || '—';
      const visibleMetrics = v.metrics
        ? DISPLAYED_METRIC_KEYS.filter(k => v.metrics[k] != null).map(k => [k, v.metrics[k]])
        : [];
      const metricsHtml = visibleMetrics.length
        ? `<div class="metric-chips">${visibleMetrics.map(([k, val]) =>
            `<span class="metric-chip"><span class="metric-chip-key">${escHtml(k)}</span>${escHtml(String(val))}</span>`
          ).join('')}</div>`
        : '—';

      const created = v.creation_timestamp ? formatDate(v.creation_timestamp) : '—';

      const safeProj  = escHtml(projectName || '');
      const safeModel = escHtml(modelName || '');
      const safeVer   = escHtml(String(ver));

      const cacheKey = `${modelName}:${ver}`;
      const cached = (cache || {})[cacheKey];
      const detCompliance = cached ? cached.deterministicCompliance : 'not_evaluated';
      const llmComplianceStatus = cached ? cached.llmCompliance : 'not_evaluated';
      const hasModelCard = !!(v.tags && v.tags['mlflow.note.content']) || !!modelCardCache[`${modelName}:${ver}`];

      const reviewLabel = 'Analyze';
      const directReviewBtn = aiAvailable ? `
        <button class="btn btn-ai btn-xs ai-direct-review-btn"
          data-kind="model"
          data-project="${safeProj}"
          data-model="${safeModel}"
          data-version="${safeVer}"
          title="AI Act compliance analysis by Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          ${reviewLabel}
        </button>` : '';

      return `
        <tr>
          <td class="mono">${safeVer}</td>
          <td>${escHtml(user)}</td>
          <td style="white-space:nowrap">${escHtml(created)}</td>
          <td class="gov-col-metrics">${metricsHtml}</td>
          <td class="gov-col-risk" data-risk-cell="${safeModel}:${safeVer}">
            <div class="flex gap-1 items-center">${renderRiskCell('model', modelName, ver, projectName)}</div>
          </td>
          <td class="gov-col-compliant">${complianceBadge(detCompliance, 'Deterministic Compliance')}</td>
          <td class="gov-col-llm" data-llm-badge="${safeModel}:${safeVer}">${complianceBadge(llmComplianceStatus, 'LLM Compliance')}</td>
          <td class="entity-actions-cell">
            <div class="flex gap-2 items-center" style="flex-wrap:nowrap">
              ${hasModelCard ? `
              <button class="btn btn-secondary btn-xs model-card-btn"
                data-project="${safeProj}"
                data-model="${safeModel}"
                data-version="${safeVer}"
                title="Voir la model card">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Model Card
              </button>` : ''}
              <button class="btn btn-secondary btn-xs ai-act-btn"
                data-kind="model"
                data-project="${safeProj}"
                data-model="${safeModel}"
                data-version="${safeVer}">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                AI Act Card
              </button>
              ${directReviewBtn}
            </div>
          </td>
        </tr>`;
    }).join('');

    return `
      <div class="table-wrap">
        <table class="gov-versions-table">
          <thead>
            <tr>
              <th class="gov-col-version">Version</th><th class="gov-col-owner">Owner</th><th class="gov-col-created">Created</th><th class="gov-col-metrics">Metrics</th><th class="gov-col-risk">Risk Level</th><th class="gov-col-compliant">Deterministic Compliance</th><th class="gov-col-llm">LLM Compliance</th><th></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderAgentSection(agentName, versions, projectName, governanceInfo) {
    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">${escHtml(agentName)}</span>
          <span class="section-count">${versions.length}</span>
        </div>
        ${renderAgentVersionsSection(versions, agentName, projectName, governanceInfo)}
      </div>`;
  }

  function renderAgentVersionsSection(versions, agentName, projectName, governanceInfo) {
    if (!versions || versions.length === 0) return '';

    const rows = versions.map(a => {
      const ver = a.agent_version || '—';
      const safeProj  = escHtml(projectName || '');
      const safeAgent = escHtml(agentName || '');
      const safeVer   = escHtml(String(ver));

      const govInfo = (governanceInfo || {})[`${agentName}:${ver}`];
      const owner   = (govInfo && govInfo.owner) || '—';
      const created = (govInfo && govInfo.createdAt) ? formatDate(govInfo.createdAt) : '—';

      const cached = aiCache.agent[`${agentName}:${ver}`];
      const detCompliance = cached ? cached.deterministicCompliance : (a.deterministic_compliance || 'not_evaluated');
      const llmComplianceStatus = cached ? cached.llmCompliance : (a.llm_compliance || 'not_evaluated');
      const hasAgentCard = !!agentCardCache[`${agentName}:${ver}`];

      const reviewLabel = 'Analyze';
      const directReviewBtn = aiAvailable ? `
        <button class="btn btn-ai btn-xs ai-direct-review-btn"
          data-kind="agent"
          data-project="${safeProj}"
          data-model="${safeAgent}"
          data-version="${safeVer}"
          title="AI Act compliance analysis by Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          ${reviewLabel}
        </button>` : '';

      return `
        <tr>
          <td class="mono">${safeVer}</td>
          <td>${escHtml(owner)}</td>
          <td style="white-space:nowrap">${escHtml(created)}</td>
          <td class="gov-col-type">${a.agent_type ? `<span class="badge badge-neutral">${escHtml(a.agent_type)}</span>` : '—'}</td>
          <td class="gov-col-llmmodel">${a.llm_model ? `<span class="mono">${escHtml(a.llm_model)}</span>` : '—'}</td>
          <td class="gov-col-risk" data-risk-cell="${safeAgent}:${safeVer}">
            <div class="flex gap-1 items-center">${renderRiskCell('agent', agentName, ver, projectName)}</div>
          </td>
          <td class="gov-col-compliant">${complianceBadge(detCompliance, 'Deterministic Compliance')}</td>
          <td class="gov-col-llm" data-llm-badge="${safeAgent}:${safeVer}">${complianceBadge(llmComplianceStatus, 'LLM Compliance')}</td>
          <td class="entity-actions-cell">
            <div class="flex gap-2 items-center" style="flex-wrap:nowrap">
              ${hasAgentCard ? `
              <button class="btn btn-secondary btn-xs agent-card-btn"
                data-project="${safeProj}"
                data-model="${safeAgent}"
                data-version="${safeVer}"
                title="Voir l'agent card">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Agent Card
              </button>` : ''}
              <button class="btn btn-secondary btn-xs ai-act-btn"
                data-kind="agent"
                data-project="${safeProj}"
                data-model="${safeAgent}"
                data-version="${safeVer}">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                AI Act Card
              </button>
              ${directReviewBtn}
            </div>
          </td>
        </tr>`;
    }).join('');

    return `
      <div class="table-wrap">
        <table class="gov-versions-table">
          <thead>
            <tr>
              <th class="gov-col-version">Version</th><th class="gov-col-owner">Owner</th><th class="gov-col-created">Created</th><th class="gov-col-type">Type</th><th class="gov-col-llmmodel">LLM model</th><th class="gov-col-risk">Risk Level</th><th class="gov-col-compliant">Deterministic Compliance</th><th class="gov-col-llm">LLM Compliance</th><th></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderAgentSection(agentName, versions, projectName) {
    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">${escHtml(agentName)}</span>
          <span class="section-count">${versions.length}</span>
        </div>
        ${renderAgentVersionsSection(versions, agentName, projectName)}
      </div>`;
  }

  function renderAgentVersionsSection(versions, agentName, projectName) {
    if (!versions || versions.length === 0) return '';

    const rows = versions.map(a => {
      const ver = a.agent_version || '—';
      const safeProj  = escHtml(projectName || '');
      const safeAgent = escHtml(agentName || '');
      const safeVer   = escHtml(String(ver));

      const cached = aiCache.agent[`${agentName}:${ver}`];
      const detCompliance = cached ? cached.deterministicCompliance : (a.deterministic_compliance || 'not_evaluated');
      const llmComplianceStatus = cached ? cached.llmCompliance : (a.llm_compliance || 'not_evaluated');
      const hasAgentCard = !!agentCardCache[`${agentName}:${ver}`];

      const reviewLabel = cached && cached.actReview ? 'Re-analyze' : 'Analyze';
      const directReviewBtn = aiAvailable ? `
        <button class="btn btn-ai btn-xs ai-direct-review-btn"
          data-kind="agent"
          data-project="${safeProj}"
          data-model="${safeAgent}"
          data-version="${safeVer}"
          title="AI Act compliance analysis by Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          ${reviewLabel}
        </button>` : '';

      return `
        <tr>
          <td class="mono">${safeVer}</td>
          <td>${a.agent_type ? `<span class="badge badge-neutral">${escHtml(a.agent_type)}</span>` : '—'}</td>
          <td>${a.llm_model ? `<span class="mono">${escHtml(a.llm_model)}</span>` : '—'}</td>
          <td style="white-space:nowrap" data-risk-cell="${safeAgent}:${safeVer}">
            <div class="flex gap-1 items-center">${renderRiskCell('agent', agentName, ver, projectName)}</div>
          </td>
          <td style="white-space:nowrap">${complianceBadge(detCompliance, 'Deterministic')}</td>
          <td style="white-space:nowrap" data-llm-badge="${safeAgent}:${safeVer}">${complianceBadge(llmComplianceStatus, 'LLM')}</td>
          <td>
            <div class="flex gap-2 items-center" style="flex-wrap:wrap">
              ${hasAgentCard ? `
              <button class="btn btn-secondary btn-xs agent-card-btn"
                data-project="${safeProj}"
                data-model="${safeAgent}"
                data-version="${safeVer}"
                title="Voir l'agent card">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Agent Card
              </button>` : ''}
              <button class="btn btn-secondary btn-xs ai-act-btn"
                data-kind="agent"
                data-project="${safeProj}"
                data-model="${safeAgent}"
                data-version="${safeVer}">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                AI Act Card
              </button>
              ${directReviewBtn}
            </div>
          </td>
        </tr>`;
    }).join('');

    return `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Version</th><th>Type</th><th>LLM model</th><th>Risk</th><th>Deterministic</th><th>LLM</th><th></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderEventsSection(events) {
    if (!events || events.length === 0) return '';

    const actionLabel = action => {
      if (!action) return '—';
      if (action.includes('remove') || action.includes('undeploy')) return 'Undeploy';
      if (action.includes('deploy')) return 'Deploy';
      return escHtml(action);
    };

    const actionBadge = action => {
      const label = actionLabel(action);
      if (label === 'Undeploy') return `<span class="badge badge-red">${label}</span>`;
      if (label === 'Deploy')   return `<span class="badge badge-green">${label}</span>`;
      return `<span class="badge badge-neutral">${label}</span>`;
    };

    const rows = events.map(e => {
      const date    = e.timestamp || '—';
      const model   = e.model_name    || '—';
      const version = e.version       || '—';
      const user    = e.user          || '—';
      const dName   = e.deployment_name || '—';

      return `
        <tr>
          <td class="mono" style="white-space:nowrap">${formatDate(date)}</td>
          <td>${actionBadge(e.action)}</td>
          <td class="font-bold">${escHtml(model)}</td>
          <td class="mono">${escHtml(String(version))}</td>
          <td style="font-size:11px;color:var(--text-2)">${escHtml(dName)}</td>
          <td style="font-size:11px;color:var(--text-2)">${escHtml(user)}</td>
        </tr>`;
    }).join('');

    return `
      <div class="card mt-4">
        <div class="card-header">
          <span class="card-title">Events</span>
          <span class="section-count">${events.length}</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th><th>Action</th><th>Model</th><th>Version</th>
                <th>Deployment name</th><th>User</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>`;
  }

  function downloadMarkdown(content, filename) {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function formatDate(raw) {
    if (!raw || raw === '—') return '—';
    try {
      const d = new Date(raw);
      if (isNaN(d)) return escHtml(String(raw));
      const pad = n => String(n).padStart(2, '0');
      return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}` +
        ` ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch { return escHtml(String(raw)); }
  }

  return { render };
})();
