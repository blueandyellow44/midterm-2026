'use client';
import { useMemo, useState } from 'react';
import { FactorBars, MarginTrack, pct } from './Console';

// Short ruler labels for the mobile dial (Max, 2026-10-27: horizontal scrolling of the steps confuses people).
const short = (label: string) => label.startsWith('My bet') ? 'Bet' : label.startsWith('Last fall') ? '’25' : label === 'No miss' ? '0' : `’${label.slice(2, 4)}`;
const SNAP = 0.2;

// The election-night wall (Max, 2026-10-27: "almost a console. Multi panel, don't need to scroll to slider"; "that American
// political news red and blue look"). One dial state drives every panel. Each race at dial value m = polls + m + its state
// adjustment + spending + early vote, so at m = the national lean it reproduces Undertow's frozen number exactly.
export type WallRace = {
  id: string; slug: string; state: string; office: 'SEN' | 'GOV' | 'HOUSE'; name: string; district?: string; d: string; r: string;
  polls: number; stateAdj: number; spending: number; earlyVote: number; undertow: number; sd: number; pollCount: number | null;
  spendLabel: string; dLetter: string;
};
type Office = 'SEN' | 'GOV' | 'HOUSE';
type Scope = 'competitive' | 'full';
// Every seat the full-chamber view adds beyond the tracked races (Max, 2026-10-27: "100 senate seats, 50 governors, and a bunch of
// house districts"). A projection moves with the dial exactly like a race, with the swing base standing in for the polls:
// margin = base + m + state adjustment + spending + early vote. A rated seat (untracked governors) and a seat not up are fixed.
export type WallSeat = {
  id: string; state: string; office: Office; district?: string; name: string; kind: 'projection' | 'rated' | 'not_up';
  side: 'D' | 'R' | null; base: number; stateAdj: number; spending: number; earlyVote: number; incumbency: number; shift: number; undertow: number | null;
  rating: string | null; holder: string; noPolls: boolean; slug?: string;
};
export type ChamberTotals = Record<Office, { notUp: { D: number; R: number }; majority: number | null; seats: number }>;
export type NoReadRace = { id: string; slug: string; state: string; district: string; name: string; d: string; r: string; rating: string };
const OFFICES: Office[] = ['SEN', 'GOV', 'HOUSE'];
const officeName = (o: Office) => (o === 'SEN' ? 'Senate' : o === 'GOV' ? 'Governor' : 'House');
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
export function seatMarginAt(s: WallSeat, m: number) { return s.base + m + s.stateAdj + s.spending + s.earlyVote; }
export function seatSideAt(s: WallSeat, m: number): 'D' | 'R' | null { if (s.kind !== 'projection') return s.side; const v = seatMarginAt(s, m); return v >= EVEN ? 'D' : v <= -EVEN ? 'R' : null; }
// Chamber count at dial value m: seats not up, tracked races at the dial, projections at the dial, rated seats fixed.
export function chamberCount(o: Office, races: WallRace[], seats: WallSeat[], totals: ChamberTotals, m: number) {
  const t = totals[o]; let d = t.notUp.D, r = t.notUp.R, u = 0;
  for (const x of races) if (x.office === o) { const v = marginAt(x, m); if (v >= EVEN) d++; else if (v <= -EVEN) r++; else u++; }
  for (const s of seats) if (s.office === o && s.kind !== 'not_up') { const side = seatSideAt(s, m); if (side === 'D') d++; else if (side === 'R') r++; else u++; }
  return { d, r, u, n: t.seats, majority: t.majority };
}
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

function Tally({ races, m, seats, totals, scope, setScope }: { races: WallRace[]; m: number; seats: WallSeat[]; totals: ChamberTotals | null; scope: Scope; setScope: (s: Scope) => void }) {
  const tracked = (o: Office) => { const rs = races.filter(r => r.office === o).map(r => marginAt(r, m)); return { d: rs.filter(v => v >= EVEN).length, r: rs.filter(v => v <= -EVEN).length, u: rs.filter(v => Math.abs(v) < EVEN).length, n: rs.length, majority: null as number | null }; };
  const full = scope === 'full' && totals;
  return <div className="wall-tally" aria-live="polite">
    {totals && <div className="wall-toggle wall-scope" role="group" aria-label="Which seats to count"><button type="button" aria-pressed={scope === 'competitive'} onClick={() => setScope('competitive')}>Tracked races</button><button type="button" aria-pressed={scope === 'full'} onClick={() => setScope('full')}>Full chamber</button></div>}
    {OFFICES.filter(o => races.some(r => r.office === o) || (full && totals![o].seats > 0)).map(o => { const c = full ? chamberCount(o, races, seats, totals!, m) : tracked(o); const majAt = c.majority ? pct(100 * c.majority / c.n) : null;
      return <div key={o} className="wall-tally-row"><span className="wall-tally-label">{officeName(o)}<small>{full ? `of ${c.n}` : `${c.n} tracked`}</small></span><span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${pct(100 * c.d / c.n)}`}/><i className={`is-r gw-${pct(100 * c.r / c.n)}`}/>{majAt !== null && <em className={`wall-tally-maj ga-${majAt}`}/>}</span><span className="wall-tally-num"><b className="is-d">D {c.d}</b> <b className="is-r">R {c.r}</b>{c.u > 0 && full ? <small> {c.u} even</small> : null}</span></div>; })}
    {full && <p className="wall-tally-note">Untracked seats are projections from the 2024 vote and the generic ballot, not readings, and are not graded. Senate majority 51 (a 50-50 Senate is Republican: the Vice President breaks ties); House 218.</p>}
  </div>;
}

// The House has no geography a tile map can hold at this size: districts sit in a grid grouped by state, in the same shades.
function HouseGrid({ races, noRead, seats, full, m, selected, select }: { races: WallRace[]; noRead: NoReadRace[]; seats: WallSeat[]; full: boolean; m: number; selected: string; select: (id: string) => void }) {
  const tracked = new Set([...races.map(r => r.id), ...noRead.map(n => n.id)]);
  const all = [...races.map(r => ({ id: r.id, state: r.state, district: r.district || '', r, s: null as WallSeat | null, n: null as NoReadRace | null })),
    ...noRead.map(n => ({ id: n.id, state: n.state, district: n.district, r: null as WallRace | null, s: full ? seats.find(x => x.id === n.id) || null : null, n })),
    ...(full ? seats.filter(x => x.office === 'HOUSE' && !tracked.has(x.id)).map(x => ({ id: x.id, state: x.state, district: x.district || '', r: null as WallRace | null, s: x, n: null as NoReadRace | null })) : [])]
    .sort((a, b) => a.state.localeCompare(b.state) || a.district.localeCompare(b.district));
  return <div className="wall-housegrid">{all.map(x => {
    if (x.r) { const v = marginAt(x.r, m); return <button key={x.id} type="button" className={`wall-dtile ${shade(v)}${selected === x.id ? ' is-selected' : ''}`} aria-pressed={selected === x.id} aria-label={`${x.r.name}: ${marginLabel(v, x.r)}`} onClick={() => select(x.id)}><span className="wall-tile-st">{x.state}-{x.district}</span><span className="wall-tile-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, x.r)}+${Math.abs(v).toFixed(1)}`}</span></button>; }
    if (x.s) { const v = seatMarginAt(x.s, m); return <button key={x.id} type="button" className={`wall-dtile is-proj ${shade(v)}${selected === x.id ? ' is-selected' : ''}`} aria-pressed={selected === x.id} aria-label={`${x.s.name}: projected ${seatLabel(v)}`} onClick={() => select(x.id)}><span className="wall-tile-st">{x.state}-{x.district}</span><span className="wall-tile-v">{seatLabel(v)}</span></button>; }
    const n = x.n!; return <a key={x.id} href={`/race/${n.slug}/`} className="wall-dtile is-noread" aria-label={`${n.name}: no public polls`}><span className="wall-tile-st">{x.state}-{x.district}</span><span className="wall-tile-v">no polls</span></a>; })}</div>;
}
const seatLabel = (v: number) => (Math.abs(v) < EVEN ? 'EVEN' : `${v > 0 ? 'D' : 'R'}+${Math.abs(v).toFixed(1)}`);

function TileMap({ races, m, office, setOffice, selected, select, noRead = [], seats = [], full = false }: { races: WallRace[]; m: number; office: Office; setOffice: (o: Office) => void; selected: string; select: (id: string) => void; noRead?: NoReadRace[]; seats?: WallSeat[]; full?: boolean }) {
  const byState = new Map(races.filter(r => r.office === office).map(r => [r.state, r]));
  const seatByState = new Map(full ? seats.filter(x => x.office === office && x.kind !== 'not_up').map(x => [x.state, x]) : []);
  return <section className="wall-panel wall-map" aria-label={full ? 'Map of every seat' : 'Map of tracked races'}>
    <div className="wall-panel-head"><p className="wall-kicker">{office === 'HOUSE' ? (full ? 'All 435 House seats' : 'Competitive House seats') : `The map · ${officeName(office)}${full ? ' · every seat up' : ''}`}</p>
      <div className="wall-toggle" role="group" aria-label="Office">{OFFICES.map(o => <button key={o} type="button" aria-pressed={office === o} onClick={() => setOffice(o)}>{officeName(o)}</button>)}</div></div>
    {office === 'HOUSE' ? <HouseGrid races={races.filter(r => r.office === 'HOUSE')} noRead={noRead} seats={seats} full={full} m={m} selected={selected} select={select}/> : <div className="wall-tiles">{Object.entries(TILES).map(([st, [c, rw]]) => { const r = byState.get(st); const v = r ? marginAt(r, m) : 0;
      const pos = `tc-${c} tr-${rw}`; const sx = r ? undefined : seatByState.get(st);
      if (r) return <button key={st} type="button" className={`wall-tile ${pos} ${shade(v)}${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} aria-label={`${r.name}: ${marginLabel(v, r)}`} onClick={() => select(r.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>;
      if (sx) { const sv = sx.kind === 'projection' ? seatMarginAt(sx, m) : (sx.side === 'D' ? 20 : sx.side === 'R' ? -20 : 0); const lab = sx.kind === 'projection' ? seatLabel(sv) : (sx.rating || 'rated');
        return <button key={st} type="button" className={`wall-tile is-proj ${pos} ${shade(sv)}${selected === sx.id ? ' is-selected' : ''}`} aria-pressed={selected === sx.id} aria-label={`${sx.name}: ${sx.kind === 'projection' ? `projected ${seatLabel(sv)}` : `Cook ${sx.rating}, not tracked`}`} onClick={() => select(sx.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v wall-tile-rated">{lab}</span></button>; }
      return <span key={st} className={`wall-tile is-off ${pos}`} aria-hidden="true"><span className="wall-tile-st">{st}</span></span>; })}</div>}
    {full && <p className="wall-note">Dashed tiles are projections or Cook ratings, not Undertow readings.</p>}
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

// Breakdown for a seat Undertow does not track: the projection's parts, or the rating it carries.
function SeatDetail({ s, m, national }: { s: WallSeat; m: number; national: number }) {
  if (s.kind !== 'projection') return <section className="wall-panel wall-detail" aria-label={`${s.name} rating`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p><span className="wall-badge">Not tracked</span></div>
    <p className="wall-matchup">Cook Political Report rating: <strong>{s.rating}</strong>{s.holder === 'D' || s.holder === 'R' ? <> · seat held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}</> : null}</p>
    <p className="wall-note">Governor races Undertow does not track carry Cook’s rating as given. Governor results track the presidential vote badly (in 2022 a swing projection missed them by 10.5 points on average against 4.2 for the polls), so no projection is made and the dial does not move this seat.</p>
  </section>;
  const at = seatMarginAt(s, m); const moved = Math.abs(m - national) >= 0.05;
  const parts: [string, number][] = [['Generic-ballot swing since 2024', s.shift], ['Incumbent on the ballot', s.incumbency], ['Last fall’s polling miss', national], ['This state’s polling record', s.stateAdj], ['Early vote', s.earlyVote]];
  return <section className="wall-panel wall-detail" aria-label={`${s.name} projection`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p>{s.slug ? <a className="wall-link" href={`/race/${s.slug}/`}>Race page →</a> : <span className="wall-badge">Projection</span>}</div>
    <p className="wall-matchup">{s.noPolls ? 'No public polls, so the seat is projected from its 2024 vote.' : 'Not tracked: projected from its 2024 vote, not polled.'}{s.holder === 'D' || s.holder === 'R' ? <> Held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}{s.rating ? <>, Cook: {s.rating}</> : null}.</> : null}</p>
    <div className="wall-figures">
      <div><p className="wall-label">2024 vote</p><p className={`wall-big ${side(s.base - s.shift - s.incumbency)}`}>{seatLabel(s.base - s.shift - s.incumbency)}</p><p className="wall-sub">presidential margin, these lines</p></div>
      <div><p className="wall-label">Projection</p><p className={`wall-big ${side(s.undertow ?? 0)}`}>{seatLabel(s.undertow ?? 0)}</p><p className="wall-sub">at my bet · not graded</p></div>
      <div><p className="wall-label">At your dial</p><p className={`wall-big ${side(at)}`}>{seatLabel(at)}</p><p className="wall-sub">{moved ? 'with your polling miss' : 'same as the bet'}</p></div>
    </div>
    <FactorBars parts={parts.map(([label, v]) => ({ label, v }))}/>
  </section>;
}

function Board({ races, m, selected, select, office }: { races: WallRace[]; m: number; selected: string; select: (id: string) => void; office: Office }) {
  const rows = useMemo(() => races.filter(r => r.office === office).map(r => ({ r, v: marginAt(r, m) })).sort((a, b) => b.v - a.v), [races, m, office]);
  return <section className="wall-panel wall-board" aria-label="Every race, from most Democratic to most Republican">
    <div className="wall-panel-head"><p className="wall-kicker">{officeName(office)} · {rows.length} {rows.length === 1 ? 'race' : 'races'}</p><p className="wall-key"><i className="wall-key-tick"/> polls</p></div>
    <ol>{rows.map(({ r, v }) => <li key={r.id}><button type="button" className={`wall-row${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} onClick={() => select(r.id)}>
      <span className="wall-row-name">{r.office === 'HOUSE' ? `${r.state}-${r.district}` : r.state} <small>{r.office === 'SEN' ? 'Sen' : r.office === 'GOV' ? 'Gov' : ''}</small></span>
      <MarginTrack v={v} tick={r.polls} span={BOARD_SPAN}/>
      <span className={`wall-row-v ${side(v)}`}>{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button></li>)}</ol>
  </section>;
}

export function ElectionWall({ races, national, lastFall, initial, history, noRead = [], seats = [], totals = null }: { races: WallRace[]; national: number; lastFall: number; initial: string; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null }) {
  const [m, setM] = useState(national);
  const [office, setOffice] = useState<Office>('SEN');
  const [scope, setScope] = useState<Scope>('competitive');
  const [selected, setSelected] = useState(initial);
  const full = scope === 'full' && !!totals;
  const sel = races.find(r => r.id === selected);
  const selSeat = !sel && full ? seats.find(x => x.id === selected) : undefined;
  const shown = sel || (selSeat ? undefined : races[0]);
  const select = (id: string) => { setSelected(id); const r = races.find(x => x.id === id) || seats.find(x => x.id === id); if (r) setOffice(r.office); };
  const pick = (sc: Scope) => { setScope(sc); if (sc === 'competitive' && !sel) setSelected(initial); };
  return <div className="wall">
    <aside className="wall-left"><Dial m={m} setM={setM} national={national} lastFall={lastFall} history={history}/><Tally races={races} m={m} seats={seats} totals={totals} scope={scope} setScope={pick}/></aside>
    <div className="wall-center"><TileMap races={races} m={m} office={office} setOffice={setOffice} selected={selected} select={select} noRead={noRead} seats={seats} full={full}/>{selSeat ? <SeatDetail s={selSeat} m={m} national={national}/> : shown && <Detail r={shown} m={m} national={national}/>}</div>
    <aside className="wall-right"><Board races={races} m={m} selected={selected} select={select} office={office}/></aside>
  </div>;
}

function DialBar({ m, setM, national, lastFall, history }: { m: number; setM: (v: number) => void; national: number; lastFall: number; history: HistoryPreset[] }) {
  const span = Math.max(8, Math.ceil(lastFall));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const dir = m >= EVEN ? 'Polls understate Democrats' : m <= -EVEN ? 'Polls understate Republicans' : 'Polls miss neither way';
  const presets = presetList(history, national, lastFall);
  return <section className="wall-dialbar" aria-label="How wrong are the polls?">
    <div className="wall-dialbar-top"><span className={`wall-num wall-dialbar-num ${side(m)}`}>{Math.abs(m).toFixed(1)}</span><span className="wall-dialbar-dir">{dir}<small>How wrong are the polls? Drag to change every race.</small></span></div>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => { const v = Number(e.target.value); const hit = presets.find(([, p]) => Math.abs(p - v) <= SNAP); setM(hit ? hit[1] : v); }} aria-label="National polling miss in points; negative means polls understate Republicans"/>
    <div className="wall-ruler" role="group" aria-label="Past polling misses">{presets.map(([label, v]) => <button key={label} type="button" className={`wall-ruler-mark ga-${pct(100 * (v + span) / (2 * span))}${near(v) ? ' is-on' : ''}`} aria-pressed={near(v)} aria-label={`${label}: ${Math.abs(v) < EVEN ? 'no miss' : `${Math.abs(v).toFixed(1)} points toward ${v > 0 ? 'Democrats' : 'Republicans'}`}`} onClick={() => setM(v)}><i aria-hidden="true"/><span>{short(label)}</span></button>)}</div>
  </section>;
}

export function MobileWall({ races, national, lastFall, history, noRead = [], seats = [], totals = null }: { races: WallRace[]; national: number; lastFall: number; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null }) {
  const [m, setM] = useState(national);
  const [open, setOpen] = useState<string | null>(null);
  const [office, setOffice] = useState<Office>('SEN');
  const [scope, setScope] = useState<Scope>('competitive');
  const full = scope === 'full' && !!totals;
  const openSeat = open && full ? seats.find(x => x.id === open) : undefined;
  const rows = useMemo(() => races.filter(r => r.office === office).map(r => ({ r, v: marginAt(r, m) })).sort((a, b) => b.v - a.v), [races, m, office]);
  const pick = (id: string) => { setOpen(id); if (typeof document !== 'undefined') document.getElementById(`m-${id}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }); };
  return <div className="wall-mobile">
    <Tally races={races} m={m} seats={seats} totals={totals} scope={scope} setScope={setScope}/>
    <TileMap races={races} m={m} office={office} setOffice={setOffice} selected={open || ''} select={pick} noRead={noRead} seats={seats} full={full}/>
    {openSeat && <SeatDetail s={openSeat} m={m} national={national}/>}
    <ol className="wall-mobile-list">{rows.map(({ r, v }) => <li key={r.id} id={`m-${r.id}`}>
      <button type="button" className={`wall-mrow ${shade(v)}`} aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
        <span className="wall-mrow-name">{r.name}<small>{last(r.d)} ({r.dLetter}) vs {last(r.r)} (R)</small></span>
        <span className="wall-mrow-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>
      {open === r.id && <Detail r={r} m={m} national={national}/>}
    </li>)}
    {office === 'HOUSE' && noRead.map(n => <li key={n.id}><a className="wall-mrow is-noread" href={`/race/${n.slug}/`}><span className="wall-mrow-name">{n.name}<small>{last(n.d)} (D) vs {last(n.r)} (R) · {n.rating}</small></span><span className="wall-mrow-v">no polls</span></a></li>)}</ol>
    <DialBar m={m} setM={setM} national={national} lastFall={lastFall} history={history}/>
  </div>;
}
