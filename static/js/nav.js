(function () {
  const toggle = document.getElementById('nav-toggle');
  const nav = document.getElementById('site-nav');
  if (!toggle || !nav) return;

  function setOpen(isOpen) {
    nav.classList.toggle('is-open', isOpen);
    toggle.classList.toggle('is-active', isOpen);
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  toggle.addEventListener('click', function () {
    setOpen(!nav.classList.contains('is-open'));
  });

  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) {
      setOpen(false);
    }
  });

  window.matchMedia('(min-width: 901px)').addEventListener('change', function (e) {
    if (e.matches) setOpen(false);
  });
})();

(function () {
  const menu = document.getElementById('user-menu');
  const trigger = document.getElementById('user-menu-trigger');
  if (!menu || !trigger) return;

  function setOpen(isOpen) {
    menu.classList.toggle('is-open', isOpen);
    trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  trigger.addEventListener('click', function (e) {
    e.stopPropagation();
    setOpen(!menu.classList.contains('is-open'));
  });

  document.addEventListener('click', function (e) {
    if (!menu.contains(e.target)) setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
})();
