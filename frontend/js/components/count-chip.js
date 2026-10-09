// Count chip — a quantity, not a status, so it never borrows a status badge.
// One component wherever the product shows how many models are deployed.
const CountChip = (() => {
  function deployed(deployedCount, total) {
    if (total === 0) {
      return `<span class="count-chip count-chip--empty" title="No model registered in this project">No models</span>`;
    }
    return `<span class="count-chip" title="${deployedCount} of ${total} model${total > 1 ? 's' : ''} deployed">`
      + `${deployedCount}<span class="count-chip__total">/${total}</span> deployed</span>`;
  }

  return { deployed };
})();
