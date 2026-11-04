import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Side } from './ballot-code';

// AP calls for ballot races with no official count to enter (live/calls.json, written by scripts/live/set_call.py).
// Max, 2026-11-03, on New Hampshire called hours ago and still blank in Standings: "Have parallel session do it".
// /ballot/ ONLY: this file never feeds the grade, the dial, the scoreboard or analysis/; those read live/results.json.
// Keyed by ballot race id (2026-NH-SEN, SENATE-CONTROL), not the results slug. Validated on read: a malformed file or
// an id that is not on the ballot fails the build instead of locking a wrong winner.
export type HandCall = { winner: Side; called_at: string; source: string };

export function loadCalls(ballotIds: Set<string>, file = join(process.cwd(), 'live/calls.json')): Record<string, Side> {
  const raw = JSON.parse(readFileSync(file, 'utf8'));
  if (raw?.schema !== '1.0' || !raw.calls || typeof raw.calls !== 'object' || Array.isArray(raw.calls)) throw new Error('live/calls.json: unsupported schema');
  const out: Record<string, Side> = {};
  for (const [id, c] of Object.entries<any>(raw.calls)) {
    if (!ballotIds.has(id)) throw new Error(`live/calls.json: ${id} is not a ballot race`);
    if (c?.winner !== 'D' && c?.winner !== 'R') throw new Error(`live/calls.json: bad winner for ${id}`);
    if (typeof c.source !== 'string' || !c.source.startsWith('https://')) throw new Error(`live/calls.json: missing source for ${id}`);
    if (typeof c.called_at !== 'string' || Number.isNaN(Date.parse(c.called_at))) throw new Error(`live/calls.json: bad called_at for ${id}`);
    out[id] = c.winner;
  }
  return out;
}
