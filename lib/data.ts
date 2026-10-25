import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { validateBundle, readCsv } from '../scripts/bundle.mjs';
export const bundle=validateBundle(join(process.cwd(),'data'));
export const { manifest, derived, manifestHash }=bundle;
export const raceIds: string[]=[...manifest.scope.senate_races,...manifest.scope.governor_races];
export const states: Record<string,string>={TX:'Texas',IA:'Iowa',ME:'Maine',AK:'Alaska',OH:'Ohio',MI:'Michigan',NC:'North Carolina',GA:'Georgia',WI:'Wisconsin'};
export const slug=(id:string)=>id.replace('2026-','').toLowerCase();
export const raceName=(id:string)=>`${states[id.split('-')[1]]} ${id.includes('GOV')?'governor':'Senate'}${id.includes('SPECIAL')?' · special':''}`;
export function raceData(id:string) {
 const r=derived.races[id];const heat=derived.section9_heat.per_race[id];
 const contributing=derived.estimates.filter((e:{estimate_id:string})=>r.averaging_estimate_ids.includes(e.estimate_id));
 const ends=contributing.map((e:{field_end:string})=>e.field_end).sort();
 return {id,name:raceName(id),slug:slug(id),...r,newestPollEnd:r.latest_contributing_field_end??ends.at(-1)??null,oldestPollEnd:r.oldest_contributing_field_end??ends.at(0)??null,heat,coverage:derived.section10_coverage.find((c:{race:string})=>c.race===id)};
}
export const races=raceIds.map(raceData);
export const publicEstimates=(id:string)=>derived.estimates.filter((e:{race:string;quarantined:boolean})=>e.race===id && !e.quarantined);
export const method=readFileSync(join(process.cwd(),'data/midterm-2026-poll-weighting.md'),'utf8').replace(/^---[\s\S]*?---\s*/,'');
export const excluded=readCsv(readFileSync(join(process.cwd(),'data/exclusions.csv'),'utf8'));
export const quarantine=derived.estimates.filter((e:{quarantined:boolean})=>e.quarantined);
export const pollsterNames: Record<string,string>=Object.fromEntries(readCsv(readFileSync(join(process.cwd(),'data/pollsters.csv'),'utf8')).map((p:Record<string,string>)=>[p.pollster_id,p.pollster_name||p.pollster_id]));
