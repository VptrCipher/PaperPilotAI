// PaperPilot AI: brand-story runtime (DesignForge). Vanilla, no dependencies; destroy() is used by the React adapter.
function installBrandSite(doc) {
  var d = doc || document, w = window, html = d.documentElement;
  var offs = [], timers = [], observers = [], rafs = {};
  function on(t, ev, fn, o) { if (!t) return; t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function raf(key, fn) { if (rafs[key]) return; rafs[key] = w.requestAnimationFrame(function (t) { rafs[key] = 0; fn(t); }); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  var cache = {};
  function setVar(el, name, val, key) { var v = Math.round(val * 1000) / 1000; if (cache[key] === v) return; cache[key] = v; el.style.setProperty(name, String(v)); }
  function setClass(el, cls, onOff, key) { if (cache[key] === onOff) return; cache[key] = onOff; el.classList.toggle(cls, onOff); }
  var rmq = w.matchMedia('(prefers-reduced-motion: reduce)');
  var fine = w.matchMedia('(hover: hover) and (pointer: fine)');
  var reduced = rmq.matches;
  html.classList.add('bs-js');
  rafs.ready = w.requestAnimationFrame(function () { rafs.ready = 0; html.classList.add('bs-ready'); });

  /* Entrances: IntersectionObserver adds .in, then retires stagger delays */
  var reveals = [].slice.call(d.querySelectorAll('[data-reveal]'));
  var io = 'IntersectionObserver' in w ? new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('in'); io.unobserve(e.target);
      (function (el) { timers.push(setTimeout(function () { el.classList.add('settled'); }, 1700)); })(e.target);
    });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 }) : null;
  if (io) observers.push(io);
  function armReveals() { reveals.forEach(function (el) { if (!io || reduced) el.classList.add('in', 'settled'); else if (!el.classList.contains('in')) io.observe(el); }); }
  armReveals();

  /* Living elements run only on screen; everything pauses on hidden tabs */
  var lives = [].slice.call(d.querySelectorAll('[data-live]'));
  if ('IntersectionObserver' in w) {
    var lio = new IntersectionObserver(function (es) { es.forEach(function (e) { e.target.classList.toggle('is-live', e.isIntersecting); }); });
    lives.forEach(function (el) { lio.observe(el); }); observers.push(lio);
  } else lives.forEach(function (el) { el.classList.add('is-live'); });
  on(d, 'visibilitychange', function () { d.body.classList.toggle('paused', d.hidden); });

  /* Scroll-driven state: one rAF per scroll burst, delta-gated writes, rests when idle */
  var header = d.querySelector('[data-header]');
  var meter = d.querySelector('.bs-meter span');
  var words = d.querySelector('[data-words]');
  var paints = [].slice.call(d.querySelectorAll('[data-paint]'));
  var drawRoot = d.querySelector('[data-draw-root] .bs-steps-wrap');
  var steps = [].slice.call(d.querySelectorAll('[data-step]'));
  var plates = [].slice.call(d.querySelectorAll('[data-depth]'));
  function sectionProgress(el, startAt, span) {
    var r = el.getBoundingClientRect(), vh = w.innerHeight || 1;
    return clamp((vh * startAt - r.top) / (r.height + vh * span), 0, 1);
  }
  function onScrollFrame() {
    var y = w.scrollY || 0, max = Math.max(1, html.scrollHeight - w.innerHeight);
    if (header) setClass(header, 'is-scrolled', y > 24, 'hdr');
    if (meter) setVar(meter, '--sp', y / max, 'meter');
    if (scrubApi) scrubApi.onScroll();
    if (reduced) return;
    if (words) setVar(words, '--p', sectionProgress(words, 0.92, 0.1), 'words');
    paints.forEach(function (m, i) { var r = m.getBoundingClientRect(), vh = w.innerHeight || 1; setVar(m, '--pp', clamp((vh * 0.82 - r.top) / (vh * 0.3), 0, 1), 'paint' + i); });
    if (drawRoot) {
      var dp = sectionProgress(drawRoot, 0.85, -0.2);
      setVar(drawRoot, '--dp', dp, 'dp');
      steps.forEach(function (s, i) { setClass(s, 'is-lit', dp >= (i / Math.max(1, steps.length - 1)) * 0.92 + 0.02, 'step' + i); });
    }
    plates.forEach(function (p, i) {
      var r = p.parentElement.getBoundingClientRect(), vh = w.innerHeight;
      if (r.bottom < -100 || r.top > vh + 100) return;
      var c = (r.top + r.height / 2 - vh / 2) / vh;
      setVar(p, '--py', c * parseFloat(p.getAttribute('data-depth')) * -400, 'plate' + i);
    });
  }
  on(w, 'scroll', function () { raf('scroll', onScrollFrame); }, { passive: true });
  on(w, 'resize', function () { raf('scroll', onScrollFrame); }, { passive: true });
  onScrollFrame();

  /* Hero pointer parallax: eased toward the pointer, frame-rate independent, rests when converged */
  var hero = d.querySelector('[data-hero]');
  var tx = 0, ty = 0, cx = 0, cy = 0, last = 0;
  function heroTick(now) {
    var dt = Math.min(100, now - (last || now)); last = now;
    var k = 1 - Math.pow(1 - 0.09, dt / 16.667);
    cx += (tx - cx) * k; cy += (ty - cy) * k;
    setVar(hero, '--px', cx, 'px'); setVar(hero, '--py', cy, 'py');
    if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) raf('hero', heroTick); else last = 0;
  }
  if (hero) {
    on(hero, 'pointermove', function (e) { if (reduced || !fine.matches) return; var r = hero.getBoundingClientRect(); tx = ((e.clientX - r.left) / r.width - 0.5) * 2; ty = ((e.clientY - r.top) / r.height - 0.5) * 2; raf('hero', heroTick); });
    on(hero, 'pointerleave', function () { tx = 0; ty = 0; raf('hero', heroTick); });
  }

  /* Magnetic buttons (bounded 6px) */
  [].slice.call(d.querySelectorAll('[data-magnetic]')).forEach(function (b) {
    on(b, 'pointermove', function (e) { if (reduced || !fine.matches) return; var r = b.getBoundingClientRect(); b.style.setProperty('--mx', (((e.clientX - r.left) / r.width - 0.5) * 12).toFixed(2) + 'px'); b.style.setProperty('--my', (((e.clientY - r.top) / r.height - 0.5) * 10).toFixed(2) + 'px'); });
    on(b, 'pointerleave', function () { b.style.setProperty('--mx', '0px'); b.style.setProperty('--my', '0px'); });
  });

  /* Card spotlight + bounded tilt (5deg) */
  [].slice.call(d.querySelectorAll('[data-tilt]')).forEach(function (card) {
    on(card, 'pointermove', function (e) {
      if (!fine.matches) return;
      var r = card.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      card.style.setProperty('--sx', (x * 100).toFixed(1) + '%'); card.style.setProperty('--sy', (y * 100).toFixed(1) + '%');
      if (reduced) return;
      card.classList.add('is-tilting');
      card.style.setProperty('--ry', ((x - 0.5) * 8).toFixed(2) + 'deg'); card.style.setProperty('--rx', ((0.5 - y) * 6).toFixed(2) + 'deg');
    });
    on(card, 'pointerleave', function () { card.classList.remove('is-tilting'); card.style.setProperty('--rx', '0deg'); card.style.setProperty('--ry', '0deg'); });
  });

  /* Counters: count up once on view, final value under reduced motion */
  var counters = [].slice.call(d.querySelectorAll('[data-count]'));
  function setCount(el, v) { var s = String(Math.round(v)); if (el.textContent !== s) el.textContent = s; }
  if ('IntersectionObserver' in w && !reduced) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return; cio.unobserve(e.target);
        var el = e.target, to = Number(el.getAttribute('data-count')), t0 = 0;
        if (reduced) { setCount(el, to); return; }
        function step(t) { t0 = t0 || t; var k = clamp((t - t0) / 1300, 0, 1); setCount(el, to * (1 - Math.pow(1 - k, 3))); if (k < 1) raf('count' + to, step); }
        setCount(el, 0); raf('count' + to, step);
      });
    });
    counters.forEach(function (c) { cio.observe(c); }); observers.push(cio);
  }

  /* The interactive moment: press-and-hold builds, early release eases back, completion lights the content */
  var holdRoot = d.querySelector('[data-hold-root]'), holdBtn = d.querySelector('[data-hold]');
  var status = d.getElementById('moment-status');
  var hp = 0, holding = false, done = false, hLast = 0, pinnedHold = false;
  function holdState(s) { if (holdRoot && holdRoot.getAttribute('data-state') !== s) holdRoot.setAttribute('data-state', s); }
  function complete() {
    done = true; holding = false; hp = 1; setVar(holdRoot, '--hp', 1, 'hp'); holdState('complete');
    if (status) status.textContent = status.getAttribute('data-done') || 'Done.';
  }
  function holdTick(now) {
    var dt = Math.min(64, now - (hLast || now)); hLast = now;
    hp = holding ? hp + dt / 1400 : hp - dt / 900;
    if (hp >= 1) { complete(); hLast = 0; return; }
    if (!holding && hp <= 0) { hp = 0; setVar(holdRoot, '--hp', 0, 'hp'); holdState('idle'); hLast = 0; return; }
    if (hp < 0) hp = 0;
    setVar(holdRoot, '--hp', hp, 'hp');
    raf('hold', holdTick);
  }
  function startHold() { if (done) return; if (reduced) { complete(); return; } holding = true; holdState('holding'); raf('hold', holdTick); }
  function endHold() { if (!holding) return; holding = false; if (!done) { holdState('releasing'); raf('hold', holdTick); } }
  if (holdRoot && holdBtn) {
    on(holdBtn, 'pointerdown', function (e) { if (e.button !== 0) return; try { holdBtn.setPointerCapture(e.pointerId); } catch (err) {} startHold(); });
    on(holdBtn, 'pointerup', endHold); on(holdBtn, 'pointercancel', endHold); on(holdBtn, 'lostpointercapture', endHold);
    on(holdBtn, 'keydown', function (e) { if (e.repeat) return; if (e.key === 'Enter') { e.preventDefault(); complete(); } else if (e.key === ' ') { e.preventDefault(); startHold(); } });
    on(holdBtn, 'keyup', function (e) { if (e.key === ' ') endHold(); });
    on(holdBtn, 'click', function (e) { if (reduced || e.detail === 0) complete(); });
    on(holdBtn, 'contextmenu', function (e) { e.preventDefault(); });
  }

  /* Form: validation, loading, success; never claims to have sent anything it did not */
  var form = d.getElementById('primary-cta-form'), email = d.getElementById('cta-email'), submit = d.getElementById('cta-submit'), fb = d.getElementById('cta-feedback');
  if (form && email && submit && fb) {
    on(form, 'submit', function (ev) {
      ev.preventDefault();
      var value = String(email.value || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        email.setAttribute('aria-invalid', 'true'); fb.setAttribute('data-state', 'error');
        fb.textContent = 'Please enter a valid email, like name@example.com.'; email.focus(); return;
      }
      email.removeAttribute('aria-invalid'); submit.disabled = true;
      fb.setAttribute('data-state', 'loading'); fb.textContent = 'Sending...';
      timers.push(setTimeout(function () {
        submit.disabled = false; fb.setAttribute('data-state', 'success');
        fb.textContent = form.getAttribute('data-success') || 'Thank you.'; form.reset();
      }, 60));
    });
  }

  /* Scroll-scrubbed hero for supplied footage (10k-websites scrub standard). Blob-streamed behind an honest ring,
     lerped displayed time that rests, gated seeks, caption bands paced in scroll distance, five static gates decided live. */
  var scrubHero = d.querySelector('[data-scrub]');
  var scrubApi = null;
  if (scrubHero) {
    var GATES = ["(max-width: 720px)","(orientation: portrait) and (max-width: 1024px)","(orientation: portrait) and (pointer: coarse)","(orientation: landscape) and (pointer: coarse) and (max-height: 560px)","(prefers-reduced-motion: reduce)"];
    var sTrack = scrubHero.querySelector('[data-scrub-track]');
    var sVideo = scrubHero.querySelector('video');
    var sPoster = scrubHero.querySelector('.bs-poster');
    var VIDEO_URL = scrubHero.getAttribute('data-video'), VIDEO_BYTES = parseInt(scrubHero.getAttribute('data-video-bytes') || '0', 10), POSTER_URL = scrubHero.getAttribute('data-poster');
    var bands = [].slice.call(scrubHero.querySelectorAll('[data-band]')).map(function (el) { var r = el.getAttribute('data-band').split(','); return { el: el, a: parseFloat(r[0]), b: parseFloat(r[1]) }; });
    var sTarget = 0, sShown = 0, sLast = 0, sOnScreen = true, seekBusy = false, pendingTime = null, sStarted = false, scrubOn = false;
    function sProgress() { var r = sTrack.getBoundingClientRect(); return clamp(-r.top / Math.max(1, r.height - w.innerHeight), 0, 1); }
    function smooth(p, e0, e1) { var t = clamp((p - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); }
    function updateBands(p) {
      bands.forEach(function (bd, i) {
        var f = Math.min(0.02, (bd.b - bd.a) / 3);
        var up = i === 0 ? 1 : smooth(p, bd.a, bd.a + f);
        var down = i === bands.length - 1 ? 1 : 1 - smooth(p, bd.b - f, bd.b);
        var op = up * down;
        var k = i === 0 ? 1 : clamp((p - bd.a) / Math.min(0.025, (bd.b - bd.a) * 0.35), 0, 1);
        setVar(bd.el, '--bo', op, 'bo' + i); setVar(bd.el, '--k', k, 'bk' + i); setClass(bd.el, 'is-on', op > 0.5, 'bon' + i);
      });
    }
    function requestSeek(t) {
      if (!sVideo.duration) return;
      if (seekBusy) { pendingTime = t; return; }
      seekBusy = true; sVideo.currentTime = t;
    }
    on(sVideo, 'seeked', function () { seekBusy = false; if (pendingTime !== null) { var t = pendingTime; pendingTime = null; requestSeek(t); } });
    on(sVideo, 'error', function () { seekBusy = false; pendingTime = null; if (sVideo.getAttribute('src')) failVideo(); });
    function sTick(now) {
      var dt = Math.min(100, now - (sLast || now)); sLast = now;
      sShown += (sTarget - sShown) * (1 - Math.pow(1 - 0.16, dt / 16.667));
      if (Math.abs(sTarget - sShown) < 0.0005) { sShown = sTarget; sLast = 0; } else if (sOnScreen) raf('scrub', sTick);
      requestSeek(sShown * (sVideo.duration || 0)); updateBands(sShown);
    }
    function failVideo() { scrubHero.classList.add('video-failed'); }
    function setRing(frac) { setVar(scrubHero, '--ld', 126 * (1 - frac), 'ld'); }
    function loadHeroBlob() {
      var ctrl = new AbortController(), dog = setTimeout(function () { ctrl.abort(); }, 20000);
      return fetch(VIDEO_URL, { priority: 'low', signal: ctrl.signal }).then(function (res) {
        if (!res.ok) throw new Error('video ' + res.status);
        var total = Number(res.headers.get('Content-Length')) || VIDEO_BYTES;
        if (!res.body || !res.body.getReader) return res.blob().then(function (b) { clearTimeout(dog); setRing(1); return b; });
        var reader = res.body.getReader(), chunks = [], got = 0, lastRing = 0;
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) { clearTimeout(dog); setRing(1); return new Blob(chunks, { type: /\.webm$/i.test(VIDEO_URL) ? 'video/webm' : 'video/mp4' }); }
            clearTimeout(dog); dog = setTimeout(function () { ctrl.abort(); }, 20000);
            chunks.push(r.value); got += r.value.length;
            var now = performance.now(), frac = total ? Math.min(1, got / total) : 0;
            if (now - lastRing > 100 || frac === 1) { lastRing = now; setRing(frac); }
            return pump();
          });
        }
        return pump();
      }).then(function (blob) {
        sVideo.src = URL.createObjectURL(blob); sVideo.load();
        sVideo.addEventListener('canplay', function () {
          sTarget = sShown = sProgress(); requestSeek(sShown * sVideo.duration); updateBands(sShown);
          scrubHero.classList.add('video-ready');
        }, { once: true });
      });
    }
    function startBlobFetch() { if (sStarted) return; sStarted = true; loadHeroBlob().catch(failVideo); }
    function initHeroOnce() {
      // Poster first, then the blob: the poster wins the bandwidth race. Only ever runs on the scrub path.
      if (!POSTER_URL) { startBlobFetch(); return; }
      sPoster.style.backgroundImage = "url('" + POSTER_URL + "')";
      var img = new Image(); img.onload = startBlobFetch; img.onerror = startBlobFetch; img.src = POSTER_URL;
      timers.push(setTimeout(startBlobFetch, 4000));
    }
    function clearBandCache() { Object.keys(cache).forEach(function (k) { if (/^b(o|k|on)\d/.test(k)) delete cache[k]; }); }
    function enableScrub() {
      if (scrubOn) return; scrubOn = true;
      scrubHero.classList.remove('is-static'); initHeroOnce(); clearBandCache();
      sTarget = sShown = sProgress(); updateBands(sShown);
      if (sVideo.duration) requestSeek(sShown * sVideo.duration);
    }
    function disableScrub() {
      var was = scrubOn; scrubOn = false;
      scrubHero.classList.add('is-static');
      if (rafs.scrub) { w.cancelAnimationFrame(rafs.scrub); rafs.scrub = 0; }
      sLast = 0;
      if (was) clearBandCache();
    }
    var mqls = GATES.map(function (q) { return w.matchMedia(q); }); // kept referenced so listeners survive
    function applyHeroMode() { if (mqls.some(function (m) { return m.matches; })) disableScrub(); else enableScrub(); }
    mqls.forEach(function (m) { on(m, 'change', applyHeroMode); });
    if ('IntersectionObserver' in w) {
      var sio = new IntersectionObserver(function (es) { es.forEach(function (e) { sOnScreen = e.isIntersecting; if (sOnScreen && scrubOn) { sTarget = sProgress(); raf('scrub', sTick); } }); });
      sio.observe(sTrack); observers.push(sio);
    }
    // Keyboard users: focusing a caption control that is not on screen scrolls the journey to that caption.
    bands.forEach(function (bd) {
      on(bd.el, 'focusin', function () {
        if (!scrubOn) return;
        var r = sTrack.getBoundingClientRect(), range = Math.max(1, r.height - w.innerHeight), mid = (bd.a + bd.b) / 2, p = sProgress();
        if (p < bd.a || p > bd.b) w.scrollTo(0, w.scrollY + r.top + mid * range);
      });
    });
    scrubApi = { onScroll: function () { if (!scrubOn) return; sTarget = sProgress(); if (sOnScreen) raf('scrub', sTick); } };
    applyHeroMode();
  }

  /* Poster Signal: a perspective grid floor bent by the pointer, decorative agent cursors that select headings,
     and a cursor swarm in the close. Each loop runs only on screen, rests on hidden tabs, and stops under reduced motion. */
  var poster = (function () {
    var floor = d.querySelector('[data-backdrop]'), kind = floor ? floor.getAttribute('data-backdrop') : '', agentsRoot = d.querySelector('[data-agents]'), swarm = d.querySelector('[data-swarm]');
    var running = false, floorOn = false, swarmOn = false, accent = '#ff2d2d';
    function readAccent() { var v = w.getComputedStyle(html).getPropertyValue('--accent-primary').trim(); if (v) accent = v; readGlows(); }
    function fit(cv) { var r = Math.min(w.devicePixelRatio || 1, 1.5), cw = cv.clientWidth, ch = cv.clientHeight; if (cv.width !== Math.round(cw * r) || cv.height !== Math.round(ch * r)) { cv.width = Math.round(cw * r); cv.height = Math.round(ch * r); } return r; }

    /* Floor */
    var fctx = floor ? floor.getContext('2d') : null, phase = 0, fLast = 0, bend = 0, bendT = 0, fpx = 0.5, fpy = 0.5;
    /* Other backdrop kinds share the floor's loop, pointer and visibility gate. */
    var glowA = '#888', glowB = '#444', dots = null;
    function readGlows() { var cs = w.getComputedStyle(html); glowA = cs.getPropertyValue('--glow-a').trim() || accent; glowB = cs.getPropertyValue('--glow-b').trim() || accent; }
    function seedDots(n) { var s = 7, out = []; function rnd() { s = (s * 16807) % 2147483647; return s / 2147483647; } for (var i = 0; i < n; i++) out.push({ x: rnd(), y: rnd(), vx: (rnd() - 0.5) * 0.00005, vy: (rnd() - 0.5) * 0.00005 }); return out; }
    function drawParticles(now, W, H, r) {
      if (!dots) dots = seedDots(Math.min(140, Math.round(W * H / (r * r * 9000)) + 40));
      var px = fpx * W, py = fpy * H, reach = Math.min(W, H) * 0.32, link = Math.min(W, H) * 0.14, i, j, a, b, dx, dy, dd;
      fctx.fillStyle = accent; fctx.strokeStyle = accent; fctx.lineWidth = r;
      for (i = 0; i < dots.length; i++) { a = dots[i]; a.x = (a.x + a.vx * 16 + 1) % 1; a.y = (a.y + a.vy * 16 + 1) % 1; }
      for (i = 0; i < dots.length; i++) {
        a = dots[i]; var ax = a.x * W, ay = a.y * H, pd = Math.hypot(ax - px, ay - py), near = Math.max(0, 1 - pd / reach);
        fctx.globalAlpha = 0.25 + near * 0.65; fctx.beginPath(); fctx.arc(ax, ay, (1.3 + near * 1.6) * r, 0, 6.283); fctx.fill();
        if (near <= 0) continue;
        for (j = i + 1; j < dots.length; j++) {
          b = dots[j]; dx = ax - b.x * W; dy = ay - b.y * H; dd = Math.hypot(dx, dy);
          if (dd < link) { fctx.globalAlpha = near * (1 - dd / link) * 0.6; fctx.beginPath(); fctx.moveTo(ax, ay); fctx.lineTo(b.x * W, b.y * H); fctx.stroke(); }
        }
      }
    }
    function drawWaves(now, W, H, r) {
      var lines = 16, i, x;
      fctx.lineWidth = 1.2 * r;
      for (i = 0; i < lines; i++) {
        var f = i / (lines - 1), y0 = H * (0.3 + 0.62 * f);
        fctx.strokeStyle = i % 4 === 0 ? glowB : accent; fctx.globalAlpha = 0.12 + 0.5 * f;
        fctx.beginPath();
        for (x = 0; x <= W; x += W / 64) {
          var dx = (x - fpx * W) / (W * 0.14), bump = Math.exp(-dx * dx) * (8 + bend * 34) * r * (1 - Math.abs(f - fpy));
          var y = y0 + Math.sin(x / (W * 0.11) + now * 0.0007 + i * 0.45) * 10 * r * (0.4 + f) - bump;
          if (x === 0) fctx.moveTo(x, y); else fctx.lineTo(x, y);
        }
        fctx.stroke();
      }
    }
    function drawOrbits(now, W, H, r) {
      var cxp = W * (0.5 + (fpx - 0.5) * 0.08), cyp = H * (0.58 + (fpy - 0.5) * 0.06), k, j, tilt = 0.3 + (fpy - 0.5) * 0.12;
      for (k = 0; k < 7; k++) {
        var rx = Math.min(W, H * 1.8) * (0.09 + k * 0.075), ry = rx * tilt, rot = now * 0.00004 * (k % 2 ? 1 : -1);
        fctx.strokeStyle = k % 3 === 0 ? glowB : accent; fctx.globalAlpha = 0.5 - k * 0.055; fctx.lineWidth = r;
        fctx.beginPath(); fctx.ellipse(cxp, cyp, rx, ry, rot, 0, 6.283); fctx.stroke();
        for (j = 0; j < 3; j++) {
          var a = now * 0.00025 * (1 + k * 0.15) + j * 2.094 + k, ex = Math.cos(a) * rx, ey = Math.sin(a) * ry;
          var qx = cxp + ex * Math.cos(rot) - ey * Math.sin(rot), qy = cyp + ex * Math.sin(rot) + ey * Math.cos(rot);
          fctx.globalAlpha = 0.85; fctx.fillStyle = accent; fctx.beginPath(); fctx.arc(qx, qy, (2 + (k % 3)) * r, 0, 6.283); fctx.fill();
        }
      }
    }
    function drawMatrix(now, W, H, r) {
      var gap = 26 * r, x, y, px = fpx * W, py = fpy * H, reach = Math.min(W, H) * 0.28;
      fctx.fillStyle = accent;
      for (y = gap / 2; y < H; y += gap) for (x = gap / 2; x < W; x += gap) {
        var d = Math.hypot(x - px, y - py), near = Math.exp(-(d * d) / (reach * reach)), ripple = Math.sin(d / (14 * r) - now * 0.004) * 0.5 + 0.5;
        var s = (0.8 + near * (2.4 + bend * 1.6) + ripple * near * 1.2) * r;
        fctx.globalAlpha = 0.16 + near * 0.7 + (y / H) * 0.12;
        fctx.fillRect(x - s / 2, y - s / 2, s, s);
      }
    }
    function drawAurora(now, W, H, r) {
      var k, x, cols3 = [accent, glowA, glowB];
      fctx.lineCap = 'round';
      for (k = 0; k < 3; k++) {
        fctx.strokeStyle = cols3[k]; fctx.globalAlpha = 0.16; fctx.lineWidth = H * (0.09 + k * 0.03);
        fctx.beginPath();
        for (x = -W * 0.1; x <= W * 1.1; x += W / 40) {
          var dx = (x - fpx * W) / (W * 0.25), lift = Math.exp(-dx * dx) * H * 0.05 * (0.3 + bend);
          var y = H * (0.42 + k * 0.14) + Math.sin(x / (W * 0.22) + now * 0.00025 * (k + 1) + k * 1.7) * H * 0.08 - lift;
          if (x <= -W * 0.1) fctx.moveTo(x, y); else fctx.lineTo(x, y);
        }
        fctx.stroke();
      }
      fctx.lineCap = 'butt';
    }
    function drawFloor(now) {
      if (!fctx) return;
      if (kind !== 'grid-floor') {
        var r0 = fit(floor), W0 = floor.width, H0 = floor.height;
        fctx.clearRect(0, 0, W0, H0);
        if (kind === 'particle-field') drawParticles(now, W0, H0, r0); else if (kind === 'wave-lines') drawWaves(now, W0, H0, r0); else if (kind === 'orbit-rings') drawOrbits(now, W0, H0, r0); else if (kind === 'dot-matrix') drawMatrix(now, W0, H0, r0); else drawAurora(now, W0, H0, r0);
        fctx.globalAlpha = 1;
        return;
      }
      var r = fit(floor), W = floor.width, H = floor.height, cx = W / 2 + (hero ? (cx0() * W * 0.04) : 0);
      fctx.clearRect(0, 0, W, H);
      fctx.strokeStyle = accent; fctx.lineWidth = Math.max(1, r);
      var cols = 22, near = W / 9, i, x, k;
      // One gradient and one path for all converging lines: a single stroke per frame.
      var g = fctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.45, accent); g.addColorStop(1, accent);
      fctx.globalAlpha = 0.62; fctx.strokeStyle = g; fctx.beginPath();
      for (i = -cols; i <= cols; i++) { x = cx + i * near; fctx.moveTo(cx + i * near * 0.04, 0); fctx.lineTo(x, H); }
      fctx.stroke();
      fctx.strokeStyle = accent;
      var rows = 18;
      for (k = 0; k < rows; k++) {
        var t = (k + phase) / rows, depth = Math.pow(t, 2.2), y = depth * H;
        fctx.globalAlpha = Math.min(0.7, 0.04 + depth * 0.8);
        fctx.beginPath();
        for (x = 0; x <= W; x += W / 48) {
          var dx = (x - fpx * W) / (W * 0.16), lift = Math.exp(-dx * dx) * bend * 26 * r * depth;
          if (x === 0) fctx.moveTo(x, y - lift); else fctx.lineTo(x, y - lift);
        }
        fctx.stroke();
      }
      fctx.globalAlpha = 1;
    }
    function cx0() { return parseFloat(hero.style.getPropertyValue('--px')) || 0; }
    function floorTick(now) {
      var dt = Math.min(64, now - (fLast || now)); fLast = now;
      phase = (phase + dt * 0.00035) % 1;
      bend += (bendT - bend) * (1 - Math.pow(0.9, dt / 16.667)); bendT *= Math.pow(0.97, dt / 16.667);
      drawFloor(now);
      if (running && floorOn && !d.hidden) raf('floor', floorTick); else fLast = 0;
    }
    if (floor && hero) on(hero, 'pointermove', function (e) { var b = floor.getBoundingClientRect(); fpx = clamp((e.clientX - b.left) / (b.width || 1), 0, 1); fpy = clamp((e.clientY - b.top) / (b.height || 1), 0, 1); bendT = 1; });

    /* Agents */
    var agents = agentsRoot ? [].slice.call(agentsRoot.querySelectorAll('.ps-agent')) : [], box = agentsRoot ? agentsRoot.querySelector('[data-select-box]') : null;
    var state = [], aLast = 0, selTarget = null, selUntil = 0, nextAgent = 0, t0 = 0;
    function seedAgents() {
      var narrow = w.innerWidth < 700 || !fine.matches, count = Math.min(narrow ? 2 : 3, agents.length);
      state = agents.slice(0, count).map(function (el, i) { el.style.display = ''; return { el: el, x: w.innerWidth * (0.2 + 0.6 * ((i * 0.37) % 1)), y: w.innerHeight * (0.3 + 0.4 * ((i * 0.53) % 1)), seed: i * 17.3 + 3.1, task: null }; });
      agents.slice(count).forEach(function (el) { el.style.display = 'none'; });
    }
    // Text the cursors must never sit on: refreshed at most every 400ms (layout reads stay cheap).
    var avoid = [], avoidAt = 0;
    var avoidSel = 'h1, h2, h3, p, li, .bs-btn, .bs-cta-row, .ps-card, .bs-chip, .bs-input';
    function refreshAvoid(now) {
      if (now - avoidAt < 400) return; avoidAt = now; avoid = [];
      var H = w.innerHeight;
      [].slice.call(d.querySelectorAll('main ' + avoidSel.split(', ').join(', main '))).forEach(function (el) {
        if (el.closest('[aria-hidden="true"]')) return;
        var r = el.getBoundingClientRect();
        if (r.width && r.bottom > -40 && r.top < H + 40) avoid.push({ l: r.left - 24, t: r.top - 30, r: r.right + 24, b: r.bottom + 30 });
      });
    }
    function clear(x, y, s) {
      var wdt = (s.el.offsetWidth || 90) + 8, hgt = (s.el.offsetHeight || 30) + 8;
      for (var i = 0; i < avoid.length; i++) { var a = avoid[i]; if (x + wdt > a.l && x < a.r && y + hgt > a.t && y < a.b) return false; }
      return true;
    }
    function wander(s, t) {
      var W = w.innerWidth, H = w.innerHeight;
      var u = (Math.sin(t * 0.00013 + s.seed) + Math.sin(t * 0.00031 + s.seed * 2.1) * 0.5) / 1.5;
      var v = (Math.cos(t * 0.00017 + s.seed * 1.3) + Math.sin(t * 0.00023 + s.seed) * 0.5) / 1.5;
      var maxX = W - (s.el.offsetWidth || 90) - 8;
      var p = { x: Math.min(W * (0.5 + u * 0.46), maxX), y: H * (0.5 + v * 0.42) };
      if (clear(p.x, p.y, s)) return p;
      // Nearest free spot: try the margins left and right of the content first, then above and below.
      var tries = [[W * 0.04, p.y], [maxX, p.y], [p.x, H * 0.12], [p.x, H * 0.88], [W * 0.04, H * 0.15], [maxX, H * 0.85]];
      for (var k = 0; k < tries.length; k++) if (clear(tries[k][0], tries[k][1], s)) return { x: tries[k][0], y: tries[k][1] };
      return { x: maxX, y: H * 0.9 };
    }
    function agentTick(now) {
      t0 = t0 || now;
      refreshAvoid(now);
      var t = now - t0;
      state.forEach(function (s) {
        var tg = s.task && now < s.task.until ? s.task : wander(s, t);
        if (s.task && now >= s.task.until) s.task = null;
        s.x += (tg.x - s.x) * (s.task ? 0.09 : 0.03); s.y += (tg.y - s.y) * (s.task ? 0.09 : 0.03);
        s.el.style.transform = 'translate3d(' + s.x.toFixed(1) + 'px,' + s.y.toFixed(1) + 'px,0)';
      });
      if (box) {
        if (selTarget && now < selUntil) {
          var r = selTarget.getBoundingClientRect();
          box.style.transform = 'translate3d(' + (r.left - 10).toFixed(1) + 'px,' + (r.top - 8).toFixed(1) + 'px,0)';
          box.style.width = (r.width + 20).toFixed(1) + 'px'; box.style.height = (r.height + 16).toFixed(1) + 'px';
          setClass(box, 'is-on', true, 'selbox');
        } else setClass(box, 'is-on', false, 'selbox');
      }
      if (running && !d.hidden) raf('agents', agentTick); else aLast = 0;
    }
    var selIo = null;
    if (agentsRoot && 'IntersectionObserver' in w) {
      selIo = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting || !running || !state.length) return;
          selIo.unobserve(e.target);
          var i = nextAgent++ % state.length, s = state[i], el = agents[i], r = e.target.getBoundingClientRect();
          var colour = el.style.getPropertyValue('--ac');
          if (box) { box.style.setProperty('--sel', colour); var lab = box.querySelector('span'); if (lab) lab.textContent = el.querySelector('span') ? el.querySelector('span').textContent : ''; }
          selTarget = e.target; selUntil = w.performance.now() + 1900;
          s.task = { x: Math.min(r.right - 6, w.innerWidth - (el.offsetWidth || 90) - 8), y: r.bottom - 4, until: selUntil - 300 };
        });
      }, { rootMargin: '-25% 0px -35% 0px' });
      [].slice.call(d.querySelectorAll('[data-select]')).forEach(function (h) { selIo.observe(h); });
      observers.push(selIo);
    }

    /* Swarm */
    var sctx = swarm ? swarm.getContext('2d') : null, parts = [], spx = 0.5, spy = 0.5, sLast = 0;
    var cols = ['#ffd23f', '#3df5a0', '#c4a8ff', '#7fd8ff', '#ff9ad5'];
    function seedSwarm() { parts = []; for (var i = 0; i < 70; i++) parts.push({ a: (i / 70) * Math.PI * 2, r: 0.12 + (i % 7) * 0.035, x: 0.5, y: 0.5, vx: 0, vy: 0, c: i % 5 === 0 ? accent : cols[i % cols.length], s: 0.7 + (i % 3) * 0.18 }); }
    function drawSwarm(now) {
      if (!sctx) return;
      var r = fit(swarm), W = swarm.width, H = swarm.height, m = Math.min(W, H);
      sctx.clearRect(0, 0, W, H);
      parts.forEach(function (p) {
        var a = p.a + now * 0.0004 * (p.s > 0.9 ? -1 : 1);
        var tx = spx + Math.cos(a) * p.r * (1 + Math.sin(now * 0.001 + p.a * 3) * 0.12) * m / W, ty = spy + Math.sin(a) * p.r * 0.8 * m / H;
        p.vx += (tx - p.x) * 0.012; p.vy += (ty - p.y) * 0.012; p.vx *= 0.9; p.vy *= 0.9; p.x += p.vx; p.y += p.vy;
        sctx.save(); sctx.translate(p.x * W, p.y * H); sctx.rotate(Math.atan2(p.vy, p.vx) - Math.PI / 4); sctx.scale(p.s * r, p.s * r);
        sctx.beginPath(); sctx.moveTo(0, 0); sctx.lineTo(0, 12); sctx.lineTo(3.2, 9.2); sctx.lineTo(5.6, 14); sctx.lineTo(7.6, 13.1); sctx.lineTo(5.4, 8.4); sctx.lineTo(9.6, 8.3); sctx.closePath();
        sctx.fillStyle = p.c; sctx.fill(); sctx.restore();
      });
    }
    function swarmTick(now) { drawSwarm(now); if (running && swarmOn && !d.hidden) raf('swarm', swarmTick); }
    if (swarm) {
      var host = swarm.parentElement;
      on(host, 'pointermove', function (e) { var b = swarm.getBoundingClientRect(); spx = (e.clientX - b.left) / (b.width || 1); spy = (e.clientY - b.top) / (b.height || 1); });
      on(host, 'pointerleave', function () { spx = 0.5; spy = 0.5; });
      on(host, 'pointerdown', function () { parts.forEach(function (p) { var dx = p.x - spx, dy = p.y - spy, dd = Math.hypot(dx, dy) || 1; p.vx += dx / dd * 0.05; p.vy += dy / dd * 0.05; }); });
    }

    /* Cursor follower (trail ring, follow dot or spotlight), fine pointers only. */
    var follower = d.querySelector('[data-cursor]'), cfx = 0, cfy = 0, ctx2 = 0, cty2 = 0, cShown = false;
    function cursorTick() {
      cfx += (ctx2 - cfx) * 0.2; cfy += (cty2 - cfy) * 0.2;
      follower.style.transform = 'translate3d(' + cfx.toFixed(1) + 'px,' + cfy.toFixed(1) + 'px,0)';
      if (running && (Math.abs(ctx2 - cfx) > 0.3 || Math.abs(cty2 - cfy) > 0.3)) raf('cursor', cursorTick);
    }
    if (follower) on(w, 'pointermove', function (e) {
      if (!running || !fine.matches) return;
      ctx2 = e.clientX; cty2 = e.clientY;
      if (!cShown) { cfx = ctx2; cfy = cty2; cShown = true; follower.classList.add('is-on'); }
      var t = e.target; setClass(follower, 'is-hot', !!(t && t.closest && t.closest('a,button,input,[data-tilt]')), 'curhot');
      raf('cursor', cursorTick);
    }, { passive: true });

    /* Headline scramble: characters resolve left to right; the accessible text is the sr-only copy. */
    var scrWords = d.querySelector('[data-g-headline="scramble"]') ? [].slice.call(d.querySelectorAll('.bs-hero .bs-word-in')) : [];
    scrWords.forEach(function (el) { el.setAttribute('data-final', el.textContent); });
    var scrambled = false;
    function scramble() {
      if (scrambled || !scrWords.length) return; scrambled = true;
      var glyphs = '#%&*+=?/<>01ABCDEFKXYZ';
      scrWords.forEach(function (el, i) {
        var fin = el.getAttribute('data-final') || '', t0 = 0, dur = 650 + i * 110;
        // Lock the word's box so substituted glyphs never reflow the line (no layout shift).
        el.style.width = el.getBoundingClientRect().width + 'px'; el.style.whiteSpace = 'nowrap'; el.style.overflow = 'hidden'; el.style.verticalAlign = 'top';
        function step(t) {
          t0 = t0 || t;
          var k = clamp((t - t0) / dur, 0, 1), n = Math.floor(fin.length * k), s = fin.slice(0, n), c;
          for (c = n; c < fin.length; c++) s += glyphs.charAt(Math.floor(Math.random() * glyphs.length));
          el.textContent = k < 1 ? s : fin;
          if (k < 1 && running) raf('scr' + i, step); else { el.textContent = fin; el.style.width = ''; el.style.whiteSpace = ''; el.style.overflow = ''; el.style.verticalAlign = ''; }
        }
        raf('scr' + i, step);
      });
    }
    function unscramble() { scrWords.forEach(function (el) { el.textContent = el.getAttribute('data-final') || el.textContent; el.style.width = ''; el.style.whiteSpace = ''; el.style.overflow = ''; el.style.verticalAlign = ''; }); }

    /* Scroll-driven 3D: sections rotate into place, or hero layers separate with scroll. */
    var gRoot = d.querySelector('[data-g-depth]'), depthKind = gRoot ? gRoot.getAttribute('data-g-depth') : '';
    var depthSecs = depthKind === 'scroll-rotate' ? [].slice.call(d.querySelectorAll('.bs-section')) : [];
    function depthFrame() {
      if (!running) return;
      var vh = w.innerHeight || 1;
      depthSecs.forEach(function (s, i) { var r = s.getBoundingClientRect(); setVar(s, '--enter', clamp((vh - r.top) / (vh * 0.55), 0, 1), 'enter' + i); });
      if (depthKind === 'parallax-layers' && hero) setVar(hero, '--hy', Math.min(w.scrollY || 0, vh * 1.5), 'hy');
    }
    if (depthSecs.length || depthKind === 'parallax-layers') on(w, 'scroll', function () { raf('depth', depthFrame); }, { passive: true });
    function depthRest() { depthSecs.forEach(function (s) { s.style.setProperty('--enter', '1'); }); if (hero) hero.style.setProperty('--hy', '0'); }

    /* Visibility gates */
    if ('IntersectionObserver' in w) {
      var vio = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.target === floor) { floorOn = e.isIntersecting; if (floorOn && running) raf('floor', floorTick); }
          if (e.target === swarm) { swarmOn = e.isIntersecting; if (swarmOn && running) raf('swarm', swarmTick); }
        });
      });
      if (floor) vio.observe(floor); if (swarm) vio.observe(swarm); observers.push(vio);
    } else { floorOn = true; swarmOn = true; }
    on(d, 'visibilitychange', function () { if (!d.hidden && running) { if (floorOn) raf('floor', floorTick); if (swarmOn) raf('swarm', swarmTick); if (state.length) raf('agents', agentTick); } });
    on(w, 'resize', function () { if (!running) { drawFloor(0); drawSwarm(0); } });

    // Reduced motion: one finished frame, particles placed on their rings, no loops.
    function stillFrame() { readAccent(); seedSwarm(); var W = swarm ? swarm.clientWidth || 1 : 1, H = swarm ? swarm.clientHeight || 1 : 1, m = Math.min(W, H); parts.forEach(function (p) { p.x = 0.5 + Math.cos(p.a) * p.r * m / W; p.y = 0.5 + Math.sin(p.a) * p.r * 0.8 * m / H; p.vx = Math.cos(p.a + 1.6) * 0.001; p.vy = Math.sin(p.a + 1.6) * 0.001; }); drawSwarm(0); bend = 0; drawFloor(0); }
    return {
      start: function () {
        readAccent(); seedSwarm(); running = true;
        if (agentsRoot) { seedAgents(); agentsRoot.classList.add('is-on'); raf('agents', agentTick); }
        if (floorOn) raf('floor', floorTick); if (swarmOn) raf('swarm', swarmTick);
        if (!floorOn) drawFloor(0);
        scramble(); depthFrame();
      },
      stop: function () {
        running = false; if (agentsRoot) agentsRoot.classList.remove('is-on'); if (box) box.classList.remove('is-on');
        if (follower) follower.classList.remove('is-on');
        unscramble(); depthRest();
        stillFrame();
      },
    };
  })();
  if (reduced) poster.stop(); else poster.start();

  /* Product stage: tab groups (request routing, quick-start platform) with full keyboard support, and copy buttons. */
  [].slice.call(d.querySelectorAll('[data-tabs]')).forEach(function (group) {
    var tabs = [].slice.call(group.querySelectorAll('[role="tab"]'));
    var panels = [].slice.call(group.querySelectorAll('[role="tabpanel"]'));
    function select(i, focus) {
      tabs.forEach(function (t, k) {
        var isOn = k === i;
        t.setAttribute('aria-selected', isOn ? 'true' : 'false'); t.tabIndex = isOn ? 0 : -1;
        if (panels[k]) panels[k].hidden = !isOn;
      });
      if (focus) tabs[i].focus();
    }
    tabs.forEach(function (t, i) {
      on(t, 'click', function () { select(i, false); });
      on(t, 'keydown', function (e) {
        var n = tabs.length, k = e.key;
        if (k === 'ArrowRight' || k === 'ArrowDown') { e.preventDefault(); select((i + 1) % n, true); }
        else if (k === 'ArrowLeft' || k === 'ArrowUp') { e.preventDefault(); select((i - 1 + n) % n, true); }
        else if (k === 'Home') { e.preventDefault(); select(0, true); }
        else if (k === 'End') { e.preventDefault(); select(n - 1, true); }
      });
    });
  });
  /* Workspace demo: replays recorded runs through the app's own flow. Nothing here calls a model. */
  [].slice.call(d.querySelectorAll('[data-workspace]')).forEach(function (ws) {
    ws.classList.add('ws-ready');
    var input = ws.querySelector('[data-ws-input]'), form = ws.querySelector('[data-ws-form]'), msg = ws.querySelector('[data-ws-msg]');
    var meta = {}, shown = {}, busy = false;
    [].slice.call(ws.querySelectorAll('[data-run-meta]')).forEach(function (m) {
      meta[m.getAttribute('data-run-meta')] = { request: m.getAttribute('data-request'), tab: m.getAttribute('data-tab'), keywords: (m.getAttribute('data-keywords') || '').split('|').filter(Boolean), requires: m.getAttribute('data-requires') };
    });
    function q(sel) { return [].slice.call(ws.querySelectorAll(sel)); }
    function say(t) { msg.textContent = t; }
    function setBusy(v) { busy = v; if (v) ws.setAttribute('data-busy', 'true'); else ws.removeAttribute('data-busy'); }
    function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
    function show(id) {
      var r = meta[id];
      q('[data-result]').forEach(function (n) { if (n.parentNode.getAttribute('data-panel') === r.tab) { if (n.getAttribute('data-result') === id) n.setAttribute('data-on', ''); else n.removeAttribute('data-on'); } });
      var panel = ws.querySelector('[data-panel="' + r.tab + '"]'); if (panel) panel.setAttribute('data-has-result', '');
      var tab = ws.querySelector('#ws-tab-' + r.tab); if (tab) tab.click();
      shown[id] = true; if (r.tab) shown[r.tab] = true;
      q('[data-run]').forEach(function (b) { if (b.getAttribute('data-run') === id) b.setAttribute('data-active', ''); else b.removeAttribute('data-active'); });
      q('[data-requires]').forEach(function (b) { var need = b.getAttribute('data-requires'); if (need && shown[need]) b.setAttribute('aria-disabled', 'false'); });
      setBusy(false); say('Done. This is a recorded result, not a new model run.');
    }
    function run(id) {
      var r = meta[id]; if (!r || busy) return;
      if (r.requires && !shown[r.requires]) { say('Run the earlier request first, as in the app: a follow-up needs a previous result.'); return; }
      setBusy(true); say('Replaying the recorded run\u2026');
      var act = ws.querySelector('[data-ws-activity]'); if (act) act.open = true;
      var ae = ws.querySelector('[data-ws-activity-empty]'); if (ae) ae.hidden = true;
      var pe = ws.querySelector('[data-ws-proc-empty]'); if (pe) pe.hidden = true;
      q('[data-steps]').forEach(function (n) { var on = n.getAttribute('data-steps') === id; n.hidden = !on; if (on) { n.setAttribute('data-on', ''); [].slice.call(n.children).forEach(function (li) { li.removeAttribute('data-on'); }); } else n.removeAttribute('data-on'); });
      q('[data-proc]').forEach(function (n) { var on = n.getAttribute('data-proc') === id; n.hidden = !on; if (on) n.setAttribute('data-on', ''); else n.removeAttribute('data-on'); });
      var steps = [].slice.call(ws.querySelectorAll('[data-steps="' + id + '"] li'));
      var text = r.request, i = 0;
      function finish() {
        var t = 0;
        steps.forEach(function (li) { later(function () { li.setAttribute('data-on', ''); }, reduced ? 0 : (t += 320)); });
        later(function () { show(id); }, reduced ? 0 : t + 350);
      }
      if (reduced) { input.value = text; finish(); return; }
      input.value = '';
      (function type() { input.value = text.slice(0, ++i); if (i < text.length) later(type, 14); else later(finish, 200); })();
    }
    function pick(text) {
      var words = ' ' + text.toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ') + ' ';
      var best = null, score = 0;
      Object.keys(meta).forEach(function (id) {
        var n = 0; meta[id].keywords.forEach(function (k) { if (words.indexOf(' ' + k.toLowerCase() + ' ') > -1) n++; });
        if (n > score) { score = n; best = id; }
      });
      return best;
    }
    q('button[data-run]').forEach(function (b) {
      on(b, 'click', function () { if (b.getAttribute('aria-disabled') === 'true') { say('Run the earlier request first, as in the app: a follow-up needs a previous result.'); return; } run(b.getAttribute('data-run')); });
    });
    on(form, 'submit', function (e) {
      e.preventDefault(); if (busy) return;
      var text = (input.value || '').trim();
      if (!text) { say('Type a request, or pick an action below.'); return; }
      var id = pick(text);
      if (!id) { say('This recording only covers summaries, concepts, slides, viva questions and a shorter follow-up. Run PaperPilot locally to ask anything.'); return; }
      run(id);
    });
    q('[data-ws-feedback]').forEach(function (btn) {
      on(btn, 'click', function () { var fb = btn.parentNode.querySelector('[data-ws-fb]'); if (fb) { fb.hidden = false; btn.hidden = true; } });
    });
  });
  [].slice.call(d.querySelectorAll('[data-copy]')).forEach(function (btn) {
    on(btn, 'click', function () {
      var target = d.getElementById(btn.getAttribute('data-copy'));
      var label = btn.querySelector('span');
      function flash(msg) { if (label) label.textContent = msg; timers.push(setTimeout(function () { if (label) label.textContent = 'Copy'; }, 1800)); }
      if (!target) return;
      if (w.navigator.clipboard && w.navigator.clipboard.writeText) {
        w.navigator.clipboard.writeText(target.textContent || '').then(function () { flash('Copied'); }, function () { flash('Select and copy'); });
      } else {
        var range = d.createRange(); range.selectNodeContents(target);
        var sel = w.getSelection(); if (sel) { sel.removeAllRanges(); sel.addRange(range); }
        flash('Select and copy');
      }
    });
  });

  /* Reduced motion, live in both directions */
  function pinFinal() {
    reveals.forEach(function (el) { el.classList.add('in', 'settled'); });
    counters.forEach(function (c) { setCount(c, Number(c.getAttribute('data-count'))); });
    if (holdRoot && !done) { pinnedHold = true; complete(); }
    if (hero) { tx = ty = cx = cy = 0; setVar(hero, '--px', 0, 'px'); setVar(hero, '--py', 0, 'py'); }
    Object.keys(rafs).forEach(function (k) { if (rafs[k]) { w.cancelAnimationFrame(rafs[k]); rafs[k] = 0; } });
    html.classList.add('bs-ready'); // the cancelled ready frame must not leave the page unready
    poster.stop();
    paints.forEach(function (m) { m.style.setProperty('--pp', '1'); });
  }
  function unpin() {
    if (pinnedHold && holdRoot) { pinnedHold = false; done = false; hp = 0; setVar(holdRoot, '--hp', 0, 'hp'); holdState('idle'); if (status) status.textContent = 'Press and hold, or press Enter.'; }
    cache = {}; onScrollFrame();
    poster.start();
  }
  on(rmq, 'change', function (e) { reduced = e.matches; if (reduced) pinFinal(); else unpin(); });
  if (reduced) pinFinal();

  return function destroy() {
    offs.forEach(function (f) { f(); }); offs = [];
    observers.forEach(function (o) { o.disconnect(); }); observers = [];
    timers.forEach(function (t) { clearTimeout(t); }); timers = [];
    Object.keys(rafs).forEach(function (k) { if (rafs[k]) w.cancelAnimationFrame(rafs[k]); });
    html.classList.remove('bs-js', 'bs-ready');
  };
}
installBrandSite(document);
