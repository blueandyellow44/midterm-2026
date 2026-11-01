// The page a reader gets: the visible text of one built route, extracted from .open-next/assets exactly as served.
// QA_ROOT points at another build (a backup) to run the suite against a known-bad site, the same switch the QA sweep
// uses. A mutation doctors the text the way a real regression would (the labels the 2026-10-31 cold read flagged), so
// the suite can be proven to FAIL on a bad page before it is trusted; a mutation whose target text is absent throws,
// because a mutation that cannot bite proves nothing.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = process.env.QA_ROOT || join(fileURLToPath(new URL('../..', import.meta.url)), '.open-next/assets');

export function htmlToText(html) {
  let h = html.replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<style[\s\S]*?<\/style>/gi, '').replace(/<noscript[\s\S]*?<\/noscript>/gi, '');
  h = h.replace(/<(br|\/p|\/div|\/li|\/h[1-6]|\/tr|\/section|\/article|\/header|\/footer|\/dt|\/dd|\/figcaption|\/summary|\/caption|\/th|\/td|\/label|\/button)[^>]*>/gi, '\n');
  h = h.replace(/<[^>]+>/g, ' ');
  h = h.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
  return h.split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter(Boolean).join('\n');
}

/** Every mutation is a list of [find, replace]; each find must occur in the page it is applied to. */
export const MUTATIONS = {
  // The thesis names the wrong party: the direction claim is the one sentence the site exists for.
  'flip-bet': [['My bet: Democrats beat their polls again in November', 'My bet: Republicans beat their polls again in November']],
  // The pre-2026-11-01 labels: a bare number pointing at a letter, slider ends that read as who wins.
  'strip-direction': [['polls under R by 5.5', '5.5 toward R'], ['polls under R by 4.2', '4.2 toward R'], ['polls under R by 2.5', '2.5 toward R'], ['polls under R by 1.3', '1.3 toward R'], ['polls under D by 1.9', '1.9 toward D'], ['polls under D by 7.3', '7.3 toward D'], ['◀ Polls under R Polls under D ▶', '◀ Republicans Democrats ▶']],
  // The freeze date gone from the race page.
  'hide-freeze': [['freezes Nov 2', ''], ['both readings are frozen on November 2 and graded against the results', 'both readings are graded against the results'], ['Frozen on November 2 and graded against certified results', 'Graded against certified results']],
  // Two sentence losses: the tie rule gone from the chamber line, the ranked-choice note gone from the scoreboard.
  'drop-tie-rule': [['; a 50-50 tie goes to R', '']],
  'drop-rcv-note': [[' Maine and Alaska use ranked-choice voting; they are scored on the first-round count, the same full-ballot basis as their polling averages.', '']],
};

export function mutate(text, name) {
  const rules = MUTATIONS[name];
  if (!rules) throw new Error(`unknown mutation ${name}; known: ${Object.keys(MUTATIONS).join(', ')}`);
  let out = text;
  let bit = 0;
  for (const [find, repl] of rules) if (out.includes(find)) { out = out.split(find).join(repl); bit++; }
  if (!bit) throw new Error(`mutation ${name} found none of its targets on this page; it cannot bite`);
  return out;
}

export function pageText(route, { mutation = '', maxChars = Number(process.env.EVAL_MAX_CHARS || 24000) } = {}) {
  const file = join(ROOT, route, 'index.html');
  if (!existsSync(file)) throw new Error(`no built page at ${file}: run npm run build:cloudflare first`);
  let t = htmlToText(readFileSync(file, 'utf8'));
  if (mutation) t = mutate(t, mutation);
  if (t.length > maxChars) t = t.slice(0, maxChars) + '\n[page text truncated here]';
  return t;
}
