// Admin page — platform user management
const AdminPage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Administration</div>
            <h1 class="page-title">Users</h1>
          </div>
          <button class="btn btn-primary btn-sm" id="create-user-btn">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            New user
          </button>
        </div>

        <div class="page-content">
          <div id="create-user-area"></div>
          <div class="card">
            <div class="card-header">
              <span class="card-title">Platform users</span>
              <span class="section-count" id="users-count">—</span>
            </div>
            <div id="users-list-area">
              <div class="loading-screen"><span class="spinner"></span><span>Loading…</span></div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('create-user-btn').addEventListener('click', () => toggleCreateForm());
    loadUsers();
  }

  async function loadUsers() {
    const area = document.getElementById('users-list-area');
    try {
      const users = await API.users.getAll();
      renderUsersList(users, area);
      const countEl = document.getElementById('users-count');
      if (countEl) countEl.textContent = users.length;
    } catch (err) {
      area.innerHTML = `
        <div class="empty-state" style="padding:32px">
          <div class="empty-state-title" style="color:var(--red-light)">Access denied</div>
          <div class="empty-state-desc">${escHtml(err.message)}</div>
        </div>`;
    }
  }

  function renderUsersList(users, area) {
    if (!users || users.length === 0) {
      area.innerHTML = `
        <div class="empty-state" style="padding:32px">
          <div class="empty-state-title">No users yet</div>
          <div class="empty-state-desc">Create the first platform user above.</div>
        </div>`;
      return;
    }

    const rows = users.map(u => {
      const email = u.email || u;
      const role  = u.role  || 'SIMPLE_USER';
      const badgeCls = role === 'ADMIN' ? 'badge-orange' : 'badge-neutral';
      return `
        <tr>
          <td class="mono">${escHtml(email)}</td>
          <td><span class="badge ${badgeCls}">${escHtml(role)}</span></td>
        </tr>`;
    }).join('');

    area.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr><th>Email</th><th>Role</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function toggleCreateForm() {
    const area = document.getElementById('create-user-area');
    if (area.dataset.open === 'true') {
      area.innerHTML = '';
      area.dataset.open = 'false';
      return;
    }
    area.dataset.open = 'true';
    area.innerHTML = `
      <div class="card mb-4">
        <div class="card-header"><span class="card-title">Create new user</span></div>
        <div style="padding:16px 20px;display:flex;flex-direction:column;gap:12px;max-width:480px">
          <div class="form-group">
            <label class="form-label">Email</label>
            <input class="form-input" id="new-user-email" type="email" placeholder="user@example.com" autocomplete="off">
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input class="form-input" id="new-user-password" type="password" placeholder="••••••••" autocomplete="new-password">
          </div>
          <div class="form-group">
            <label class="form-label">Role</label>
            <select class="form-select" id="new-user-role">
              <option value="SIMPLE_USER">SIMPLE_USER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm" id="create-user-submit">Create</button>
            <button class="btn btn-secondary btn-sm" id="create-user-cancel">Cancel</button>
          </div>
        </div>
      </div>`;

    document.getElementById('create-user-cancel').addEventListener('click', () => {
      area.innerHTML = '';
      area.dataset.open = 'false';
    });

    document.getElementById('create-user-submit').addEventListener('click', async () => {
      const email    = document.getElementById('new-user-email').value.trim();
      const password = document.getElementById('new-user-password').value;
      const role     = document.getElementById('new-user-role').value;
      if (!email || !password) { Toast.error('Email and password are required.'); return; }

      const btn = document.getElementById('create-user-submit');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span>';
      try {
        await API.users.create(email, password, role);
        Toast.success(`User ${email} created.`);
        area.innerHTML = '';
        area.dataset.open = 'false';
        loadUsers();
      } catch (err) {
        Toast.error(err.message);
        btn.disabled = false;
        btn.innerHTML = 'Create';
      }
    });
  }

  return { render };
})();
