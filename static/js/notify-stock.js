(function () {
  const overlay = document.getElementById('notify-modal-overlay');
  const form = document.getElementById('notify-modal-form');
  const emailInput = document.getElementById('notify-modal-email');
  if (!overlay || !form || !emailInput) return;

  let pendingTrigger = null;

  function openModal(trigger) {
    pendingTrigger = trigger;
    emailInput.value = '';
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    emailInput.focus();
  }

  function closeModal() {
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
    pendingTrigger = null;
  }

  function markSubscribed(trigger) {
    trigger.disabled = true;
    trigger.classList.add('is-subscribed');
    if (trigger.dataset.label) {
      trigger.textContent = 'أنت على قائمة الانتظار';
    } else {
      trigger.setAttribute('aria-label', 'أنت على قائمة الانتظار — سنُرسل لك بريدًا إلكترونيًا عند التوفر');
      trigger.setAttribute('title', 'أنت على قائمة الانتظار — سنُرسل لك بريدًا إلكترونيًا عند التوفر');
    }
  }

  function submitNotify(trigger, email) {
    const url = trigger.dataset.url;
    const body = new URLSearchParams();
    if (trigger.dataset.variant) body.set('variant', trigger.dataset.variant);
    if (email) body.set('email', email);

    trigger.disabled = true;
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': window.CSRF_TOKEN,
        'X-Requested-With': 'XMLHttpRequest',
      },
      body,
    })
      .then((res) => res.json())
      .then((data) => {
        if (window.EnjazCart) window.EnjazCart.showToast(data.message);
        if (data.success) {
          markSubscribed(trigger);
        } else {
          trigger.disabled = false;
        }
      })
      .catch(() => {
        trigger.disabled = false;
        if (window.EnjazCart) window.EnjazCart.showToast('حدث خطأ ما. حاول مرة أخرى.');
      });
  }

  document.addEventListener('click', function (e) {
    const trigger = e.target.closest('[data-notify-trigger]');
    if (trigger && !trigger.disabled) {
      e.preventDefault();
      if (window.ENJAZ_USER_EMAIL) {
        submitNotify(trigger, '');
      } else {
        openModal(trigger);
      }
      return;
    }
    if (e.target === overlay || e.target.closest('[data-notify-modal-close]')) {
      closeModal();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeModal();
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const email = emailInput.value.trim();
    const trigger = pendingTrigger;
    if (!email || !trigger) return;
    closeModal();
    submitNotify(trigger, email);
  });
})();
