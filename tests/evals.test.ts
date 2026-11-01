// The eval grader and the doctored-page mutations, proven on known-bad inputs before the live suite is trusted
// (tests/evals/run.mjs). A grader that cannot fail measures nothing; a mutation that cannot bite proves nothing.
import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import { grade, validateCases } from './evals/grade.mjs';
import { htmlToText, mutate, MUTATIONS, pageText, ROOT } from './evals/page-text.mjs';

const cases = JSON.parse(readFileSync(new URL('./evals/cases.json', import.meta.url), 'utf8'));
const byId = (id: string) => cases.find((c: any) => c.id === id);

describe('grader', () => {
  it('every case is well formed and checks something', () => {
    expect(() => validateCases(cases)).not.toThrow();
    expect(() => validateCases([{ id: 'x', page: '/', ask: 'q', expect: {} }])).toThrow(/checks nothing/);
    expect(() => validateCases([cases[0], cases[0]])).toThrow(/duplicate/);
  });
  it('fails an empty answer', () => {
    expect(grade(byId('senate-control'), '')).toMatchObject({ pass: false, evidence: ['no answer', expect.stringMatching(/does not match/)] });
  });
  it('says: the right number passes, the wrong number fails and names the pattern', () => {
    expect(grade(byId('senate-control'), 'The site gives Democrats a 91% chance.').pass).toBe(true);
    const g = grade(byId('senate-control'), 'The site gives Democrats a 78% chance.');
    expect(g.pass).toBe(false);
    expect(g.evidence[0]).toMatch(/\/91\/i/);
  });
  it('says as a list: every pattern must hold, and the missing one is named', () => {
    expect(grade(byId('nc-two-numbers'), 'Polls: Cooper +9.5. Undertow: Cooper +14.3.').pass).toBe(true);
    const g = grade(byId('nc-two-numbers'), 'Polls say Cooper +9.5.');
    expect(g.pass).toBe(false);
    expect(g.evidence).toEqual([expect.stringMatching(/14\\\.3/)]);
  });
  it('never_says: the forbidden direction fails even when the required word is present', () => {
    const g = grade(byId('thesis-direction'), 'Republicans will beat their polls, not Democrats.');
    expect(g.pass).toBe(false);
    expect(g.evidence).toEqual([expect.stringMatching(/matches/)]);
  });
  it('an admission that the page does not say fails a fact case even when a stray word matches', () => {
    const g = grade(byId('tie-rule'), 'The page lists Ricketts (R) as even, but it does not say who controls a 50-50 Senate.');
    expect(g.pass).toBe(false);
    expect(g.evidence).toEqual(['answer says the page does not say']);
    expect(grade(byId('tie-rule'), "The page doesn't describe a 50-50 Senate; it shows D 54, R 45.").pass).toBe(false);
    expect(grade(byId('absent-race'), 'The page does not mention a Wyoming governor race.').pass).toBe(true);
  });
  it('not_only: a bare word fails', () => {
    const c = { id: 't', page: '/', ask: 'q', expect: { not_only: 'yes' } };
    expect(grade(c, 'Yes.').pass).toBe(false);
    expect(grade(c, 'Yes, the freeze is November 2.').pass).toBe(true);
  });
  it('judge is not a deterministic check: a passing answer still passes here, so the runner must ask the judge', () => {
    expect(grade(byId('lead-not-odds'), 'That lead of 14.3 points is the chance Cooper wins.')).toMatchObject({ pass: true });
  });
});

describe('page text', () => {
  it('strips scripts, styles and tags and keeps the words', () => {
    const t = htmlToText('<html><head><style>p{}</style><script>var x="hidden";</script></head><body><h1>Undertow</h1><p>My bet:&nbsp;Democrats &amp; co.</p><div>Next<br>line</div></body></html>');
    expect(t).toBe('Undertow\nMy bet: Democrats & co.\nNext\nline');
    expect(t).not.toMatch(/hidden/);
  });
  it('a mutation with no target on the page throws instead of silently passing', () => {
    expect(() => mutate('nothing to see', 'flip-bet')).toThrow(/cannot bite/);
    expect(() => mutate('x', 'no-such')).toThrow(/unknown mutation/);
  });
  it('each mutation changes the text it targets', () => {
    for (const [name, rules] of Object.entries(MUTATIONS)) {
      const page = rules.map(([find]) => `line ${find} end`).join('\n');
      const out = mutate(page, name);
      expect(out, name).not.toBe(page);
      for (const [find, repl] of rules) if (repl && !repl.includes(find)) expect(out, `${name}: ${find}`).not.toContain(find);
    }
  });
  const built = existsSync(`${ROOT}/index.html`);
  it.skipIf(!built)('the built home page carries the thesis and the direction anchors, and every mutation bites on a real page', () => {
    const home = pageText('/');
    expect(home).toContain('My bet: Democrats beat their polls again in November');
    expect(home).toContain('polls under R by 5.5');
    expect(mutate(home, 'flip-bet')).toContain('My bet: Republicans beat');
    expect(mutate(home, 'strip-direction')).not.toContain('polls under R by 5.5');
    expect(mutate(home, 'drop-tie-rule')).not.toContain('tie goes to R');
    expect(mutate(pageText('/scoreboard/'), 'drop-rcv-note')).not.toMatch(/ranked|first-round/i);
    const nc = mutate(pageText('/race/nc-sen/'), 'hide-freeze');
    expect(nc).not.toMatch(/nov(ember)?\.? ?2\b/i);
  });
  it.skipIf(!built)('every case names a built page', () => {
    for (const c of cases) expect(existsSync(`${ROOT}${c.page}index.html`), c.page).toBe(true);
  });
});
