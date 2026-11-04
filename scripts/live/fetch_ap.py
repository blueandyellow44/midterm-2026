"""AP's own election-night feed, read directly (2026-11-04; Max: "stop using the browser to get results!!").
interactives.apelections.org/election-results/data-live/<date>/results/races/<ST>/metadata.json lists a state's races
(office, seat, call status, candidates with party); .../<raceKey>/summary.json carries each candidate's votes, the
winner flag and eevp (AP's "% of votes counted"). Responses are gzipped. Prints, per tracked slug: eevp, AP's call,
and full-ballot D/R/other shares. The shares are for races whose state posts no live official count (Max: "Do both");
every other race keeps the state's own numbers and uses only the eevp and call from here."""
from __future__ import annotations
import gzip, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'}
BASE = 'https://interactives.apelections.org/election-results/data-live/2026-11-03/results/races/'
PAGE = 'https://apnews.com/projects/elections-2026/'
# The model's D slot when the leading non-Republican is not a Democrat (analysis/weight.py PARTISAN_INDEPENDENT_D, house races.json).
D_SLOT_NAME = {'ne-sen': 'Osborn', 'ak-al-house': 'Hill'}
SPECIAL = {'oh-sen': 'oh-sen-special', 'fl-sen': 'fl-sen-special'}
STATE_NAME = {'AK':'alaska','AL':'alabama','AZ':'arizona','CA':'california','CO':'colorado','FL':'florida','GA':'georgia','IA':'iowa','KS':'kansas','KY':'kentucky','ME':'maine','MI':'michigan','MN':'minnesota','MS':'mississippi','MT':'montana','NC':'north-carolina','NE':'nebraska','NH':'new-hampshire','NJ':'new-jersey','NM':'new-mexico','NV':'nevada','NY':'new-york','OH':'ohio','PA':'pennsylvania','SC':'south-carolina','TX':'texas','VA':'virginia','WA':'washington','WI':'wisconsin','OK':'oklahoma','OR':'oregon','VT':'vermont'}

def get(url):
    b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15).read()
    return json.loads(gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b)

def slug_for(st, v):
    o = v['officeID']; s = st.lower()
    if o == 'S': return SPECIAL.get(f'{s}-sen', f'{s}-sen')
    if o == 'G': return f'{s}-gov'
    if o == 'H':
        seat = str(v.get('seatNum') or '')
        return f'{s}-al-house' if seat in ('', '0', '1') and st == 'AK' else f'{s}-{int(seat):02d}-house'
    return None

def race_rows(st, wanted):
    meta = get(f'{BASE}{st}/metadata.json'); out = []
    for key, v in meta.items():
        if v.get('raceTypeID') != 'G': continue
        slug = slug_for(st, v)
        if slug not in wanted: continue
        cands = v.get('candidates') or {}  # keyed by candidateID
        summ = get(f'{BASE}{st}/{key}/summary.json')
        votes = [(cands.get(c['candidateID'], {}), c.get('voteCount', 0), c.get('winner') == 'X') for c in summ['candidates']]
        tot = sum(n for _, n, _ in votes)
        if not tot: out.append((slug, summ.get('eevp'), None, None, None, None)); continue
        dname = D_SLOT_NAME.get(slug)
        isd = (lambda c: c.get('last') == dname) if dname else (lambda c: c.get('party') == 'Dem')
        d = sum(n for c, n, _ in votes if isd(c))
        # R slot: the leading Republican (Alaska's first round can carry two), every other candidate is 'other'
        r = max((n for c, n, _ in votes if c.get('party') == 'GOP' and not isd(c)), default=0)
        win = next((c for c, _, w in votes if w), None)
        called = None if not win else ('D' if isd(win) else 'R' if win.get('party') == 'GOP' else None)
        D, R = round(100 * d / tot, 2), round(100 * r / tot, 2)
        out.append((slug, summ.get('eevp'), called, D, R, round(100 - D - R, 2)))
    return out

def page_url(slug):
    st = slug[:2].upper(); n = STATE_NAME[st]
    if slug.endswith('-house'):
        seat = slug.split('-')[1]; return f'{PAGE}{n}-us-house-results/#{1 if seat == "al" else int(seat)}'
    return f'{PAGE}{n}-{"governor" if slug.endswith("-gov") else "us-senate"}-results/'

if __name__ == '__main__':
    sys.path.insert(0, 'analysis'); import weight
    wanted = {r.replace('2026-', '').lower() for r in weight.ALL_RACES}
    states = sorted({s[:2].upper() for s in wanted})
    with ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda st: (st, race_rows(st, wanted)), states))
    for st, rows in res:
        for slug, eevp, called, D, R, O in sorted(rows):
            print(f'{slug}\t{eevp}\t{called or "-"}\t{D}\t{R}\t{O}\t{page_url(slug)}')
