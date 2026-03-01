// App — router, sidebar, health checks, initialization
const App = (() => {

  // Current route state
  let currentRoute = null;
  let currentParams = {};

  // Auto-refresh interval (matches Streamlit 20s)
  let refreshTimer = null;

  // ── Routing ────────────────────────────────────────────────

  function navigateTo(route, params = {}) {
    if (route === 'login') {
      window.location.hash = '#login';
    } else if (route === 'project') {
      window.location.hash = `#project/${encodeURIComponent(params.name)}`;
    } else {
      window.location.hash = `#${route}`;
    }
  }

  function handleRoute() {
    const hash = window.location.hash.slice(1) || 'login';
    const [base, ...rest] = hash.split('/');

    if (!Auth.isLoggedIn() && base !== 'login') {
      navigateTo('login');
      return;
    }

    if (Auth.isLoggedIn() && base === 'login') {
      navigateTo('projects');
      return;
    }

    currentRoute  = base;
    currentParams = rest.length ? { name: decodeURIComponent(rest.join('/')) } : {};

    updateSidebar();
    renderPage();
  }

  function renderPage() {
    const container = document.getElementById('app');

    switch (currentRoute) {
      case 'login':
        hideSidebar();
        LoginPage.render(container);
        break;

      case 'projects':
        showSidebar();
        updateNavActive('projects');
        ProjectsPage.render(container);
        break;

      case 'project':
        showSidebar();
        updateNavActive('projects');
        ProjectDetailPage.render(container, currentParams);
        break;

      case 'governance':
        showSidebar();
        updateNavActive('governance');
        GovernancePage.render(container);
        break;

      case 'search':
        showSidebar();
        updateNavActive('search');
        SearchPage.render(container, currentParams);
        break;

      default:
        if (Auth.isLoggedIn()) {
          navigateTo('projects');
        } else {
          navigateTo('login');
        }
    }
  }

  // ── Sidebar ────────────────────────────────────────────────

  function showSidebar() {
    document.getElementById('sidebar').classList.remove('hidden');
    document.getElementById('main').classList.remove('no-sidebar');
  }

  function hideSidebar() {
    document.getElementById('sidebar').classList.add('hidden');
    document.getElementById('main').classList.add('no-sidebar');
  }

  function updateSidebar() {
    if (!Auth.isLoggedIn()) return;

    const user = Auth.getUser();
    if (user) {
      const email = user.email || user.username || '';
      const avatarChar = email.charAt(0).toUpperCase();
      const avatarEl = document.getElementById('user-avatar');
      const emailEl  = document.getElementById('user-email');
      if (avatarEl) avatarEl.textContent = avatarChar;
      if (emailEl)  emailEl.textContent  = email;
    }
  }

  function updateNavActive(route) {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.route === route);
    });
  }

  // ── Health checks ──────────────────────────────────────────

  async function checkHealth() {
    const backendDot = document.getElementById('backend-status-dot');
    const storageDot = document.getElementById('storage-status-dot');
    if (!backendDot || !storageDot) return;

    try {
      await API.health.check();
      backendDot.dataset.status = 'ok';
    } catch {
      backendDot.dataset.status = 'error';
    }

    try {
      const ok = await API.health.checkStorage();
      storageDot.dataset.status = ok ? 'ok' : 'error';
    } catch {
      storageDot.dataset.status = 'error';
    }
  }

  // ── Init ───────────────────────────────────────────────────

  function init() {
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', () => {
      Auth.logout();
    });

    // Sidebar nav links (update active without reload where possible)
    document.querySelectorAll('.nav-item[data-route]').forEach(item => {
      item.addEventListener('click', e => {
        e.preventDefault();
        navigateTo(item.dataset.route);
      });
    });

    // Route handling
    window.addEventListener('hashchange', handleRoute);
    handleRoute(); // handle initial load

    // Global keyboard shortcut: Cmd+K / Ctrl+K → Model Search
    document.addEventListener('keydown', e => {
      if (!Auth.isLoggedIn()) return;
      const isMod = e.metaKey || e.ctrlKey;
      if (isMod && e.key === 'k') {
        e.preventDefault();
        navigateTo('search');
        // If already on search, focus the input directly
        const input = document.getElementById('search-main-input');
        if (input) { input.focus(); input.select(); }
      }
    });

    // Health checks — only when logged in
    if (Auth.isLoggedIn()) {
      checkHealth();
      setInterval(checkHealth, 30000);
    }
  }

  return { init, navigateTo };
})();

// Bootstrap on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
