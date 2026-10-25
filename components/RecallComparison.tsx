import { number,shortDate } from '@/lib/format';

const labels={YES:'Uses 2024 vote',NO:'Does not use it'};
const populations:Record<string,string>={LV:'likely voters',RV:'registered voters',A:'adults'};
const ballots:Record<string,string>={FULL:'full ballot',LEANERS:'undecided leaners included',TWO_WAY:'two-candidate choice'};

export function RecallComparison({r,pollsterNames={}}:{r:any;pollsterNames?:Record<string,string>}) {
 const comparison=r?.recallComparison;
 const groups=comparison?.groups;
 if(!groups || !Number.isFinite(comparison.value) || ['YES','NO'].some(key=>!Number.isFinite(groups[key]?.mean)||!Number.isInteger(groups[key]?.estimates)||!(groups[key]?.estimates>0)||!Number.isInteger(groups[key]?.pollsters)||!(groups[key]?.pollsters>0))) return null;
 const sourceRows=Array.isArray(r.recallSources)?r.recallSources:[];
 const candidates=r.heat?.candidates;
 if(!candidates?.D?.candidate || !candidates?.R?.candidate) return null;
 const gap=comparison.value;
 const unknown=r.recall_counts_principal_both?.UNVERIFIED;
 return <section className="recall-comparison" aria-label={`${r.name||'This race'}: how pollsters use the 2024 vote`}>
  <h4>How pollsters use the 2024 vote</h4>
  <p className="recall-intro">Some polls adjust their sample using how people say they voted in 2024. Here is how the two groups compare.</p>
  <dl className="recall-groups">{(['YES','NO'] as const).map(key=>{
   const group=groups[key];const value=group.mean;const even=Math.abs(value)<0.05;
   const candidate=value>0?candidates.D.candidate:candidates.R.candidate;
   return <div className="recall-group" key={key}>
    <dt>{labels[key]}</dt>
    <dd className={`recall-group-margin ${even?'':value>0?'lead-number-d':'lead-number-r'}`}>{even?'Even':<>{number(Math.abs(value))}<small> point lead</small></>}</dd>
    <dd className="recall-group-candidate">{even?'At displayed precision':`for ${candidate}`}</dd>
    <dd className="recall-group-count">{group.estimates} {group.estimates===1?'poll':'polls'} · {group.pollsters} {group.pollsters===1?'pollster':'pollsters'}</dd>
   </div>;
  })}</dl>
  <p className="recall-gap">{Math.abs(gap)<0.05?'The groups are even at displayed precision.':<>Polls using 2024 votes read <strong>{number(Math.abs(gap))} points more favorably for {gap>0?candidates.D.candidate:candidates.R.candidate}.</strong></>}</p>
  <p className="recall-limit">Different pollsters and dates may explain this gap. It does not establish which method is better.</p>
  <details className="recall-sources"><summary>Poll dates, sources and comparison details<span aria-hidden="true">+</span></summary>
   <p>“Uses 2024 vote” means reported past votes help determine how much weight respondents receive. “Does not use it” requires documented non-use. Unknown methods are left out.</p>
   <p>These are different polls, not the same poll recalculated. Each pollster counts equally within its group; multiple polls from one firm are averaged first. These group readings use a different inclusion rule from the headline weighted average.</p>
   <p>Compared: {populations[comparison.stratum?.pop]||comparison.stratum?.pop} · {ballots[comparison.stratum?.denominator_class]||comparison.stratum?.denominator_class}{comparison.stratum?.round&&comparison.stratum.round!=='NA'?` · ${comparison.stratum?.round.toLowerCase()} round`:''}. Dates are not matched.</p>
   {typeof unknown==='number'&&<p>Across this race, {unknown} {unknown===1?'poll has':'polls have'} unverified recall weighting and {unknown===1?'is':'are'} excluded from this comparison. Other voter groups and ballot formats are also excluded.</p>}
   {(['YES','NO'] as const).map(key=><div className="recall-source-group" key={key}><h5>{labels[key]}</h5><ul>{sourceRows.filter((e:any)=>e.recall_weighted===key).map((e:any)=><li key={e.estimate_id}><a href={e.source_url} target="_blank" rel="noopener noreferrer">{pollsterNames[e.pollster_id]||e.pollster_id}<span aria-hidden="true"> ↗</span></a><span>{shortDate(e.field_start)}–{shortDate(e.field_end)} · {e.primary_verified==='YES'?'Primary verified':'Unverified'}</span></li>)}</ul></div>)}
   <p>{r.recallFraming}</p>
  </details>
 </section>;
}
