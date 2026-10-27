import { readFileSync,writeFileSync,readdirSync,statSync } from 'node:fs';
import { join,relative } from 'node:path';
import { createHash } from 'node:crypto';
export function htmlFiles(directory){return readdirSync(directory).flatMap(n=>{const p=join(directory,n);return statSync(p).isDirectory()?htmlFiles(p):p.endsWith('.html')?[p]:[];});}
export function inlineScripts(html){return [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m=>! /\bsrc\s*=/.test(m[1]) && !/type="application\/(?:ld\+)?json"/.test(m[1])).map(m=>m[2]);}
export const policy=(html)=>`default-src 'self'; script-src 'self' ${[...new Set(inlineScripts(html).map(body=>`'sha256-${createHash('sha256').update(body).digest('base64')}'`))].join(' ')}; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self' https://buttondown.com`;
export function routeFor(file){const p=relative('.next/server/app',file).replace(/\.html$/,'');return p==='index'?'/':p==='_not-found'?'/404/':`/${p}/`;}
if (process.argv[1]===new URL(import.meta.url).pathname) {
 let headers='/*\n  Cache-Control: no-cache\n  Strict-Transport-Security: max-age=31536000\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n';
 const map=[];
 for (const file of htmlFiles('.next/server/app').filter(p=>!p.endsWith('/_global-error.html'))) {
  const route=routeFor(file),html=readFileSync(file,'utf8'),csp=policy(html);
  if (html.includes(' style=')) throw new Error(`Unexpected inline style in ${route}`);
  if (csp.length+27>2000) throw new Error(`CSP exceeds Cloudflare line limit: ${route}`);
  for (const path of route==='/'?['/']: [route,route.slice(0,-1)]) headers+=`${path}\n  Content-Security-Policy: ${csp}\n`;
  map.push({file,route,csp});
 }
 writeFileSync('public/_headers',headers);
 writeFileSync('.next/csp-routes.json',JSON.stringify(map,null,2));
 console.log(`Hashed final Next HTML for ${map.length} routes; no inline styles required.`);
}
