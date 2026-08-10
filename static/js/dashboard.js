(function () {
  /* --------------------------------------------------------------------
     Product image dropzone + dynamic formset rows (product add/edit page)
     -------------------------------------------------------------------- */

  function previewFile(dropzone, file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      dropzone.style.backgroundImage = `url(${e.target.result})`;
      dropzone.classList.add('has-image');
    };
    reader.readAsDataURL(file);

    const row = dropzone.closest('[data-formset-row]');
    const filenameEl = row ? row.querySelector('.image-dropzone__filename') : null;
    if (filenameEl) filenameEl.textContent = file.name;
  }

  document.addEventListener('change', (e) => {
    if (e.target.matches('[data-formset="images"] input[name$="-is_primary"]') && e.target.checked) {
      document.querySelectorAll('[data-formset="images"] input[name$="-is_primary"]').forEach((checkbox) => {
        if (checkbox !== e.target) checkbox.checked = false;
      });
    }
  });

  function addFormsetRow(prefix) {
    const template = document.getElementById(`${prefix}-empty-form`);
    const container = document.querySelector(`[data-formset="${prefix}"]`);
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    if (!template || !container || !totalForms) return null;

    const index = parseInt(totalForms.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, index);
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html.trim();
    const row = wrapper.firstElementChild;
    container.appendChild(row);
    totalForms.value = index + 1;
    return row;
  }

  // Removing a formset row's DOM node isn't enough on its own: Django still
  // expects TOTAL_FORMS worth of "prefix-N-" fields on submit. Leaving a gap
  // makes it reconstruct a form for the missing index from blank/default
  // values, which can look "changed" (e.g. a stock field defaulting to 0
  // vs. a missing value) and fail required-field validation - the row then
  // reappears on the re-rendered page with "This field is required".
  // Renumbering the remaining rows keeps prefixes contiguous with
  // TOTAL_FORMS so no such phantom form ever gets built.
  function reindexFormset(prefix) {
    const container = document.querySelector(`[data-formset="${prefix}"]`);
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    if (!container || !totalForms) return;

    const rows = Array.from(container.querySelectorAll('[data-formset-row]'));
    const indexRe = new RegExp(`(${prefix}-)\\d+(-)`);
    rows.forEach((row, index) => {
      row.querySelectorAll('[name], [id], label[for]').forEach((el) => {
        if (el.hasAttribute('name')) {
          el.setAttribute('name', el.getAttribute('name').replace(indexRe, `$1${index}$2`));
        }
        if (el.hasAttribute('id')) {
          el.setAttribute('id', el.getAttribute('id').replace(indexRe, `$1${index}$2`));
        }
        if (el.hasAttribute('for')) {
          el.setAttribute('for', el.getAttribute('for').replace(indexRe, `$1${index}$2`));
        }
      });
    });
    totalForms.value = rows.length;
  }

  document.addEventListener('click', (e) => {
    const addBtn = e.target.closest('[data-add-row]');
    if (addBtn) {
      addFormsetRow(addBtn.dataset.addRow);
      return;
    }

    const removeBtn = e.target.closest('[data-remove-row]');
    if (removeBtn) {
      const row = removeBtn.closest('[data-formset-row]');
      const container = row ? row.closest('[data-formset]') : null;
      if (row) row.remove();
      if (container) reindexFormset(container.dataset.formset);
    }
  });

  /* --------------------------------------------------------------------
     Multi-file image upload: drop/select several photos at once and
     have each one fill its own formset row automatically.
     -------------------------------------------------------------------- */

  function findEmptyImageRow() {
    const rows = document.querySelectorAll('[data-formset="images"] [data-formset-row]');
    for (const row of rows) {
      const dropzone = row.querySelector('.image-dropzone');
      const input = row.querySelector('.image-dropzone input[type="file"]');
      if (dropzone && input && !input.files.length && !dropzone.classList.contains('has-image')) {
        return row;
      }
    }
    return null;
  }

  function assignFileToRow(row, file) {
    const dropzone = row.querySelector('.image-dropzone');
    const input = dropzone ? dropzone.querySelector('input[type="file"]') : null;
    if (!dropzone || !input) return;

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;
    previewFile(dropzone, file);
  }

  function handleMultipleImageFiles(fileList) {
    Array.from(fileList)
      .filter((file) => file.type.startsWith('image/'))
      .forEach((file) => {
        const row = findEmptyImageRow() || addFormsetRow('images');
        if (row) assignFileToRow(row, file);
      });
  }

  const multiDropzone = document.getElementById('images-multi-dropzone');
  const multiInput = document.getElementById('images-multi-input');

  if (multiDropzone && multiInput) {
    multiInput.addEventListener('change', () => {
      handleMultipleImageFiles(multiInput.files);
      multiInput.value = '';
    });

    multiDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      multiDropzone.classList.add('is-dragover');
    });

    multiDropzone.addEventListener('dragleave', () => {
      multiDropzone.classList.remove('is-dragover');
    });

    multiDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      multiDropzone.classList.remove('is-dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length) {
        handleMultipleImageFiles(e.dataTransfer.files);
      }
    });
  }

  /* --------------------------------------------------------------------
     Mobile sidebar drawer
     -------------------------------------------------------------------- */

  const hamburger = document.getElementById('dash-hamburger');
  const sidebar = document.getElementById('dash-sidebar');
  const sidebarBackdrop = document.getElementById('sidebar-backdrop');

  function openSidebar() {
    sidebar.classList.add('is-open');
    sidebarBackdrop.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('is-open');
    sidebarBackdrop.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  if (hamburger && sidebar && sidebarBackdrop) {
    hamburger.addEventListener('click', openSidebar);
    sidebarBackdrop.addEventListener('click', closeSidebar);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeSidebar();
    });
  }

  /* --------------------------------------------------------------------
     Modal system: AJAX-loaded forms, AJAX-submitted forms, confirm dialogs
     -------------------------------------------------------------------- */

  const overlay = document.getElementById('modal-overlay');
  const modalBody = document.getElementById('modal-body');
  const modalTitle = document.getElementById('modal-title');
  if (!overlay) return;

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function openModal(title) {
    modalTitle.textContent = title || '';
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    overlay.classList.remove('is-open');
    modalBody.innerHTML = '';
    document.body.style.overflow = '';
  }

  async function loadModalForm(url, title) {
    openModal(title);
    modalBody.innerHTML = '<p class="modal-loading">جارٍ التحميل…</p>';
    try {
      const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      modalBody.innerHTML = await res.text();
    } catch (err) {
      modalBody.innerHTML = '<p class="form-errors">تعذّر تحميل هذا النموذج. حاول مرة أخرى.</p>';
    }
  }

  function openConfirmModal(title, message, actionUrl, confirmLabel) {
    openModal(title);
    modalBody.innerHTML = `
      <p>${message}</p>
      <form data-modal-ajax-form action="${actionUrl}" method="post">
        <div class="form-actions">
          <button type="submit" class="btn btn-danger">${confirmLabel || 'نعم، متابعة'}</button>
          <button type="button" class="btn btn-outline" data-modal-close>إلغاء</button>
        </div>
      </form>`;
  }

  function setButtonLoading(btn, loadingLabel) {
    if (!btn) return null;
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-spinner"></span> ${loadingLabel}`;
    return originalHtml;
  }

  async function submitModalForm(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHtml = setButtonLoading(submitBtn, 'جارٍ الحفظ…');

    try {
      const res = await fetch(form.action || window.location.href, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: new FormData(form),
      });

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await res.json();
        if (data.success) {
          window.location.reload();
        } else {
          modalBody.innerHTML = `<p class="form-errors">${data.error || 'حدث خطأ ما.'}</p>
            <div class="form-actions"><button type="button" class="btn btn-outline" data-modal-close>إغلاق</button></div>`;
        }
      } else if (res.status >= 500) {
        // A genuine server error, not a validation re-render — surface it
        // instead of silently dumping a debug page into the modal.
        modalBody.innerHTML = `<p class="form-errors">حدث خطأ في الخادم (رمز الخطأ ${res.status}). حاول مرة أخرى.</p>
          <div class="form-actions"><button type="button" class="btn btn-outline" data-modal-close>إغلاق</button></div>`;
      } else {
        // Form re-rendered with validation errors
        modalBody.innerHTML = await res.text();
      }
    } catch (err) {
      modalBody.innerHTML = '<p class="form-errors">حدث خطأ ما. حاول مرة أخرى.</p>';
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHtml;
      }
    }
  }

  document.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('[data-modal-close]')) {
      closeModal();
      return;
    }

    const opener = e.target.closest('[data-modal-url]');
    if (opener && !opener.hasAttribute('data-modal-confirm')) {
      e.preventDefault();
      loadModalForm(opener.dataset.modalUrl, opener.dataset.modalTitle || '');
      return;
    }

    const confirmer = e.target.closest('[data-modal-confirm]');
    if (confirmer) {
      e.preventDefault();
      openConfirmModal(
        confirmer.dataset.modalTitle || 'هل أنت متأكد؟',
        confirmer.dataset.modalMessage || 'لا يمكن التراجع عن هذا الإجراء.',
        confirmer.dataset.modalUrl,
        confirmer.dataset.modalConfirmLabel,
      );
    }
  });

  document.addEventListener('submit', (e) => {
    if (e.target.closest('#modal-body')) {
      e.preventDefault();
      submitModalForm(e.target);
      return;
    }

    if (e.target.id === 'order-status-form') {
      setButtonLoading(e.target.querySelector('button[type="submit"]'), 'جارٍ الحفظ…');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeModal();
  });
})();
