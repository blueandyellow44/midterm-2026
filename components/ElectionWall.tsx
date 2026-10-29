'use client';
import { surname, pollCountLabel } from '@/lib/format';
import { useMemo, useState } from 'react';
import { FactorBars, MarginTrack, pct } from './Console';
import { Hemicycle, type HemiSeat } from './Hemicycle';

// Short ruler labels for the mobile dial (Max, 2026-10-27: horizontal scrolling of the steps confuses people).
const short = (label: string) => label.startsWith('Counted') ? 'Now' : label.startsWith('My bet') ? 'Bet' : label.startsWith('Last fall') ? '’25' : label === 'No miss' ? '0' : `’${label.slice(2, 4)}`;
const SNAP = 0.2;

// The election-night wall (Max, 2026-10-27: "almost a console. Multi panel, don't need to scroll to slider"; "that American
// political news red and blue look"). One dial state drives every panel. Each race at dial value m = polls + m + its state
// adjustment + spending + early vote, so at m = the national lean it reproduces Undertow's frozen number exactly.
export type WallRace = {
  id: string; slug: string; state: string; office: 'SEN' | 'GOV' | 'HOUSE'; name: string; district?: string; d: string; r: string;
  polls: number; stateAdj: number; spending: number; earlyVote: number; partisan: number; undertow: number; sd: number; pollCount: number | null; sponsoredOnly?: boolean;
  spendLabel: string; dLetter: string;
  result?: { margin: number; called: 'D' | 'R' | null; reporting: number; settled: boolean };   // election night, from live/results.json
};
type Office = 'SEN' | 'GOV' | 'HOUSE';
// Every seat the full-chamber view adds beyond the tracked races (Max, 2026-10-27: "100 senate seats, 50 governors, and a bunch of
// house districts"). A projection moves with the dial exactly like a race, with the swing base standing in for the polls:
// margin = base + m + state adjustment + spending + early vote. A rated seat (untracked governors) and a seat not up are fixed.
export type WallSeat = {
  id: string; state: string; office: Office; district?: string; name: string; kind: 'projection' | 'rated' | 'not_up';
  side: 'D' | 'R' | null; base: number; stateAdj: number; spending: number; earlyVote: number; incumbency: number; shift: number; undertow: number | null;
  rating: string | null; holder: string; noPolls: boolean; slug?: string; d?: string; r?: string; dLetter?: string;
};
export type ChamberTotals = Record<Office, { notUp: { D: number; R: number }; majority: number | null; seats: number }>;
export type NoReadRace = { id: string; slug: string; state: string; district: string; name: string; d: string; r: string; rating: string; dLetter: string };
const OFFICES: Office[] = ['SEN', 'GOV', 'HOUSE'];
// Win probability (Max, 2026-10-29: "We can add win probability"). weight.py's correlated simulation (analysis/simulate.py)
// gives the odds at every half point of the dial; the site only reads them off and interpolates between two points.
export type Odds = { values: number[]; chambers: Partial<Record<Office, number[]>>; perRace: Record<string, number[]> };
export function oddsAt(o: Odds | null | undefined, arr: number[] | undefined, m: number): number | null {
  if (!o || !arr || arr.length !== o.values.length) return null;
  const v = o.values; if (m <= v[0]) return arr[0]; if (m >= v[v.length - 1]) return arr[arr.length - 1];
  const i = v.findIndex(x => x > m); const t = (m - v[i - 1]) / (v[i] - v[i - 1]);
  return arr[i - 1] + t * (arr[i] - arr[i - 1]);
}
export const chanceLabel = (p: number) => (p < 0.005 ? '<1%' : p > 0.995 ? '>99%' : `${Math.round(100 * p)}%`);
const officeName = (o: Office) => (o === 'SEN' ? 'Senate' : o === 'GOV' ? 'Governor' : 'House');
export type HistoryPreset = { year: number; miss_toward_d: number };
// Dial presets are real past national misses from the archive, then no miss, my bet and last fall (Max, 2026-10-27).
function presetList(history: HistoryPreset[], national: number, lastFall: number, live: LiveDial = null): [string, number][] {
  return [...(live ? [[`Counted ${live.m >= 0 ? 'D' : 'R'} ${Math.abs(live.m).toFixed(1)}`, Math.round(live.m * 10) / 10] as [string, number]] : []), ...history.map(h => [`${h.year} again`, Math.round(h.miss_toward_d * 10) / 10] as [string, number]), ['No miss', 0], [`My bet ${national.toFixed(1)}`, national], [`Last fall ${lastFall.toFixed(1)}`, lastFall]];
}
const EVEN = 0.05;
const last = surname;
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


export function marginAt(r: WallRace, m: number) { return r.result?.settled ? r.result.margin : r.polls + m + r.stateAdj + r.spending + r.earlyVote + r.partisan; }
// Election night (Max, 2026-10-28): weight.py's implied national miss from the settled races, written by set_result.py.
export type LiveDial = { m: number; settled: number; se: number | null; pollsMae: number | null; undertowMae: number | null; undertowCloser: number; pollsCloser: number } | null;
export function seatMarginAt(s: WallSeat, m: number) { return s.base + m + s.stateAdj + s.spending + s.earlyVote; }
export function seatSideAt(s: WallSeat, m: number): 'D' | 'R' | null { if (s.kind !== 'projection') return s.side; const v = seatMarginAt(s, m); return v >= EVEN ? 'D' : v <= -EVEN ? 'R' : null; }
// Chamber count at dial value m: seats not up, tracked races at the dial, projections at the dial, rated seats fixed.
export function chamberCount(o: Office, races: WallRace[], seats: WallSeat[], totals: ChamberTotals, m: number) {
  const t = totals[o]; let d = t.notUp.D, r = t.notUp.R, u = 0;
  for (const x of races) if (x.office === o) { const v = marginAt(x, m); if (v >= EVEN) d++; else if (v <= -EVEN) r++; else u++; }
  for (const s of seats) if (s.office === o && s.kind !== 'not_up') { const side = seatSideAt(s, m); if (side === 'D') d++; else if (side === 'R') r++; else u++; }
  return { d, r, u, n: t.seats, majority: t.majority };
}
// Big figures wrap between the name and the number, never inside a name (Max, 2026-10-28 screenshot: "Hyde-Smith +5.2"
// ran into the next column on desktop).
function Big({ text }: { text: string }) { const i = text.lastIndexOf(' '); const len = Math.min(20, Math.max(6, ...text.split(' ').map(w => w.length))); const cls = `big-len-${len}`; return i < 0 ? <span className={cls}>{text}</span> : <><span className={cls}>{text.slice(0, i)}</span> <span className={cls}>{text.slice(i + 1)}</span></>; }
export function marginLabel(v: number, r: WallRace) { return Math.abs(v) < EVEN ? 'Even' : `${last(v > 0 ? r.d : r.r)} +${Math.abs(v).toFixed(1)}`; }
export function shade(v: number) { const a = Math.abs(v); const side = v > 0 ? 'd' : 'r'; return a < 1 ? 'toss' : a < 4 ? `${side}-lean` : a < 9 ? `${side}-likely` : `${side}-safe`; }
const letter = (v: number, r: WallRace) => (v > 0 ? r.dLetter : 'R');
const side = (v: number) => (v >= EVEN ? 'is-d' : v <= -EVEN ? 'is-r' : 'is-even');

function Dial({ m, setM, national, lastFall, history, compact, live = null }: { m: number; setM: (v: number) => void; national: number; lastFall: number; history: HistoryPreset[]; compact?: boolean; live?: LiveDial }) {
  const span = Math.max(8, Math.ceil(lastFall));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const hit = presetList(history, national, lastFall, live).find(([, v]) => near(v));
  const mark = hit ? (hit[1] === national ? 'My bet' : hit[0].startsWith('Counted') ? 'the count so far' : hit[0]) : null;
  const dir = m >= EVEN ? 'understate Democrats' : m <= -EVEN ? 'understate Republicans' : 'miss neither way';
  return <section className={`wall-panel wall-dial${compact ? ' is-compact' : ''}`} aria-label="How wrong are the polls?">
    <p className="wall-kicker">How wrong are the polls?</p>
    <p className={`wall-dial-readout ${side(m)}`}><span className="wall-num">{Math.abs(m).toFixed(1)}</span><span className="wall-dial-unit">pts</span></p>
    <p className="wall-dial-dir">Polls {dir}{mark ? <> · <strong>{mark}</strong></> : null}</p>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label="National polling miss in points; negative means polls understate Republicans"/>
    <div className="wall-scale"><span className="is-r">◀ Republicans</span><span className="is-d">Democrats ▶</span></div>
    <div className="wall-presets">{presetList(history, national, lastFall, live).map(([label, v]) => <button key={label} type="button" aria-pressed={near(v)} onClick={() => setM(v)}><span>{label}</span><small>{Math.abs(v) < EVEN ? 'polls right' : `${Math.abs(v).toFixed(1)} toward ${v > 0 ? 'D' : 'R'}`}</small></button>)}</div>
    {!compact && (live ? <p className="wall-note"><strong>Live:</strong> the {live.settled} races counted so far put this year’s miss at {Math.abs(live.m).toFixed(1)} toward {live.m >= 0 ? 'Democrats' : 'Republicans'}{live.se !== null ? ` (± ${live.se.toFixed(1)})` : ''}. The dial starts there; counted races show their count. My graded call stays at my bet.</p> : <p className="wall-note">Slide to set this year’s national polling miss. Each race keeps its own state record, spending and early vote. The call I am graded on stays at my bet.</p>)}
  </section>;
}

// One count per chamber (Max, 2026-10-28: "people want to see that threshold cross over 50 for the Senate, and they want to see
// the whole picture"; layout ruling: "One bar, tracked band inside"). Solid ends are seats not up plus projections and
// rated seats; the hatched band in the middle is the races Undertow reads, the part the dial moves. Numbers are the chamber.
export type ChamberSplit = { dSafe: number; dPlay: number; even: number; rPlay: number; rSafe: number; n: number; majority: number | null; play: number; noPolls: number; tossUp: number };
// Scope (Max, 2026-10-28: "I want to be able to toggle between all seats and seats in this election"): 'all' is the whole
// chamber, seats not up included; 'up' counts only the contests on this year's ballot, so there is no control line.
export type Scope = 'all' | 'up';
export function chamberSplit(o: Office, races: WallRace[], seats: WallSeat[], totals: ChamberTotals, m: number, scope: Scope = 'all'): ChamberSplit {
  const t = totals[o]; const all = scope === 'all';
  const x = { dSafe: all ? t.notUp.D : 0, dPlay: 0, even: 0, rPlay: 0, rSafe: all ? t.notUp.R : 0, n: t.seats, majority: all ? t.majority : null, play: 0, noPolls: 0, tossUp: 0 };
  let up = 0;
  for (const r of races) if (r.office === o) { const v = marginAt(r, m); x.play++; up++; if (v >= EVEN) x.dPlay++; else if (v <= -EVEN) x.rPlay++; else x.even++; }
  for (const s of seats) if (s.office === o && s.kind !== 'not_up') {
    const side = seatSideAt(s, m); up++;
    if (s.noPolls) { x.play++; x.noPolls++; if (side === 'D') x.dPlay++; else if (side === 'R') x.rPlay++; else x.even++; }
    else if (side === 'D') x.dSafe++; else if (side === 'R') x.rSafe++; else { x.even++; if (s.kind === 'rated') x.tossUp++; }
  }
  if (!all) x.n = up;
  return x;
}
function ScopeToggle({ scope, setScope }: { scope: Scope; setScope: (s: Scope) => void }) {
  return <div className="scope-toggle" role="group" aria-label="Which seats to count">{(['all', 'up'] as const).map(k => <button key={k} type="button" aria-pressed={scope === k} className={scope === k ? 'is-on' : ''} onClick={() => setScope(k)}>{k === 'all' ? 'All seats' : 'Up this year'}</button>)}</div>;
}
function ControlOdds({ p }: { p: number | null }) {
  if (p === null) return null;
  const d = p >= 0.5;
  return <span className="wall-tally-odds">Chance of control: <b className={d ? 'is-d' : 'is-r'}>{d ? 'D' : 'R'} {chanceLabel(d ? p : 1 - p)}</b></span>;
}
function Tally({ races, m, seats, totals, scope = 'all', setScope, odds }: { races: WallRace[]; m: number; seats: WallSeat[]; totals: ChamberTotals | null; scope?: Scope; setScope?: (s: Scope) => void; odds?: Odds | null }) {
  const tracked = (o: Office) => { const rs = races.filter(r => r.office === o).map(r => marginAt(r, m)); const n = rs.length; return { dSafe: 0, dPlay: rs.filter(v => v >= EVEN).length, even: rs.filter(v => Math.abs(v) < EVEN).length, rPlay: rs.filter(v => v <= -EVEN).length, rSafe: 0, n, majority: null, play: n, noPolls: 0, tossUp: 0 } as ChamberSplit; };
  return <div className="wall-tally" aria-live="polite">
    {totals && setScope && <ScopeToggle scope={scope} setScope={setScope}/>}
    {OFFICES.filter(o => races.some(r => r.office === o) || (totals && totals[o].seats > 0)).map(o => { const sc: Scope = o === 'HOUSE' ? 'all' : scope; const c = totals ? chamberSplit(o, races, seats, totals, m, sc) : tracked(o); const d = c.dSafe + c.dPlay, r = c.rSafe + c.rPlay; const w = (k: number) => pct(100 * k / c.n);
      return <div key={o} className="wall-tally-row">
        <span className="wall-tally-label">{officeName(o)}<small>{totals ? (sc === 'up' ? `${c.n} up` : `of ${c.n}`) : `${c.n} tracked`}</small></span>
        <span className="wall-tally-num"><b className="is-d">D {d}</b> <b className="is-r">R {r}</b></span>
        {c.majority ? <ControlOdds p={oddsAt(odds, odds?.chambers[o], m)}/> : null}
        <span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${w(c.dSafe)}`}/><i className={`is-d-play gw-${w(c.dPlay)}`}/><i className={`is-even gw-${w(c.even)}`}/><i className={`is-r-play gw-${w(c.rPlay)}`}/><i className={`is-r gw-${w(c.rSafe)}`}/>{c.majority && <em className={`wall-tally-maj ga-${pct(100 * c.majority / c.n)}`}/>}</span>
        {totals && <span className="wall-tally-play">{c.play} in play: <b className="is-d">{c.dPlay} D</b>, <b className="is-r">{c.rPlay} R</b>{c.even - c.tossUp > 0 ? `, ${c.even - c.tossUp} even` : ''}{c.tossUp ? ` · ${c.tossUp} Cook toss-up` : ''}<span className="is-extra">{c.noPolls ? ` · ${c.noPolls} of them projected, no polls` : ''}{c.majority ? ` · ${c.majority} for control${o === 'SEN' ? ' (50-50 goes R)' : ''}` : ''}</span></span>}
      </div>; })}
    {totals && <p className="wall-tally-note wall-hide-phone">Hatched: the races I read, which the dial moves. The rest are projections. <a href="/method/#full-chamber">How</a></p>}
  </div>;
}

const seatLabel = (v: number) => (Math.abs(v) < EVEN ? 'EVEN' : `${v > 0 ? 'D' : 'R'}+${Math.abs(v).toFixed(1)}`);
const tileNum = (v: number) => (Math.abs(v) >= 10 ? Math.round(Math.abs(v)).toString() : Math.abs(v).toFixed(1));   // tiles: whole numbers from 10 up so the label fits
// Every House seat as a hemicycle dot. Tracked view: readings colored, no-poll districts hollow, untracked seats gray as
// held. Full view: untracked seats and no-poll districts take their projection. Ordering happens inside the hemicycle.
function houseSeats(races: WallRace[], noRead: NoReadRace[], seats: WallSeat[], full: boolean, m: number): HemiSeat[] {
  const tracked = new Set(races.map(r => r.id));
  const out: HemiSeat[] = races.filter(r => r.office === 'HOUSE').map(r => { const v = marginAt(r, m); return { id: r.id, label: `${r.name}: ${marginLabel(v, r)}`, v, shade: shade(v), ring: true, proj: false }; });
  for (const s of seats) {
    if (s.office !== 'HOUSE' || tracked.has(s.id)) continue;
    const n = noRead.find(x => x.id === s.id);
    if (full) { const v = seatMarginAt(s, m); out.push({ id: s.id, label: `${s.name}: projected ${seatLabel(v)}`, v, shade: shade(v), ring: !!n, proj: true }); }
    else if (n) out.push({ id: s.id, label: `${n.name}: no public polls`, v: 0, shade: 'is-noread', ring: true, proj: false });
    else out.push({ id: s.id, label: `${s.name}: not tracked (${s.holder === 'D' ? 'Democratic' : s.holder === 'R' ? 'Republican' : 'other'} seat)`, v: s.holder === 'D' ? 100 : s.holder === 'R' ? -100 : 0, shade: 'is-off', ring: false, proj: false, off: true });
  }
  return out;
}

function TileMap({ races, m, office, setOffice, selected, select, noRead = [], seats = [], full = false, hideToggle = false }: { races: WallRace[]; m: number; office: Office; setOffice: (o: Office) => void; selected: string; select: (id: string) => void; noRead?: NoReadRace[]; seats?: WallSeat[]; full?: boolean; hideToggle?: boolean }) {
  const byState = new Map(races.filter(r => r.office === office).map(r => [r.state, r]));
  const seatByState = new Map(full ? seats.filter(x => x.office === office && x.kind !== 'not_up').map(x => [x.state, x]) : []);
  return <section className="wall-panel wall-map" aria-label={full ? 'Map of every seat' : 'Map of tracked races'}>
    <div className="wall-panel-head"><p className="wall-kicker">{office === 'HOUSE' ? (full ? 'The House · all 435 seats' : 'The House · tracked seats colored, the rest as held') : `The map · ${officeName(office)}${full ? ' · every seat up' : ''}`}</p>
      {!hideToggle && <div className="wall-toggle" role="group" aria-label="Office">{OFFICES.map(o => <button key={o} type="button" aria-pressed={office === o} onClick={() => setOffice(o)}>{officeName(o)}</button>)}</div>}</div>
    {office === 'HOUSE' ? (() => { const hs = houseSeats(races, noRead, seats, full, m); const d = hs.filter(x => x.shade !== 'is-noread' && (x.v ?? 0) >= EVEN).length; const r = hs.filter(x => x.shade !== 'is-noread' && (x.v ?? 0) <= -EVEN).length;
      return <Hemicycle seats={hs} majority={218} selected={selected} select={select} dCount={d} rCount={r} count={full} title={full ? 'All 435 House seats, most Democratic to most Republican' : 'The House: tracked seats colored, others as held'}/>; })() : <div className="wall-tiles">{Object.entries(TILES).map(([st, [c, rw]]) => { const r = byState.get(st); const v = r ? marginAt(r, m) : 0;
      const pos = `tc-${c} tr-${rw}`; const sx = r ? undefined : seatByState.get(st);
      if (r) return <button key={st} type="button" className={`wall-tile ${pos} ${shade(v)}${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} aria-label={`${r.name}: ${marginLabel(v, r)}`} onClick={() => select(r.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${tileNum(v)}`}</span></button>;
      if (sx) { const sv = sx.kind === 'projection' ? seatMarginAt(sx, m) : (sx.side === 'D' ? 20 : sx.side === 'R' ? -20 : 0); const lab = sx.kind === 'projection' ? (Math.abs(sv) < EVEN ? 'EVEN' : `${sv > 0 ? 'D' : 'R'}+${tileNum(sv)}`) : (sx.rating || 'rated');
        return <button key={st} type="button" className={`wall-tile is-proj ${pos} ${shade(sv)}${selected === sx.id ? ' is-selected' : ''}`} aria-pressed={selected === sx.id} aria-label={`${sx.name}: ${sx.kind === 'projection' ? `projected ${seatLabel(sv)}` : `Cook ${sx.rating}, not tracked`}`} onClick={() => select(sx.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v wall-tile-rated">{lab}</span></button>; }
      return <span key={st} className={`wall-tile is-off ${pos}`} aria-hidden="true"><span className="wall-tile-st">{st}</span></span>; })}</div>}
    {full && !hideToggle && <p className="wall-note">{office === 'HOUSE' ? 'Ringed dots are tracked races; plain dots are projections from the 2024 vote, not readings.' : 'Dashed tiles are projections or Cook ratings, not Undertow readings.'}</p>}
    {!hideToggle && <div className="wall-legend" aria-hidden="true"><span className="r-safe">Safe R</span><span className="r-likely">Likely</span><span className="r-lean">Lean</span><span className="toss">Toss-up</span><span className="d-lean">Lean</span><span className="d-likely">Likely</span><span className="d-safe">Safe D</span></div>}
  </section>;
}

function WinChance({ r, p, moved }: { r: WallRace; p: number | null; moved: boolean }) {
  if (p === null || r.result?.settled) return null;
  return <div className="wall-chance">
    <p className="wall-label">Chance to win{moved ? ' at your dial' : ''}</p>
    <p className="wall-chance-names"><span className="is-d">{last(r.d)} {chanceLabel(p)}</span><span className="is-r">{last(r.r)} {chanceLabel(1 - p)}</span></p>
    <span className="wall-chance-bar" aria-hidden="true"><i className={`is-d gw-${pct(100 * p)}`}/><i className={`is-r gw-${100 - pct(100 * p)}`}/></span>
  </div>;
}
function Detail({ r, m, national, odds }: { r: WallRace; m: number; national: number; odds?: Odds | null }) {
  const at = marginAt(r, m); const pull = r.undertow - r.polls; const moved = Math.abs(m - national) >= 0.05 && !r.result?.settled;
  const parts: [string, number][] = [['Last fall’s polling miss', national], ['This state’s polling record', r.stateAdj], [r.spendLabel, r.spending], ['Early vote', r.earlyVote], ...(r.office === 'SEN' ? [['The state’s partisan record', r.partisan] as [string, number]] : [])];
  return <section className="wall-panel wall-detail" aria-label={`${r.name} breakdown`}>
    <div className="wall-panel-head"><p className="wall-kicker">{r.name}</p><a className="wall-link" href={`/race/${r.slug}/`}>Full race and every poll →</a></div>
    <p className="wall-matchup"><span className="is-d">{r.d} ({r.dLetter})</span> vs <span className="is-r">{r.r} (R)</span></p>
    <div className="wall-figures">
      <div><p className="wall-label">Polls</p><p className={`wall-big ${side(r.polls)}`}><Big text={marginLabel(r.polls, r)}/></p><p className="wall-sub">{pollCountLabel(r.pollCount, r.sponsoredOnly)}</p></div>
      <div><p className="wall-label">Undertow</p><p className={`wall-big ${side(r.undertow)}`}><Big text={marginLabel(r.undertow, r)}/></p><p className="wall-sub">± {r.sd.toFixed(1)} · my call, frozen Nov 2</p></div>
      {r.result ? <div><p className="wall-label">The count</p><p className={`wall-big ${side(r.result.margin)}`}><Big text={marginLabel(r.result.margin, r)}/></p><p className="wall-sub">{r.result.reporting.toFixed(0)}% counted{r.result.called ? ` · called for ${last(r.result.called === 'D' ? r.d : r.r)}` : ''}</p></div> : null}
      <div><p className="wall-label">The pull</p><p className={`wall-big ${side(pull)}`}>{Math.abs(pull) < EVEN ? 'None' : `${Math.abs(pull).toFixed(1)} → ${pull > 0 ? r.dLetter : 'R'}`}</p><p className="wall-sub">{moved ? <>At your dial: <b className={side(at)}>{marginLabel(at, r)}</b></> : 'Undertow minus the polls'}</p></div>
    </div>
    <WinChance r={r} p={oddsAt(odds, odds?.perRace[r.id], m)} moved={moved}/>
    <FactorBars parts={parts.map(([label, v]) => ({ label, v }))} dLetter={r.dLetter}/>
  </section>;
}

// Breakdown for a seat Undertow does not track: the projection's parts, or the rating it carries.
function SeatDetail({ s, m, national, full }: { s: WallSeat; m: number; national: number; full: boolean }) {
  if (!full && s.noPolls) return <section className="wall-panel wall-detail" aria-label={`${s.name}, no public polls`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p>{s.slug && <a className="wall-link" href={`/race/${s.slug}/`}>Race page and spending →</a>}</div>
    {s.d && s.r && <p className="wall-matchup"><span className="is-d">{s.d} ({s.dLetter || 'D'})</span> vs <span className="is-r">{s.r} (R)</span></p>}
    <p className="wall-matchup">No public poll since September 1 could be verified at its source.{s.rating ? <> Cook rates it <strong>{s.rating}</strong>{s.holder === 'D' || s.holder === 'R' ? <>, held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}</> : null}.</> : null}</p>
    <p className="wall-note">Listed without a number (no reading, not graded). The Full chamber view projects it from its 2024 vote.</p>
  </section>;
  if (s.kind !== 'projection') return <section className="wall-panel wall-detail" aria-label={`${s.name} rating`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p><span className="wall-badge">Not tracked</span></div>
    <p className="wall-matchup">Cook Political Report rating: <strong>{s.rating}</strong>{s.holder === 'D' || s.holder === 'R' ? <> · seat held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}</> : null}</p>
    <p className="wall-note">Governor races Undertow does not track carry Cook’s rating as given. Governor results track the presidential vote badly (in 2022 a swing projection missed them by 10.5 points on average against 4.2 for the polls), so no projection is made and the dial does not move this seat.</p>
  </section>;
  const at = seatMarginAt(s, m); const moved = Math.abs(m - national) >= 0.05;
  const parts: [string, number][] = [['Generic-ballot swing since 2024', s.shift], ['Incumbent on the ballot', s.incumbency], ['Last fall’s polling miss', national], ['This state’s polling record', s.stateAdj], ['Early vote', s.earlyVote]];
  return <section className="wall-panel wall-detail" aria-label={`${s.name} projection`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p>{s.slug ? <a className="wall-link" href={`/race/${s.slug}/`}>Race page →</a> : <span className="wall-badge">Projection</span>}</div>
    {s.d && s.r && <p className="wall-matchup"><span className="is-d">{s.d} ({s.dLetter || 'D'})</span> vs <span className="is-r">{s.r} (R)</span></p>}
    <p className="wall-matchup">{s.noPolls ? 'No public polls, so the seat is projected from its 2024 vote.' : 'Not tracked: projected from its 2024 vote, not polled.'}{s.holder === 'D' || s.holder === 'R' ? <> Held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}{s.rating ? <>, Cook: {s.rating}</> : null}.</> : null}</p>
    <div className="wall-figures">
      <div><p className="wall-label">2024 vote</p><p className={`wall-big ${side(s.base - s.shift - s.incumbency)}`}>{seatLabel(s.base - s.shift - s.incumbency)}</p><p className="wall-sub">presidential margin, these lines</p></div>
      <div><p className="wall-label">Projection</p><p className={`wall-big ${side(s.undertow ?? 0)}`}>{seatLabel(s.undertow ?? 0)}</p><p className="wall-sub">at my bet · not graded</p></div>
      <div><p className="wall-label">At your dial</p><p className={`wall-big ${side(at)}`}>{seatLabel(at)}</p><p className="wall-sub">{moved ? 'with your polling miss' : 'same as the bet'}</p></div>
    </div>
    <FactorBars parts={parts.map(([label, v]) => ({ label, v }))} dLetter={s.dLetter}/>
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

export function ElectionWall({ races, national, lastFall, initial, history, noRead = [], seats = [], totals = null, live = null, odds = null }: { races: WallRace[]; national: number; lastFall: number; initial: string; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null; live?: LiveDial; odds?: Odds | null }) {
  const [m, setM] = useState(live ? live.m : national);
  const [office, setOffice] = useState<Office>('SEN');
  const [selected, setSelected] = useState(initial);
  const [scope, setScope] = useState<Scope>('all');
  const full = !!totals;
  const sel = races.find(r => r.id === selected);
  const selSeat = !sel ? seats.find(x => x.id === selected) : undefined;
  const shown = sel || (selSeat ? undefined : races[0]);
  const select = (id: string) => { setSelected(id); const r = races.find(x => x.id === id) || seats.find(x => x.id === id); if (r) setOffice(r.office); };
  return <div className="wall">
    <div className="wall-top"><Tally races={races} m={m} seats={seats} totals={totals} scope={scope} setScope={setScope} odds={live ? null : odds}/></div>
    <aside className="wall-left"><Dial m={m} setM={setM} national={national} lastFall={lastFall} history={history} live={live}/></aside>
    <div className="wall-center"><TileMap races={races} m={m} office={office} setOffice={setOffice} selected={selected} select={select} noRead={noRead} seats={seats} full={full}/>{selSeat ? <SeatDetail s={selSeat} m={m} national={national} full={full}/> : shown && <Detail r={shown} m={m} national={national} odds={live ? null : odds}/>}</div>
    <aside className="wall-right"><Board races={races} m={m} selected={selected} select={select} office={office}/></aside>
  </div>;
}

function DialBar({ m, setM, national, lastFall, history, live = null }: { m: number; setM: (v: number) => void; national: number; lastFall: number; history: HistoryPreset[]; live?: LiveDial }) {
  const span = Math.max(8, Math.ceil(lastFall));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const dir = m >= EVEN ? 'Polls understate Democrats' : m <= -EVEN ? 'Polls understate Republicans' : 'Polls miss neither way';
  const presets = presetList(history, national, lastFall, live);
  return <section className="wall-dialbar" aria-label="How wrong are the polls?">
    <div className="wall-dialbar-top"><span className={`wall-num wall-dialbar-num ${side(m)}`}>{Math.abs(m).toFixed(1)}</span><span className="wall-dialbar-dir">{dir}<small>How wrong are the polls? Drag to change every race.</small></span></div>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => { const v = Number(e.target.value); const hit = presets.find(([, p]) => Math.abs(p - v) <= SNAP); setM(hit ? hit[1] : v); }} aria-label="National polling miss in points; negative means polls understate Republicans"/>
    <div className="wall-ruler" role="group" aria-label="Past polling misses">{presets.map(([label, v]) => <button key={label} type="button" className={`wall-ruler-mark ga-${pct(100 * (v + span) / (2 * span))}${near(v) ? ' is-on' : ''}`} aria-pressed={near(v)} aria-label={`${label}: ${Math.abs(v) < EVEN ? 'no miss' : `${Math.abs(v).toFixed(1)} points toward ${v > 0 ? 'Democrats' : 'Republicans'}`}`} onClick={() => setM(v)}><i aria-hidden="true"/><span>{short(label)}</span></button>)}</div>
  <div className="phone-key" aria-hidden="true"><span className="phone-key-bar"><i className="r-safe"/><i className="r-likely"/><i className="r-lean"/><i className="toss"/><i className="d-lean"/><i className="d-likely"/><i className="d-safe"/></span><span className="phone-key-labels"><b>Safe R</b><b>Toss-up</b><b>Safe D</b></span></div>
  </section>;
}

// Phone first screen (Max, 2026-10-28: "How do other sites get it all to fit on the landing screen?" -> "Build it"): three chamber
// chips that switch both the numbers and the map, and one full bar for the selected chamber.
function PhoneChambers({ races, m, seats, totals, office, setOffice, odds }: { races: WallRace[]; m: number; seats: WallSeat[]; totals: ChamberTotals; office: Office; setOffice: (o: Office) => void; odds?: Odds | null }) {
  const [scope, setScope] = useState<Scope>('all'); const sc: Scope = office === 'HOUSE' ? 'all' : scope;
  const c = chamberSplit(office, races, seats, totals, m, sc); const d = c.dSafe + c.dPlay, r = c.rSafe + c.rPlay; const w = (k: number) => pct(100 * k / c.n);
  return <section className="wall-tally phone-chambers" aria-live="polite">
    <div className="phone-chips" role="tablist" aria-label="Chamber">{OFFICES.map(o => { const x = chamberSplit(o, races, seats, totals, m, o === 'HOUSE' ? 'all' : scope); return <button key={o} type="button" role="tab" aria-selected={office === o} className={office === o ? 'is-on' : ''} onClick={() => setOffice(o)}><span>{o === 'GOV' ? 'Governors' : officeName(o)}</span><b><i className="is-d">D {x.dSafe + x.dPlay}</i> <i className="is-r">R {x.rSafe + x.rPlay}</i></b></button>; })}</div>
    <div className="wall-tally-row">
      <span className="wall-tally-label">{office === 'GOV' ? 'Governors' : officeName(office)}<small>{sc === 'up' ? `${c.n} up` : `of ${c.n}`}</small></span>
      <span className="wall-tally-num"><b className="is-d">D {d}</b> <b className="is-r">R {r}</b></span>
      {c.majority ? <ControlOdds p={oddsAt(odds, odds?.chambers[office], m)}/> : null}
      <span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${w(c.dSafe)}`}/><i className={`is-d-play gw-${w(c.dPlay)}`}/><i className={`is-even gw-${w(c.even)}`}/><i className={`is-r-play gw-${w(c.rPlay)}`}/><i className={`is-r gw-${w(c.rSafe)}`}/>{c.majority && <em className={`wall-tally-maj ga-${pct(100 * c.majority / c.n)}`}/>}</span>
      <span className="wall-tally-play">{c.play} in play: <b className="is-d">{c.dPlay} D</b>, <b className="is-r">{c.rPlay} R</b>{c.even - c.tossUp > 0 ? `, ${c.even - c.tossUp} even` : ''}{c.tossUp ? ` · ${c.tossUp} Cook toss-up` : ''}{c.majority ? ` · ${c.majority} for control${office === 'SEN' ? ' (50-50 goes R)' : ''}` : ''}</span>
    </div>
    {office !== 'HOUSE' && <ScopeToggle scope={scope} setScope={setScope}/>}
  </section>;
}

export function MobileWall({ races, national, lastFall, history, noRead = [], seats = [], totals = null, live = null, odds = null }: { races: WallRace[]; national: number; lastFall: number; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null; live?: LiveDial; odds?: Odds | null }) {
  const [m, setM] = useState(live ? live.m : national);
  const [open, setOpen] = useState<string | null>(null);
  const [office, setOffice] = useState<Office>('SEN');
  const full = !!totals;
  const openSeat = open && !races.some(r => r.id === open) ? seats.find(x => x.id === open) : undefined;
  const rows = useMemo(() => races.filter(r => r.office === office).map(r => ({ r, v: marginAt(r, m) })).sort((a, b) => b.v - a.v), [races, m, office]);
  const pick = (id: string) => { setOpen(id); if (typeof document !== 'undefined') document.getElementById(`m-${id}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }); };
  return <div className="wall-mobile">
    {totals ? <PhoneChambers races={races} m={m} seats={seats} totals={totals} office={office} setOffice={setOffice} odds={live ? null : odds}/> : <Tally races={races} m={m} seats={seats} totals={totals}/>}
    <TileMap races={races} m={m} office={office} setOffice={setOffice} selected={open || ''} select={pick} noRead={noRead} seats={seats} full={full} hideToggle={!!totals}/>
    {openSeat && <SeatDetail s={openSeat} m={m} national={national} full={full}/>}
    <ol className="wall-mobile-list">{rows.map(({ r, v }) => <li key={r.id} id={`m-${r.id}`}>
      <button type="button" className={`wall-mrow ${shade(v)}`} aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
        <span className="wall-mrow-name">{r.name}<small>{last(r.d)} ({r.dLetter}) vs {last(r.r)} (R)</small></span>
        <span className="wall-mrow-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>
      {open === r.id && <Detail r={r} m={m} national={national} odds={live ? null : odds}/>}
    </li>)}
    {office === 'HOUSE' && noRead.map(n => <li key={n.id}><a className="wall-mrow is-noread" href={`/race/${n.slug}/`}><span className="wall-mrow-name">{n.name}<small>{last(n.d)} ({n.dLetter}) vs {last(n.r)} (R) · {n.rating}</small></span><span className="wall-mrow-v">no polls</span></a></li>)}</ol>
    <DialBar m={m} setM={setM} national={national} lastFall={lastFall} history={history} live={live}/>
  </div>;
}
