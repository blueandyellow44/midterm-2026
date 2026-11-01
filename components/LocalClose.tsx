'use client';
import { useEffect, useState } from 'react';

// The reader's own clock for a poll-closing hour. Static pages render Eastern only; the browser adds its zone after load,
// and says nothing when the reader is already on Eastern time (Max, 2026-11-01).
const ET = 'America/New_York';
export function LocalClose({ iso }: { iso: string }) {
  const [text, setText] = useState('');
  useEffect(() => {
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const at = new Date(iso);
    const opts: Intl.DateTimeFormatOptions = { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' };
    const local = at.toLocaleTimeString('en-US', opts), east = at.toLocaleTimeString('en-US', { ...opts, timeZone: ET });
    if (!zone || zone === ET || local === east) return;
    const dayOf = (tz?: string) => at.toLocaleDateString('en-US', { timeZone: tz, day: 'numeric' });
    const otherDay = dayOf() !== dayOf(ET) ? `${at.toLocaleDateString('en-US', { weekday: 'short' })} ` : '';
    setText(`${otherDay}${local} your time`);
  }, [iso]);
  return text ? <span className="tonight-local">{text}</span> : null;
}
