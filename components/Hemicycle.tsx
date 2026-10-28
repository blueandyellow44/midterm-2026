import { pct } from './Console';

// The House as a hemicycle (Max, 2026-10-27: "we need a better visualization for house seat cards. the grid doesn't work").
// 435 seats on concentric half-rings, ordered from the most Democratic margin on the left to the most Republican on the
// right, so the 218th seat sits at the apex and the dial visibly moves the split. Pure SVG, classes only (the CSP forbids
// style attributes); server-safe.
export type HemiSeat = { id: string; label: string; v: number | null; shade: string; ring: boolean; proj: boolean; off?: boolean };
const W = 600, CX = 300, CY = 300, R0 = 118, R1 = 290, ROWS = 9;

export function hemicyclePositions(n: number) {
  // Seats per row proportional to the row's arc length; positions sorted by angle so the color boundary is a radial line.
  const radii = Array.from({ length: ROWS }, (_, i) => R0 + (R1 - R0) * i / (ROWS - 1));
  const total = radii.reduce((a, r) => a + r, 0);
  let left = n;
  const per = radii.map((r, i) => (i === ROWS - 1 ? left : (() => { const k = Math.round(n * r / total); left -= k; return k; })()));
  const pts: { x: number; y: number; a: number; row: number }[] = [];
  per.forEach((k, row) => { for (let j = 0; j < k; j++) { const a = Math.PI - (k === 1 ? Math.PI / 2 : Math.PI * j / (k - 1)); pts.push({ x: CX + radii[row] * Math.cos(a), y: CY - radii[row] * Math.sin(a), a, row }); } });
  return pts.sort((p, q) => q.a - p.a || p.row - q.row);
}

export function Hemicycle({ seats, majority, selected, select, dCount, rCount, count = true, compact, title }: { seats: HemiSeat[]; majority: number; selected?: string; select?: (id: string) => void; dCount: number; rCount: number; count?: boolean; compact?: boolean; title: string }) {
  const ordered = [...seats].sort((a, b) => (b.v ?? 0) - (a.v ?? 0) || a.id.localeCompare(b.id));
  const pos = hemicyclePositions(ordered.length);
  const rad = compact ? 7.5 : 8.5;
  const apex = pos[majority - 1];
  return <div className={`hemi${compact ? ' is-compact' : ''}`}>
    <svg viewBox={`0 0 ${W} ${CY + 24}`} role="img" aria-label={title} className="hemi-svg">
      {apex && <line className="hemi-maj" x1={CX} y1={CY - R1 - 14} x2={CX} y2={CY - R0 + 14}/>}
      {ordered.map((s, i) => { const p = pos[i]; const cls = `hemi-seat ${s.off ? 'is-off' : s.shade}${s.ring ? ' is-ring' : ''}${s.proj ? ' is-proj' : ''}${selected === s.id ? ' is-selected' : ''}`;
        return select && !s.off ? <circle key={s.id} className={cls} cx={p.x.toFixed(1)} cy={p.y.toFixed(1)} r={rad} role="button" tabIndex={0} aria-label={s.label} aria-pressed={selected === s.id} onClick={() => select(s.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(s.id); } }}><title>{s.label}</title></circle>
          : <circle key={s.id} className={cls} cx={p.x.toFixed(1)} cy={p.y.toFixed(1)} r={rad}><title>{s.label}</title></circle>; })}
    </svg>
    {count ? <><p className="hemi-count" aria-live="polite"><b className="is-d">D {dCount}</b><span className="hemi-count-maj">{majority} for a majority</span><b className="is-r">R {rCount}</b></p>
    <span className="hemi-bar" aria-hidden="true"><i className={`is-d gw-${pct(100 * dCount / seats.length)}`}/><i className={`is-r gw-${pct(100 * rCount / seats.length)}`}/></span></>
    : null}
    <ul className="hemi-key" aria-label="Key">
      <li><svg viewBox="0 0 20 20" aria-hidden="true"><circle className="hemi-seat d-likely is-ring" cx="10" cy="10" r="7"/></svg>Tracked</li>
      <li><svg viewBox="0 0 20 20" aria-hidden="true"><circle className="hemi-seat is-noread" cx="10" cy="10" r="7"/></svg>No polls</li>
      {count ? <li><svg viewBox="0 0 20 20" aria-hidden="true"><circle className="hemi-seat r-lean is-proj" cx="10" cy="10" r="7"/></svg>Projection</li>
        : <li><svg viewBox="0 0 20 20" aria-hidden="true"><circle className="hemi-seat is-off" cx="10" cy="10" r="7"/></svg>As held</li>}
      <li><svg viewBox="0 0 20 20" aria-hidden="true"><line className="hemi-maj" x1="10" y1="2" x2="10" y2="18"/></svg>{majority}</li>
    </ul>
  </div>;
}
