// Labels for computed flags must be true for every category behind the flag (Max, 2026-10-28: the Mississippi card
// called a poll with no stated sponsor "paid for by campaigns or partisan groups").
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { pollCountLabel, SPONSOR_TIER_TAG } from '../lib/format';
const derived = JSON.parse(readFileSync('data/derived.json', 'utf8'));
const v2 = derived.signals.polling_v2;
const SPONSORED_TIERS = Object.keys(v2.sponsor_weights);

describe('payer labels', () => {
  it('tags every sponsored tier weight.py emits, and no tier it does not', () => {
    expect(Object.keys(SPONSOR_TIER_TAG).sort()).toEqual(SPONSORED_TIERS.sort());
  });
  it('the sponsored-only line names no category, so it holds for internal, partisan-paid and unstated sponsors alike', () => {
    const line = pollCountLabel(1, true);
    expect(line).not.toMatch(/campaign|partisan|PAC|party/i);
    expect(line).toMatch(/none independently paid for/);
  });
  it('grammar: one poll, many polls, none', () => {
    expect(pollCountLabel(1)).toBe('1 poll');
    expect(pollCountLabel(3)).toBe('3 polls, weighted');
    expect(pollCountLabel(null)).toBe('weighted average');
  });
  it('sponsored_only agrees with each race mix and with the estimates', () => {
    const tier = new Map(derived.estimates.map((e: any) => [e.estimate_id, e.sponsor_tier]));
    for (const [race, x] of Object.entries<any>(v2.per_race)) {
      const tiers = x.estimate_ids.map((id: string) => tier.get(id));
      expect(tiers.every((t: string) => t !== undefined), race).toBe(true);
      expect(x.sponsored_only, race).toBe(tiers.every((t: string) => t !== 'INDEPENDENT'));
      expect(x.sponsor_mix.INDEPENDENT + x.sponsor_mix.INTERNAL + x.sponsor_mix.PARTISAN_SPONSORED + x.sponsor_mix.UNKNOWN, race).toBe(x.polls);
    }
  });
});
