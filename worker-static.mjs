// Every published document is a prerendered Workers asset. Unmatched paths must
// never enter Next's server/ISR runtime or request an unconfigured cache binding.
export default {
  fetch() {
    return new Response('Not found. Return to the Election Weather race index at /.', {
      status: 404,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
      }
    });
  }
};
