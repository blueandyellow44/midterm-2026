'use client';
import { useEffect, useState } from 'react';

// Freeze is 2026-11-02 00:00 Pacific (07:00 UTC). Static pages render the build-time count; the client corrects it.
const FREEZE_MS = Date.UTC(2026, 10, 2, 7, 0, 0);
const DAY_MS = 86_400_000;

function label(now: number): string {
  const left = FREEZE_MS - now;
  if (left <= 0) return 'Frozen. Graded after the results.';
  const days = Math.ceil(left / DAY_MS);
  return days === 1 ? 'Freezes tomorrow' : `Freezes in ${days} days`;
}

export function FreezeCountdown({ builtAt }: { builtAt: number }) {
  const [text, setText] = useState(() => label(builtAt));
  useEffect(() => { setText(label(Date.now())); }, []);
  return <span className="freeze-countdown">{text}</span>;
}
