import { derived } from '@/lib/data';
import { number } from '@/lib/format';
import { FIELD } from '@/lib/field';

// Method section for the in-house models (Max, 2026-10-29: "what if we made our own?"; "Go"). Every figure is read from
// derived.models, sealed by analysis/models.py through weight.py; nothing is computed here.
const pct = (p: number | null | undefined) => (typeof p !== 'number' ? '—' : p < 0.005 ? '<1%' : p > 0.995 ? '>99%' : `${Math.round(100 * p)}%`);
export function ModelNotes() {
  const mb = (derived as any).models;
  const sim = (derived as any).simulation;
  if (!mb?.models || !sim) return null;
  const m = mb.models, bt = mb.backtest, env = mb.fundamentals_env;
  const ch = (derived as any).chambers?.chambers || {};
  const seats = (k: string, c: string) => { const x = m[k]?.up_at_default?.[c]; const nu = ch[c]?.not_up || {}; return x ? `${x.D + (nu.D || 0)}–${x.R + (nu.R || 0)}` : '—'; };
  const odds = (k: string, c: string) => pct(m[k]?.simulation?.chambers?.[c]?.p_control_d);
  const field = FIELD.filter(f => f.house !== null);
  const lo = Math.min(...field.map(f => f.house as number)), hi = Math.max(...field.map(f => f.house as number));
  const order = ['polls', 'blend', 'fundamentals', 'ratings'].filter(k => m[k]);
  const sc = (g: any, k: string) => g?.[k];
  return <section className="method-document mb-10" id="models">
    <h2>Other ways to read the same polls</h2>
    <p>The home page has a switch beside the dial: my bet, then four other readings built here from the same sealed data. None of them is graded; the bet is. Each one gives every seat up this year a center, keeps the same correlated spread, and moves with the dial. They exist so a reader can see where the bet sits against the standard ways of reading a midterm, with the arithmetic in the open.</p>
    <ul>
      <li><strong>Polls only.</strong> The polling average as published, no lean. Seats without a poll carry the 2024 result, the generic-ballot shift and the incumbency bonus; untracked governors keep Cook’s rating.</li>
      <li><strong>Forecaster blend.</strong> The shape of a professional forecast: each race’s polls blended with a prior from the state’s 2024 result and this year’s environment, the polls weighted more the more of them there are (the same inverse-variance weights as the Senate partisan term, applied to every office alike). Its national spread is the one its own backtest measured, {number(m.blend?.national_sd, 1)} points.</li>
      <li><strong>Fundamentals.</strong> No 2026 race polls at all. Every seat starts from its 2024 result and moves {number(env?.swing_against_president, 1)} points toward the party out of the White House, the average swing in Senate and governor results against the president’s party across the six midterms from 2002 to 2022 in the archive ({Object.entries(env?.years || {}).map(([y, v]) => `${y}: ${number(v as number, 1)}`).join(', ')}), plus incumbency. It is the structural midterm penalty, nothing else.</li>
      <li><strong>Ratings.</strong> Cook’s ratings turned into margins, the same centers the simulation already uses for untracked governors (Solid ±15, Likely ±8, Lean ±3.5, toss-up even), for every seat up.</li>
    </ul>
    <div className="method-table"><table><thead><tr><th>Reading</th><th>Senate</th><th>House</th><th>Senate, D control</th><th>House, D control</th></tr></thead><tbody>
      <tr><td><strong>My bet</strong></td><td data-label="Senate">{ch.SEN ? `${ch.SEN.at_bet.D}–${ch.SEN.at_bet.R}` : '—'}</td><td data-label="House">{ch.HOUSE ? `${ch.HOUSE.at_bet.D}–${ch.HOUSE.at_bet.R}` : '—'}</td><td data-label="Senate, D control">{pct(sim.chambers?.SEN?.p_control_d)}</td><td data-label="House, D control">{pct(sim.chambers?.HOUSE?.p_control_d)}</td></tr>
      {order.map(k => <tr key={k}><td>{m[k].name}</td><td data-label="Senate">{seats(k, 'SEN')}</td><td data-label="House">{seats(k, 'HOUSE')}</td><td data-label="Senate, D control">{odds(k, 'SEN')}</td><td data-label="House, D control">{odds(k, 'HOUSE')}</td></tr>)}
    </tbody></table></div>
    {bt ? <>
      <p><strong>The record.</strong> Each reading replayed on every Senate and governor race in the archive, {bt.years}, each year using only the years before it, scored seven days out against the result: average miss in points, winners called, and Brier score at a {number(bt.sigma, 0)}-point spread (lower is better). Fundamentals is defined only in midterm years, so the first three rows share that subset.</p>
      <div className="method-table"><table><thead><tr><th>Reading</th><th>Races</th><th>Average miss</th><th>Winner right</th><th>Brier</th></tr></thead><tbody>
        {[['Polls only, midterms', sc(bt.midterms, 'polls')], ['Forecaster blend, midterms', sc(bt.midterms, 'blend')], ['Fundamentals, midterms', sc(bt.midterms, 'fundamentals')], ['Polls only, all years', sc(bt.all_years, 'polls')], ['Forecaster blend, all years', sc(bt.all_years, 'blend')]].map(([name, r]: any) => r ? <tr key={name}><td>{name}</td><td data-label="Races">{r.races}</td><td data-label="Average miss">{number(r.mae, 2)}</td><td data-label="Winner right">{Math.round(100 * r.winner_right)}%</td><td data-label="Brier">{number(r.brier, 4)}</td></tr> : null)}
      </tbody></table></div>
      <p>{bt.ratings_note}. Fundamentals misses by more than twice the polls at the end of a campaign, which is the usual finding and why forecasters let it fade by Election Day; it is here to show what the structure alone says, not as a rival call. The blend edges the polls by a hair, as it should: it is the polls with a little regression toward the state’s record.</p>
    </> : null}
    <p><strong>Against the published field.</strong> {field.map(f => `${f.name} ${pct(f.house)}`).join(', ')} on the House as of their dates (sources on the <a href="#field">field table</a>). The forecaster blend built here gives {odds('blend', 'HOUSE')}, inside that {pct(lo)} to {pct(hi)} range. That says only that a blend built here lands where the published ones do; it tests none of them against a result. My bet is {pct(sim.chambers?.HOUSE?.p_control_d)}, and the Method sections above say why.</p>
  </section>;
}
