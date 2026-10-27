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
export function ReadingKey(){return <details className="reading-key mb-7"><summary><span>How to read this snapshot</span><span className="reading-key-flags">{ready?'Heuristic weighted averages':'Weighted margins pending'} · Coverage stale Oct 8</span></summary><div className="muted pb-4 text-sm leading-relaxed">Recall counts describe October principal estimates. September is context only. {ready?'Weighted means use the selected averaging stratum and the documented factor rules. The simple average of the same polls is shown beside each weighted margin.':'Preliminary means use the selected averaging stratum.'} R +2.5 and R +5 are uniform shifts toward Republicans from the displayed mean; they imply no chamber-control result. pH gaps are D minus R; positive means more measured hyperbole for the Democratic candidate. All coverage readings are stale, from October 8; PARTIAL matches do not establish full race coverage. There are {derived.counts.selected_estimates_both} October principal estimates in this release.</div></details>}

export function WallStrip(){return <div className="wall-strip"><p className="wall-strip-head">Polls have missed Democrats by {missText} since last fall. <span>I think they are missing it again.</span></p><div className="wall-strip-meta"><span>By Max Sheahan</span><span>Updated {snapshotDate}</span><FreezeCountdown builtAt={builtAt}/></div></div>}
export const biggestPullId=top?.id||'';
export function WallMeta(){return <div className="wall-strip wall-mobile-strip"><div className="wall-strip-meta"><span>Undertow · By Max Sheahan</span><span>Updated {snapshotDate}</span><FreezeCountdown builtAt={builtAt}/></div></div>}
