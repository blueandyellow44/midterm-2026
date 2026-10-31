import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { derived,races,publicEstimates,pollsterNames,signalsMeta,predictions } from '@/lib/data';
import { MethodNotes, signalLines } from '@/components/SignalReading';
import { Both,RecallLegend,Empty } from '@/components/UI';
import { Conditions } from '@/components/RaceLedger';
import { RecallComparison } from '@/components/RecallComparison';
import { DotPlot, CandidateChart } from '@/components/Charts';
import { Panel, Figure, FactorBars, MarginTrack, tone, EVEN } from '@/components/Console';
import { margin,number,shortDate, surname, pollCountLabel, SPONSOR_TIER_TAG, SITE_PREVIEW_IMAGE } from '@/lib/format';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
export function generateStaticParams(){return races.map(r=>({slug:r.slug}));}
export const dynamicParams=false;
// Races with no polling read have no per-race card (build_share_cards.py draws only read races); they share the site card.
const raceImage=(slug:string)=>existsSync(join(process.cwd(),'public/og',`${slug}.png`))?`/og/${slug}.png`:SITE_PREVIEW_IMAGE.url;
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{const {slug}=await params;const r=races.find(r=>r.slug===slug);const img=r?raceImage(r.slug):'';return {title:r?.name||'Race not found',alternates:r?{canonical:`/race/${r.slug}/`}:undefined,openGraph:r?{title:`${r.name} · Undertow`,siteName:'Undertow',type:'website',url:`/race/${r.slug}/`,description:'The polls, my number, and the pull between them. By Max Sheahan.',images:[{url:img,width:1200,height:630,alt:img===SITE_PREVIEW_IMAGE.url?SITE_PREVIEW_IMAGE.alt:`${r.name}: polls, Undertow and the pull`}]}:undefined,twitter:r?{card:'summary_large_image',images:[img]}:undefined,description:r?`${r.name}: the polls, my number and the pull between them, with every poll and source behind it.`:'Race not found'};}

// Races whose D slot holds an independent (Nebraska: Dan Osborn).
const INDEPENDENT_D_SLOT=new Set(['2026-NE-SEN','2026-AK-AL-HOUSE']);
const lastName=surname;
function label(v:number,names:{D:string;R:string}){return Math.abs(v)<EVEN?'Even':`${lastName(v>0?names.D:names.R)} +${Math.abs(v).toFixed(1)}`;}

// The single-race console (Max, 2026-10-27: "We need to rethink site ui"; one design system across every page).
function RaceHead({r}:{r:any}){const s=r.signal;const names={D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate};const dl=INDEPENDENT_D_SLOT.has(r.id)||/^independent/i.test(String((derived as any).candidates?.[r.id]?.D?.party||''))?'I':'D';
 const n=(v:unknown)=>v===null||v===undefined||v===''?NaN:Number(v);   // Number(null) is 0, which read a no-poll race as a tie
 const polls=n(s?.polling_margin??r.polling_read?.margin);const und=n(s?.adjusted_margin);const pull=und-polls;const ok=Number.isFinite(polls)&&Number.isFinite(und);
 const proj=((derived as any).chambers?.chambers?.HOUSE?.items||[]).find((i:any)=>i.race===r.id&&i.kind==='projection');
 return <Panel className="race-head" kicker={<>2026 · {r.id.split('-')[1]} · {r.id.endsWith('HOUSE')?`House · ${r.id.split('-')[2]==='AL'?'at-large':`district ${Number(r.id.split('-')[2])}`}`:r.id.includes('GOV')?'Governor':'Senate'}{r.id.includes('SPECIAL')?' · special':''}</>} action={<a className="c-link" href="/">← All races</a>}>
  <h1 className="race-title">{r.name}</h1>
  <p className="race-matchup"><span className="is-d">{names.D} ({dl})</span> vs <span className="is-r">{names.R} (R)</span></p>
  {ok?<><div className="race-figures">
   <Figure label="Polls" value={label(polls,names)} v={polls} sub={r.polling_read?.kind==='LATEST_POLL'?'one published poll':pollCountLabel(r.polling_read?.poll_count,(derived as any).signals?.polling_v2?.per_race?.[r.id]?.sponsored_only===true)}/>
   <Figure label="Undertow" value={label(und,names)} v={und} sub={`± ${Number(s.range_sd).toFixed(1)} · my call, ${predictions?'frozen':'freezes'} Nov 2`}/>
   <Figure label="The pull" value={Math.abs(pull)<EVEN?'None':`${Math.abs(pull).toFixed(1)} → ${pull>0?dl:'R'}`} v={pull} sub="Undertow minus the polls"/>
  </div>
  <div className="race-trackrow"><span className="is-r">◀ {lastName(names.R)}</span><MarginTrack v={und} tick={polls} large/><span className="is-d">{lastName(names.D)} ▶</span></div>
  <p className="c-sub race-trackkey"><i className="c-key-tick"/> polls · bar: Undertow</p>
  {(()=>{const p=Number((derived as any).simulation?.per_seat?.[r.id]?.p_d);if(!Number.isFinite(p))return null;const pc=Math.max(0,Math.min(100,Math.round(100*p)));const cl=(x:number)=>x<0.005?'<1%':x>0.995?'>99%':`${Math.round(100*x)}%`;
   return <div className="wall-chance race-chance"><p className="c-label">Chance to win, at my bet</p><p className="wall-chance-names"><span className="is-d">{lastName(names.D)} {cl(p)}</span><span className="is-r">{lastName(names.R)} {cl(1-p)}</span></p><span className="wall-chance-bar" aria-hidden="true"><i className={`is-d gw-${pc}`}/><i className={`is-r gw-${100-pc}`}/></span><p className="c-sub">From 20,000 simulated elections in which polling misses move together across states. <a href="/method/#win-probability">How</a></p></div>;})()}</>
  :<><p className="c-sub race-noread">{r.id.endsWith('HOUSE')?'No public poll of this race since September 1 could be verified at its source, so Undertow makes no call here and nothing on this page is graded.':'No verified polling read in this snapshot.'}</p>
   {proj&&<p className="race-proj">For the chamber count it is projected from its 2024 vote and the national swing: <strong className={tone(proj.undertow)}>{label(proj.undertow,names)}</strong>. A projection, not a reading.</p>}</>}
 </Panel>;}

function HouseFacts({r}:{r:any}){const c=(derived as any).candidates?.[r.id];if(!c?.rating)return null;const sp=r.signal?.spending;const total=(Number(sp?.d_fav_recent)||0)+(Number(sp?.r_fav_recent)||0);const p=Number(c.pres2024_d_minus_r);
 return <Panel className="race-house" kicker="The district">
  <dl className="conditions grid gap-4 sm:grid-cols-4">
   <div><dt>Cook rating</dt><dd>{c.rating} <span className="c-sub">({shortDate(c.rating_date)})</span></dd></div>
   <div><dt>Incumbent</dt><dd>{c.incumbent==='OPEN'?'Open seat':`${c.incumbent} (${c.incumbent_party})`}</dd></div>
   <div><dt>2024 president, this district</dt><dd className={`mono ${tone(p)}`}>{Math.abs(p)<EVEN?'Even':`${p>0?'Harris':'Trump'} +${Math.abs(p).toFixed(1)}`}</dd></div>
   <div><dt>Outside money, two weeks</dt><dd className="mono">{Number.isFinite(total)?`$${(total/1e6).toFixed(1)}M`:'NA'}</dd></div>
  </dl>
  {c.lines_note&&<p className="c-sub mt-3">{c.lines_note}</p>}
 </Panel>;}

function WhyPull({r}:{r:any}){const s=r.signal;if(!s||!Number.isFinite(s.adjusted_margin))return null;const names={D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate};
 const national=Number(s.polling_error?.national)||0;const state=Number(s.polling_error?.state_adjustment)||0;
 const parts=[{label:'Last fall’s polling miss',v:national},{label:'This state’s polling record',v:state},{label:s.spending?.coverage==='DIGITAL_CANDIDATE'?'Campaign ad spending':'Outside spending',v:Number(s.delta_spending)||0},{label:'Early vote',v:Number(s.delta_early_vote)||0},...(r.id.includes('-SEN')?[{label:'The state’s partisan record',v:Number(s.delta_partisan)||0}]:[])];
 const lines=signalLines(s,names,signalsMeta);
 return <Panel className="race-why" kicker="Why the pull">
  <FactorBars parts={parts}/>
  <dl className="race-explain">{lines.map(l=><div key={l.key}><dt>{l.label}</dt><dd>{l.text}</dd></div>)}</dl>
  <MethodNotes s={s} meta={signalsMeta}/>
 </Panel>;}

const WINDOW_LABEL:Record<string,string>={BOTH:'October',HOUSE_ONLY:'September',OUT_OF_WINDOW:'before September 1, context only',BACKTEST:'2025 backtest'};
function ThePolls({r}:{r:any}){const read=r.polling_read?.kind==='UNAVAILABLE'?null:r.polling_read;const latest=read?.kind==='LATEST_POLL'?read.latest_poll:null;if(!read&&!/-ME-|-AK-/.test(r.id))return null;
 return <Panel className="race-polls" kicker="The polls">
  <ul className="race-facts">
   {read&&<li>{latest?'One published poll':`${read.poll_count} comparable polls`} · newest finished {shortDate(read.field_end)} ({read.age_days} {read.age_days===1?'day':'days'} old)</li>}
   {read&&(latest||Number(read.poll_count)<=2)&&<li className="c-flag">Thin evidence: {latest?'one published poll':Number(read.poll_count)===1?'only 1 poll':`only ${read.poll_count} polls`} behind this number.</li>}
   {/-ME-|-AK-/.test(r.id)&&<li className="c-flag">{r.id.includes('-ME-')?'Maine':'Alaska'} uses ranked-choice voting. These are first-choice numbers, and second choices can change the result.</li>}
  </ul>
 </Panel>;}

function Ledger({r}:{r:any}){const estimates=publicEstimates(r.id);
 return <Panel className="race-ledger-panel" kicker="Every poll" action={<RecallLegend/>}>
  <p className="c-sub">All non-quarantined stored variants. Principal selection and primary verification are separate from recall classification; a displayed estimate need not enter an average. Quarantined rows appear only on <a href="/excluded/">Excluded</a>.</p>
  {!estimates.length?<Empty title="No poll estimates">No eligible source records in this release.</Empty>:<table className="source-table w-full"><thead><tr><th>Pollster / field dates</th><th>D / R share</th><th>Margin</th><th>Recall</th><th>Stratum</th><th>Selection / source</th></tr></thead><tbody>{estimates.map((e:any)=><tr key={e.estimate_id}><th scope="row">{pollsterNames[e.pollster_id]||e.pollster_id}{SPONSOR_TIER_TAG[e.sponsor_tier]?<span className="party-tag">{SPONSOR_TIER_TAG[e.sponsor_tier]}</span>:null}{(e.pollster_alignment==="D"||e.pollster_alignment==="R")?<span className="party-tag">{e.pollster_alignment==="D"?"Democratic-aligned":"Republican-aligned"}</span>:null}<span className="muted block text-xs font-normal">{shortDate(e.field_start)}–{shortDate(e.field_end)}</span></th><td data-label="D / R share" className="mono">{number(e.D)} / {number(e.R)}</td><td data-label="Margin" className="mono">{margin(e.margin)}</td><td data-label="Recall" className={`recall-${e.recall_weighted.toLowerCase()}`}>{e.recall_weighted==='YES'?'▲':e.recall_weighted==='NO'?'●':'■'} {e.recall_weighted}</td><td data-label="Stratum" className="text-xs">{e.round} / {e.pop} / {e.denominator_class}<span className="muted block">{WINDOW_LABEL[e.window]||e.window}</span></td><td data-label="Selection / source" className="text-xs"><span>{e.selected==='1'?'Principal':'Alternate'} · primary {e.primary_verified}</span><a href={e.source_url} target="_blank" rel="noopener noreferrer" className="block">{pollsterNames[e.pollster_id]||e.pollster_id} release</a></td></tr>)}</tbody></table>}
 </Panel>;}

export default async function Race({params}:{params:Promise<{slug:string}>}) {const {slug}=await params;const r=races.find(r=>r.slug===slug);if(!r)notFound();
 const drawers=<>
  <details className="c-drawer"><summary>All race readings<span aria-hidden="true">+</span></summary><div className="c-drawer-body"><dl className="conditions grid gap-4 sm:grid-cols-3"><Conditions r={r}/></dl></div></details>
  
 </>;
 return <div className="race-console">
  <RaceHead r={r}/>
  {r.id.endsWith('HOUSE')&&<HouseFacts r={r}/>}
  {publicEstimates(r.id).some((e:any)=>e.window==='BOTH'||e.window==='HOUSE_ONLY')?<Panel className="race-recall" kicker="The polls">
   <div className="race-recall-grid">
    {r.trend?.length?<Both desktop={<CandidateChart estimates={publicEstimates(r.id)} trend={r.trend} name={r.name} names={{D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate}}/>} mobile={<CandidateChart compact estimates={publicEstimates(r.id)} trend={r.trend} name={r.name} names={{D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate}}/>}/>
    :<Both desktop={<DotPlot estimates={publicEstimates(r.id)} name={r.name} groups={r.recallComparison?.groups} included={r.recallComparison?.included_estimate_ids} names={{D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate}}/>} mobile={<DotPlot compact estimates={publicEstimates(r.id)} name={r.name} groups={r.recallComparison?.groups} included={r.recallComparison?.included_estimate_ids} names={{D:r.heat.candidates.D.candidate,R:r.heat.candidates.R.candidate}}/>}/>}
    <div>{r.recallComparison?<RecallComparison r={r} pollsterNames={pollsterNames}/>:<p className="c-sub">Not enough polls on both sides to compare polls that weight on recalled 2024 vote with polls that do not.</p>}</div>
   </div>
  </Panel>:<Panel className="race-recall" kicker="The polls"><p className="c-sub">No public poll since September 1. {publicEstimates(r.id).length?'Older polls are listed below as context; they enter no number.':'None found earlier this year either.'}</p></Panel>}
  <div className="race-stack"><ThePolls r={r}/><WhyPull r={r}/></div>

  <Ledger r={r}/>
  {drawers}
 </div>;}
