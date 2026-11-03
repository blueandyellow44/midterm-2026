import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { ballotRaces } from '@/lib/ballot';
import { CODE, POINTS, encode, parse, score, topScore, type Side } from '@/lib/ballot-code';
import { readCsv } from '../scripts/bundle.mjs';

const races = ballotRaces();
const seats = readCsv(readFileSync('data/seats.csv', 'utf8')) as Record<string, string>[];

describe('election night ballot', () => {
  it('carries both control picks and exactly the Senate and governor seats rated Toss-up to Likely', () => {
    const tossups = seats.filter(s => s.up_2026 === '1' && ['Toss-up', 'Lean D', 'Lean R', 'Likely D', 'Likely R'].includes(s.cook_rating) && (s.chamber === 'SEN' || s.chamber === 'GOV')).map(s => s.seat).sort();
    expect(races.filter(r => r.cat !== 'CONTROL').map(r => r.id).sort()).toEqual(tossups);
    expect(races.filter(r => r.cat === 'CONTROL').map(r => r.id).sort()).toEqual(['HOUSE-CONTROL', 'SENATE-CONTROL']);
    expect(races.some(r => r.id.endsWith('-HOUSE'))).toBe(false);
  });
  it('names both candidates in every race and matches the sealed holder and incumbent', () => {
    for (const r of races.filter(r => r.cat !== 'CONTROL')) {
      const s = seats.find(x => x.seat === r.id)!;
      expect(r.d && r.r).toBeTruthy();
      expect(r.held).toBe(s.holder_party);
      expect(r.inc).toBe(s.incumbent_on_ballot === 'D' || s.incumbent_on_ballot === 'R' ? s.incumbent_on_ballot : null);
    }
  });
  it('scores 1 point per pick, top 33', () => {
    expect(races.filter(r => r.cat === 'SEN')).toHaveLength(15);
    expect(races.filter(r => r.cat === 'GOV')).toHaveLength(16);
    expect(POINTS).toEqual({ CONTROL: 1, SEN: 1, GOV: 1 });
    expect(topScore(races)).toBe(33);
    expect(races.find(r => r.id === '2026-NE-SEN')?.dParty).toBe('I');
    expect(races.some(r => r.id === '2026-MS-SEN')).toBe(true);
  });
  it('yields no ballot, not a failed build, for a release without seats.csv', () => {
    expect(ballotRaces('/nonexistent/seats.csv')).toEqual([]);
  });
  it('round-trips a copied ballot and refuses an older or damaged line', () => {
    const picks: Record<string, Side> = { 'SENATE-CONTROL': 'D', '2026-TX-SEN': 'R' };
    const line = encode(races, 'Max | Jr', picks, ['48', '221', '10:30 PM']);
    const f = parse(`Undertow election night ballot · Max\n${line}`, races.length)!;
    expect(f.name).toBe('Max   Jr');
    expect(f.tb).toEqual(['48', '221', '10:30 PM']);
    expect(score(races, f.picks, { 'SENATE-CONTROL': 'D', '2026-TX-SEN': 'R', 'HOUSE-CONTROL': 'R' })).toBe(2);
    expect(parse(line.replace(CODE, 'UB4'), races.length)).toBeNull();
    expect(parse(`${CODE}|Ana|DDR`, races.length)).toBeNull();
    expect(parse(`${CODE}|Ana|${'X'.repeat(races.length)}`, races.length)).toBeNull();
  });
});
