(function () {
  function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => toast.classList.remove('is-visible'), 2500);
  }

  function request(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.CSRF_TOKEN,
      },
      body: JSON.stringify(body),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'حدث خطأ ما.');
      }
      return data;
    });
  }

  function addItem(variantId, quantity) {
    if (!variantId) {
      showToast('يرجى اختيار خيار أولاً.');
      return Promise.reject(new Error('لم يتم اختيار خيار'));
    }
    return request('/api/cart/add/', { variant_id: variantId, quantity: quantity })
      .then((data) => {
        const counter = document.getElementById('cart-count');
        if (counter) counter.textContent = data.total_items;
        showToast('تمت الإضافة إلى السلة.');
        return data;
      })
      .catch((err) => {
        showToast(err.message);
        throw err;
      });
  }

  function updateItem(itemId, quantity) {
    return request(`/api/cart/items/${itemId}/update/`, { quantity: quantity })
      .catch((err) => {
        showToast(err.message);
        throw err;
      });
  }

  function removeItem(itemId) {
    return request(`/api/cart/items/${itemId}/remove/`, {})
      .then((data) => {
        showToast('تمت إزالة المنتج.');
        return data;
      });
  }

  function applyCoupon(code) {
    return request('/api/cart/apply-coupon/', { code: code });
  }

  function removeCoupon() {
    return request('/api/cart/remove-coupon/', {})
      .then((data) => {
        showToast('تمت إزالة الكوبون.');
        return data;
      });
  }

  function formatPrice(value) {
    const amount = Math.round(parseFloat(value));
    return Number.isFinite(amount) ? amount.toLocaleString('ar-SD') : value;
  }

  window.CSRF_TOKEN = window.CSRF_TOKEN || (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '');

  window.EnjazCart = { addItem, updateItem, removeItem, applyCoupon, removeCoupon, showToast, formatPrice };

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-quick-add]');
    if (!btn || btn.disabled) return;
    e.preventDefault();

    const variantId = btn.dataset.variantId;
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = 'جارٍ الإضافة…';

    addItem(variantId, 1)
      .catch(() => {})
      .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      });
  });
})();
