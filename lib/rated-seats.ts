import type { WallSeat } from '@/components/ElectionWall';

// Puts each rated seat (an untracked governor) at its Cook rating's center (simulation.rated_center) with the bet's lean as
// its resting dial, so it sits exactly at the rating until the dial moves (Max, 2026-11-03). Server-safe: the page and the
// tests build seats through this so the two cannot drift.
export function ratedAtCenter(seats: WallSeat[], ratedCenter: Record<string, number> | undefined, national: number): WallSeat[] {
  // A release without a center for the rating (no simulation block) leaves the seat as it was: fixed at its saved side,
  // never an invented toss-up (Greptile on PR #4).
  return seats.map(s => {
    const center = Number(ratedCenter?.[s.rating as string]);
    return s.kind === 'rated' && Number.isFinite(center) && Number.isFinite(national) ? { ...s, base: center, rest: national } : s;
  });
}
