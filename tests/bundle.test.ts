import { describe,it,expect,afterEach } from 'vitest';
import { readCsv,validateBundle,sha256 } from '../scripts/bundle.mjs';
import { mkdtempSync,cpSync,writeFileSync,readFileSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const temps:string[]=[];
function fixture(){const p=mkdtempSync(join(tmpdir(),'ew-bundle-'));temps.push(p);cpSync('data',p,{recursive:true});return p;}
afterEach(()=>{for(const p of temps.splice(0))rmSync(p,{recursive:true,force:true});});
describe('CSV boundaries',()=>{
 it('rejects empty and missing columns',()=>{expect(()=>readCsv(null)).toThrow();expect(()=>readCsv('')).toThrow();expect(()=>readCsv('a\n1',['race'])).toThrow();});
 it('rejects malformed rows and duplicate columns',()=>{expect(()=>readCsv('a,b\n1,2,3')).toThrow();expect(()=>readCsv('a,a\n1,2')).toThrow();expect(()=>readCsv('a\n"unfinished')).toThrow();});
 it('supports header-only, quoted multiline and a realistic volume',()=>{expect(readCsv('a,b\n')).toEqual([]);expect(readCsv('a,b\n"one\ntwo","a,b"')).toEqual([{a:'one\ntwo',b:'a,b'}]);expect(readCsv('a\n'+Array.from({length:10000},(_,i)=>i).join('\n')).length).toBe(10000);});
});
describe('atomic bundle publication',()=>{
 it('rejects changed bytes and extra private files',()=>{let p=fixture();writeFileSync(join(p,'polls.csv'),'tampered');expect(()=>validateBundle(p)).toThrow(/integrity/);p=fixture();writeFileSync(join(p,'run-state.json'),'{}');expect(()=>validateBundle(p)).toThrow(/Unexpected/);});
 it('rejects unknown schema and mixed derived identities even with valid file hash',()=>{let p=fixture();let m=JSON.parse(readFileSync(join(p,'manifest.json'),'utf8'));m.csv_schemas.polls='9';writeFileSync(join(p,'manifest.json'),JSON.stringify(m));expect(()=>validateBundle(p)).toThrow(/schema/);p=fixture();m=JSON.parse(readFileSync(join(p,'manifest.json'),'utf8'));const d=JSON.parse(readFileSync(join(p,'derived.json'),'utf8'));d.release_id='other';const bytes=Buffer.from(JSON.stringify(d));writeFileSync(join(p,'derived.json'),bytes);const f=m.files.find((f:any)=>f.path==='derived.json');f.sha256=sha256(bytes);f.bytes=bytes.length;writeFileSync(join(p,'manifest.json'),JSON.stringify(m));expect(()=>validateBundle(p)).toThrow(/Mixed/);});
 it('validates the sealed current release',()=>{expect(validateBundle('data').manifest.release_id).toMatch(/stage(?:1b|2)/);});
 it('rejects a passed ratings gate with missing weighted results even when bytes match',()=>{const p=fixture();const m=JSON.parse(readFileSync(join(p,'manifest.json'),'utf8'));const d=JSON.parse(readFileSync(join(p,'derived.json'),'utf8'));d.stage2c_passed=true;m.stage_status.stage2c='PASSED';const race:any=Object.values(d.races).find((r:any)=>r.retained_count>0);race.weighted_margin=null;const bytes=Buffer.from(JSON.stringify(d));writeFileSync(join(p,'derived.json'),bytes);const entry=m.files.find((f:any)=>f.path==='derived.json');entry.sha256=sha256(bytes);entry.bytes=bytes.length;writeFileSync(join(p,'manifest.json'),JSON.stringify(m));expect(()=>validateBundle(p)).toThrow(/weighted margin/);});
});

function editDerived(p:string,change:(d:any)=>void){const m=JSON.parse(readFileSync(join(p,'manifest.json'),'utf8'));const d=JSON.parse(readFileSync(join(p,'derived.json'),'utf8'));change(d);const bytes=Buffer.from(JSON.stringify(d));writeFileSync(join(p,'derived.json'),bytes);const f=m.files.find((f:any)=>f.path==='derived.json');f.sha256=sha256(bytes);f.bytes=bytes.length;writeFileSync(join(p,'manifest.json'),JSON.stringify(m));}
function seedReads(d:any){delete d.signals;for(const r of Object.values(d.races) as any[])r.polling_read={kind:'UNAVAILABLE',margin:null,poll_count:0};const r=d.races['2026-MI-GOV'];r.weighted_margin=null;r.retained_count=0;const e=d.estimates.find((e:any)=>e.race===r.race&&e.flags.principal&&e.primary_verified==='YES'&&e.round==='NA'&&e.window==='BOTH');r.polling_read={kind:'LATEST_POLL',margin:e.margin,poll_count:1,age_days:7,field_end:e.field_end,stratum:{pop:e.pop,round:e.round,denominator_class:e.denominator_class},latest_poll:{estimate_id:e.estimate_id,source_url:e.source_url}};return {r,e};}
describe('public polling read boundary',()=>{
 it('accepts source context without turning it into an average',()=>{const p=fixture();editDerived(p,d=>{seedReads(d);});expect(()=>validateBundle(p)).not.toThrow();});
 it('rejects unverified, quarantined, altered and unsupported-round sources even with matching hashes',()=>{for(const change of [(e:any)=>e.primary_verified='UNVERIFIED',(e:any)=>e.quarantined=true,(e:any)=>e.round='UNVERIFIED',(e:any)=>e.margin=999]){const p=fixture();editDerived(p,d=>{const {e}=seedReads(d);change(e);});expect(()=>validateBundle(p)).toThrow(/latest-poll/);}});
 it('rejects unknown or incomplete public read contracts',()=>{for(const change of [(r:any)=>r.polling_read.kind='PROBABILITY',(r:any)=>delete r.polling_read]){const p=fixture();editDerived(p,d=>{const {r}=seedReads(d);change(r);});expect(()=>validateBundle(p)).toThrow(/public polling read/);}});
});
describe('signal-adjusted reading boundary',()=>{
 it('accepts the sealed signal block and older releases without one',()=>{expect(validateBundle('data').derived.signals.per_race['2026-TX-SEN'].polling_margin).toBe(validateBundle('data').derived.races['2026-TX-SEN'].polling_read.margin);const p=fixture();editDerived(p,d=>{delete d.signals;});expect(()=>validateBundle(p)).not.toThrow();});
 it('rejects tampered arithmetic, a different starting number, an adjusted no-signal race and unknown alignment',()=>{
  const cases:[(d:any)=>void,RegExp][]=[
   [d=>{d.signals.per_race['2026-TX-SEN'].adjusted_margin+=1;},/arithmetic/],
   [d=>{d.signals.per_race['2026-TX-SEN'].polling_margin+=1;},/different polling number/],
   [d=>{const s=d.signals.per_race['2026-TX-SEN'];s.alignment='NO_SIGNAL';s.delta_spending=1;s.delta_rhetoric=0;s.delta_total=1;s.adjusted_margin=s.polling_margin+1;},/No-signal race/],
   [d=>{d.signals.per_race['2026-TX-SEN'].alignment='VIBES';},/alignment/],
   [d=>{d.signals.per_race['2026-XX-SEN']=d.signals.per_race['2026-TX-SEN'];},/unknown race/],
  ];
  for(const [change,err] of cases){const p=fixture();editDerived(p,change);expect(()=>validateBundle(p)).toThrow(err);}
 });
});
