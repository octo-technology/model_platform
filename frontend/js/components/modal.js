// Modal dialog system
const Modal = (() => {
  function open({ title, body, footer, onClose } = {}) {
    const overlay  = document.getElementById('modal-overlay');
    const container = document.getElementById('modal-container');

    overlay.classList.remove('hidden');

    container.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h2 class="modal-title">${title || ''}</h2>
          <button class="modal-close" id="modal-close-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">${body || ''}</div>
        ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
      </div>
    `;

    function close() {
      overlay.classList.add('hidden');
      container.innerHTML = '';
      if (onClose) onClose();
    }

    document.getElementById('modal-close-btn').addEventListener('click', close);
    overlay.addEventListener('click', close, { once: true });

    return { close };
  }

  function confirm({ title, message, confirmLabel = 'Confirm', danger = false }) {
    return new Promise(resolve => {
      const { close } = open({
        title,
        body: `<p style="color: var(--text-1); line-height:1.6;">${message}</p>`,
        footer: `
          <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
          <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="modal-confirm">${confirmLabel}</button>
        `,
        onClose: () => resolve(false),
      });

      document.getElementById('modal-cancel').addEventListener('click', () => { close(); resolve(false); });
      document.getElementById('modal-confirm').addEventListener('click', () => { close(); resolve(true); });
    });
  }

  return { open, confirm };
})();
