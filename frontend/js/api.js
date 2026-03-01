// API client layer for Model Platform
// All backend communication goes through this module.

const API_BASE = window.API_BASE_URL || 'http://backend.model-platform.svc.cluster.local:8000';

const API = (() => {

  async function request(method, path, { body, rawBody, skipAuth } = {}) {
    const headers = {};
    const token = Auth.getToken();

    if (token && !skipAuth) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    const init = {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : rawBody,
    };

    const response = await fetch(`${API_BASE}${path}`, init);

    if (response.status === 401) {
      Auth.removeToken();
      App.navigateTo('login');
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let msg;
      try { msg = (await response.json()).detail || response.statusText; }
      catch { msg = response.statusText; }
      throw new Error(msg);
    }

    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) return response.json();
    if (ct.includes('application/zip') || ct.includes('octet-stream')) return response.blob();
    return response.text();
  }

  const get  = (path, opts) => request('GET',  path, opts);
  const post = (path, opts) => request('POST', path, opts);

  return {
    // ── Auth ──────────────────────────────────────────────────
    auth: {
      login(email, password) {
        const fd = new FormData();
        fd.append('username', email);
        fd.append('password', password);
        return fetch(`${API_BASE}/auth/token`, { method: 'POST', body: fd })
          .then(async r => {
            if (!r.ok) throw new Error((await r.json()).detail || 'Invalid credentials');
            return r.json();
          });
      },
      me: () => get('/auth/me'),
    },

    // ── Users ─────────────────────────────────────────────────
    users: {
      getAll: () => get('/users/get_all').then(r => r.users ?? r),
      create: (email, password) =>
        post(`/users/add?email=${enc(email)}&password=${enc(password)}&role=SIMPLE_USER`),
    },

    // ── Projects ──────────────────────────────────────────────
    projects: {
      list:     () => get('/projects/list'),
      info:     (name) => get(`/projects/${name}/info`),
      add:      (data) => post('/projects/add', { body: data }),
      remove:   (name) => get(`/projects/${name}/remove`),
      governance:       (name) => get(`/projects/${name}/governance`),
      downloadGovernance: (name) =>
        fetch(`${API_BASE}/projects/${name}/download_governance`, {
          headers: { Authorization: `Bearer ${Auth.getToken()}` },
        }).then(r => r.blob()),

      registryStatus: (name) => get(`/projects/${name}/registry_status`).then(r => r.status).catch(() => 'error'),

      // User management
      getUsers:       (name) => get(`/projects/${name}/users`).then(r => r.users ?? r),
      addUser:        (proj, email, role) =>
        post(`/projects/${proj}/add_user?email=${enc(email)}&role=${enc(role)}`),
      removeUser:     (proj, email) =>
        post(`/projects/${proj}/remove_user?email=${enc(email)}`),
      changeUserRole: (proj, email, role) =>
        post(`/projects/${proj}/change_user_role?email=${enc(email)}&role=${enc(role)}`),
    },

    // ── Models ────────────────────────────────────────────────
    models: {
      list:     (proj) => get(`/${proj}/models/list`),
      versions: (proj, model) => get(`/${proj}/models/${model}/versions`),
      deploy:   (proj, model, ver) => get(`/${proj}/models/deploy/${model}/${ver}`),
      undeploy: (proj, model, ver) => get(`/${proj}/models/undeploy/${model}/${ver}`),
      taskStatus: (proj, taskId) => get(`/${proj}/models/task-status/${taskId}`),

      searchHuggingFace: (query) => get(`/hugging_face/search?search_args=${enc(query)}`),
      getHuggingFaceModel: (proj, modelId) =>
        get(`/hugging_face/get_model/?project_name=${proj}&model_id=${enc(modelId)}`),
    },

    // ── Deployed models ───────────────────────────────────────
    deployedModels: {
      list:   (proj) => get(`/${proj}/deployed_models/list`),
      remove: (proj, model, ver) =>
        get(`/${proj}/deployed_models/remove/${model}/${ver}`),
    },

    // ── Health ────────────────────────────────────────────────
    health: {
      check: () => get('/health'),
      checkStorage: () => get('/health/storage').then(r => r.status === 'ok').catch(() => false),
    },
  };
})();

function enc(v) { return encodeURIComponent(v); }

function escHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
