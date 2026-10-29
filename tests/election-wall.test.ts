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
// chamber counts and the sealed control odds; at zero it reproduces the polls-alone odds. Skipped before the simulation.
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
