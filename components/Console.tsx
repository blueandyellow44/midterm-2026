import type { ReactNode } from 'react';

// Shared console primitives (Max, 2026-10-27: one design system for every page, not per-page patches). Server-safe: no
// hooks, no inline styles (the CSP forbids style attributes), so positions and widths use quantized classes.
export const EVEN = 0.05;
export const tone = (v: number) => (v >= EVEN ? 'is-d' : v <= -EVEN ? 'is-r' : 'is-even');
export const pct = (x: number) => Math.max(0, Math.min(100, Math.round(x)));

export function Panel({ kicker, action, className = '', children, label }: { kicker?: ReactNode; action?: ReactNode; className?: string; children: ReactNode; label?: string }) {
  return <section className={`c-panel ${className}`} aria-label={label}>{(kicker || action) && <div className="c-head">{kicker && <p className="c-kicker">{kicker}</p>}{action}</div>}{children}</section>;
}

export function Figure({ label, value, v, sub }: { label: string; value: ReactNode; v?: number; sub?: ReactNode }) {
  return <div className="c-figure"><p className="c-label">{label}</p><p className={`c-big ${v === undefined ? '' : tone(v)}`}>{value}</p>{sub && <p className="c-sub">{sub}</p>}</div>;
}

// One signed contribution as a bar from the center line: blue to the right for D, red to the left for R.
export function SignedBar({ v, max }: { v: number; max: number }) {
  const w = pct(50 * Math.abs(v) / Math.max(max, 1e-9));
  return <span className="c-sbar" aria-hidden="true"><i className={`${tone(v)} ${v >= 0 ? 'from-mid-l' : 'from-mid-r'} gw-${w}`}/></span>;
}

export function FactorBars({ parts, dLetter = 'D' }: { parts: { label: string; v: number }[]; dLetter?: string }) {
  const max = Math.max(1, ...parts.map(p => Math.abs(p.v)));
  return <ul className="c-factors">{parts.map(p => <li key={p.label}><span className="c-factor-label">{p.label}</span><SignedBar v={p.v} max={max}/><span className={`c-factor-v ${tone(p.v)}`}>{Math.abs(p.v) < EVEN ? '0.0' : `${p.v > 0 ? dLetter : 'R'} +${Math.abs(p.v).toFixed(1)}`}</span></li>)}</ul>;
}

// Margin track from R +span (left) to D +span (right): a bar from center to the value, a tick for a reference value.
export function MarginTrack({ v, tick, span = 20, large }: { v: number; tick?: number; span?: number; large?: boolean }) {
  const at = (x: number) => pct(50 + 50 * Math.max(-span, Math.min(span, x)) / span);
  const p = at(v);
  return <span className={`c-track${large ? ' is-large' : ''}`} aria-hidden="true">
    <i className={`c-track-bar ${tone(v)} ${v >= 0 ? 'from-mid-l' : 'from-mid-r'} gw-${Math.abs(p - 50)}`}/>
    {tick !== undefined && <i className={`c-track-tick ga-${at(tick)}`}/>}
  </span>;
}
