"""One election-night round, no browser (2026-11-04). Runs fetch_official.py (state feeds) and fetch_ap.py (AP feed),
then enters every tracked race whose numbers moved:
  - shares: the state's official count where we read one; AP's count, labeled by its apnews.com source, for races in
    AP_SHARES (states with no usable live official count: Max, 2026-11-04, "Do both"), or for a race the state feed
    does not cover yet that has no entry;
  - reporting: AP's eevp ("% of votes counted"), rounded as AP shows it; called: AP's winner.
Entry rule unchanged: a race enters at 50% counted or an AP call. Called races keep refreshing (lesson 2026-11-04).
Prints what changed; publish with scripts/live/publish.sh."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AP_SHARES = {'wi-gov', 'wi-01-house', 'wi-03-house', 'nj-07-house', 'nh-sen', 'me-sen', 'me-02-house', 'ms-sen', 'al-02-house',
             'mi-sen', 'mi-gov', 'mi-04-house', 'mi-07-house', 'mi-10-house'}
FIRST = {'me-sen', 'ak-sen', 'ak-al-house'}

def run(script):
    out = subprocess.run([sys.executable, str(ROOT / 'scripts/live' / script)], cwd=ROOT, capture_output=True, text=True)
    if out.returncode: print(f'# {script} failed: {out.stderr.strip()[:300]}')
    for l in out.stderr.splitlines():
        if l.startswith('#'): print(l)
    return [l.split('\t') for l in out.stdout.splitlines() if l and not l.startswith('#')]

def main(dry=False):
    official = {r[0]: r for r in run('fetch_official.py')}          # slug d r o tot src note
    ap = {r[0]: r for r in run('fetch_ap.py')}                       # slug eevp called d r o url
    live = json.loads((ROOT / 'live/results.json').read_text())['races']
    for slug, (_, eevp, called, ad, ar, ao, url) in sorted(ap.items()):
        if eevp in ('None', '') or ad == 'None': continue
        rep = round(float(eevp)); call = None if called == '-' else called
        if rep < 50 and not call: continue
        cur = live.get(slug)
        if slug in official: d, r, o, src = official[slug][1], official[slug][2], official[slug][3], official[slug][5]
        else:
            # No state feed for this race: AP's current count, labeled AP on the page. Never pair an old state count with
            # AP's newer % counted (the stale-count mistake of 2026-11-03); the state's own feed replaces it once wired.
            d, r, o, src = ad, ar, ao, url
        if cur and (float(d), float(r), float(rep), call) == (cur['d_pct'], cur['r_pct'], cur['reporting_pct'], cur['called']): continue
        args = [sys.executable, 'scripts/live/set_result.py', slug, '--d', d, '--r', r, '--other', o, '--reporting', str(rep), '--source', src]
        if call: args += ['--called', call]
        if slug in FIRST: args += ['--round', 'FIRST']
        tag = 'AP' if 'apnews.com' in src else 'state'
        if dry: print('would enter', tag, ' '.join(args[2:])); continue
        res = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        print(f'[{tag}]', (res.stdout.splitlines() or [res.stderr.strip()])[0])

if __name__ == '__main__': main(dry='--dry' in sys.argv)
