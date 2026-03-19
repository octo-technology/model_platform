// Demo Simulation page — Load test deployed models and simulate DS model deployments
const DemoPage = (() => {

  let pollInterval = null;
  const POLL_INTERVAL = 15000; // 15 seconds

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Testing</div>
            <h1 class="page-title">Demo Simulation</h1>
            <p class="page-subtitle">Load test deployed models and simulate Data Scientist model deployments</p>
          </div>
        </div>

        <div class="page-content">
          <div class="demo-section">
            <div class="demo-section-title">Start New Simulation</div>

            <form class="demo-inline-form" id="demo-form">
              <div class="demo-inline-field">
                <label class="demo-inline-label">Project</label>
                <select class="demo-inline-input" id="project-name-input">
                  <option value="" disabled selected>Loading…</option>
                </select>
              </div>
              <div class="demo-inline-field">
                <label class="demo-inline-label">Model</label>
                <select class="demo-inline-input" id="model-name-input" disabled>
                  <option value="" disabled selected>Select project</option>
                </select>
              </div>
              <div class="demo-inline-field demo-inline-field--narrow">
                <label class="demo-inline-label">Duration (m)</label>
                <input class="demo-inline-input" id="duration-input" type="number" min="1" max="30" value="2" autocomplete="off">
              </div>
              <div class="demo-inline-field demo-inline-field--narrow">
                <label class="demo-inline-label">Users</label>
                <input class="demo-inline-input" id="users-input" type="number" min="1" value="5" autocomplete="off">
              </div>
              <div class="demo-inline-field demo-inline-field--narrow">
                <label class="demo-inline-label">Success rate (%)</label>
                <input class="demo-inline-input" id="success-rate-input" type="number" min="0" max="100" value="100" autocomplete="off">
              </div>
              <button type="submit" class="btn btn-primary btn-sm" id="submit-btn">
                <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Start
              </button>
            </form>
          </div>

          <div class="demo-section">
            <div class="demo-section-title">Active Simulations</div>
            <div id="active-simulations" class="demo-simulations-list">
              <div class="loading-screen"><span class="spinner"></span><span>Loading simulations…</span></div>
            </div>
          </div>

          <div class="demo-section">
            <div class="demo-section-title">Data Scientist Simulation</div>
            <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">Simulate a data scientist training and registering model versions in the project MLflow registry.</p>

            <form class="demo-inline-form" id="ds-demo-form">
              <div class="demo-inline-field">
                <label class="demo-inline-label">Project</label>
                <select class="demo-inline-input" id="ds-project-name-input">
                  <option value="" disabled selected>Loading…</option>
                </select>
              </div>
              <div class="demo-inline-field">
                <label class="demo-inline-label">Model name</label>
                <input class="demo-inline-input" id="ds-model-name-input" type="text" placeholder="credit-default-predictor" value="credit-default-predictor" autocomplete="off">
              </div>
              <div class="demo-inline-field demo-inline-field--narrow">
                <label class="demo-inline-label">Versions</label>
                <input class="demo-inline-input" id="ds-num-versions-input" type="number" min="1" max="20" value="3" autocomplete="off">
              </div>
              <div class="demo-inline-field demo-inline-field--narrow">
                <label class="demo-inline-label">Interval (s)</label>
                <input class="demo-inline-input" id="ds-interval-input" type="number" min="10" value="60" autocomplete="off">
              </div>
              <button type="submit" class="btn btn-primary btn-sm" id="ds-submit-btn">
                <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                Start DS
              </button>
            </form>
          </div>

          <div class="demo-section">
            <div class="demo-section-title">Active DS Simulations</div>
            <div id="active-ds-simulations" class="demo-simulations-list">
              <div class="loading-screen"><span class="spinner"></span><span>Loading simulations…</span></div>
            </div>
          </div>
        </div>
      </div>
    `;

    attachEvents();
    startPolling();
    loadProjects();
    refreshSimulations();
    refreshDsSimulations();
  }

  function attachEvents() {
    const form = document.getElementById('demo-form');
    form.addEventListener('submit', handleFormSubmit);
    const dsForm = document.getElementById('ds-demo-form');
    dsForm.addEventListener('submit', handleDsFormSubmit);
    document.getElementById('project-name-input').addEventListener('change', (e) => {
      loadModelsForProject(e.target.value);
    });
  }

  async function loadProjects() {
    try {
      const projects = await API.projects.list();
      const names = (projects || []).map(p => p.name || p.Name || '').filter(Boolean).sort();
      const options = names.map(n => `<option value="${escHtml(n)}">${escHtml(n)}</option>`).join('');
      const fallback = '<option value="" disabled>No projects found</option>';
      const html = names.length ? options : fallback;
      const selUser = document.getElementById('project-name-input');
      const selDs   = document.getElementById('ds-project-name-input');
      if (selUser) { selUser.innerHTML = html; if (names.length) { selUser.value = names[0]; loadModelsForProject(names[0]); } }
      if (selDs)   { selDs.innerHTML   = html; if (names.length) selDs.value   = names[0]; }
    } catch (err) {
      console.error('[Demo] Failed to load projects:', err);
    }
  }

  async function loadModelsForProject(projectName) {
    const sel = document.getElementById('model-name-input');
    if (!sel) return;
    sel.innerHTML = '<option value="" disabled selected>Loading…</option>';
    sel.disabled = true;
    try {
      const models = await API.deployedModels.list(projectName);
      const deployed = (models || []).filter(m => m.name || m.model_name);
      if (deployed.length) {
        sel.innerHTML = deployed.map(m => {
          const name = m.name || m.model_name;
          const ver  = m.version || '';
          const label = ver ? `${name} (v${ver})` : name;
          return `<option value="${escHtml(name)}::${escHtml(String(ver))}">${escHtml(label)}</option>`;
        }).join('');
        sel.disabled = false;
      } else {
        sel.innerHTML = '<option value="" disabled selected>No deployed models</option>';
      }
    } catch (err) {
      sel.innerHTML = '<option value="" disabled selected>Error loading models</option>';
      console.error('[Demo] Failed to load models:', err);
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();

    const projectName = document.getElementById('project-name-input').value.trim();
    const [modelName, modelVersion] = (document.getElementById('model-name-input').value || '').split('::');
    const duration = parseInt(document.getElementById('duration-input').value);
    const numUsers = parseInt(document.getElementById('users-input').value);
    const successRate = parseInt(document.getElementById('success-rate-input').value);

    // Validation
    if (!projectName || !modelName) {
      Toast.error('Please select a project and a model');
      return;
    }

    if (duration < 1 || duration > 10) {
      Toast.error('Duration must be between 1 and 10 minutes');
      return;
    }

    if (numUsers < 1) {
      Toast.error('Must have at least 1 user');
      return;
    }

    if (isNaN(successRate) || successRate < 0 || successRate > 100) {
      Toast.error('Success rate must be between 0 and 100');
      return;
    }

    const submitBtn = document.getElementById('submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-small"></span>Starting…';

    try {
      await API.demo.start({
        project_name: projectName,
        model_name: modelName,
        model_version: modelVersion,
        duration_minutes: duration,
        num_users: numUsers,
        success_rate: successRate,
      });

      Toast.success('Simulation started successfully');
      document.getElementById('demo-form').reset();
      refreshSimulations();
    } catch (err) {
      Toast.error(`Failed to start simulation: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  }

  async function handleDsFormSubmit(e) {
    e.preventDefault();

    const projectName = document.getElementById('ds-project-name-input').value.trim();
    const modelName = document.getElementById('ds-model-name-input').value.trim();
    const numVersions = parseInt(document.getElementById('ds-num-versions-input').value);
    const intervalSeconds = parseInt(document.getElementById('ds-interval-input').value);

    if (!projectName || !modelName) {
      Toast.error('Please fill in project name and model name');
      return;
    }
    if (numVersions < 1 || numVersions > 20) {
      Toast.error('Number of versions must be between 1 and 20');
      return;
    }
    if (intervalSeconds < 10) {
      Toast.error('Interval must be at least 10 seconds');
      return;
    }

    const submitBtn = document.getElementById('ds-submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-small"></span>Starting…';

    try {
      await API.demo.ds.start({
        project_name: projectName,
        model_name: modelName,
        num_versions: numVersions,
        interval_seconds: intervalSeconds,
      });

      Toast.success('DS simulation started');
      document.getElementById('ds-demo-form').reset();
      refreshDsSimulations();
    } catch (err) {
      Toast.error(`Failed to start DS simulation: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  }

  function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(() => {
      refreshSimulations();
      refreshDsSimulations();
    }, POLL_INTERVAL);
  }

  async function refreshSimulations() {
    const container = document.getElementById('active-simulations');
    if (!container) return;

    try {
      const response = await API.demo.list();
      console.log('[Demo] Full API response:', response);

      const simulations = response.simulations || [];

      console.log(`[Demo] Refreshing: ${simulations.length} simulations total`);
      console.log('[Demo] Simulations raw:', simulations);
      console.log('[Demo] Is array?', Array.isArray(simulations));

      // Separate running and stopped simulations
      const running = simulations.filter(s => s.is_running);
      const stopped = simulations.filter(s => !s.is_running);

      console.log(`[Demo] Running: ${running.length}, Stopped: ${stopped.length}`);

      if (running.length === 0 && stopped.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="empty-state-title">No simulations</div>
            <div class="empty-state-desc">Start a new simulation above to load test a deployed model</div>
          </div>
        `;
        return;
      }

      let html = '';

      // Running simulations section
      if (running.length > 0) {
        html += '<div class="demo-status-section"><div class="demo-status-section-title">🟢 Running</div>';
        html += running.map(sim => renderSimulationCard(sim)).join('');
        html += '</div>';
      }

      // Stopped simulations section
      if (stopped.length > 0) {
        html += '<div class="demo-status-section"><div class="demo-status-section-title">⚫ Terminated</div>';
        html += stopped.map(sim => renderSimulationCard(sim)).join('');
        html += '</div>';
      }

      container.innerHTML = html;
    } catch (err) {
      console.error('[Demo] Error refreshing:', err);
      console.error('[Demo] Error stack:', err.stack);
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--red-light)">Error loading simulations</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>
      `;
    }
  }

  async function refreshDsSimulations() {
    const container = document.getElementById('active-ds-simulations');
    if (!container) return;

    try {
      const response = await API.demo.ds.list();
      const simulations = response.simulations || [];

      const running = simulations.filter(s => s.is_running);
      const stopped = simulations.filter(s => !s.is_running);

      if (running.length === 0 && stopped.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <div class="empty-state-title">No DS simulations</div>
            <div class="empty-state-desc">Start a DS simulation above to push model versions to MLflow</div>
          </div>
        `;
        return;
      }

      let html = '';
      if (running.length > 0) {
        html += '<div class="demo-status-section"><div class="demo-status-section-title">🟢 Running</div>';
        html += running.map(sim => renderDsSimulationCard(sim)).join('');
        html += '</div>';
      }
      if (stopped.length > 0) {
        html += '<div class="demo-status-section"><div class="demo-status-section-title">⚫ Terminated</div>';
        html += stopped.map(sim => renderDsSimulationCard(sim)).join('');
        html += '</div>';
      }
      container.innerHTML = html;
    } catch (err) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--red-light)">Error loading DS simulations</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>
      `;
    }
  }

  function renderDsSimulationCard(sim) {
    const running = sim.is_running;
    const simIdShort = sim.simulation_id ? sim.simulation_id.substring(0, 8) : 'unknown';
    const timeAgo = sim.last_run_time ? getTimeAgo(sim.last_run_time * 1000) : 'Never';
    const successRate = sim.total_runs > 0
      ? ((sim.successful_runs / sim.total_runs) * 100).toFixed(1)
      : '0.0';
    const failedStyle = sim.failed_runs > 0 ? 'color:var(--red-light)' : '';

    return `
      <div class="demo-row">
        <div class="demo-row-dot ${running ? 'running' : 'stopped'}" title="${running ? 'Running' : 'Stopped'}"></div>
        <span class="demo-row-name">${escHtml(sim.model_name)}</span>
        <span class="demo-row-project">${escHtml(sim.project_name)}</span>
        <span class="demo-row-simid" title="${escHtml(sim.simulation_id)}">#${simIdShort}</span>
        <div class="demo-row-divider"></div>
        <div class="demo-row-stats">
          <div class="demo-row-stat"><span class="demo-row-stat-label">Versions</span><span class="demo-row-stat-value">${sim.num_versions}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Interval</span><span class="demo-row-stat-value">${sim.interval_seconds}s</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Runs</span><span class="demo-row-stat-value">${sim.total_runs}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Success</span><span class="demo-row-stat-value">${successRate}%</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Failed</span><span class="demo-row-stat-value" style="${failedStyle}">${sim.failed_runs}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Last push</span><span class="demo-row-stat-value">${timeAgo}</span></div>
        </div>
        <div class="demo-row-actions">
          ${running ? `
            <button class="btn btn-sm btn-danger" onclick="DemoPageStopDsSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
              Stop
            </button>
          ` : `
            <button class="btn btn-sm btn-primary" onclick="DemoPageRestartDsSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36M3.67 19a9 9 0 0 0 14.82-3.66"/></svg>
              Restart
            </button>
          `}
        </div>
      </div>
    `;
  }

  function renderSimulationCard(sim) {
    const running = sim.is_running;
    const successRate = sim.total_calls > 0
      ? ((sim.successful_calls / sim.total_calls) * 100).toFixed(1)
      : '0.0';
    const timeAgo = sim.last_call_time ? getTimeAgo(sim.last_call_time * 1000) : 'Never';
    const simIdShort = sim.simulation_id ? sim.simulation_id.substring(0, 8) : 'unknown';
    const failedStyle = sim.failed_calls > 0 ? 'color:var(--red-light)' : '';

    return `
      <div class="demo-row">
        <div class="demo-row-dot ${running ? 'running' : 'stopped'}" title="${running ? 'Running' : 'Stopped'}"></div>
        <span class="demo-row-name">${escHtml(sim.model_name)}</span>
        <span class="demo-row-project">${escHtml(sim.project_name)}</span>
        <span class="demo-row-simid" title="${escHtml(sim.simulation_id)}">#${simIdShort}</span>
        <div class="demo-row-divider"></div>
        <div class="demo-row-stats">
          <div class="demo-row-stat"><span class="demo-row-stat-label">Duration</span><span class="demo-row-stat-value">${sim.duration_minutes}m</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Users</span><span class="demo-row-stat-value">${sim.num_users}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Target rate</span><span class="demo-row-stat-value">${sim.success_rate ?? 100}%</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Calls</span><span class="demo-row-stat-value">${sim.total_calls}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Success</span><span class="demo-row-stat-value">${successRate}%</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Failed</span><span class="demo-row-stat-value" style="${failedStyle}">${sim.failed_calls}</span></div>
          <div class="demo-row-stat"><span class="demo-row-stat-label">Last call</span><span class="demo-row-stat-value">${timeAgo}</span></div>
        </div>
        <div class="demo-row-actions">
          ${running ? `
            <button class="btn btn-sm btn-danger" onclick="DemoPageStopSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
              Stop
            </button>
          ` : `
            <button class="btn btn-sm btn-primary" onclick="DemoPageRestartSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36M3.67 19a9 9 0 0 0 14.82-3.66"/></svg>
              Restart
            </button>
          `}
        </div>
      </div>
    `;
  }

  function getTimeAgo(ms) {
    const seconds = Math.floor((Date.now() - ms) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  }

  // Public method to stop simulation (called from button onclick)
  const stopSimulation = async function(simulationId) {
    if (!confirm('Stop this simulation?')) return;

    try {
      await API.demo.stop(simulationId);
      Toast.success('Simulation stopped');
      await refreshSimulations();
    } catch (err) {
      Toast.error(`Failed to stop simulation: ${err.message}`);
    }
  };

  // Public method to restart simulation (called from button onclick)
  const restartSimulation = async function(simulationId) {
    if (!confirm('Restart this simulation?')) return;

    try {
      await API.demo.restart(simulationId);
      Toast.success('Simulation restarted');
      await refreshSimulations();
    } catch (err) {
      Toast.error(`Failed to restart simulation: ${err.message}`);
    }
  };

  // Cleanup
  window.addEventListener('beforeunload', () => {
    if (pollInterval) clearInterval(pollInterval);
  });

  // Public method to stop DS simulation (called from button onclick)
  const stopDsSimulation = async function(simulationId) {
    if (!confirm('Stop this DS simulation?')) return;

    try {
      await API.demo.ds.stop(simulationId);
      Toast.success('DS simulation stopped');
      await refreshDsSimulations();
    } catch (err) {
      Toast.error(`Failed to stop DS simulation: ${err.message}`);
    }
  };

  // Public method to restart DS simulation (called from button onclick)
  const restartDsSimulation = async function(simulationId) {
    if (!confirm('Restart this DS simulation?')) return;

    try {
      await API.demo.ds.restart(simulationId);
      Toast.success('DS simulation restarted');
      await refreshDsSimulations();
    } catch (err) {
      Toast.error(`Failed to restart DS simulation: ${err.message}`);
    }
  };

  return { render, stopSimulation, restartSimulation, stopDsSimulation, restartDsSimulation };
})();

// Expose methods to window for onclick handlers
window.DemoPageStopSimulation = DemoPage.stopSimulation;
window.DemoPageRestartSimulation = DemoPage.restartSimulation;
window.DemoPageStopDsSimulation = DemoPage.stopDsSimulation;
window.DemoPageRestartDsSimulation = DemoPage.restartDsSimulation;
