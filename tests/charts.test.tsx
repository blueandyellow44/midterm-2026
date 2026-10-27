import { expect,it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { DotPlot } from '../components/Charts';
import { marginLabel, type WallRace } from '../components/ElectionWall';
it('shows a rounded tie as Even rather than a lead of 0.0',()=>{
 expect(marginLabel(0.0293,{d:'Ann Dee',r:'Rob Arr'} as WallRace)).toBe('Even');
 expect(marginLabel(-0.0293,{d:'Ann Dee',r:'Rob Arr'} as WallRace)).toBe('Even');
});
it('emits chart and point titles as actual SVG text during server rendering',()=>{
 const html=renderToStaticMarkup(<DotPlot name="Alaska Senate" estimates={[{estimate_id:'one',margin:2.1,field_start:'2026-10-09',field_end:'2026-10-10',field_midpoint:281.5,recall_weighted:'NO',pollster_id:'Example Pollster',round:'FINAL',pop:'LV',denominator_class:'FULL',primary_verified:'YES',flags:{principal:true}}]}/>);
 expect(html).toContain('<title>Alaska Senate poll margins</title>');
 expect(html).toContain('<title>Example Pollster: D +2.1, Oct 9–Oct 10; recall NO; FINAL/LV/FULL</title>');
 expect(html).not.toContain('<title></title>');
});

