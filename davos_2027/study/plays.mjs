// The study, read after the fact.
//
// Every play of veri+as iii on the published page leaves one anonymous record on public Nostr relays (NIP-78 app data,
// kind 30078, tag "veritas-play"): the counts the mirror reads, the shape of the constellation, the names of what grew.
// No picture, no face, no name, no address. This script fetches them all, keeps the latest record of each play, drops tests,
// and writes, next to itself:
//   plays.json   every play, as recorded
//   plays.csv    one row per play, one column per measure
//   sky.html     every constellation at once: the population's sky, for a wall
// Then it looks for structure in how people played without deciding the groups in advance: k-means on standardised measures
// of the finished plays, with the number of groups chosen by silhouette, each group described only by what sets it apart.
//
// From the repo root (from anywhere else, give the full path: ~/Claude/Projects/tiat_slop_2026/davos_2027/study/plays.mjs):
//   node davos_2027/study/plays.mjs              all relays, finished plays clustered
//   node davos_2027/study/plays.mjs --k 4        fix the number of groups
//   node davos_2027/study/plays.mjs --tests      include test plays (?probe&study), to check the pipeline
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const RELAYS = ['wss://relay.damus.io', 'wss://nos.lol', 'wss://relay.primal.net'];
const KIND = 30078, TAG = 'veritas-play';
const MEASURES = ['finds', 'holds', 'letgo', 'longest', 'stay', 'seek', 'direct', 'stir', 'scrubs', 'wiped', 'knobs', 'we',
  'together', 'noon', 'minutes', 'hull', 'sectors', 'turn', 'cross', 'closure', 'graft', 'cells', 'seam', 'taps'];
// record v1: 24 stills, the eye forgot you after two holds; v2 (from 15.10.2026, evening): 32 stills, and once seen you are in every
// form of life after, so "you" (how many have the viewer in them) is counted. Compare groups across versions with care.
// v3 (same evening): you are in most forms of life after you are seen, not all; each play also carries how many skies this device
// had grown before it (skies), whether it arrived through a sent sky (sent), and the name its sky was given (sky).
// v4 (later that night): sky names are code, noun_participle_hour (e.g. vigilia_videns_vesperi).
// v5 (15.10.2026, late): each finished play also carries c, its 52-character universe code (the shape and the recipe of each form of
// life, no picture), so the macroverse can open anyone's universe: veritas3.html?sky=<c>. f gains nothing new.
// v6 (same night): cul, the culture each youniverse ended with, as [feed, kill] (the Gray-Scott f and k), so the macroverse shows it.
// v7 (25.10.2026): no camera; noon in NOON.zone. looked and you are gone from the record and from MEASURES.
const args = process.argv.slice(2);
const K = args.includes('--k') ? parseInt(args[args.indexOf('--k')+1], 10) : 0;
const TESTS = args.includes('--tests');

function fetchRelay(url){
  return new Promise((resolve) => {
    const out = [];
    let ws;
    try { ws = new WebSocket(url); } catch (e) { resolve(out); return; }
    const done = () => { clearTimeout(timer); try { ws.close(); } catch (e) {} resolve(out); };
    const timer = setTimeout(done, 20000);
    ws.onopen = () => ws.send(JSON.stringify(['REQ', 'study', { kinds:[KIND], '#t':[TAG], limit:10000 }]));
    ws.onmessage = (m) => { try { const d = JSON.parse(m.data); if (d[0] === 'EVENT' && d[2]) out.push(d[2]); else if (d[0] === 'EOSE') done(); } catch (e) {} };
    ws.onerror = () => done();
  });
}

const events = (await Promise.all(RELAYS.map(fetchRelay))).flat();
const byPlay = new Map();
for (const ev of events) {
  const d = (ev.tags || []).find((t) => t[0] === 'd')?.[1];
  if (!d || !d.startsWith('veritas-play:')) continue;
  let c; try { c = JSON.parse(ev.content); } catch (e) { continue; }
  if (!c || typeof c !== 'object' || (c.test && !TESTS)) continue;
  const prev = byPlay.get(d);
  if (!prev || ev.created_at > prev.at) byPlay.set(d, { id: d.slice('veritas-play:'.length), at: ev.created_at, ...c });
}
const plays = [...byPlay.values()].sort((a, b) => a.at - b.at);
writeFileSync(join(HERE, 'plays.json'), JSON.stringify(plays, null, 1));

const csv = [['id', 'at', 'v', 'stage', 'mode', 'day', 'hour', 'coarse', 'skies', 'sent', 'sky', 'c', ...MEASURES].join(',')];
for (const p of plays) csv.push([p.id, new Date(p.at*1000).toISOString(), p.v ?? 1, p.stage, p.mode, p.day, p.hour, p.coarse, p.skies ?? '', p.sent ?? '', String(p.sky || '').replace(/[^A-Za-z_ ]/g, ''), String(p.c || '').replace(/[^A-Za-z0-9_-]/g, ''), ...MEASURES.map((k) => p.f?.[k] ?? '')].join(','));
writeFileSync(join(HERE, 'plays.csv'), csv.join('\n') + '\n');

// ---- how many, and how far they got
const count = (fn) => plays.filter(fn).length;
const finished = plays.filter((p) => p.stage === 'done' && p.f);
console.log(`${events.length} records from ${RELAYS.length} relays; ${plays.length} plays${TESTS ? ' (tests included)' : ''}`);
console.log(`  started only ${count((p) => p.stage === 'start')}, found at least one ${count((p) => p.stage === 'find')}, finished ${finished.length}`);
console.log(`  web ${count((p) => p.mode === 'web')}, wall ${count((p) => p.mode === 'gallery')}, sink ${count((p) => p.mode === 'sink')}; phones ${count((p) => p.coarse)}`);

// ---- the population's sky
const W = 900, C = W/2, S = (W*0.46)/0.395;
const lines = plays.filter((p) => Array.isArray(p.path) && p.path.length > 1).map((p) => {
  const pts = p.path.map(([x, y]) => `${(C + x*S).toFixed(1)},${(C - y*S).toFixed(1)}`).join(' ');
  return `<polyline points="${pts}"/>`;
}).join('\n');
const stars = plays.flatMap((p) => (p.path || []).map(([x, y]) => `<circle cx="${(C + x*S).toFixed(1)}" cy="${(C - y*S).toFixed(1)}" r="2.2"/>`)).join('\n');
writeFileSync(join(HERE, 'sky.html'), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>veri+as · everyone's sky</title>
<style>html,body{margin:0;height:100%;background:#030304;color:#8a8d93;font:12px/1.6 ui-monospace,Menlo,monospace}
main{min-height:100%;display:grid;place-items:center;padding:24px;box-sizing:border-box}svg{width:min(92vw,92vh);height:auto}
p{text-align:center;letter-spacing:.2em;text-transform:uppercase}</style></head><body><main><div>
<svg viewBox="0 0 ${W} ${W}" role="img" aria-label="Every constellation made so far, drawn at once">
<circle cx="${C}" cy="${C}" r="${(0.395*S).toFixed(1)}" fill="none" stroke="#24252a"/>
<g fill="none" stroke="#c2a27a" stroke-opacity="${Math.max(0.06, Math.min(0.5, 6/Math.max(1, plays.length)))}" stroke-width="1.2">${lines}</g>
<g fill="#e4dfd2" fill-opacity="${Math.max(0.15, Math.min(0.9, 10/Math.max(1, plays.length)))}">${stars}</g>
</svg><p>everyone's sky &middot; ${plays.length} plays &middot; ${new Date().toISOString().slice(0, 10)}</p></div></main></body></html>
`);

// ---- structure, found after the fact
if (finished.length < 8) {
  console.log(`  ${finished.length} finished plays: too few to look for groups yet (8 or more needed).`);
} else {
  const keys = MEASURES.filter((k) => new Set(finished.map((p) => p.f[k])).size > 1);
  const mean = (a) => a.reduce((x, y) => x + y, 0)/a.length;
  const mu = {}, sd = {};
  for (const k of keys) { const v = finished.map((p) => +p.f[k] || 0); mu[k] = mean(v); sd[k] = Math.sqrt(mean(v.map((x) => (x-mu[k])**2))) || 1; }
  const X = finished.map((p) => keys.map((k) => ((+p.f[k] || 0) - mu[k])/sd[k]));
  const d2 = (a, b) => a.reduce((t, x, i) => t + (x-b[i])**2, 0);
  function kmeans(k){
    const cent = [X[Math.floor(Math.random()*X.length)]];
    while (cent.length < k) {                                   // k-means++ seeding
      const w = X.map((x) => Math.min(...cent.map((c) => d2(x, c)))), tot = w.reduce((a, b) => a + b, 0);
      let r = Math.random()*tot, i = 0; while (r > w[i] && i < X.length-1) { r -= w[i]; i++; }
      cent.push(X[i]);
    }
    let lab = new Array(X.length).fill(0);
    for (let it = 0; it < 60; it++) {
      const next = X.map((x) => { let b = 0, bd = Infinity; cent.forEach((c, j) => { const v = d2(x, c); if (v < bd) { bd = v; b = j; } }); return b; });
      if (next.every((l, i) => l === lab[i]) && it) break;
      lab = next;
      for (let j = 0; j < k; j++) { const m = X.filter((_, i) => lab[i] === j); if (m.length) cent[j] = keys.map((_, q) => mean(m.map((x) => x[q]))); }
    }
    return { lab, cent };
  }
  function silhouette(lab, k){
    let t = 0;
    for (let i = 0; i < X.length; i++) {
      const own = X.filter((_, j) => j !== i && lab[j] === lab[i]);
      if (!own.length) continue;
      const a = mean(own.map((x) => Math.sqrt(d2(X[i], x))));
      let b = Infinity;
      for (let j = 0; j < k; j++) { if (j === lab[i]) continue; const o = X.filter((_, q) => lab[q] === j); if (o.length) b = Math.min(b, mean(o.map((x) => Math.sqrt(d2(X[i], x))))); }
      t += (b-a)/Math.max(a, b);
    }
    return t/X.length;
  }
  let best = null;
  const ks = K ? [K] : Array.from({ length: Math.min(6, finished.length-1) - 1 }, (_, i) => i+2);
  for (const k of ks) for (let rep = 0; rep < 8; rep++) { const r = kmeans(k), s = silhouette(r.lab, k); if (!best || s > best.s) best = { ...r, k, s }; }
  console.log(`  finished plays fall into ${best.k} groups (silhouette ${best.s.toFixed(2)}). What sets each apart, in standard deviations:`);
  for (let j = 0; j < best.k; j++) {
    const n = best.lab.filter((l) => l === j).length;
    const top = keys.map((k, q) => [k, best.cent[j][q]]).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1])).slice(0, 4);
    console.log(`    group ${j+1}: ${n} plays; ` + top.map(([k, z]) => `${k} ${z >= 0 ? '+' : ''}${z.toFixed(1)}`).join(', '));
  }
}
console.log(`wrote plays.json, plays.csv and sky.html in ${HERE}`);
