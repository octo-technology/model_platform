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
      create: (email, password, role = 'SIMPLE_USER') =>
        post(`/users/add?email=${enc(email)}&password=${enc(password)}&role=${enc(role)}`),
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

    // ── Model Infos (governance metadata + full-text search) ──
    modelInfos: {
      search: (query, projectName) => {
        let url = `/model_infos/search?query=${enc(query)}`;
        if (projectName) url += `&project_name=${enc(projectName)}`;
        return get(url);
      },
      aiActCard: (projectName, modelName, version) =>
        get(`/model_infos/${enc(projectName)}/${enc(modelName)}/${enc(version)}/ai_act_card`),
      listForProject: (projectName) => get(`/model_infos/${enc(projectName)}/list`),
    },

    // ── Compliance ──────────────────────────────────────────────
    compliance: {
      dashboard: () => get('/compliance/dashboard'),
      evaluateProject: (proj) => post(`/${enc(proj)}/models/evaluate_compliance`),
      downloadPlatformReport: () =>
        fetch(`${API_BASE}/compliance/download_report`, {
          headers: { Authorization: `Bearer ${Auth.getToken()}` },
        }).then(r => {
          if (!r.ok) throw new Error(r.statusText);
          return r.blob();
        }),
      getGatePolicy: () => get('/ai/gate_policy'),
      setGatePolicy: (policy) =>
        fetch(`${API_BASE}/ai/gate_policy`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ policy }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
    },

    // ── AI Assist ─────────────────────────────────────────────
    ai: {
      status: () => get('/ai/status').catch(() => ({ available: false, provider: null })),
      modelCardSuggest: (proj, model, ver) =>
        post(`/ai/${enc(proj)}/${enc(model)}/${enc(ver)}/model_card_suggest`),
      actReview: (proj, model, ver) =>
        post(`/ai/${enc(proj)}/${enc(model)}/${enc(ver)}/act_review`),
      updateModelCard: (proj, model, ver, modelCard) =>
        fetch(`${API_BASE}/ai/${enc(proj)}/${enc(model)}/${enc(ver)}/model_card`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ model_card: modelCard }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      setCredentials: (apiKey, region) =>
        fetch(`${API_BASE}/ai/credentials`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ api_key: apiKey, region }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      removeCredentials: () =>
        fetch(`${API_BASE}/ai/credentials`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${Auth.getToken()}` },
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      setModel: (modelId) =>
        fetch(`${API_BASE}/ai/model`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ model_id: modelId }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      setProvider: (provider) =>
        fetch(`${API_BASE}/ai/provider`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ provider }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      setApiKey: (apiKey) =>
        fetch(`${API_BASE}/ai/api_key`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ api_key: apiKey }),
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
      removeApiKey: () =>
        fetch(`${API_BASE}/ai/api_key`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${Auth.getToken()}` },
        }).then(async r => {
          if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
          return r.json();
        }),
    },

    // ── Health ────────────────────────────────────────────────
    health: {
      check: () => get('/health'),
      checkStorage: () => get('/health/storage').then(r => r.status === 'ok').catch(() => false),
    },

    // ── Demo Simulation ───────────────────────────────────────
    demo: {
      start: (payload) => post('/demo/start', { body: payload }),
      stop: (simulationId) =>
        post(`/demo/stop`, { body: { simulation_id: simulationId } }),
      restart: (simulationId) =>
        post(`/demo/restart`, { body: { simulation_id: simulationId } }),
      list: () => get('/demo/list'),
      ds: {
        start: (payload) => post('/demo/ds/start', { body: payload }),
        stop: (simulationId) =>
          post('/demo/ds/stop', { body: { simulation_id: simulationId } }),
        restart: (simulationId) =>
          post('/demo/ds/restart', { body: { simulation_id: simulationId } }),
        list: () => get('/demo/ds/list'),
      },
    },
  };
})();

function enc(v) { return encodeURIComponent(v); }

function escHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
