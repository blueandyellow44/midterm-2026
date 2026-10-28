// Every published document is a prerendered Workers asset. Unmatched paths must never enter Next's server/ISR runtime or
// request an unconfigured cache binding. The per-page Content-Security-Policy (one hash set per route) is attached here
// from the map scripts/csp-hashes.mjs writes at build time: Cloudflare's _headers file allows 100 rules and the site has
// more pages than that since the House build (deploy refused 2026-10-27, code 100324).
import CSP from './csp-routes.json';
const GLOBAL = {
  'Cache-Control': 'no-cache',
  'Strict-Transport-Security': 'max-age=31536000',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
};
const DENY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";
export default {
  async fetch(request, env) {
    if (!env || !env.ASSETS) return new Response('Not found. Return to the Undertow race index at /.', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8', ...GLOBAL, 'Content-Security-Policy': DENY } });
    const res = await env.ASSETS.fetch(request);
    const headers = new Headers(res.headers);
    for (const [k, v] of Object.entries(GLOBAL)) headers.set(k, v);
    const type = headers.get('Content-Type') || '';
    if (type.includes('text/html')) {
      const path = new URL(request.url).pathname;
      const route = res.status === 404 ? '/404/' : path.endsWith('/') ? path : `${path}/`;
      headers.set('Content-Security-Policy', CSP[route] || DENY);
    }
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
  },
};
