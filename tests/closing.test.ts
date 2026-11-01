import { describe, expect, it } from 'vitest';
import { closeInstant, STATE_CLOSE } from '../lib/closing';

// Tonight's hours carry Eastern Standard Time (UTC-5) on Nov 3, 2026; after-midnight hours land on Nov 4 (Max, 2026-11-01).
describe('poll-closing instants', () => {
  it('maps Eastern clock times to the right UTC instant', () => {
    expect(closeInstant('7:00 PM')).toBe('2026-11-04T00:00:00.000Z');
    expect(closeInstant('7:30 PM')).toBe('2026-11-04T00:30:00.000Z');
    expect(closeInstant('6:00 PM')).toBe('2026-11-03T23:00:00.000Z');
    expect(closeInstant('12:00 AM')).toBe('2026-11-04T05:00:00.000Z');
    expect(closeInstant('1:00 AM')).toBe('2026-11-04T06:00:00.000Z');
    expect(new Date(closeInstant('7:00 PM')).toLocaleTimeString('en-US', { timeZone: 'America/Los_Angeles', hour: 'numeric', minute: '2-digit' })).toBe('4:00 PM');
  });
  it('refuses a time it cannot read, and every listed hour parses', () => {
    expect(() => closeInstant('7 PM')).toThrow();
    for (const c of Object.values(STATE_CLOSE)) { closeInstant(c.at); if (c.first) closeInstant(c.first); }
  });
  it('every clock time in a note says ET', () => {
    for (const c of Object.values(STATE_CLOSE)) if (c.note) expect(c.note.replace(/(\d{1,2}:\d\d|midnight) ET/g, '')).not.toMatch(/\d{1,2}:\d\d|midnight/);
  });
});
