import { surname } from '../lib/format';
import { it, expect } from 'vitest';
it('surname skips generational suffixes', () => { expect(surname('Nick Begich III')).toBe('Begich'); expect(surname('Ted Cruz Jr.')).toBe('Cruz'); expect(surname('Roy Cooper')).toBe('Cooper'); expect(surname('Cher')).toBe('Cher'); });
