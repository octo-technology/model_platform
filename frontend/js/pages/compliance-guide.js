// Philippe Stepniewski
// Compliance Guide — static reference page for data scientists
const ComplianceGuidePage = (() => {

  const MODEL_CARD_TEMPLATE = `# Model Card — {model_name}

## Description
<!-- Décrivez brièvement ce que fait ce modèle -->

## Niveau de risque AI Act
<!-- inacceptable / élevé / limité / minimal -->
<!-- Justifiez votre choix au regard de l'usage prévu et de l'Annexe III -->

## Usage prévu
### Objectif
<!-- But principal du système -->
### Cas d'usage
<!-- Usages prévus -->
### Utilisateurs cibles
<!-- Qui utilise ce modèle -->
### Usages interdits
<!-- Ce que le modèle ne doit PAS faire -->

## Données d'entraînement
<!-- Source, volume, période, langue, données personnelles, prétraitement -->

## Évaluation des performances et équité
<!-- Résultats des évaluations, analyse des biais par sous-groupes -->

## Limites connues
<!-- Limites techniques, domaine de validité, risques résiduels -->

## Contrôle humain
<!-- Mesures de supervision humaine, alertes, kill switch, audit -->

## Explicabilité
<!-- Méthodes d'explicabilité utilisées (SHAP, LIME…) -->

## Robustesse
<!-- Tests de robustesse effectués, gestion des entrées hors distribution -->`;

  const MINIMAL_SNIPPET = `import mlflow

with mlflow.start_run():
    # 1. Niveau de risque (obligatoire)
    mlflow.set_tag("risk_level", "minimal")

    # 2. Auteur (obligatoire — automatique via mlflow.user)

    # 3. Métriques (obligatoire — au moins une)
    mlflow.log_metric("accuracy", 0.94)

    # 4. Model card (obligatoire)
    mlflow.set_tag("mlflow.note.content", """
# Model Card — Mon Modèle
## Description
Modèle de classification simple.
## Niveau de risque AI Act
Minimal — pas d'impact direct sur les personnes.
    """)

    # 5. Paramètres (recommandé)
    mlflow.log_param("n_estimators", 100)

    # 6. Signature (recommandé)
    from mlflow.models import infer_signature
    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, "model", signature=signature)`;

  const LIMITED_SNIPPET = `import mlflow

with mlflow.start_run():
    # 1. Niveau de risque
    mlflow.set_tag("risk_level", "limited")

    # 2. Métriques de performance
    mlflow.log_metric("accuracy", 0.92)
    mlflow.log_metric("f1_score", 0.89)

    # 3. Paramètres du modèle
    mlflow.log_param("model_type", "gradient_boosting")
    mlflow.log_param("n_estimators", 200)

    # 4. Model card avec section transparence
    mlflow.set_tag("mlflow.note.content", """
# Model Card — Mon Modèle (Risque Limité)

## Description
Chatbot de support client utilisant un modèle de NLP.

## Niveau de risque AI Act
Limité (Art. 50) — système d'IA interagissant avec des personnes.

## Usage prévu
### Objectif
Répondre aux questions fréquentes des clients.
### Utilisateurs cibles
Clients du service après-vente.
### Usages interdits
Ne doit pas prendre de décisions engageantes.

## Transparence (Art. 50)
Les utilisateurs sont informés qu'ils interagissent avec une IA
via un bandeau visible sur l'interface.

## Données d'entraînement
Historique de 50 000 conversations anonymisées (2023-2024).

## Limites connues
Ne couvre pas les demandes hors périmètre SAV.
    """)

    # 5. Signature du modèle
    from mlflow.models import infer_signature
    signature = infer_signature(X_test, predictions)
    mlflow.sklearn.log_model(model, "model", signature=signature)`;

  const HIGH_SNIPPET = `import mlflow
from mlflow.models import infer_signature

with mlflow.start_run():
    # ── 1. Niveau de risque ──────────────────────────────
    mlflow.set_tag("risk_level", "high")

    # ── 2. Métriques de performance complètes ────────────
    mlflow.log_metric("accuracy", 0.91)
    mlflow.log_metric("f1_score", 0.88)
    mlflow.log_metric("precision", 0.90)
    mlflow.log_metric("recall", 0.86)
    mlflow.log_metric("auc_roc", 0.95)
    # Métriques par sous-groupe (équité)
    mlflow.log_metric("f1_male", 0.89)
    mlflow.log_metric("f1_female", 0.87)
    mlflow.log_metric("demographic_parity_diff", 0.02)

    # ── 3. Paramètres détaillés ──────────────────────────
    mlflow.log_param("model_type", "xgboost")
    mlflow.log_param("n_estimators", 500)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("training_dataset", "credit_bureau_2024_v3")
    mlflow.log_param("training_samples", 150000)
    mlflow.log_param("feature_count", 42)

    # ── 4. Model card complète ───────────────────────────
    mlflow.set_tag("mlflow.note.content", """
# Model Card — Credit Scoring Model

## Description
Modèle de scoring crédit évaluant la solvabilité des
demandeurs de prêt personnel.

## Niveau de risque AI Act
Élevé (Art. 6, Annexe III §5a) — évaluation de la
solvabilité des personnes physiques.

## Usage prévu
### Objectif
Calculer un score de risque crédit (0-1000).
### Cas d'usage
Aide à la décision pour l'octroi de prêts personnels.
### Utilisateurs cibles
Analystes crédit de la banque de détail.
### Usages interdits
- Décision entièrement automatisée sans recours humain
- Utilisation sur des populations non représentées

## Données d'entraînement
Source : Bureau de crédit national, 150 000 dossiers.
Période : Jan 2022 — Dec 2024.
Variables sensibles exclues : origine ethnique, religion.
Prétraitement : imputation médiane, normalisation, SMOTE.

## Évaluation des performances et équité
AUC-ROC : 0.95, F1 global : 0.88
Analyse par genre : écart F1 < 2%.
Demographic parity difference : 0.02.

## Limites connues
- Performances dégradées pour les profils < 25 ans
- Non validé pour les prêts immobiliers

## Contrôle humain
Seuil de revue manuelle : score entre 400 et 600.
Kill switch : désactivation en < 5 min via dashboard.

## Explicabilité
SHAP values calculées pour chaque prédiction.
Top 5 features affichées à l'analyste.

## Robustesse
Tests adversariaux sur 10 000 échantillons perturbés.
Monitoring de data drift via PSI (seuil : 0.2).
    """)

    # ── 5. Signature du modèle ───────────────────────────
    signature = infer_signature(X_test, model.predict(X_test))
    mlflow.xgboost.log_model(model, "model", signature=signature)`;

  const SIMPLIFIED_CARD = `# Model Card — {model_name}

## Description
<!-- Décrivez brièvement ce que fait ce modèle -->

## Niveau de risque AI Act
Minimal — <!-- justification -->

## Usage prévu
<!-- But principal et utilisateurs cibles -->

## Données d'entraînement
<!-- Source et volume -->

## Limites connues
<!-- Limites principales -->`;

  // ── Tab content data ──────────────────────────────────────

  const TABS = [
    { id: 'minimal',       label: 'Minimal',       color: 'green' },
    { id: 'limited',       label: 'Limité',        color: 'yellow' },
    { id: 'high',          label: 'Élevé',         color: 'orange' },
    { id: 'unacceptable',  label: 'Inacceptable',  color: 'red' },
  ];

  // ── Render ────────────────────────────────────────────────

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Documentation</div>
            <h1 class="page-title">Guide de conformité</h1>
            <p class="cg-subtitle">Tout ce qu'un data scientist doit pousser vers MLflow pour rendre ses modèles conformes à l'AI Act.</p>
          </div>
        </div>

        <div class="page-content">

          <!-- Quick Start -->
          <div class="cg-quickstart">
            <div class="cg-quickstart__header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <h2>Quick Start — Critères plateforme</h2>
            </div>
            <div class="cg-quickstart__body">
              <div class="cg-checklist">
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Niveau de risque</strong> — tag <code>risk_level</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Model card</strong> — tag <code>mlflow.note.content</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Au moins une métrique</strong> — <code>mlflow.log_metric()</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Auteur</strong> — automatique via <code>mlflow.user</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--recommended">
                  <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
                  <span><strong>Paramètres</strong> — <code>mlflow.log_param()</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--recommended">
                  <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
                  <span><strong>Signature du modèle</strong> — <code>infer_signature()</code></span>
                </div>
              </div>
              <div class="cg-checklist__legend">
                <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span> Obligatoire
                <span class="cg-checklist__icon cg-checklist__icon--recommended" style="margin-left:16px">○</span> Recommandé (1 minimum pour statut "compliant")
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="cg-tabs" id="cg-tabs">
            ${TABS.map(t => `
              <button class="cg-tabs__btn cg-tabs__btn--${t.color}" data-tab="${t.id}">
                <span class="cg-tabs__dot cg-tabs__dot--${t.color}"></span>
                ${t.label}
              </button>
            `).join('')}
          </div>

          <!-- Tab content area with TOC -->
          <div class="cg-layout">
            <div class="cg-main" id="cg-main"></div>
            <nav class="cg-toc" id="cg-toc"></nav>
          </div>

        </div>
      </div>
    `;

    initTabs();
    activateTab('minimal');
  }

  // ── Tabs ──────────────────────────────────────────────────

  function initTabs() {
    document.querySelectorAll('.cg-tabs__btn').forEach(btn => {
      btn.addEventListener('click', () => activateTab(btn.dataset.tab));
    });
  }

  function activateTab(tabId) {
    document.querySelectorAll('.cg-tabs__btn').forEach(btn => {
      btn.classList.toggle('cg-tabs__btn--active', btn.dataset.tab === tabId);
    });
    const main = document.getElementById('cg-main');
    main.innerHTML = getTabContent(tabId);
    buildToc();
    initCopyButtons();
  }

  // ── TOC with scroll spy ───────────────────────────────────

  let tocObserver = null;

  function buildToc() {
    if (tocObserver) tocObserver.disconnect();

    const headings = document.querySelectorAll('#cg-main h3[id]');
    const toc = document.getElementById('cg-toc');

    if (!headings.length) { toc.innerHTML = ''; return; }

    toc.innerHTML = headings.length
      ? `<div class="cg-toc__title">Sur cette page</div>` +
        Array.from(headings).map(h =>
          `<a class="cg-toc__link" href="#${h.id}" data-target="${h.id}">${h.textContent}</a>`
        ).join('')
      : '';

    tocObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          document.querySelectorAll('.cg-toc__link').forEach(l => l.classList.remove('active'));
          const link = document.querySelector(`.cg-toc__link[data-target="${entry.target.id}"]`);
          if (link) link.classList.add('active');
        }
      });
    }, { rootMargin: '-80px 0px -60% 0px' });

    headings.forEach(h => tocObserver.observe(h));
  }

  // ── Copy buttons ──────────────────────────────────────────

  function initCopyButtons() {
    document.querySelectorAll('.cg-code__copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.closest('.cg-code').querySelector('code').textContent;
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = 'Copié !';
          setTimeout(() => { btn.textContent = 'Copier'; }, 2000);
        });
      });
    });

    document.querySelectorAll('.cg-template__copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const tpl = btn.dataset.template;
        const content = tpl === 'full' ? MODEL_CARD_TEMPLATE : SIMPLIFIED_CARD;
        navigator.clipboard.writeText(content).then(() => {
          btn.textContent = 'Copié !';
          setTimeout(() => { btn.textContent = 'Copier le template'; }, 2000);
        });
      });
    });
  }

  // ── Code block helper ─────────────────────────────────────

  function codeBlock(code, title = '') {
    const titleHtml = title ? `<div class="cg-code__title">${title}</div>` : '';
    const escaped = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return `
      <div class="cg-code">
        <div class="cg-code__header">
          ${titleHtml}
          <button class="cg-code__copy">Copier</button>
        </div>
        <pre><code>${escaped}</code></pre>
      </div>`;
  }

  function callout(type, content) {
    const icons = {
      info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
      warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      tip: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
      danger: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    };
    return `<div class="cg-callout cg-callout--${type}">${icons[type] || ''}<div>${content}</div></div>`;
  }

  // ── Tab content generators ────────────────────────────────

  function getTabContent(tabId) {
    switch (tabId) {
      case 'minimal':       return minimalContent();
      case 'limited':       return limitedContent();
      case 'high':          return highContent();
      case 'unacceptable':  return unacceptableContent();
      default:              return '';
    }
  }

  function minimalContent() {
    return `
      <h3 id="min-overview">Vue d'ensemble</h3>
      <p>Les systèmes d'IA à <strong>risque minimal</strong> ne sont soumis à aucune obligation spécifique de l'AI Act.
      Cependant, les critères de la plateforme restent nécessaires pour assurer la traçabilité et la qualité.</p>

      ${callout('info', '<strong>Exemples :</strong> filtres anti-spam, recommandation de contenu, optimisation logistique, jeux vidéo.')}

      <h3 id="min-obligations">Obligations AI Act</h3>
      <p>Aucune obligation réglementaire spécifique. Le fournisseur peut volontairement adhérer à des codes de conduite (Art. 95).</p>

      <h3 id="min-checklist">Checklist plateforme</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"minimal"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Model card (même simplifiée)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Au moins 1 métrique de performance</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Auteur identifié (automatique)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Paramètres du modèle</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Signature du modèle</span>
        </div>
      </div>

      <h3 id="min-code">Code snippet</h3>
      ${codeBlock(MINIMAL_SNIPPET, 'Enregistrement MLflow — Risque Minimal')}

      <h3 id="min-template">Template model card</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge">Simplifié</span>
          <span>Model card pour risque minimal</span>
        </div>
        <pre class="cg-template__preview">${SIMPLIFIED_CARD.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="simplified">Copier le template</button>
      </div>

      <h3 id="min-tips">Tips score LLM</h3>
      ${callout('tip', 'Même pour un modèle à risque minimal, une model card bien documentée améliorera votre score de review LLM. Visez au minimum une description claire et une justification du niveau de risque.')}
      <p>Pour un score ≥ 5/10 sur un modèle minimal, documentez au minimum :</p>
      <ul class="cg-list">
        <li>La classification du risque avec justification</li>
        <li>Une description de l'usage prévu</li>
        <li>Les métriques de performance principales</li>
      </ul>
    `;
  }

  function limitedContent() {
    return `
      <h3 id="lim-overview">Vue d'ensemble</h3>
      <p>Les systèmes d'IA à <strong>risque limité</strong> sont soumis à des <strong>obligations de transparence</strong> (Article 50).
      L'utilisateur doit être informé qu'il interagit avec un système d'IA.</p>

      ${callout('info', '<strong>Exemples :</strong> chatbots, systèmes de génération de contenu (texte, image, audio), deepfakes, systèmes de reconnaissance d\'émotions.')}

      <h3 id="lim-obligations">Obligations AI Act (Art. 50)</h3>
      <ul class="cg-list">
        <li><strong>Transparence envers l'utilisateur</strong> — informer clairement que le contenu est généré par IA ou que l'interaction est avec une IA</li>
        <li><strong>Marquage du contenu</strong> — les contenus générés (deepfakes, texte synthétique) doivent être identifiés comme tels</li>
        <li><strong>Information accessible</strong> — notification visible, compréhensible, dans la langue de l'utilisateur</li>
      </ul>

      <h3 id="lim-checklist">Checklist plateforme</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"limited"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Model card avec <strong>section Transparence</strong></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Au moins 1 métrique de performance</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Auteur identifié</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Paramètres du modèle</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Signature du modèle</span>
        </div>
      </div>
      ${callout('warning', 'Pour le risque limité, la model card <strong>doit inclure une section Transparence</strong> décrivant comment les utilisateurs sont informés qu\'ils interagissent avec une IA.')}

      <h3 id="lim-code">Code snippet</h3>
      ${codeBlock(LIMITED_SNIPPET, 'Enregistrement MLflow — Risque Limité')}

      <h3 id="lim-template">Template model card</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge cg-template__badge--limited">Limité</span>
          <span>Model card avec section transparence</span>
        </div>
        <pre class="cg-template__preview">${MODEL_CARD_TEMPLATE.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="full">Copier le template</button>
      </div>

      <h3 id="lim-tips">Tips score LLM</h3>
      <p>Pour un score ≥ 6/10 sur un modèle à risque limité :</p>
      <ul class="cg-list">
        <li>Classification du risque avec référence à l'Art. 50</li>
        <li>Section transparence détaillée (comment l'utilisateur est notifié)</li>
        <li>Description des données d'entraînement</li>
        <li>Métriques de performance documentées</li>
      </ul>
    `;
  }

  function highContent() {
    return `
      <h3 id="high-overview">Vue d'ensemble</h3>
      <p>Les systèmes d'IA à <strong>risque élevé</strong> (Art. 6, Annexe III) sont soumis à l'ensemble des exigences de conformité du règlement.
      La documentation doit être exhaustive et couvrir tous les aspects du cycle de vie du modèle.</p>

      ${callout('warning', '<strong>Domaines Annexe III</strong> concernés : identification biométrique, infrastructures critiques, éducation et formation, emploi et recrutement, accès aux services essentiels (crédit, assurance), forces de l\'ordre, migration et asile, justice.')}

      <h3 id="high-obligations">Obligations AI Act</h3>
      <ul class="cg-list">
        <li><strong>Système de gestion des risques</strong> (Art. 9) — identification, estimation et évaluation des risques</li>
        <li><strong>Données et gouvernance</strong> (Art. 10) — qualité, représentativité, détection de biais</li>
        <li><strong>Documentation technique</strong> (Art. 11) — description complète du système</li>
        <li><strong>Enregistrement des activités</strong> (Art. 12) — traçabilité des décisions</li>
        <li><strong>Transparence</strong> (Art. 13) — information des utilisateurs et des personnes concernées</li>
        <li><strong>Contrôle humain</strong> (Art. 14) — supervision effective par un humain</li>
        <li><strong>Exactitude et robustesse</strong> (Art. 15) — performance, résilience, cybersécurité</li>
        <li><strong>Surveillance post-déploiement</strong> (Art. 72) — monitoring continu</li>
      </ul>

      <h3 id="high-checklist">Checklist détaillée</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"high"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Model card <strong>complète</strong> (toutes les sections)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Métriques détaillées + métriques d'équité par sous-groupe</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Auteur identifié</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Paramètres complets (modèle + données + entraînement)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Signature du modèle (input/output schema)</span>
        </div>
      </div>

      <h3 id="high-code">Code snippet</h3>
      ${codeBlock(HIGH_SNIPPET, 'Enregistrement MLflow — Risque Élevé (complet)')}

      <h3 id="high-template">Template model card</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge cg-template__badge--high">Complet</span>
          <span>Model card pour risque élevé — toutes sections requises</span>
        </div>
        <pre class="cg-template__preview">${MODEL_CARD_TEMPLATE.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="full">Copier le template</button>
      </div>

      <h3 id="high-tips">Tips pour le score LLM</h3>
      <p>Le review LLM évalue votre model card sur <strong>9 critères</strong>. Voici comment maximiser chacun :</p>

      <div class="cg-criteria-grid">
        <div class="cg-criteria">
          <div class="cg-criteria__num">1</div>
          <div class="cg-criteria__body">
            <strong>Classification du risque</strong>
            <p>Justifiez avec une référence précise à l'Annexe III (ex : "§5a — évaluation de solvabilité"). Expliquez pourquoi l'usage prévu tombe dans cette catégorie.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">2</div>
          <div class="cg-criteria__body">
            <strong>Documentation technique (Art. 11)</strong>
            <p>Architecture du modèle, paramètres, métriques de performance, description des jeux de données. Plus c'est détaillé, mieux c'est.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">3</div>
          <div class="cg-criteria__body">
            <strong>Traçabilité (Art. 12)</strong>
            <p>Auteur identifié, versioning clair, run ID MLflow, lien vers le dépôt Git. La chaîne de responsabilité doit être identifiable.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">4</div>
          <div class="cg-criteria__body">
            <strong>Données et biais (Art. 10)</strong>
            <p>Description complète du dataset (source, volume, période). Plan d'atténuation des biais avec métriques d'équité par sous-groupe.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">5</div>
          <div class="cg-criteria__body">
            <strong>Transparence (Art. 13)</strong>
            <p>Instructions d'usage claires, limitations documentées, cas d'usage inappropriés listés. Les utilisateurs en aval doivent comprendre les risques.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">6</div>
          <div class="cg-criteria__body">
            <strong>Surveillance post-déploiement (Art. 72)</strong>
            <p>Plan de monitoring avec KPIs et seuils d'alerte. Décrivez la détection de drift (data drift, concept drift) et les procédures de mise à jour.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">7</div>
          <div class="cg-criteria__body">
            <strong>Mesures de conformité</strong>
            <p>Identifiez les lacunes restantes et les actions correctives requises avant déploiement.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">8</div>
          <div class="cg-criteria__body">
            <strong>Plan d'actions</strong>
            <p>Recommandations concrètes classées par priorité (critique / important / amélioration) avec un responsable et un livrable attendu.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">9</div>
          <div class="cg-criteria__body">
            <strong>Score de complétude</strong>
            <p>Chaque section bien documentée ≈ 1 point. Le LLM justifie sa note globale sur 10.</p>
          </div>
        </div>
      </div>

      ${callout('tip', '<strong>Pour atteindre 7/10</strong>, documentez au minimum : classification du risque avec justification Annexe III, documentation technique complète (architecture + métriques + données), description des données avec analyse de biais, et un plan de surveillance post-déploiement avec KPIs.')}
    `;
  }

  function unacceptableContent() {
    return `
      <h3 id="ua-overview">Vue d'ensemble</h3>
      <div class="cg-banner cg-banner--danger">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div>
          <strong>Déploiement interdit</strong>
          <p>Les systèmes d'IA à risque inacceptable sont interdits par l'Article 5 du règlement AI Act.
          La plateforme <strong>bloque automatiquement</strong> le déploiement de tout modèle classifié "inacceptable".</p>
        </div>
      </div>

      <h3 id="ua-practices">Pratiques interdites (Art. 5)</h3>
      <p>Les pratiques suivantes sont expressément interdites :</p>
      <ul class="cg-list cg-list--danger">
        <li><strong>Manipulation subliminale</strong> — techniques visant à altérer le comportement d'une personne de manière à causer un préjudice</li>
        <li><strong>Exploitation de vulnérabilités</strong> — ciblage de personnes vulnérables (âge, handicap, situation sociale)</li>
        <li><strong>Scoring social</strong> — notation des personnes basée sur leur comportement social ou caractéristiques personnelles, par ou pour les autorités publiques</li>
        <li><strong>Évaluation prédictive du risque criminel</strong> — basée uniquement sur le profilage ou les traits de personnalité</li>
        <li><strong>Scraping facial non ciblé</strong> — constitution de bases de données de reconnaissance faciale par collecte massive d'images</li>
        <li><strong>Reconnaissance des émotions</strong> — sur le lieu de travail ou dans les établissements d'éducation (sauf raisons médicales ou de sécurité)</li>
        <li><strong>Catégorisation biométrique</strong> — basée sur des données sensibles (origine, orientation sexuelle, opinions politiques, etc.)</li>
        <li><strong>Identification biométrique à distance en temps réel</strong> — dans les espaces publics à des fins répressives (exceptions très encadrées)</li>
      </ul>

      <h3 id="ua-platform">Comportement plateforme</h3>
      ${callout('danger', 'Lorsqu\'un modèle est classifié <code>risk_level = "unacceptable"</code>, la plateforme :<br>• Marque le statut de conformité comme <strong>non conforme</strong> automatiquement<br>• <strong>Bloque le déploiement</strong> (si la gate policy est activée)<br>• Aucune review LLM n\'est déclenchée')}

      <h3 id="ua-action">Que faire ?</h3>
      <p>Si vous pensez que votre modèle est classifié à tort comme "inacceptable" :</p>
      <ul class="cg-list">
        <li>Réévaluez l'usage prévu — l'interdiction porte sur l'<strong>usage</strong>, pas sur la technologie</li>
        <li>Vérifiez si une exception s'applique (Art. 5, paragraphes 2-4)</li>
        <li>Consultez votre responsable conformité ou DPO</li>
        <li>Si l'usage réel est différent, modifiez le tag <code>risk_level</code> avec la classification appropriée et mettez à jour la model card</li>
      </ul>
    `;
  }

  return { render };
})();
