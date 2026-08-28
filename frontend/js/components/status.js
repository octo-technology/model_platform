// Status vocabulary — one label and one colour per meaning, product-wide.
//
// Four tones carry every status: ok, warn, error, neutral. A word never
// means two things and a meaning never gets two colours, so `Running`
// and `Healthy` read the same because they say the same thing.
// AI Act risk keeps its own four-step scale: it is a severity ladder,
// not a health signal, and must not borrow the ok/warn/error colours.
const Status = (() => {
  // Deployment, job and simulation lifecycle.
  const RUNTIME = {
    running:    { label: 'Running',      tone: 'ok' },
    serving:    { label: 'Serving',      tone: 'ok' },
    deployed:   { label: 'Deployed',     tone: 'ok' },
    completed:  { label: 'Completed',    tone: 'ok' },
    succeeded:  { label: 'Succeeded',    tone: 'ok' },
    enabled:    { label: 'Enabled',      tone: 'ok' },
    active:     { label: 'Active',       tone: 'ok' },
    inactive:   { label: 'Inactive',     tone: 'neutral' },
    pending:    { label: 'Pending',      tone: 'warn' },
    starting:   { label: 'Starting',     tone: 'warn' },
    building:   { label: 'Building',     tone: 'warn' },
    queued:     { label: 'Queued',       tone: 'warn' },
    stopped:    { label: 'Stopped',      tone: 'neutral' },
    disabled:   { label: 'Disabled',     tone: 'neutral' },
    not_found:  { label: 'Not deployed', tone: 'neutral' },
    unknown:    { label: 'Unknown',      tone: 'neutral' },
    failed:     { label: 'Failed',       tone: 'error' },
    error:      { label: 'Error',        tone: 'error' },
  };

  // Runtime values arrive from several backends with their own spellings.
  const RUNTIME_ALIASES = [
    [/(^|_)(run|serv)/, 'running'],
    [/(pend|build|start|queu|progress)/, 'pending'],
    [/(fail|err|crash)/, 'failed'],
    [/(complet|success|succeed|done)/, 'completed'],
    [/(stop|terminat|not.?found|absent)/, 'stopped'],
  ];

  // Observed health of a served model.
  const HEALTH = {
    healthy: { label: 'Healthy', tone: 'ok' },
    caution: { label: 'Caution', tone: 'warn' },
    alert:   { label: 'Alert',   tone: 'error' },
    unknown: { label: 'Unknown', tone: 'neutral' },
  };

  // Governance verdict on a model version.
  const COMPLIANCE = {
    compliant:           { label: 'Compliant',     tone: 'ok' },
    partially_compliant: { label: 'Partial',       tone: 'warn' },
    non_compliant:       { label: 'Non-compliant', tone: 'error' },
    not_evaluated:       { label: 'Not evaluated', tone: 'neutral' },
  };

  // AI Act risk — a severity ladder with its own dedicated classes.
  const RISK = {
    minimal:      { label: 'Minimal',      cls: 'risk-minimal' },
    limited:      { label: 'Limited',      cls: 'risk-limited' },
    high:         { label: 'High',         cls: 'risk-high' },
    unacceptable: { label: 'Unacceptable', cls: 'risk-unacceptable' },
  };

  const SCALES = { runtime: RUNTIME, health: HEALTH, compliance: COMPLIANCE, risk: RISK };

  function normalize(kind, value) {
    const raw = String(value == null ? '' : value).trim().toLowerCase().replace(/[\s-]+/g, '_');
    if (SCALES[kind][raw]) return raw;
    if (kind !== 'runtime') return null;
    const alias = RUNTIME_ALIASES.find(([re]) => re.test(raw));
    return alias ? alias[1] : null;
  }

  // Returns { label, tone, cls } for a value, or null when it is unknown to
  // the scale — callers decide whether to fall back or show the raw value.
  function meta(kind, value) {
    const key = normalize(kind, value);
    if (!key) return null;
    const entry = SCALES[kind][key];
    return kind === 'risk'
      ? { label: entry.label, cls: entry.cls }
      : { label: entry.label, tone: entry.tone, cls: `badge-${entry.tone}` };
  }

  function escape(text) {
    return String(text).replace(/[&<>"']/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  }

  // One markup shape for every status badge in the product. The badge dot
  // and the label carry the meaning, so colour is never the only cue.
  function badge(kind, value, { label, title, extraClass = '' } = {}) {
    if (kind === 'risk') return riskBadge(value, label);
    const m = meta(kind, value);
    const text = label || (m ? m.label : (value || '—'));
    const cls = ['badge', m ? m.cls : 'badge-neutral', extraClass].filter(Boolean).join(' ');
    return `<span class="${cls}" title="${escape(title || text)}">${escape(text)}</span>`;
  }

  function riskBadge(level, label) {
    const m = meta('risk', level);
    if (!m) return `<span class="risk-badge risk-unknown" title="Risk level not set">${escape(label || level || '—')}</span>`;
    return `<span class="risk-badge ${m.cls}" title="AI Act risk — ${escape(m.label)}">${escape(label || m.label)}</span>`;
  }

  function label(kind, value) {
    const m = meta(kind, value);
    return m ? m.label : String(value || '—');
  }

  function tone(kind, value) {
    const m = meta(kind, value);
    return m && m.tone ? m.tone : 'neutral';
  }

  return { badge, riskBadge, meta, label, tone, RISK, HEALTH, RUNTIME, COMPLIANCE };
})();
