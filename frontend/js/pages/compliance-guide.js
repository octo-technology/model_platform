// Philippe Stepniewski
// Compliance Guide — static reference page for data scientists
const ComplianceGuidePage = (() => {

  const MODEL_CARD_TEMPLATE = `# Model Card — {model_name}

## Description
<!-- Briefly describe what this model does -->

## AI Act Risk Level
<!-- unacceptable / high / limited / minimal -->
<!-- Justify your choice based on intended use and Annex III -->

## Intended Use
### Objective
<!-- Main purpose of the system -->
### Use Cases
<!-- Intended uses -->
### Target Users
<!-- Who uses this model -->
### Prohibited Uses
<!-- What the model must NOT do -->

## Training Data
<!-- Source, volume, period, language, personal data, preprocessing -->

## Performance Evaluation and Fairness
<!-- Evaluation results, bias analysis by subgroups -->

## Known Limitations
<!-- Technical limitations, validity domain, residual risks -->

## Human Oversight
<!-- Human supervision measures, alerts, kill switch, audit -->

## Explainability
<!-- Explainability methods used (SHAP, LIME…) -->

## Robustness
<!-- Robustness tests performed, out-of-distribution input handling -->`;

  const MINIMAL_SNIPPET = `import mlflow

with mlflow.start_run():
    # 1. Risk level (mandatory)
    mlflow.set_tag("risk_level", "minimal")

    # 2. Author (mandatory — automatic via mlflow.user)

    # 3. Metrics (mandatory — at least one)
    mlflow.log_metric("accuracy", 0.94)

    # 4. Model card (mandatory)
    mlflow.set_tag("mlflow.note.content", """
# Model Card — My Model
## Description
Simple classification model.
## AI Act Risk Level
Minimal — no direct impact on individuals.
    """)

    # 5. Parameters (recommended)
    mlflow.log_param("n_estimators", 100)

    # 6. Signature (recommended)
    from mlflow.models import infer_signature
    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, "model", signature=signature)`;

  const LIMITED_SNIPPET = `import mlflow

with mlflow.start_run():
    # 1. Risk level
    mlflow.set_tag("risk_level", "limited")

    # 2. Performance metrics
    mlflow.log_metric("accuracy", 0.92)
    mlflow.log_metric("f1_score", 0.89)

    # 3. Model parameters
    mlflow.log_param("model_type", "gradient_boosting")
    mlflow.log_param("n_estimators", 200)

    # 4. Model card with transparency section
    mlflow.set_tag("mlflow.note.content", """
# Model Card — My Model (Limited Risk)

## Description
Customer support chatbot using an NLP model.

## AI Act Risk Level
Limited (Art. 50) — AI system interacting with people.

## Intended Use
### Objective
Answer frequently asked customer questions.
### Target Users
After-sales service customers.
### Prohibited Uses
Must not make binding decisions.

## Transparency (Art. 50)
Users are informed they are interacting with an AI
via a visible banner on the interface.

## Training Data
History of 50,000 anonymized conversations (2023-2024).

## Known Limitations
Does not cover requests outside the after-sales scope.
    """)

    # 5. Model signature
    from mlflow.models import infer_signature
    signature = infer_signature(X_test, predictions)
    mlflow.sklearn.log_model(model, "model", signature=signature)`;

  const HIGH_SNIPPET = `import mlflow
from mlflow.models import infer_signature

with mlflow.start_run():
    # ── 1. Risk level ─────────────────────────────────
    mlflow.set_tag("risk_level", "high")

    # ── 2. Comprehensive performance metrics ──────────
    mlflow.log_metric("accuracy", 0.91)
    mlflow.log_metric("f1_score", 0.88)
    mlflow.log_metric("precision", 0.90)
    mlflow.log_metric("recall", 0.86)
    mlflow.log_metric("auc_roc", 0.95)
    # Subgroup fairness metrics
    mlflow.log_metric("f1_male", 0.89)
    mlflow.log_metric("f1_female", 0.87)
    mlflow.log_metric("demographic_parity_diff", 0.02)

    # ── 3. Detailed parameters ────────────────────────
    mlflow.log_param("model_type", "xgboost")
    mlflow.log_param("n_estimators", 500)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("training_dataset", "credit_bureau_2024_v3")
    mlflow.log_param("training_samples", 150000)
    mlflow.log_param("feature_count", 42)

    # ── 4. Complete model card ────────────────────────
    mlflow.set_tag("mlflow.note.content", """
# Model Card — Credit Scoring Model

## Description
Credit scoring model evaluating the creditworthiness
of personal loan applicants.

## AI Act Risk Level
High (Art. 6, Annex III §5a) — creditworthiness
assessment of natural persons.

## Intended Use
### Objective
Calculate a credit risk score (0-1000).
### Use Cases
Decision support for personal loan approval.
### Target Users
Retail banking credit analysts.
### Prohibited Uses
- Fully automated decisions without human recourse
- Use on unrepresented populations

## Training Data
Source: National credit bureau, 150,000 records.
Period: Jan 2022 — Dec 2024.
Sensitive variables excluded: ethnic origin, religion.
Preprocessing: median imputation, normalization, SMOTE.

## Performance Evaluation and Fairness
AUC-ROC: 0.95, Overall F1: 0.88
Gender analysis: F1 gap < 2%.
Demographic parity difference: 0.02.

## Known Limitations
- Degraded performance for profiles < 25 years old
- Not validated for mortgage loans

## Human Oversight
Manual review threshold: score between 400 and 600.
Kill switch: deactivation in < 5 min via dashboard.

## Explainability
SHAP values computed for each prediction.
Top 5 features displayed to the analyst.

## Robustness
Adversarial tests on 10,000 perturbed samples.
Data drift monitoring via PSI (threshold: 0.2).
    """)

    # ── 5. Model signature ────────────────────────────
    signature = infer_signature(X_test, model.predict(X_test))
    mlflow.xgboost.log_model(model, "model", signature=signature)`;

  const SIMPLIFIED_CARD = `# Model Card — {model_name}

## Description
<!-- Briefly describe what this model does -->

## AI Act Risk Level
Minimal — <!-- justification -->

## Intended Use
<!-- Main purpose and target users -->

## Training Data
<!-- Source and volume -->

## Known Limitations
<!-- Main limitations -->`;

  // ── Tab content data ──────────────────────────────────────

  const TABS = [
    { id: 'minimal',       label: 'Minimal',       color: 'green' },
    { id: 'limited',       label: 'Limited',        color: 'yellow' },
    { id: 'high',          label: 'High',           color: 'orange' },
    { id: 'unacceptable',  label: 'Unacceptable',   color: 'red' },
  ];

  // ── Render ────────────────────────────────────────────────

  function render(container) {
    container.innerHTML = `
      <div class="page-animate">
        <div class="page-header">
          <div class="page-title-group">
            <div class="page-eyebrow">Governance</div>
            <h1 class="page-title">Compliance Guide</h1>
            <p class="cg-subtitle">Everything a data scientist needs to push to MLflow to make their models AI Act compliant.</p>
          </div>
        </div>

        <div class="page-content">

          <!-- Quick Start -->
          <div class="cg-quickstart">
            <div class="cg-quickstart__header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <h2>Quick Start — Platform Criteria</h2>
            </div>
            <div class="cg-quickstart__body">
              <div class="cg-checklist">
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Risk level</strong> — tag <code>risk_level</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Model card</strong> — tag <code>mlflow.note.content</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>At least one metric</strong> — <code>mlflow.log_metric()</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--mandatory">
                  <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
                  <span><strong>Author</strong> — automatic via <code>mlflow.user</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--recommended">
                  <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
                  <span><strong>Parameters</strong> — <code>mlflow.log_param()</code></span>
                </div>
                <div class="cg-checklist__item cg-checklist__item--recommended">
                  <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
                  <span><strong>Model signature</strong> — <code>infer_signature()</code></span>
                </div>
              </div>
              <div class="cg-checklist__legend">
                <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span> Mandatory
                <span class="cg-checklist__icon cg-checklist__icon--recommended" style="margin-left:16px">○</span> Recommended (1 minimum for "compliant" status)
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
      ? `<div class="cg-toc__title">On this page</div>` +
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
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
        });
      });
    });

    document.querySelectorAll('.cg-template__copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const tpl = btn.dataset.template;
        const content = tpl === 'full' ? MODEL_CARD_TEMPLATE : SIMPLIFIED_CARD;
        navigator.clipboard.writeText(content).then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy template'; }, 2000);
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
          <button class="cg-code__copy">Copy</button>
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
      <h3 id="min-overview">Overview</h3>
      <p><strong>Minimal risk</strong> AI systems are not subject to any specific obligation under the AI Act.
      However, platform criteria remain necessary to ensure traceability and quality.</p>

      ${callout('info', '<strong>Examples:</strong> spam filters, content recommendation, logistics optimization, video games.')}

      <h3 id="min-obligations">AI Act Obligations</h3>
      <p>No specific regulatory obligation. The provider may voluntarily adhere to codes of conduct (Art. 95).</p>

      <h3 id="min-checklist">Platform Checklist</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"minimal"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Model card (even simplified)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>At least 1 performance metric</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Identified author (automatic)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Model parameters</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Model signature</span>
        </div>
      </div>

      <h3 id="min-code">Code snippet</h3>
      ${codeBlock(MINIMAL_SNIPPET, 'MLflow Registration — Minimal Risk')}

      <h3 id="min-template">Model card template</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge">Simplified</span>
          <span>Model card for minimal risk</span>
        </div>
        <pre class="cg-template__preview">${SIMPLIFIED_CARD.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="simplified">Copy template</button>
      </div>

      <h3 id="min-tips">LLM Score Tips</h3>
      ${callout('tip', 'Even for a minimal risk model, a well-documented model card will improve your LLM review score. At minimum, aim for a clear description and a risk level justification.')}
      <p>For a score ≥ 5/10 on a minimal model, document at minimum:</p>
      <ul class="cg-list">
        <li>Risk classification with justification</li>
        <li>A description of the intended use</li>
        <li>Key performance metrics</li>
      </ul>
    `;
  }

  function limitedContent() {
    return `
      <h3 id="lim-overview">Overview</h3>
      <p><strong>Limited risk</strong> AI systems are subject to <strong>transparency obligations</strong> (Article 50).
      Users must be informed that they are interacting with an AI system.</p>

      ${callout('info', '<strong>Examples:</strong> chatbots, content generation systems (text, image, audio), deepfakes, emotion recognition systems.')}

      <h3 id="lim-obligations">AI Act Obligations (Art. 50)</h3>
      <ul class="cg-list">
        <li><strong>Transparency to users</strong> — clearly inform that content is AI-generated or that the interaction is with an AI</li>
        <li><strong>Content marking</strong> — generated content (deepfakes, synthetic text) must be identified as such</li>
        <li><strong>Accessible information</strong> — visible, understandable notification in the user's language</li>
      </ul>

      <h3 id="lim-checklist">Platform Checklist</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"limited"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Model card with <strong>Transparency section</strong></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>At least 1 performance metric</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Identified author</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Model parameters</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Model signature</span>
        </div>
      </div>
      ${callout('warning', 'For limited risk, the model card <strong>must include a Transparency section</strong> describing how users are informed they are interacting with an AI.')}

      <h3 id="lim-code">Code snippet</h3>
      ${codeBlock(LIMITED_SNIPPET, 'MLflow Registration — Limited Risk')}

      <h3 id="lim-template">Model card template</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge cg-template__badge--limited">Limited</span>
          <span>Model card with transparency section</span>
        </div>
        <pre class="cg-template__preview">${MODEL_CARD_TEMPLATE.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="full">Copy template</button>
      </div>

      <h3 id="lim-tips">LLM Score Tips</h3>
      <p>For a score ≥ 6/10 on a limited risk model:</p>
      <ul class="cg-list">
        <li>Risk classification with reference to Art. 50</li>
        <li>Detailed transparency section (how the user is notified)</li>
        <li>Training data description</li>
        <li>Documented performance metrics</li>
      </ul>
    `;
  }

  function highContent() {
    return `
      <h3 id="high-overview">Overview</h3>
      <p><strong>High risk</strong> AI systems (Art. 6, Annex III) are subject to the full set of compliance requirements under the regulation.
      Documentation must be comprehensive and cover all aspects of the model lifecycle.</p>

      ${callout('warning', '<strong>Annex III domains</strong> covered: biometric identification, critical infrastructure, education and training, employment and recruitment, access to essential services (credit, insurance), law enforcement, migration and asylum, justice.')}

      <h3 id="high-obligations">AI Act Obligations</h3>
      <ul class="cg-list">
        <li><strong>Risk management system</strong> (Art. 9) — risk identification, estimation and evaluation</li>
        <li><strong>Data and governance</strong> (Art. 10) — quality, representativeness, bias detection</li>
        <li><strong>Technical documentation</strong> (Art. 11) — complete system description</li>
        <li><strong>Activity logging</strong> (Art. 12) — decision traceability</li>
        <li><strong>Transparency</strong> (Art. 13) — information for users and affected persons</li>
        <li><strong>Human oversight</strong> (Art. 14) — effective human supervision</li>
        <li><strong>Accuracy and robustness</strong> (Art. 15) — performance, resilience, cybersecurity</li>
        <li><strong>Post-deployment monitoring</strong> (Art. 72) — continuous monitoring</li>
      </ul>

      <h3 id="high-checklist">Detailed Checklist</h3>
      <div class="cg-checklist cg-checklist--compact">
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Tag <code>risk_level</code> = <code>"high"</code></span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span><strong>Complete</strong> model card (all sections)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Detailed metrics + fairness metrics by subgroup</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--mandatory">
          <span class="cg-checklist__icon cg-checklist__icon--mandatory">●</span>
          <span>Identified author</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Complete parameters (model + data + training)</span>
        </div>
        <div class="cg-checklist__item cg-checklist__item--recommended">
          <span class="cg-checklist__icon cg-checklist__icon--recommended">○</span>
          <span>Model signature (input/output schema)</span>
        </div>
      </div>

      <h3 id="high-code">Code snippet</h3>
      ${codeBlock(HIGH_SNIPPET, 'MLflow Registration — High Risk (complete)')}

      <h3 id="high-template">Model card template</h3>
      <div class="cg-template">
        <div class="cg-template__header">
          <span class="cg-template__badge cg-template__badge--high">Complete</span>
          <span>Model card for high risk — all sections required</span>
        </div>
        <pre class="cg-template__preview">${MODEL_CARD_TEMPLATE.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
        <button class="cg-template__copy" data-template="full">Copy template</button>
      </div>

      <h3 id="high-tips">LLM Score Tips</h3>
      <p>The LLM review evaluates your model card on <strong>9 criteria</strong>. Here's how to maximize each:</p>

      <div class="cg-criteria-grid">
        <div class="cg-criteria">
          <div class="cg-criteria__num">1</div>
          <div class="cg-criteria__body">
            <strong>Risk Classification</strong>
            <p>Justify with a precise reference to Annex III (e.g., "§5a — creditworthiness assessment"). Explain why the intended use falls under this category.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">2</div>
          <div class="cg-criteria__body">
            <strong>Technical Documentation (Art. 11)</strong>
            <p>Model architecture, parameters, performance metrics, dataset descriptions. The more detailed, the better.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">3</div>
          <div class="cg-criteria__body">
            <strong>Traceability (Art. 12)</strong>
            <p>Identified author, clear versioning, MLflow run ID, link to Git repository. The chain of responsibility must be identifiable.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">4</div>
          <div class="cg-criteria__body">
            <strong>Data and Bias (Art. 10)</strong>
            <p>Complete dataset description (source, volume, period). Bias mitigation plan with fairness metrics by subgroup.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">5</div>
          <div class="cg-criteria__body">
            <strong>Transparency (Art. 13)</strong>
            <p>Clear usage instructions, documented limitations, listed inappropriate use cases. Downstream users must understand the risks.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">6</div>
          <div class="cg-criteria__body">
            <strong>Post-deployment Monitoring (Art. 72)</strong>
            <p>Monitoring plan with KPIs and alert thresholds. Describe drift detection (data drift, concept drift) and update procedures.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">7</div>
          <div class="cg-criteria__body">
            <strong>Compliance Measures</strong>
            <p>Identify remaining gaps and corrective actions required before deployment.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">8</div>
          <div class="cg-criteria__body">
            <strong>Action Plan</strong>
            <p>Concrete recommendations ranked by priority (critical / important / improvement) with an owner and expected deliverable.</p>
          </div>
        </div>
        <div class="cg-criteria">
          <div class="cg-criteria__num">9</div>
          <div class="cg-criteria__body">
            <strong>Completeness Score</strong>
            <p>Each well-documented section ≈ 1 point. The LLM justifies its overall score out of 10.</p>
          </div>
        </div>
      </div>

      ${callout('tip', '<strong>To reach 7/10</strong>, document at minimum: risk classification with Annex III justification, complete technical documentation (architecture + metrics + data), data description with bias analysis, and a post-deployment monitoring plan with KPIs.')}
    `;
  }

  function unacceptableContent() {
    return `
      <h3 id="ua-overview">Overview</h3>
      <div class="cg-banner cg-banner--danger">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div>
          <strong>Deployment Prohibited</strong>
          <p>Unacceptable risk AI systems are prohibited under Article 5 of the AI Act regulation.
          The platform <strong>automatically blocks</strong> deployment of any model classified as "unacceptable".</p>
        </div>
      </div>

      <h3 id="ua-practices">Prohibited Practices (Art. 5)</h3>
      <p>The following practices are expressly prohibited:</p>
      <ul class="cg-list cg-list--danger">
        <li><strong>Subliminal manipulation</strong> — techniques aimed at altering a person's behavior in a way that causes harm</li>
        <li><strong>Exploitation of vulnerabilities</strong> — targeting vulnerable persons (age, disability, social situation)</li>
        <li><strong>Social scoring</strong> — rating persons based on their social behavior or personal characteristics, by or for public authorities</li>
        <li><strong>Predictive criminal risk assessment</strong> — based solely on profiling or personality traits</li>
        <li><strong>Untargeted facial scraping</strong> — building facial recognition databases through mass image collection</li>
        <li><strong>Emotion recognition</strong> — in the workplace or educational institutions (except for medical or safety reasons)</li>
        <li><strong>Biometric categorization</strong> — based on sensitive data (origin, sexual orientation, political opinions, etc.)</li>
        <li><strong>Real-time remote biometric identification</strong> — in public spaces for law enforcement purposes (very limited exceptions)</li>
      </ul>

      <h3 id="ua-platform">Platform Behavior</h3>
      ${callout('danger', 'When a model is classified <code>risk_level = "unacceptable"</code>, the platform:<br>• Automatically marks compliance status as <strong>non-compliant</strong><br>• <strong>Blocks deployment</strong> (if gate policy is enabled)<br>• No LLM review is triggered')}

      <h3 id="ua-action">What to Do?</h3>
      <p>If you believe your model is incorrectly classified as "unacceptable":</p>
      <ul class="cg-list">
        <li>Re-evaluate the intended use — the prohibition targets the <strong>use</strong>, not the technology</li>
        <li>Check if an exception applies (Art. 5, paragraphs 2-4)</li>
        <li>Consult your compliance officer or DPO</li>
        <li>If the actual use is different, update the <code>risk_level</code> tag with the appropriate classification and update the model card</li>
      </ul>
    `;
  }

  return { render };
})();
