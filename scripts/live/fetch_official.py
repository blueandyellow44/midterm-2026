"""Election-night official counts straight from the states' own results feeds (2026-11-03), no browser.
Max: "There's got to be a faster way to check results than via chrome". Prints full-ballot shares per tracked slug,
ready for set_result.py. Sources are the same official pages entered by hand tonight; only the transport changed.
The feeds refuse a bare client (CloudFront 403), so requests carry a browser user-agent."""
from __future__ import annotations
import json, re, subprocess, sys

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
def get(url):
    # curl, not urllib: this Python has no CA bundle installed, and curl uses the system's.
    return subprocess.run(['curl', '-sf', '--compressed', '--max-time', '15', '-A', UA, url], check=True, capture_output=True, text=True).stdout

# Clarity ENR: state/election id, and contest-name -> slug.
CLARITY = {
    'SC/127300': {r'^U\.S\. Senate$': 'sc-sen', r'^U\.S\. House of Representatives, District 1$': 'sc-01-house'},
    'IA/127077': {r'^United States Senator$': 'ia-sen', r'^Governor and Lt\. Governor$': 'ia-gov',
                  r'^United States Representative District 1$': 'ia-01-house', r'^United States Representative District 2$': 'ia-02-house',
                  r'^United States Representative District 3$': 'ia-03-house'},
    'CO/127407': {r'^Representative to the 120th United States Congress - District 4$|^District 4$': 'co-04-house',
                  r'^Representative to the 120th United States Congress - District 5$|^District 5$': 'co-05-house',
                  r'^Representative to the 120th United States Congress - District 8$|^District 8$': 'co-08-house'},
}
NC = {'1383': 'nc-sen', '1369': 'nc-01-house', '1379': 'nc-11-house'}

def shares(rows):
    """rows: [(party, votes)] for one contest -> (d, r, other) percent of all votes cast for the office."""
    tot = sum(v for _, v in rows)
    if not tot: return None
    d = sum(v for p, v in rows if p in ('DEM', 'D')); r = sum(v for p, v in rows if p in ('REP', 'R'))
    D, R = round(100 * d / tot, 2), round(100 * r / tot, 2)
    return D, R, round(100 - D - R, 2), tot

def clarity(out):
    for sid, want in CLARITY.items():
        base = f'https://results.enr.clarityelections.com/{sid}'
        ver = get(f'{base}/current_ver.txt').strip()
        for c in json.loads(get(f'{base}/{ver}/json/en/summary.json')):
            for pat, slug in want.items():
                if re.search(pat, ' '.join(c['C'].split())) and slug not in out:  # the feeds double-space some names
                    s = shares(list(zip(c['P'], c['V'])))
                    if s: out[slug] = (*s, f'{base}/web.345435/#/summary', f"{c['C']} PR {c.get('PR')}/{c.get('TP')}")

def ncsbe(out):
    rows = json.loads(get('https://er.ncsbe.gov/enr/20261103/data/results_0.txt'))
    for gid, slug in NC.items():
        rr = [(x['pty'], int(x['vct'])) for x in rows if x['gid'] == gid]
        s = shares(rr)
        if s: out[slug] = (*s, f'https://er.ncsbe.gov/?election_dt=11/03/2026&county_id=0&office=FED&contest={gid}', f'gid {gid}')

if __name__ == '__main__':
    out = {}
    for f in (clarity, ncsbe):
        try: f(out)
        except Exception as e: print(f'# {f.__name__} failed: {e}', file=sys.stderr)
    for slug, (d, r, o, tot, src, note) in sorted(out.items()):
        print(f'{slug}\t{d}\t{r}\t{o}\t{tot}\t{src}\t{note}')
