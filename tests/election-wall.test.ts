import { describe, it, expect } from 'vitest';
import { races, derived } from '@/lib/data';
import { marginAt, type WallRace } from '@/components/ElectionWall';

// The wall's dial must reproduce Undertow's frozen number at the national lean, for every race.
describe('election wall', () => {
 it('reproduces every adjusted margin at the national lean', () => {
  const national = Number((derived as any).signals.rules.poll_error_toward_d);
  for (const r of races as any[]) {
   if (!r.signal || !Number.isFinite(r.signal.adjusted_margin)) continue;
   const w = { polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0 } as WallRace;
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
  const wall = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0 })) as WallRace[];
  const totals: ChamberTotals = { SEN: { notUp: ch.chambers.SEN.not_up, majority: 51, seats: 100 }, GOV: { notUp: ch.chambers.GOV.not_up, majority: null, seats: 50 }, HOUSE: { notUp: { D: 0, R: 0 }, majority: 218, seats: 435 } };
  for (const o of ['SEN', 'GOV', 'HOUSE'] as const) {
   const c = chamberCount(o, wall, seats, totals, national);
   expect([c.d, c.r, c.u, c.n]).toEqual([ch.chambers[o].at_bet.D, ch.chambers[o].at_bet.R, ch.chambers[o].at_bet.undecided, ch.chambers[o].seats]);
  }
 });
 it2('the one-bar split adds up to the chamber and agrees with the count at every notch', () => {
  const wall = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => ({ id: r.id, office: r.id.endsWith('HOUSE') ? 'HOUSE' : r.id.includes('GOV') ? 'GOV' : 'SEN', polls: r.signal.polling_margin, stateAdj: Number(r.signal.polling_error?.state_adjustment) || 0, spending: Number(r.signal.delta_spending) || 0, earlyVote: Number(r.signal.delta_early_vote) || 0 })) as WallRace[];
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
