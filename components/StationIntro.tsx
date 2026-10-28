import { derived } from '@/lib/data';
import { shortDate } from '@/lib/format';
import { FreezeCountdown } from './FreezeCountdown';
const ready=derived.stage2c_passed;
const snapshotDate=shortDate(derived.analytical_as_of.slice(0,10));
const sig=(derived as any).signals?.per_race||{};
const pulls=Object.entries(sig).map(([id,s]:[string,any])=>({id,pull:Number(s.delta_total)})).filter(x=>Number.isFinite(x.pull)).sort((a,b)=>Math.abs(b.pull)-Math.abs(a.pull));
const miss=Number((derived as any).signals?.rules?.poll_error_2025_miss);
const missText=Number.isFinite(miss)?miss.toFixed(1):'7.5';
const builtAt=Date.parse(derived.analytical_as_of);
const top=pulls[0];const heatRaces=(derived as any).section9_heat?.per_race||{};const topName=top?(top.pull>0?heatRaces[top.id]?.candidates?.D?.candidate:heatRaces[top.id]?.candidates?.R?.candidate):'';const states:Record<string,string>={TX:'Texas',IA:'Iowa',ME:'Maine',AK:'Alaska',OH:'Ohio',MI:'Michigan',NC:'North Carolina',GA:'Georgia',WI:'Wisconsin',KS:'Kansas',NE:'Nebraska',SC:'South Carolina',MS:'Mississippi',NH:'New Hampshire',FL:'Florida'};const topRace=top?`${states[top.id.split('-')[1]]} ${top.id.includes('GOV')?'governor':'Senate'}`:'';
export function ReadingKey(){return <details className="reading-key mb-7"><summary><span>How to read this snapshot</span><span className="reading-key-flags">{ready?'Heuristic weighted averages':'Weighted margins pending'}</span></summary><div className="muted pb-4 text-sm leading-relaxed">Recall counts describe October principal estimates. September is context only. {ready?'Weighted means use the selected averaging stratum and the documented factor rules. The simple average of the same polls is shown beside each weighted margin.':'Preliminary means use the selected averaging stratum.'} R +2.5 and R +5 are uniform shifts toward Republicans from the displayed mean; they imply no chamber-control result. There are {derived.counts.selected_estimates_both} October principal estimates in this release.</div></details>}

type LiveLine = { settled: number; polls_mae: number | null; undertow_mae: number | null; undertow_closer?: number; polls_closer?: number; implied_miss: number | null } | null;
// Running grade on election night and the locked state after the freeze (Max, 2026-10-28). Every figure is from weight.py.
function NightLine({ live, locked }: { live: LiveLine; locked: boolean }) {
  if (live && live.settled > 0) return <p className="wall-strip-night"><b>Counted so far: {live.settled} {live.settled === 1 ? 'race' : 'races'}.</b> Polls off by {live.polls_mae?.toFixed(1)} on average, Undertow by {live.undertow_mae?.toFixed(1)}. Undertow closer in {live.undertow_closer ?? 0}, the polls in {live.polls_closer ?? 0}. <a href="/scoreboard/">Scoreboard →</a></p>;
  if (locked) return <p className="wall-strip-night"><b>Locked {snapshotDate}.</b> Nothing on this page changes until the votes are counted. <a href="/grading/">How it is graded →</a></p>;
  return null;
}
export function WallStrip({ live = null, locked = false }: { live?: LiveLine; locked?: boolean }){return <div className="wall-strip"><p className="wall-strip-head">Since last fall, polls have understated Democrats by {missText} points. <span>I think they still are.</span></p><div className="wall-strip-meta"><span>By Max Sheahan</span><span>Updated {snapshotDate}</span>{!locked && <FreezeCountdown builtAt={builtAt}/>}</div><NightLine live={live} locked={locked}/><Moved/></div>}
// What moved since the last release (Max, 2026-10-28), from derived.changes, which the release step computes in weight.py.
const ch=(derived as any).changes;
const raceShort=(id:string)=>{const [,st,a,b]=id.split('-');return id.endsWith('HOUSE')?`${st}-${a}`:`${states[st]||st} ${id.includes('GOV')?'Gov':'Sen'}${b==='SPECIAL'?' special':''}`;};
const signed=(v:number)=>`${v>=0?'D':'R'} +${Math.abs(v).toFixed(1)}`;
function Moved(){if(!ch)return null;const top=(ch.moved||[]).slice(0,4);const parts=[ch.polls_added>0?`${ch.polls_added} new ${ch.polls_added===1?'poll':'polls'}`:null,...top.map((x:any)=>`${raceShort(x.race)} ${signed(x.from)} → ${signed(x.to)}`),(ch.new_readings||[]).length?`${ch.new_readings.length} new ${ch.new_readings.length===1?'reading':'readings'}`:null].filter(Boolean);if(!parts.length)return null;return <p className="wall-strip-moved"><b>Since {shortDate(String(ch.since_as_of).slice(0,10))}:</b> {parts.join(' · ')}{(ch.moved||[]).length>top.length?` · ${ch.moved.length-top.length} more`:''}</p>;}
export const biggestPullId=top?.id||'';
// Phone landing (Max, 2026-10-28: "This sucks as a landing page look"): the claim first, then who and when, then the numbers.
export function WallMeta({ live = null, locked = false }: { live?: LiveLine; locked?: boolean }){return <div className="wall-mobile-hero"><h1 className="wall-mobile-claim">Since last fall, polls have understated Democrats by {missText} points. <span>I think they still are.</span></h1><p className="wall-mobile-by"><span>By Max Sheahan · {snapshotDate}</span>{!locked && <FreezeCountdown builtAt={builtAt}/>}</p><NightLine live={live} locked={locked}/></div>}
export function MovedLine(){return <Moved/>}
