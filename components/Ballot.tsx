'use client';
import { useEffect, useRef, useState } from 'react';
import { CATEGORIES, POINTS, encode, parse, score, type BallotRace, type FriendBallot, type Side } from '@/lib/ballot-code';
import { surname } from '@/lib/format';

// Election night ballot (Max, 2026-11-03). Picks live in this browser only; a friend's ballot reaches the scorekeeper as
// copied text (the UB line) pasted into the Standings tab. Nothing leaves the page: the site has no server routes.
const KEY = 'undertow-ballot-2026';
const TIEBREAKERS: { id: string; label: string; hint: string; numeric: boolean }[] = [
  { id: 'tb-sen', label: 'Senate seats for Democrats', hint: 'of 100, with the independents who caucus with them', numeric: true },
  { id: 'tb-house', label: 'House seats Democrats win', hint: 'of 435', numeric: true },
  { id: 'tb-time', label: 'Time the AP calls the House', hint: 'your time, or “not tonight”', numeric: false },
];
type Saved = { name: string; picks: Record<string, Side>; tb: Record<string, string>; results: Record<string, Side>; friends: FriendBallot[] };
const EMPTY: Saved = { name: '', picks: {}, tb: {}, results: {}, friends: [] };

function load(races: BallotRace[]): Saved {
  let raw: Partial<Saved> = {};
  try { raw = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch { raw = {}; }
  const ids = new Set(races.map(r => r.id));
  const keep = (m: unknown) => Object.fromEntries(Object.entries((m && typeof m === 'object' ? m : {}) as Record<string, Side>).filter(([id, v]) => ids.has(id) && (v === 'D' || v === 'R')));
  return {
    name: typeof raw.name === 'string' ? raw.name : '',
    picks: keep(raw.picks), results: keep(raw.results),
    tb: raw.tb && typeof raw.tb === 'object' ? raw.tb as Record<string, string> : {},
    friends: Array.isArray(raw.friends) ? raw.friends.filter(f => f && typeof f.picks === 'string' && f.picks.length === races.length) : [],
  };
}

function PickButton({ race, side, chosen, onPick }: { race: BallotRace; side: Side; chosen: boolean; onPick: () => void }) {
  const name = side === 'D' ? race.d : race.r;
  return <button type="button" className={`ballot-pick is-${side.toLowerCase()}`} aria-pressed={chosen} onClick={onPick}>
    <span className="ballot-dot" aria-hidden="true"/>
    <span className="ballot-name">{name}{race.cat !== 'CONTROL' && <span className="ballot-party">{side === 'D' ? race.dParty || 'D' : 'R'}</span>}{race.inc === side && <span className="ballot-inc" title="Incumbent"> ★</span>}</span>
  </button>;
}

function RaceList({ races, chosen, onPick, mode }: { races: BallotRace[]; chosen: Record<string, Side>; onPick: (id: string, s: Side) => void; mode: 'mine' | 'results' }) {
  return <>{CATEGORIES.map(({ cat, title, note }) => <section key={cat} className={`ballot-cat ballot-cat-${cat.toLowerCase()}`} aria-label={title}>
    <div className="ballot-cat-head"><h2>{title}</h2><span>{note}</span></div>
    <div className="ballot-list">{races.filter(r => r.cat === cat).map(r => <div key={r.id} className="ballot-race" role="group" aria-label={r.label}>
      <div className="ballot-race-label"><b>{r.label}</b><em>{mode === 'results' && chosen[r.id] ? 'called' : cat === 'CONTROL' ? `${r.held === 'R' ? 'Republicans' : 'Democrats'} hold it now` : `${r.rating} · held ${r.held}`}</em></div>
      <div className="ballot-pair">{(['D', 'R'] as Side[]).map(s => <PickButton key={s} race={r} side={s} chosen={chosen[r.id] === s} onPick={() => onPick(r.id, s)}/>)}</div>
    </div>)}</div>
  </section>)}</>;
}

export function Ballot({ races, top, pdf, ratingDates }: { races: BallotRace[]; top: number; pdf: string; ratingDates: string }) {
  const [st, setSt] = useState<Saved>(EMPTY);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState<'ballot' | 'score'>('ballot');
  const [toast, setToast] = useState('');
  const [fallback, setFallback] = useState<string | null>(null);
  const [paste, setPaste] = useState('');
  const [pasteNote, setPasteNote] = useState('');
  const [armed, setArmed] = useState(false);
  const meter = useRef<HTMLElement>(null);
  const fallbackRef = useRef<HTMLTextAreaElement>(null);
  const dock = useRef<HTMLDivElement>(null);

  useEffect(() => { setSt(load(races)); setReady(true); }, [races]);
  useEffect(() => { if (!ready) return; try { localStorage.setItem(KEY, JSON.stringify(st)); } catch { /* storage blocked: picks last for this visit only */ } }, [st, ready]);
  const n = races.length, picked = Object.keys(st.picks).length;
  // The CSP allows no inline style attributes, so the meter width is set on the element after render.
  useEffect(() => { if (meter.current) meter.current.style.width = `${(100 * picked) / n}%`; }, [picked, n]);
  useEffect(() => { if (fallback !== null) fallbackRef.current?.select(); }, [fallback]);
  // The phone bar is pinned over the page, so the page reserves the bar's measured height, which grows when the copy
  // fallback opens (Greptile on PR #3). CSSOM, not a style attribute: the CSP allows none.
  useEffect(() => {
    const el = dock.current, root = document.documentElement;
    if (!el || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(() => root.style.setProperty('--ballot-dock-h', `${Math.ceil(el.getBoundingClientRect().height)}px`));
    ro.observe(el);
    return () => { ro.disconnect(); root.style.removeProperty('--ballot-dock-h'); };
  }, []);

  const update = (f: (s: Saved) => Saved) => setSt(s => f(s));
  const toggle = (key: 'picks' | 'results') => (id: string, side: Side) => update(s => {
    const next = { ...s[key] };
    if (next[id] === side) delete next[id]; else next[id] = side;
    return { ...s, [key]: next };
  });
  const tb = (): [string, string, string] => [st.tb['tb-sen'] || '', st.tb['tb-house'] || '', st.tb['tb-time'] || ''];

  function picksText() {
    const who = st.name.trim() || 'Anonymous';
    const lines = [`Undertow election night ballot · ${who}`];
    for (const { cat, title } of CATEGORIES) lines.push(`${title}: ${races.filter(r => r.cat === cat).map(r => {
      const s = st.picks[r.id], name = s ? (s === 'D' ? r.d : r.r) : '';
      const who = surname(name), party = s === 'D' ? r.dParty || 'D' : 'R';
      return `${r.label.replace(/^The /, '')} ${s ? (cat === 'CONTROL' ? name : `${who} (${party})`) : 'no pick'}`;
    }).join(', ')}`);
    const [a, b, c] = tb();
    lines.push(`Tiebreakers: Senate D ${a || '?'} · House D ${b || '?'} · AP calls the House ${c || '?'}`);
    lines.push(encode(races, st.name, st.picks, tb()));
    return lines.join('\n');
  }
  function copy() {
    const text = picksText(), left = n - picked;
    const done = () => { setFallback(null); setToast(left ? `Copied. ${left} ${left === 1 ? 'pick is' : 'picks are'} still blank.` : 'Copied. Paste it in the group chat.'); };
    const fail = () => { setFallback(text); setToast('Copying is blocked here. The text is selected below; copy it by hand.'); };
    try { navigator.clipboard.writeText(text).then(done, fail); } catch { fail(); }
  }
  function addFriend() {
    const f = parse(paste, n);
    if (!f) { setPasteNote(`That text has no readable ballot line (it starts with UB5). Ask them to tap Copy my picks again and paste all of it.`); return; }
    update(s => ({ ...s, friends: [...s.friends.filter(x => x.name !== f.name), f] }));
    setPaste(''); setPasteNote(`Added ${f.name}.`);
  }

  const called = Object.keys(st.results).length;
  const awarded = races.reduce((a, r) => a + (st.results[r.id] ? POINTS[r.cat] : 0), 0);
  const mine: FriendBallot & { you: true; fi: -1 } = { name: st.name.trim(), picks: races.map(r => st.picks[r.id] || '-').join(''), tb: tb(), you: true, fi: -1 };
  const standings = [mine, ...st.friends.map((f, fi) => ({ ...f, you: false as const, fi }))]
    .map(f => ({ ...f, s: score(races, f.picks, st.results) })).sort((a, b) => b.s - a.s);

  return <div className="ballot">
    <div className="ballot-tabs" role="tablist" aria-label="Your picks or the standings">
      <button type="button" role="tab" id="ballot-tab-mine" aria-controls="ballot-view-mine" aria-selected={tab === 'ballot'} onClick={() => setTab('ballot')}>Your picks</button>
      <button type="button" role="tab" id="ballot-tab-score" aria-controls="ballot-view-score" aria-selected={tab === 'score'} onClick={() => setTab('score')}>Standings</button>
    </div>
    <div className="ballot-layout">
      <div className="ballot-main">
        <section id="ballot-view-mine" role="tabpanel" aria-labelledby="ballot-tab-mine" hidden={tab !== 'ballot'}>
          <div className="ballot-field"><label htmlFor="ballot-name">Your name</label><input id="ballot-name" autoComplete="off" maxLength={30} placeholder="Name on the ballot" value={st.name} onChange={e => { const v = e.target.value; update(s => ({ ...s, name: v })); }}/></div>
          <p className="ballot-key"><span><b>★</b> incumbent on the ballot</span><span><b>held R</b> party holding the seat now</span><span><b className="is-d">D</b> Democrat · <b className="is-d">I</b> independent · <b className="is-r">R</b> Republican</span></p>
          <RaceList races={races} chosen={st.picks} onPick={toggle('picks')} mode="mine"/>
        </section>
        <section id="ballot-view-score" role="tabpanel" aria-labelledby="ballot-tab-score" hidden={tab !== 'score'}>
          <div className="c-panel ballot-panel">
            <div className="ballot-panel-head"><h3>Who is winning</h3><span>{called} of {n} called · {awarded} points awarded</span></div>
            <ol className="ballot-board">{standings.map((f, i) => <li key={f.you ? 'you' : `${f.name}-${f.fi}`}>
              <span className="ballot-rank">{i + 1}</span>
              <span className="ballot-who"><b>{f.you ? (f.name ? `${f.name} (you)` : 'You') : f.name}</b><small>Senate {f.tb[0] || '?'} · House {f.tb[1] || '?'} · {f.tb[2] || '?'}</small></span>
              <span className="ballot-score">{f.s}<small>/{top}</small></span>
              {f.you ? <span aria-hidden="true"/> : <button type="button" className="ballot-remove" aria-label={`Remove ${f.name}`} onClick={() => update(s => ({ ...s, friends: s.friends.filter((_, j) => j !== f.fi) }))}>✕</button>}
            </li>)}</ol>
            {!st.friends.length && <p className="muted text-sm">Only your ballot so far. Paste a friend’s picks below to add them.</p>}
          </div>
          <div className="c-panel ballot-panel">
            <h3>Add a friend’s ballot</h3>
            <p className="muted text-sm">Paste everything they copied from this page.</p>
            <label className="sr-only" htmlFor="ballot-paste">Friend’s copied picks</label>
            <textarea id="ballot-paste" className="ballot-text" placeholder="Paste here" value={paste} onChange={e => setPaste(e.target.value)}/>
            <div className="ballot-actions">
              <button type="button" className="ballot-btn" onClick={addFriend}>Add ballot</button>
              <button type="button" className="ballot-btn is-ghost" onBlur={() => setArmed(false)} onClick={() => { if (armed) { update(s => ({ ...s, results: {} })); setArmed(false); } else setArmed(true); }}>{armed ? 'Tap again to clear every call' : 'Clear results'}</button>
            </div>
            <p className="ballot-note" role="status">{pasteNote}</p>
          </div>
          <p className="eyebrow ballot-results-kicker">Results · tap the winner when the AP calls it</p>
          <div className="ballot-results"><RaceList races={races} chosen={st.results} onPick={toggle('results')} mode="results"/></div>
        </section>
      </div>
      <aside className="ballot-rail" aria-label="Your progress">
        <div className="ballot-dock" ref={dock}>
          <div className="ballot-count"><b>{picked} of {n}</b><small>{picked === n ? 'every race picked' : `picked · ${n - picked} to go`}</small><div className="ballot-meter"><i ref={meter}/></div></div>
          <button type="button" className="ballot-btn" onClick={copy}>Copy my picks</button>
          <p className="ballot-note" role="status" aria-live="polite">{toast}</p>
          {fallback !== null && <><label className="sr-only" htmlFor="ballot-fallback">Your picks, to copy by hand</label><textarea id="ballot-fallback" ref={fallbackRef} className="ballot-text" readOnly value={fallback}/><button type="button" className="ballot-btn is-ghost" onClick={() => { setFallback(null); setToast(''); }}>Done</button></>}
        </div>
        <div className="c-panel ballot-panel" hidden={tab !== 'ballot'}>
          <h3>Tiebreakers</h3>
          <p className="muted text-sm">A tie goes to the closest Senate number, then the House number, then the time.</p>
          {TIEBREAKERS.map(t => <div key={t.id} className="ballot-tb"><label htmlFor={t.id}>{t.label}<span>{t.hint}</span></label>
            <input id={t.id} maxLength={12} inputMode={t.numeric ? 'numeric' : 'text'} placeholder={t.numeric ? '0' : '9:45 PM'} value={st.tb[t.id] || ''} onChange={e => { const v = e.target.value; update(s => ({ ...s, tb: { ...s.tb, [t.id]: v } })); }}/></div>)}
        </div>
        <div className="c-panel ballot-panel">
          <p className="text-sm"><b>Scoring.</b> Every correct pick is 1 point. A pick scores once the AP calls it. A 50-50 Senate goes to Republicans, since the vice president breaks the tie. Top score: <b>{top}</b>.</p>
          <p className="muted text-sm mt-3">The races are every Senate and governor seat Cook rated anything from Toss-up to Likely ({ratingDates}); safe seats are left off. Picks stay in this browser.</p>
          <p className="text-sm mt-3"><a href={pdf}>Print version (PDF)</a></p>
        </div>
      </aside>
    </div>
  </div>;
}
