// Election night ballot (Max, 2026-11-03: "move the phone version to the Undertow site"). Pure helpers shared by the
// page and its tests: points, the coded line a copied ballot carries, and scoring against called races.
export type Side = 'D' | 'R';
export type BallotCat = 'CONTROL' | 'SEN' | 'GOV';
export type BallotRace = { id: string; cat: BallotCat; label: string; held: Side; d: string; r: string; inc: Side | null; rating?: string; dParty?: 'D' | 'I' };
export type FriendBallot = { name: string; picks: string; tb: [string, string, string] };

// Max, 2026-11-03: the 18 House districts are cut for a House control pick (people do not know the districts), with a
// matching Senate control pick; seat counts and the call time are tiebreakers. Every pick is 1 point ("1 point each",
// after the 5/3/2 weights read as arbitrary and paid a Lean favorite like a toss-up): the score is a count of checks.
export const POINTS: Record<BallotCat, number> = { CONTROL: 1, SEN: 1, GOV: 1 };
export const CATEGORIES: { cat: BallotCat; title: string; note: string }[] = [
  { cat: 'CONTROL', title: 'Who wins control', note: 'Senate and House' },
  { cat: 'SEN', title: 'Senate races', note: 'Toss-up to Likely' },
  { cat: 'GOV', title: 'Governor races', note: 'Toss-up to Likely' },
];
// The code names the race list it was copied from: UB1 the 29-race draft, UB2 the 28-race one, UB3 the 12-pick one,
// UB4 the 26-pick one, UB5 this 33-pick ballot. An older line no longer lines up and is refused.
export const CODE = 'UB5';

export const topScore = (races: BallotRace[]) => races.reduce((a, r) => a + POINTS[r.cat], 0);
export const clean = (s: string) => s.replace(/[|\n\r]/g, ' ').trim();

export function encode(races: BallotRace[], name: string, picks: Record<string, Side>, tb: [string, string, string]) {
  return [CODE, clean(name) || 'Anonymous', races.map(r => picks[r.id] || '-').join(''), ...tb.map(clean)].join('|');
}

export function parse(text: string, n: number): FriendBallot | null {
  const line = text.split('\n').map(l => l.trim()).find(l => l.startsWith(`${CODE}|`));
  if (!line) return null;
  const p = line.split('|');
  if (p.length < 3 || p[2].length !== n || /[^DR-]/.test(p[2])) return null;
  return { name: p[1] || 'Friend', picks: p[2], tb: [p[3] || '', p[4] || '', p[5] || ''] };
}

export function score(races: BallotRace[], picks: string, results: Record<string, Side>) {
  return races.reduce((a, r, i) => (results[r.id] && picks[i] === results[r.id] ? a + POINTS[r.cat] : a), 0);
}
