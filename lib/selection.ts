'use client';
// The console's selection (reading + scenario value), shared with every race card and race page (Max, 2026-10-31:
// "cards should follow by model and dial" -> yes; "do it"). The console writes it on every change; cards read it and
// show one extra line beneath the official figures, which never move. Stored in the browser only; never sent anywhere.
export type Selection = { model: string; name: string; m: number; label: string; at: string };
const KEY = 'undertow-selection';
const EVENT = 'undertow-selection';
export function readSelection(): Selection | null {
  if (typeof window === 'undefined') return null;
  try { const raw = window.localStorage.getItem(KEY); if (!raw) return null; const s = JSON.parse(raw); return s && typeof s.model === 'string' && Number.isFinite(s.m) ? s as Selection : null; } catch { return null; }
}
export function writeSelection(s: Selection) {
  if (typeof window === 'undefined') return;
  try { window.localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* private mode or blocked storage: the console still works, cards show nothing */ }
  window.dispatchEvent(new CustomEvent(EVENT, { detail: s }));
}
export function subscribeSelection(fn: (s: Selection | null) => void): () => void {
  if (typeof window === 'undefined') return () => {};
  const onLocal = (e: Event) => fn((e as CustomEvent<Selection>).detail);
  const onStorage = (e: StorageEvent) => { if (e.key === KEY) fn(readSelection()); };
  window.addEventListener(EVENT, onLocal); window.addEventListener('storage', onStorage);
  return () => { window.removeEventListener(EVENT, onLocal); window.removeEventListener('storage', onStorage); };
}
