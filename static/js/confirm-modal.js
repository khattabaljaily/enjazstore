(function () {
  const overlay = document.getElementById('confirm-modal-overlay');
  if (!overlay) return;

  const titleEl = document.getElementById('confirm-modal-title');
  const messageEl = document.getElementById('confirm-modal-message');
  const confirmBtn = document.getElementById('confirm-modal-confirm');
  let pendingForm = null;

  function openModal(title, message, confirmLabel) {
    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmLabel || 'Yes, continue';
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
    pendingForm = null;
  }

  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.hasAttribute('data-confirm-submit') || form.dataset.confirmed === 'true') return;

    e.preventDefault();
    pendingForm = form;
    openModal(
      form.dataset.confirmTitle || 'Are you sure?',
      form.dataset.confirmMessage || "This can't be undone.",
      form.dataset.confirmLabel,
    );
  });

  confirmBtn.addEventListener('click', function () {
    if (!pendingForm) return;
    const form = pendingForm;
    closeModal();
    form.dataset.confirmed = 'true';
    // form.submit() bypasses the 'submit' event entirely (per spec), so
    // spinner.js's global listener never sees this — trigger it directly.
    if (window.EnjazSpinner) window.EnjazSpinner.show();
    form.submit();
  });

  document.addEventListener('click', function (e) {
    if (e.target === overlay || e.target.closest('[data-confirm-modal-close]')) {
      closeModal();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeModal();
  });
})();
