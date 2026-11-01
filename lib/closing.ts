// When each tracked race's polls close on November 3, 2026, Eastern Time. Schedule data, not an analytical number.
// Source: 270toWin, "2026 Election Poll Closing Times" (fetched 2026-10-28). Where a state spans two time zones the race
// is listed at the hour the whole state (or district) has closed; `first` is the earlier close in the rest of the state.
export const CLOSING_SOURCE = { name: '270toWin, 2026 poll closing times', url: 'https://www.270towin.com/poll-closing-times/', fetched: '2026-10-28' };
type Close = { at: string; order: number; first?: string; note?: string };
const T = (at: string, order: number, first?: string, note?: string): Close => ({ at, order, first, note });
export const STATE_CLOSE: Record<string, Close> = {
  KY: T('7:00 PM', 2, '6:00 PM', 'eastern Kentucky closes at 6:00 ET'), GA: T('7:00 PM', 2), SC: T('7:00 PM', 2), VA: T('7:00 PM', 2),
  FL: T('8:00 PM', 4, '7:00 PM', 'most of Florida closes at 7:00 ET; the Panhandle at 8:00 ET'),
  NC: T('7:30 PM', 3), OH: T('7:30 PM', 3),
  AL: T('8:00 PM', 4), ME: T('8:00 PM', 4), MS: T('8:00 PM', 4), NH: T('8:00 PM', 4), NJ: T('8:00 PM', 4), PA: T('8:00 PM', 4),
  MI: T('9:00 PM', 6, '8:00 PM', 'most of Michigan closes at 8:00 ET; the western Upper Peninsula at 9:00 ET'),
  TX: T('9:00 PM', 6, '8:00 PM', 'most of Texas closes at 8:00 ET; the El Paso area at 9:00 ET'),
  KS: T('9:00 PM', 6, '8:00 PM', 'most of Kansas closes at 8:00 ET; the western counties at 9:00 ET'),
  AZ: T('9:00 PM', 6), CO: T('9:00 PM', 6), IA: T('9:00 PM', 6), MN: T('9:00 PM', 6), NE: T('9:00 PM', 6), NM: T('9:00 PM', 6), NY: T('9:00 PM', 6), WI: T('9:00 PM', 6),
  MT: T('10:00 PM', 7), NV: T('10:00 PM', 7), CA: T('11:00 PM', 8), WA: T('11:00 PM', 8),
  AK: T('1:00 AM', 10, '12:00 AM', 'most of Alaska closes at midnight ET; the Aleutians at 1:00 ET'),
};
// House districts that sit wholly in a state's earlier zone close at that earlier hour.
const EARLY_DISTRICTS = new Set(['KY-06', 'FL-13', 'FL-14', 'FL-22', 'FL-25', 'FL-27', 'MI-04', 'MI-07', 'MI-10', 'TX-15', 'TX-28', 'TX-34', 'TX-35']);
const ORDER_OF: Record<string, number> = { '6:00 PM': 1, '7:00 PM': 2, '7:30 PM': 3, '8:00 PM': 4, '8:30 PM': 5, '9:00 PM': 6, '10:00 PM': 7, '11:00 PM': 8, '12:00 AM': 9, '1:00 AM': 10 };
// The instant each hour lands (Nov 3, 2026 is Eastern Standard Time, UTC-5), so a reader's browser can show it in their own zone
// (Max, 2026-11-01: "what to watch times need either a timezone or to be adjusted by users location").
export function closeInstant(at: string): string {
  const m = /^(\d{1,2}):(\d\d) (AM|PM)$/.exec(at); if (!m) throw new Error(`closing time not understood: ${at}`);
  const h12 = Number(m[1]) % 12, h = m[3] === 'PM' ? h12 + 12 : h12;
  const day = m[3] === 'AM' && h < 6 ? 4 : 3;   // 12:00 AM and 1:00 AM fall after midnight, on November 4
  return new Date(Date.UTC(2026, 10, day, h + 5, Number(m[2]))).toISOString();
}
export function closeFor(raceId: string): Close | null {
  const [, st, d] = raceId.split('-'); const c = STATE_CLOSE[st]; if (!c) return null;
  if (raceId.endsWith('HOUSE') && c.first && EARLY_DISTRICTS.has(`${st}-${d}`)) return { at: c.first, order: ORDER_OF[c.first] };
  return c;
}
