import { expect,it } from 'vitest';
import { margin,number,shortDate } from '../lib/format';
it('keeps null, unknown and zero distinct',()=>{expect(margin(null,true)).toBe('not yet computed');expect(margin(null)).toBe('NA');expect(number(null)).toBe('NA');expect(number('UNVERIFIED')).toBe('UNVERIFIED');expect(number(0)).toBe('0.0');expect(margin(0)).toBe('Even');expect(margin(-2.5)).toBe('R +2.5');expect(margin(NaN)).toBe('UNVERIFIED');});
it('formats dates without timezone day drift and rejects invalid calendar dates',()=>{expect(shortDate('2026-10-01')).toBe('Oct 1');expect(shortDate('')).toBe('UNVERIFIED');expect(shortDate('2026-99-99')).toBe('UNVERIFIED');expect(shortDate('2026-02-30')).toBe('UNVERIFIED');expect(number('  ')).toBe('NA');expect(margin('')).toBe('NA');});
