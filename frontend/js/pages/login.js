// Login page — sign in + account creation
const LoginPage = (() => {

  function render(container) {
    container.innerHTML = `
      <div class="login-shell page-animate">

        <!-- Left branding panel -->
        <div class="login-brand">
          <div class="login-brand-logo">
            <svg width="36" height="36" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="rgba(0,163,190,0.18)"/>
              <path d="M16 4L28 10.5V21.5L16 28L4 21.5V10.5L16 4Z" stroke="#00A3BE" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
              <circle cx="16" cy="16" r="5" fill="#00A3BE"/>
              <circle cx="16" cy="16" r="2.5" fill="#0E2356"/>
            </svg>
            <div>
              <div class="login-brand-name">MODEL PLATFORM</div>
            </div>
          </div>

          <div class="login-brand-content">
            <h1 class="login-brand-headline">
              ML<br>MODELS<br><span>AT SCALE</span>
            </h1>
            <p class="login-brand-desc">
              Version, deploy and govern machine learning models on Kubernetes — with minimal configuration and full visibility.
            </p>
            <div class="login-brand-pills">
              <span class="login-pill">Kubernetes-native</span>
              <span class="login-pill">MLflow registry</span>
              <span class="login-pill">Role-based access</span>
              <span class="login-pill">Governance audit trail</span>
              <span class="login-pill">HuggingFace integration</span>
            </div>
          </div>

          <div class="login-brand-footnote">
            <span class="login-brand-footnote-label">Developed by</span>
            <img src="assets/octo_logo.png" alt="OCTO Technology" class="login-octo-logo">
          </div>
        </div>

        <!-- Right form panel -->
        <div class="login-form-panel">
          <div class="login-card">
            <h2 class="login-title">Welcome back</h2>
            <p class="login-subtitle">Sign in to your account to continue.</p>

            <div class="login-tabs">
              <button class="login-tab-btn active" data-tab="signin">Sign in</button>
              <button class="login-tab-btn" data-tab="create">Create account</button>
            </div>

            <!-- Sign in form -->
            <div id="tab-signin">
              <form class="login-form" id="signin-form">
                <div class="form-group">
                  <label class="form-label">Email</label>
                  <input class="form-input" type="email" id="signin-email" placeholder="you@company.com" autocomplete="email" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Password</label>
                  <input class="form-input" type="password" id="signin-password" placeholder="••••••••" autocomplete="current-password" required>
                </div>
                <button type="submit" class="btn btn-primary" id="signin-btn">Sign in</button>
                <p id="signin-error" style="color:var(--red-light);font-size:12px;display:none;text-align:center;"></p>
              </form>
            </div>

            <!-- Create account form -->
            <div id="tab-create" class="hidden">
              <form class="login-form" id="create-form">
                <div class="form-group">
                  <label class="form-label">Email</label>
                  <input class="form-input" type="email" id="create-email" placeholder="you@company.com" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Password</label>
                  <input class="form-input" type="password" id="create-password" placeholder="Choose a password" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Confirm password</label>
                  <input class="form-input" type="password" id="create-password-confirm" placeholder="Repeat your password" required>
                </div>
                <button type="submit" class="btn btn-primary" id="create-btn">Create account</button>
                <p id="create-error" style="color:var(--red-light);font-size:12px;display:none;text-align:center;"></p>
              </form>
            </div>
          </div>
        </div>
      </div>
    `;

    attachEvents();
  }

  function attachEvents() {
    // Tab switching
    document.querySelectorAll('.login-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.login-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        document.getElementById('tab-signin').classList.toggle('hidden', tab !== 'signin');
        document.getElementById('tab-create').classList.toggle('hidden', tab !== 'create');
      });
    });

    // Sign in
    document.getElementById('signin-form').addEventListener('submit', async e => {
      e.preventDefault();
      const btn   = document.getElementById('signin-btn');
      const email = document.getElementById('signin-email').value.trim();
      const pass  = document.getElementById('signin-password').value;
      const err   = document.getElementById('signin-error');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span> Signing in…';
      err.style.display = 'none';

      try {
        await Auth.login(email, pass);
        App.navigateTo('projects');
      } catch (ex) {
        err.textContent = ex.message;
        err.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Sign in';
      }
    });

    // Create account
    document.getElementById('create-form').addEventListener('submit', async e => {
      e.preventDefault();
      const btn     = document.getElementById('create-btn');
      const email   = document.getElementById('create-email').value.trim();
      const pass    = document.getElementById('create-password').value;
      const confirm = document.getElementById('create-password-confirm').value;
      const err     = document.getElementById('create-error');

      if (pass !== confirm) {
        err.textContent = 'Passwords do not match';
        err.style.display = 'block';
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span> Creating…';
      err.style.display = 'none';

      try {
        await API.users.create(email, pass);
        Toast.success('Account created! You can now sign in.');
        document.querySelector('[data-tab="signin"]').click();
        document.getElementById('signin-email').value = email;
      } catch (ex) {
        err.textContent = ex.message;
        err.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Create account';
      }
    });
  }

  return { render };
})();
