// Search page — platform-wide full-text search over model infos (model cards + risk levels)
const SearchPage = (() => {

  let debounceTimer = null;
  let currentProjectFilter = '';

  const RISK_META = {
    unacceptable: { cls: 'risk-unacceptable', label: 'Unacceptable' },
    high:         { cls: 'risk-high',         label: 'High' },
    limited:      { cls: 'risk-limited',      label: 'Limited' },
    minimal:      { cls: 'risk-minimal',      label: 'Minimal' },
  };

  function render(container, params = {}) {
    const initialQuery = params.q || '';

    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Platform</div>
            <h1 class="page-title">Model Search</h1>
          </div>
        </div>

        <div class="page-content">
          <div class="search-hero">
            <div class="search-hero-bar">
              <div class="search-hero-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <input
                class="search-hero-input"
                id="search-main-input"
                type="text"
                placeholder="Search model cards, risk levels, model names…"
                autocomplete="off"
                spellcheck="false"
                value="${escHtml(initialQuery)}"
              >
              <div class="search-hero-kbd" id="search-clear-btn" style="display:none" title="Clear">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </div>
            </div>

            <div class="search-filters" id="search-filters">
              <span class="search-filter-label">Scope:</span>
              <select class="search-scope-select" id="search-scope-select">
                <option value="">All projects</option>
              </select>
              <div class="search-hint">
                <kbd>⌘K</kbd> from anywhere
              </div>
            </div>
          </div>

          <div id="search-results" class="search-results-area">
            ${initialQuery ? '' : renderEmptyPrompt()}
          </div>
        </div>
      </div>
    `;

    loadProjectScope();
    attachEvents(initialQuery);

    // Auto-focus and auto-search if query passed via URL
    const input = document.getElementById('search-main-input');
    input.focus();
    if (initialQuery) {
      triggerSearch(initialQuery);
    }
  }

  function attachEvents(initialQuery) {
    const input     = document.getElementById('search-main-input');
    const clearBtn  = document.getElementById('search-clear-btn');
    const scopeSel  = document.getElementById('search-scope-select');

    input.addEventListener('input', e => {
      const q = e.target.value;
      clearBtn.style.display = q ? '' : 'none';
      clearTimeout(debounceTimer);
      if (!q.trim()) {
        document.getElementById('search-results').innerHTML = renderEmptyPrompt();
        return;
      }
      debounceTimer = setTimeout(() => triggerSearch(q.trim()), 320);
    });

    clearBtn.addEventListener('click', () => {
      input.value = '';
      clearBtn.style.display = 'none';
      document.getElementById('search-results').innerHTML = renderEmptyPrompt();
      input.focus();
    });

    scopeSel.addEventListener('change', e => {
      currentProjectFilter = e.target.value;
      const q = input.value.trim();
      if (q) triggerSearch(q);
    });

    // Show clear button if pre-filled
    if (initialQuery) clearBtn.style.display = '';
  }

  async function loadProjectScope() {
    const select = document.getElementById('search-scope-select');
    try {
      const projects = await API.projects.list();
      if (!projects || projects.length === 0) return;
      const options = projects.map(p => {
        const name = p.name || p.Name || '';
        return `<option value="${escHtml(name)}">${escHtml(name)}</option>`;
      }).join('');
      select.innerHTML = `<option value="">All projects</option>${options}`;
    } catch {}
  }

  async function triggerSearch(query) {
    const area = document.getElementById('search-results');
    area.innerHTML = `<div class="loading-screen"><span class="spinner"></span><span>Searching…</span></div>`;

    try {
      const results = await API.modelInfos.search(query, currentProjectFilter || undefined);
      renderResults(area, results, query);
    } catch (err) {
      area.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title" style="color:var(--red-light)">Search error</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>`;
    }
  }

  function renderResults(area, results, query) {
    if (!results || results.length === 0) {
      area.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </div>
          <div class="empty-state-title">No results for "${escHtml(query)}"</div>
          <div class="empty-state-desc">Try different terms or broaden the scope to all projects.</div>
        </div>`;
      return;
    }

    const cards = results.map(r => renderResultCard(r, query)).join('');
    area.innerHTML = `
      <div class="search-results-header">
        <span class="search-results-count">${results.length} result${results.length > 1 ? 's' : ''}</span>
        ${currentProjectFilter ? `<span class="search-results-scope">in <strong>${escHtml(currentProjectFilter)}</strong></span>` : ''}
      </div>
      <div class="search-results-list">${cards}</div>
    `;

    // Wire project links → navigate to project
    area.querySelectorAll('[data-nav-project]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        App.navigateTo('project', { name: el.dataset.navProject });
      });
    });
  }

  function renderResultCard(r, query) {
    const modelName    = r.model_name    || '—';
    const modelVersion = r.model_version || '—';
    const projectName  = r.project_name  || '—';
    const riskLevel    = (r.risk_level || '').toLowerCase();
    const modelCard    = r.model_card    || '';

    const riskMeta = RISK_META[riskLevel] || null;
    const riskBadge = riskMeta
      ? `<span class="risk-badge ${riskMeta.cls}">${riskMeta.label}</span>`
      : riskLevel
        ? `<span class="risk-badge risk-unknown">${escHtml(r.risk_level)}</span>`
        : '';

    const cardExcerpt = modelCard ? highlightSnippet(modelCard, query, 200) : '';

    return `
      <div class="search-result-card">
        <div class="search-result-header">
          <div class="search-result-identity">
            <span class="search-result-name">${escHtml(modelName)}</span>
            <span class="search-result-version mono">v${escHtml(String(modelVersion))}</span>
          </div>
          <div class="search-result-meta">
            ${riskBadge}
            <a href="#" class="search-result-project-link" data-nav-project="${escHtml(projectName)}">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              ${escHtml(projectName)}
            </a>
          </div>
        </div>
        ${cardExcerpt ? `<div class="search-result-excerpt">${cardExcerpt}</div>` : ''}
      </div>`;
  }

  // Returns a safe HTML snippet of `text` around the first occurrence of `query`,
  // with matches highlighted via <mark>.
  function highlightSnippet(text, query, maxLen) {
    if (!text) return '';
    const safeText = String(text);

    // Find the best window to show
    const lowerText  = safeText.toLowerCase();
    const lowerQuery = query.toLowerCase().trim();
    const idx = lowerText.indexOf(lowerQuery);

    let start = 0;
    if (idx > 0) {
      start = Math.max(0, idx - 60);
    }

    let excerpt = safeText.slice(start, start + maxLen);
    if (start > 0)          excerpt = '…' + excerpt;
    if (start + maxLen < safeText.length) excerpt += '…';

    // Escape, then highlight query terms
    const escaped = escHtml(excerpt);
    const terms = lowerQuery.split(/\s+/).filter(Boolean);
    let highlighted = escaped;
    terms.forEach(term => {
      const re = new RegExp(escapeRe(escHtml(term)), 'gi');
      highlighted = highlighted.replace(re, m => `<mark class="search-mark">${m}</mark>`);
    });

    return highlighted;
  }

  function escapeRe(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function renderEmptyPrompt() {
    return `
      <div class="search-empty-prompt">
        <div class="search-empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </div>
        <div class="search-empty-title">Search your models</div>
        <div class="search-empty-desc">Full-text search across model cards and risk levels of all your projects.</div>
        <div class="search-empty-tips">
          <div class="search-tip-item">
            <span class="search-tip-icon">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </span>
            Search by risk level: <code>high</code>, <code>minimal</code>, <code>unacceptable</code>
          </div>
          <div class="search-tip-item">
            <span class="search-tip-icon">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="9" height="9"/><rect x="13" y="2" width="9" height="9"/><rect x="13" y="13" width="9" height="9"/><rect x="2" y="13" width="9" height="9"/></svg>
            </span>
            Search by use case, domain, or model card content
          </div>
          <div class="search-tip-item">
            <span class="search-tip-icon">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </span>
            Filter by project using the selector above
          </div>
        </div>
      </div>`;
  }

  return { render };
})();
