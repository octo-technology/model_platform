// Demo Simulation page — Load test deployed models with concurrent users
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
            <p class="page-subtitle">Load test deployed models with concurrent user simulation</p>
          </div>
        </div>

        <div class="page-content">
          <div class="demo-section">
            <div class="demo-section-title">Start New Simulation</div>

            <form class="demo-form" id="demo-form">
              <div class="form-grid-2">
                <div class="form-group">
                  <label for="project-name-input" class="form-label">Project Name</label>
                  <input
                    class="form-input"
                    id="project-name-input"
                    type="text"
                    placeholder="e.g., smart-grid-load-forecasting"
                    value="Smart-Grid-Load-Forecasting"
                    autocomplete="off"
                  >
                  <div class="form-hint">Exact project name from deployed models</div>
                </div>

                <div class="form-group">
                  <label for="model-name-input" class="form-label">Model Name</label>
                  <input
                    class="form-input"
                    id="model-name-input"
                    type="text"
                    placeholder="e.g., credit-default-predictor"
                    value="credit-default-predictor"
                    autocomplete="off"
                  >
                  <div class="form-hint">Short name (not full deployment name)</div>
                </div>
              </div>

              <div class="form-grid-2">
                <div class="form-group">
                  <label for="model-version-input" class="form-label">Model Version</label>
                  <input
                    class="form-input"
                    id="model-version-input"
                    type="text"
                    placeholder="e.g., 1"
                    value="1"
                    autocomplete="off"
                  >
                  <div class="form-hint">Version of the deployed model</div>
                </div>

                <div class="form-group">
                  <label for="duration-input" class="form-label">Duration (minutes)</label>
                  <input
                    class="form-input"
                    id="duration-input"
                    type="number"
                    min="1"
                    max="30"
                    value="2"
                    autocomplete="off"
                  >
                  <div class="form-hint">1-30 minutes (longer simulations take more time)</div>
                </div>
              </div>

              <div class="form-grid-2">
                <div class="form-group">
                  <label for="users-input" class="form-label">Concurrent Users</label>
                  <input
                    class="form-input"
                    id="users-input"
                    type="number"
                    min="1"
                    value="5"
                    autocomplete="off"
                  >
                  <div class="form-hint">Number of simultaneous users per round</div>
                </div>
              </div>

              <button type="submit" class="btn btn-primary" id="submit-btn">
                <svg class="btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Start Simulation
              </button>
            </form>
          </div>

          <div class="demo-section">
            <div class="demo-section-title">Active Simulations</div>
            <div id="active-simulations" class="demo-simulations-list">
              <div class="loading-screen"><span class="spinner"></span><span>Loading simulations…</span></div>
            </div>
          </div>
        </div>
      </div>
    `;

    attachEvents();
    startPolling();
    refreshSimulations();
  }

  function attachEvents() {
    const form = document.getElementById('demo-form');
    form.addEventListener('submit', handleFormSubmit);
  }

  async function handleFormSubmit(e) {
    e.preventDefault();

    const projectName = document.getElementById('project-name-input').value.trim();
    const modelName = document.getElementById('model-name-input').value.trim();
    const modelVersion = document.getElementById('model-version-input').value.trim();
    const duration = parseInt(document.getElementById('duration-input').value);
    const numUsers = parseInt(document.getElementById('users-input').value);

    // Validation
    if (!projectName || !modelName || !modelVersion) {
      Toast.error('Please fill in all required fields');
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

  function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(() => {
      refreshSimulations();
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

  function renderSimulationCard(sim) {
    const status = sim.is_running ? 'running' : 'stopped';
    const statusCls = status === 'running' ? 'demo-status-running' : 'demo-status-stopped';
    const statusLabel = status === 'running' ? '🟢 Running' : '⚫ Stopped';

    const successRate = sim.total_calls > 0
      ? ((sim.successful_calls / sim.total_calls) * 100).toFixed(1)
      : '0.0';

    const timeAgo = sim.last_call_time ? getTimeAgo(sim.last_call_time * 1000) : 'Never';
    const simIdShort = sim.simulation_id ? sim.simulation_id.substring(0, 8) : 'unknown';

    return `
      <div class="card demo-card">
        <div class="demo-card-header">
          <div class="demo-card-title">
            <span class="demo-card-name">${escHtml(sim.model_name)}</span>
            <span class="demo-card-version">v${escHtml(sim.model_version)}</span>
            <span class="demo-card-project">${escHtml(sim.project_name)}</span>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <div class="demo-card-simid" title="${escHtml(sim.simulation_id)}">#${simIdShort}</div>
            <div class="demo-card-status ${statusCls}">${statusLabel}</div>
          </div>
        </div>

        <div class="demo-card-config">
          <div class="demo-config-item">
            <span class="demo-config-label">Duration</span>
            <span class="demo-config-value">${sim.duration_minutes} min</span>
          </div>
          <div class="demo-config-item">
            <span class="demo-config-label">Users</span>
            <span class="demo-config-value">${sim.num_users} concurrent</span>
          </div>
          <div class="demo-config-item">
            <span class="demo-config-label">Interval</span>
            <span class="demo-config-value">${sim.random_interval}</span>
          </div>
        </div>

        <div class="demo-card-stats">
          <div class="demo-stat">
            <div class="demo-stat-label">Total Calls</div>
            <div class="demo-stat-value">${sim.total_calls}</div>
          </div>
          <div class="demo-stat">
            <div class="demo-stat-label">Success Rate</div>
            <div class="demo-stat-value">${successRate}%</div>
          </div>
          <div class="demo-stat">
            <div class="demo-stat-label">Failed</div>
            <div class="demo-stat-value" style="${sim.failed_calls > 0 ? 'color:var(--red-light)' : ''}">${sim.failed_calls}</div>
          </div>
          <div class="demo-stat">
            <div class="demo-stat-label">Last Call</div>
            <div class="demo-stat-value">${timeAgo}</div>
          </div>
        </div>

        ${sim.last_error ? `
          <div class="demo-card-error">
            <span class="demo-error-label">Last Error:</span>
            <span class="demo-error-msg">${escHtml(sim.last_error)}</span>
          </div>
        ` : ''}

        <div class="demo-card-actions">
          ${sim.is_running ? `
            <button class="btn btn-sm btn-danger" onclick="DemoPageStopSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
              </svg>
              Stop
            </button>
          ` : `
            <button class="btn btn-sm btn-primary" onclick="DemoPageRestartSimulation('${escHtml(sim.simulation_id)}')">
              <svg class="btn-icon-small" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 4v6h-6"/>
                <path d="M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36M3.67 19a9 9 0 0 0 14.82-3.66"/>
              </svg>
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

  return { render, stopSimulation, restartSimulation };
})();

// Expose methods to window for onclick handlers
window.DemoPageStopSimulation = DemoPage.stopSimulation;
window.DemoPageRestartSimulation = DemoPage.restartSimulation;
