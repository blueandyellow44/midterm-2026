import { number } from '@/lib/format';

// Formats the calculator's signal-adjusted reading. Every number comes from derived.json (weight.py); this file only
// rounds, picks candidate names for a sign, and writes the plain-language explanation.
const EVEN=0.05;
const leanWord:Record<string,string>={D:'Democratic',R:'Republican'};
const money=(v:number|null|undefined)=>Number.isFinite(v)?`$${((v as number)/1e6).toFixed(1)}M`:'NA';

function toward(value:number,names:{D:string;R:string}) {return value>0?names.D:names.R;}

export function signalLines(s:any,names:{D:string;R:string}) {
 const lines:{key:string;label:string;value:number|null;text:string}[]=[];
 const sp=s.spending; const rh=s.rhetoric; const fav=s.fundamentals?.underdog==='D'?'R':s.fundamentals?.underdog==='R'?'D':null;
 if(s.weight_spending>0 && Number.isFinite(sp?.excess_z) && fav) {
  const heavy=sp.excess_z>0;const total=(sp.d_fav_recent??0)+(sp.r_fav_recent??0);
  lines.push({key:'spending',label:'Outside spending',value:s.delta_spending,text:heavy
   ?`${money(total)} in outside money over two weeks, more than a race this close usually draws. In a state that leans ${leanWord[fav]}, heavy money from either side reads as ${names[fav==='D'?'R':'D']} doing better than the polls show.`
   :`${money(total)} in outside money over two weeks, less than a race this close usually draws. Parties pull money from races they think are decided, so this reads as ${names[Number(s.polling_margin)>0?'D':'R']}’s lead being safer than the polls show.`});
 }
 if(s.weight_rhetoric>0 && Number.isFinite(rh?.gap)) {
  const hot=rh.gap>0?'R':'D';
  lines.push({key:'rhetoric',label:'Rhetoric',value:s.delta_rhetoric,text:`${names[hot]}’s ads and debate answers run hotter (${number(hot==='R'?rh.mean_r:rh.mean_d,1)} against ${number(hot==='R'?rh.mean_d:rh.mean_r,1)} on a 1 to 5 scale). Trailing candidates tend to attack, so this reads as ${names[hot]} behind in their own polls.${s.rhetoric_capped?' The rhetoric effect is capped.':''}`});
 }
 return lines;
}

export function signalGaps(s:any) {
 const gaps:string[]=[];
 if(s.spending?.coverage==='NOT_FEDERAL') gaps.push('governor campaigns report spending to the state, not the FEC');
 else if(s.weight_spending===0) gaps.push(Number.isFinite(s.spending?.excess_z)?'outside spending is about what a race this close usually draws':'no usable outside-spending total');
 if(s.weight_rhetoric===0) gaps.push(Number.isFinite(s.rhetoric?.gap)?'the two candidates’ rhetoric runs about equally hot':'not enough scored ads or debate answers for both candidates');
 return gaps;
}

const agreement:Record<string,string>={ALIGNED:'Spending and rhetoric point the same way, so both count in full.',OPPOSED:'Spending and rhetoric point in opposite directions, so each counts at one quarter.',SPENDING_ONLY:'Only spending gives a signal here, so it counts at half.',RHETORIC_ONLY:'Only rhetoric gives a signal here, so it counts at half.'};

export function SignalReading({r,meta}:{r:any;meta?:any}) {
 const s=r?.signal;
 const names={D:r?.heat?.candidates?.D?.candidate,R:r?.heat?.candidates?.R?.candidate};
 if(!s || !names.D || !names.R) return null;
 if(s.status!=='ADJUSTED' || !Number.isFinite(s.adjusted_margin)) {
  const gaps=signalGaps(s);
  return <p className="signal-none"><strong>Campaign signals:</strong> none strong enough to adjust this reading{gaps.length?` (${gaps.join('; ')})`:''}.</p>;
 }
 const a=s.adjusted_margin;const even=Math.abs(a)<EVEN;const shift=s.delta_total;const lines=signalLines(s,names);
 return <section className="signal-reading" aria-label={`${r.name||'This race'}: reading adjusted for campaign spending and rhetoric`}>
  <div className="signal-heading"><h4>Reading the campaigns</h4><span className="signal-chip">Experimental</span></div>
  <p className="signal-intro">Polls plus what the campaigns are doing: where outside money goes and how hot the rhetoric runs.</p>
  <p className="signal-lead">{even?'Even at displayed precision':<>{toward(a,names)}<span className="reading-lead-verb"> leads by </span><strong className={a>0?'lead-number-d':'lead-number-r'}>{number(Math.abs(a))}<small> points</small></strong></>}</p>
  <p className="signal-shift">{Math.abs(shift)<EVEN?'About the same as the polls.':<>{number(Math.abs(shift))} points toward {toward(shift,names)} compared with the polls.</>}</p>
  <ul className="signal-lines">{lines.map(l=><li key={l.key}><span className="signal-line-label">{l.label}</span><span className={`signal-line-value ${Number(l.value)>0?'lead-number-d':Number(l.value)<0?'lead-number-r':''}`}>{Math.abs(Number(l.value))<EVEN?'0.0':`${number(Math.abs(Number(l.value)))} toward ${toward(Number(l.value),names)}`}</span><span className="signal-line-text">{l.text}</span></li>)}</ul>
  <p className="signal-limit">{agreement[s.alignment]} History shows only a weak link between these signals and polling misses, so this reading may miss by more than the polls. Both are graded against the results.</p>
  <details className="signal-details"><summary>How this is calculated<span aria-hidden="true">+</span></summary>
   <p>The adjustment starts from the polling read above and adds two terms. Spending: outside money in the two weeks to {s.window_end||meta?.window_end||'the snapshot'}, compared with what a race this close usually draws, read against the state’s 2024 presidential result. Rhetoric: the average LITMUS heat score of each side’s scored ads and debate answers.</p>
   {meta&&<p>Spending counts {number(meta.posterior?.beta?.[0],2)} points per standard deviation of extra money, a starting assumption of {number(meta.priors?.beta?.[0],1)} updated with {meta.history?.n} Senate races from {meta.history?.years?.join(' and ')}. Rhetoric counts {number(meta.posterior?.gamma?.[0],1)} points per point of heat gap, a starting assumption with no history behind it, capped at {number(meta.rules?.rhetoric_cap,0)} points.</p>}
   <dl className="signal-facts">
    <div><dt>2024 presidential result</dt><dd className="mono">{Number.isFinite(s.fundamentals?.pres_d_minus_r)?`${s.fundamentals.pres_d_minus_r>0?'D':'R'} +${number(Math.abs(s.fundamentals.pres_d_minus_r))}`:'NA'}</dd></div>
    <div><dt>Outside money, two weeks</dt><dd className="mono">{money(s.spending?.d_fav_recent)} D-side · {money(s.spending?.r_fav_recent)} R-side</dd></div>
    <div><dt>Extra money vs typical</dt><dd className="mono">{Number.isFinite(s.spending?.excess_z)?`${s.spending.excess_z>0?'+':''}${number(s.spending.excess_z,2)} SD`:'NA'}</dd></div>
    <div><dt>Heat, D / R</dt><dd className="mono">{number(s.rhetoric?.mean_d,2)} ({s.rhetoric?.n_d}) / {number(s.rhetoric?.mean_r,2)} ({s.rhetoric?.n_r})</dd></div>
    <div><dt>Uncertainty from the assumptions</dt><dd className="mono">± {number(s.delta_sd,1)} points</dd></div>
   </dl>
   <p>Outside spending is FEC independent expenditures only; campaigns’ own ad budgets and reservations are not included. Heat scores hyperbole, which stands in for attack rhetoric. {meta?.framing}</p>
  </details>
 </section>;
}
