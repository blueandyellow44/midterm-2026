import { Empty, RecallLegend } from './UI';
import { number, margin, shortDate } from '@/lib/format';
type Estimate={estimate_id:string; margin:number; D?:number; R?:number; chart_d?:number; chart_r?:number; field_start:string;field_end:string;field_midpoint:number;recall_weighted:string;pollster_id:string;round:string;pop:string;denominator_class:string;primary_verified:string;flags:{principal:boolean}};
type Groups={YES?:{mean:number};NO?:{mean:number}};
const lead=(v:number,names?:{D:string;R:string})=>Math.abs(v)<0.05?'Even':names?`${(v>0?names.D:names.R).trim().split(/\s+/).pop()} +${Math.abs(v).toFixed(1)}`:margin(v);
// Poll margins by field midpoint, marked by whether each poll weights on recalled 2024 vote, with each group's average as a
// labeled line (Max, 2026-10-27: "Anyway to make the recall graph easier to read? Maybe more prominent"). Group averages
// are calculator outputs (section5 contrast groups); this component only draws them.
export function DotPlot({estimates,name,groups,names,included,compact}:{estimates:Estimate[];name:string;groups?:Groups;names?:{D:string;R:string};included?:string[];compact?:boolean}) {
 const points=estimates.filter(e=>e.flags.principal&&e.primary_verified==='YES'&&Number.isFinite(e.margin));
 if (!points.length) return <Empty title="No verified principal estimates">The source ledger remains below. No dots are inferred from unverified releases.</Empty>;
 // Domains and coordinate transforms only. Margins and midpoints are calculator outputs.
 const start=240,end=305;
 // Zoom to the data (always keeping Even in view) so the gap between the groups is readable.
 const hi=Math.ceil((Math.max(0,...points.map(p=>p.margin))+2)/5)*5, lo=Math.floor((Math.min(0,...points.map(p=>p.margin))-2)/5)*5;
 const inc=new Set(included||[]);const inGroup=(p:Estimate)=>!included||inc.has(p.estimate_id);
 // Phones get their own geometry: drawn at phone size so text stays legible; line labels move into the key.
 const W=compact?380:900,H=compact?300:370,L=compact?52:70,R=compact?366:640,T=compact?14:24,B=compact?262:330;
 const x=(v:number)=>L+(v-start)/(end-start)*(R-L);const y=(v:number)=>T+(hi-v)/(hi-lo)*(B-T);
 const ticks=Array.from({length:Math.round((hi-lo)/5)+1},(_,i)=>lo+5*i).filter(t=>(hi-lo)<=30||t%10===0);
 const lines=(['YES','NO'] as const).filter(k=>Number.isFinite(groups?.[k]?.mean)).map(k=>{const own=points.filter(p=>inc.has(p.estimate_id)&&p.recall_weighted===k).map(p=>p.field_midpoint);return {k,v:groups![k]!.mean,x1:own.length?x(Math.min(...own))-10:L,x2:own.length?x(Math.max(...own))+10:R};});
 // keep the two line labels from colliding
 const ly=lines.map(l=>y(l.v));if(ly.length===2&&Math.abs(ly[0]-ly[1])<34){const mid=(ly[0]+ly[1])/2;const up=ly[0]<=ly[1]?0:1;ly[up]=mid-17;ly[1-up]=mid+17;}
 return <figure className="recall-chart">
<svg className={`dotplot w-full${compact?' is-compact':''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${name}: verified principal poll margins by field midpoint, marked by recalled 2024 vote weighting. D minus R in percentage points. Exact values are listed in the source ledger.`}>
<title>{`${name} poll margins`}</title>
<desc>Navy triangles weight on recalled 2024 vote (YES), amber circles do not (NO), gray squares are unverified. Dashed lines are each group's average.</desc>{ticks.map(t=>
<g key={t}><line x1={L} x2={R} y1={y(t)} y2={y(t)} className={t===0?'axis-zero':'gridline'}/><text x={L-12} y={y(t)+5} textAnchor="end">{t===0?'Even':`${t>0?'D':'R'} +${Math.abs(t)}`}</text></g>)}
{[[243,'Sep 1'],[273,'Oct 1'],[297,'Oct 25']].map(([v,label])=><text key={v} x={x(Number(v))} y={H-12} textAnchor="middle">{label}</text>)}
{lines.map((l,i)=><g key={l.k} className={`recall-line recall-${l.k.toLowerCase()}`}><line x1={l.x1} x2={l.x2} y1={y(l.v)} y2={y(l.v)}/>{!compact&&<><path d={`M ${l.x2} ${y(l.v)} L ${R+14} ${ly[i]}`} className="recall-leader"/><text x={R+20} y={ly[i]-3} className="recall-line-label">{l.k==='YES'?'Uses 2024 vote':'Does not'}</text><text x={R+20} y={ly[i]+16} className="recall-line-value">{lead(l.v,names)}</text></>}</g>)}
{points.map(p=><g key={p.estimate_id} className={`recall-${p.recall_weighted.toLowerCase()}${inGroup(p)?'':' is-context'}`}>
<title>{`${p.pollster_id}: ${margin(p.margin)}, ${shortDate(p.field_start)}–${shortDate(p.field_end)}; recall ${p.recall_weighted}; ${p.round}/${p.pop}/${p.denominator_class}`}</title>{p.recall_weighted==='YES'?<path d={`M ${x(p.field_midpoint)} ${y(p.margin)-8} l 8 14 h -16 Z`}/>:p.recall_weighted==='NO'?<circle cx={x(p.field_midpoint)} cy={y(p.margin)} r="7"/>:<rect x={x(p.field_midpoint)-6} y={y(p.margin)-6} width="12" height="12"/>}</g>)}</svg>
<p className="recall-chart-key" aria-hidden="true"><span className="recall-yes">▲ Uses 2024 vote{compact&&lines.find(l=>l.k==='YES')?` · avg ${lead(lines.find(l=>l.k==='YES')!.v,names)}`:''}</span><span className="recall-no">● Does not{compact&&lines.find(l=>l.k==='NO')?` · avg ${lead(lines.find(l=>l.k==='NO')!.v,names)}`:''}</span><span className="recall-unverified">■ Unverified</span>{lines.length?<span className="muted">dashed lines: each group’s average, over the bold polls it uses; faded polls are outside the comparison</span>:<span className="muted">Too few polls on one side to draw group averages in this race.</span>}</p>
</figure>;
}

type TrendPoint={date:string;d:number;r:number;margin:number;polls:number};
const doy=(iso:string)=>{const d=new Date(iso+'T12:00:00Z');return Math.round((d.getTime()-Date.UTC(d.getUTCFullYear(),0,0))/86400000);};
// The candidate chart (Max, 2026-10-27: "Where are the lines that show the candidates in the graph?"): one line per
// candidate from the calculator's weekly polling average (derived races[].trend, ending at the published number), with each
// poll's reported shares as dots. Marker shape keeps the recall method; hollow marks are polls reporting only the two
// candidates, whose shares run higher than full-ballot polls.
export function CandidateChart({estimates,trend,name,names,compact}:{estimates:Estimate[];trend:TrendPoint[];name:string;names:{D:string;R:string};compact?:boolean}) {
 const points=estimates.filter(e=>e.flags.principal&&e.primary_verified==='YES'&&Number.isFinite(e.D)&&Number.isFinite(e.R));
 if(!trend?.length) return <Empty title="No polling average yet">The polls behind this race are listed below.</Empty>;
 const W=compact?380:900,H=compact?300:380,L=compact?40:52,R=compact?300:720,T=16,B=compact?262:338;
 const start=240,end=305;
 const cd=(p:Estimate)=>Number.isFinite(p.chart_d)?p.chart_d as number:p.D as number, cr=(p:Estimate)=>Number.isFinite(p.chart_r)?p.chart_r as number:p.R as number;
 const vals=[...points.flatMap(p=>[cd(p),cr(p)]),...trend.flatMap(t=>[t.d,t.r])];
 const hi=Math.ceil((Math.max(...vals)+2)/5)*5, lo=Math.floor((Math.min(...vals)-2)/5)*5;
 const x=(v:number)=>L+(Math.max(start,Math.min(end,v))-start)/(end-start)*(R-L);const y=(v:number)=>T+(hi-v)/(hi-lo)*(B-T);
 const ticks=Array.from({length:Math.round((hi-lo)/5)+1},(_,i)=>lo+5*i).filter(t=>(hi-lo)<=30||t%10===0);
 const path=(k:'d'|'r')=>trend.map((t,i)=>`${i?'L':'M'} ${x(doy(t.date)).toFixed(1)} ${y(t[k]).toFixed(1)}`).join(' ');
 const last=trend[trend.length-1];const sur=(n:string)=>n.trim().split(/\s+/).pop();
 let yd=y(last.d), yr=y(last.r); if(Math.abs(yd-yr)<34){const mid=(yd+yr)/2;if(yd<=yr){yd=mid-17;yr=mid+17;}else{yd=mid+17;yr=mid-17;}}
 const mark=(p:Estimate,v:number,cls:string)=>{const cx=x(p.field_midpoint),cy=y(v),o=p.denominator_class==='TWO_WAY'?' is-hollow':'';
  return p.recall_weighted==='YES'?<path className={cls+o} d={`M ${cx} ${cy-7} l 7 12 h -14 Z`}/>:p.recall_weighted==='NO'?<circle className={cls+o} cx={cx} cy={cy} r="6"/>:<rect className={cls+o} x={cx-5} y={cy-5} width="10" height="10"/>;};
 return <figure className="cand-chart">
<svg className={`dotplot w-full${compact?' is-compact':''}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${name}: each candidate's polling average by week, with every verified poll's reported shares. Exact values are listed in the poll table.`}>
<title>{`${name} candidate polling`}</title>
<desc>{`Blue: ${names.D}. Red: ${names.R}. Lines are the weekly polling average ending at the published number; dots are individual polls.`}</desc>
{ticks.map(t=><g key={t}><line x1={L} x2={R} y1={y(t)} y2={y(t)} className="gridline"/><text x={L-10} y={y(t)+5} textAnchor="end">{t}%</text></g>)}
{[[243,'Sep 1'],[273,'Oct 1'],[297,'Oct 25']].map(([v,label])=><text key={v} x={x(Number(v))} y={H-12} textAnchor="middle">{label}</text>)}
{points.map(p=><g key={p.estimate_id}><title>{`${p.pollster_id}: ${sur(names.D)} ${p.D}, ${sur(names.R)} ${p.R}${Number.isFinite(p.chart_d)?' (two-candidate poll, drawn on the full-ballot scale)':''}, ${shortDate(p.field_start)}–${shortDate(p.field_end)}; recall ${p.recall_weighted}; ${p.denominator_class}`}</title>{mark(p,cd(p),'cand-d')}{mark(p,cr(p),'cand-r')}</g>)}
<path d={path('d')} className="cand-line cand-line-d"/><path d={path('r')} className="cand-line cand-line-r"/>
{!compact&&<><text x={R+14} y={yd-2} className="cand-label cand-d">{sur(names.D)}</text><text x={R+14} y={yd+22} className="cand-value cand-d">{last.d.toFixed(1)}</text>
<text x={R+14} y={yr-2} className="cand-label cand-r">{sur(names.R)}</text><text x={R+14} y={yr+22} className="cand-value cand-r">{last.r.toFixed(1)}</text></>}
</svg>
<p className="recall-chart-key" aria-hidden="true"><><span className="cand-d">— {sur(names.D)}{compact?` ${last.d.toFixed(1)}`:''}</span><span className="cand-r">— {sur(names.R)}{compact?` ${last.r.toFixed(1)}`:''}</span><span className="muted">lines: weekly average</span></><span>▲ weights on 2024 vote</span><span>● does not</span><span>■ unverified</span><span className="cand-hollow-key"><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5"/></svg> two-candidate poll, on the full-ballot scale</span></p>
</figure>;
}
