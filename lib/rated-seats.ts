import type { WallSeat } from '@/components/ElectionWall';

// Puts each rated seat (an untracked governor) at its Cook rating's center (simulation.rated_center) with the bet's lean as
// its resting dial, so it sits exactly at the rating until the dial moves (Max, 2026-11-03). Server-safe: the page and the
// tests build seats through this so the two cannot drift.
export function ratedAtCenter(seats: WallSeat[], ratedCenter: Record<string, number> | undefined, national: number): WallSeat[] {
  return seats.map(s => (s.kind === 'rated' ? { ...s, base: Number(ratedCenter?.[s.rating as string]) || 0, rest: national } : s));
}
