(function setupPWAInstallPrompt() {
  var installPrompt = null;
  var isiOS = /iphone|ipad|ipod/.test(navigator.userAgent.toLowerCase());
  var promptShownKey = 'pwa_install_prompt_shown';
  var iOSPromptKey = 'ios_install_prompt_shown';
  var installedKey = 'pwa_installed';

  var downloadIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
  var shareIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>';
  var closeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

  function isAppAlreadyInstalled() {
    return window.navigator.standalone === true ||
      window.matchMedia('(display-mode: standalone)').matches ||
      localStorage.getItem(installedKey) === 'true';
  }

  if (isAppAlreadyInstalled()) return;

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    installPrompt = e;
    showInstallBanner('desktop');
  });

  if (isiOS) {
    var iosShown = sessionStorage.getItem(iOSPromptKey);
    if (!iosShown) {
      setTimeout(function () {
        showInstallBanner('ios');
        sessionStorage.setItem(iOSPromptKey, 'true');
      }, 3000);
    }
  }

  function showInstallBanner(type) {
    if (sessionStorage.getItem(promptShownKey + '_' + type)) return;

    var banner = document.createElement('div');
    banner.className = 'pwa-install-banner pwa-install-banner--' + type;
    banner.setAttribute('role', 'alert');
    banner.innerHTML = type === 'ios' ?
      '<div class="pwa-install-banner__content">' +
        '<div class="pwa-install-banner__icon">' + downloadIcon + '</div>' +
        '<div class="pwa-install-banner__text">' +
          '<div class="pwa-install-banner__title">تثبيت تطبيق إنجاز</div>' +
          '<div class="pwa-install-banner__description">اضغط ' + shareIcon + ' ثم "إضافة إلى الشاشة الرئيسية"</div>' +
        '</div>' +
        '<button type="button" class="pwa-install-banner__close" aria-label="إغلاق">' + closeIcon + '</button>' +
      '</div>' :
      '<div class="pwa-install-banner__content">' +
        '<div class="pwa-install-banner__icon">' + downloadIcon + '</div>' +
        '<div class="pwa-install-banner__text">' +
          '<div class="pwa-install-banner__title">تثبيت تطبيق إنجاز</div>' +
          '<div class="pwa-install-banner__description">ثبّت التطبيق على جهازك للوصول السريع</div>' +
        '</div>' +
        '<div class="pwa-install-banner__actions">' +
          '<button type="button" class="pwa-install-banner__btn pwa-install-banner__btn--primary" data-action="install">تثبيت</button>' +
          '<button type="button" class="pwa-install-banner__btn pwa-install-banner__btn--secondary" data-action="dismiss">إغلاق</button>' +
        '</div>' +
      '</div>';

    document.body.insertBefore(banner, document.body.firstChild);
    sessionStorage.setItem(promptShownKey + '_' + type, 'true');

    function dismiss() {
      banner.classList.add('pwa-install-banner--hidden');
      setTimeout(function () { banner.remove(); }, 300);
    }

    var closeBtn = banner.querySelector('.pwa-install-banner__close');
    if (closeBtn) closeBtn.addEventListener('click', dismiss);

    var installBtn = banner.querySelector('[data-action="install"]');
    var dismissBtn = banner.querySelector('[data-action="dismiss"]');

    if (installBtn) {
      installBtn.addEventListener('click', function () {
        if (!installPrompt) return;
        installPrompt.prompt();
        installPrompt.userChoice.then(function (choiceResult) {
          if (choiceResult.outcome === 'accepted') dismiss();
        });
      });
    }

    if (dismissBtn) dismissBtn.addEventListener('click', dismiss);

    setTimeout(function () {
      if (document.body.contains(banner)) dismiss();
    }, 10000);
  }

  window.addEventListener('appinstalled', function () {
    localStorage.setItem(installedKey, 'true');
    sessionStorage.removeItem(promptShownKey + '_desktop');
  });
})();
