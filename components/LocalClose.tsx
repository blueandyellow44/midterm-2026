'use client';
import { useEffect, useState } from 'react';

// Closing times in the reader's own zone (Max, 2026-11-01: "why dont we just have the browser show the local time?").
// The static page renders Eastern with its label; the browser swaps in local time with the zone abbreviation, so a
// screenshot shared across zones still says which clock it is. A day that differs from Nov 3 carries its weekday.
const ET = 'America/New_York';
export function localClock(iso: string, zone?: string): string {
  const at = new Date(iso);
  const time = at.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZoneName: 'short', timeZone: zone });
  const day = at.toLocaleDateString('en-US', { day: 'numeric', timeZone: zone });
  return day === '3' ? time : `${at.toLocaleDateString('en-US', { weekday: 'short', timeZone: zone })} ${time}`;
}
export function LocalClose({ iso, et }: { iso: string; et: string }) {
  const [text, setText] = useState(et);
  useEffect(() => { setText(localClock(iso)); }, [iso]);
  return <>{text}</>;
}
// A note such as "most of Florida closes at 7:00 ET; the Panhandle at 8:00 ET": each "H:MM ET" or "midnight ET" becomes local.
const TOKEN = /(\d{1,2}):(\d\d) ET|midnight ET/g;
export function noteInstant(h: number, min: number): string {   // note hours run 6 PM to 1 AM Eastern (UTC-5)
  const h24 = h === 12 ? 0 : h <= 5 ? h : h + 12, day = h24 < 6 ? 4 : 3;
  return new Date(Date.UTC(2026, 10, day, h24 + 5, min)).toISOString();
}
export function LocalNote({ text }: { text: string }) {
  const [out, setOut] = useState(text);
  useEffect(() => { setOut(text.replace(TOKEN, (m, h, mm) => localClock(m.startsWith('midnight') ? noteInstant(12, 0) : noteInstant(Number(h), Number(mm))))); }, [text]);
  return <>{out}</>;
}
