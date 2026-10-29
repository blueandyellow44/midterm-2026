export function number(value: unknown, digits=1): string {
  if (value === null || value === undefined || (typeof value==='string'&&!value.trim()) || value === 'NA') return 'NA';
  if (value === 'UNVERIFIED') return 'UNVERIFIED';
  const n=Number(value);return Number.isFinite(n)?n.toFixed(digits):'UNVERIFIED';
}
export function margin(value: unknown, pending=false): string {
  if (value === null || value === undefined || (typeof value==='string'&&!value.trim())) return pending?'not yet computed':'NA';
  const n=Number(value);if (!Number.isFinite(n)) return 'UNVERIFIED';
  return Math.abs(n)<0.05?'Even':`${n>0?'D':'R'} +${Math.abs(n).toFixed(1)}`;
}
export function shortDate(value: string): string {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'UNVERIFIED';
  const date=new Date(value+'T12:00:00Z');
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0,10)!==value) return 'UNVERIFIED';
  return new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',timeZone:'UTC'}).format(date);
}

// A candidate's surname for short labels: the last word, skipping generational suffixes ("Nick Begich III" -> "Begich").
const SUFFIX = /^(jr|sr|ii|iii|iv|v)\.?$/i;
export function surname(name: string): string {
  const w = String(name ?? '').trim().split(/\s+/).filter(Boolean);
  while (w.length > 1 && SUFFIX.test(w[w.length - 1])) w.pop();
  return w[w.length - 1] || String(name ?? '');
}

// Poll count under a polls number (Max, 2026-10-28: internal polls flagged). sponsoredOnly comes from weight.py's
// polling_v2 sponsored_only: no poll behind the number was paid for independently (each is a campaign or PAC internal,
// paid by a partisan group, or has no stated sponsor).
export function pollCountLabel(n: number | null | undefined, sponsoredOnly = false): string {
  if (!n) return 'weighted average';
  const base = n === 1 ? '1 poll' : `${n} polls, weighted`;
  return sponsoredOnly ? `${base} · none independently paid for` : base;
}

// Who paid, per poll, from weight.py's sponsor_tier.
export const SPONSOR_TIER_TAG: Record<string, string> = {
  INTERNAL: 'Campaign or PAC internal',
  PARTISAN_SPONSORED: 'Paid by a partisan group',
  UNKNOWN: 'Sponsor not stated',
};

// Per-page share metadata (Max, 2026-10-28 pre-share audit): each page names its own address and preview text, so a
// shared link carries the apex URL and the page's own title instead of the home card's.
export const SITE_PREVIEW_IMAGE = { url: '/og.png', width: 1200, height: 630, alt: 'Undertow, 2026 midterm field notes' };
export function pageShare(path: string, title: string, description: string, image: { url: string; width: number; height: number; alt: string } = SITE_PREVIEW_IMAGE) {
  return {
    alternates: { canonical: path },
    openGraph: { title: `${title} · Undertow`, description, url: path, siteName: 'Undertow', type: 'website' as const, images: [image] },
    twitter: { card: 'summary_large_image' as const, title: `${title} · Undertow`, description, images: [image.url] },
  };
}
