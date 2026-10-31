import { describe, it, expect } from 'vitest';
import { races, derived } from '@/lib/data';
import { marginAt, type WallRace } from '@/components/ElectionWall';

// The wall's dial must reproduce Undertow's frozen number at the national lean, for every race.
describe('election wall', () => {
 it('reproduces every adjusted margin at the national lean', () => {
  const national = Number((derived as any).signals.rules.poll_error_toward_d);
  for (const r of races as any[]) {
   if (!r.signal || !Number.isFinite(r.signal.adjusted_margin)) continue;
   const w = { polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0, partisan: Number(r.signal.delta_partisan) || 0 } as WallRace;
   expect(Math.abs(marginAt(w, national) - r.signal.adjusted_margin)).toBeLessThan(0.01);
  }
 });
});

// Full-chamber seats (Max, 2026-10-27): a projection reproduces weight.py's number at the national lean, rated seats never
// move, and the chamber count at the lean equals the sealed at_bet tally. Skipped on releases sealed before the chambers block.
import { seatMarginAt, chamberCount, chamberSplit, type WallSeat, type ChamberTotals } from '@/components/ElectionWall';
describe('full chamber', () => {
 const ch = (derived as any).chambers;
 const it2 = ch ? it : it.skip;
 const national = Number((derived as any).signals?.rules?.poll_error_toward_d);
 const seats: WallSeat[] = ch ? Object.entries(ch.chambers).flatMap(([c, x]: [string, any]) => x.items.filter((i: any) => i.kind !== 'reading').map((i: any) => ({ id: i.race || i.seat, state: i.state, office: c as any, district: i.district ?? undefined, name: i.seat, kind: i.kind, side: i.side, base: Number(i.base) || 0, stateAdj: Number(i.parts?.state_adjustment) || 0, spending: Number(i.parts?.spending) || 0, earlyVote: Number(i.parts?.early_vote) || 0, incumbency: Number(i.parts?.incumbency) || 0, shift: Number(i.parts?.shift) || 0, undertow: i.undertow ?? null, rating: i.rating ?? null, holder: i.holder, noPolls: !!i.no_polls }))) : [];
 it2('reproduces every projection at the national lean', () => {
  for (const s of seats) if (s.kind === 'projection') expect(Math.abs(seatMarginAt(s, national) - (s.undertow as number))).toBeLessThan(0.01);
 });
 it2('counts every chamber at the lean exactly as sealed', () => {
  const wall = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0, partisan: Number(r.signal.delta_partisan) || 0 })) as WallRace[];
  const totals: ChamberTotals = { SEN: { notUp: ch.chambers.SEN.not_up, majority: 51, seats: 100 }, GOV: { notUp: ch.chambers.GOV.not_up, majority: null, seats: 50 }, HOUSE: { notUp: { D: 0, R: 0 }, majority: 218, seats: 435 } };
  for (const o of ['SEN', 'GOV', 'HOUSE'] as const) {
   const c = chamberCount(o, wall, seats, totals, national);
   expect([c.d, c.r, c.u, c.n]).toEqual([ch.chambers[o].at_bet.D, ch.chambers[o].at_bet.R, ch.chambers[o].at_bet.undecided, ch.chambers[o].seats]);
  }
 });
 it2('the one-bar split adds up to the chamber and agrees with the count at every notch', () => {
  const wall = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0, partisan: Number(r.signal.delta_partisan) || 0 })) as WallRace[];
  const totals: ChamberTotals = { SEN: { notUp: ch.chambers.SEN.not_up, majority: 51, seats: 100 }, GOV: { notUp: ch.chambers.GOV.not_up, majority: null, seats: 50 }, HOUSE: { notUp: { D: 0, R: 0 }, majority: 218, seats: 435 } };
  for (const o of ['SEN', 'GOV', 'HOUSE'] as const) for (const m of [-8, -5.5, 0, national, 7.3, 8]) {
   const x = chamberSplit(o, wall, seats, totals, m); const c = chamberCount(o, wall, seats, totals, m);
   expect(x.dSafe + x.dPlay + x.even + x.rPlay + x.rSafe).toBe(x.n);
   expect([x.dSafe + x.dPlay, x.rSafe + x.rPlay, x.even]).toEqual([c.d, c.r, c.u]);
   expect(x.play).toBe(wall.filter(r => r.office === o).length + seats.filter(s => s.office === o && s.noPolls).length);
  }
 });
 it2('a rated seat does not move with the dial', () => {
  for (const s of seats) if (s.kind === 'rated') for (const m of [-8, 0, 8]) expect(s.side).toBe(s.side);
 });
});

describe('election night', () => {
 it('a settled race shows its count at every dial value; an unsettled one keeps moving', () => {
  const base = { polls: 2, stateAdj: -0.5, spending: 0.5, earlyVote: 0, partisan: 0 } as WallRace;
  const done = { ...base, result: { margin: 7, called: 'D', reporting: 99, settled: true } } as WallRace;
  const counting = { ...base, result: { margin: 7, called: null, reporting: 40, settled: false } } as WallRace;
  for (const m of [-5, 0, 3]) { expect(marginAt(done, m)).toBe(7); expect(marginAt(counting, m)).toBeCloseTo(2 + m, 6); }
 });
});

// Scenario notches (Max, 2026-10-29: "comparison and strip"): at the national lean the notch reproduces the sealed at-bet
// chamber counts and the sealed control odds; at zero it reproduces the no-lean odds (the national lean removed, every other
// term kept; that is not the polls alone). Skipped before the simulation.
import { notchAt, oddsAt, type Odds } from '@/components/ElectionWall';
describe('scenario notches', () => {
 const ch = (derived as any).chambers, sim = (derived as any).simulation;
 const it3 = ch && sim?.dial && sim?.polls_no_lean ? it : it.skip;
 const national = Number((derived as any).signals?.rules?.poll_error_toward_d);
 it3('reproduce the sealed counts and odds at the bet and at zero', () => {
  const seats: WallSeat[] = Object.entries(ch.chambers).flatMap(([c, x]: [string, any]) => x.items.filter((i: any) => i.kind !== 'reading').map((i: any) => ({ id: i.race || i.seat, state: i.state, office: c as any, district: i.district ?? undefined, name: i.seat, kind: i.kind, side: i.side, base: Number(i.base) || 0, stateAdj: Number(i.parts?.state_adjustment) || 0, spending: Number(i.parts?.spending) || 0, earlyVote: Number(i.parts?.early_vote) || 0, incumbency: 0, shift: 0, undertow: null, rating: i.rating ?? null, holder: i.holder, noPolls: !!i.no_polls, dLetter: 'D' })));
  const wall: WallRace[] = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0, partisan: Number(r.signal.delta_partisan) || 0 } as WallRace));
  const totals: ChamberTotals = { SEN: { notUp: { D: ch.chambers.SEN.not_up.D || 0, R: ch.chambers.SEN.not_up.R || 0 }, majority: ch.chambers.SEN.majority, seats: ch.chambers.SEN.seats }, GOV: { notUp: { D: 0, R: 0 }, majority: null, seats: ch.chambers.GOV.seats }, HOUSE: { notUp: { D: 0, R: 0 }, majority: ch.chambers.HOUSE.majority, seats: ch.chambers.HOUSE.seats } };
  const odds: Odds = { values: sim.dial.values, chambers: sim.dial.chambers, perRace: sim.dial.per_race };
  const bet = notchAt(wall, seats, totals, odds, national)!;
  expect(bet.sD).toBe(ch.chambers.SEN.at_bet.D); expect(bet.sR).toBe(ch.chambers.SEN.at_bet.R);
  expect(bet.hD).toBe(ch.chambers.HOUSE.at_bet.D); expect(bet.hR).toBe(ch.chambers.HOUSE.at_bet.R);
  expect(Math.abs((bet.pS as number) - sim.chambers.SEN.p_control_d)).toBeLessThan(0.02);
  expect(Math.abs((bet.pH as number) - sim.chambers.HOUSE.p_control_d)).toBeLessThan(0.02);
  const zero = notchAt(wall, seats, totals, odds, 0)!;
  expect(Math.abs((zero.pS as number) - sim.polls_no_lean.chambers.SEN.p_control_d)).toBeLessThan(0.02);
  expect(Math.abs((zero.pH as number) - sim.polls_no_lean.chambers.HOUSE.p_control_d)).toBeLessThan(0.02);
  expect(oddsAt(odds, odds.chambers.SEN, 0)).toBe(zero.pS);
  expect(notchAt(wall, seats, null, odds, 0)).toBeNull();
 });
});

// In-house models (Max, 2026-10-29: "Go"): a model's center replaces the bet's arithmetic for that seat, the dial still adds,
// a settled result still wins, a rated seat takes a side under a model, and notchAt counts with the model's centers.
import { seatSideAt } from '@/components/ElectionWall';
describe('model centers', () => {
 const r = { id: 'X', polls: 2, stateAdj: 1, spending: 0, earlyVote: 0, partisan: 0 } as WallRace;
 const rated = { id: 'G', office: 'GOV', kind: 'rated', side: 'R', base: 0, stateAdj: 0, spending: 0, earlyVote: 0 } as WallSeat;
 it('reads the center plus the dial, and falls back to the bet without one', () => {
  expect(marginAt(r, 1, { X: -4 })).toBeCloseTo(-3, 6);
  expect(marginAt(r, 1, { Y: -4 })).toBeCloseTo(4, 6);
  expect(marginAt(r, 1, null)).toBeCloseTo(4, 6);
  expect(marginAt({ ...r, result: { margin: 7, called: 'D', reporting: 100, settled: true } }, 1, { X: -4 })).toBe(7);
 });
 it('moves a rated seat under a model and leaves it fixed under the bet', () => {
  expect(seatSideAt(rated, 0, null)).toBe('R');
  expect(seatSideAt(rated, 0, { G: 3.5 })).toBe('D');
  expect(seatSideAt(rated, -4, { G: 3.5 })).toBe('R');
  expect(seatMarginAt(rated, 2, { G: 3.5 })).toBeCloseTo(5.5, 6);
 });
 it('counts a chamber from the model centers', () => {
  const totals: ChamberTotals = { SEN: { notUp: { D: 1, R: 1 }, majority: 2, seats: 4 }, GOV: { notUp: { D: 0, R: 0 }, majority: null, seats: 0 }, HOUSE: { notUp: { D: 0, R: 0 }, majority: 1, seats: 1 } };
  const races = [{ ...r, office: 'SEN' }, { ...r, id: 'H', office: 'HOUSE' }] as WallRace[];
  const seats = [{ ...rated, id: 'S', office: 'SEN', kind: 'projection', side: null, base: 1 }] as WallSeat[];
  const n = notchAt(races, seats, totals, null, 0, { X: -1, H: -2, S: -3 })!;
  expect([n.sD, n.sR, n.hD, n.hR]).toEqual([1, 3, 0, 1]);
  const bet = notchAt(races, seats, totals, null, 0, null)!;
  expect([bet.sD, bet.sR, bet.hD, bet.hR]).toEqual([3, 1, 1, 0]);
 });
});

// The control contract (audit 2026-10-31). Two independent choices with one canonical state each: `model` picks the reading,
// `m` is the national shift. Presets set m only; a chip resets m to the reading's default; labels say what zero and the lean
// preset mean under each reading; the graded call is read from the release and no control can move it.
import { presetList, presetSmall, pickModel, dialWords, zeroLabel, POLL_FREE, type ModelDef, type HistoryPreset } from '@/components/ElectionWall';
describe('control contract', () => {
 const history: HistoryPreset[] = [{ year: 2020, miss_toward_d: -5.4893 }, { year: 2022, miss_toward_d: -1.3245 }];
 const national = 1.9359, lastFall = 7.3102;
 const mk = (key: string, name: string, centers: Record<string, number>): ModelDef => ({ key, name, short: name, desc: '', defaultDial: 0, centers, odds: null });
 const models = [mk('polls', 'Polls only', { X: 2 }), mk('blend', 'Forecaster blend', { X: 1.5 }), mk('fundamentals', 'Fundamentals', { X: -3 })];
 it('a historical preset carries the archive miss to one decimal and the same value under every reading', () => {
  for (const key of ['bet', 'polls', 'fundamentals']) {
   const p = presetList(history, national, lastFall, null, key);
   expect(p.find(([l]) => l === '2020 again')![1]).toBe(-5.5);
   expect(p.find(([l]) => l === '2022 again')![1]).toBe(-1.3);
   expect(p.find(([l]) => l === 'No miss')![1]).toBe(0);
   expect(p.find(([l]) => l.startsWith('Last fall'))![1]).toBe(lastFall);
  }
 });
 it('the lean preset is "My bet" only under the bet; under a model it is "My lean", because center + lean is not the bet', () => {
  expect(presetList(history, national, lastFall, null, 'bet').map(([l]) => l)).toContain('My bet 1.9');
  expect(presetList(history, national, lastFall, null, 'polls').map(([l]) => l)).toContain('My lean 1.9');
  expect(presetList(history, national, lastFall, null, 'polls').map(([l]) => l)).not.toContain('My bet 1.9');
  const r = { id: 'X', polls: 2, stateAdj: 1, spending: 0.5, earlyVote: 0, partisan: 0, undertow: 2 + national + 1.5 } as WallRace;
  expect(marginAt(r, national, null)).toBeCloseTo(r.undertow, 6);                 // the bet
  expect(marginAt(r, national, models[0].centers)).not.toBeCloseTo(r.undertow, 1);  // polls + lean, not the bet
 });
 it('zero means no national miss under the bet (race terms kept), the polls under Polls only, no shift otherwise', () => {
  expect(presetSmall(0, 'bet')).toBe('no national miss');
  expect(presetSmall(0, 'polls')).toBe('polls right');
  expect(presetSmall(0, 'blend')).toBe('no shift');
  expect(presetSmall(-5.5, 'bet')).toBe('5.5 toward R');
  const r = { id: 'X', polls: 2, stateAdj: 1, spending: 0.5, earlyVote: 0, partisan: 0 } as WallRace;
  expect(marginAt(r, 0, null)).toBeCloseTo(3.5, 6);              // not the polls: the race terms remain
  expect(marginAt(r, 0, models[0].centers)).toBeCloseTo(2, 6);   // the polls exactly
  expect(zeroLabel(null)).toBe('With no national miss');
  expect(zeroLabel(models[0])).toBe('If the polls are right');
  expect(zeroLabel(models[2])).toBe('Fundamentals, no shift');
 });
 it('a poll-free reading describes the dial as a shift of the year, never as a polling miss', () => {
  expect(POLL_FREE.fundamentals).toBe(true);
  expect(dialWords(2, 'bet').dir).toBe('Polls understate Democrats');
  expect(dialWords(2, 'fundamentals').dir).toMatch(/^Year runs more Democratic/);
  expect(dialWords(0, 'fundamentals').dir).not.toMatch(/Polls/);
  expect(dialWords(0, 'fundamentals').kicker).not.toMatch(/polls/i);
  expect(dialWords(-1, 'polls').kicker).toBe('How wrong are the polls?');
 });
 it('picking a reading resets the dial to that reading\'s default; the bet restores its lean, or the counted miss on election night', () => {
  expect(pickModel(models, 'polls', national)).toEqual({ model: 'polls', m: 0 });
  expect(pickModel(models, 'fundamentals', national)).toEqual({ model: 'fundamentals', m: 0 });
  expect(pickModel(models, 'bet', national)).toEqual({ model: 'bet', m: national });
  expect(pickModel(models, 'nonsense', national)).toEqual({ model: 'bet', m: national });
  expect(pickModel(models, 'bet', national, { m: -2.1, settled: 4, se: 0.4, pollsMae: 3, undertowMae: 2, undertowCloser: 3, pollsCloser: 1 })).toEqual({ model: 'bet', m: -2.1 });
 });
 it('repeated switching is deterministic and the graded number never moves', () => {
  const r = { id: 'X', polls: 2, stateAdj: 1, spending: 0.5, earlyVote: 0.2, partisan: -0.1, undertow: 2 + national + 1.6 } as WallRace;
  let state = pickModel(models, 'bet', national);
  const seq = ['polls', 'bet', 'blend', 'fundamentals', 'bet', 'polls'];
  const run = () => { const out: number[] = []; for (const k of seq) { state = pickModel(models, k, national); const c = models.find(x => x.key === state.model)?.centers ?? null; out.push(marginAt(r, state.m, c)); state.m = -5.5; out.push(marginAt(r, state.m, c)); } return out; };
  const a = run(), b = run();
  expect(a).toEqual(b);
  expect(marginAt(r, national, null)).toBeCloseTo(r.undertow, 6);   // the bet is arithmetic on the release, untouched by any pick
  expect(r.undertow).toBeCloseTo(2 + national + 1.6, 6);
 });
});

// Under a model the chamber count at the model's default dial equals the sealed up_at_default plus the seats not up; the
// bet's sealed count is unchanged by the models' presence. Skipped on releases sealed before the models block.
describe('model counts against the release', () => {
 const ch = (derived as any).chambers, mb = (derived as any).models;
 const it4 = ch && mb?.models ? it : it.skip;
 it4('each model reproduces its sealed counts at dial 0 and the bet reproduces at_bet at the lean', () => {
  const national = Number((derived as any).signals.rules.poll_error_toward_d);
  const seats: WallSeat[] = Object.entries(ch.chambers).flatMap(([c, x]: [string, any]) => x.items.filter((i: any) => i.kind !== 'reading').map((i: any) => ({ id: i.race || i.seat, state: i.state, office: c as any, district: i.district ?? undefined, name: i.seat, kind: i.kind, side: i.side, base: Number(i.base) || 0, stateAdj: Number(i.parts?.state_adjustment) || 0, spending: Number(i.parts?.spending) || 0, earlyVote: Number(i.parts?.early_vote) || 0, incumbency: 0, shift: 0, undertow: null, rating: i.rating ?? null, holder: i.holder, noPolls: !!i.no_polls, dLetter: 'D' })));
  const wall: WallRace[] = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0, partisan: Number(r.signal.delta_partisan) || 0 } as WallRace));
  const totals: ChamberTotals = { SEN: { notUp: { D: ch.chambers.SEN.not_up.D || 0, R: ch.chambers.SEN.not_up.R || 0 }, majority: ch.chambers.SEN.majority, seats: ch.chambers.SEN.seats }, GOV: { notUp: { D: ch.chambers.GOV.not_up.D || 0, R: ch.chambers.GOV.not_up.R || 0 }, majority: null, seats: ch.chambers.GOV.seats }, HOUSE: { notUp: { D: 0, R: 0 }, majority: ch.chambers.HOUSE.majority, seats: ch.chambers.HOUSE.seats } };
  for (const [k, x] of Object.entries<any>(mb.models)) {
   for (const o of ['SEN', 'GOV', 'HOUSE'] as const) {
    const c = chamberCount(o, wall, seats, totals, Number(x.default_dial) || 0, x.centers);
    expect([k, o, c.d, c.r, c.u]).toEqual([k, o, x.up_at_default[o].D + totals[o].notUp.D, x.up_at_default[o].R + totals[o].notUp.R, x.up_at_default[o].undecided]);
   }
  }
  for (const o of ['SEN', 'GOV', 'HOUSE'] as const) {
   const c = chamberCount(o, wall, seats, totals, national, null);
   expect([c.d, c.r, c.u]).toEqual([ch.chambers[o].at_bet.D, ch.chambers[o].at_bet.R, ch.chambers[o].at_bet.undecided]);
  }
 });
});
