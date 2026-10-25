import { expect,it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { DotPlot,HeatBars } from '../components/Charts';
import { MarginStrip } from '../components/MarginStrip';
it('gives screen-reader users the same rounded tie as the visible headline',()=>{
 const html=renderToStaticMarkup(<MarginStrip value={0.0293}/>);
 expect(html).toContain('Polling margin: even at displayed precision.');
 expect(html).not.toContain('leads by 0.0');
});
it('emits chart and point titles as actual SVG text during server rendering',()=>{
 const html=renderToStaticMarkup(<DotPlot name="Alaska Senate" estimates={[{estimate_id:'one',margin:2.1,field_start:'2026-10-09',field_end:'2026-10-10',field_midpoint:281.5,recall_weighted:'NO',pollster_id:'Example Pollster',round:'FINAL',pop:'LV',denominator_class:'FULL',primary_verified:'YES',flags:{principal:true}}]}/>);
 expect(html).toContain('<title>Alaska Senate poll margins</title>');
 expect(html).toContain('<title>Example Pollster: D +2.1, Oct 9–Oct 10; recall NO; FINAL/LV/FULL</title>');
 expect(html).not.toContain('<title></title>');
});
it('uses the meter’s five-point maximum rather than a chemical pH scale',()=>{
 const html=renderToStaticMarkup(<HeatBars heat={{candidates:{D:{candidate:'Candidate D',DEBATE:{mean:5,n:1}},R:{candidate:'Candidate R',DEBATE:{mean:1,n:1}}}}}/>);
 expect(html).toMatch(/width="600"[^>]*class="heat-bar-d"/);
 expect(html).toMatch(/width="120"[^>]*class="heat-bar-r"/);
 expect(html).toContain('5 pH · more hyperbole');
 expect(html).not.toContain('14 pH');
});
