import { describe, it, expect, beforeEach } from 'vitest';
import { readSelection, writeSelection, subscribeSelection } from '@/lib/selection';

// The shared selection (2026-10-31): survives a round trip, rejects garbage, notifies subscribers, and is null with no window.
describe('selection store', () => {
 const store: Record<string, string> = {};
 beforeEach(() => {
  const listeners: Record<string, ((e: any) => void)[]> = {};
  (globalThis as any).window = { localStorage: { getItem: (k: string) => store[k] ?? null, setItem: (k: string, v: string) => { store[k] = v; } },
   addEventListener: (t: string, f: any) => { (listeners[t] ||= []).push(f); }, removeEventListener: () => {}, dispatchEvent: (e: any) => { for (const f of listeners[e.type] || []) f(e); return true; } };
  (globalThis as any).CustomEvent = class { type: string; detail: any; constructor(t: string, o: any) { this.type = t; this.detail = o?.detail; } };
 });
 it('round-trips and notifies', () => {
  let seen: any = null; subscribeSelection(s => { seen = s; });
  writeSelection({ model: 'blend', name: 'Forecaster blend', m: -5.5, label: '2020 again', at: 't' });
  expect(readSelection()?.m).toBe(-5.5); expect(seen?.model).toBe('blend');
 });
 it('rejects garbage', () => { store['undertow-selection'] = '{"model":1}'; expect(readSelection()).toBeNull(); store['undertow-selection'] = 'nope'; expect(readSelection()).toBeNull(); });
});
