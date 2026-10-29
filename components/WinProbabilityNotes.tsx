import { derived } from '@/lib/data';
import { number } from '@/lib/format';

// Method section for win probability (Max, 2026-10-29: "We can add win probability"). Every figure is read from the
// sealed release (derived.simulation, written by analysis/simulate.py through weight.py); nothing is computed here.
const pctOf = (p: number) => (p < 0.005 ? 'under 1%' : p > 0.995 ? 'over 99%' : `${Math.round(100 * p)}%`);
export function WinProbabilityNotes() {
  const s = (derived as any).simulation;
  if (!s) return null;
  const e = s.error_structure; const sen = s.chambers.SEN, hse = s.chambers.HOUSE;
  const iSen = s.independent.SEN, pSen = s.polls_no_lean?.chambers?.SEN, pHse = s.polls_no_lean?.chambers?.HOUSE;
  return <section className="method-document mb-10" id="win-probability">
    <h2>Win probability</h2>
    <p>A reading is a center, not a certainty. To turn the readings into odds, the calculator runs {number(s.sims, 0)} simulated elections. In each one every seat up this year lands somewhere around its reading, and the seats are counted. A chamber’s chance of control is the share of those elections in which a party reaches the majority.</p>
    <p><strong>Polling misses move together.</strong> In the archive of past polling ({e.races} Senate and governor races in even years, {e.from} to {e.to}), a year’s polls miss in the same direction by about {number(e.shared_sd_measured, 1)} points on average across the whole country. Two races in the same state that year share a further miss of about {number(e.state_sd, 1)} points, and states in the same part of the country share a little more ({number(e.division_sd, 1)}). Each simulated election draws all of these at once: one national miss, one per region, one per state, and then each race’s own. The national part uses the uncertainty of my bet itself ({number(s.national_sd, 1)} points), so the odds carry the chance that I am wrong about the lean.</p>
    <p><strong>Why it matters.</strong> Counted as if every race were its own coin, the Senate would look {pctOf(iSen.p_control_d)} Democratic. With the misses moving together it is {pctOf(sen.p_control_d)}. I tested this on every year from 2010 to 2024, fitting the model only on the years before each one. Treated as independent, the number of races Democrats won fell outside the 90% range in 3 of 8 years (2014, 2020 and 2022). With the misses moving together it fell inside all 8, and not by making the ranges huge: the actual counts landed across the whole range, not bunched in the middle.</p>
    <p><strong>What did not change.</strong> Each race keeps a total spread of {number(s.race_total_sd, 0)} points, the same as before{s.tail_df ? <>, drawn from a fatter-tailed curve than a bell curve (Student t, {s.tail_df} degrees of freedom), which scored better on past races</> : null}. I tested a wider spread for races with only one or two polls; it scored worse on those races, so it was dropped. Untracked seats use the 2022 test of the projection ({number(s.projection_residual_sd, 1)} points of district-level miss). Governors Undertow does not track turn Cook’s rating into a center I chose, not one I fit; they count toward the governor range only.</p>
    <p><strong>At my bet</strong>, Democrats control the Senate in {pctOf(sen.p_control_d)} of simulated elections ({sen.d_seats_90[0]} to {sen.d_seats_90[1]} Democratic seats, 90% of the time) and the House in {pctOf(hse.p_control_d)} ({hse.d_seats_90[0]} to {hse.d_seats_90[1]}).{pSen && pHse ? <> If the polls are right on average, with no lean, the Senate is {pctOf(pSen.p_control_d)} and the House {pctOf(pHse.p_control_d)}.</> : null} The odds follow the dial: moving it shifts every reading and projection and keeps the same spread around them. On election night, once races are counted, the odds come off the console, because they do not know the count.</p>
  </section>;
}
