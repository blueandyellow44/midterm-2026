"""After apply_round.py: the grade line, calls against Undertow (computed, never from memory), oddities since the
previous board (/tmp/prev.json, saved by the round), and AK/KS governor call status for the ballot."""
import json, gzip, sys, urllib.request
P = json.load(open('/tmp/prev.json'))['races']; D = json.load(open('live/results.json')); d = D['derived']
s = json.load(open('data/derived.json'))['signals']['per_race']
ag = [k for k, c in D['races'].items() if c['called'] and s.get('2026-' + k.upper(), {}).get('adjusted_margin') is not None
      and c['called'] != ('D' if s['2026-' + k.upper()]['adjusted_margin'] > 0 else 'R')]
odd = []
for k, c in D['races'].items():
    p = P.get(k)
    if not p: continue
    if c['reporting_pct'] < p['reporting_pct']: odd.append(f"{k} % counted down {p['reporting_pct']:.0f}->{c['reporting_pct']:.0f}")
    if (c['d_pct'] - c['r_pct']) * (p['d_pct'] - p['r_pct']) < 0: odd.append(f"{k} leader flip")
print(f"{d['settled']} graded; Undertow closer {d.get('undertow_closer')}, polls {d.get('polls_closer')}; avg miss Undertow {d['undertow_mae']:.2f} vs polls {d['polls_mae']:.2f}; against Undertow: {ag}; odd: {odd or 'none'}")
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'}
B = 'https://interactives.apelections.org/election-results/data-live/2026-11-03/results/races/'
def get(u):
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=15).read()
    return json.loads(gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b)
for st in ('AK', 'KS'):
    for key, v in get(f'{B}{st}/metadata.json').items():
        if v.get('officeID') == 'G' and v.get('raceTypeID') == 'G':
            sm = get(f'{B}{st}/{key}/summary.json'); win = next((v['candidates'][c['candidateID']] for c in sm['candidates'] if c.get('winner') == 'X'), None)
            print(f"{st}-GOV eevp {sm.get('eevp')} call: {win['last'] + ' ' + win['party'] if win else 'none'}")
