import { number } from '@/lib/format';

// Formats the calculator's signal-adjusted reading. Every number comes from derived.json (weight.py); this file only
// rounds, picks candidate names for a sign, and writes the plain-language explanation.
const EVEN=0.05;
const leanWord:Record<string,string>={D:'Democratic',R:'Republican'};
const money=(v:number|null|undefined)=>Number.isFinite(v)?`$${((v as number)/1e6).toFixed(1)}M`:'NA';

function toward(value:number,names:{D:string;R:string}) {return value>0?names.D:names.R;}
export function marginText(m:number,names:{D:string;R:string}){if(!Number.isFinite(m))return 'NA';if(Math.abs(m)<EVEN)return 'Even';return `${m>0?names.D:names.R} +${number(Math.abs(m))}`;}
export function rangeLead(s:any,names:{D:string;R:string}){const r=s.range;if(!Array.isArray(r)||!r.every((v:any)=>Number.isFinite(v)))return null;const[lo,hi]=r as number[];if(lo>0)return <>{names.D}<span className="reading-lead-verb"> ahead by </span><strong className="lead-number-d">{number(lo)} to {number(hi)}<small> points</small></strong></>;if(hi<0)return <>{names.R}<span className="reading-lead-verb"> ahead by </span><strong className="lead-number-r">{number(-hi)} to {number(-lo)}<small> points</small></strong></>;return <>Too close to call<span className="reading-lead-verb">: </span><strong>{names.R} +{number(-lo)} to {names.D} +{number(hi)}</strong></>;}
export function stateLeanText(s:any){const a=Number(s.polling_error?.state_adjustment);if(!Number.isFinite(a)||!s.polling_error?.cycles)return 'This state has too little polling history to adjust,';if(a>=EVEN)return 'Polls here have run more Republican than the national pattern,';if(a<=-EVEN)return 'Polls here have overstated Democrats more than the national pattern,';return 'Polls here track the national pattern,';}

export function signalLines(s:any,names:{D:string;R:string},meta?:any) {
 const lines:{key:string;label:string;value:number|null;text:string}[]=[];
 if(Number.isFinite(s.delta_polling_error)&&Math.abs(s.delta_polling_error)>=EVEN) lines.push({key:'polling-error',label:'Recent polling error',value:s.delta_polling_error,text:`Polls have understated Democrats in every statewide race since November 2025, by ${number(meta?.rules?.poll_error_2025_miss??7.5,1)} points in last fall’s governor races. About a third of an off-year miss has repeated the next year, which gives ${number(s.polling_error?.national,1)} points nationally, give or take ${number(meta?.rules?.poll_error_sd??1.8,1)}. This lean is the site’s main bet. ${stateLeanText(s)} so we lean this race ${number(Math.abs(s.delta_polling_error))} points toward the Democrat.`});
 const sp=s.spending; const rh=s.rhetoric; const fav=s.fundamentals?.underdog==='D'?'R':s.fundamentals?.underdog==='R'?'D':null;
 if(s.weight_spending>0 && Number.isFinite(sp?.excess_z) && fav) {
  const heavy=sp.excess_z>0;const total=(sp.d_fav_recent??0)+(sp.r_fav_recent??0);const digital=sp.coverage==='DIGITAL_CANDIDATE';const what=digital?'in campaign digital ads (Google and Meta) over about four weeks':'in outside money over two weeks';const label=digital?'Campaign ad spending':'Outside spending';
  lines.push({key:'spending',label,value:s.delta_spending,text:heavy
   ?`${money(total)} ${what}, more than a race this close usually draws. In a state that leans ${leanWord[fav]}, heavy money from either side reads as ${names[fav==='D'?'R':'D']} doing better than the polls show.`
   :`${money(total)} ${what}, less than a race this close usually draws. Parties pull money from races they think are decided, so this reads as ${names[Number(s.polling_margin)>0?'D':'R']}’s lead being safer than the polls show.`});
 }
 if(s.weight_rhetoric>0 && Number.isFinite(rh?.gap)) {
  const hot=rh.gap>0?'R':'D';
  lines.push({key:'rhetoric',label:'Rhetoric',value:s.delta_rhetoric,text:`${names[hot]}’s ads and debate answers run hotter (${number(hot==='R'?rh.mean_r:rh.mean_d,1)} against ${number(hot==='R'?rh.mean_d:rh.mean_r,1)} on a 1 to 5 scale). Trailing candidates tend to attack, so this reads as ${names[hot]} behind in their own polls.${s.rhetoric_capped?' The rhetoric effect is capped.':''}`});
 }
 if(!(s.weight_spending>0) && Number.isFinite(sp?.excess_z) && sp.excess_z<0 && Math.abs(Number(s.polling_margin))<(meta?.rules?.abandon_min_lead??2)) lines.push({key:'spending-none',label:'Outside spending · no direction',value:0,text:`Less money than a race this close usually draws. That usually means one side thinks the race is decided, but the polls here are within ${number(meta?.rules?.abandon_min_lead??2,0)} points, so there is no clear leader for the money to point to.`});
 if(rh?.in_reading===false && Number.isFinite(rh?.gap) && Math.abs(rh.gap)>=0.1) {const hot=rh.gap>0?'R':'D';lines.push({key:'rhetoric-test',label:'Rhetoric · tested, not counted',value:0,text:`${names[hot]}’s ads and debate answers run hotter (${number(hot==='R'?rh.mean_r:rh.mean_d,1)} against ${number(hot==='R'?rh.mean_d:rh.mean_r,1)} on a 1 to 5 scale). We think hotter rhetoric means a campaign is behind in its own polls, but there is no record to prove it yet, so it does not move this reading. It is graded after the election.`});}
 const ev=s.early_vote; if(ev && Number.isFinite(ev.shift_vs_2022_toward_d)) {const sh=ev.shift_vs_2022_toward_d;const basis=ev.party_basis==='registration'?'by party registration':'by modeled party';lines.push({key:'early-vote',label:'Early vote · tested, not counted',value:0,text:`${Math.abs(sh)<0.05?'Early voting is running even with':`Early voting is running ${number(Math.abs(sh),1)} points ${sh>0?'more Democratic':'more Republican'} than`} the same point in 2022, ${basis}, as of ${ev.as_of}. A turnout surge can beat the polls, but when we tested early vote in North Carolina from 2010 to 2024 it matched the direction of the polling miss in only 2 of 6 elections, so it does not move this reading. It is frozen November 2 and graded after the election.`});}
 return lines;
}

export function signalGaps(s:any) {
 const gaps:string[]=[];
 if(s.spending?.coverage==='NOT_FEDERAL') gaps.push('governor campaigns report spending to the state, not the FEC');
 else if(s.weight_spending===0) gaps.push(Number.isFinite(s.spending?.excess_z)?'outside spending is about what a race this close usually draws':'no usable outside-spending total');
 if(s.weight_rhetoric===0&&s.rhetoric?.in_reading!==false) gaps.push(Number.isFinite(s.rhetoric?.gap)?'the two candidates’ rhetoric runs about equally hot':'not enough scored ads or debate answers for both candidates');
 return gaps;
}

const agreement:Record<string,string>={NO_SIGNAL:'No campaign signal is strong enough here, so only the polling-error lean applies.',ALIGNED:'Spending and rhetoric point the same way, so both count in full.',OPPOSED:'Spending and rhetoric point in opposite directions, so each counts at one quarter.',SPENDING_ONLY:'Spending counts at half weight, because its track record is thin and nothing else confirms it.',RHETORIC_ONLY:'Only rhetoric gives a signal here, so it counts at half.'};

export function SignalReading({r,meta}:{r:any;meta?:any}) {
 const s=r?.signal;
 const names={D:r?.heat?.candidates?.D?.candidate,R:r?.heat?.candidates?.R?.candidate};
 if(!s || !names.D || !names.R) return null;
 if(s.status!=='ADJUSTED' || !Number.isFinite(s.adjusted_margin)) {
  const gaps=signalGaps(s);
  return <p className="signal-none"><strong>Campaign signals:</strong> none strong enough to adjust this reading{gaps.length?` (${gaps.join('; ')})`:''}.</p>;
 }
 const a=s.adjusted_margin;const even=Math.abs(a)<EVEN;const shift=s.delta_total;const lines=signalLines(s,names,meta);
 return <section className="signal-reading" aria-label={`${r.name||'This race'}: reading adjusted for campaign spending and rhetoric`}>
  <div className="signal-heading"><h4>The undertow</h4><span className="signal-chip">Experimental</span></div>
  <p className="signal-intro">The pull is how far recent polling error and outside money move this race off its polls. The ± is our margin of error, like a poll’s.</p>
  <dl className="pull-block"><div className="pull-row pull-polls"><dt>Polls</dt><dd className="mono">{marginText(Number(s.polling_margin),names)}</dd></div><div className="pull-row pull-undertow"><dt>Undertow</dt><dd className="mono"><strong className={a>0?'lead-number-d':'lead-number-r'}>{marginText(a,names)}</strong><span className="pull-pm"> ± {number(s.range_sd,1)}</span></dd></div><div className="pull-row pull-pull"><dt>The pull</dt><dd className="mono"><strong className={shift>0?'lead-number-d':'lead-number-r'}>{Math.abs(shift)<EVEN?'none':`${number(Math.abs(shift))} toward ${toward(shift,names)}`}</strong></dd></div></dl><ul className="signal-lines">{lines.map(l=><li key={l.key}><span className="signal-line-label">{l.label}</span><span className={`signal-line-value ${Number(l.value)>0?'lead-number-d':Number(l.value)<0?'lead-number-r':''}`}>{l.key==='rhetoric-test'||l.key==='early-vote'?'not counted':l.key==='spending-none'?'none':Math.abs(Number(l.value))<EVEN?'0.0':`${number(Math.abs(Number(l.value)))} toward ${toward(Number(l.value),names)}`}</span><span className="signal-line-text">{l.text}</span></li>)}</ul>
  <p className="signal-limit">{agreement[s.alignment]} Graded against the results alongside the polls.</p>{meta?.poll_error_model?.backtest&&<p className="signal-record"><strong>The record so far.</strong> Applied to {meta.poll_error_model.backtest.races} past Senate and governor races from {meta.poll_error_model.backtest.from} to 2024, this lean did not beat the polls: an average miss of {number(meta.poll_error_model.backtest.mae_with_lean,1)} points against {number(meta.poll_error_model.backtest.mae_polls,1)}.{meta?.spending_backtest?` Spending did not either, in ${meta.spending_backtest.races} past Senate races.`:''} The bet is that 2026 is different: last fall’s {number(meta.poll_error_model.offyear_miss_toward_d,1)}-point miss is the largest off-year miss in the archive, which goes back to 1999.</p>}
  <details className="signal-details"><summary>How this is calculated<span aria-hidden="true">+</span></summary>
   <p>The adjustment starts from the polling read above and adds two terms. Recent polling error: a lean toward Democrats, sized for each state. Spending: outside money in the two weeks to {s.window_end||meta?.window_end||'the snapshot'}, compared with what a race this close usually draws, read against the state’s 2024 presidential result. Rhetoric is scored but not counted: it has no track record yet, so it is frozen on November 2 and graded on its own.</p>
   {meta&&<p>Spending counts {number(meta.posterior?.beta?.[0],2)} points per standard deviation of extra money, a starting assumption of {number(meta.priors?.beta?.[0],1)} updated with {meta.history?.n} Senate races from {meta.history?.years?.join(' and ')}. Rhetoric counts {number(meta.posterior?.gamma?.[0],2)} points per point of heat gap, a starting assumption with no history behind it, capped at {number(meta.rules?.rhetoric_cap,1)} points. The national polling-error lean is {number(meta.rules?.poll_error_toward_d,1)} points, give or take {number(meta.rules?.poll_error_sd,1)}: in every off-year since 1999, about a third of that year’s polling miss repeated in the next year’s elections, and the 2025 miss was {number(meta.rules?.poll_error_2025_miss,1)} points toward Democrats. That history is thin, so the range above includes this uncertainty, along with the race-by-race error of a final polling average, about 4 points once the year’s shared miss is set aside. The true result should land inside the range about two times in three. Each state then moves by {number(meta.state_lean?.slope,2)} times its own average miss against the national miss over the last {meta.state_lean?.window_years} years; here that is {s.polling_error?.state_adjustment>0?'+':''}{number(s.polling_error?.state_adjustment,1)} points across {s.polling_error?.cycles} election cycles.</p>}
   <dl className="signal-facts">
    <div><dt>2024 presidential result</dt><dd className="mono">{Number.isFinite(s.fundamentals?.pres_d_minus_r)?`${s.fundamentals.pres_d_minus_r>0?'D':'R'} +${number(Math.abs(s.fundamentals.pres_d_minus_r))}`:'NA'}</dd></div>
    <div><dt>{s.spending?.coverage==='DIGITAL_CANDIDATE'?'Campaign digital ads, ~4 weeks':'Outside money, two weeks'}</dt><dd className="mono">{money(s.spending?.d_fav_recent)} D-side · {money(s.spending?.r_fav_recent)} R-side</dd></div>
    <div><dt>Extra money vs typical</dt><dd className="mono">{Number.isFinite(s.spending?.excess_z)?`${s.spending.excess_z>0?'+':''}${number(s.spending.excess_z,2)} SD`:'NA'}</dd></div>
    <div><dt>Heat, D / R</dt><dd className="mono">{number(s.rhetoric?.mean_d,2)} ({s.rhetoric?.n_d}) / {number(s.rhetoric?.mean_r,2)} ({s.rhetoric?.n_r})</dd></div>
    <div><dt>Range, about two in three chance</dt><dd className="mono">± {number(s.range_sd,1)} points: {number(s.delta_sd,1)} from our adjustments, {number(meta?.rules?.race_poll_sd??4.06,1)} from this race’s own polling error</dd></div>
   </dl>
   <p>Outside spending is FEC independent expenditures only; campaigns’ own ad budgets and reservations are not included. Heat scores hyperbole, which stands in for attack rhetoric. {meta?.framing}</p>
  </details>
 </section>;
}
