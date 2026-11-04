import { describe, expect, it } from 'vitest';
import { readFileSync, writeFileSync, mkdtempSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { ballotRaces } from '@/lib/ballot';
import { POINTS, toText, fromText, nextFriendName, score, topScore, liveSlug, siteCalls, effectiveResults, mergeCalls, type Side } from '@/lib/ballot-code';
import { loadCalls } from '@/lib/live-calls';
import { loadLive } from '@/lib/live';
import { surname } from '@/lib/format';
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
  it('round-trips a copied ballot as readable text and scores it', () => {
    const picks: Record<string, Side> = { 'SENATE-CONTROL': 'D', 'HOUSE-CONTROL': 'R', '2026-TX-SEN': 'R', '2026-AK-GOV': 'R', '2026-NE-SEN': 'D' };
    const text = toText(races, 'Max', picks, ['48', '221', '10:30 PM']);
    expect(text).toContain('Control: Senate D, House R');
    expect(text).toContain('TX Paxton');
    expect(text).toContain('AK Wilson');
    expect(text).not.toMatch(/\|/);
    const f = fromText(`Here are mine!\n${text}`, races)!;
    expect(f.name).toBe('Max');
    expect(f.tb).toEqual(['48', '221', '10:30 PM']);
    expect(f.picks).toBe(races.map(r => picks[r.id] || '-').join(''));
    expect(score(races, f.picks, { 'SENATE-CONTROL': 'D', '2026-TX-SEN': 'R', 'HOUSE-CONTROL': 'D' })).toBe(2);
  });
  it('reads a hand-edited paste and skips a pick that names nobody in that race', () => {
    const f = fromText('Senate: tx talarico,  ak SULLIVAN, ME Smith\nGovernors: AZ Hobbs', races)!;
    const at = (id: string) => f.picks[races.findIndex(r => r.id === id)];
    expect([at('2026-TX-SEN'), at('2026-AK-SEN'), at('2026-ME-SEN'), at('2026-AZ-GOV')]).toEqual(['D', 'R', '-', 'D']);
    expect(f.name).toBe('');
    expect(fromText('no picks here', races)).toBeNull();
  });
  it('names an unnamed paste with an unused Friend N, even after a removal', () => {
    expect(nextFriendName([])).toBe('Friend 1');
    expect(nextFriendName(['Friend 2', 'Friend 3'])).toBe('Friend 1');
    expect(nextFriendName(['Friend 1', 'Friend 3'])).toBe('Friend 2');
    expect(nextFriendName(['Friend 1', 'Ana', 'Friend 2'])).toBe('Friend 3');
  });
  it('gives every race two different surnames and a unique code within its section', () => {
    for (const r of races.filter(r => r.cat !== 'CONTROL')) expect(surname(r.d).toLowerCase()).not.toBe(surname(r.r).toLowerCase());
    for (const cat of ['CONTROL', 'SEN', 'GOV']) {
      const codes = races.filter(r => r.cat === cat).map(r => r.code);
      expect(new Set(codes).size).toBe(codes.length);
    }
  });
});

describe('standings fills in the races Undertow has called', () => {
  const id = (k: string) => races.findIndex(r => r.id === k);
  const only = (k: string, side: Side) => races.map((r, i) => (i === id(k) ? side : '-')).join('');
  it('maps every ballot seat to the live slug scripts/live/set_result.py accepts, and names the ones it never can', () => {
    // The tracked set and the slug rule come from the results tooling itself, not a copy of it.
    const py = 'import sys, json; sys.path.insert(0, "analysis"); import weight; print(json.dumps({r: r.replace("2026-", "").lower() for r in weight.ALL_RACES}))';
    const tracked = JSON.parse(execFileSync('python3', ['-c', py], { encoding: 'utf8' })) as Record<string, string>;
    const accepted = new Set(Object.values(tracked));
    for (const r of races) if (tracked[r.id]) expect(liveSlug(r.id)).toBe(tracked[r.id]);
    expect(liveSlug('2026-OH-SEN-SPECIAL')).toBe('oh-sen-special');
    expect(liveSlug('SENATE-CONTROL')).toBeNull();
    const never = races.filter(r => !liveSlug(r.id) || !accepted.has(liveSlug(r.id)!)).map(r => r.id).sort();
    expect(never).toEqual(['2026-AK-GOV', '2026-AZ-GOV', '2026-FL-GOV', '2026-KS-GOV', '2026-MN-SEN', '2026-NE-GOV', '2026-NH-GOV',
      '2026-NV-GOV', '2026-OK-GOV', '2026-OR-GOV', '2026-TX-GOV', '2026-VT-GOV', 'HOUSE-CONTROL', 'SENATE-CONTROL']);
  });
  it('takes only AP calls, and treats a missing or uncalled race as not called', () => {
    const calls = siteCalls(races, { 'ga-sen': { called: 'D' }, 'ne-sen': { called: null }, 'tx-15-house': { called: 'D' } });
    expect(calls).toEqual({ '2026-GA-SEN': 'D' });
    expect(calls['2026-WI-GOV']).toBeUndefined();
  });
  it('lets a site call override a conflicting stored tap', () => {
    const results = effectiveResults({ '2026-GA-SEN': 'D' }, { '2026-GA-SEN': 'R' });
    expect(results['2026-GA-SEN']).toBe('D');
    expect(score(races, only('2026-GA-SEN', 'D'), results)).toBe(1);
    expect(score(races, only('2026-GA-SEN', 'R'), results)).toBe(0);
  });
  it('still scores an uncalled race from a tap, and leaves a race absent from live results tappable', () => {
    const calls = siteCalls(races, { 'ga-sen': { called: 'D' } });
    const results = effectiveResults(calls, { '2026-WI-GOV': 'R' });
    expect(score(races, only('2026-WI-GOV', 'R'), results)).toBe(1);
    expect(calls['2026-WI-GOV']).toBeUndefined();   // not locked, so the scorekeeper can tap it
    expect(effectiveResults(calls, {})['2026-WI-GOV']).toBeUndefined();   // and no tap is no result, for either side
  });
  it('keeps site calls when the taps are cleared', () => {
    const calls = { '2026-GA-SEN': 'D', '2026-FL-SEN-SPECIAL': 'R' } as Record<string, Side>;
    expect(effectiveResults(calls, {})).toEqual(calls);
  });
});

describe('hand-entered AP calls (live/calls.json) for races with no official count', () => {
  const ids = new Set(races.map(r => r.id));
  const dir = mkdtempSync(join(tmpdir(), 'ballot-calls-'));
  const file = (calls: unknown, name = 'calls.json') => { const f = join(dir, name); writeFileSync(f, JSON.stringify({ schema: '1.0', calls })); return f; };
  const call = (winner: string, source = 'https://apnews.com/x') => ({ winner, called_at: '2026-11-03T20:15:00-08:00', source });
  // The committed file is filled on election night (set_call.py); it must load, and every entry must be a ballot race
  // called D or R. (Was "ships empty", true only until the first call was entered.)
  it('loads the committed file, every entry a ballot race called D or R', () => {
    const calls = loadCalls(ids);
    for (const [id, w] of Object.entries(calls)) { expect(ids.has(id)).toBe(true); expect(['D', 'R']).toContain(w); }
  });
  it('adds a hand call to the results calls, and keeps a race neither file has uncalled', () => {
    const merged = mergeCalls(siteCalls(races, { 'ga-sen': { called: 'D' } }), loadCalls(ids, file({ '2026-NH-SEN': call('D'), '2026-TX-GOV': call('R') })));
    expect(merged).toEqual({ '2026-GA-SEN': 'D', '2026-NH-SEN': 'D', '2026-TX-GOV': 'R' });
    expect(merged['2026-WI-GOV']).toBeUndefined();
  });
  it('fails the build when live/calls.json contradicts a call in live/results.json, and accepts a matching one', () => {
    expect(() => mergeCalls({ '2026-GA-SEN': 'D' }, { '2026-GA-SEN': 'R' })).toThrow(/GA-SEN is called D in live\/results.json but R/);
    expect(mergeCalls({ '2026-GA-SEN': 'D' }, { '2026-GA-SEN': 'D' })).toEqual({ '2026-GA-SEN': 'D' });
  });
  it('rejects an id not on the ballot, a bad winner, a non-https source and a bad schema', () => {
    expect(() => loadCalls(ids, file({ 'nh-sen': call('D') }))).toThrow(/not a ballot race/);
    expect(() => loadCalls(ids, file({ '2026-PA-GOV': call('D') }))).toThrow(/not a ballot race/);
    expect(() => loadCalls(ids, file({ '2026-NH-SEN': call('I') }))).toThrow(/bad winner/);
    expect(() => loadCalls(ids, file({ '2026-NH-SEN': call('D', 'http://x') }))).toThrow(/missing source/);
    expect(() => loadCalls(ids, file({ '2026-NH-SEN': { ...call('D'), called_at: 'tonight' } }))).toThrow(/called_at/);
    writeFileSync(join(dir, 'bad.json'), JSON.stringify({ schema: '2.0', calls: {} }));
    expect(() => loadCalls(ids, join(dir, 'bad.json'))).toThrow(/schema/);
  });
  it('takes the same ballot ids as scripts/live/set_call.py', () => {
    const py = JSON.parse(execFileSync('python3', ['scripts/live/set_call.py', '--list'], { encoding: 'utf8' })) as string[];
    expect([...py].sort()).toEqual([...ids].sort());
  });
  it('never reaches the grade, the dial, the scoreboard or analysis/', () => {
    // Only the ballot page, its pure helpers, its loader and its CLI may name calls.json or loadCalls.
    const walk = (d: string): string[] => readdirSync(d).flatMap(n => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
    const readers = ['app', 'components', 'lib', 'analysis', 'scripts'].flatMap(walk).filter(p => /\.(tsx?|mjs|py)$/.test(p))
      .filter(p => /calls\.json|loadCalls|live-calls/.test(readFileSync(p, 'utf8'))).sort();
    expect(readers).toEqual(['app/ballot/page.tsx', 'lib/ballot-code.ts', 'lib/live-calls.ts', 'scripts/live/set_call.py']);
    // And the live grade read from live/results.json is the same with a populated calls file beside it.
    const before = loadLive();
    const f = 'live/calls.json', saved = readFileSync(f, 'utf8');
    try {
      writeFileSync(f, JSON.stringify({ schema: '1.0', calls: { '2026-NH-SEN': call('D'), '2026-WI-GOV': call('R'), 'SENATE-CONTROL': call('D') } }));
      expect(loadLive()).toEqual(before);
      expect(loadLive().derived).toEqual(before.derived);
    } finally { writeFileSync(f, saved); }
  });
});
