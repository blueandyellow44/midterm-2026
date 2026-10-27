'use client';
import { useMemo, useState } from 'react';

// Exploration only: the frozen call is Undertow's number. The dial sets a national polling miss m, in either direction.
// Each race = polls + m + its own state adjustment + its spending and early-vote terms (the `spending` field carries both). At m = the national lean this reproduces
// Undertow's number exactly; at m = 0 it is the polls plus each state's record and the spending signal; a negative m
// means polls are undercounting Republicans (Max, 2026-10-27: "poll slider needs to go both ways").
export type DialRace = { id: string; name: string; d: string; r: string; polls: number; stateAdj: number; spending: number };
const EVEN = 0.05;
const last = (n: string) => n.trim().split(/\s+/).pop();

export function PollMissDial({ races, national, lastFall }: { races: DialRace[]; national: number; lastFall: number }) {
  const [m, setM] = useState(national);
  const span = Math.max(8, Math.ceil(lastFall));
  const rows = useMemo(() => races.map(r => ({ ...r, margin: r.polls + m + r.stateAdj + r.spending })).sort((a, b) => b.margin - a.margin), [races, m]);
  const dLeads = rows.filter(r => r.margin >= EVEN).length, rLeads = rows.filter(r => r.margin <= -EVEN).length;
  const near = (x: number) => Math.abs(m - x) < 0.05;
  const mark = near(national) ? 'my bet' : near(0) ? 'no national miss' : near(lastFall) ? 'last fall\u2019s miss repeats in full' : near(-lastFall) ? 'a miss this size the other way' : null;
  const dir = m >= EVEN ? 'understate Democrats' : m <= -EVEN ? 'understate Republicans' : 'miss neither way';
  return <section className="dial" aria-label="How wrong are the polls?">
    <h2>How wrong are the polls?</h2>
    <p className="dial-intro">Slide either way to set how far polls miss this year: right for polls that understate Democrats, left for polls that understate Republicans, as in 2016, 2020 and 2024. My bet sits at {national.toFixed(1)} points toward Democrats. Each race keeps its own state record, spending and early vote. This is for exploring; the call I am graded on stays my number.</p>
    <div className="dial-control">
      <input type="range" min={-span} max={span} step={0.1} value={m} onChange={e => setM(Number(e.target.value))} aria-label="National polling miss in points; negative means polls understate Republicans"/>
      <div className="dial-scale"><span>Understate Republicans</span><span>Understate Democrats</span></div>
      <div className="dial-readout"><strong>{Math.abs(m).toFixed(1)}</strong> points: polls {dir}{mark ? <span> · {mark}</span> : null}</div>
      <div className="dial-presets">
        <button type="button" onClick={() => setM(-5)}>Polls miss Republicans by 5</button>
        <button type="button" onClick={() => setM(0)}>No national miss</button>
        <button type="button" onClick={() => setM(national)}>My bet</button>
        <button type="button" onClick={() => setM(lastFall)}>Last fall repeats</button>
      </div>
    </div>
    <p className="dial-tally"><span className="lead-number-d">Democrats lead {dLeads}</span> · <span className="lead-number-r">Republicans lead {rLeads}</span>{rows.length - dLeads - rLeads ? ` · even ${rows.length - dLeads - rLeads}` : ''}</p>
    <ul className="dial-list">{rows.map(r => <li key={r.id}><span>{r.name}</span><span className={`mono ${r.margin >= EVEN ? 'lead-number-d' : r.margin <= -EVEN ? 'lead-number-r' : ''}`}>{Math.abs(r.margin) < EVEN ? 'Even' : `${last(r.margin > 0 ? r.d : r.r)} +${Math.abs(r.margin).toFixed(1)}`}</span></li>)}</ul>
  </section>;
}
