// Projects list page
const ProjectsPage = (() => {

  const DEMO_PROJECTS = [
    {
      name: "Credit-Risk-Assessment",
      owner: "BancoFrance - Risk Management Division",
      description: "Scoring crédit et segmentation client",
      team: "Risk & Data Science",
      domain: "Banking",
      scope: "Modèle de scoring crédit pour évaluer le risque de défaut des clients professionnels. Utilise des données transactionnelles, financières et comportementales pour prédire la probabilité de défaut à 12 mois. Déploiement en production pour aide à la décision des conseillers.",
      data_perimeter: "Données clients entreprises France (2019-2024): bilans comptables, flux de trésorerie, historique de crédit, ratios financiers, secteur d'activité. ~500k entreprises. RGPD: Conforme - Pseudonymisation par hachage SHA-256 des identifiants SIREN/SIRET.",
    },
    {
      name: "Medical-Document-NLP",
      owner: "AP-HP (Assistance Publique Hôpitaux de Paris) - DSI Innovation",
      description: "Extraction d'entités cliniques et classification de documents",
      team: "NLP & Clinical AI",
      domain: "Healthcare",
      scope: "Extraction automatique d'informations cliniques depuis les comptes-rendus médicaux non structurés. NLP pour identifier pathologies, traitements, résultats d'examens, allergies. Aide au codage PMSI et à la recherche clinique.",
      data_perimeter: "Comptes-rendus médicaux (hospitalisation, consultations, imagerie) de 2015 à 2024. ~50M de documents. RGPD: Conforme - Pseudonymisation selon MR-004 CNIL. Hébergement certifié HDS. Comité éthique consulté.",
    },
    {
      name: "Employee-Attrition-Prediction",
      owner: "TalentCorp RH - People Analytics Division",
      description: "Prédiction de l'attrition et scoring de satisfaction",
      team: "People Analytics",
      domain: "Human Resources",
      scope: "Prédiction du risque de départ volontaire des collaborateurs et scoring de satisfaction. Modèles entraînés sur des données RH synthétiques: ancienneté, satisfaction, performance, mobilité. Aide à la rétention et à la gestion prévisionnelle des emplois.",
      data_perimeter: "Données RH synthétiques: profils collaborateurs, historique de performance, enquêtes de satisfaction, mobilités internes. ~80k collaborateurs simulés. RGPD: Conforme - Données entièrement synthétiques.",
    },
    {
      name: "Fraud-Detection-Payments",
      owner: "EuroBank Systems - Cyber & Fraud Prevention",
      description: "Détection de fraude et anomalies transactionnelles",
      team: "Fraud & Cyber Analytics",
      domain: "Banking",
      scope: "Détection en temps réel des fraudes sur paiements par carte (e-commerce et retail). Modèle de ML évaluant le risque de chaque transaction en <100ms. Réduction des faux positifs tout en maintenant un taux de détection >95%.",
      data_perimeter: "Transactions par carte des 24 derniers mois: montant, type de commerce, localisation, heure, devise. ~2 milliards de transactions/an. RGPD: Conforme - Tokenisation PCI-DSS v4.0, pseudonymisation des identités clients.",
    },
    {
      name: "Ecommerce-Recommendation",
      owner: "ShopNow Digital - Personalization & Growth",
      description: "Recommandation produit et prédiction du churn client",
      team: "Personalization ML",
      domain: "E-commerce",
      scope: "Système de recommandation produit personnalisé et prédiction du churn client. Modèles entraînés sur les comportements d'achat, navigation et engagement. Optimisation du panier moyen et réduction du taux d'attrition.",
      data_perimeter: "Données comportementales e-commerce synthétiques: historique d'achats, navigation, notes, interactions. ~2M de profils simulés. RGPD: Conforme - Données entièrement synthétiques.",
    },
    {
      name: "Supply-Chain-Optimization",
      owner: "MarchéPlus Distribution - Supply Chain & Advanced Analytics",
      description: "Prévision de la demande et scoring risque fournisseur",
      team: "Supply Chain Analytics",
      domain: "Retail & Logistics",
      scope: "Optimisation des stocks et prévision de la demande pour les produits frais en grande distribution. Scoring du risque fournisseur pour sécuriser les approvisionnements. Réduction du gaspillage alimentaire et des ruptures de stock.",
      data_perimeter: "Historique des ventes quotidiennes sur 3 ans pour 12000 références dans 5000 magasins. Données météo locale, événements, logistiques, évaluations fournisseurs. RGPD: Conforme - Aucune donnée personnelle collectée.",
    },
  ];

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Overview</div>
            <h1 class="page-title">Projects</h1>
          </div>
          <div class="page-actions">
            <button class="btn btn-primary" id="new-project-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              New Project
            </button>
          </div>
        </div>

        <div class="page-content">
          <div id="projects-loading" class="loading-screen">
            <span class="spinner"></span>
            <span>Loading projects…</span>
          </div>
          <div id="projects-grid" class="projects-grid hidden"></div>
          <div id="projects-empty" class="empty-state hidden">
            <div class="empty-state-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="empty-state-title">No projects yet</div>
            <div class="empty-state-desc">Create your first project to start managing ML models.</div>
            <button class="btn btn-primary mt-4" id="new-project-btn-empty">
              Create first project
            </button>
          </div>
        </div>
      </div>
    `;

    loadProjects();
    document.getElementById('new-project-btn').addEventListener('click', openNewProjectModal);
  }

  async function loadProjects() {
    try {
      const projects = await API.projects.list();
      // Fetch deployed model count for each project in parallel
      const enriched = await Promise.all(
        projects.map(async p => {
          const name = p.name || p.Name || '';
          const [deployed, registryOk] = await Promise.allSettled([
            API.deployedModels.list(name),
            API.projects.registryStatus(name),
          ]);
          return {
            ...p,
            _deployed_count: deployed.status === 'fulfilled' && Array.isArray(deployed.value) ? deployed.value.length : 0,
            _registry_status: registryOk.status === 'fulfilled' ? registryOk.value : 'error',
          };
        })
      );
      renderProjects(enriched);
    } catch (err) {
      Toast.error(`Failed to load projects: ${err.message}`);
      document.getElementById('projects-loading').classList.add('hidden');
    }
  }

  function renderProjects(projects) {
    const loading = document.getElementById('projects-loading');
    const grid    = document.getElementById('projects-grid');
    const empty   = document.getElementById('projects-empty');

    loading.classList.add('hidden');

    if (!projects || projects.length === 0) {
      empty.classList.remove('hidden');
      document.getElementById('new-project-btn-empty')?.addEventListener('click', openNewProjectModal);
      return;
    }

    grid.classList.remove('hidden');
    grid.innerHTML = projects.map(p => projectCard(p)).join('');

    grid.querySelectorAll('.project-card').forEach(card => {
      card.addEventListener('click', () => {
        const name = card.dataset.project;
        App.navigateTo('project', { name });
      });
    });

    grid.querySelectorAll('.registry-link').forEach(link => {
      link.addEventListener('click', e => e.stopPropagation());
    });

    grid.querySelectorAll('.delete-project-btn').forEach(btn => {
      btn.addEventListener('click', async e => {
        e.stopPropagation();
        const name = btn.dataset.project;
        const ok = await Modal.confirm({
          title: 'Delete Project',
          message: `Delete project <strong>${name}</strong>? This action cannot be undone.`,
          confirmLabel: 'Delete',
          danger: true,
        });
        if (ok) {
          try {
            await API.projects.remove(name);
            Toast.success(`Project "${name}" deleted.`);
            loadProjects();
          } catch (err) {
            Toast.error(err.message);
          }
        }
      });
    });
  }

  function sanitizeName(name) {
    return name.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/^-+/, '').replace(/-+$/, '');
  }

  function buildRegistryUrl(name) {
    const host = window.MP_HOST_NAME || 'model-platform.com';
    const path = window.MP_REGISTRY_PATH || 'registry';
    return `http://${host}/${path}/${sanitizeName(name)}/`;
  }

  function deployedBadge(count) {
    if (count > 0) {
      return `<span class="badge badge-running">${count} deployed</span>`;
    }
    return `<span class="badge badge-neutral">No deployments</span>`;
  }

  function registryStatusDot(status) {
    const map = {
      running:   { color: 'var(--cyan)',       label: 'Healthy'      },
      pending:   { color: 'var(--orange)',      label: 'Starting…'    },
      error:     { color: 'var(--red-light)',   label: 'Error'        },
      not_found: { color: 'var(--text-2)',      label: 'Not deployed' },
    };
    const { color, label } = map[status] || { color: 'var(--text-2)', label: status || '…' };
    return `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:${color};white-space:nowrap" title="Registry: ${label}">
      <svg width="7" height="7" viewBox="0 0 7 7" fill="currentColor"><circle cx="3.5" cy="3.5" r="3.5"/></svg>
      ${escHtml(label)}
    </span>`;
  }

  function projectCard(p) {
    const name           = p.name  || p.Name  || '—';
    const owner          = p.owner || p.Owner || '—';
    const scope          = p.scope || p.Scope || '';
    const deployedCount  = p._deployed_count  ?? 0;
    const registryStatus = p._registry_status || 'error';
    const registryUrl    = buildRegistryUrl(name);

    return `
      <div class="project-card" data-project="${escHtml(name)}">
        <div class="project-card-header">
          <div class="project-name">${escHtml(name)}</div>
          ${deployedBadge(deployedCount)}
        </div>
        ${scope ? `<p class="project-scope-desc">${escHtml(scope)}</p>` : ''}
        <div class="project-meta">
          <div class="project-meta-row">
            <span class="project-meta-key">Owner</span>
            <span class="project-meta-val">${escHtml(owner)}</span>
          </div>
        </div>
        <div class="project-card-footer">
          <div class="flex items-center gap-2">
            <a class="btn btn-ghost btn-sm registry-link" href="${escHtml(registryUrl)}" target="_blank" rel="noopener" title="Open MLflow registry">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              MLflow
            </a>
            ${registryStatusDot(registryStatus)}
          </div>
          <button class="btn btn-ghost btn-sm delete-project-btn" data-project="${escHtml(name)}" title="Delete project">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
            </svg>
          </button>
        </div>
      </div>
    `;
  }

  function openNewProjectModal() {
    const { close } = Modal.open({
      title: 'New Project',
      body: `
        <div class="form-group">
          <label class="form-label">Project name</label>
          <input class="form-input" id="new-proj-name" placeholder="e.g. fraud-detection" autocomplete="off">
        </div>
        <div class="form-group">
          <label class="form-label">Owner</label>
          <input class="form-input" id="new-proj-owner" placeholder="Team or person" autocomplete="off">
        </div>
        <div class="form-group">
          <label class="form-label">Scope</label>
          <textarea class="form-input" id="new-proj-scope" placeholder="What is this project about?" rows="3" style="resize:vertical"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Data perimeter</label>
          <textarea class="form-input" id="new-proj-perimeter" placeholder="Data sources, GDPR compliance, retention…" rows="3" style="resize:vertical"></textarea>
        </div>
        <div class="form-group" style="display:flex;align-items:center;gap:8px">
          <input type="checkbox" id="new-proj-batch" style="width:16px;height:16px;cursor:pointer">
          <label for="new-proj-batch" class="form-label" style="margin:0;cursor:pointer">Enable batch predictions</label>
        </div>
        <p id="new-proj-error" style="color:var(--red-light);font-size:12px;display:none;"></p>
      `,
      footer: `
        <button class="btn btn-ghost btn-sm" id="modal-autofill" title="Fill with a demo project">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          Auto-fill demo
        </button>
        <div style="flex:1"></div>
        <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
        <button class="btn btn-primary" id="modal-create">Create</button>
      `,
    });

    document.getElementById('modal-autofill').addEventListener('click', () => {
      const demo = DEMO_PROJECTS[Math.floor(Math.random() * DEMO_PROJECTS.length)];
      document.getElementById('new-proj-name').value      = demo.name;
      document.getElementById('new-proj-owner').value     = demo.owner;
      document.getElementById('new-proj-scope').value     = demo.scope;
      document.getElementById('new-proj-perimeter').value = demo.data_perimeter;
      document.getElementById('new-proj-error').style.display = 'none';
    });

    document.getElementById('modal-cancel').addEventListener('click', () => close());

    document.getElementById('modal-create').addEventListener('click', async () => {
      const name      = document.getElementById('new-proj-name').value.trim();
      const owner     = document.getElementById('new-proj-owner').value.trim();
      const scope     = document.getElementById('new-proj-scope').value.trim();
      const perimeter = document.getElementById('new-proj-perimeter').value.trim();
      const errEl     = document.getElementById('new-proj-error');

      if (!name) { errEl.textContent = 'Project name is required.'; errEl.style.display = 'block'; return; }

      const btn = document.getElementById('modal-create');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner spinner-sm"></span> Creating…';

      try {
        const batchEnabled = document.getElementById('new-proj-batch').checked;
        await API.projects.add({ name, owner, scope, data_perimeter: perimeter, batch_enabled: batchEnabled });
        close();
        Toast.success(`Project "${name}" created.`);
        loadProjects();
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Create';
      }
    });
  }

  return { render };
})();

// escHtml is defined in api.js and available globally
