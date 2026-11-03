// Election night ballot (Max, 2026-11-03: "move the phone version to the Undertow site"). Pure helpers shared by the
// page and its tests: points, the plain-text ballot people copy and paste, and scoring against called races.
import { surname } from './format';
export type Side = 'D' | 'R';
export type BallotCat = 'CONTROL' | 'SEN' | 'GOV';
// code is the state's postal code, or Senate / House for the control picks; it names the race in copied text.
export type BallotRace = { id: string; cat: BallotCat; code: string; label: string; held: Side; d: string; r: string; inc: Side | null; rating?: string; dParty?: 'D' | 'I' };
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
// A copied ballot is plain text people can read in a group chat or a Facebook comment (Max, 2026-11-03: "There's got to
// be a better fix" than a coded line). Each pick is a state code and a surname, one section per category; the
// Standings tab reads the same text back. A state appears once per section, so code plus section names the race.
//   Undertow ballot · Max
//   Control: Senate D, House R
//   Senate: AK Sullivan, FL Moody, GA Ossoff
//   Governors: AK Wilson, AZ Hobbs
//   Tiebreakers: Senate D 49 · House D 221 · AP call 11:30 PM
const SECTION: Record<BallotCat, string> = { CONTROL: 'Control', SEN: 'Senate', GOV: 'Governors' };
const HEADER = 'Undertow ballot';

export const topScore = (races: BallotRace[]) => races.reduce((a, r) => a + POINTS[r.cat], 0);
const clean = (s: string) => s.replace(/[\n\r·,]/g, ' ').replace(/\s+/g, ' ').trim();
const norm = (s: string) => s.toLowerCase().replace(/[^a-z]/g, '');

export function toText(races: BallotRace[], name: string, picks: Record<string, Side>, tb: [string, string, string]) {
  const lines = [`${HEADER} · ${clean(name) || 'Anonymous'}`];
  for (const cat of ['CONTROL', 'SEN', 'GOV'] as BallotCat[]) {
    const items = races.filter(r => r.cat === cat && picks[r.id]).map(r => {
      const side = picks[r.id];
      return `${r.code} ${cat === 'CONTROL' ? side : surname(side === 'D' ? r.d : r.r)}`;
    });
    lines.push(`${SECTION[cat]}: ${items.join(', ') || 'no picks yet'}`);
  }
  const [s, h, t] = tb.map(clean);
  lines.push(`Tiebreakers: Senate D ${s || '?'} · House D ${h || '?'} · AP call ${t || '?'}`);
  return lines.join('\n');
}

// Reads a pasted ballot back into one pick per race (D, R or - for none). A pick that names nobody in that race is
// skipped rather than guessed. Returns null when the text holds no readable pick at all.
export function fromText(text: string, races: BallotRace[]): FriendBallot | null {
  const sections: Partial<Record<string, string>> = {};
  for (const m of text.matchAll(/\b(Control|Senate|Governors|Tiebreakers):\s*([^\n]*)/g)) sections[m[1]] = m[2];
  const picks = races.map(r => {
    const body = sections[SECTION[r.cat]];
    if (!body) return '-';
    for (const item of body.split(',')) {
      const [code, ...rest] = item.trim().split(/\s+/);
      if (!code || code.toUpperCase() !== r.code.toUpperCase()) continue;
      const who = norm(rest.join(' '));
      if (who === 'd' || who === 'i' || who === norm(surname(r.d)) || who === norm(r.d)) return 'D';
      if (who === 'r' || who === norm(surname(r.r)) || who === norm(r.r)) return 'R';
    }
    return '-';
  }).join('');
  if (!/[DR]/.test(picks)) return null;
  const head = text.match(new RegExp(`${HEADER}\\s*·\\s*([^\\n]+)`));
  const tbs = sections.Tiebreakers || '';
  const grab = (re: RegExp) => { const v = (tbs.match(re)?.[1] || '').trim(); return v === '?' ? '' : v; };
  return { name: head?.[1].trim() || '', picks, tb: [grab(/Senate D\s*([^·]*)/), grab(/House D\s*([^·]*)/), grab(/AP call\s*(.*)$/)] };
}

export function score(races: BallotRace[], picks: string, results: Record<string, Side>) {
  return races.reduce((a, r, i) => (results[r.id] && picks[i] === results[r.id] ? a + POINTS[r.cat] : a), 0);
}
