'use client';
import { useEffect, useState } from 'react';
import { readSelection, subscribeSelection, type Selection } from '@/lib/selection';
import { marginAt, oddsAt, chanceLabel, type Odds, type WallRace } from '@/components/ElectionWall';
import { surname } from '@/lib/format';

// One line under a race's official figures: the reading and scenario picked on the console, applied to this race.
// Shown only when the console's selection differs from the bet at its lean; the official numbers above never move.
export type FollowedData = { id: string; d: string; r: string; dLetter: string; national: number; bet: { polls: number; stateAdj: number; spending: number; earlyVote: number; partisan: number };
  centers: Record<string, number>; grids: Record<string, number[] | undefined>; values: number[] | null };
const EVEN = 0.05;
export function Followed({ data }: { data: FollowedData }) {
  const [sel, setSel] = useState<Selection | null>(null);
  useEffect(() => { setSel(readSelection()); return subscribeSelection(setSel); }, []);
  if (!sel) return null;
  const isBet = sel.model === 'bet';
  if (isBet && Math.abs(sel.m - data.national) < EVEN) return null;
  const race = { id: data.id, ...data.bet } as WallRace;
  const v = isBet ? marginAt(race, sel.m) : (typeof data.centers[sel.model] === 'number' ? data.centers[sel.model] + sel.m : null);
  if (v === null) return null;
  const grid = data.grids[sel.model]; const odds: Odds | null = data.values && grid ? { values: data.values, chambers: {}, perRace: { [data.id]: grid } } : null;
  const p = oddsAt(odds, grid, sel.m);
  const who = Math.abs(v) < EVEN ? 'Even' : `${surname(v > 0 ? data.d : data.r)} +${Math.abs(v).toFixed(1)}`;
  return <p className="c-followed" aria-live="polite"><strong>{sel.name}</strong> · {sel.label}: <b className={v >= EVEN ? 'is-d' : v <= -EVEN ? 'is-r' : 'is-even'}>{who}</b>{p !== null ? <> · {surname(data.d)} {chanceLabel(p)}, {surname(data.r)} {chanceLabel(1 - p)}</> : null} <span className="muted">· set on the <a href="/">home page</a>; the figures above are the call</span></p>;
}
