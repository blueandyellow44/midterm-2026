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
