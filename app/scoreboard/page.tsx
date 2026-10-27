import type { Metadata } from 'next';
import { races, derived } from '@/lib/data';
import { loadLive, settled, SETTLED_REPORTING } from '@/lib/live';
import { PageTitle } from '@/components/UI';
import { Signup } from '@/components/Signup';

export const metadata: Metadata = { title: 'Scoreboard', description: 'Election night: the polls against Undertow, race by race, as the votes are counted.' };

const EVEN = 0.05;
const last = (n: string) => String(n).trim().split(/\s+/).pop();
const fmt = (m: number, d: string, r: string) => !Number.isFinite(m) ? 'NA' : Math.abs(m) < EVEN ? 'Even' : `${last(m > 0 ? d : r)} +${Math.abs(m).toFixed(1)}`;
const cls = (m: number) => m >= EVEN ? 'lead-number-d' : m <= -EVEN ? 'lead-number-r' : '';

export default function Scoreboard() {
  const live = loadLive();
  const rows = races.map((r: any) => {
    const s = r.signal; const d = r.heat.candidates.D.candidate; const rep = r.heat.candidates.R.candidate;
    const c = live.races[r.slug];
    const count = c ? c.d_pct - c.r_pct : NaN;
    const pollErr = c ? Math.abs(s.polling_margin - count) : NaN, ourErr = c ? Math.abs(s.adjusted_margin - count) : NaN;
    const winner = c && settled(c) ? (Math.abs(pollErr - ourErr) < EVEN ? 'tie' : ourErr < pollErr ? 'undertow' : 'polls') : null;
    return { r, s, d, rep, c, count, pollErr, ourErr, winner };
  });
  const done = rows.filter(x => x.winner);
  const ours = done.filter(x => x.winner === 'undertow').length, theirs = done.filter(x => x.winner === 'polls').length;
  const started = Object.keys(live.races).length > 0;
  return <>
    <PageTitle kicker="Election night · November 3" title="The polls against Undertow."><p>Each race compares the polling average and my number with the count as it comes in. A race joins the tally once it is called or {SETTLED_REPORTING}% counted. Counts are unofficial, entered by hand from each state's official results page, and linked on every row. My numbers are from {derived.analytical_as_of.slice(0, 10)}.</p></PageTitle>
    <section className="scoreboard-tally" aria-live="polite">
      {started ? <><p className="tally-line"><strong>Undertow closer in {ours}</strong> · polls closer in {theirs} · {done.length} of {rows.length} races settled</p><p className="muted text-sm">Last updated {live.updated_at ? new Date(live.updated_at).toLocaleString('en-US', { timeZone: 'America/Los_Angeles', dateStyle: 'medium', timeStyle: 'short' }) + ' Pacific' : 'NA'}.</p></>
        : <p className="tally-line">Counting starts the evening of November 3. Until then, this page shows the numbers the night will test.</p>}
    </section>
    <div className="scoreboard-table method-table"><table><thead><tr><th>Race</th><th>Polls</th><th>Undertow</th><th>The count</th><th>Closer</th></tr></thead><tbody>
      {rows.map(x => <tr key={x.r.id}>
        <th scope="row"><a href={`/race/${x.r.slug}/`}>{x.r.name}</a></th>
        <td className={`mono ${cls(x.s.polling_margin)}`}>{fmt(x.s.polling_margin, x.d, x.rep)}</td>
        <td className={`mono ${cls(x.s.adjusted_margin)}`}>{fmt(x.s.adjusted_margin, x.d, x.rep)}</td>
        <td className="mono">{x.c ? <><span className={cls(x.count)}>{fmt(x.count, x.d, x.rep)}</span><small className="muted block"><a href={x.c.source} target="_blank" rel="noopener noreferrer">{x.c.reporting_pct.toFixed(0)}% counted</a>{x.c.called ? ` · called for ${last(x.c.called === 'D' ? x.d : x.rep)}` : ''}</small></> : <span className="muted">Not yet</span>}</td>
        <td>{x.winner === 'undertow' ? <strong className="accent-text">Undertow, by {(x.pollErr - x.ourErr).toFixed(1)}</strong> : x.winner === 'polls' ? <strong>Polls, by {(x.ourErr - x.pollErr).toFixed(1)}</strong> : x.winner === 'tie' ? 'Even' : x.c ? <span className="muted">Still counting</span> : <span className="muted">Not yet</span>}</td>
      </tr>)}
    </tbody></table></div>
    <p className="muted mt-4 text-sm">Closer means nearer to the count's margin between the two candidates. Early counts swing as different kinds of ballots are added, so a race is only scored once it is called or nearly complete. The final grade uses certified results.</p>
    <Signup placement="scoreboard"/>
  </>;
}
