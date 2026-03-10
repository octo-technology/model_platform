// Settings page — platform-level configuration and integrations
const SettingsPage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Platform</div>
            <h1 class="page-title">Settings</h1>
          </div>
        </div>

        <div class="page-content">
          <div class="settings-section-label">Integrations</div>
          <div id="integrations-area">
            <div class="loading-screen"><span class="spinner"></span><span>Loading…</span></div>
          </div>
        </div>
      </div>
    `;

    loadClaudeStatus();
  }

  async function loadClaudeStatus() {
    const area = document.getElementById('integrations-area');
    try {
      const status = await API.ai.status();
      renderClaudeCard(status, area);
    } catch {
      renderClaudeCard({ available: false, provider: null }, area);
    }
  }

  function renderClaudeCard(status, area) {
    const { available, provider, bedrock_models, bedrock_model_id } = status;
    const statusBadge = available
      ? `<span class="badge badge-green integration-status-badge">Active</span>`
      : `<span class="badge badge-neutral integration-status-badge">Inactive</span>`;

    area.innerHTML = `
      <div class="integration-card">
        <div class="integration-card-top">
          <div class="integration-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="integration-meta">
            <div class="integration-name-row">
              <span class="integration-name">Claude AI Assist</span>
              ${statusBadge}
            </div>
            <div class="integration-desc">
              AI-powered model card generation and EU AI Act compliance analysis.
              Credentials are stored server-side and never returned to the browser.
            </div>
          </div>
        </div>
        <div class="integration-divider"></div>
        <div class="integration-body">
          ${renderProviderToggle(provider)}
          ${provider === 'bedrock' ? renderModelSelector(bedrock_models, bedrock_model_id) : ''}
          ${provider ? renderCredentialsSection(provider, available) : ''}
        </div>
      </div>
    `;

    bindEvents(provider, available, bedrock_models);
  }

  function renderProviderToggle(provider) {
    return `
      <div style="margin-bottom:20px">
        <div class="form-label" style="margin-bottom:8px">Provider</div>
        <div class="provider-toggle-group">
          <button
            class="btn btn-sm provider-toggle-btn ${provider === 'bedrock' ? 'provider-toggle-btn--active' : ''}"
            id="provider-btn-bedrock"
            data-provider="bedrock"
          >AWS Bedrock</button>
          <button
            class="btn btn-sm provider-toggle-btn ${provider === 'anthropic' ? 'provider-toggle-btn--active' : ''}"
            id="provider-btn-anthropic"
            data-provider="anthropic"
          >Anthropic API</button>
        </div>
      </div>
    `;
  }

  function renderModelSelector(models, selectedModelId) {
    if (!models) return '';
    const options = Object.entries(models)
      .map(([id, label]) => `<option value="${id}" ${id === selectedModelId ? 'selected' : ''}>${label}</option>`)
      .join('');
    return `
      <div style="margin-bottom:20px">
        <div class="form-label" style="margin-bottom:8px">Model</div>
        <select class="form-input" id="settings-bedrock-model-select" style="max-width:360px">
          ${options}
        </select>
      </div>
    `;
  }

  function renderCredentialsSection(provider, available) {
    if (provider === 'bedrock') {
      return available ? renderBedrockConfigured() : renderBedrockUnconfigured();
    }
    if (provider === 'anthropic') {
      return available ? renderAnthropicConfigured() : renderAnthropicUnconfigured();
    }
    return '';
  }

  function renderBedrockUnconfigured() {
    return `
      <div class="key-row" style="flex-direction:column;gap:12px;align-items:stretch">
        <div class="key-input-group">
          <label class="form-label">API Key</label>
          <input
            class="form-input key-input"
            id="settings-bedrock-api-key-input"
            type="password"
            placeholder="Bedrock API key (bearer token)"
            autocomplete="off"
            spellcheck="false"
          >
        </div>
        <div class="key-input-group">
          <label class="form-label">Region</label>
          <input
            class="form-input key-input"
            id="settings-region-input"
            type="text"
            placeholder="us-east-1"
            value="us-east-1"
            autocomplete="off"
            spellcheck="false"
          >
        </div>
        <div>
          <button class="btn btn-primary btn-sm" id="settings-key-save" style="white-space:nowrap">
            Save credentials
          </button>
        </div>
      </div>
    `;
  }

  function renderBedrockConfigured() {
    return `
      <div>
        <div class="key-secured">
          <span class="key-secured-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </span>
          <div class="key-secured-content">
            <div class="key-secured-value">••••••••••••••••••••</div>
            <div class="key-secured-note">Stored securely · value never leaves the server</div>
          </div>
        </div>
        <div class="key-secured-actions">
          <button class="btn btn-secondary btn-sm btn-danger-soft" id="settings-key-remove">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
            Remove credentials
          </button>
        </div>
      </div>
    `;
  }

  function renderAnthropicUnconfigured() {
    return `
      <div class="key-row" style="flex-direction:column;gap:12px;align-items:stretch">
        <div class="key-input-group">
          <label class="form-label">API Key</label>
          <input
            class="form-input key-input"
            id="settings-anthropic-key-input"
            type="password"
            placeholder="sk-ant-…"
            autocomplete="off"
            spellcheck="false"
          >
          <div class="key-hint">Starts with <mark>sk-ant-</mark></div>
        </div>
        <div>
          <button class="btn btn-primary btn-sm" id="settings-anthropic-key-save" style="white-space:nowrap">
            Save API key
          </button>
        </div>
      </div>
    `;
  }

  function renderAnthropicConfigured() {
    return `
      <div>
        <div class="key-secured">
          <span class="key-secured-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </span>
          <div class="key-secured-content">
            <div class="key-secured-value">sk-ant-••••••••••••••••</div>
            <div class="key-secured-note">Stored securely · value never leaves the server</div>
          </div>
        </div>
        <div class="key-secured-actions">
          <button class="btn btn-secondary btn-sm btn-danger-soft" id="settings-anthropic-key-remove">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
            Remove API key
          </button>
        </div>
      </div>
    `;
  }

  function bindEvents(provider, available, bedrockModels) {
    // Provider toggle
    document.querySelectorAll('.provider-toggle-btn[data-provider]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const selected = btn.dataset.provider;
        if (selected === provider) return;
        btn.disabled = true;
        try {
          await API.ai.setProvider(selected);
          loadClaudeStatus();
        } catch (err) {
          Toast.error(err.message);
          btn.disabled = false;
        }
      });
    });

    // Bedrock model selector
    const modelSelect = document.getElementById('settings-bedrock-model-select');
    if (modelSelect) {
      modelSelect.addEventListener('change', async () => {
        try {
          await API.ai.setModel(modelSelect.value);
          Toast.success('Model updated.');
        } catch (err) {
          Toast.error(err.message);
        }
      });
    }

    if (provider === 'bedrock') {
      if (!available) {
        const apiKeyInput = document.getElementById('settings-bedrock-api-key-input');
        const regionInput = document.getElementById('settings-region-input');
        const saveBtn     = document.getElementById('settings-key-save');

        saveBtn.addEventListener('click', async () => {
          const apiKey = apiKeyInput.value.trim();
          const region = regionInput.value.trim() || 'us-east-1';

          if (!apiKey) { Toast.error('Please enter a Bedrock API key.'); return; }

          saveBtn.disabled = true;
          saveBtn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.ai.setCredentials(apiKey, region);
            Toast.success('Bedrock API key saved.');
            loadClaudeStatus();
          } catch (err) {
            Toast.error(err.message);
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Save credentials';
          }
        });
      } else {
        document.getElementById('settings-key-remove').addEventListener('click', async () => {
          const btn = document.getElementById('settings-key-remove');
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.ai.removeCredentials();
            Toast.success('AWS credentials removed.');
            loadClaudeStatus();
          } catch (err) {
            Toast.error(err.message);
            btn.disabled = false;
            btn.innerHTML = 'Remove credentials';
          }
        });
      }
    } else if (provider === 'anthropic') {
      if (!available) {
        const keyInput = document.getElementById('settings-anthropic-key-input');
        const saveBtn  = document.getElementById('settings-anthropic-key-save');

        saveBtn.addEventListener('click', async () => {
          const apiKey = keyInput.value.trim();
          if (!apiKey) { Toast.error('Please enter an API key.'); return; }
          if (!apiKey.startsWith('sk-ant-')) { Toast.error('API key must start with sk-ant-.'); return; }

          saveBtn.disabled = true;
          saveBtn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.ai.setApiKey(apiKey);
            Toast.success('Anthropic API key saved.');
            loadClaudeStatus();
          } catch (err) {
            Toast.error(err.message);
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Save API key';
          }
        });
      } else {
        document.getElementById('settings-anthropic-key-remove').addEventListener('click', async () => {
          const btn = document.getElementById('settings-anthropic-key-remove');
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner spinner-sm"></span>';
          try {
            await API.ai.removeApiKey();
            Toast.success('Anthropic API key removed.');
            loadClaudeStatus();
          } catch (err) {
            Toast.error(err.message);
            btn.disabled = false;
            btn.innerHTML = 'Remove API key';
          }
        });
      }
    }
  }

  return { render };
})();
