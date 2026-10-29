// Deploy and prove it (Max, 2026-10-28: "jesus dont wrap before deploy!"). Runs the static checks, deploys, records
// which commit is live in .deploys/ (deploys.jsonl is the history, last.json the current state), then byte-compares
// the live HTML of every route with the build. Exit code 1 if any live page differs. scripts/ship-status.mjs reads the
// record so a wrap can see commits that are not live yet.
import { execSync, spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, appendFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const ORIGIN = process.env.DEPLOY_ORIGIN || 'https://midtermundertow.com';
const sh = c => execSync(c, { encoding: 'utf8' }).trim();
// --record-existing <cloudflare version> <commit>: record a deploy that already happened (no wrangler run), byte-checked.
const existing = process.argv[2] === '--record-existing' ? process.argv[3] : null;
if (existing && !process.argv[4]) throw new Error('--record-existing needs <cloudflare version> <commit that was deployed>');
if (!existing && sh('git status --porcelain --untracked-files=no')) throw new Error('Commit first: the deploy record names a commit, so the tree must be clean');
const commit = sh(`git rev-parse ${existing ? process.argv[4] : 'HEAD'}`), subject = sh(`git log -1 --format=%s ${commit}`);
execSync('node scripts/verify-static.mjs', { stdio: 'inherit' });
let version = existing;
if (!existing) {
  const run = spawnSync('npx', ['wrangler', 'deploy'], { encoding: 'utf8' });
  process.stdout.write(run.stdout || ''); process.stderr.write(run.stderr || '');
  if (run.status !== 0) throw new Error('wrangler deploy failed; nothing recorded');
  version = ((run.stdout || '').match(/Current Version ID:\s*(\S+)/) || [])[1] || null;
}
const release = JSON.parse(readFileSync('data/derived.json', 'utf8')).release_id;
const routes = JSON.parse(readFileSync('.next/csp-routes.json', 'utf8')).map(r => r.route).filter(r => r !== '/404/');
const sha = b => createHash('sha256').update(b).digest('hex');
// A route that differs right after upload is usually the edge still propagating (2026-10-29: 12 of 75 routes
// differed at +10 s and all 75 matched at +40 s), so a mismatch is rechecked up to three times, 20 s apart.
const check = async route => {
  const local = readFileSync(`.open-next/assets${route === '/' ? '/' : route}index.html`);
  const live = Buffer.from(await (await fetch(`${ORIGIN}${route}?deploy-check=${Date.now()}`, { signal: AbortSignal.timeout(15000) })).arrayBuffer());
  return sha(local) === sha(live);
};
let mismatched = [];
for (const route of routes) if (!(await check(route))) mismatched.push(route);
for (let attempt = 1; mismatched.length && attempt <= 3; attempt++) {
  console.log(`${mismatched.length} route(s) differ; waiting 20 s for the edge (recheck ${attempt} of 3)`);
  await new Promise(r => setTimeout(r, 20000));
  const still = [];
  for (const route of mismatched) if (!(await check(route))) still.push(route);
  mismatched = still;
}
const rec = { at: new Date().toISOString(), commit, subject, cloudflare_version: version, release_id: release, routes_checked: routes.length, live_matches_build: mismatched.length === 0, mismatched };
mkdirSync('.deploys', { recursive: true });
appendFileSync('.deploys/deploys.jsonl', JSON.stringify(rec) + '\n');
writeFileSync('.deploys/last.json', JSON.stringify(rec, null, 2) + '\n');
console.log(`${existing ? "Recorded existing deploy of" : "Deployed"} ${commit.slice(0, 7)} as Cloudflare ${version}; live matches build on ${routes.length - mismatched.length}/${routes.length} routes.`);
if (mismatched.length) { console.error('LIVE DIFFERS from build on: ' + mismatched.join(', ')); process.exitCode = 1; }
