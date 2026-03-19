// Project detail page with 4 tabs:
// Settings · Available Models · Public Registry · Deployed Models
const ProjectDetailPage = (() => {

  const ROLES = ['VIEWER', 'DEVELOPER', 'MAINTAINER', 'ADMIN'];

  // Tracks in-progress deploy polling timers
  const pollingTimers = {};

  function render(container, { name }) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="breadcrumb">
              <a href="#projects" data-nav="projects">Projects</a>
              <span class="breadcrumb-sep">/</span>
              <span class="breadcrumb-current">${escHtml(name)}</span>
            </div>
            <h1 class="page-title">${escHtml(name)}</h1>
          </div>
        </div>

        <div class="page-content">
          <div class="tabs" id="project-tabs">
            <button class="tab-btn active" data-tab="settings">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
              Settings
            </button>
            <button class="tab-btn" data-tab="models">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="9" height="9"/><rect x="13" y="2" width="9" height="9"/><rect x="13" y="13" width="9" height="9"/><rect x="2" y="13" width="9" height="9"/></svg>
              Available Models
            </button>
            <button class="tab-btn" data-tab="registry">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Public Registry
            </button>
            <button class="tab-btn" data-tab="deployed">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Deployed Models
            </button>
            <button class="tab-btn" data-tab="batch">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              Batch Predictions
            </button>
          </div>

          <div id="tab-settings" class="tab-panel active"></div>
          <div id="tab-models"   class="tab-panel"></div>
          <div id="tab-registry" class="tab-panel"></div>
          <div id="tab-deployed" class="tab-panel"></div>
          <div id="tab-batch"    class="tab-panel"></div>
        </div>
      </div>
    `;

    // Tab switching
    document.querySelectorAll('#project-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#project-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const panel = document.getElementById(`tab-${btn.dataset.tab}`);
        panel.classList.add('active');
        // Lazy load each tab on first activation
        if (!panel.dataset.loaded) {
          panel.dataset.loaded = 'true';
          loadTab(btn.dataset.tab, name, panel);
        }
      });
    });

    // Breadcrumb navigation
    document.querySelector('[data-nav="projects"]')?.addEventListener('click', e => {
      e.preventDefault();
      clearPolling();
      App.navigateTo('projects');
    });

    // Load first tab immediately
    const settingsPanel = document.getElementById('tab-settings');
    settingsPanel.dataset.loaded = 'true';
    loadTab('settings', name, settingsPanel);
  }

  function loadTab(tab, projectName, panel) {
    switch (tab) {
      case 'settings': loadSettings(projectName, panel); break;
      case 'models':   loadModels(projectName, panel);   break;
      case 'registry': loadRegistry(projectName, panel); break;
      case 'deployed': loadDeployed(projectName, panel); break;
      case 'batch':    loadBatch(projectName, panel);    break;
    }
  }

  // ── Settings Tab ─────────────────────────────────────────────

  async function loadSettings(projectName, panel) {
    panel.innerHTML = loadingHTML();
    try {
      const [info, users] = await Promise.all([
        API.projects.info(projectName),
        API.projects.getUsers(projectName),
      ]);
      renderSettings(projectName, info, users, panel);
    } catch (err) {
      panel.innerHTML = errorHTML(err.message);
    }
  }

  function renderSettings(projectName, info, users, panel) {
    const name      = info.name      || info.Name      || projectName;
    const owner     = info.owner     || info.Owner     || '—';
    const scope     = info.scope     || info.Scope     || '—';
    const perimeter = info.data_perimeter || info['Data Perimeter'] || '—';
    const batchEnabled = info.batch_enabled || false;

    panel.innerHTML = `
      <div class="card mb-4">
        <div class="card-header">
          <span class="card-title">Project Information</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Owner</th><th>Scope</th><th>Data Perimeter</th></tr></thead>
            <tbody>
              <tr>
                <td class="font-bold">${escHtml(name)}</td>
                <td>${escHtml(owner)}</td>
                <td><span class="badge badge-orange">${escHtml(scope)}</span></td>
                <td class="mono">${escHtml(perimeter)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header">
          <span class="card-title">Batch Predictions</span>
        </div>
        <div style="padding:16px 20px;display:flex;align-items:center;gap:12px">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
            <input type="checkbox" id="batch-toggle" ${batchEnabled ? 'checked' : ''} style="width:16px;height:16px;cursor:pointer">
            <span>Enable batch predictions for this project</span>
          </label>
          <span id="batch-status" class="badge ${batchEnabled ? 'badge-running' : 'badge-neutral'}">${batchEnabled ? 'Enabled' : 'Disabled'}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Users Access</span>
          <div class="flex gap-2">
            <button class="btn btn-secondary btn-sm" id="add-user-btn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Add User
            </button>
          </div>
        </div>
        <div id="add-user-form-area"></div>
        <div id="users-table-area"></div>
      </div>
    `;

    renderUsersTable(projectName, users, document.getElementById('users-table-area'));

    document.getElementById('batch-toggle').addEventListener('change', async (e) => {
      const enabled = e.target.checked;
      const statusEl = document.getElementById('batch-status');

      if (!enabled) {
        const ok = await Modal.confirm({
          title: 'Disable Batch Predictions',
          message: `This will <strong>permanently delete</strong> all batch prediction files stored for project <strong>${escHtml(projectName)}</strong>. This action cannot be undone.`,
          confirmLabel: 'Disable & Delete',
          danger: true,
        });
        if (!ok) {
          e.target.checked = true;
          return;
        }
      }

      try {
        await API.projects.updateBatchEnabled(projectName, enabled);
        statusEl.className = `badge ${enabled ? 'badge-running' : 'badge-neutral'}`;
        statusEl.textContent = enabled ? 'Enabled' : 'Disabled';
        Toast.success(`Batch predictions ${enabled ? 'enabled' : 'disabled'}.`);
      } catch (err) {
        e.target.checked = !enabled;
        Toast.error(err.message);
      }
    });

    document.getElementById('add-user-btn').addEventListener('click', () =>
      toggleAddUserForm(projectName)
    );
  }

  function renderUsersTable(projectName, users, area) {
    if (!users || users.length === 0) {
      area.innerHTML = `
        <div class="empty-state" style="padding:32px">
          <div class="empty-state-title">No users yet</div>
          <div class="empty-state-desc">Add team members to this project.</div>
        </div>`;
      return;
    }

    const rows = users.map(u => {
      const userName = u.name || u.Name || u.email || u.Email || '—';
      const email    = u.email || u.Email || '—';
      const role     = u.role  || u.Role  || '—';

      return `
        <tr>
          <td class="font-bold">${escHtml(userName)}</td>
          <td class="mono">${escHtml(email)}</td>
          <td>
            <select class="form-select" style="width:140px;padding:4px 28px 4px 8px;" data-user="${escHtml(email)}" data-original="${escHtml(role)}">
              ${ROLES.map(r => `<option value="${r}" ${r === role ? 'selected' : ''}>${r}</option>`).join('')}
            </select>
          </td>
          <td class="actions">
            <div class="flex gap-2 justify-end">
              <button class="btn btn-secondary btn-xs save-role-btn" data-user="${escHtml(email)}" data-project="${escHtml(projectName)}">Save role</button>
              <button class="btn btn-danger btn-xs remove-user-btn" data-user="${escHtml(email)}" data-project="${escHtml(projectName)}">Remove</button>
            </div>
          </td>
        </tr>`;
    }).join('');

    area.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th style="text-align:right">Actions</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;

    area.querySelectorAll('.save-role-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const email = btn.dataset.user;
        const select = area.querySelector(`select[data-user="${email}"]`);
        const role = select.value;
        try {
          await API.projects.changeUserRole(projectName, email, role);
          Toast.success(`Role updated for ${email}`);
          select.dataset.original = role;
        } catch (err) { Toast.error(err.message); }
      });
    });

    area.querySelectorAll('.remove-user-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const email = btn.dataset.user;
        const ok = await Modal.confirm({
          title: 'Remove User',
          message: `Remove <strong>${email}</strong> from this project?`,
          confirmLabel: 'Remove',
          danger: true,
        });
        if (ok) {
          try {
            await API.projects.removeUser(projectName, email);
            Toast.success(`${email} removed.`);
            loadSettings(projectName, document.getElementById('tab-settings'));
          } catch (err) { Toast.error(err.message); }
        }
      });
    });
  }

  async function toggleAddUserForm(projectName) {
    const area = document.getElementById('add-user-form-area');
    if (area.dataset.open === 'true') {
      area.innerHTML = '';
      area.dataset.open = 'false';
      return;
    }
    area.dataset.open = 'true';

    // Try to load the user list for autocomplete (admin only).
    // Always fall back to a plain text input so non-admins can still add users.
    let allUsers = [];
    try { allUsers = await API.users.getAll(); } catch {}

    const hasUserList = allUsers.length > 0;
    const emailField = hasUserList
      ? `<select class="form-select" id="add-user-email" style="flex:2">
           ${allUsers.map(u => { const e = u.email || u; return `<option value="${escHtml(e)}">${escHtml(e)}</option>`; }).join('')}
         </select>`
      : `<input class="form-input" id="add-user-email" type="email" placeholder="user@example.com" style="flex:2" autocomplete="off">`;

    area.innerHTML = `
      <div class="row-form" style="padding:10px 20px;border-bottom:1px solid var(--border-0)">
        ${emailField}
        <select class="form-select" id="add-user-role" style="flex:1">
          ${ROLES.map(r => `<option value="${r}">${r}</option>`).join('')}
        </select>
        <button class="btn btn-primary btn-sm" id="add-user-submit">Add</button>
        <button class="btn btn-secondary btn-sm" id="add-user-cancel">Cancel</button>
      </div>`;

    document.getElementById('add-user-cancel').addEventListener('click', () => {
      area.innerHTML = '';
      area.dataset.open = 'false';
    });

    document.getElementById('add-user-submit').addEventListener('click', async () => {
      const emailEl = document.getElementById('add-user-email');
      const email   = (emailEl.value || '').trim();
      const role    = document.getElementById('add-user-role').value;
      if (!email) { Toast.error('Please enter a user email.'); return; }
      try {
        await API.projects.addUser(projectName, email, role);
        Toast.success(`${email} added as ${role}.`);
        area.innerHTML = '';
        area.dataset.open = 'false';
        loadSettings(projectName, document.getElementById('tab-settings'));
      } catch (err) { Toast.error(err.message); }
    });
  }

  // ── Available Models Tab ─────────────────────────────────────

  async function loadModels(projectName, panel) {
    panel.innerHTML = loadingHTML();
    try {
      const [models, modelInfos] = await Promise.all([
        API.models.list(projectName),
        API.modelInfos.listForProject(projectName).catch(() => []),
      ]);
      if (!models || models.length === 0) {
        panel.innerHTML = emptyHTML('No models found', 'Register models in MLflow to see them here.');
        return;
      }

      // Build compliance lookup: "modelName:version" → { deterministic, llm }
      const complianceMap = {};
      for (const info of modelInfos) {
        complianceMap[`${info.model_name}:${info.model_version}`] = {
          deterministic: info.deterministic_compliance || 'not_evaluated',
          llm: info.llm_compliance || 'not_evaluated',
        };
      }

      // Fetch all versions for each model in parallel
      const modelsWithVersions = await Promise.all(
        models.map(async m => {
          try {
            const versions = await API.models.versions(projectName, m.name);
            return { ...m, all_versions: versions };
          } catch {
            return { ...m, all_versions: m.latest_versions || [] };
          }
        })
      );
      renderModels(projectName, modelsWithVersions, panel, complianceMap);
    } catch (err) {
      panel.innerHTML = errorHTML(err.message);
    }
  }

  function renderModels(projectName, models, panel, complianceMap) {
    const rows = models.map(m => modelRow(m, projectName, 'available', complianceMap)).join('');

    panel.innerHTML = `
      <div class="section-toolbar">
        <div class="section-toolbar-left">
          <span class="section-title">MLflow Registry</span>
          <span class="section-count">${models.length}</span>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model name</th>
              <th>Aliases</th>
              <th>Latest version</th>
              <th>Registered</th>
              <th>Version to deploy</th>
              <th>Compliance</th>
              <th style="text-align:right">Action</th>
            </tr>
          </thead>
          <tbody id="models-tbody">${rows}</tbody>
        </table>
      </div>
      <div id="deploy-status-area"></div>
    `;

    attachModelEvents(projectName, panel, 'available', complianceMap);
  }

  function complianceIcon(status, label) {
    const prefix = label ? `<span style="font-size:10px;color:var(--text-2);margin-right:4px">${escHtml(label)}</span>` : '';
    if (status === 'compliant') return `${prefix}<span class="badge badge-green" title="${escHtml(label || '')} — Conforme">Conforme</span>`;
    if (status === 'partially_compliant') return `${prefix}<span class="badge badge-orange" title="${escHtml(label || '')} — Partiellement conforme">Partiel</span>`;
    if (status === 'non_compliant') return `${prefix}<span class="badge badge-red" title="${escHtml(label || '')} — Non conforme">Non conforme</span>`;
    if (status === 'not_evaluated') return `${prefix}<span class="badge badge-neutral" title="${escHtml(label || '')} — Non évalué">Non évalué</span>`;
    return `${prefix}<span class="badge badge-neutral">—</span>`;
  }

  function modelRow(m, projectName, context, complianceMap) {
    const name = m.name || '—';

    // all_versions is populated by loadModels (fetched via API.models.versions)
    // each entry is an object with at least a `version` field (string number)
    const versionObjects = m.all_versions || m.latest_versions || [];
    const versionNumbers = versionObjects
      .map(v => (typeof v === 'object' ? v.version : v))
      .filter(Boolean)
      .sort((a, b) => Number(b) - Number(a));

    const latest = versionNumbers.length > 0 ? versionNumbers[0] : '—';

    const ts = m.creation_timestamp;
    const registered = ts ? new Date(ts).toLocaleDateString() : '—';

    const aliases = m.aliases && typeof m.aliases === 'object' ? Object.keys(m.aliases) : (Array.isArray(m.aliases) ? m.aliases : []);
    const aliasesDisplay = aliases.length > 0 ? aliases.join(', ') : '—';

    const versionOptions = versionNumbers.length > 0
      ? versionNumbers.map(v => `<option value="${escHtml(String(v))}">${escHtml(String(v))}</option>`).join('')
      : `<option value="">—</option>`;

    // Compliance badge for the first (latest) version
    const complianceData = JSON.stringify(complianceMap || {}).replace(/"/g, '&quot;');
    const firstVersion = versionNumbers.length > 0 ? versionNumbers[0] : '';
    const firstCompliance = (complianceMap || {})[`${name}:${firstVersion}`];
    const initialBadge = firstCompliance
      ? `${complianceIcon(firstCompliance.deterministic, 'Dét.')} ${complianceIcon(firstCompliance.llm, 'LLM')}`
      : `${complianceIcon('not_evaluated', 'Dét.')} ${complianceIcon('not_evaluated', 'LLM')}`;

    return `
      <tr>
        <td class="font-bold">${escHtml(name)}</td>
        <td style="font-size:12px;color:var(--text-2)">${escHtml(aliasesDisplay)}</td>
        <td class="mono">${escHtml(String(latest))}</td>
        <td>${escHtml(registered)}</td>
        <td>
          <select class="form-select version-select" style="width:90px;padding:4px 28px 4px 8px;" data-model="${escHtml(name)}">
            ${versionOptions}
          </select>
        </td>
        <td class="compliance-cell" data-model="${escHtml(name)}">${initialBadge}</td>
        <td class="actions">
          <button class="btn btn-primary btn-sm deploy-btn" data-model="${escHtml(name)}" data-project="${escHtml(projectName)}">
            Deploy
          </button>
        </td>
      </tr>
    `;
  }

  function attachModelEvents(projectName, panel, context, complianceMap) {
    // Update compliance badges when version changes
    panel.querySelectorAll('.version-select').forEach(sel => {
      sel.addEventListener('change', () => {
        const modelName = sel.dataset.model;
        const version = sel.value;
        const cell = panel.querySelector(`.compliance-cell[data-model="${modelName}"]`);
        if (!cell) return;
        const c = (complianceMap || {})[`${modelName}:${version}`];
        cell.innerHTML = c
          ? `${complianceIcon(c.deterministic, 'Dét.')} ${complianceIcon(c.llm, 'LLM')}`
          : `${complianceIcon('not_evaluated', 'Dét.')} ${complianceIcon('not_evaluated', 'LLM')}`;
      });
    });

    panel.querySelectorAll('.deploy-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const modelName = btn.dataset.model;
        const row = btn.closest('tr');
        const version = row.querySelector(`select[data-model="${modelName}"]`).value;

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner spinner-sm"></span>';

        try {
          const result = await API.models.deploy(projectName, modelName, version);
          const taskId = result.task_id || result.id || null;
          btn.innerHTML = 'Deploying…';

          if (taskId) {
            pollDeployStatus(projectName, taskId, modelName, version, btn);
          } else {
            Toast.success(`Deployment started for ${modelName} v${version}`);
            btn.innerHTML = 'Deploy';
            btn.disabled = false;
          }
        } catch (err) {
          Toast.error(`Deploy failed: ${err.message}`);
          btn.innerHTML = 'Deploy';
          btn.disabled = false;
        }
      });
    });
  }

  function pollDeployStatus(projectName, taskId, modelName, version, btn) {
    const timer = setInterval(async () => {
      try {
        const status = await API.models.taskStatus(projectName, taskId);
        const state  = (status.status || status.state || '').toLowerCase();

        if (state === 'completed' || state === 'success' || state === 'done') {
          clearInterval(timer);
          Toast.success(`${modelName} v${version} deployed successfully.`);
          btn.innerHTML = 'Deploy';
          btn.disabled = false;
        } else if (state === 'error' || state === 'failed') {
          clearInterval(timer);
          Toast.error(`Deployment of ${modelName} v${version} failed.`);
          btn.innerHTML = 'Deploy';
          btn.disabled = false;
        }
      } catch { clearInterval(timer); }
    }, 3000);

    pollingTimers[taskId] = timer;
  }

  // ── Public Registry (HuggingFace) Tab ───────────────────────

  function loadRegistry(projectName, panel) {
    panel.innerHTML = `
      <div class="section-toolbar">
        <div class="section-toolbar-left">
          <span class="section-title">HuggingFace Model Hub</span>
        </div>
      </div>
      <div class="search-wrap mb-4" style="max-width:480px">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input class="form-input" id="hf-search" placeholder="Search HuggingFace models…" autocomplete="off">
      </div>
      <div id="hf-results"></div>
    `;

    let debounce;
    document.getElementById('hf-search').addEventListener('input', e => {
      clearTimeout(debounce);
      const q = e.target.value.trim();
      if (!q) { document.getElementById('hf-results').innerHTML = ''; return; }
      debounce = setTimeout(() => searchHuggingFace(projectName, q), 500);
    });
  }

  async function searchHuggingFace(projectName, query) {
    const results = document.getElementById('hf-results');
    results.innerHTML = loadingHTML('Searching HuggingFace…');
    try {
      const models = await API.models.searchHuggingFace(query);
      if (!models || models.length === 0) {
        results.innerHTML = emptyHTML('No results', `No HuggingFace models found for "${query}".`);
        return;
      }

      const rows = models.map(m => {
        const id     = m.id     || m.modelId || '—';
        const author = m.author || id.split('/')[0] || '—';
        const task   = m.pipeline_tag || m.task || '—';
        const likes  = m.likes  != null ? m.likes : '—';

        return `
          <tr>
            <td class="font-bold mono" style="font-size:12px">${escHtml(id)}</td>
            <td>${escHtml(author)}</td>
            <td><span class="badge badge-neutral">${escHtml(task)}</span></td>
            <td class="mono">${likes}</td>
            <td class="actions">
              <button class="btn btn-secondary btn-sm import-hf-btn" data-model="${escHtml(id)}" data-project="${escHtml(projectName)}">
                Import
              </button>
            </td>
          </tr>`;
      }).join('');

      results.innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr><th>Model ID</th><th>Author</th><th>Task</th><th>Likes</th><th style="text-align:right">Action</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;

      results.querySelectorAll('.import-hf-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const modelId = btn.dataset.model;
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.models.getHuggingFaceModel(projectName, modelId);
            Toast.success(`Model "${modelId}" imported to project.`);
            btn.innerHTML = 'Imported';
          } catch (err) {
            Toast.error(err.message);
            btn.innerHTML = 'Import';
            btn.disabled = false;
          }
        });
      });
    } catch (err) {
      results.innerHTML = errorHTML(err.message);
    }
  }

  // ── Deployed Models Tab ──────────────────────────────────────

  async function loadDeployed(projectName, panel) {
    panel.innerHTML = loadingHTML();
    try {
      const models = await API.deployedModels.list(projectName);
      renderDeployed(projectName, models, panel);
    } catch (err) {
      panel.innerHTML = errorHTML(err.message);
    }
  }

  function renderDeployed(projectName, models, panel) {
    if (!models || models.length === 0) {
      panel.innerHTML = emptyHTML('No deployments', 'Deploy a model from the Available Models tab.');
      return;
    }

    const rows = models.map(m => {
      const name        = m.name             || m.model_name  || '—';
      const version     = m.version          || '—';
      const status      = m.status           || 'unknown';
      const deployName  = m.deployment_name  || m.name || '—';
      const dashUrl     = m.dashboard_url    || buildDashboardUrl(projectName, deployName);
      const deployDate  = m.deployment_date  ? new Date(m.deployment_date).toLocaleDateString() : '—';
      const endpointUrl = buildDashboardUrl(projectName, deployName);

      return `
        <tr>
          <td class="font-bold">${escHtml(name)}</td>
          <td class="mono">${escHtml(String(version))}</td>
          <td>${escHtml(deployDate)}</td>
          <td>${endpointUrl ? `<a href="${escHtml(endpointUrl)}" target="_blank" rel="noopener" style="color:var(--cyan);font-size:12px;font-family:var(--font-mono)">${escHtml(endpointUrl)}</a>` : '—'}</td>
          <td class="mono">${escHtml(deployName)}</td>
          <td>${statusBadge(status)}</td>
          <td class="actions">
            <div class="flex gap-2 justify-end">
              ${dashUrl ? `<a href="${escHtml(dashUrl)}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">Dashboard</a>` : ''}
              <button class="btn btn-danger btn-sm undeploy-btn" data-model="${escHtml(name)}" data-version="${escHtml(String(version))}">Undeploy</button>
            </div>
          </td>
        </tr>`;
    }).join('');

    panel.innerHTML = `
      <div class="section-toolbar">
        <div class="section-toolbar-left">
          <span class="section-title">Live Deployments</span>
          <span class="section-count">${models.length}</span>
        </div>
        <button class="btn btn-secondary btn-sm" id="refresh-deployed-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Refresh
        </button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Model</th><th>Version</th><th>Deployed on</th><th>Endpoint</th><th>Deployment name</th><th>Status</th><th style="text-align:right">Actions</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;

    document.getElementById('refresh-deployed-btn').addEventListener('click', () =>
      loadDeployed(projectName, panel)
    );

    panel.querySelectorAll('.undeploy-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const modelName = btn.dataset.model;
        const version   = btn.dataset.version;
        const ok = await Modal.confirm({
          title: 'Undeploy Model',
          message: `Undeploy <strong>${modelName}</strong> v${version}?`,
          confirmLabel: 'Undeploy',
          danger: true,
        });
        if (ok) {
          try {
            await API.models.undeploy(projectName, modelName, version);
            Toast.success(`${modelName} v${version} undeployed.`);
            loadDeployed(projectName, panel);
          } catch (err) { Toast.error(err.message); }
        }
      });
    });
  }

  // ── Batch Predictions Tab ────────────────────────────────────

  const batchPollingTimers = {};

  async function loadBatch(projectName, panel) {
    panel.innerHTML = loadingHTML();
    try {
      const info = await API.projects.info(projectName);
      const batchEnabled = info.batch_enabled || false;

      if (!batchEnabled) {
        panel.innerHTML = emptyHTML(
          'Batch Predictions Disabled',
          'Enable batch predictions in the Settings tab to use this feature.'
        );
        return;
      }

      const [models, jobs] = await Promise.all([
        API.models.list(projectName).catch(() => []),
        API.batch.list(projectName).catch(() => []),
      ]);

      // Fetch all versions for each model
      const modelsWithVersions = await Promise.all(
        (models || []).map(async m => {
          try {
            const versions = await API.models.versions(projectName, m.name);
            return { ...m, all_versions: versions };
          } catch {
            return { ...m, all_versions: m.latest_versions || [] };
          }
        })
      );
      renderBatch(projectName, modelsWithVersions, jobs, panel);
    } catch (err) {
      panel.innerHTML = errorHTML(err.message);
    }
  }

  function renderBatch(projectName, models, jobs, panel) {
    const modelOptions = (models || []).flatMap(m => {
      const name = m.name || '';
      const versionObjects = m.all_versions || m.latest_versions || [];
      const versionNumbers = versionObjects
        .map(v => (typeof v === 'object' ? v.version : v))
        .filter(Boolean)
        .sort((a, b) => Number(b) - Number(a));
      return versionNumbers.map(v =>
        `<option value="${escHtml(name)}:${escHtml(String(v))}">${escHtml(name)} v${escHtml(String(v))}</option>`
      );
    }).join('');

    const noModelsMsg = (!models || models.length === 0)
      ? '<p style="color:var(--text-2);font-size:13px">No models available. Register models in MLflow to submit batch predictions.</p>'
      : '';

    const rows = (jobs || []).map(j => batchJobRow(j, projectName)).join('');

    panel.innerHTML = `
      <div class="card mb-4">
        <div class="card-header">
          <span class="card-title">Submit Batch Prediction</span>
        </div>
        <div style="padding:16px 20px">
          ${noModelsMsg}
          ${models && models.length > 0 ? `
          <div class="row-form" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <select class="form-select" id="batch-model-select" style="flex:1;min-width:200px">
              ${modelOptions}
            </select>
            <label class="btn btn-secondary btn-sm" style="cursor:pointer">
              <input type="file" id="batch-file-input" accept=".csv" style="display:none">
              Choose CSV file
            </label>
            <span id="batch-file-name" style="font-size:12px;color:var(--text-2)">No file selected</span>
            <button class="btn btn-primary btn-sm" id="batch-submit-btn" disabled>Submit</button>
          </div>` : ''}
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Batch Jobs</span>
          <span class="section-count">${(jobs || []).length}</span>
          <button class="btn btn-secondary btn-sm" id="batch-cleanup-btn" style="margin-left:auto">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            Cleanup
          </button>
          <button class="btn btn-secondary btn-sm" id="batch-refresh-btn">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Refresh
          </button>
        </div>
        <div id="batch-jobs-area">
          ${rows ? `
          <div class="table-wrap">
            <table>
              <thead><tr><th>Job ID</th><th>Model</th><th>Version</th><th>Status</th><th>Created</th><th style="text-align:right">Actions</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>` : emptyHTML('No batch jobs', 'Submit a batch prediction to get started.')}
        </div>
      </div>
    `;

    // File input handling
    const fileInput = document.getElementById('batch-file-input');
    const submitBtn = document.getElementById('batch-submit-btn');
    if (fileInput) {
      fileInput.addEventListener('change', () => {
        const fileName = fileInput.files[0]?.name || 'No file selected';
        document.getElementById('batch-file-name').textContent = fileName;
        submitBtn.disabled = !fileInput.files[0];
      });
    }

    // Submit handling
    if (submitBtn) {
      submitBtn.addEventListener('click', async () => {
        const select = document.getElementById('batch-model-select');
        const [modelName, version] = select.value.split(':');
        const file = fileInput.files[0];
        if (!file) return;

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner spinner-sm"></span>';
        try {
          const result = await API.batch.submit(projectName, modelName, version, file);
          Toast.success(`Batch job submitted: ${result.job_id}`);
          loadBatch(projectName, panel);
        } catch (err) {
          Toast.error(`Submit failed: ${err.message}`);
          submitBtn.innerHTML = 'Submit';
          submitBtn.disabled = false;
        }
      });
    }

    // Refresh
    document.getElementById('batch-refresh-btn')?.addEventListener('click', () =>
      loadBatch(projectName, panel)
    );

    // Cleanup finished/failed jobs
    document.getElementById('batch-cleanup-btn')?.addEventListener('click', async () => {
      const ok = await Modal.confirm({
        title: 'Cleanup Batch Jobs',
        message: 'Delete all completed and failed batch jobs and their associated files?',
        confirmLabel: 'Cleanup',
        danger: true,
      });
      if (ok) {
        try {
          const result = await API.batch.cleanup(projectName);
          Toast.success(`Cleaned up ${result.deleted} batch job(s).`);
          loadBatch(projectName, panel);
        } catch (err) { Toast.error(err.message); }
      }
    });

    // Delete buttons
    panel.querySelectorAll('.batch-delete-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const jobId = btn.dataset.jobId;
        const ok = await Modal.confirm({
          title: 'Delete Batch Job',
          message: `Delete batch job <strong>${escHtml(jobId)}</strong> and all associated files?`,
          confirmLabel: 'Delete',
          danger: true,
        });
        if (ok) {
          try {
            await API.batch.delete(projectName, jobId);
            Toast.success('Batch job deleted.');
            loadBatch(projectName, panel);
          } catch (err) { Toast.error(err.message); }
        }
      });
    });

    // Error detail buttons
    panel.querySelectorAll('.batch-error-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        Modal.confirm({
          title: 'Batch Job Error',
          message: `<pre style="white-space:pre-wrap;font-size:12px;max-height:300px;overflow:auto">${escHtml(btn.dataset.error)}</pre>`,
          confirmLabel: 'OK',
        });
      });
    });

    // Download buttons
    panel.querySelectorAll('.batch-download-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const jobId = btn.dataset.jobId;
        try {
          const blob = await API.batch.download(projectName, jobId);
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `predictions-${jobId}.csv`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } catch (err) { Toast.error(err.message); }
      });
    });

    // Poll for building/pending/running jobs
    (jobs || []).forEach(j => {
      const s = (j.status || '').toLowerCase();
      if (s === 'building' || s === 'pending' || s === 'running') {
        pollBatchStatus(projectName, j.job_id, panel);
      }
    });
  }

  function batchJobRow(j, projectName) {
    const jobId = j.job_id || '—';
    const model = j.model_name || '—';
    const version = j.model_version || '—';
    const status = j.status || 'unknown';
    const created = j.created_at ? new Date(j.created_at).toLocaleString() : '—';
    const isCompleted = status.toLowerCase() === 'completed';
    const isFailed = status.toLowerCase() === 'failed';
    const errorMsg = j.error_message || '';

    return `
      <tr data-job-id="${escHtml(jobId)}">
        <td class="mono" style="font-size:12px">${escHtml(jobId)}</td>
        <td class="font-bold">${escHtml(model)}</td>
        <td class="mono">${escHtml(String(version))}</td>
        <td>
          ${statusBadge(status)}
          ${isFailed && errorMsg ? `<button class="btn btn-secondary btn-xs batch-error-btn" data-error="${escHtml(errorMsg)}" style="margin-left:4px" title="View error">?</button>` : ''}
        </td>
        <td>${escHtml(created)}</td>
        <td class="actions">
          <div class="flex gap-2 justify-end">
            ${isCompleted ? `<button class="btn btn-secondary btn-sm batch-download-btn" data-job-id="${escHtml(jobId)}">Download</button>` : ''}
            <button class="btn btn-danger btn-xs batch-delete-btn" data-job-id="${escHtml(jobId)}">Delete</button>
          </div>
        </td>
      </tr>`;
  }

  function pollBatchStatus(projectName, jobId, panel) {
    if (batchPollingTimers[jobId]) return;
    const timer = setInterval(async () => {
      try {
        const result = await API.batch.status(projectName, jobId);
        const state = (result.status || '').toLowerCase();
        if (state === 'completed' || state === 'failed') {
          clearInterval(timer);
          delete batchPollingTimers[jobId];
          loadBatch(projectName, panel);
          if (state === 'completed') {
            Toast.success(`Batch job ${jobId} completed.`);
          } else {
            Toast.error(`Batch job ${jobId} failed.`);
          }
        }
      } catch {
        clearInterval(timer);
        delete batchPollingTimers[jobId];
      }
    }, 3000);
    batchPollingTimers[jobId] = timer;
  }

  // ── Helpers ──────────────────────────────────────────────────

  function statusBadge(status) {
    const s = String(status).toLowerCase();
    let cls = 'badge-neutral';
    if (s.includes('run') || s.includes('serv'))       cls = 'badge-running';
    else if (s.includes('pend') || s.includes('build')) cls = 'badge-pending';
    else if (s.includes('err') || s.includes('fail'))  cls = 'badge-error';
    else if (s === 'deployed')                          cls = 'badge-deployed';
    return `<span class="badge ${cls}">${escHtml(status)}</span>`;
  }

  function buildDashboardUrl(projectName, deployName) {
    const host = window.MP_HOST_NAME || '';
    if (!host || !deployName || deployName === '—') return '';
    return `http://${host}/deploy/${projectName}/${deployName}`;
  }

  function loadingHTML(text = 'Loading…') {
    return `<div class="loading-screen"><span class="spinner"></span><span>${text}</span></div>`;
  }

  function errorHTML(msg) {
    return `<div class="empty-state"><div class="empty-state-title" style="color:var(--red-light)">Error</div><div class="empty-state-desc">${escHtml(msg)}</div></div>`;
  }

  function emptyHTML(title, desc) {
    return `<div class="empty-state"><div class="empty-state-title">${title}</div><div class="empty-state-desc">${desc}</div></div>`;
  }

  function clearPolling() {
    Object.values(pollingTimers).forEach(clearInterval);
    Object.values(batchPollingTimers).forEach(clearInterval);
  }

  return { render };
})();
