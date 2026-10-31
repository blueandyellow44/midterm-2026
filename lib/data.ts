import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { validateBundle, readCsv } from '../scripts/bundle.mjs';
import { toPublicNote } from './public-note';
export const bundle=validateBundle(join(process.cwd(),'data'));
export const { manifest, derived, manifestHash }=bundle;
export const raceIds: string[]=[...manifest.scope.senate_races,...manifest.scope.governor_races,...(manifest.scope.house_races||[])];
export const states: Record<string,string>={AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'};
export const slug=(id:string)=>id.replace('2026-','').toLowerCase();
const ordinal=(n:number)=>{const t=n%100;return `${n}${t>=11&&t<=13?'th':({1:'st',2:'nd',3:'rd'} as Record<number,string>)[n%10]||'th'}`;};
export const isHouse=(id:string)=>id.endsWith('-HOUSE');
export const raceName=(id:string)=>{const [,st,d]=id.split('-');if(isHouse(id))return `${states[st]} ${d==='AL'?'at-large':ordinal(Number(d))} District`;return `${states[st]} ${id.includes('GOV')?'governor':'Senate'}${id.includes('SPECIAL')?' · special':''}`;};
export function raceData(id:string) {
 const r=derived.races[id];const heat=derived.section9_heat.per_race[id]??{candidates:(derived as any).candidates?.[id]};
 const recallComparison=derived.section5_contrasts.ii.per_race[id];
 const recallSources=derived.estimates.filter((e:{estimate_id:string})=>recallComparison?.included_estimate_ids?.includes(e.estimate_id)).sort((a:{field_end:string},b:{field_end:string})=>b.field_end.localeCompare(a.field_end));
 const contributing=derived.estimates.filter((e:{estimate_id:string})=>r.averaging_estimate_ids.includes(e.estimate_id));
 const ends=contributing.map((e:{field_end:string})=>e.field_end).sort();
 return {id,name:raceName(id),slug:slug(id),...r,recallComparison,recallSources,recallFraming:derived.section5_contrasts.framing,newestPollEnd:r.latest_contributing_field_end??ends.at(-1)??null,oldestPollEnd:r.oldest_contributing_field_end??ends.at(0)??null,heat,coverage:derived.section10_coverage.find((c:{race:string})=>c.race===id),signal:derived.signals?.per_race?.[id]??null};
}
export const races=raceIds.map(raceData);
export const signalsMeta=derived.signals?{window_end:derived.signals.window_end,priors:derived.signals.priors,posterior:derived.signals.posterior,history:derived.signals.history,rules:derived.signals.rules,framing:derived.signals.framing,state_lean:derived.signals.state_lean,poll_error_model:derived.signals.poll_error_model,spending_backtest:derived.signals.spending_backtest,early_vote_model:derived.signals.early_vote_model,witness_model:derived.signals.witness_model,offyear_record:derived.signals.offyear_record,early_vote_states:[...new Set(Object.values(derived.signals.per_race||{}).filter((r:any)=>r.early_vote?.in_reading).map((r:any)=>r.polling_error?.state))].sort()}:null;
export const chambers=(derived as any).chambers??null;
export const publicEstimates=(id:string)=>derived.estimates.filter((e:{race:string;quarantined:boolean})=>e.race===id && !e.quarantined);
export const method=toPublicNote(readFileSync(join(process.cwd(),'data/midterm-2026-poll-weighting.md'),'utf8'));
export const excluded=readCsv(readFileSync(join(process.cwd(),'data/exclusions.csv'),'utf8'));
export const quarantine=derived.estimates.filter((e:{quarantined:boolean})=>e.quarantined);
// The frozen record (Stage 3): present only in a release sealed with --freeze; null before November 2.
export const predictions: Record<string,string>[]|null=existsSync(join(process.cwd(),'data/predictions.csv'))?readCsv(readFileSync(join(process.cwd(),'data/predictions.csv'),'utf8'),['race','vector','p_d_slot','weighted_margin','frozen_at']):null;
export const pollsterNames: Record<string,string>=Object.fromEntries(readCsv(readFileSync(join(process.cwd(),'data/pollsters.csv'),'utf8')).map((p:Record<string,string>)=>[p.pollster_id,p.pollster_name||p.pollster_id]));
