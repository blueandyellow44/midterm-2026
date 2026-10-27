import { expect,it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { RecallComparison } from '../components/RecallComparison';
import { races,pollsterNames } from '../lib/data';

const fixture=()=>({slug:'test',heat:{candidates:{D:{candidate:'Candidate D'},R:{candidate:'Candidate R'}}},recallComparison:{value:2,groups:{YES:{mean:3,estimates:1,pollsters:1},NO:{mean:1,estimates:2,pollsters:1}},stratum:{pop:'LV',denominator_class:'FULL',round:'NA'}},recallSources:[],recall_counts_principal_both:{UNVERIFIED:4},recallFraming:'Every comparison here is descriptive.'});
const render=(r:any)=>renderToStaticMarkup(<RecallComparison r={r}/>);

it('omits absent, empty, one-sided and malformed comparisons without false zeros',()=>{
 for(const r of [null,{}, {recallComparison:null},{recallComparison:{value:0,groups:{}}}])expect(render(r)).toBe('');
 for(const change of [(r:any)=>r.recallComparison.groups.NO.mean=null,(r:any)=>r.recallComparison.value=NaN,(r:any)=>r.recallComparison.groups.NO.pollsters=0,(r:any)=>r.recallComparison.groups.YES.estimates=Infinity]){const r=fixture();change(r);expect(render(r)).toBe('');}
});
it('labels the two methods and separates poll waves from pollster counts',()=>{
 const html=render(fixture());expect(html).toContain('average leads');expect(html).toContain('Uses 2024 vote');expect(html).toContain('Does not use it');expect(html).toContain('2 polls · 1 pollster');expect(html).toContain('2.0 points more favorably for Candidate D');expect(html).toContain('Each pollster counts equally');expect(html).toContain('Different pollsters and dates may explain this gap');
});
it('handles the reverse direction without inventing an accuracy winner',()=>{
 const r=fixture();r.recallComparison.value=-2;r.recallComparison.groups.YES.mean=-3;r.recallComparison.groups.NO.mean=-1;const html=render(r);expect(html).toContain('for Candidate R');expect(html).toContain('2.0 points more favorably for Candidate R');expect(html).toContain('It does not establish which method is better');
});
it('preserves real zero and displayed ties without a zero-point leader',()=>{
 const r=fixture();r.recallComparison.value=0.0293;r.recallComparison.groups.YES.mean=0;r.recallComparison.groups.NO.mean=-0.0293;const html=render(r);expect(html).toContain('The groups are even at displayed precision');expect(html).not.toContain('0.0 points more favorably');expect(html).not.toContain('0.0<small>');
});
it('keeps unknown methods out of the NO sources and renders field dates and primary links',()=>{
 const r:any=fixture();r.recallSources=[{estimate_id:'known',pollster_id:'known-firm',source_url:'https://example.org/known',field_start:'2026-10-01',field_end:'2026-10-04',recall_weighted:'NO',primary_verified:'YES'},{estimate_id:'unknown',pollster_id:'unknown-firm',source_url:'https://example.org/unknown',recall_weighted:'UNVERIFIED'}];const html=render(r);expect(html).toContain('https://example.org/known');expect(html).toContain('Oct 1–Oct 4');expect(html).not.toContain('unknown-firm');expect(html).toContain('4 polls have unverified recall weighting');
});
it('uses all six sealed comparisons, including the Ohio counterexample, with precisely their listed sources',()=>{
 const expected:Record<string,string>={'2026-TX-SEN':'2.8 points more favorably for James Talarico','2026-NC-SEN':'1.4 points more favorably for Michael Whatley','2026-MI-GOV':'6.4 points more favorably for Jocelyn Benson','2026-OH-GOV':'5.5 points more favorably for Amy Acton','2026-OH-SEN-SPECIAL':'4.0 points more favorably for Sherrod Brown','2026-MI-SEN':'0.5 points more favorably for Mike Rogers'};
 const visible=races.filter(r=>r.recallComparison?.groups);expect(visible).toHaveLength(6);
 for(const r of races){const html=renderToStaticMarkup(<RecallComparison r={r} pollsterNames={pollsterNames}/>);if(!expected[r.id]){expect(html).toBe('');continue;}const phrase=expected[r.id];expect(html).toContain(phrase);expect(r.recallSources.map((e:any)=>e.estimate_id).sort()).toEqual([...r.recallComparison.included_estimate_ids].sort());expect(r.recallSources.every((e:any)=>e.primary_verified==='YES'&&!e.quarantined&&e.flags.principal&&['YES','NO'].includes(e.recall_weighted))).toBe(true);for(const e of r.recallSources)expect(html).toContain(e.source_url.replaceAll('&','&amp;'));}
});
