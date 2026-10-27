import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { derived,races,publicEstimates,pollsterNames,signalsMeta } from '@/lib/data';
import { MethodNotes, signalLines } from '@/components/SignalReading';
import { Both,RecallLegend,Empty } from '@/components/UI';
import { Conditions } from '@/components/RaceLedger';
import { RecallComparison } from '@/components/RecallComparison';
import { DotPlot } from '@/components/Charts';
import { Panel, Figure, FactorBars, MarginTrack, tone, EVEN } from '@/components/Console';
import { margin,number,shortDate } from '@/lib/format';
export function generateStaticParams(){return races.map(r=>({slug:r.slug}));}
export const dynamicParams=false;
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{const {slug}=await params;const r=races.find(r=>r.slug===slug);return {title:r?.name||'Race not found',openGraph:r?{title:`${r.name} · Undertow`,description:'The polls, my number, and the pull between them. By Max Sheahan.',images:[{url:`/og/${r.slug}.png`,width:1200,height:630,alt:`${r.name}: polls, Undertow and the pull`}]}:undefined,twitter:r?{card:'summary_large_image',images:[`/og/${r.slug}.png`]}:undefined,description:r?`${r.name}: the polls, my number and the pull between them, with every poll and source behind it.`:'Race not found'};}

// Races whose D slot holds an independent (Nebraska: Dan Osborn).
const INDEPENDENT_D_SLOT=new Set(['2026-NE-SEN']);
const lastName=(n:string)=>n.trim().split(/\s+/).pop()||n;
function label(v:number,names:{D:string;R:string}){return Math.abs(v)<EVEN?'Even':`${lastName(v>0?names.D:names.R)} +${Math.abs(v).toFixed(1)}`;}

// The single-race console (Max, 2026-10-27: "We need to rethink site ui"; one design system across every page).
function RaceHead({r}:{r:any}){const s=r.signal;const names={D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate};const dl=INDEPENDENT_D_SLOT.has(r.id)?'I':'D';
 const polls=Number(s?.polling_margin??r.polling_read?.margin);const und=Number(s?.adjusted_margin);const pull=und-polls;const ok=Number.isFinite(polls)&&Number.isFinite(und);
 return <Panel className="race-head" kicker={<>2026 · {r.id.split('-')[1]} · {r.id.includes('GOV')?'Governor':'Senate'}{r.id.includes('SPECIAL')?' · special':''}</>} action={<a className="c-link" href="/">← All races</a>}>
  <h1 className="race-title">{r.name}</h1>
  <p className="race-matchup"><span className="is-d">{names.D} ({dl})</span> vs <span className="is-r">{names.R} (R)</span></p>
  {ok?<><div className="race-figures">
   <Figure label="Polls" value={label(polls,names)} v={polls} sub={r.polling_read?.kind==='LATEST_POLL'?'one published poll':`${r.polling_read?.poll_count} polls, weighted`}/>
   <Figure label="Undertow" value={label(und,names)} v={und} sub={`± ${Number(s.range_sd).toFixed(1)} · my call, frozen Nov 2`}/>
   <Figure label="The pull" value={Math.abs(pull)<EVEN?'None':`${Math.abs(pull).toFixed(1)} → ${pull>0?dl:'R'}`} v={pull} sub="Undertow minus the polls"/>
  </div>
  <div className="race-trackrow"><span className="is-r">◀ {lastName(names.R)}</span><MarginTrack v={und} tick={polls} large/><span className="is-d">{lastName(names.D)} ▶</span></div>
  <p className="c-sub race-trackkey"><i className="c-key-tick"/> polls · bar: Undertow</p></>
  :<p className="c-sub">No verified polling read in this snapshot.</p>}
 </Panel>;}

function WhyPull({r}:{r:any}){const s=r.signal;if(!s||!Number.isFinite(s.adjusted_margin))return null;const names={D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate};
 const national=Number(s.polling_error?.national)||0;const state=Number(s.polling_error?.state_adjustment)||0;
 const parts=[{label:'Last fall’s polling miss',v:national},{label:'This state’s polling record',v:state},{label:s.spending?.coverage==='DIGITAL_CANDIDATE'?'Campaign ad spending':'Outside spending',v:Number(s.delta_spending)||0},{label:'Early vote',v:Number(s.delta_early_vote)||0}];
 const lines=signalLines(s,names,signalsMeta);
 return <Panel className="race-why" kicker="Why the pull">
  <FactorBars parts={parts}/>
  <dl className="race-explain">{lines.map(l=><div key={l.key}><dt>{l.label}</dt><dd>{l.text}</dd></div>)}</dl>
  <MethodNotes s={s} meta={signalsMeta}/>
 </Panel>;}

function ThePolls({r}:{r:any}){const read=r.polling_read;const latest=read?.kind==='LATEST_POLL'?read.latest_poll:null;
 return <Panel className="race-polls" kicker="The polls">
  <DotPlot estimates={publicEstimates(r.id)} name={r.name}/>
  <ul className="race-facts">
   {read&&<li>{latest?'One published poll':`${read.poll_count} comparable polls`} · newest finished {shortDate(read.field_end)} ({read.age_days} {read.age_days===1?'day':'days'} old)</li>}
   {read&&(latest||Number(read.poll_count)<=2)&&<li className="c-flag">Thin evidence: {latest?'one published poll':`only ${read.poll_count} polls`} behind this number.</li>}
   {/-ME-|-AK-/.test(r.id)&&<li className="c-flag">{r.id.includes('-ME-')?'Maine':'Alaska'} uses ranked-choice voting. These are first-choice numbers, and second choices can change the result.</li>}
   <li>Averaging stratum: {r.averaging_stratum?`${r.averaging_stratum.round} / ${r.averaging_stratum.denominator_class} / ${r.averaging_stratum.pop}`:'NA'}. {r.averaging_stratum_reason}</li>
  </ul>
 </Panel>;}

function Ledger({r}:{r:any}){const estimates=publicEstimates(r.id);
 return <Panel className="race-ledger-panel" kicker="Every poll" action={<RecallLegend/>}>
  <p className="c-sub">All non-quarantined stored variants. Principal selection and primary verification are separate from recall classification; a displayed estimate need not enter an average. Quarantined rows appear only on <a href="/excluded/">Excluded</a>.</p>
  {!estimates.length?<Empty title="No poll estimates">No eligible source records in this release.</Empty>:<table className="source-table w-full"><thead><tr><th>Pollster / field dates</th><th>D / R share</th><th>Margin</th><th>Recall</th><th>Stratum</th><th>Selection / source</th></tr></thead><tbody>{estimates.map((e:any)=><tr key={e.estimate_id}><th scope="row">{pollsterNames[e.pollster_id]||e.pollster_id}{(e.pollster_alignment==="D"||e.pollster_alignment==="R")?<span className="party-tag">{e.pollster_alignment==="D"?"Democratic-aligned":"Republican-aligned"}</span>:String(e.sponsor_class||"").startsWith("PARTISAN")?<span className="party-tag">Partisan sponsor</span>:null}<span className="muted block text-xs font-normal">{shortDate(e.field_start)}–{shortDate(e.field_end)}</span></th><td data-label="D / R share" className="mono">{number(e.D)} / {number(e.R)}</td><td data-label="Margin" className="mono">{margin(e.margin)}</td><td data-label="Recall" className={`recall-${e.recall_weighted.toLowerCase()}`}>{e.recall_weighted==='YES'?'▲':e.recall_weighted==='NO'?'●':'■'} {e.recall_weighted}</td><td data-label="Stratum" className="text-xs">{e.round} / {e.pop} / {e.denominator_class}<span className="muted block">{e.window}</span></td><td data-label="Selection / source" className="text-xs"><span>{e.selected==='1'?'Principal':'Alternate'} · primary {e.primary_verified}</span><a href={e.source_url} target="_blank" rel="noopener noreferrer" className="block">Source ↗︎</a></td></tr>)}</tbody></table>}
 </Panel>;}

export default async function Race({params}:{params:Promise<{slug:string}>}) {const {slug}=await params;const r=races.find(r=>r.slug===slug);if(!r)notFound();
 const drawers=<>
  <details className="c-drawer"><summary>All race readings<span aria-hidden="true">+</span></summary><div className="c-drawer-body"><dl className="conditions grid gap-4 sm:grid-cols-3"><Conditions r={r}/></dl></div></details>
  <details className="c-drawer"><summary>Explore coverage temperature · stale Oct 8<span aria-hidden="true">+</span></summary>{r.coverage?<section className="c-drawer-body"><p className="status-note mb-4 text-sm">STALE_FLAG · returned edition {r.coverage.returned_edition}; expected {r.coverage.expected_edition}. Query match: {r.coverage.match_status}.</p><dl className="conditions grid gap-4 sm:grid-cols-3"><div><dt>Stories / outlets</dt><dd className="mono">{r.coverage.story_count} / {r.coverage.outlet_count}</dd></div><div><dt>Coverage range</dt><dd className="mono">{number(r.coverage.ph_low)} to {number(r.coverage.ph_high)} pH</dd></div><div><dt>Spread</dt><dd className="mono">{number(r.coverage.spread)} pH</dd></div><div><dt>Calmest outlet</dt><dd>{r.coverage.calmest_outlet}</dd></div><div><dt>Hottest outlet</dt><dd>{r.coverage.hottest_outlet}</dd></div></dl><p className="muted mt-4 text-sm">Coverage pH describes outlet framing, a different unit from candidate rhetoric. Partial candidate matches and stale results are context only.</p></section>:<section className="c-drawer-body"><p className="muted text-sm">No coverage reading for this race. It was added to Undertow on October 27, after the October 8 coverage snapshot.</p></section>}</details>
 </>;
 return <div className="race-console">
  <RaceHead r={r}/>
  <Both desktop={<div className="race-grid"><WhyPull r={r}/><ThePolls r={r}/></div>} mobile={<div className="race-stack"><WhyPull r={r}/><ThePolls r={r}/></div>}/>
  {r.recallComparison&&<Panel className="race-recall" kicker="Weighting by recalled 2024 vote"><RecallComparison r={r} pollsterNames={pollsterNames}/></Panel>}
  <Ledger r={r}/>
  {drawers}
 </div>;}
