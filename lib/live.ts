import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// Election-night counts (live/results.json), kept outside the sealed release. Validated on read: a malformed
// file fails the build instead of rendering a wrong scoreboard.
export type LiveRace = { d_pct: number; r_pct: number; other_pct: number; round: 'NA' | 'FIRST'; basis: 'full_ballot'; reporting_pct: number; called: 'D' | 'R' | null; source: string; updated_at: string };
export type LiveDerived = { settled: number; min_races: number; implied_miss: number | null; implied_miss_se: number | null; dial_live: boolean; polls_mae: number | null; undertow_mae: number | null; polls_miss_mean: number | null; undertow_closer?: number; polls_closer?: number; release_id: string };
export type Live = { updated_at: string | null; races: Record<string, LiveRace>; derived: LiveDerived | null };
const pct = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 100;

export function loadLive(): Live {
  const raw = JSON.parse(readFileSync(join(process.cwd(), 'live/results.json'), 'utf8'));
  if (raw?.schema !== '1.0' || typeof raw.races !== 'object') throw new Error('live/results.json: unsupported schema');
  for (const [slug, r] of Object.entries<any>(raw.races)) {
    if (!pct(r.d_pct) || !pct(r.r_pct) || !pct(r.reporting_pct)) throw new Error(`live/results.json: bad shares for ${slug}`);
    if (r.called !== null && r.called !== 'D' && r.called !== 'R') throw new Error(`live/results.json: bad call for ${slug}`);
    if (r.basis !== 'full_ballot' || !pct(r.other_pct) || Math.abs(r.d_pct + r.r_pct + r.other_pct - 100) > 1.5) throw new Error(`live/results.json: ${slug} is not entered as full-ballot shares`);
    if (['me-sen', 'ak-sen', 'ak-al-house'].includes(slug) !== (r.round === 'FIRST')) throw new Error(`live/results.json: ${slug} has the wrong ballot round`);
    if (typeof r.source !== 'string' || !r.source.startsWith('https://')) throw new Error(`live/results.json: missing source for ${slug}`);
  }
  const d = raw.derived ?? null;
  // The computed block is tied to the release it was computed from; a newer synced release needs set_result.py rerun.
  const rel = JSON.parse(readFileSync(join(process.cwd(), 'data/manifest.json'), 'utf8')).release_id;
  if (d && d.release_id !== rel) throw new Error(`live/results.json: computed against ${d.release_id}, site has ${rel}; rerun scripts/live/set_result.py --recompute`);
  if (Object.keys(raw.races).length && !d) throw new Error('live/results.json: counts entered without the computed block (run scripts/live/set_result.py)');
  if (d && (typeof d.settled !== 'number' || typeof d.dial_live !== 'boolean' || (d.implied_miss !== null && !Number.isFinite(d.implied_miss)))) throw new Error('live/results.json: malformed computed block');
  return { updated_at: raw.updated_at ?? null, races: raw.races, derived: d };
}

// A race counts toward the tally once it is called or nearly fully counted.
export const SETTLED_REPORTING = 95;
export const settled = (r: LiveRace) => r.called !== null || r.reporting_pct >= SETTLED_REPORTING;
