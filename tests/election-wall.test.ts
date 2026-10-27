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
