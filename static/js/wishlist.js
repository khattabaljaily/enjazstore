(function () {
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-wishlist-toggle]');
    if (!btn || btn.disabled) return;
    e.preventDefault();

    btn.disabled = true;
    fetch(btn.dataset.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then((res) => res.json())
      .then((data) => {
        btn.classList.toggle('is-active', data.in_wishlist);
        const svg = btn.querySelector('svg');
        if (svg) svg.setAttribute('fill', data.in_wishlist ? 'currentColor' : 'none');
        if (btn.dataset.activeLabel) {
          btn.innerHTML = data.in_wishlist ? btn.dataset.activeLabel : btn.dataset.inactiveLabel;
        }
        if (window.EnjazCart) {
          window.EnjazCart.showToast(data.in_wishlist ? 'تمت الإضافة إلى المفضلة.' : 'تمت الإزالة من المفضلة.');
        }
      })
      .finally(() => { btn.disabled = false; });
  });
})();
