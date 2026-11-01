// Local QA server for the built site (Max, 2026-10-28: "need workflows because we made lots of mistakes today").
// Serves .open-next/assets exactly as built, plus the QA page at /__qa/. Open http://127.0.0.1:8790/__qa/ in Max's
// Chrome (one tab, never a test browser, never resize the window): the page drives every route at phone and desktop
// widths inside an iframe and leaves its verdict in window.__qaReport. Stop with Ctrl+C or kill the PID it prints.
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, extname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
// QA_ROOT points the server at another build, e.g. a backup, to prove the checks FAIL on a known-bad state.
const root = process.env.QA_ROOT || join(fileURLToPath(new URL('../..', import.meta.url)), '.open-next/assets');
const qaDir = fileURLToPath(new URL('./page', import.meta.url));
const routesFile = join(fileURLToPath(new URL('../..', import.meta.url)), '.next/csp-routes.json');
if (!existsSync(join(root, 'index.html'))) throw new Error('No build at .open-next/assets: run npm run build:cloudflare first');
const PORT = Number(process.env.QA_PORT || 8790);
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.txt': 'text/plain' };
function file(path) {
  if (existsSync(path) && statSync(path).isDirectory()) path = join(path, 'index.html');
  return existsSync(path) ? path : null;
}
createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = decodeURIComponent(url.pathname);
  if (p === '/__qa/derived.json') { res.writeHead(200, { 'content-type': TYPES['.json'] }); return res.end(readFileSync(join(fileURLToPath(new URL('../..', import.meta.url)), 'data/derived.json'))); }
  if (p === '/__qa/routes.json') {
    const routes = JSON.parse(readFileSync(routesFile, 'utf8')).map(r => r.route).filter(r => r !== '/404/');
    res.writeHead(200, { 'content-type': TYPES['.json'] }); return res.end(JSON.stringify(routes));
  }
  const base = p.startsWith('/__qa') ? qaDir : root;
  const rel = normalize(p.startsWith('/__qa') ? p.slice(5) || '/' : p);
  if (rel.includes('..')) { res.writeHead(400); return res.end(); }
  const f = file(join(base, rel));
  if (!f) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'content-type': TYPES[extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(readFileSync(f));
}).listen(PORT, '127.0.0.1', () => console.log(`QA server PID ${process.pid}: open http://127.0.0.1:${PORT}/__qa/ (Ctrl+C or kill ${process.pid} to stop)`));
