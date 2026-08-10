(function () {
  document.querySelectorAll('[data-category-slider]').forEach(function (slider) {
    const track = slider.querySelector('[data-slider-track]');
    const prevBtn = slider.querySelector('[data-slider-prev]');
    const nextBtn = slider.querySelector('[data-slider-next]');
    if (!track || !prevBtn || !nextBtn) return;

    function updateState() {
      const maxScroll = track.scrollWidth - track.clientWidth;
      const atStart = track.scrollLeft <= 2;
      const atEnd = track.scrollLeft >= maxScroll - 2;
      slider.classList.toggle('is-at-start', atStart);
      slider.classList.toggle('is-at-end', atEnd);
      prevBtn.hidden = atStart;
      nextBtn.hidden = atEnd || maxScroll <= 0;
    }

    function scrollByPage(direction) {
      track.scrollBy({ left: direction * track.clientWidth * 0.8, behavior: 'smooth' });
    }

    prevBtn.addEventListener('click', function () { scrollByPage(-1); });
    nextBtn.addEventListener('click', function () { scrollByPage(1); });
    track.addEventListener('scroll', updateState, { passive: true });
    window.addEventListener('resize', updateState);

    updateState();
  });
})();
