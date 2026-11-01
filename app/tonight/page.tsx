import { surname, pageShare } from '@/lib/format';
import type { Metadata } from 'next';
import { races, derived } from '@/lib/data';
import { closeFor, closeInstant, CLOSING_SOURCE } from '@/lib/closing';
import { LocalClose } from '@/components/LocalClose';
import { PageTitle } from '@/components/UI';
import { MarginTrack } from '@/components/Console';

export const metadata:Metadata={title:'Tonight',description:'Every race Undertow reads, in the order its polls close on November 3, with the polls, my number, and what a 2020-sized miss would say.',...pageShare('/tonight/','Tonight','Every race Undertow reads, in the order its polls close on November 3, with the polls, my number, and what a 2020-sized miss would say.')};

// Election night in poll-closing order (Max, 2026-10-28, "Do it" to the election-night plan): the first hours test the bet.
const EVEN = 0.05;
const last = surname;
const fmt = (m: number, d: string, r: string, dl: string) => Math.abs(m) < EVEN ? 'Even' : `${last(m > 0 ? d : r)} (${m > 0 ? dl : 'R'}) +${Math.abs(m).toFixed(1)}`;
const cls = (m: number) => (m >= EVEN ? 'lead-number-d' : m <= -EVEN ? 'lead-number-r' : '');

export default function Tonight() {
  const h2020 = ((derived as any).signals?.history_presets || []).find((h: any) => h.year === 2020)?.miss_toward_d as number | undefined;
  const rows = (races as any[]).filter(r => r.signal && Number.isFinite(r.signal.adjusted_margin)).map(r => {
    const s = r.signal; const c = closeFor(r.id); const dl = /^independent/i.test(String((derived as any).candidates?.[r.id]?.D?.party || '')) || r.id === '2026-NE-SEN' ? 'I' : 'D';
    const at2020 = h2020 === undefined ? null : s.polling_margin + h2020 + (Number(s.polling_error?.state_adjustment) || 0) + (Number(s.delta_spending) || 0) + (Number(s.delta_early_vote) || 0) + (Number(s.delta_partisan) || 0);
    return { r, s, c, dl, at2020, d: r.heat.candidates.D.candidate, rep: r.heat.candidates.R.candidate };
  }).filter(x => x.c).sort((a, b) => a.c!.order - b.c!.order || Math.abs(a.s.adjusted_margin) - Math.abs(b.s.adjusted_margin));
  const hours = [...new Set(rows.map(x => x.c!.at))];
  return <>
    <PageTitle kicker="Election night · November 3 · Eastern Time" title="What to watch, in order."><p>Every race I read, listed by when its polls close. Each shows the polling average, my number, and what the race looks like if the polls miss the way they did in 2020{h2020 !== undefined ? <> ({Math.abs(h2020).toFixed(1)} points toward Republicans)</> : null}. The first two hours carry most of the test: if Georgia, North Carolina and Ohio come in closer to my number than to the polls, the bet is holding.</p></PageTitle>
    {hours.map(h => <section key={h}>
      <h2 className="tonight-hour">{h} ET<LocalClose iso={closeInstant(h)}/><small>{(n => `${n} ${n === 1 ? "race" : "races"}`)(rows.filter(x => x.c!.at === h).length)}</small></h2>
      <div className="c-panel method-table"><table><thead><tr><th>Race</th><th>Status</th><th>Polls</th><th>Undertow</th><th>If 2020 again</th></tr></thead><tbody>
        {rows.filter(x => x.c!.at === h).map(x => <tr key={x.r.id}>
          <th scope="row"><a href={`/race/${x.r.slug}/`}>{x.r.name}</a>{x.c!.note ? <small className="muted block">{x.c!.note}</small> : null}</th>
          <td data-label="Status"><MarginTrack v={x.s.adjusted_margin} tick={x.s.polling_margin}/></td>
          <td data-label="Polls" className={`mono ${cls(x.s.polling_margin)}`}>{fmt(x.s.polling_margin, x.d, x.rep, x.dl)}</td>
          <td data-label="Undertow" className={`mono ${cls(x.s.adjusted_margin)}`}>{fmt(x.s.adjusted_margin, x.d, x.rep, x.dl)}</td>
          <td data-label="If 2020 again" className={`mono ${x.at2020 === null ? '' : cls(x.at2020)}`}>{x.at2020 === null ? 'NA' : fmt(x.at2020, x.d, x.rep, x.dl)}</td>
        </tr>)}
      </tbody></table></div>
    </section>)}
    <p className="muted mt-6 text-sm">Closing times from <a href={CLOSING_SOURCE.url} target="_blank" rel="noopener noreferrer">{CLOSING_SOURCE.name}</a>, fetched {CLOSING_SOURCE.fetched}. A state that spans two time zones is listed when its last polls close. Results posted before then come from the earlier zone. House districts without public polls are not listed; they appear on the House view of the home page.</p>
  </>;
}
