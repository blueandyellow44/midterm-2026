import {readFileSync,writeFileSync} from 'node:fs';
import {validateBundle} from './bundle.mjs';
const base=process.argv[2];if(!base||!/^https?:\/\//.test(base))throw new Error('Usage: node scripts/verify-http.mjs <origin> [report.json]');
const {manifest}=validateBundle('data');
const routes=JSON.parse(readFileSync('.next/csp-routes.json','utf8')).filter(r=>r.route!=='/404/');
const checks=await Promise.all(routes.map(async({route,csp})=>{
 const response=await fetch(new URL(route+'?verify='+Date.now(),base),{signal:AbortSignal.timeout(15000)});const html=await response.text();
 const errors=[];if(response.status!==200)errors.push(`HTTP ${response.status}`);
 if(response.headers.get('cache-control')!=='no-cache')errors.push('Cache-Control');
 if(response.headers.get('content-security-policy')!==csp)errors.push('CSP differs from final HTML');
 if(response.headers.get('x-content-type-options')!=='nosniff')errors.push('nosniff');
 if(response.headers.get('referrer-policy')!=='strict-origin-when-cross-origin')errors.push('referrer');
 if(response.headers.get('permissions-policy')!=='camera=(), microphone=(), geolocation=()')errors.push('permissions');
 if(!html.includes(manifest.release_id))errors.push('release footer');
 return {route,status:response.status,errors};
}));
for(const [path,type] of [['/favicon.svg','image/svg+xml'],['/favicon.png','image/png'],['/og.png','image/png']]){
 const response=await fetch(new URL(path,base),{signal:AbortSignal.timeout(15000)});checks.push({route:path,status:response.status,errors:response.status===200&&response.headers.get('content-type')?.includes(type)?[]:['asset MIME/status']});
}
const unknown=await fetch(new URL('/not-a-published-race/',base),{signal:AbortSignal.timeout(15000)});checks.push({route:'/not-a-published-race/',status:unknown.status,errors:unknown.status===404?[]:['unknown route is not 404']});
const report={checked_at:new Date().toISOString(),base,release_id:manifest.release_id,checks};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n',{flag:'wx'});
for(const check of checks)console.log(`${check.status} ${check.route}${check.errors.length?' FAIL '+check.errors.join(', '):' PASS'}`);
if(checks.some(c=>c.errors.length))process.exitCode=1;
