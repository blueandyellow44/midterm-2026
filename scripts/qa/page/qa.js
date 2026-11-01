// Undertow UI sweep. Every check here comes from a bug that reached Max on 2026-10-28:
//   TAP-BLOCKED   a closed menu's invisible links ate taps on phones
//   SPILL         "Hyde-Smith +5.2" ran into the next column; long surnames spilled at 1280/1440
//   HSCROLL / OFFSCREEN   anything wider than the screen
//   LEAK          NaN, undefined, "1 polls" in visible text
//   TINY          text under the 11px floor (map tile labels and the hemicycle are exempt by ruling)
// The home panel is checked with EVERY race selected, in every chamber, because the overlap only showed for some races.
// Result: window.__qaReport = {done, failures, warnings, runs}. FAIL items block a deploy; WARN items are listed for Max.
(function () {
  const q = new URLSearchParams(location.search);
  const WIDTHS = (q.get('widths') || '340,390,1100,1280,1440').split(',').map(Number);
  const ONLY = q.get('routes') ? q.get('routes').split(',') : null;
  const f = document.getElementById('f'), bar = document.getElementById('bar');
  const report = window.__qaReport = { done: false, failures: [], warnings: [], runs: 0, started: new Date().toISOString() };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const load = async (route, w) => { f.style.width = w + 'px'; f.style.height = (w < 1000 ? (w <= 340 ? 700 : 844) : 820) + 'px'; await new Promise(r => { f.onload = r; f.src = route; }); await sleep(350); return f.contentDocument; };
  const vis = e => e.checkVisibility && e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }) && e.getBoundingClientRect().width > 0;
  const desc = e => { let s = e.tagName.toLowerCase(); if (typeof e.className === 'string' && e.className.trim()) s += '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.'); const t = (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 32); return s + (t ? ` "${t}"` : ''); };
  const EXEMPT_TINY = el => el.closest('svg,.wall-tile,.hemi,.sr-only') || /wall-tile/.test(el.className || '');
  function check(doc, where, scope) {
    const win = doc.defaultView, out = [];
    const fail = (kind, msg) => out.push({ level: 'FAIL', kind, where, msg });
    const warn = (kind, msg) => out.push({ level: 'WARN', kind, where, msg });
    const rootEl = scope || doc.body;
    if (!scope && doc.documentElement.scrollWidth > win.innerWidth + 1) fail('HSCROLL', `${doc.documentElement.scrollWidth} > ${win.innerWidth}`);
    const text = rootEl.innerText;
    for (const re of [/\bNaN\b/, /\bundefined\b/, /\bInfinity\b/, /\[object /, /\b1 polls\b/]) { const m = text.match(re); if (m) fail('LEAK', `${re} near "${text.substr(Math.max(0, m.index - 30), 70).replace(/\n/g, ' ')}"`); }
    for (const e of rootEl.querySelectorAll('*')) {
      if (!vis(e)) continue;
      const cs = win.getComputedStyle(e); const hasText = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!hasText) continue;
      const fs = parseFloat(cs.fontSize);
      if (fs > 0 && fs < 11 && !EXEMPT_TINY(e)) warn('TINY', `${desc(e)} ${fs}px`);
      const r = e.getBoundingClientRect();
      if (r.right > win.innerWidth + 1 && cs.position !== 'fixed') fail('OFFSCREEN', desc(e));
      const p = e.parentElement; if (!p || cs.overflowX !== 'visible' || win.getComputedStyle(p).overflowX !== 'visible') continue;
      const range = doc.createRange(); range.selectNodeContents(e); const tr = range.getBoundingClientRect(), pr = p.getBoundingClientRect();
      if (tr.right > pr.right + 2) fail('SPILL', `${desc(e)} text ends ${Math.round(tr.right)}px, its box ends ${Math.round(pr.right)}px`);
    }
    // Consistency (2026-11-01): every 'in play' subtotal sums; every visible slider announces a value; every stacked phone
    // table cell carries its header; every in-page anchor resolves; a race page's Undertow figure matches the sealed release.
    for (const m of text.matchAll(/(\d+) in play: (\d+) D, (\d+) R(?:, (\d+) even)?/g)) { const [, play, d, r, e] = m.map(Number); if (d + r + (e || 0) !== play) fail('SUM', `"${m[0]}" does not add up`); }
    for (const e of rootEl.querySelectorAll('input[type=range]')) if (vis(e) && !e.getAttribute('aria-valuetext')) fail('A11Y-VALUE', `${desc(e)} has no aria-valuetext`);
    if (win.innerWidth < 1000) for (const t of rootEl.querySelectorAll('table')) { const th = t.querySelector('thead'); if (!th || win.getComputedStyle(th).display !== 'none') continue; for (const td of t.querySelectorAll('tbody td')) if (vis(td) && td.textContent.trim() && !td.hasAttribute('data-label') && td !== td.parentElement.firstElementChild) fail('NO-LABEL', `${desc(td)} stacked without data-label`); }
    for (const a of rootEl.querySelectorAll('a[href^="#"]')) { const id = decodeURIComponent(a.getAttribute('href').slice(1)); if (id && !doc.getElementById(id)) fail('ANCHOR', `#${id} has no target`); }
    const head = rootEl.querySelector('section.race-head[data-race]');
    if (head && window.__sealed) { const id = head.getAttribute('data-race'); const sig = window.__sealed.signals?.per_race?.[id]; const fig = [...head.querySelectorAll('.c-figure, .c-fig')].find(x => /Undertow/i.test(x.textContent)); const shown = fig && fig.textContent.match(/[+−-]\s?(\d+\.\d)/); if (sig && shown && Math.abs(Math.abs(Number(sig.adjusted_margin)) - Number(shown[1])) > 0.051) fail('RELEASE', `${id} shows ${shown[0]} but the release says ${sig.adjusted_margin}`); }
    const taps = [...rootEl.querySelectorAll('a[href],button,summary,input,select,textarea,[role=button],[role=tab],[role=slider]')].filter(vis);
    for (const e of taps) {
      e.scrollIntoView({ block: 'center', inline: 'nearest' });
      const rects = [...e.getClientRects()].filter(r => r.width > 1 && r.height > 1); if (!rects.length) continue;
      const hit = rects.some(r => { const x = r.left + r.width / 2, y = r.top + r.height / 2; if (x < 0 || y < 0 || x >= win.innerWidth || y >= win.innerHeight) return true; const h = doc.elementFromPoint(x, y); return h && (h === e || e.contains(h) || (h.tagName === 'LABEL' && h.contains(e))); });
      if (!hit) { const r = rects[0]; const h = doc.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); fail('TAP-BLOCKED', `${desc(e)} covered by ${h ? desc(h) : 'nothing'}`); }
      const b = e.getBoundingClientRect(); if (win.innerWidth < 1000 && (b.height < 24 || b.width < 24) && !e.closest('p,li')) warn('SMALL-TAP', `${desc(e)} ${Math.round(b.width)}x${Math.round(b.height)}`);
    }
    win.scrollTo(0, 0);
    return out;
  }
  window.__qaCheck = check;   // exposed so a doctored document can prove the checks fail (ROE: a detector is untrusted until seen to fail)
  const add = items => { for (const i of items) (i.level === 'FAIL' ? report.failures : report.warnings).push(i); };
  const status = s => { bar.textContent = `Undertow QA: ${s}\nruns ${report.runs} · FAIL ${report.failures.length} · WARN ${report.warnings.length}`; };
  async function homePanels(doc, w) {
    if (w >= 1100) {
      const chambers = [...doc.querySelectorAll('button')].filter(b => vis(b) && /^(Senate|Governor|House)$/.test(b.innerText.trim()));
      for (const c of chambers) {
        c.click(); await sleep(150);
        const rows = [...doc.querySelectorAll('.wall-row,.wall-tile')].filter(vis);
        for (const r of rows) { r.click(); await sleep(40); const panel = doc.querySelector('.wall-detail'); if (panel && vis(panel)) add(check(doc, `/ @${w} ${c.innerText.trim()}: ${r.innerText.replace(/\s+/g, ' ').slice(0, 20)}`, panel)); report.runs++; }
      }
    } else {
      for (const chip of [...doc.querySelectorAll('.phone-chips button')].filter(vis)) { chip.click(); await sleep(150); add(check(doc, `/ @${w} chip ${chip.innerText.replace(/\s+/g, ' ').slice(0, 20)}`)); report.runs++; }
    }
  }
  (async () => {
    const routes = ONLY || await (await fetch('/__qa/routes.json')).json();
    try { window.__sealed = await (await fetch('/__qa/derived.json')).json(); } catch { window.__sealed = null; }
    for (const w of WIDTHS) for (const route of routes) {
      status(`${route} at ${w}px`);
      const doc = await load(route, w); add(check(doc, `${route} @${w}`)); report.runs++;
      if (route === '/') await homePanels(doc, w);
    }
    // de-duplicate identical messages so the list stays readable
    for (const k of ['failures', 'warnings']) { const seen = new Map(); for (const i of report[k]) { const key = i.kind + i.msg; if (!seen.has(key)) seen.set(key, { ...i, count: 0, first: i.where }); seen.get(key).count++; } report[k] = [...seen.values()]; }
    report.done = true; report.finished = new Date().toISOString();
    status(report.failures.length ? 'FAILED, see window.__qaReport.failures' : 'PASS (warnings listed in window.__qaReport.warnings)');
  })();
})();
