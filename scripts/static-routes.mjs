import { readFileSync,copyFileSync,mkdirSync } from 'node:fs';
import { join,dirname } from 'node:path';
// OpenNext's default cache output does not guarantee prerendered HTML is an asset.
// Promote the exact already-hashed bytes, without rebuilding Next or using ISR.
const routes=JSON.parse(readFileSync('.next/csp-routes.json','utf8'));
for(const {file,route} of routes){const target=join('.open-next/assets',route==='/404/'?'404.html':`${route}/index.html`);mkdirSync(dirname(target),{recursive:true});copyFileSync(file,target);}
copyFileSync('public/_headers','.open-next/assets/_headers');
// No server routes: replace the unused OpenNext fallback with a static 404.
copyFileSync('worker-static.mjs','.open-next/worker.js');
copyFileSync('.next/csp-routes.map.json','.open-next/csp-routes.json');
await import('./verify-static.mjs');
