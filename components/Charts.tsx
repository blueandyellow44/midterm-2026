import { Empty, RecallLegend } from './UI';
import { number, margin, shortDate } from '@/lib/format';
type Estimate={estimate_id:string; margin:number; field_start:string;field_end:string;field_midpoint:number;recall_weighted:string;pollster_id:string;round:string;pop:string;denominator_class:string;primary_verified:string;flags:{principal:boolean}};
type Groups={YES?:{mean:number};NO?:{mean:number}};
const lead=(v:number,names?:{D:string;R:string})=>Math.abs(v)<0.05?'Even':names?`${(v>0?names.D:names.R).trim().split(/\s+/).pop()} +${Math.abs(v).toFixed(1)}`:margin(v);
// Poll margins by field midpoint, marked by whether each poll weights on recalled 2024 vote, with each group's average as a
// labeled line (Max, 2026-10-27: "Anyway to make the recall graph easier to read? Maybe more prominent"). Group averages
// are calculator outputs (section5 contrast groups); this component only draws them.
export function DotPlot({estimates,name,groups,names,included}:{estimates:Estimate[];name:string;groups?:Groups;names?:{D:string;R:string};included?:string[]}) {
 const points=estimates.filter(e=>e.flags.principal&&e.primary_verified==='YES'&&Number.isFinite(e.margin));
 if (!points.length) return <Empty title="No verified principal estimates">The source ledger remains below. No dots are inferred from unverified releases.</Empty>;
 // Domains and coordinate transforms only. Margins and midpoints are calculator outputs.
 const start=240,end=305;
 // Zoom to the data (always keeping Even in view) so the gap between the groups is readable.
 const hi=Math.ceil((Math.max(0,...points.map(p=>p.margin))+2)/5)*5, lo=Math.floor((Math.min(0,...points.map(p=>p.margin))-2)/5)*5;
 const inc=new Set(included||[]);const inGroup=(p:Estimate)=>!included||inc.has(p.estimate_id);
 const L=70,R=640,T=24,B=330;
 const x=(v:number)=>L+(v-start)/(end-start)*(R-L);const y=(v:number)=>T+(hi-v)/(hi-lo)*(B-T);
 const ticks=Array.from({length:Math.round((hi-lo)/5)+1},(_,i)=>lo+5*i).filter(t=>(hi-lo)<=30||t%10===0);
 const lines=(['YES','NO'] as const).filter(k=>Number.isFinite(groups?.[k]?.mean)).map(k=>{const own=points.filter(p=>inc.has(p.estimate_id)&&p.recall_weighted===k).map(p=>p.field_midpoint);return {k,v:groups![k]!.mean,x1:own.length?x(Math.min(...own))-10:L,x2:own.length?x(Math.max(...own))+10:R};});
 // keep the two line labels from colliding
 const ly=lines.map(l=>y(l.v));if(ly.length===2&&Math.abs(ly[0]-ly[1])<34){const mid=(ly[0]+ly[1])/2;const up=ly[0]<=ly[1]?0:1;ly[up]=mid-17;ly[1-up]=mid+17;}
 return <figure className="recall-chart">
<svg className="dotplot w-full" viewBox="0 0 900 370" role="img" aria-label={`${name}: verified principal poll margins by field midpoint, marked by recalled 2024 vote weighting. D minus R in percentage points. Exact values are listed in the source ledger.`}>
<title>{`${name} poll margins`}</title>
<desc>Navy triangles weight on recalled 2024 vote (YES), amber circles do not (NO), gray squares are unverified. Dashed lines are each group's average.</desc>{ticks.map(t=>
<g key={t}><line x1={L} x2={R} y1={y(t)} y2={y(t)} className={t===0?'axis-zero':'gridline'}/><text x={L-12} y={y(t)+5} textAnchor="end">{t===0?'Even':`${t>0?'D':'R'} +${Math.abs(t)}`}</text></g>)}
{[[243,'Sep 1'],[273,'Oct 1'],[297,'Oct 25']].map(([v,label])=><text key={v} x={x(Number(v))} y="358" textAnchor="middle">{label}</text>)}
{lines.map((l,i)=><g key={l.k} className={`recall-line recall-${l.k.toLowerCase()}`}><line x1={l.x1} x2={l.x2} y1={y(l.v)} y2={y(l.v)}/><path d={`M ${l.x2} ${y(l.v)} L ${R+14} ${ly[i]}`} className="recall-leader"/><text x={R+20} y={ly[i]-3} className="recall-line-label">{l.k==='YES'?'Uses 2024 vote':'Does not'}</text><text x={R+20} y={ly[i]+16} className="recall-line-value">{lead(l.v,names)}</text></g>)}
{points.map(p=><g key={p.estimate_id} className={`recall-${p.recall_weighted.toLowerCase()}${inGroup(p)?'':' is-context'}`}>
<title>{`${p.pollster_id}: ${margin(p.margin)}, ${shortDate(p.field_start)}–${shortDate(p.field_end)}; recall ${p.recall_weighted}; ${p.round}/${p.pop}/${p.denominator_class}`}</title>{p.recall_weighted==='YES'?<path d={`M ${x(p.field_midpoint)} ${y(p.margin)-8} l 8 14 h -16 Z`}/>:p.recall_weighted==='NO'?<circle cx={x(p.field_midpoint)} cy={y(p.margin)} r="7"/>:<rect x={x(p.field_midpoint)-6} y={y(p.margin)-6} width="12" height="12"/>}</g>)}</svg>
<p className="recall-chart-key" aria-hidden="true"><span className="recall-yes">▲ Uses 2024 vote</span><span className="recall-no">● Does not</span><span className="recall-unverified">■ Unverified</span><span className="muted">{included?'dashed line: average of the bold polls in each group; faded polls are outside the comparison':'dashed line: group average'}</span></p>
</figure>;
}
