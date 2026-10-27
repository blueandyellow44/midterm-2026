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

function witnessText(s:any){const w=s.witness;if(!w||!Number.isFinite(w.weight_state)||w.weight_state>=1)return '';const pct=(x:number)=>`${Math.round(100*x)}%`;const st=w.state_adjustment_raw;const rel=w.agree===true?'It points the same way as this state’s polling record':w.agree===false?'It points the other way from this state’s polling record':'This state’s polling record has little to say';return ` ${rel}, so the two are weighed against each other: the state record counts ${pct(w.weight_state)} and spending ${pct(w.weight_spending)}${Number.isFinite(st)&&Math.abs(st)>=0.05?`, where the state record alone would move this race ${number(Math.abs(st))} toward ${st>0?'the Democrat':'the Republican'}`:''}.`;}

function recordText(meta:any){const o=meta?.offyear_record;return o?.largest_on_record?` Last fall’s miss in the governor races, ${number(o.miss_toward_d,1)} points, was the largest of any off-year since ${o.since}; the previous high was ${number(o.earlier_max,1)} in ${o.earlier_max_year}.`:'';}

export function signalLines(s:any,names:{D:string;R:string},meta?:any) {
 const lines:{key:string;label:string;value:number|null;text:string}[]=[];
 if(Number.isFinite(s.delta_polling_error)) lines.push({key:'polling-error',label:'Recent polling error',value:s.delta_polling_error,text:`Polls have understated Democrats in every statewide election since November 2025: ${number(meta?.rules?.poll_error_2025_miss??7.3,1)} points on average, counting each state’s electorate once and weighting low-turnout contests down.${recordText(meta)} In regular elections since 1999, about a quarter of an off-year miss has repeated the next year, which gives ${number(s.polling_error?.national,1)} points nationally, give or take ${number(meta?.rules?.poll_error_sd??1.4,1)}. ${stateLeanText(s)} ${Math.abs(s.delta_polling_error)<EVEN?'which cancels the national lean, so this race gets none.':`so we lean this race ${number(Math.abs(s.delta_polling_error))} points toward ${s.delta_polling_error>0?'the Democrat':'the Republican'}.`}`});
 const sp=s.spending; const rh=s.rhetoric; const fav=s.fundamentals?.underdog==='D'?'R':s.fundamentals?.underdog==='R'?'D':null;
 if(s.weight_spending>0 && Number.isFinite(sp?.excess_z) && fav) {
  const heavy=sp.excess_z>0;const total=(sp.d_fav_recent??0)+(sp.r_fav_recent??0);const digital=sp.coverage==='DIGITAL_CANDIDATE';const what=digital?'in campaign digital ads (Google and Meta) over about four weeks':'in outside money over two weeks';const label=digital?'Campaign ad spending':'Outside spending';
  const typical=Math.abs(sp.excess_z)<(meta?.rules?.spend_min_z??0.25);
  lines.push({key:'spending',label,value:s.delta_spending,text:(typical
   ?`${money(total)} ${what}, about what a race this close usually draws. That says this race’s miss should look like the national one.`
   :heavy
   ?`${money(total)} ${what}, more than a race this close usually draws. In a state that leans ${leanWord[fav]}, heavy money from either side reads as ${names[fav==='D'?'R':'D']} doing better than the polls show.`
   :`${money(total)} ${what}, less than a race this close usually draws. Parties pull money from races they think are decided, so this reads as ${names[Number(s.polling_margin)>0?'D':'R']}’s lead being safer than the polls show.`)+witnessText(s)});
 }
 if(s.weight_rhetoric>0 && Number.isFinite(rh?.gap)) {
  const hot=rh.gap>0?'R':'D';
  lines.push({key:'rhetoric',label:'Rhetoric',value:s.delta_rhetoric,text:`${names[hot]}’s ads and debate answers run hotter (${number(hot==='R'?rh.mean_r:rh.mean_d,1)} against ${number(hot==='R'?rh.mean_d:rh.mean_r,1)} on a 1 to 5 scale). Trailing candidates tend to attack, so this reads as ${names[hot]} behind in their own polls.${s.rhetoric_capped?' The rhetoric effect is capped.':''}`});
 }
 if(!(s.weight_spending>0) && Number.isFinite(sp?.excess_z) && Math.abs(sp.excess_z)<(meta?.rules?.spend_min_z??0.25)) {const lead=Math.abs(Number(s.polling_margin));const close=lead<(meta?.rules?.abandon_min_lead??2);const digital=sp.coverage==='DIGITAL_CANDIDATE';lines.push({key:'spending-typical',label:`${digital?'Campaign ad spending':'Outside spending'} · matches the polls`,value:0,text:`${money((sp.d_fav_recent??0)+(sp.r_fav_recent??0))} ${digital?'in campaign digital ads (Google and Meta)':'in outside money over two weeks'}, about what ${close?'a race this close':`a race with a ${number(lead,0)}-point polling lead`} usually draws. ${close?'Both sides are spending like it is a toss-up, which is what the polls say.':'Neither side is spending like the race is in play, which says their own polls agree with the public ones: the lead is real.'} It confirms the polls rather than moving them.`});}
 if(!(s.weight_spending>0) && Number.isFinite(sp?.excess_z) && sp.excess_z<=-(meta?.rules?.spend_min_z??0.25) && Math.abs(Number(s.polling_margin))<(meta?.rules?.abandon_min_lead??2)) lines.push({key:'spending-none',label:'Outside spending · no direction',value:0,text:`Less money than a race this close usually draws. That usually means one side thinks the race is decided, but the polls here are within ${number(meta?.rules?.abandon_min_lead??2,0)} points, so there is no clear leader for the money to point to.`});
 const ev=s.early_vote; const evm=meta?.early_vote_model;
 if(ev?.in_reading && Number.isFinite(s.delta_early_vote) && evm) {const sh=ev.shift_vs_2022_toward_d;lines.push({key:'early-vote',label:'Early vote',value:s.delta_early_vote,text:`${Math.abs(sh)<0.05?'Early voting is running even with':`Early voting is running ${number(Math.abs(sh),1)} points ${sh>0?'more Democratic':'more Republican'} than`} the same point in 2022, by party registration, as of ${ev.as_of}. Across states the average shift is ${number(ev.mean_shift_vs_2022,1)} points toward Democrats, so this state is running ${number(Math.abs(ev.relative_shift),1)} points ${ev.relative_shift>0?'more Democratic':'more Republican'} than the rest. In 2018 and 2022, states whose early vote moved further toward one party saw their polls miss toward that party.`});}
 return lines;
}

export function signalGaps(s:any) {
 const gaps:string[]=[];
 if(s.spending?.coverage==='NOT_FEDERAL') gaps.push('governor campaigns report spending to the state, not the FEC');
 else if(s.weight_spending===0) gaps.push(Number.isFinite(s.spending?.excess_z)?'outside spending is about what a race this close usually draws':'no usable outside-spending total');
 if(s.weight_rhetoric===0&&s.rhetoric?.in_reading!==false) gaps.push(Number.isFinite(s.rhetoric?.gap)?'the two candidates’ rhetoric runs about equally hot':'not enough scored ads or debate answers for both candidates');
 return gaps;
}

const agreement:Record<string,string>={NO_SIGNAL:'',ALIGNED:'',OPPOSED:'',SPENDING_ONLY:'Spending counts at half weight.',RHETORIC_ONLY:'',WITNESS:''};

export function SignalReading({r,meta}:{r:any;meta?:any}) {
 const s=r?.signal;
 const names={D:r?.heat?.candidates?.D?.candidate,R:r?.heat?.candidates?.R?.candidate};
 if(!s || !names.D || !names.R) return null;
 if(s.status!=='ADJUSTED' || !Number.isFinite(s.adjusted_margin)) {
  const gaps=signalGaps(s);
  return <p className="signal-none"><strong>Campaign signals:</strong> none strong enough to adjust this reading{gaps.length?` (${gaps.join('; ')})`:''}.</p>;
 }
 const a=s.adjusted_margin;const even=Math.abs(a)<EVEN;const shift=s.delta_total;const lines=signalLines(s,names,meta);
 return <section className="signal-reading" aria-label={`${r.name||'This race'}: reading adjusted for polling error, spending and early vote`}>
  <div className="signal-heading"><h4>The undertow</h4></div>
  <p className="signal-intro">The pull is how far recent polling error, outside money and early voting move this race off its polls. The ± is our margin of error, like a poll’s.</p>
  <dl className="pull-block"><div className="pull-row pull-polls"><dt>Polls</dt><dd className="mono">{marginText(Number(s.polling_margin),names)}</dd></div><div className="pull-row pull-undertow"><dt>Undertow</dt><dd className="mono"><strong className={a>0?'lead-number-d':'lead-number-r'}>{marginText(a,names)}</strong><span className="pull-pm"> ± {number(s.range_sd,1)}</span></dd></div><div className="pull-row pull-pull"><dt>The pull</dt><dd className="mono"><strong className={shift>0?'lead-number-d':'lead-number-r'}>{Math.abs(shift)<EVEN?'none':`${number(Math.abs(shift))} toward ${toward(shift,names)}`}</strong></dd></div></dl><ul className="signal-lines">{lines.map(l=><li key={l.key}><span className="signal-line-label">{l.label}</span><span className={`signal-line-value ${Number(l.value)>0?'lead-number-d':Number(l.value)<0?'lead-number-r':''}`}>{l.key==='spending-typical'?'confirms':l.key==='spending-none'?'none':Math.abs(Number(l.value))<EVEN?'0.0':`${number(Math.abs(Number(l.value)))} toward ${toward(Number(l.value),names)}`}</span><span className="signal-line-text">{l.text}</span></li>)}</ul>
  <p className="signal-limit">{agreement[s.alignment]?`${agreement[s.alignment]} `:""}Frozen November 2 and graded against the results alongside the polls.</p>
  <MethodNotes s={s} meta={meta}/>
 </section>;
}

// The per-race method notes, shared by the card and the race console.
export function MethodNotes({s,meta}:{s:any;meta?:any}) {return <details className="signal-details"><summary>How this is calculated<span aria-hidden="true">+</span></summary>
   <p>The adjustment starts from the polling read above and adds up to three terms. Recent polling error: a lean toward Democrats, sized for each state. Spending: outside money in the two weeks to {s.window_end||meta?.window_end||'the snapshot'}, compared with what a race this close usually draws, read against the state’s 2024 presidential result. Early vote: where the state reports early voters’ party registration, how far its shift since 2022 runs ahead of or behind the other states’.</p>
   {meta&&<p>{meta.witness_model?<>Spending and the state’s polling record are two witnesses to where this year’s miss lands. Each is weighted by how reliable it has been in {meta.witness_model.n} Senate races from {meta.witness_model.years?.join(' and ')}: the state record counts {Math.round(100*meta.witness_model.weight_state)}% and spending {Math.round(100*meta.witness_model.weight_spending)}%, at {number(meta.witness_model.spend_points_per_z,2)} points per standard deviation of extra money. Spending is measured against other races this year, so it places the miss; it does not size the national lean.</>:<>Spending counts {number(meta.posterior?.beta?.[0],2)} points per standard deviation of extra money.</>}{meta.early_vote_model?<> Early vote counts {number(meta.early_vote_model.slope,2)} points per point of relative shift, fit on {meta.early_vote_model.n} states in the 2018 and 2022 midterms, each against the midterm before; held out a year at a time, it cut the average miss from {number(meta.early_vote_model.holdout_mae_without,1)} to {number(meta.early_vote_model.holdout_mae_with,1)} points.</>:null} The national polling-error lean is {number(meta.rules?.poll_error_toward_d,1)} points, give or take {number(meta.rules?.poll_error_sd,1)}: in regular elections in every off-year since 1999 (specials and Louisiana primaries left out), about a quarter of that year’s polling miss repeated in the next year’s elections, and the 2025 miss was {number(meta.rules?.poll_error_2025_miss,1)} points toward Democrats. The margin of error includes both the uncertainty in that carryover share and how far a year has strayed from it in the past, along with the race-by-race error of a final polling average, about 4 points. That history is thin: in a replay of the lean on past races, results landed inside a band built this way {number(100*(meta.poll_error_model?.backtest?.coverage??0),0)}% of the time, short of the 68% a well-sized band would cover, so treat the ± as a floor. Each state then moves by {number(meta.state_lean?.slope,2)} times its own average miss against the national miss over the last {meta.state_lean?.window_years} years; here that is {s.polling_error?.state_adjustment>0?'+':''}{number(s.polling_error?.state_adjustment,1)} points across {s.polling_error?.cycles} election cycles.</p>}
   <dl className="signal-facts">
    <div><dt>2024 presidential result</dt><dd className="mono">{Number.isFinite(s.fundamentals?.pres_d_minus_r)?`${s.fundamentals.pres_d_minus_r>0?'D':'R'} +${number(Math.abs(s.fundamentals.pres_d_minus_r))}`:'NA'}</dd></div>
    <div><dt>{s.spending?.coverage==='DIGITAL_CANDIDATE'?'Campaign digital ads, ~4 weeks':'Outside money, two weeks'}</dt><dd className="mono">{money(s.spending?.d_fav_recent)} D-side · {money(s.spending?.r_fav_recent)} R-side</dd></div>
    <div><dt>Extra money vs typical</dt><dd className="mono">{Number.isFinite(s.spending?.excess_z)?`${s.spending.excess_z>0?'+':''}${number(s.spending.excess_z,2)} SD`:'NA'}</dd></div>
    {s.early_vote?.in_reading&&<div><dt>Early vote vs 2022, by registration</dt><dd className="mono">{s.early_vote.shift_vs_2022_toward_d>0?'+':''}{number(s.early_vote.shift_vs_2022_toward_d,1)} D · {s.early_vote.relative_shift>0?'+':''}{number(s.early_vote.relative_shift,1)} vs other states</dd></div>}
    <div><dt>Margin of error, one standard deviation</dt><dd className="mono">± {number(s.range_sd,1)} points: {number(s.delta_sd,1)} from our adjustments, {number(meta?.rules?.race_poll_sd??4.06,1)} from this race’s own polling error</dd></div>
   </dl>
   <p>{s.spending?.coverage==='DIGITAL_CANDIDATE'?'Governor campaigns do not report to the FEC, so this race uses each campaign’s own in-state digital ad spending on Google and Meta; TV and other ad budgets are not included.':'Outside spending is FEC independent expenditures only; campaigns’ own ad budgets and reservations are not included.'} {meta?.framing}</p>
  </details>;}
