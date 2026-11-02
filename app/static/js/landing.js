/* CampusBeacon landing: reveal, word scrub, chapters, parallax, count-up */
(function () {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // reveal on scroll
  const io = new IntersectionObserver((es) => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { threshold: .15, rootMargin: '0px 0px -6% 0px' });
  $$('.rv').forEach(el => io.observe(el));

  // split statement into words
  const st = document.querySelector('.statement p');
  if (st) {
    st.innerHTML = st.textContent.trim().split(/\s+/).map(w => `<span class="w">${w}</span>`).join(' ');
  }
  const words = $$('.statement .w');

  // chapters: highlight the one nearest viewport centre, swap the glass card
  const chaps = $$('.chap'), glass = $$('.glass');
  let active = -1;
  function setChapter(i) {
    if (i === active) return; active = i;
    chaps.forEach((c, k) => c.classList.toggle('on', k === i));
    glass.forEach((g, k) => g.classList.toggle('on', k === i));
  }

  // count-up
  const counters = $$('[data-count]');
  const cio = new IntersectionObserver((es) => es.forEach(e => {
    if (!e.isIntersecting) return; cio.unobserve(e.target);
    const el = e.target, end = +el.dataset.count, t0 = performance.now(), dur = 1600;
    const tick = t => { const p = Math.min(1, (t - t0) / dur), v = 1 - Math.pow(1 - p, 4);
      el.textContent = Math.round(end * v); if (p < 1) requestAnimationFrame(tick); };
    reduce ? (el.textContent = end) : requestAnimationFrame(tick);
  }), { threshold: .6 });
  counters.forEach(c => cio.observe(c));

  // one rAF loop for scroll-linked effects
  const blobs = $$('.blob'), hero = document.querySelector('.hero2 .wrap'), nav = document.querySelector('.lp-nav-in');
  let ticking = false;
  function frame() {
    ticking = false;
    const y = scrollY, vh = innerHeight;
    if (!reduce) {
      blobs.forEach((b, i) => b.style.translate = `0 ${y * (.08 + i * .05)}px`);
      if (hero && y < vh * 1.2) { hero.style.transform = `translateY(${y * .22}px) scale(${1 - Math.min(y / vh, 1) * .06})`; hero.style.opacity = 1 - Math.min(y / (vh * .75), 1); }
    }
    nav && nav.classList.toggle('scrolled', y > 40);
    // word scrub
    if (words.length) {
      const r = st.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, (vh * .85 - r.top) / (vh * .6 + r.height * .6)));
      const n = Math.floor(p * (words.length + 1));
      words.forEach((w, i) => w.classList.toggle('on', i < n));
    }
    // chapters
    if (chaps.length) {
      let best = 0, bd = 1e9;
      chaps.forEach((c, i) => { const r = c.getBoundingClientRect(), d = Math.abs(r.top + r.height / 2 - vh / 2); if (d < bd) { bd = d; best = i; } });
      setChapter(best);
    }
  }
  const req = () => { if (!ticking) { ticking = true; requestAnimationFrame(frame); } };
  addEventListener('scroll', req, { passive: true });
  addEventListener('resize', req);
  frame();
})();
