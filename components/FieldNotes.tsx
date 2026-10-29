import { derived, manifest } from '@/lib/data';
import { number } from '@/lib/format';
import { FIELD } from '@/lib/field';

// Method section "Against the field" (Max, 2026-10-29: "comparison and strip"). Other forecasters never move the map, so
// they live here as dated quotes with links; the years live on the dial. Undertow's rows are read from the sealed
// simulation (derived.simulation); nothing is computed here.
const pct = (p: number | null) => (p === null ? '—' : p < 0.005 ? '<1%' : p > 0.995 ? '>99%' : `${Math.round(100 * p)}%`);
const day = (iso: string) => new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
export function FieldNotes() {
  const s = (derived as any).simulation;
  if (!s?.polls_no_lean?.chambers) return null;
  const bet = s.chambers, polls = s.polls_no_lean.chambers, e = s.error_structure;
  const asOf = String(manifest.analytical_as_of || '').slice(0, 10);
  const field = FIELD.filter(f => f.house !== null);
  const lo = Math.min(...field.map(f => f.house as number)), hi = Math.max(...field.map(f => f.house as number));
  const row = (name: string, h: number, hs: string, sn: number, ss: string, when: string, bold = false) => <tr key={name}><td>{bold ? <strong>{name}</strong> : name}</td><td data-label="House, Democrats">{pct(h)} <small>{hs}</small></td><td data-label="Senate, Democrats">{pct(sn)} <small>{ss}</small></td><td data-label="As of">{when}</td></tr>;
  return <section className="method-document mb-10" id="field">
    <h2>The published field</h2>
    <p>Five published models and one market, read at their sources on the dates shown. They are quotes, not calculations, so they do not move with the dial.</p>
    <div className="method-table"><table><thead><tr><th>Forecast</th><th>House, Democrats</th><th>Senate, Democrats</th><th>As of</th></tr></thead><tbody>
      {row('Undertow, my bet', bet.HOUSE.p_control_d, `${bet.HOUSE.d_seats_90[0]} to ${bet.HOUSE.d_seats_90[1]} seats`, bet.SEN.p_control_d, `${bet.SEN.d_seats_90[0]} to ${bet.SEN.d_seats_90[1]}`, day(asOf), true)}
      {row('Undertow, polls alone', polls.HOUSE.p_control_d, `${polls.HOUSE.d_seats_90[0]} to ${polls.HOUSE.d_seats_90[1]} seats`, polls.SEN.p_control_d, `${polls.SEN.d_seats_90[0]} to ${polls.SEN.d_seats_90[1]}`, day(asOf))}
      {FIELD.map(f => <tr key={f.name}><td><a href={f.url} target="_blank" rel="noopener noreferrer">{f.name}</a>{f.note ? <small className="field-note">{f.note}</small> : null}</td><td data-label="House, Democrats">{pct(f.house)}{f.houseSeats ? <small> {f.houseSeats}{f.house !== null ? ' seats' : ' seats'}</small> : null}</td><td data-label="Senate, Democrats">{pct(f.senate)}{f.senateSeats ? <small> {f.senateSeats}</small> : null}</td><td data-label="As of">{day(f.asOf)}</td></tr>)}
    </tbody></table></div>
    <p>These are the dated sources for the comparison in <a href="#models">Other ways to read the same polls</a>, where the same shapes are built here from Undertow’s own data. On the House, Undertow with no lean ({pct(polls.HOUSE.p_control_d)}) sits at the top of a field that runs from {pct(lo)} to {pct(hi)}, because it draws one national miss with a spread of {number(s.national_sd, 1)} points, fit on {e.races} past races, and keeps no prior for a late swing; the forecaster blend above, which keeps one, lands inside the field. On the Senate the lean is what carries the bet from {pct(polls.SEN.p_control_d)} to {pct(bet.SEN.p_control_d)}.</p>
  </section>;
}
