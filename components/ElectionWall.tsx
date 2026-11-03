'use client';
import { surname, pollCountLabel } from '@/lib/format';
import { useMemo, useState, useRef } from 'react';
import { FactorBars, MarginTrack, pct } from './Console';
import { Hemicycle, type HemiSeat } from './Hemicycle';

// Short ruler labels for the mobile dial (Max, 2026-10-27: horizontal scrolling of the steps confuses people).
const SNAP = 0.2;

// The election-night wall (Max, 2026-10-27: "almost a console. Multi panel, don't need to scroll to slider"; "that American
// political news red and blue look"). One dial state drives every panel. Each race at dial value m = polls + m + its state
// adjustment + spending + early vote, so at m = the national lean it reproduces Undertow's frozen number exactly.
// Two independent choices, one canonical state each (audit 2026-10-31): `model` picks WHICH reading (the bet's arithmetic, or a
// center set from derived.models) and `m` is the national shift added to it. Presets and the slider set m only; a chip sets
// model and resets m to that reading's default. Nothing here can change the graded call: it is read from the sealed release.
export type WallRace = {
  id: string; slug: string; state: string; office: 'SEN' | 'GOV' | 'HOUSE'; name: string; district?: string; d: string; r: string;
  polls: number; stateAdj: number; spending: number; earlyVote: number; partisan: number; undertow: number; sd: number; pollCount: number | null; sponsoredOnly?: boolean;
  spendLabel: string; dLetter: string;
  result?: { margin: number; called: 'D' | 'R' | null; reporting: number; settled: boolean };   // election night, from live/results.json
};
type Office = 'SEN' | 'GOV' | 'HOUSE';
// Every seat the full-chamber view adds beyond the tracked races (Max, 2026-10-27: "100 senate seats, 50 governors, and a bunch of
// house districts"). A projection moves with the dial exactly like a race, with the swing base standing in for the polls:
// margin = base + m + state adjustment + spending + early vote. A seat not up is fixed. A rated seat (an untracked governor)
// sits at its Cook rating's center at the bet's resting dial and moves with the dial from there (Max, 2026-11-03, on a reader
// finding the slider never moved Texas governor: "That is inexcusable"); it was fixed under the bet from 2026-10-27.
export type WallSeat = {
  id: string; state: string; office: Office; district?: string; name: string; kind: 'projection' | 'rated' | 'not_up';
  side: 'D' | 'R' | null; base: number; stateAdj: number; spending: number; earlyVote: number; incumbency: number; shift: number; undertow: number | null;
  rating: string | null; holder: string; noPolls: boolean; slug?: string; d?: string; r?: string; dLetter?: string;
  // A rated seat sits at its Cook center when the dial is at `rest` (the bet's lean) and moves point for point from there.
  rest?: number;
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
// Other ways to read the same polls (Max, 2026-10-29: "what if we made our own?"; "Go"). A model is a center for every seat up
// (derived.models, built by analysis/models.py) plus its own odds grid; the dial adds m to every center. 'bet' is the site's own
// reading and the only graded call. The site never computes a center or an odds number; it reads them.
export type Centers = Record<string, number> | null;
export type ModelDef = { key: string; name: string; short: string; desc: string; defaultDial: number; centers: Record<string, number>; odds: Odds | null };
// One sentence per reading, shown under the chips when it is picked (Max, 2026-10-29: "describe each model somewhere on landing page, best if upon toggle").
export const BET_DESC = 'A polling average plus a declared lean: my call on how the polls are wrong this year, stated before the vote and graded after it, beside the polls themselves.';
// Seat counts and control odds at one dial setting (Max, 2026-10-29: "comparison and strip"; "I like everything on the landing page
// changing the maps and numbers"). Years are scenarios: the same model at a past year's miss. Other forecasters never move the
// map, so they live on the Method page (/method/#field).
export type Notch = { sD: number; sR: number; hD: number; hR: number; pS: number | null; pH: number | null };
export function notchAt(races: WallRace[], seats: WallSeat[], totals: ChamberTotals | null, odds: Odds | null | undefined, v: number, c: Centers = null): Notch | null {
  if (!totals) return null;
  const s = chamberSplit('SEN', races, seats, totals, v, 'all', c), h = chamberSplit('HOUSE', races, seats, totals, v, 'all', c);
  return { sD: s.dSafe + s.dPlay, sR: s.rSafe + s.rPlay, hD: h.dSafe + h.dPlay, hR: h.rSafe + h.rPlay, pS: oddsAt(odds, odds?.chambers.SEN, v), pH: oddsAt(odds, odds?.chambers.HOUSE, v) };
}
// Each reading carries its own scenario (Max, 2026-10-31: "models and past years are very different things, no?"; "chips +
// slider on both. build it"). The chips pick the reading; the slider below asks the question that reading can answer, and its
// marks, preset buttons and words come from here. The slider's value m is still ONE uniform shift added to every seat of the
// active reading (the sealed odds grids are built on exactly that), so switching the words never changes the arithmetic.
//   bet, polls, blend  a national polling miss; marks are past years' misses from the archive, no miss, the bet's lean (bet only),
//                      last fall. The blend's prior is set by this year's polls, so a national miss moves all of it.
//   fundamentals       no polls in it, so the scenario is which past midterm this year looks like: marks from the sealed swing
//                      table (derived.models.fundamentals_env.years), the average at the default.
//   ratings            Cook's calls a level or two too far one way; one level = the release's Lean center (simulation.rated_center).
export type Tick = { label: string; name: string; v: number; sub: string; ruler?: boolean };
export type Scenario = { key: string; question: string; unit: string; scope: 'race' | 'seat'; tableHead: string; left: string; right: string; zero: string; note: string; aria: string; ticks: Tick[]; show: (m: number) => string; dir: (m: number) => string };
export type ScenarioExtras = { fundYears?: Record<string, number>; fundDefault?: number; level?: number };
export type ScenarioCtx = { history: HistoryPreset[]; national: number; lastFall: number; live?: LiveDial; extras?: ScenarioExtras };
// One decimal, except a miss under 0.1 shows two so it does not read as zero (2018 at 0.08; Max, 2026-11-01: "if it was -.08 reflect that").
const pts = (v: number) => Math.abs(v).toFixed(v !== 0 && Math.abs(v) < 0.1 ? 2 : 1);
const toward = (v: number) => `polls under ${v > 0 ? 'D' : 'R'} by ${pts(v)}`;
const yy = (y: string | number) => `’${String(y).slice(2, 4)}`;
// The accessible value says what the readout says (Fundamentals shows the swing, not the native offset; audit 2026-10-31).
export const valueText = (sc: Scenario, m: number) => `${sc.show(m)} ${sc.unit}, ${sc.dir(m)}`;
export function scenarioFor(key: string, ctx: ScenarioCtx): Scenario {
  const { history, national, lastFall, live = null, extras = {} } = ctx;
  if (key === 'fundamentals') {
    const base = Number.isFinite(extras.fundDefault) ? (extras.fundDefault as number) : 0;
    const years = Object.entries(extras.fundYears || {}).map(([y, v]) => ({ y, m: Math.round((Number(v) - base) * 10) / 10 })).filter(x => Number.isFinite(x.m)).sort((a, b) => a.m - b.m);
    const ticks: Tick[] = [];
    for (const x of years) {   // two midterms within half a point share one mark (2006 and 2010 both land near 11)
      const near = ticks.find(t => Math.abs(t.v - x.m) <= 0.5);
      if (near) { near.label += `/${yy(x.y)}`; near.name = near.name.replace(/ again$/, '') + ` or ${x.y} again`; continue; }
      ticks.push({ label: yy(x.y), name: `${x.y} again`, v: x.m, sub: `${(base + x.m).toFixed(1)} pt swing` });
    }
    ticks.push({ label: 'Avg', name: 'Average midterm', v: 0, sub: `${base.toFixed(1)} pt swing` });
    ticks.sort((a, b) => a.v - b.v);
    return { key, question: 'Which midterm does this year look like?', unit: 'pt swing', scope: 'seat', tableHead: 'If the year swings like…', left: '◀ Gentler', right: 'Harsher ▶', zero: 'At the average midterm swing',
      note: 'Pick a past midterm or set your own swing. Every seat follows.', aria: 'Midterm swing against the president’s party, in points', ticks,
      show: m => (base + m).toFixed(1), dir: m => m >= EVEN ? 'Harsher on the president’s party than average' : m <= -EVEN ? 'Gentler on the president’s party than average' : 'The average midterm penalty' };
  }
  if (key === 'ratings') {
    const L = Number.isFinite(extras.level) && (extras.level as number) > 0 ? (extras.level as number) : 3.5;
    const lv = (k: number) => `${Math.abs(k)} ${Math.abs(k) === 1 ? 'level' : 'levels'} toward ${k > 0 ? 'D' : 'R'}`;
    const ticks: Tick[] = [-2, -1, 0, 1, 2].map(k => k === 0 ? { label: 'As is', name: 'As published', v: 0, sub: 'as published' } : { label: `${Math.abs(k)}${k > 0 ? 'D' : 'R'}`, name: lv(k).replace(/^(\d)/, d => ['', 'One', 'Two'][Number(d)]), v: k * L, sub: toward(k * L) });
    return { key, question: 'If Cook’s calls run too far one way', unit: 'pts', scope: 'seat', tableHead: 'If Cook is off by…', left: '◀ Too Democratic', right: 'Too Republican ▶', zero: 'Ratings as published',
      note: 'Test Cook’s calls a level or two off. Every rated seat follows.', aria: 'Rating miss in points; negative means the ratings run too Democratic', ticks,
      show: m => Math.abs(m).toFixed(1), dir: m => m >= EVEN ? `Ratings too Republican by ${(Math.abs(m) / L).toFixed(1)} levels` : m <= -EVEN ? `Ratings too Democratic by ${(Math.abs(m) / L).toFixed(1)} levels` : 'Ratings as published' };
  }
  const ticks: Tick[] = [
    ...(live ? [{ label: 'Now', name: `Counted ${live.m >= 0 ? 'D' : 'R'} ${Math.abs(live.m).toFixed(1)}`, v: Math.round(live.m * 10) / 10, sub: 'the count so far' }] : []),
    // its own button at its real miss; a year too close to zero to draw apart on the phone ruler stays off the ruler (2018)
    ...history.map(h => { const v = Math.abs(h.miss_toward_d) < 0.1 ? Math.round(h.miss_toward_d * 100) / 100 : Math.round(h.miss_toward_d * 10) / 10; return { label: yy(h.year), name: `${h.year} again`, v, sub: toward(v), ruler: Math.abs(v) > 0.5 }; }),
    { label: '0', name: 'No miss', v: 0, sub: key === 'bet' ? 'no national miss' : key === 'polls' ? 'polls right' : 'no miss' },
    ...(key === 'bet' ? [{ label: 'Bet', name: `My bet ${national.toFixed(1)}`, v: national, sub: toward(national) }] : []),
    { label: '’25', name: `Last fall ${lastFall.toFixed(1)}`, v: lastFall, sub: toward(lastFall) },
  ].sort((a, b) => a.v - b.v);
  return { key, question: 'How wrong are the polls?', unit: 'pts', scope: 'race', tableHead: 'If the polls miss like…', left: '◀ Polls under R', right: 'Polls under D ▶',
    zero: key === 'bet' ? 'With no national miss' : key === 'polls' ? 'If the polls are right' : 'Forecaster blend, no miss',
    note: 'Pick a past year’s miss or set your own. Every race and seat follows; untracked governors start from Cook’s rating.', aria: 'National polling miss in points; negative means polls understate Republicans', ticks,
    show: m => pts(m), dir: m => m >= EVEN ? 'Polls understate Democrats' : m <= -EVEN ? 'Polls understate Republicans' : 'Polls miss neither way' };
}
// Picking a reading (Max, 2026-10-29: "picking a model sets the dial to 0"): each model's headline is its own center set
// at its default dial, so the pick resets m to that default; the bet restores its lean (or the counted miss on election night).
export function pickModel(models: ModelDef[], key: string, national: number, live: LiveDial = null): { model: string; m: number } {
  const d = models.find(x => x.key === key);
  return d ? { model: key, m: d.defaultDial } : { model: 'bet', m: live ? live.m : national };
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


export function marginAt(r: WallRace, m: number, c: Centers = null) { if (r.result?.settled) return r.result.margin; const x = c?.[r.id]; return typeof x === 'number' ? x + m : r.polls + m + r.stateAdj + r.spending + r.earlyVote + r.partisan; }
// Election night (Max, 2026-10-28): weight.py's implied national miss from the settled races, written by set_result.py.
export type LiveDial = { m: number; settled: number; se: number | null; pollsMae: number | null; undertowMae: number | null; undertowCloser: number; pollsCloser: number } | null;
export function seatMarginAt(s: WallSeat, m: number, c: Centers = null) { const x = c?.[s.id]; if (typeof x === 'number') return x + m; if (s.kind === 'rated') return s.rest === undefined ? (s.side === 'D' ? 20 : s.side === 'R' ? -20 : 0) : s.base + m - s.rest; return s.base + m + s.stateAdj + s.spending + s.earlyVote; }
export function seatSideAt(s: WallSeat, m: number, c: Centers = null): 'D' | 'R' | null { if ((s.kind === 'not_up' || (s.kind === 'rated' && s.rest === undefined)) && typeof c?.[s.id] !== 'number') return s.side; const v = seatMarginAt(s, m, c); return v >= EVEN ? 'D' : v <= -EVEN ? 'R' : null; }
// Chamber count at dial value m: seats not up, tracked races, projections and rated seats at the dial.
export function chamberCount(o: Office, races: WallRace[], seats: WallSeat[], totals: ChamberTotals, m: number, c: Centers = null) {
  const t = totals[o]; let d = t.notUp.D, r = t.notUp.R, u = 0;
  for (const x of races) if (x.office === o) { const v = marginAt(x, m, c); if (v >= EVEN) d++; else if (v <= -EVEN) r++; else u++; }
  for (const s of seats) if (s.office === o && s.kind !== 'not_up') { const side = seatSideAt(s, m, c); if (side === 'D') d++; else if (side === 'R') r++; else u++; }
  return { d, r, u, n: t.seats, majority: t.majority };
}
// Big figures wrap between the name and the number, never inside a name (Max, 2026-10-28 screenshot: "Hyde-Smith +5.2"
// ran into the next column on desktop).
function Big({ text }: { text: string }) { const i = text.lastIndexOf(' '); const len = Math.min(20, Math.max(6, ...text.split(' ').map(w => w.length))); const cls = `big-len-${len}`; return i < 0 ? <span className={cls}>{text}</span> : <><span className={cls}>{text.slice(0, i)}</span> <span className={cls}>{text.slice(i + 1)}</span></>; }
export function marginLabel(v: number, r: WallRace) { return Math.abs(v) < EVEN ? 'Even' : `${last(v > 0 ? r.d : r.r)} +${Math.abs(v).toFixed(1)}`; }
export function shade(v: number) { const a = Math.abs(v); const side = v > 0 ? 'd' : 'r'; return a < 1 ? 'toss' : a < 4 ? `${side}-lean` : a < 9 ? `${side}-likely` : `${side}-safe`; }
const letter = (v: number, r: WallRace) => (v > 0 ? r.dLetter : 'R');
const side = (v: number) => (v >= EVEN ? 'is-d' : v <= -EVEN ? 'is-r' : 'is-even');

// Whose reading? (Max, 2026-10-29: "Go" on in-house models). The bet is the default and the only graded call; the others are
// other ways to read the same polls, built from the same sealed data, each with a backtest on the Method page.
function ModelChips({ models, model, pick }: { models: ModelDef[]; model: string; pick: (k: string) => void }) {
  if (!models.length) return null;
  const cur = models.find(x => x.key === model);
  return <div className="wall-models-wrap">
    <div className="wall-models" role="group" aria-label="Whose reading?">
      <button type="button" aria-pressed={model === 'bet'} className={model === 'bet' ? 'is-on' : ''} onClick={() => pick('bet')}>My bet</button>
      {models.map(x => <button key={x.key} type="button" aria-pressed={model === x.key} className={model === x.key ? 'is-on' : ''} onClick={() => pick(x.key)} title={x.name}>{x.short}</button>)}
    </div>
    <p className="wall-models-desc" aria-live="polite"><strong>{cur ? cur.name : 'My bet'}.</strong> {cur ? cur.desc : BET_DESC} <a href="/method/#models">{cur ? 'Its record →' : 'How →'}</a></p>
  </div>;
}
function Dial({ m, setM, sc, compact, live = null, chips = null }: { m: number; setM: (v: number) => void; sc: Scenario; compact?: boolean; live?: LiveDial; chips?: React.ReactNode }) {
  const span = Math.max(8, ...sc.ticks.map(t => Math.ceil(Math.abs(t.v))));
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const hit = sc.ticks.find(t => near(t.v));
  return <section className={`wall-panel wall-dial${compact ? ' is-compact' : ''}`} aria-label={sc.question}>
    {chips}
    <p className="wall-kicker">{sc.question}</p>
    <p className={`wall-dial-readout ${side(m)}`}><span className="wall-num">{sc.show(m)}</span><span className="wall-dial-unit">{sc.unit}</span></p>
    <p className="wall-dial-dir">{sc.dir(m)}{hit ? <> · <strong>{hit.name}</strong></> : null}</p>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label={sc.aria} aria-valuetext={valueText(sc, m)}/>
    <div className="wall-scale"><span className="is-r">{sc.left}</span><span className="is-d">{sc.right}</span></div>
    <div className="wall-presets">{sc.ticks.map(t => <button key={t.name} type="button" aria-pressed={near(t.v)} onClick={() => setM(t.v)}><span>{t.name}</span><small>{t.sub}</small></button>)}</div>
    {!compact && (live ? <p className="wall-note"><strong>Live:</strong> the {live.settled} races counted so far put this year’s miss at {Math.abs(live.m).toFixed(1)} toward {live.m >= 0 ? 'Democrats' : 'Republicans'}{live.se !== null ? ` (± ${live.se.toFixed(1)})` : ''}. The dial starts there; counted races show their count.</p> : <p className="wall-note">{sc.note}</p>)}
  </section>;
}

// One count per chamber (Max, 2026-10-28: "people want to see that threshold cross over 50 for the Senate, and they want to see
// the whole picture"; layout ruling: "One bar, tracked band inside"). Solid ends are seats not up plus projections and
// rated seats; the hatched band in the middle is the races Undertow reads, the part the dial moves. Numbers are the chamber.
export type ChamberSplit = { dSafe: number; dPlay: number; even: number; evenPlay: number; rPlay: number; rSafe: number; n: number; majority: number | null; play: number; noPolls: number; tossUp: number };
// Scope (Max, 2026-10-28: "I want to be able to toggle between all seats and seats in this election"): 'all' is the whole
// chamber, seats not up included; 'up' counts only the contests on this year's ballot, so there is no control line.
export type Scope = 'all' | 'up';
export function chamberSplit(o: Office, races: WallRace[], seats: WallSeat[], totals: ChamberTotals, m: number, scope: Scope = 'all', c: Centers = null): ChamberSplit {
  const t = totals[o]; const all = scope === 'all';
  const x = { dSafe: all ? t.notUp.D : 0, dPlay: 0, even: 0, evenPlay: 0, rPlay: 0, rSafe: all ? t.notUp.R : 0, n: t.seats, majority: all ? t.majority : null, play: 0, noPolls: 0, tossUp: 0 };
  let up = 0;
  for (const r of races) if (r.office === o) { const v = marginAt(r, m, c); x.play++; up++; if (v >= EVEN) x.dPlay++; else if (v <= -EVEN) x.rPlay++; else { x.even++; x.evenPlay++; } }
  for (const s of seats) if (s.office === o && s.kind !== 'not_up') {
    const side = seatSideAt(s, m, c); up++;
    if (s.noPolls) { x.play++; x.noPolls++; if (side === 'D') x.dPlay++; else if (side === 'R') x.rPlay++; else { x.even++; x.evenPlay++; } }
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
function Tally({ races, m, seats, totals, scope = 'all', setScope, odds, c = null }: { races: WallRace[]; m: number; seats: WallSeat[]; totals: ChamberTotals | null; scope?: Scope; setScope?: (s: Scope) => void; odds?: Odds | null; c?: Centers }) {
  const tracked = (o: Office) => { const rs = races.filter(r => r.office === o).map(r => marginAt(r, m, c)); const n = rs.length; const ev = rs.filter(v => Math.abs(v) < EVEN).length; return { dSafe: 0, dPlay: rs.filter(v => v >= EVEN).length, even: ev, evenPlay: ev, rPlay: rs.filter(v => v <= -EVEN).length, rSafe: 0, n, majority: null, play: n, noPolls: 0, tossUp: 0 } as ChamberSplit; };
  return <div className="wall-tally" aria-live="polite">
    {totals && setScope && <ScopeToggle scope={scope} setScope={setScope}/>}
    {OFFICES.filter(o => races.some(r => r.office === o) || (totals && totals[o].seats > 0)).map(o => { const sc: Scope = o === 'HOUSE' ? 'all' : scope; const cs = totals ? chamberSplit(o, races, seats, totals, m, sc, c) : tracked(o); const d = cs.dSafe + cs.dPlay, r = cs.rSafe + cs.rPlay; const w = (k: number) => pct(100 * k / cs.n);
      return <div key={o} className="wall-tally-row">
        <span className="wall-tally-label">{officeName(o)}<small>{totals ? (sc === 'up' ? `${cs.n} up` : `of ${cs.n}`) : `${cs.n} tracked`}</small></span>
        <span className="wall-tally-num"><b className="is-d">D {d}</b> <b className="is-r">R {r}</b></span>
        {cs.majority ? <ControlOdds p={oddsAt(odds, odds?.chambers[o], m)}/> : null}
        <span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${w(cs.dSafe)}`}/><i className={`is-d-play gw-${w(cs.dPlay)}`}/><i className={`is-even gw-${w(cs.even)}`}/><i className={`is-r-play gw-${w(cs.rPlay)}`}/><i className={`is-r gw-${w(cs.rSafe)}`}/>{cs.majority && <em className={`wall-tally-maj ga-${pct(100 * cs.majority / cs.n)}`}/>}</span>
        {totals && <span className="wall-tally-play">{cs.play} in play: <b className="is-d">{cs.dPlay} D</b>, <b className="is-r">{cs.rPlay} R</b>{cs.evenPlay > 0 ? `, ${cs.evenPlay} even` : ''}{cs.even - cs.evenPlay - cs.tossUp > 0 ? ` · ${cs.even - cs.evenPlay - cs.tossUp} projected ${cs.even - cs.evenPlay - cs.tossUp === 1 ? 'seat' : 'seats'} even` : ''}{cs.tossUp ? ` · ${cs.tossUp} Cook toss-up` : ''}<span className="is-extra">{cs.noPolls ? ` · ${cs.noPolls} of them projected, no polls` : ''}{o === 'HOUSE' && cs.n > cs.play ? ` · the other ${cs.n - cs.play} are projections or Cook ratings, not my reading` : ''}{cs.majority ? ` · ${cs.majority} seats to control${o === 'SEN' ? '; a 50-50 tie goes to R' : ''}` : ''}</span></span>}
      </div>; })}
    {totals && <p className="wall-tally-note wall-hide-phone">Hatched: the races I read, which the dial moves. The rest are projections. <a href="/method/#full-chamber">How</a> · <a href="/method/#models">Other readings</a></p>}
  </div>;
}

const seatLabel = (v: number) => (Math.abs(v) < EVEN ? 'EVEN' : `${v > 0 ? 'D' : 'R'}+${Math.abs(v).toFixed(1)}`);
const tileNum = (v: number) => (Math.abs(v) >= 10 ? Math.round(Math.abs(v)).toString() : Math.abs(v).toFixed(1));   // tiles: whole numbers from 10 up so the label fits
// Every House seat as a hemicycle dot. Tracked view: readings colored, no-poll districts hollow, untracked seats gray as
// held. Full view: untracked seats and no-poll districts take their projection. Ordering happens inside the hemicycle.
function houseSeats(races: WallRace[], noRead: NoReadRace[], seats: WallSeat[], full: boolean, m: number, c: Centers = null): HemiSeat[] {
  const tracked = new Set(races.map(r => r.id));
  const out: HemiSeat[] = races.filter(r => r.office === 'HOUSE').map(r => { const v = marginAt(r, m, c); return { id: r.id, label: `${r.name}: ${marginLabel(v, r)}`, v, shade: shade(v), ring: true, proj: false }; });
  for (const s of seats) {
    if (s.office !== 'HOUSE' || tracked.has(s.id)) continue;
    const n = noRead.find(x => x.id === s.id);
    if (full) { const v = seatMarginAt(s, m, c); out.push({ id: s.id, label: `${s.name}: projected ${seatLabel(v)}`, v, shade: shade(v), ring: !!n, proj: true }); }
    else if (n) out.push({ id: s.id, label: `${n.name}: no public polls`, v: 0, shade: 'is-noread', ring: true, proj: false });
    else out.push({ id: s.id, label: `${s.name}: not tracked (${s.holder === 'D' ? 'Democratic' : s.holder === 'R' ? 'Republican' : 'other'} seat)`, v: s.holder === 'D' ? 100 : s.holder === 'R' ? -100 : 0, shade: 'is-off', ring: false, proj: false, off: true });
  }
  return out;
}

function TileMap({ races, m, office, setOffice, selected, select, noRead = [], seats = [], full = false, hideToggle = false, c = null }: { races: WallRace[]; m: number; office: Office; setOffice: (o: Office) => void; selected: string; select: (id: string) => void; noRead?: NoReadRace[]; seats?: WallSeat[]; full?: boolean; hideToggle?: boolean; c?: Centers }) {
  const byState = new Map(races.filter(r => r.office === office).map(r => [r.state, r]));
  const seatByState = new Map(full ? seats.filter(x => x.office === office && x.kind !== 'not_up').map(x => [x.state, x]) : []);
  return <section className="wall-panel wall-map" aria-label={full ? 'Map of every seat' : 'Map of tracked races'}>
    <div className="wall-panel-head"><p className="wall-kicker">{office === 'HOUSE' ? (full ? 'The House · all 435 seats' : 'The House · tracked seats colored, the rest as held') : `The map · ${officeName(office)}${full ? ' · every seat up' : ''}`}</p>
      {!hideToggle && <div className="wall-toggle" role="group" aria-label="Office">{OFFICES.map(o => <button key={o} type="button" aria-pressed={office === o} onClick={() => setOffice(o)}>{officeName(o)}</button>)}</div>}</div>
    {office === 'HOUSE' ? (() => { const hs = houseSeats(races, noRead, seats, full, m, c); const d = hs.filter(x => x.shade !== 'is-noread' && (x.v ?? 0) >= EVEN).length; const r = hs.filter(x => x.shade !== 'is-noread' && (x.v ?? 0) <= -EVEN).length;
      return <Hemicycle seats={hs} majority={218} selected={selected} select={select} dCount={d} rCount={r} count={full} title={full ? 'All 435 House seats, most Democratic to most Republican' : 'The House: tracked seats colored, others as held'}/>; })() : <div className="wall-tiles">{Object.entries(TILES).map(([st, [tc, rw]]) => { const r = byState.get(st); const v = r ? marginAt(r, m, c) : 0;
      const pos = `tc-${tc} tr-${rw}`; const sx = r ? undefined : seatByState.get(st);
      if (r) return <button key={st} type="button" className={`wall-tile ${pos} ${shade(v)}${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} aria-label={`${r.name}: ${marginLabel(v, r)}`} onClick={() => select(r.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${tileNum(v)}`}</span></button>;
      if (sx) { const atRating = sx.kind === 'rated' && typeof c?.[sx.id] !== 'number' && (sx.rest === undefined || Math.abs(m - sx.rest) < 0.05); const sv = !atRating && (sx.kind !== 'not_up' || typeof c?.[sx.id] === 'number') ? seatMarginAt(sx, m, c) : (sx.side === 'D' ? 20 : sx.side === 'R' ? -20 : 0); const lab = !atRating && (sx.kind !== 'not_up' || typeof c?.[sx.id] === 'number') ? (Math.abs(sv) < EVEN ? 'EVEN' : `${sv > 0 ? 'D' : 'R'}+${tileNum(sv)}`) : (sx.rating || 'rated');
        return <button key={st} type="button" className={`wall-tile is-proj ${pos} ${shade(sv)}${selected === sx.id ? ' is-selected' : ''}`} aria-pressed={selected === sx.id} aria-label={`${sx.name}: ${sx.kind === 'projection' ? `projected ${seatLabel(sv)}` : atRating ? `Cook ${sx.rating}, not tracked` : `${seatLabel(sv)} at this setting, from Cook ${sx.rating}, not tracked`}`} onClick={() => select(sx.id)}><span className="wall-tile-st">{st}</span><span className="wall-tile-v wall-tile-rated">{lab}</span></button>; }
      return <span key={st} className={`wall-tile is-off ${pos}`} aria-hidden="true"><span className="wall-tile-st">{st}</span></span>; })}</div>}
    {full && !hideToggle && <p className="wall-note">{office === 'HOUSE' ? 'Ringed dots are tracked races; plain dots are projections from the 2024 vote, not readings.' : 'Dashed tiles are projections or Cook ratings, not Undertow readings.'}</p>}
    {!hideToggle && <div className="wall-legend" aria-hidden="true"><span className="r-safe">Safe R</span><span className="r-likely">Likely R</span><span className="r-lean">Lean R</span><span className="toss">Toss-up</span><span className="d-lean">Lean D</span><span className="d-likely">Likely D</span><span className="d-safe">Safe D</span></div>}
  </section>;
}

// The second line shows the same race with no national miss (the dial's "No miss · polls right" preset), so a reader sees
// how much of the chance is the bet (fix 3 of six, Max, 2026-10-29: "please do the six fixes").
// The second line's label says what dial zero is for the active reading (audit 2026-10-31): under the bet the race keeps its
// state, spending, early-vote and partisan terms, so zero is 'no national miss', not 'the polls are right'. The words come
// from the reading's scenario (scenarioFor).
function WinChance({ r, p, p0, moved, zero }: { r: WallRace; p: number | null; p0?: number | null; moved: boolean; zero: string }) {
  if (p === null || r.result?.settled) return null;
  const showBase = typeof p0 === 'number' && chanceLabel(p0) !== chanceLabel(p);
  return <div className="wall-chance">
    <p className="wall-label">Chance to win{moved ? ' at your dial' : ''}</p>
    <p className="wall-chance-names"><span className="is-d">{last(r.d)} {chanceLabel(p)}</span><span className="is-r">{last(r.r)} {chanceLabel(1 - p)}</span></p>
    <span className="wall-chance-bar" aria-hidden="true"><i className={`is-d gw-${pct(100 * p)}`}/><i className={`is-r gw-${100 - pct(100 * p)}`}/></span>
    {showBase && <p className="wall-chance-sub">{zero}: {last(r.d)} {chanceLabel(p0)}, {last(r.r)} {chanceLabel(1 - p0)}.</p>}
  </div>;
}
// The bet's terms, named as Method names them: the national lean is the carried share of last fall's miss, not the miss itself
// (audit 2026-10-31: the bar read 'Last fall's polling miss 1.9' beside a 7.3 headline). The race page's 'Recent polling error' is
// this lean plus the state record together.
export const LEAN_LABEL = 'National lean';
function Detail({ r, m, national, odds, c = null, model = null, locked = false, zero = 'With no national miss' }: { r: WallRace; m: number; national: number; odds?: Odds | null; c?: Centers; model?: ModelDef | null; locked?: boolean; zero?: string }) {
  const at = marginAt(r, m, c); const pull = r.undertow - r.polls; const moved = Math.abs(m - (model ? model.defaultDial : national)) >= 0.05 && !r.result?.settled;
  const parts: [string, number][] = [[LEAN_LABEL, national], ['This state’s polling record', r.stateAdj], [r.spendLabel, r.spending], ['Early vote', r.earlyVote], ...(r.office === 'SEN' ? [['The state’s partisan record', r.partisan] as [string, number]] : [])];
  return <section className="wall-panel wall-detail" aria-label={`${r.name} breakdown`}>
    <div className="wall-panel-head"><p className="wall-kicker">{r.name}</p><a className="wall-link" href={`/race/${r.slug}/`}>Full race and every poll →</a></div>
    <p className="wall-matchup"><span className="is-d">{r.d} ({r.dLetter})</span> vs <span className="is-r">{r.r} (R)</span></p>
    <div className="wall-figures">
      <div><p className="wall-label">Polls</p><p className={`wall-big ${side(r.polls)}`}><Big text={marginLabel(r.polls, r)}/></p><p className="wall-sub">{pollCountLabel(r.pollCount, r.sponsoredOnly)}</p></div>
      <div><p className="wall-label">Undertow</p><p className={`wall-big ${side(r.undertow)}`}><Big text={marginLabel(r.undertow, r)}/></p><p className="wall-sub">± {r.sd.toFixed(1)} · my call, {locked ? 'frozen' : 'freezes'} Nov 2</p></div>
      {r.result ? <div><p className="wall-label">The count</p><p className={`wall-big ${side(r.result.margin)}`}><Big text={marginLabel(r.result.margin, r)}/></p><p className="wall-sub">{r.result.reporting.toFixed(0)}% counted{r.result.called ? ` · called for ${last(r.result.called === 'D' ? r.d : r.r)}` : ''}</p></div> : null}
      {model && typeof model.centers[r.id] === 'number' ? <div><p className="wall-label">{model.name}</p><p className={`wall-big ${side(model.centers[r.id])}`}><Big text={marginLabel(model.centers[r.id], r)}/></p><p className="wall-sub">{moved ? <>At your dial: <b className={side(at)}>{marginLabel(at, r)}</b></> : 'another reading, not graded'}</p></div> : <div><p className="wall-label">The pull</p><p className={`wall-big ${side(pull)}`}>{Math.abs(pull) < EVEN ? 'None' : `${Math.abs(pull).toFixed(1)} → ${pull > 0 ? r.dLetter : 'R'}`}</p><p className="wall-sub">{moved ? <>At your dial: <b className={side(at)}>{marginLabel(at, r)}</b></> : 'Undertow minus the polls'}</p></div>}
    </div>
    <WinChance r={r} p={oddsAt(odds, odds?.perRace[r.id], m)} p0={oddsAt(odds, odds?.perRace[r.id], 0)} moved={moved} zero={zero}/>
    {!model && <FactorBars parts={parts.map(([label, v]) => ({ label, v }))} dLetter={r.dLetter}/>}
  </section>;
}

// Breakdown for a seat Undertow does not track: the projection's parts, or the rating it carries.
function SeatDetail({ s, m, national, full, c = null, model = null }: { s: WallSeat; m: number; national: number; full: boolean; c?: Centers; model?: ModelDef | null }) {
  if (!full && s.noPolls) return <section className="wall-panel wall-detail" aria-label={`${s.name}, no public polls`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p>{s.slug && <a className="wall-link" href={`/race/${s.slug}/`}>Race page and spending →</a>}</div>
    {s.d && s.r && <p className="wall-matchup"><span className="is-d">{s.d} ({s.dLetter || 'D'})</span> vs <span className="is-r">{s.r} (R)</span></p>}
    <p className="wall-matchup">No public poll since September 1 could be verified at its source.{s.rating ? <> Cook rates it <strong>{s.rating}</strong>{s.holder === 'D' || s.holder === 'R' ? <>, held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}</> : null}.</> : null}</p>
    <p className="wall-note">Listed without a number (no reading, not graded). The Full chamber view projects it from its 2024 vote.</p>
  </section>;
  if (s.kind !== 'projection') return <section className="wall-panel wall-detail" aria-label={`${s.name} rating`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p><span className="wall-badge">Not tracked</span></div>
    <p className="wall-matchup">Cook Political Report rating: <strong>{s.rating}</strong>{s.holder === 'D' || s.holder === 'R' ? <> · seat held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}</> : null}</p>
    {typeof c?.[s.id] === 'number' && model ? <p className="wall-matchup">{model.name} reads it <strong className={side(seatMarginAt(s, m, c))}>{Math.abs(seatMarginAt(s, m, c)) < EVEN ? 'Even' : `${seatMarginAt(s, m, c) > 0 ? 'D' : 'R'} +${Math.abs(seatMarginAt(s, m, c)).toFixed(1)}`}</strong> at this setting; the dial moves it under this reading.</p> : null}
    {s.kind === 'rated' && typeof c?.[s.id] !== 'number' && s.rest !== undefined && Math.abs(m - s.rest) >= 0.05 ? <p className="wall-matchup">At this setting it reads <strong className={side(seatMarginAt(s, m, c))}>{Math.abs(seatMarginAt(s, m, c)) < EVEN ? 'Even' : `${seatMarginAt(s, m, c) > 0 ? 'D' : 'R'} +${Math.abs(seatMarginAt(s, m, c)).toFixed(1)}`}</strong>: Cook’s rating, moved by the dial.</p> : null}
    <p className="wall-note">{typeof c?.[s.id] === 'number' ? 'Under my bet this seat starts at Cook’s rating: g' : 'Governor races Undertow does not track start at Cook’s rating. G'}overnor results track the presidential vote badly (in 2022 a swing projection missed them by 10.5 points on average against 4.2 for the polls), so no projection is made. The dial still moves this seat by the same miss as every other race.</p>
  </section>;
  const at = seatMarginAt(s, m, c); const moved = Math.abs(m - (model ? model.defaultDial : national)) >= 0.05;
  const parts: [string, number][] = [['Generic-ballot swing since 2024', s.shift], ['Incumbent on the ballot', s.incumbency], [LEAN_LABEL, national], ['This state’s polling record', s.stateAdj], ['Early vote', s.earlyVote]];
  return <section className="wall-panel wall-detail" aria-label={`${s.name} projection`}>
    <div className="wall-panel-head"><p className="wall-kicker">{s.name}</p>{s.slug ? <a className="wall-link" href={`/race/${s.slug}/`}>Race page →</a> : <span className="wall-badge">Projection</span>}</div>
    {s.d && s.r && <p className="wall-matchup"><span className="is-d">{s.d} ({s.dLetter || 'D'})</span> vs <span className="is-r">{s.r} (R)</span></p>}
    <p className="wall-matchup">{s.noPolls ? 'No public polls, so the seat is projected from its 2024 vote.' : 'Not tracked: projected from its 2024 vote, not polled.'}{s.holder === 'D' || s.holder === 'R' ? <> Held by {s.holder === 'D' ? 'a Democrat' : 'a Republican'}{s.rating ? <>, Cook: {s.rating}</> : null}.</> : null}</p>
    <div className="wall-figures">
      <div><p className="wall-label">2024 vote</p><p className={`wall-big ${side(s.base - s.shift - s.incumbency)}`}>{seatLabel(s.base - s.shift - s.incumbency)}</p><p className="wall-sub">presidential margin, these lines</p></div>
      <div><p className="wall-label">Projection</p><p className={`wall-big ${side(s.undertow ?? 0)}`}>{seatLabel(s.undertow ?? 0)}</p><p className="wall-sub">at my bet · not graded</p></div>
      <div><p className="wall-label">{model ? model.name : 'At your dial'}</p><p className={`wall-big ${side(at)}`}>{seatLabel(at)}</p><p className="wall-sub">{model ? (moved ? 'at your dial, not graded' : 'another reading, not graded') : moved ? 'with your polling miss' : 'same as the bet'}</p></div>
    </div>
    {!model && <FactorBars parts={parts.map(([label, v]) => ({ label, v }))} dLetter={s.dLetter}/>}
  </section>;
}

function Board({ races, m, selected, select, office, c = null }: { races: WallRace[]; m: number; selected: string; select: (id: string) => void; office: Office; c?: Centers }) {
  const rows = useMemo(() => races.filter(r => r.office === office).map(r => ({ r, v: marginAt(r, m, c) })).sort((a, b) => b.v - a.v), [races, m, office, c]);
  return <section className="wall-panel wall-board" aria-label="Every race, from most Democratic to most Republican">
    <div className="wall-panel-head"><p className="wall-kicker">{officeName(office)} · {rows.length} {rows.length === 1 ? 'race' : 'races'}</p><p className="wall-key"><i className="wall-key-tick"/> polls</p></div>
    <ol>{rows.map(({ r, v }) => <li key={r.id}><button type="button" className={`wall-row${selected === r.id ? ' is-selected' : ''}`} aria-pressed={selected === r.id} onClick={() => select(r.id)}>
      <span className="wall-row-name">{r.office === 'HOUSE' ? `${r.state}-${r.district}` : r.state} <small>{r.office === 'SEN' ? 'Sen' : r.office === 'GOV' ? 'Gov' : ''}</small></span>
      <MarginTrack v={v} tick={r.polls} span={BOARD_SPAN}/>
      <span className={`wall-row-v ${side(v)}`}>{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button></li>)}</ol>
  </section>;
}

export function ElectionWall({ races, national, lastFall, initial, history, noRead = [], seats = [], totals = null, live = null, odds = null, models = [], locked = false, extras = {} }: { races: WallRace[]; national: number; lastFall: number; initial: string; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null; live?: LiveDial; odds?: Odds | null; models?: ModelDef[]; locked?: boolean; extras?: ScenarioExtras }) {
  const [m, setM] = useState(live ? live.m : national);
  const [office, setOffice] = useState<Office>('SEN');
  const [selected, setSelected] = useState(initial);
  const [scope, setScope] = useState<Scope>('all');
  const [model, setModel] = useState('bet');
  const cur = models.find(x => x.key === model) || null; const c: Centers = cur ? cur.centers : null; const o = cur ? cur.odds : odds;
  const pick = (k: string) => { const next = pickModel(models, k, national, live); setModel(next.model); setM(next.m); };
  const sc = scenarioFor(model, { history, national, lastFall, live, extras });
  const full = !!totals;
  const sel = races.find(r => r.id === selected);
  const selSeat = !sel ? seats.find(x => x.id === selected) : undefined;
  const shown = sel || (selSeat ? undefined : races[0]);
  const select = (id: string) => { setSelected(id); const r = races.find(x => x.id === id) || seats.find(x => x.id === id); if (r) setOffice(r.office); };
  return <div className="wall">
    <div className="wall-top"><Tally races={races} m={m} seats={seats} totals={totals} scope={scope} setScope={setScope} odds={live ? null : o} c={c}/></div>
    <aside className="wall-left"><Dial m={m} setM={setM} sc={sc} live={live} chips={<ModelChips models={models} model={model} pick={pick}/>}/></aside>
    <div className="wall-center"><TileMap races={races} m={m} office={office} setOffice={setOffice} selected={selected} select={select} noRead={noRead} seats={seats} full={full} c={c}/>{selSeat ? <SeatDetail s={selSeat} m={m} national={national} full={full} c={c} model={cur}/> : shown && <Detail r={shown} m={m} national={national} odds={live ? null : o} c={c} model={cur} locked={locked} zero={sc.zero}/>}</div>
    <aside className="wall-right"><Board races={races} m={m} selected={selected} select={select} office={office} c={c}/></aside>
  </div>;
}

function DialBar({ m, setM, sc }: { m: number; setM: (v: number) => void; sc: Scenario }) {
  const span = Math.max(8, ...sc.ticks.map(t => Math.ceil(Math.abs(t.v))));
  const byKey = useRef(false);   // the snap serves the thumb; a key press moves one native step (audit 2026-10-31)
  const near = (x: number) => Math.abs(m - x) < 0.05;
  return <section className="wall-dialbar" aria-label={sc.question}>
    <div className="wall-dialbar-top"><span className={`wall-num wall-dialbar-num ${side(m)}`}>{sc.show(m)}</span><span className="wall-dialbar-dir">{sc.dir(m)}<small>{sc.question} Drag to change every {sc.scope}.</small></span></div>
    <input className="wall-range" type="range" min={-span} max={span} step={0.1} value={m} onKeyDown={() => { byKey.current = true; }} onPointerDown={() => { byKey.current = false; }} onChange={e => { const v = Number(e.target.value); if (byKey.current) { setM(v); return; } const hit = sc.ticks.filter(t => t.ruler !== false && Math.abs(t.v - v) <= SNAP).sort((x, y) => Math.abs(x.v - v) - Math.abs(y.v - v))[0]; setM(hit ? hit.v : v); }} aria-label={sc.aria} aria-valuetext={valueText(sc, m)}/>
    <div className="wall-ruler" role="group" aria-label={sc.tableHead}>{sc.ticks.filter(t => t.ruler !== false).map(t => <button key={t.name} type="button" className={`wall-ruler-mark ga-${pct(100 * (t.v + span) / (2 * span))}${near(t.v) ? ' is-on' : ''}`} aria-pressed={near(t.v)} aria-label={`${t.name}: ${t.sub}`} onClick={() => setM(t.v)}><i aria-hidden="true"/><span>{t.label}</span></button>)}</div>
  <div className="phone-key" aria-hidden="true"><span className="phone-key-bar"><i className="r-safe"/><i className="r-likely"/><i className="r-lean"/><i className="toss"/><i className="d-lean"/><i className="d-likely"/><i className="d-safe"/></span><span className="phone-key-labels"><b>Safe R</b><b>Toss-up</b><b>Safe D</b></span></div>
  </section>;
}

// Phone first screen (Max, 2026-10-28: "How do other sites get it all to fit on the landing screen?" -> "Build it"): three chamber
// chips that switch both the numbers and the map, and one full bar for the selected chamber.
function PhoneChambers({ races, m, seats, totals, office, setOffice, odds, c = null }: { races: WallRace[]; m: number; seats: WallSeat[]; totals: ChamberTotals; office: Office; setOffice: (o: Office) => void; odds?: Odds | null; c?: Centers }) {
  const [scope, setScope] = useState<Scope>('all'); const sc: Scope = office === 'HOUSE' ? 'all' : scope;
  const cs = chamberSplit(office, races, seats, totals, m, sc, c); const d = cs.dSafe + cs.dPlay, r = cs.rSafe + cs.rPlay; const w = (k: number) => pct(100 * k / cs.n);
  return <section className="wall-tally phone-chambers" aria-live="polite">
    <div className="phone-chips" role="tablist" aria-label="Chamber">{OFFICES.map(o => { const x = chamberSplit(o, races, seats, totals, m, o === 'HOUSE' ? 'all' : scope, c); return <button key={o} type="button" role="tab" aria-selected={office === o} className={office === o ? 'is-on' : ''} onClick={() => setOffice(o)}><span>{o === 'GOV' ? 'Governors' : officeName(o)}</span><b><i className="is-d">D {x.dSafe + x.dPlay}</i> <i className="is-r">R {x.rSafe + x.rPlay}</i></b></button>; })}</div>
    <div className="wall-tally-row">
      <span className="wall-tally-label">{office === 'GOV' ? 'Governors' : officeName(office)}<small>{sc === 'up' ? `${cs.n} up` : `of ${cs.n}`}</small></span>
      <span className="wall-tally-num"><b className="is-d">D {d}</b> <b className="is-r">R {r}</b></span>
      {cs.majority ? <ControlOdds p={oddsAt(odds, odds?.chambers[office], m)}/> : null}
      <span className="wall-tally-bar" aria-hidden="true"><i className={`is-d gw-${w(cs.dSafe)}`}/><i className={`is-d-play gw-${w(cs.dPlay)}`}/><i className={`is-even gw-${w(cs.even)}`}/><i className={`is-r-play gw-${w(cs.rPlay)}`}/><i className={`is-r gw-${w(cs.rSafe)}`}/>{cs.majority && <em className={`wall-tally-maj ga-${pct(100 * cs.majority / cs.n)}`}/>}</span>
      <span className="wall-tally-play">{cs.play} in play: <b className="is-d">{cs.dPlay} D</b>, <b className="is-r">{cs.rPlay} R</b>{cs.evenPlay > 0 ? `, ${cs.evenPlay} even` : ''}{cs.even - cs.evenPlay - cs.tossUp > 0 ? ` · ${cs.even - cs.evenPlay - cs.tossUp} projected ${cs.even - cs.evenPlay - cs.tossUp === 1 ? 'seat' : 'seats'} even` : ''}{cs.tossUp ? ` · ${cs.tossUp} Cook toss-up` : ''}{office === 'HOUSE' && cs.n > cs.play ? ` · the other ${cs.n - cs.play} are projections or Cook ratings, not my reading` : ''}{cs.majority ? ` · ${cs.majority} seats to control${office === 'SEN' ? '; a 50-50 tie goes to R' : ''}` : ''}</span>
    </div>
    {office !== 'HOUSE' && <ScopeToggle scope={scope} setScope={setScope}/>}
  </section>;
}

export function MobileWall({ races, national, lastFall, history, noRead = [], seats = [], totals = null, live = null, odds = null, models = [], locked = false, extras = {} }: { races: WallRace[]; national: number; lastFall: number; history: HistoryPreset[]; noRead?: NoReadRace[]; seats?: WallSeat[]; totals?: ChamberTotals | null; live?: LiveDial; odds?: Odds | null; models?: ModelDef[]; locked?: boolean; extras?: ScenarioExtras }) {
  const [m, setM] = useState(live ? live.m : national);
  const [open, setOpen] = useState<string | null>(null);
  const [office, setOffice] = useState<Office>('SEN');
  const full = !!totals;
  const openSeat = open && !races.some(r => r.id === open) ? seats.find(x => x.id === open) : undefined;
  const [model, setModel] = useState('bet');
  const cur = models.find(x => x.key === model) || null; const c: Centers = cur ? cur.centers : null; const o = cur ? cur.odds : odds;
  const pick = (k: string) => { const next = pickModel(models, k, national, live); setModel(next.model); setM(next.m); };
  const sc = scenarioFor(model, { history, national, lastFall, live, extras });
  const rows = useMemo(() => races.filter(r => r.office === office).map(r => ({ r, v: marginAt(r, m, c) })).sort((a, b) => b.v - a.v), [races, m, office, c]);
  const pickRace = (id: string) => { setOpen(id); if (typeof document !== 'undefined') document.getElementById(`m-${id}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }); };
  return <div className="wall-mobile">
    <ModelChips models={models} model={model} pick={pick}/>
    {totals ? <PhoneChambers races={races} m={m} seats={seats} totals={totals} office={office} setOffice={setOffice} odds={live ? null : o} c={c}/> : <Tally races={races} m={m} seats={seats} totals={totals} c={c}/>}
    <TileMap races={races} m={m} office={office} setOffice={setOffice} selected={open || ''} select={pickRace} noRead={noRead} seats={seats} full={full} hideToggle={!!totals} c={c}/>
    {openSeat && <SeatDetail s={openSeat} m={m} national={national} full={full} c={c} model={cur}/>}
    <ol className="wall-mobile-list">{rows.map(({ r, v }) => <li key={r.id} id={`m-${r.id}`}>
      <button type="button" className={`wall-mrow ${shade(v)}`} aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
        <span className="wall-mrow-name">{r.name}<small>{last(r.d)} ({r.dLetter}) vs {last(r.r)} (R)</small></span>
        <span className="wall-mrow-v">{Math.abs(v) < EVEN ? 'EVEN' : `${letter(v, r)}+${Math.abs(v).toFixed(1)}`}</span></button>
      {open === r.id && <Detail r={r} m={m} national={national} odds={live ? null : o} c={c} model={cur} locked={locked} zero={sc.zero}/>}
    </li>)}
    {office === 'HOUSE' && noRead.map(n => <li key={n.id}><a className="wall-mrow is-noread" href={`/race/${n.slug}/`}><span className="wall-mrow-name">{n.name}<small>{last(n.d)} ({n.dLetter}) vs {last(n.r)} (R) · {n.rating}</small></span><span className="wall-mrow-v">no polls</span></a></li>)}</ol>
    <DialBar m={m} setM={setM} sc={sc}/>
  </div>;
}
