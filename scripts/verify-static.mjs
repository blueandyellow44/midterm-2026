import { readFileSync,existsSync } from 'node:fs';
import { join } from 'node:path';
import { policy } from './csp-hashes.mjs';
import { validateBundle,sha256 } from './bundle.mjs';
const {manifest}=validateBundle('data');
const headers=readFileSync('.open-next/assets/_headers','utf8');
const cspMap=JSON.parse(readFileSync('.open-next/csp-routes.json','utf8'));
if((headers.match(/^\//mg)||[]).length>100)throw new Error('_headers exceeds the 100-rule limit');
const routes=JSON.parse(readFileSync('.next/csp-routes.json','utf8'));
// One page per race plus these named pages; /ballot/ joined them on 2026-11-03 (Max: "move the phone version to the Undertow site").
const PAGES=['/','/method/','/excluded/','/tonight/','/ballot/','/scoreboard/','/grading/','/404/'];
const missingPage=PAGES.find(p=>!routes.some(r=>r.route===p));if(missingPage)throw new Error(`Missing page: ${missingPage}`);
if(routes.length!==manifest.scope.senate_races.length+manifest.scope.governor_races.length+(manifest.scope.house_races||[]).length+PAGES.length)throw new Error('Unexpected route count');
for(const {file,route,csp} of routes){const p=join('.open-next/assets',route==='/404/'?'404.html':`${route}/index.html`);if(!existsSync(p))throw new Error(`Missing static route: ${route}`);const html=readFileSync(p,'utf8');if(sha256(html)!==sha256(readFileSync(file)))throw new Error(`HTML changed after hashing: ${route}`);if(policy(html)!==csp||cspMap[route]!==csp)throw new Error(`CSP mismatch: ${route}`);if(route!=='/404/'&&!html.includes(manifest.release_id))throw new Error('Missing release identity');if(/(?:sk-ant-|AIzaSy|-----BEGIN (?:RSA |EC )?PRIVATE KEY)/.test(html))throw new Error('Secret pattern in emitted HTML');if(/\[\[[A-Za-z][^\]\n]*\]\]|~\/[A-Za-z]|Resources\/methods|Prompt revision|Second Brain/.test(html))throw new Error(`Vault artifact in emitted HTML: ${route}`);}
const allCsp=Object.values(cspMap).join('\n');if(allCsp.includes("'unsafe-inline'")||allCsp.includes('nonce-')||Object.keys(cspMap).length!==routes.length)throw new Error('Unsafe or incomplete script policy');
if(sha256(readFileSync('.open-next/worker.js'))!==sha256(readFileSync('worker-static.mjs')))throw new Error('Unexpected dynamic Worker fallback');
console.log(`Verified ${routes.length} static routes, final CSP hashes, release footer, secret scan and vault-leak scan.`);
