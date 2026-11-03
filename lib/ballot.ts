import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { readCsv } from '../scripts/bundle.mjs';
import { derived, states } from './data';
import type { BallotCat, BallotRace, Side } from './ballot-code';

// The ballot (Max, 2026-11-03): who wins each chamber, then every Senate and governor seat up in 2026 that Cook rates
// anywhere from Toss-up to Likely in the sealed seats.csv, named from the sealed candidates. Built as toss-ups only, then
// widened the same day to Lean ("We need Texas governor, Iowa governor. I want to get those lean senates in there, too")
// and to Likely ("as encompassing as possible without being overwhelming, but leaning towards encompassing"), which
// brings Mississippi Senate back after it was cut. Solid seats stay off. The 18 House districts were cut for control picks.
// Two governor toss-ups are outside Undertow's tracked scope and have no sealed candidates; their nominees live in
// lib/ballot-nominees.json, which the print sheet's builder (scripts/ballot/build_print.py) reads too.
const UNTRACKED_NOMINEES = JSON.parse(readFileSync(join(process.cwd(), 'lib/ballot-nominees.json'), 'utf8')) as Record<string, { D: string; R: string }>;
const ORDER: Record<BallotCat, number> = { CONTROL: 0, SEN: 1, GOV: 2 };
// Current majorities: Republicans hold both chambers going into November 3, 2026.
const CONTROL: BallotRace[] = [
  { id: 'SENATE-CONTROL', cat: 'CONTROL', code: 'Senate', label: 'The Senate', held: 'R', d: 'Democrats', r: 'Republicans', inc: null },
  { id: 'HOUSE-CONTROL', cat: 'CONTROL', code: 'House', label: 'The House', held: 'R', d: 'Democrats', r: 'Republicans', inc: null },
];

// seats.csv is optional in a release bundle (scripts/bundle.mjs), so an older release yields no ballot rather than a
// failed build (Greptile on PR #3); the page then says the ballot is unavailable.
export function ballotRaces(seatsFile = join(process.cwd(), 'data/seats.csv')): BallotRace[] {
  if (!existsSync(seatsFile)) return [];
  const seats = readCsv(readFileSync(seatsFile, 'utf8')) as Record<string, string>[];
  const cands = (derived as any).candidates as Record<string, { D?: { candidate?: string }; R?: { candidate?: string } }>;
  const seatRaces = seats
    .filter(s => s.up_2026 === '1' && BALLOT_RATINGS.includes(s.cook_rating) && (s.chamber === 'SEN' || s.chamber === 'GOV'))
    .map(s => {
      const cat = s.chamber as BallotCat;
      const sealed = cands[s.seat];
      const d = sealed?.D?.candidate || UNTRACKED_NOMINEES[s.seat]?.D;
      const r = sealed?.R?.candidate || UNTRACKED_NOMINEES[s.seat]?.R;
      if (!d || !r) throw new Error(`Ballot: no nominees for ${s.seat}`);
      const inc = s.incumbent_on_ballot === 'D' || s.incumbent_on_ballot === 'R' ? s.incumbent_on_ballot as Side : null;
      const label = `${states[s.state]}${s.special === '1' ? ' (special)' : ''}`;
      // Nebraska's Osborn runs as an independent in the D slot; the Tonight page marks him the same way.
      const dParty: 'D' | 'I' = s.seat === '2026-NE-SEN' || /^independent/i.test(String((sealed?.D as any)?.party || '')) ? 'I' : 'D';
      return { id: s.seat, cat, code: s.state, label, held: s.holder_party as Side, d, r, inc, rating: s.cook_rating, dParty };
    });
  // Control keeps Senate then House; seat races sort by state.
  return [...CONTROL, ...seatRaces.sort((a, b) => ORDER[a.cat] - ORDER[b.cat] || a.label.localeCompare(b.label))];
}

export const BALLOT_RATINGS = ['Toss-up', 'Lean D', 'Lean R', 'Likely D', 'Likely R'];
export const BALLOT_RATING_DATES = 'October 20 to 30, 2026';
export const BALLOT_PDF = '/ballot/undertow-election-night-ballot.pdf';
