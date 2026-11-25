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

  const stories = [...document.querySelectorAll('.campaign-slide')];
  const toggle = document.getElementById('slide-rotation');
  const number = document.getElementById('slide-count');
  let current = 0;
  let paused = motion.matches;
  let timer;
  function schedule() {
    clearTimeout(timer);
    if (!paused && !document.hidden) timer = setTimeout(() => show(1, false), 5000);
  }
  function show(direction, announce) {
    stories[current].hidden = true;
    current = (current + direction + stories.length) % stories.length;
    stories[current].hidden = false;
    number.textContent = [current + 1, stories.length].map(n => String(n).padStart(2, '0')).join(' / ');
    if (announce) document.getElementById('slide-status').textContent = stories[current].getAttribute('aria-label');
    schedule();
  }
  function setPaused(value) {
    paused = value;
    toggle.textContent = paused ? '▶' : 'Ⅱ';
    toggle.setAttribute('aria-label', paused ? 'Reanudar presentación' : 'Pausar presentación');
    schedule();
  }
  toggle.addEventListener('click', () => setPaused(!paused));
  document.getElementById('slide-prev').addEventListener('click', () => show(-1, true));
  document.getElementById('slide-next').addEventListener('click', () => show(1, true));
  const campaign = document.querySelector('.campaign');
  campaign.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    show(event.key === 'ArrowRight' ? 1 : -1, true);
  });
  let touchStart;
  campaign.addEventListener('touchstart', event => {
    touchStart = event.touches.length === 1 ? event.touches[0] : null;
  }, {passive: true});
  campaign.addEventListener('touchcancel', () => { touchStart = null; });
  campaign.addEventListener('touchend', event => {
    if (!touchStart) return;
    const dx = event.changedTouches[0].clientX - touchStart.clientX;
    const dy = event.changedTouches[0].clientY - touchStart.clientY;
    touchStart = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > 1.5 * Math.abs(dy)) show(dx < 0 ? 1 : -1, true);
  }, {passive: true});
  motion.addEventListener('change', event => setPaused(event.matches));
  document.addEventListener('visibilitychange', schedule);
  setPaused(paused);
})();
