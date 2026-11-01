// Reader-facing evals for the built site: every case hands one built page's visible text to a reader with no project
// context, through Claude Code headless (`claude -p`) on the signed-in person's plan, no tools, no API key, and the
// deterministic grader decides whether the page made the fact plain. A judge (also `claude -p`) runs only for the cases
// that name one, after the checks passed. This is the model-facing twin of the QA sweep: the sweep checks geometry
// and arithmetic, this checks meaning, the gap the 2026-10-31 cold read found.
//
//   npm run build:cloudflare        (the pages come from .open-next/assets)
//   npm run test:evals
//
// Flags: --only <id,id>   --concurrency <n> (default 3)   --model <alias> (default sonnet)
//        --mutate flip-bet | strip-direction | hide-freeze | drop-tie-rule | drop-rcv-note   (known-bad pages: the suite must FAIL)
//        --list   (print the cases and the size of each page's text, no model calls)
// QA_ROOT=<another build> runs the suite against that build (a backup, to prove it fails on an older page).
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { grade, validateCases } from './grade.mjs';
import { pageText, MUTATIONS, ROOT } from './page-text.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const arg = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback; };
const MODEL = arg('model', 'sonnet');
const CONCURRENCY = Math.max(1, Number(arg('concurrency', '3')));
const ONLY = arg('only', '').split(',').filter(Boolean);
const MUTATE = arg('mutate', '');
const LIST = process.argv.includes('--list');
if (MUTATE && !MUTATIONS[MUTATE]) { console.error(`unknown mutation ${MUTATE}; known: ${Object.keys(MUTATIONS).join(', ')}`); process.exit(2); }

const SYSTEM = 'You are a first-time visitor reading one page of a website about the 2026 US midterm elections. You know nothing about the site beyond the page text you are given. Answer the question only from that text, in one or two short sentences. If the page does not say, say that it does not say. Never guess.';

const cases = JSON.parse(readFileSync(join(here, 'cases.json'), 'utf8'));
validateCases(cases);
const todo = ONLY.length ? cases.filter(c => ONLY.includes(c.id)) : cases;

// A mutation only applies to the pages that carry its target; the other pages are read as built.
const texts = new Map();
function text(route) {
  if (!texts.has(route)) {
    let t;
    try { t = pageText(route, { mutation: MUTATE }); } catch (e) { if (MUTATE && /cannot bite/.test(String(e))) t = pageText(route); else throw e; }
    texts.set(route, t);
  }
  return texts.get(route);
}

if (LIST) {
  for (const c of todo) console.log(`${c.id.padEnd(24)} ${c.page.padEnd(22)} ${String(text(c.page).length).padStart(6)} chars  ${c.ask}`);
  process.exit(0);
}

function claude(prompt, stdin, extra = []) {
  return new Promise((resolve, reject) => {
    const args = ['-p', prompt, '--output-format', 'json', '--model', MODEL, '--max-turns', '1', '--tools', '', '--setting-sources', '', '--no-session-persistence', '--system-prompt', SYSTEM, ...extra];
    const p = spawn('claude', args, { cwd: here, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1' } });
    let out = ''; let err = '';
    p.stdout.on('data', d => (out += d));
    p.stderr.on('data', d => (err += d));
    p.on('error', reject);
    p.on('close', () => {
      let r = {};
      try { r = JSON.parse(out); } catch { r = {}; }
      const u = r.usage ?? {};
      resolve({ answer: typeof r.result === 'string' ? r.result : '', usage: { input: u.input_tokens ?? 0, output: u.output_tokens ?? 0, cacheRead: u.cache_read_input_tokens ?? 0, cost: r.total_cost_usd ?? 0 }, stderr: err });
    });
    p.stdin.end(stdin);
  });
}

async function judge(question, answer) {
  const prompt = `Question about an assistant's answer: ${question}\n\nThe answer:\n"""\n${answer.slice(0, 6000)}\n"""\n\nReply with exactly one word: yes or no.`;
  const r = await claude(prompt, '', ['--system-prompt', 'You answer yes or no.']);
  const t = r.answer.trim().toLowerCase();
  return { yes: /^yes\b/.test(t), raw: t.slice(0, 40), usage: r.usage };
}

console.log(`Undertow reader evals: ${todo.length} case(s), model ${MODEL}, pages from ${ROOT}${MUTATE ? `, MUTATION ${MUTATE}` : ''}.`);
let failures = 0;
const total = { input: 0, output: 0, cacheRead: 0, cost: 0 };
const add = u => { for (const k of Object.keys(total)) total[k] += u[k]; };
const started = Date.now();
const queue = [...todo];
async function worker() {
  for (let c = queue.shift(); c; c = queue.shift()) {
    const t0 = Date.now();
    let line;
    try {
      const run = await claude(`Question: ${c.ask}\n\nThe page text follows.`, `PAGE ${c.page}\n\n${text(c.page)}`);
      add(run.usage);
      const g = grade(c, run.answer);
      let verdict = g.pass; let why = g.evidence;
      if (verdict && c.expect.judge) {
        const j = await judge(c.expect.judge, run.answer);
        add(j.usage);
        if (j.yes) { verdict = false; why = [`judge said yes: ${c.expect.judge.slice(0, 80)}…`]; } else why = [`judge said ${j.raw || 'no'}`];
      }
      if (!verdict) failures++;
      line = `${verdict ? 'PASS' : 'FAIL'}  ${c.id}  [${Math.round((Date.now() - t0) / 1000)}s]\n      page: ${c.page}  ask: ${c.ask}\n      answer: ${run.answer.replace(/\s+/g, ' ').slice(0, 240)}${why.length ? `\n      ${why.join('; ')}` : ''}${run.stderr.trim() && !run.answer ? `\n      stderr: ${run.stderr.trim().slice(0, 200)}` : ''}`;
    } catch (e) {
      failures++;
      line = `FAIL  ${c.id}  run error: ${e instanceof Error ? e.message : e}`;
    }
    console.log(line);
  }
}
await Promise.all(Array.from({ length: Math.min(CONCURRENCY, todo.length) }, worker));

console.log(`\n${todo.length - failures} passed, ${failures} failed, ${Math.round((Date.now() - started) / 1000)}s.`);
console.log(`Tokens: ${total.input.toLocaleString()} in (${total.cacheRead.toLocaleString()} from cache), ${total.output.toLocaleString()} out. API-equivalent estimate ${total.cost ? `$${total.cost.toFixed(2)}` : 'none'}; this ran on the account's Claude plan, not an API key.`);
if (MUTATE) console.log(`Mutation ${MUTATE}: ${failures ? 'the suite caught it' : 'NOT CAUGHT: the suite did not fail under this mutation'}.`);
process.exit(MUTATE ? (failures ? 0 : 1) : failures ? 1 : 0);
