import { expect,it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { SignalReading } from '../components/SignalReading';
import { races,signalsMeta } from '../lib/data';

const names={D:{candidate:'Dee'},R:{candidate:'Arr'}};
const base=(over:any={})=>({name:'Test race',heat:{candidates:names},signal:{status:'ADJUSTED',alignment:'ALIGNED',weight_spending:1,weight_rhetoric:1,
 delta_spending:1.2,delta_rhetoric:0.8,delta_total:2,delta_sd:0.9,adjusted_margin:3,polling_margin:1,rhetoric_capped:false,window_end:'2026-10-25',
 fundamentals:{pres_d_minus_r:-10,underdog:'D'},spending:{coverage:'FEC_SCHEDULE_E',d_fav_recent:2e6,r_fav_recent:8e6,excess_z:1.1},
 rhetoric:{gap:0.6,mean_d:3,mean_r:3.6,n_d:2,n_r:3},...over}});
const render=(r:any)=>renderToStaticMarkup(<SignalReading r={r} meta={signalsMeta}/>);

it('renders nothing without a signal block or candidate names',()=>{
 for(const r of [null,{},{signal:null,heat:{candidates:names}},{signal:base().signal,heat:{}}])expect(render(r)).toBe('');
});

it('shows the polling-error lean as its own line',()=>{
 const html=render(base({delta_polling_error:3.3,delta_total:5.3,adjusted_margin:6.3}));
 expect(html).toContain('Recent polling error');expect(html).toContain('3.3 toward Dee');
});

it('explains a race with no usable signal in one line instead of an empty panel',()=>{
 const html=render(base({status:'NO_SIGNAL',alignment:'NO_SIGNAL',weight_spending:0,weight_rhetoric:0,adjusted_margin:1,delta_total:0,
  spending:{coverage:'NOT_FEDERAL'},rhetoric:{gap:null}}));
 expect(html).toContain('none strong enough to adjust');
 expect(html).toContain('report spending to the state');
 expect(html).toContain('not enough scored ads');
 expect(html).not.toContain('signal-reading');
});

it('shows the adjusted lead, the shift and each contribution toward the right candidate',()=>{
 const html=render(base());
 expect(html).not.toContain('Experimental');
 expect(html).toContain('3.0');
 expect(html).toContain('The pull');expect(html).toContain('2.0 toward Dee');
 expect(html).toContain('1.2 toward Dee');
 expect(html).toContain('Arr’s ads and debate answers run hotter');

});

it('names the leader correctly when the adjustment moves toward the Republican',()=>{
 const html=render(base({alignment:'SPENDING_ONLY',weight_rhetoric:0,delta_spending:-1.5,delta_rhetoric:0,delta_total:-1.5,adjusted_margin:-0.5,spending:{coverage:'FEC_SCHEDULE_E',d_fav_recent:1e6,r_fav_recent:1e6,excess_z:-1.3}}));
 expect(html).toContain('Arr');
 expect(html).toContain('1.5 toward Arr');
 expect(html).toContain('lead being safer than the polls show');
});

it('renders the sealed release for every race without NaN or undefined',()=>{
 for(const r of races){const html=render(r);expect(html).not.toMatch(/NaN|undefined|\[object/);}
 const oh=races.find(r=>r.id==='2026-OH-SEN-SPECIAL');expect(render(oh)).toContain('weighed against each other');expect(render(oh)).not.toContain('not counted');
 const nc=races.find(r=>r.id==='2026-NC-SEN');expect(render(nc)).toContain('Early vote');expect(render(nc)).toContain('by party registration');
 const tx=races.find(r=>r.id==='2026-TX-SEN');expect(render(tx)).toContain('toward James Talarico');
});
