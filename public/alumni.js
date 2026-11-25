'use strict';

(() => {
  const track = document.getElementById('course-track');
  const filters = document.getElementById('course-filters');
  const previous = document.getElementById('course-prev');
  const next = document.getElementById('course-next');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');

  function updateArrows() {
    previous.disabled = track.scrollLeft < 2;
    next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
  }
  function scrollCourses(direction) {
    const card = track.querySelector('article:not([hidden])');
    if (!card) return;
    const step = card.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap);
    track.scrollBy({left: direction * step, behavior: motion.matches ? 'instant' : 'smooth'});
  }
  previous.addEventListener('click', () => scrollCourses(-1));
  next.addEventListener('click', () => scrollCourses(1));
  track.addEventListener('scroll', updateArrows, {passive: true});
  new ResizeObserver(updateArrows).observe(track);
  filters.addEventListener('click', event => {
    const active = event.target.closest('[data-profile]');
    if (!active) return;
    const profile = active.dataset.profile;
    let count = 0;
    for (const card of track.children) {
      card.hidden = Boolean(profile) && !card.dataset.profiles.split('|').includes(profile);
      if (!card.hidden) count++;
    }
    for (const button of filters.children) button.setAttribute('aria-pressed', String(button === active));
    document.getElementById('course-count').textContent = count + (count === 1 ? ' curso' : ' cursos');
    track.scrollTo({left: 0, behavior: 'instant'});
    updateArrows();
  });
})();
