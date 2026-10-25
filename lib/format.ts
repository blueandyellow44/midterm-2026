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
