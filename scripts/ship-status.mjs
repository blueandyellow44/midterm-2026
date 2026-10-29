// What is live vs what is only local (Max, 2026-10-28: "jesus dont wrap before deploy!"). Prints the deployed commit,
// the commits after it that are not live, and uncommitted changes. Exit code 2 when anything is unshipped, so a wrap
// or a hook can refuse to call the work done.
import { execSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
const sh = c => execSync(c, { encoding: 'utf8' }).trim();
const head = sh('git rev-parse HEAD');
const dirty = sh('git status --porcelain --untracked-files=no');
if (!existsSync('.deploys/last.json')) { console.log('No deploy recorded yet (.deploys/last.json missing): deploy with npm run deploy.'); process.exit(2); }
const last = JSON.parse(readFileSync('.deploys/last.json', 'utf8'));
const pending = last.commit === head ? [] : sh(`git log --format="%h %s" ${last.commit}..HEAD`).split('\n').filter(Boolean);
console.log(`Live: ${last.commit.slice(0, 7)} (Cloudflare ${last.cloudflare_version}) at ${last.at}; live matched build: ${last.live_matches_build}`);
if (pending.length) console.log(`NOT LIVE: ${pending.length} commit(s) after the deploy:\n  ` + pending.join('\n  '));
if (dirty) console.log('NOT COMMITTED:\n  ' + dirty.split('\n').join('\n  '));
if (!pending.length && !dirty) console.log('Everything committed is live.');
process.exit(pending.length || dirty ? 2 : 0);
