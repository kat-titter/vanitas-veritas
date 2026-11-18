// homo bulla, man is a bubble: gold films rise from the gold in the cupped hands, wobble, and pop slowly and messily.
// Use: <canvas data-goldbubbles data-photo="W H ox oy" data-from="fx fy spread"> as the first layer over an object-fit:cover photo,
// where W H is the photo's size, ox oy its object-position, and fx fy spread where the gold sits in it (fractions of the photo).
// Still under reduced motion; in print a still image of a Letter cover; paused off screen and in hidden tabs. ?probe exposes window.__bubbles.
(() => {
  const calm = matchMedia('(prefers-reduced-motion: reduce)');
  let cv = null, ctx = null, W = 0, H = 0, dpr = 1, live = false, raf = 0, last = 0, clock = 0, seed = 1;
  let bubbles = [], bits = [];
  const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const find = () => {                                    // looked up afresh: a page renderer may rebuild the canvas
    const c = document.querySelector('canvas[data-goldbubbles]');
    if (c !== cv) { cv = c; ctx = c ? c.getContext('2d') : null; W = H = 0; }
    return cv;
  };
  const size = () => {
    const r = cv.getBoundingClientRect(), d = Math.min(2, devicePixelRatio || 1);
    if (Math.abs(r.width - W) > .5 || Math.abs(r.height - H) > .5 || d !== dpr || cv.width !== Math.round(r.width * d)) {   // the bitmap too: a renderer may reset it
      W = r.width; H = r.height; dpr = d; cv.width = Math.round(W * d); cv.height = Math.round(H * d);
    }
  };
  const source = () => {                                  // the gold, in canvas pixels, through the photo's cover crop
    const [iw, ih, px, py] = (cv.dataset.photo || '1 1 .5 .5').split(' ').map(Number);
    const [fx, fy, fs] = (cv.dataset.from || '.5 1 .2').split(' ').map(Number);
    const s = Math.max(W / iw, H / ih), dw = iw * s, dh = ih * s;
    return { x: (W - dw) * px + fx * dw, y: (H - dh) * py + fy * dh, spread: fs * dw };
  };
  const target = () => Math.round(Math.max(9, Math.min(20, W * H / 46000)));

  const spawn = () => {
    const s = source(), small = Math.max(.55, Math.min(1, Math.sqrt(W / 1100)));
    const R = (5 + 56 * Math.pow(rand(), 2.3)) * small;  // most small, a few big
    const x = rand() < .75 ? s.x + (rand() + rand() - 1) * s.spread : W * (.1 + .8 * rand());
    const r = () => rand(), ph = r() * 6.283;
    return {
      x, y: Math.min(s.y + (r() - .5) * 30, H + R + 8), R, age: 0, alpha: 0, ph,
      vy: -(9 + 15 * r()) * (.85 + .3 * R / 60),          // slow: about 10 to 25 px a second
      wa: 5 + 9 * r(), fw: .25 + .45 * r(), sq: .95,
      a2: .08 + .08 * r(), a3: .03 + .04 * r(), a4: .015 + .02 * r(), a5: .008 + .017 * r(),   // never round
      p2: r() * 6.283, p3: r() * 6.283, p4: r() * 6.283, p5: r() * 6.283, w2: .25 + .45 * r(), w3: -.3 - .5 * r(), w4: .2 + .4 * r(), w5: .4 + .6 * r(),
      popAt: r() < .85 ? H * (.15 + .75 * r()) : -1e9,
    };
  };
  const outline = (b, k = 1) => {
    const n = b.R > 30 ? 64 : 40, pts = [];
    for (let i = 0; i < n; i++) {
      const th = i / n * 6.2832, t = clock;
      const r = b.R * k * (1 + b.a2 * Math.sin(2 * th + b.p2 + b.w2 * t) + b.a3 * Math.sin(3 * th + b.p3 + b.w3 * t) + b.a4 * Math.sin(4 * th + b.p4 + b.w4 * t) + b.a5 * Math.sin(5 * th + b.p5 + b.w5 * t));
      pts.push([b.x + r * Math.cos(th), b.y + r * Math.sin(th) * b.sq]);
    }
    return pts;
  };
  const trace = (p, closed) => {                          // smooth through the midpoints
    const n = p.length; ctx.beginPath();
    if (closed) {
      ctx.moveTo((p[n - 1][0] + p[0][0]) / 2, (p[n - 1][1] + p[0][1]) / 2);
      for (let i = 0; i < n; i++) { const a = p[i], b = p[(i + 1) % n]; ctx.quadraticCurveTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
      ctx.closePath();
    } else {
      ctx.moveTo(p[0][0], p[0][1]);
      for (let i = 1; i < n - 1; i++) ctx.quadraticCurveTo(p[i][0], p[i][1], (p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2);
      ctx.lineTo(p[n - 1][0], p[n - 1][1]);
    }
  };
  const pop = (b) => {                                    // the film tears into strands that sag and drip, over two to three seconds
    const p = outline(b), n = p.length;
    for (let i = 0; i < n;) {
      const len = 3 + Math.floor(rand() * n / 5);
      if (rand() < .72) bits.push({ strand: p.slice(i, Math.min(n, i + len + 1)), cx: b.x, cy: b.y, age: 0, life: 2 + rand() * .9, out: 5 + rand() * 12, sag: 14 + rand() * 30, w: Math.max(1.2, b.R * .06) });
      i += len;
    }
    const drops = 3 + Math.floor(rand() * (2 + b.R / 10));
    for (let k = 0; k < drops; k++) {
      const q = p[Math.floor(rand() * n)], dx = q[0] - b.x, dy = q[1] - b.y, d = Math.hypot(dx, dy) || 1, v = 8 + rand() * 18;
      bits.push({ x: q[0], y: q[1], vx: dx / d * v, vy: dy / d * v - 4, r: .9 + rand() * 2.2, age: 0, life: 1.8 + rand() * .9 });
    }
    b.dead = true;
  };

  const step = (dt) => {
    clock += dt;
    const tgt = target();
    if (bubbles.length < tgt && rand() < dt * tgt / 9) bubbles.push(spawn());
    for (const b of bubbles) {
      b.age += dt; b.alpha = Math.min(1, b.age / 1.8);
      b.y += b.vy * dt; b.x += Math.sin(clock * b.fw + b.ph) * b.wa * dt;
      b.R *= 1 + .008 * dt; b.sq = .95 - .03 * Math.sin(clock * .9 + b.ph);
      if (b.y < b.popAt || b.age > 45) pop(b); else if (b.y < -b.R * 1.4) b.dead = true;
    }
    bubbles = bubbles.filter((b) => !b.dead);
    for (const s of bits) if (!s.strand) { s.age += dt; s.vy += 36 * dt; s.x += s.vx * dt; s.y += s.vy * dt; s.vx *= Math.pow(.6, dt); } else s.age += dt;
    bits = bits.filter((s) => s.age < s.life);
  };
  const drawBubble = (b) => {
    const R = b.R, x = b.x, y = b.y, al = b.alpha;
    const p = outline(b);
    trace(p, true);
    ctx.strokeStyle = `rgba(20,12,4,${.4 * al})`; ctx.lineWidth = Math.max(2.2, R * .1); ctx.stroke();   // a dark meniscus, so the film reads on light ground
    const f = ctx.createRadialGradient(x - .3 * R, y - .35 * R, R * .1, x, y, R * 1.05);
    f.addColorStop(0, `rgba(255,236,205,${.02 * al})`); f.addColorStop(.7, `rgba(226,164,97,${.05 * al})`); f.addColorStop(1, `rgba(226,164,97,${.2 * al})`);
    ctx.fillStyle = f; ctx.fill();
    const g = ctx.createLinearGradient(x - R, y - R, x + R, y + R);
    g.addColorStop(0, `rgba(250,224,176,${.9 * al})`); g.addColorStop(.55, `rgba(226,164,97,${.55 * al})`); g.addColorStop(1, `rgba(170,104,48,${.3 * al})`);
    ctx.strokeStyle = g; ctx.lineWidth = Math.max(.9, R * .04); ctx.stroke();
    ctx.lineCap = 'round';                                // the window it reflects, up and to the left, as globby as the film; a glint low right
    const n = p.length, hi = outline(b, .72).slice(Math.round(n * .55), Math.round(n * .7));
    trace(hi, false); ctx.strokeStyle = `rgba(255,246,228,${.6 * al})`; ctx.lineWidth = Math.max(1, R * .085); ctx.stroke();
    ctx.beginPath(); ctx.arc(x + R * .44, y + R * .4 * b.sq, Math.max(.8, R * .05), 0, 6.2832);
    ctx.fillStyle = `rgba(255,240,210,${.35 * al})`; ctx.fill();
  };
  const drawBit = (s) => {
    const f = s.age / s.life, e = 1 - (1 - f) * (1 - f), a = 1 - f * f;   // holds, then melts away
    if (!s.strand) { ctx.beginPath(); ctx.arc(s.x, s.y, s.r * (1 - .3 * f), 0, 6.2832); ctx.fillStyle = `rgba(232,178,112,${.7 * a})`; ctx.fill(); return; }
    const n = s.strand.length, m = s.strand[n >> 1];
    const pts = s.strand.map((q, j) => {
      const dx = q[0] - s.cx, dy = q[1] - s.cy, d = Math.hypot(dx, dy) || 1, mid = .4 + .6 * Math.sin(Math.PI * j / Math.max(1, n - 1));
      const x = q[0] + dx / d * s.out * e, y = q[1] + dy / d * s.out * e;
      return [x + (m[0] - x) * .35 * e, y + (m[1] - y) * .35 * e + s.sag * f * f * mid];   // curls in, and the middle sags most
    });
    trace(pts, false); ctx.lineCap = 'round';
    ctx.strokeStyle = `rgba(236,190,128,${.75 * a})`; ctx.lineWidth = s.w * (1 - .6 * f); ctx.stroke();
  };
  const draw = () => {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    for (const b of bubbles) drawBubble(b);
    for (const s of bits) drawBit(s);
  };
  const warm = (secs) => { for (let i = 0; i < secs * 15; i++) step(1 / 15); };
  const still = () => {                                   // one settled frame, the same every time
    if (!find()) return; size(); if (!W || !H) return;
    seed = 7; clock = 0; bubbles = []; bits = []; warm(30); draw();
  };

  const printFrame = () => {                              // print shows a still image: Chrome's PDF drops whatever lies under a transparent canvas
    if (!cv || !cv.parentElement) return;
    let im = cv.parentElement.querySelector('img[data-goldbubbles-print]');
    if (!im) { im = document.createElement('img'); im.setAttribute('data-goldbubbles-print', ''); im.alt = ''; im.setAttribute('aria-hidden', 'true'); cv.after(im); }
    if (im.getAttribute('src')) return;
    const keep = [cv, ctx, W, H, dpr, seed, clock, bubbles, bits], off = document.createElement('canvas');
    off.dataset.photo = cv.dataset.photo || ''; off.dataset.from = cv.dataset.from || '';
    cv = off; W = 816; H = 1056; dpr = 2; off.width = W * dpr; off.height = H * dpr; ctx = off.getContext('2d');   // a Letter cover at 96 dpi
    seed = 7; clock = 0; bubbles = []; bits = []; warm(30); draw();
    [cv, ctx, W, H, dpr, seed, clock, bubbles, bits] = keep;
    off.toBlob((b) => { if (b) im.src = URL.createObjectURL(b); });
  };
  const css = document.createElement('style');
  css.textContent = 'img[data-goldbubbles-print]{display:none;position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;pointer-events:none}'
    + '@media print{canvas[data-goldbubbles]{display:none!important}img[data-goldbubbles-print]{display:block!important}}';
  document.head.appendChild(css);

  const onscreen = () => { const r = cv.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; };
  const frame = (now) => {
    raf = 0; if (!live) return;
    if (!find()) { raf = requestAnimationFrame(frame); return; }
    size();
    if (!onscreen()) { last = 0; setTimeout(() => { if (live && !raf) raf = requestAnimationFrame(frame); }, 400); return; }
    const dt = Math.min(.05, (now - (last || now)) / 1000); last = now;
    step(dt); draw(); raf = requestAnimationFrame(frame);
  };
  const run = () => {
    if (!calm.matches && !document.hidden) { if (!live) { live = true; last = 0; raf = requestAnimationFrame(frame); } return; }
    live = false; if (raf) { cancelAnimationFrame(raf); raf = 0; }
    if (calm.matches) still();
  };
  const poke = (e) => {                                   // a pointer passing through a bubble pops it
    if (!live || !cv) return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (x < 0 || y < 0 || x > r.width || y > r.height) return;
    for (const b of bubbles) if (!b.dead && b.alpha > .5 && Math.hypot(x - b.x, y - b.y) < b.R * .9) { pop(b); break; }
  };
  const boot = () => {
    if (!find()) return void setTimeout(boot, 200);
    size(); if (!W || !H) return void setTimeout(boot, 200);
    setTimeout(printFrame, 1200);
    if (calm.matches) return run();
    seed = (Date.now() % 2147483646) + 1; warm(24); draw(); run();
  };
  calm.addEventListener('change', () => { if (!calm.matches) { seed = (Date.now() % 2147483646) + 1; bubbles = []; bits = []; if (find()) { size(); warm(24); } } run(); });
  document.addEventListener('visibilitychange', run);
  setInterval(() => {                                     // the still frame, kept: redrawn when resized or when a renderer resets the canvas
    if (live || !calm.matches || !find()) return;
    const r = cv.getBoundingClientRect(), d = Math.min(2, devicePixelRatio || 1);
    if (cv.width !== Math.round(r.width * d) || cv.height !== Math.round(r.height * d)) still();
  }, 500);
  addEventListener('beforeprint', () => { if (find()) printFrame(); });
  document.addEventListener('pointermove', poke, { passive: true });
  document.addEventListener('pointerdown', poke, { passive: true });
  if (/[?&]probe\b/.test(location.search)) window.__bubbles = {
    state: () => ({ cw: cv && cv.width, held: cv === document.querySelector('canvas[data-goldbubbles]'), n: document.querySelectorAll('canvas[data-goldbubbles]').length, live, calm: calm.matches, bubbles: bubbles.length, bits: bits.length, W, H, clock: +clock.toFixed(2), raf: !!raf }),
    list: () => bubbles.map((b) => [Math.round(b.x), Math.round(b.y), Math.round(b.R), +b.alpha.toFixed(2)]),
    run: (secs) => { for (let i = 0; i < secs * 30; i++) step(1 / 30); draw(); return clock; },
    pop: () => { const b = bubbles.filter((q) => q.alpha > .5 && q.y > H * .2 && q.y < H * .8).sort((m, n) => n.R - m.R)[0]; if (!b) return null; pop(b); draw(); return { x: b.x, y: b.y, R: b.R }; },
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
