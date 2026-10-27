'use client';
import { useMemo, useState } from 'react';
import { FactorBars, MarginTrack, pct } from './Console';

// The election-night wall (Max, 2026-10-27: "almost a console. Multi panel, don't need to scroll to slider"; "that American
// political news red and blue look"). One dial state drives every panel. Each race at dial value m = polls + m + its state
// adjustment + spending + early vote, so at m = the national lean it reproduces Undertow's frozen number exactly.
export type WallRace = {
  id: string; slug: string; state: string; office: 'SEN' | 'GOV'; name: string; d: string; r: string;
  polls: number; stateAdj: number; spending: number; earlyVote: number; undertow: number; sd: number; pollCount: number | null;
  spendLabel: string; dLetter: string;
};
type Office = 'SEN' | 'GOV';
export type HistoryPreset = { year: number; miss_toward_d: number };
// Dial presets are real past national misses from the archive, then no miss, my bet and last fall (Max, 2026-10-27).
function presetList(history: HistoryPreset[], national: number, lastFall: number): [string, number][] {
  return [...history.map(h => [`${h.year} again`, Math.round(h.miss_toward_d * 10) / 10] as [string, number]), ['No miss', 0], [`My bet ${national.toFixed(1)}`, national], [`Last fall ${lastFall.toFixed(1)}`, lastFall]];
}
const EVEN = 0.05;
const last = (n: string) => n.trim().split(/\s+/).pop() || n;
// Square tile map, one tile per state, laid out roughly by geography (12 x 8).
const TILES: Record<string, [number, number]> = {
  AK: [0, 0], ME: [11, 0], VT: [10, 1], NH: [11, 1],
  WA: [1, 2], ID: [2, 2], MT: [3, 2], ND: [4, 2], MN: [5, 2], IL: [6, 2], WI: [7, 2], MI: [8, 2], NY: [9, 2], RI: [10, 2], MA: [11, 2],
  OR: [1, 3], NV: [2, 3], WY: [3, 3], SD: [4, 3], IA: [5, 3], IN: [6, 3], OH: [7, 3], PA: [8, 3], NJ: [9, 3], CT: [10, 3],
  CA: [1, 4], UT: [2, 4], CO: [3, 4], NE: [4, 4], MO: [5, 4], KY: [6, 4], WV: [7, 4], VA: [8, 4], MD: [9, 4], DE: [10, 4],
  AZ: [2, 5], NM: [3, 5], KS: [4, 5], AR: [5, 5], TN: [6, 5], NC: [7, 5], SC: [8, 5], DC: [9, 5],
  OK: [4, 6], LA: [5, 6], MS: [6, 6], AL: [7, 6], GA: [8, 6],
  HI: [0, 7], TX: [4, 7], FL: [9, 7],
};
const BOARD_SPAN = 20;


export function marginAt(r: WallRace, m: number) { return r.polls + m + r.stateAdj + r.spending + r.earlyVote; }
export function marginLabel(v: number, r: WallRace) { return Math.abs(v) < EVEN ? 'Even' : `${last(v > 0 ? r.d : r.r)} +${Math.abs(v).toFixed(1)}`; }
export function shade(v: number) { const a = Math.abs(v); const side = v > 0 ? 'd' : 'r'; return a < 1 ? 'toss' : a < 4 ? `${side}-lean` : a < 9 ? `${side}-likely` : `${side}-safe`; }
const letter = (v: number, r: WallRace) => (v > 0 ? r.dLetter : 'R');
const side = (v: number) => (v >= EVEN ? 'is-d' : v <= -EVEN ? 'is-r' : 'is-even');

function Dial({ m, setM, national, lastFall, history, compact }: { m: number; setM: (v: number) => void; national: number; lastFall: number; history: HistoryPreset[]; compact?: boolean }) {
  const span = Math.max(8, Math.ceil(lastFall));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const hit = presetList(history, national, lastFall).find(([, v]) => near(v));
  const mark = hit ? (hit[1] === national ? 'My bet' : hit[0]) : null;
  const dir = m >= EVEN ? 'understate Democrats' : m <= -EVEN ? 'understate Republicans' : 'miss neither way';
  return <section className={`wall-panel wall-dial${compact ? ' is-compact' : ''}`} aria-label="How wrong are the polls?">
    <p className="wall-kicker">How wrong are the polls?</p>
    <p className={`wall-dial-readout ${side(m)}`}><span className="wall-num">{Math.abs(m).toFixed(1)}</span><span className="wall-dial-unit">pts</span></p>
    <p className="wall-dial-dir">Polls {dir}{mark ? <> · <strong>{mark}</strong></> : null}</p>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label="National polling miss in points; negative means polls understate Republicans"/>
    <div className="wall-scale"><span className="is-r">◀ Republicans</span><span className="is-d">Democrats ▶</span></div>
    <div className="wall-presets">{presetList(history, national, lastFall).map(([label, v]) => <button key={label} type="button" aria-pressed={near(v)} onClick={() => setM(v)}><span>{label}</span><small>{Math.abs(v) < EVEN ? 'polls right' : `${Math.abs(v).toFixed(1)} toward ${v > 0 ? 'D' : 'R'}`}</small></button>)}</div>
    {!compact && <p className="wall-note">Slide to set this year’s national polling miss. Each race keeps its own state record, spending and early vote. The call I am graded on stays at my bet.</p>}
  </section>;
}

function Tally({ races, m }: { races: WallRace[]; m: number }) {
  const count = (o: Office) => { const rs = races.filter(r => r.office === o).map(r => marginAt(r, m)); return { d: rs.filter(v => v >= EVEN).length, r: rs.filter(v => v <= -EVEN).length, n: rs.length }; };
  return <div className="wall-tally" aria-live="polite">{(['SEN', 'GOV'] as Office[]).map(o => { const c = count(o); return <div key={o} className="wall-tally-row"><span className="wall-tally-label">{o === 'SEN' ? 'Senate' : 'Governor'}</span><span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${pct(100 * c.d / c.n)}`}/><i className={`is-r gw-${pct(100 * c.r / c.n)}`}/></span><span className="wall-tally-num"><b className="is-d">D {c.d}</b> <b className="is-r">R {c.r}</b></span></div>; })}</div>;
}

function TileMap({ races, m, office, setOffice, selected, select }: { races: WallRace[]; m: number; office: Office; setOffice: (o: Office) => void; selected: string; select: (id: string) => void }) {
  const byState = new Map(races.filter(r => r.office === office).map(r => [r.state, r]));
  return <section className="wall-panel wall-map" aria-label="Map of tracked races">
    <div className="wall-panel-head"><p className="wall-kicker">The map · {office === 'SEN' ? 'Senate' : 'Governor'}</p>
      <div className="wall-toggle" role="group" aria-label="Office">{(['SEN', 'GOV'] as Office[]).map(o => <button key={o} type="button" aria-pressed={office === o} onClick={() => setOffice(o)}>{o === 'SEN' ? 'Senate' : 'Governor'}</button>)}</div></div>
    <div className="wall-tiles">{Object.entries(TILES).map(([st, [c, rw]]) => { const r = byState.get(st); const v = r ? marginAt(r, m) : 0;
      const pos = `tc-${c} tr-${rw}`;
      return r ? <button key={st} type="button" className={`wall-tile ${pos} ${shade(v)}${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} aria-label={`${r.name}: ${marginLabel(v, r)}`} onClick={() => select(r.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>
        : <span key={st} className={`wall-tile is-off ${pos}`} aria-hidden="true"><span className="wall-tile-st">{st}</span></span>; })}</div>
    <div className="wall-legend" aria-hidden="true"><span className="r-safe">Safe R</span><span className="r-likely">Likely</span><span className="r-lean">Lean</span><span className="toss">Toss-up</span><span className="d-lean">Lean</span><span className="d-likely">Likely</span><span className="d-safe">Safe D</span></div>
  </section>;
}

function Detail({ r, m, national }: { r: WallRace; m: number; national: number }) {
  const at = marginAt(r, m); const pull = r.undertow - r.polls; const moved = Math.abs(m - national) >= 0.05;
  const parts: [string, number][] = [['Last fall’s polling miss', national], ['This state’s polling record', r.stateAdj], [r.spendLabel, r.spending], ['Early vote', r.earlyVote]];
  return <section className="wall-panel wall-detail" aria-label={`${r.name} breakdown`}>
    <div className="wall-panel-head"><p className="wall-kicker">{r.name}</p><a className="wall-link" href={`/race/${r.slug}/`}>Full race and every poll →</a></div>
    <p className="wall-matchup"><span className="is-d">{r.d} ({r.dLetter})</span> vs <span className="is-r">{r.r} (R)</span></p>
    <div className="wall-figures">
      <div><p className="wall-label">Polls</p><p className={`wall-big ${side(r.polls)}`}>{marginLabel(r.polls, r)}</p><p className="wall-sub">{r.pollCount ? `${r.pollCount} polls, weighted` : 'weighted average'}</p></div>
      <div><p className="wall-label">Undertow</p><p className={`wall-big ${side(r.undertow)}`}>{marginLabel(r.undertow, r)}</p><p className="wall-sub">± {r.sd.toFixed(1)} · my call, frozen Nov 2</p></div>
      <div><p className="wall-label">The pull</p><p className={`wall-big ${side(pull)}`}>{Math.abs(pull) < EVEN ? 'None' : `${Math.abs(pull).toFixed(1)} → ${pull > 0 ? 'D' : 'R'}`}</p><p className="wall-sub">{moved ? <>At your dial: <b className={side(at)}>{marginLabel(at, r)}</b></> : 'Undertow minus the polls'}</p></div>
    </div>
    <FactorBars parts={parts.map(([label, v]) => ({ label, v }))}/>
  </section>;
}

function Board({ races, m, selected, select }: { races: WallRace[]; m: number; selected: string; select: (id: string) => void }) {
  const rows = useMemo(() => races.map(r => ({ r, v: marginAt(r, m) })).sort((a, b) => b.v - a.v), [races, m]);
  return <section className="wall-panel wall-board" aria-label="Every race, from most Democratic to most Republican">
    <div className="wall-panel-head"><p className="wall-kicker">All {races.length} races</p><p className="wall-key"><i className="wall-key-tick"/> polls</p></div>
    <ol>{rows.map(({ r, v }) => <li key={r.id}><button type="button" className={`wall-row${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} onClick={() => select(r.id)}>
      <span className="wall-row-name">{r.state} <small>{r.office === 'SEN' ? 'Sen' : 'Gov'}</small></span>
      <MarginTrack v={v} tick={r.polls} span={BOARD_SPAN}/>
      <span className={`wall-row-v ${side(v)}`}>{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button></li>)}</ol>
  </section>;
}

export function ElectionWall({ races, national, lastFall, initial, history }: { races: WallRace[]; national: number; lastFall: number; initial: string; history: HistoryPreset[] }) {
  const [m, setM] = useState(national);
  const [office, setOffice] = useState<Office>('SEN');
  const [selected, setSelected] = useState(initial);
  const sel = races.find(r => r.id === selected) || races[0];
  const select = (id: string) => { setSelected(id); const r = races.find(x => x.id === id); if (r) setOffice(r.office); };
  return <div className="wall">
    <aside className="wall-left"><Dial m={m} setM={setM} national={national} lastFall={lastFall} history={history}/><Tally races={races} m={m}/></aside>
    <div className="wall-center"><TileMap races={races} m={m} office={office} setOffice={setOffice} selected={sel.id} select={select}/>{sel && <Detail r={sel} m={m} national={national}/>}</div>
    <aside className="wall-right"><Board races={races} m={m} selected={sel.id} select={select}/></aside>
  </div>;
}

function DialBar({ m, setM, national, lastFall, history }: { m: number; setM: (v: number) => void; national: number; lastFall: number; history: HistoryPreset[] }) {
  const span = Math.max(8, Math.ceil(lastFall));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const dir = m >= EVEN ? 'Polls understate Democrats' : m <= -EVEN ? 'Polls understate Republicans' : 'Polls miss neither way';
  const presets = presetList(history, national, lastFall);
  return <section className="wall-dialbar" aria-label="How wrong are the polls?">
    <div className="wall-dialbar-top"><span className={`wall-num wall-dialbar-num ${side(m)}`}>{Math.abs(m).toFixed(1)}</span><span className="wall-dialbar-dir">{dir}<small>How wrong are the polls? Drag to change every race.</small></span></div>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label="National polling miss in points; negative means polls understate Republicans"/>
    <div className="wall-dialbar-presets">{presets.map(([label, v]) => <button key={label} type="button" aria-pressed={near(v)} onClick={() => setM(v)}>{label}</button>)}</div>
  </section>;
}

export function MobileWall({ races, national, lastFall, history }: { races: WallRace[]; national: number; lastFall: number; history: HistoryPreset[] }) {
  const [m, setM] = useState(national);
  const [open, setOpen] = useState<string | null>(null);
  const [office, setOffice] = useState<Office>('SEN');
  const rows = useMemo(() => races.map(r => ({ r, v: marginAt(r, m) })).sort((a, b) => b.v - a.v), [races, m]);
  const pick = (id: string) => { setOpen(id); if (typeof document !== 'undefined') document.getElementById(`m-${id}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }); };
  return <div className="wall-mobile">
    <Tally races={races} m={m}/>
    <TileMap races={races} m={m} office={office} setOffice={setOffice} selected={open || ''} select={pick}/>
    <ol className="wall-mobile-list">{rows.map(({ r, v }) => <li key={r.id} id={`m-${r.id}`}>
      <button type="button" className={`wall-mrow ${shade(v)}`} aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
        <span className="wall-mrow-name">{r.name}<small>{last(r.d)} ({r.dLetter}) vs {last(r.r)} (R)</small></span>
        <span className="wall-mrow-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>
      {open === r.id && <Detail r={r} m={m} national={national}/>}
    </li>)}</ol>
    <DialBar m={m} setM={setM} national={national} lastFall={lastFall} history={history}/>
  </div>;
}
