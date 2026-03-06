// Governance page — model audit trail, version history, deployment events
const GovernancePage = (() => {

  let aiAvailable = false;
  let aiCache = {}; // key: "modelName:version" → { hasSuggestion, actReview }

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

    // Check AI availability once per page render
    API.ai.status().then(s => { aiAvailable = s.available; });

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
      const [data, list] = await Promise.all([
        API.projects.governance(projectName),
        API.modelInfos.listForProject(projectName).catch(() => []),
      ]);

      aiCache = {};
      for (const item of list) {
        aiCache[`${item.model_name}:${item.model_version}`] = {
          hasSuggestion: item.has_generated_model_card,
          actReview: item.act_review,
        };
      }

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
    const entries = data.project_governance || data.project_gouvernance || (Array.isArray(data) ? data : []);

    const versions = entries.flatMap(e => {
      const info = e.model_information || e;
      return info ? [info] : [];
    });
    const deploymentEvents = entries.flatMap(e => e.events || []);

    const modelGroups = {};
    versions.forEach(v => {
      const modelName = v.model_name || v.name || 'Unknown';
      if (!modelGroups[modelName]) modelGroups[modelName] = [];
      modelGroups[modelName].push(v);
    });

    const modelSections = Object.entries(modelGroups)
      .map(([modelName, versionList]) => renderModelSection(modelName, versionList, projectName, aiCache))
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

    // Delegate clicks on AI Act buttons
    content.addEventListener('click', async e => {
      const aiActBtn = e.target.closest('.ai-act-btn');
      if (aiActBtn) {
        openAiActModal(aiActBtn.dataset.project, aiActBtn.dataset.model, aiActBtn.dataset.version, false);
        return;
      }

      const directReviewBtn = e.target.closest('.ai-direct-review-btn');
      if (directReviewBtn) {
        openDirectReviewModal(directReviewBtn.dataset.project, directReviewBtn.dataset.model, directReviewBtn.dataset.version);
        return;
      }

      const suggestBtn = e.target.closest('.ai-suggest-btn');
      if (suggestBtn) {
        openModelCardSuggestModal(suggestBtn.dataset.project, suggestBtn.dataset.model, suggestBtn.dataset.version);
      }
    });
  }

  // ── AI Act Modal ──────────────────────────────────────────────

  async function openAiActModal(projectName, modelName, version) {
    const key = `${modelName}:${version}`;
    const cached = aiCache[key];
    const reviewBtnLabel = cached && cached.actReview ? 'Ré-analyser' : 'Analyser avec Claude';

    const aiReviewBtnHtml = aiAvailable ? `
      <button class="btn btn-ai btn-sm" id="ai-act-review-btn">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        ${reviewBtnLabel}
      </button>` : '';

    const { close } = Modal.open({
      title: `Fiche IA Act — ${modelName} v${version}`,
      body: `<div class="ai-act-loading"><span class="spinner"></span><span>Génération de la fiche…</span></div>`,
      footer: `
        ${aiReviewBtnHtml}
        <button class="btn btn-secondary" id="ai-act-download" disabled>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          Télécharger .md
        </button>`,
    });

    let markdownContent = '';
    try {
      const data = await API.modelInfos.aiActCard(projectName, modelName, version);
      markdownContent = data.markdown || '';
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = `<div class="ai-act-md">${renderMarkdown(markdownContent)}</div>`;

      // Inject cached review immediately if available
      if (cached && cached.actReview && bodyEl) {
        const reviewSection = document.createElement('div');
        reviewSection.className = 'ai-review-section';
        reviewSection.innerHTML = `
          <div class="ai-review-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            Analyse de conformité IA Act par Claude
          </div>
          <div class="ai-review-body ai-act-md">${renderMarkdown(cached.actReview)}</div>
        `;
        bodyEl.appendChild(reviewSection);
      }

      const dlBtn = document.getElementById('ai-act-download');
      if (dlBtn) {
        dlBtn.disabled = false;
        dlBtn.addEventListener('click', () => downloadMarkdown(markdownContent, `ia-act-${projectName}-${modelName}-v${version}.md`));
      }

      const reviewBtn = document.getElementById('ai-act-review-btn');
      if (reviewBtn) {
        reviewBtn.addEventListener('click', () => runAiActReview(projectName, modelName, version, markdownContent));
      }

    } catch (err) {
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = `<p style="color:var(--red-light)">Erreur : ${escHtml(err.message)}</p>`;
    }
  }

  async function runAiActReview(projectName, modelName, version, originalMarkdown) {
    const key = `${modelName}:${version}`;
    const reviewBtn = document.getElementById('ai-act-review-btn');
    if (reviewBtn) {
      reviewBtn.disabled = true;
      reviewBtn.innerHTML = '<span class="spinner spinner-sm"></span> Analyse en cours…';
    }

    try {
      const data = await API.ai.actReview(projectName, modelName, version);
      const review = data.review || '';

      // Update local cache
      aiCache[key] = aiCache[key] || { hasSuggestion: false, actReview: null };
      aiCache[key].actReview = review;

      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) {
        const reviewHtml = `
          <div class="ai-review-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            Analyse de conformité IA Act par Claude
          </div>
          <div class="ai-review-body ai-act-md">${renderMarkdown(review)}</div>
        `;
        const existingSection = bodyEl.querySelector('.ai-review-section');
        if (existingSection) {
          existingSection.innerHTML = reviewHtml;
          existingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          const reviewSection = document.createElement('div');
          reviewSection.className = 'ai-review-section';
          reviewSection.innerHTML = reviewHtml;
          bodyEl.appendChild(reviewSection);
          reviewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    } catch (err) {
      Toast.error(`Erreur d'analyse : ${escHtml(err.message)}`);
    } finally {
      if (reviewBtn) {
        reviewBtn.disabled = false;
        reviewBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg> Ré-analyser`;
      }
    }
  }

  // ── Direct Review Modal (row button) ─────────────────────────

  async function openDirectReviewModal(projectName, modelName, version) {
    const key = `${modelName}:${version}`;
    const cached = aiCache[key];

    const aiIconSvg = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;
    const rerunIconSvg = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`;

    const badge = `<div class="ai-output-badge">${aiIconSvg} Analyse de conformité IA Act par Claude</div>`;
    const loadingHtml = `${badge}<div class="ai-act-loading"><span class="spinner"></span><span>Analyse en cours…</span></div>`;
    const reviewHtml = (text) => `${badge}<div class="ai-act-md">${renderMarkdown(text)}</div>`;

    const { close } = Modal.open({
      title: `Conformité IA Act — ${modelName} v${version}`,
      body: cached && cached.actReview ? reviewHtml(cached.actReview) : loadingHtml,
      footer: `
        <button class="btn btn-ai btn-sm" id="direct-review-rerun-btn" ${cached && cached.actReview ? '' : 'disabled'}>
          ${rerunIconSvg} Ré-analyser
        </button>`,
    });

    const rerunBtn = () => document.getElementById('direct-review-rerun-btn');

    const runReview = async () => {
      const btn = rerunBtn();
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner spinner-sm"></span> Analyse en cours…'; }
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = loadingHtml;

      try {
        const data = await API.ai.actReview(projectName, modelName, version);
        const review = data.review || '';
        aiCache[key] = aiCache[key] || { hasSuggestion: false, actReview: null };
        aiCache[key].actReview = review;
        if (bodyEl) bodyEl.innerHTML = reviewHtml(review);
      } catch (err) {
        if (bodyEl) bodyEl.innerHTML = `${badge}<p style="color:var(--red-light)">Erreur : ${escHtml(err.message)}</p>`;
        Toast.error(`Erreur d'analyse : ${escHtml(err.message)}`);
      } finally {
        const btn = rerunBtn();
        if (btn) { btn.disabled = false; btn.innerHTML = `${rerunIconSvg} Ré-analyser`; }
      }
    };

    const btn = rerunBtn();
    if (btn) btn.addEventListener('click', runReview);

    if (!(cached && cached.actReview)) runReview();
  }

  // ── Model Card Suggest Modal ──────────────────────────────────

  async function openModelCardSuggestModal(projectName, modelName, version) {
    const key = `${modelName}:${version}`;
    const { close } = Modal.open({
      title: `✨ Générer model card — ${modelName} v${version}`,
      body: `<div class="ai-act-loading"><span class="spinner"></span><span>Claude génère une suggestion…</span></div>`,
      footer: `
        <button class="btn btn-ai btn-sm" id="ai-card-apply" disabled>Appliquer</button>
        <button class="btn btn-secondary btn-sm" id="ai-card-cancel">Annuler</button>`,
    });

    document.getElementById('ai-card-cancel').addEventListener('click', () => close());

    let suggestion = '';
    try {
      const data = await API.ai.modelCardSuggest(projectName, modelName, version);
      suggestion = data.suggestion || '';

      // Update cache: backend already persisted the suggestion
      aiCache[key] = aiCache[key] || { hasSuggestion: false, actReview: null };
      aiCache[key].hasSuggestion = true;

      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) {
        bodyEl.innerHTML = `
          <div style="margin-bottom:10px;font-size:12px;color:var(--text-2)">
            Suggestion générée par Claude. Vous pouvez modifier le texte avant d'appliquer.
          </div>
          <textarea class="form-input ai-suggest-textarea" id="ai-card-textarea" rows="12">${escHtml(suggestion)}</textarea>
        `;
      }

      const applyBtn = document.getElementById('ai-card-apply');
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.addEventListener('click', async () => {
          const text = document.getElementById('ai-card-textarea').value;
          if (!text.trim()) { Toast.error('Le texte ne peut pas être vide.'); return; }
          applyBtn.disabled = true;
          applyBtn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.ai.updateModelCard(projectName, modelName, version, text);
            Toast.success('Model card mise à jour.');
            close();
          } catch (err) {
            Toast.error(`Erreur : ${escHtml(err.message)}`);
            applyBtn.disabled = false;
            applyBtn.innerHTML = 'Appliquer';
          }
        });
      }
    } catch (err) {
      const bodyEl = document.querySelector('#modal-container .modal-body');
      if (bodyEl) bodyEl.innerHTML = `<p style="color:var(--red-light)">Erreur : ${escHtml(err.message)}</p>`;
      const applyBtn = document.getElementById('ai-card-apply');
      if (applyBtn) applyBtn.disabled = true;
    }
  }

  // ── Markdown renderer ─────────────────────────────────────────

  function renderMarkdown(md) {
    if (typeof marked === 'undefined') return `<pre style="white-space:pre-wrap">${escHtml(md)}</pre>`;
    // Claude wraps bold/italic phrases in newlines (\n**phrase**\n or \n\n**phrase**\n\n),
    // turning them into orphan blocks. Collapse any short bold/italic phrase surrounded
    // by newlines back to inline — limit to 80 chars to avoid collapsing real headings.
    md = md.replace(/\n+(\*{1,2}[^*\n\r]{1,80}\*{1,2})\n+/g, ' $1 ');
    return wrapStatusSections(marked.parse(md, { breaks: false, gfm: true }));
  }

  function wrapStatusSections(html) {
    // Split on every <h3> opening tag; lookahead keeps the tag in the next part
    const parts = html.split(/(?=<h3>)/);
    if (parts.length <= 1) return html;
    return parts.map((part, i) => {
      if (i === 0) return part;
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

  // ── Render helpers ────────────────────────────────────────────

  function renderModelSection(modelName, versions, projectName, cache) {
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
        ${renderVersionsSection(versions, modelName, projectName, cache)}
      </div>`;
  }

  function renderVersionsSection(versions, modelName, projectName, cache) {
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

      const safeProj  = escHtml(projectName || '');
      const safeModel = escHtml(modelName || '');
      const safeVer   = escHtml(String(ver));

      const cacheKey = `${modelName}:${ver}`;
      const cached = (cache || {})[cacheKey];
      const suggestLabel = cached && cached.hasSuggestion ? '✨ Régénérer' : '✨ Model Card';

      const suggestBtn = aiAvailable ? `
        <button class="btn btn-ai btn-xs ai-suggest-btn"
          data-project="${safeProj}"
          data-model="${safeModel}"
          data-version="${safeVer}"
          title="Générer une model card avec Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
          ${suggestLabel}
        </button>` : '';

      const reviewLabel = cached && cached.actReview ? 'Ré-analyser' : 'Analyser';
      const directReviewBtn = aiAvailable ? `
        <button class="btn btn-ai btn-xs ai-direct-review-btn"
          data-project="${safeProj}"
          data-model="${safeModel}"
          data-version="${safeVer}"
          title="Analyse de conformité IA Act par Claude">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          ${reviewLabel}
        </button>` : '';

      return `
        <tr>
          <td class="mono">${safeVer}</td>
          <td>${escHtml(runName)}</td>
          <td>${escHtml(user)}</td>
          <td style="white-space:nowrap">${escHtml(created)}</td>
          <td style="max-width:180px;color:var(--text-1);font-size:11px">${escHtml(metrics)}</td>
          <td>
            <div class="flex gap-2 items-center" style="flex-wrap:nowrap">
              ${suggestBtn}
              <button class="btn btn-secondary btn-xs ai-act-btn"
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
                Fiche IA Act
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
              <th>Version</th><th>Run Name</th><th>User</th><th>Created</th><th>Metrics</th><th></th>
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
      return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
        ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    } catch { return escHtml(String(raw)); }
  }

  return { render };
})();
