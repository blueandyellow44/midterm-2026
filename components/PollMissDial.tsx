'use client';
import { useMemo, useState } from 'react';

// Exploration only: the frozen call is Undertow's number. At the dial's "national miss" m, each race moves by
// m x (its state lean / the national lean), plus its spending term. At m = the national lean this reproduces
// Undertow's number exactly; at 0 it is the polls plus spending.
export type DialRace = { id: string; name: string; d: string; r: string; polls: number; lean: number; spending: number };
const EVEN = 0.05;
const last = (n: string) => n.trim().split(/\s+/).pop();

export function PollMissDial({ races, national, lastFall }: { races: DialRace[]; national: number; lastFall: number }) {
  const [m, setM] = useState(national);
  const rows = useMemo(() => races.map(r => ({ ...r, margin: r.polls + (national ? r.lean / national : 1) * m + r.spending }))
    .sort((a, b) => b.margin - a.margin), [races, national, m]);
  const dLeads = rows.filter(r => r.margin >= EVEN).length, rLeads = rows.filter(r => r.margin <= -EVEN).length;
  const mark = Math.abs(m - national) < 0.05 ? 'Undertow’s bet' : m < 0.05 ? 'No polling miss, spending only' : Math.abs(m - lastFall) < 0.05 ? 'Last fall’s miss repeats in full' : null;
  return <section className="dial" aria-label="How wrong are the polls?">
    <h2>How wrong are the polls?</h2>
    <p className="dial-intro">Slide to set how far polls understate Democrats this year. My bet sits at {national.toFixed(1)} points. This is for exploring; the call I am graded on stays my number.</p>
    <div className="dial-control">
      <input type="range" min={0} max={Math.max(8, Math.ceil(lastFall))} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label="Polling miss toward Democrats, in points"/>
      <div className="dial-readout"><strong>{m.toFixed(1)}</strong> points toward Democrats{mark ? <span> · {mark}</span> : null}</div>
      <div className="dial-presets">
        <button type="button" onClick={() => setM(0)}>No polling miss</button>
        <button type="button" onClick={() => setM(national)}>My bet</button>
        <button type="button" onClick={() => setM(lastFall)}>Last fall repeats</button>
      </div>
    </div>
    <p className="dial-tally"><span className="lead-number-d">Democrats lead {dLeads}</span> · <span className="lead-number-r">Republicans lead {rLeads}</span>{rows.length - dLeads - rLeads ? ` · even ${rows.length - dLeads - rLeads}` : ''}</p>
    <ul className="dial-list">{rows.map(r => <li key={r.id}><span>{r.name}</span><span className={`mono ${r.margin >= EVEN ? 'lead-number-d' : r.margin <= -EVEN ? 'lead-number-r' : ''}`}>{Math.abs(r.margin) < EVEN ? 'Even' : `${last(r.margin > 0 ? r.d : r.r)} +${Math.abs(r.margin).toFixed(1)}`}</span></li>)}</ul>
  </section>;
}
