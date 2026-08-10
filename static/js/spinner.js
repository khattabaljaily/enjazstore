(function () {
  const loader = document.getElementById('enjaz-loader');
  if (!loader) return;

  let showTimer = null;

  function show() {
    clearTimeout(showTimer);
    showTimer = setTimeout(() => loader.classList.add('is-visible'), 150);
  }

  function hide() {
    clearTimeout(showTimer);
    loader.classList.remove('is-visible');
  }

  window.EnjazSpinner = { show, hide };

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

    const link = e.target.closest('a[href]');
    if (!link) return;
    if (link.closest('[data-no-spinner]')) return;
    if (link.target === '_blank' || link.hasAttribute('download')) return;

    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;

    show();
  });

  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.closest('#modal-body') || form.closest('[data-no-spinner]')) return;
    if (form.hasAttribute('data-confirm-submit') && form.dataset.confirmed !== 'true') return;

    show();
  });

  window.addEventListener('pageshow', hide);
})();
