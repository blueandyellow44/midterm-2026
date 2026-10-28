#!/usr/bin/env python3
"""Build districts2014.csv from the three raw inputs in raw/.

Inputs (all in raw/, provenance in baselines.json):
  mit-1976-2024-house.csv                  MEDSL House returns, 2014 general rows used
  downballot-pres2012-on-2012-2014-lines.csv  Obama/Romney shares by 2012-2014 district (Daily Kos Elections / The Downballot)
  wikipedia-2014-house-elections.wikitext  incumbent status, winner marker, candidate pct cross-check

Rules copied from ../swing-test-2018/derive_districts2018.py (itself from ../swing-test-2022/). Sign: D minus R, percentage points.
Run from anywhere: python3 derive_districts2014.py
"""
import csv, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
OUT = os.path.join(HERE, 'districts2014.csv')

EXCL = {'BLANK', 'BLANKS', 'BLANK VOTES', 'VOID', 'OVERVOTES', 'UNDERVOTES', 'EXHAUSTED BALLOT',
        'BLANK VOTE', 'OVER VOTE', 'BLANK VOTE/VOID VOTE/SCATTERING'}  # 2014 spellings (HI, ME, MA, NY, WY)
# MEDSL 'OTHER' rows (MA, ME, OR) are scattered write-ins: kept in the denominator, credited to no party
WRITEIN_ROWS = {'OTHER'}
DP = {'DEMOCRAT', 'DEMOCRATIC', 'DEMOCRATIC-FARMER-LABOR', 'DEMOCRATIC-NPL', 'DEMOCRATIC-NONPARTISAN LEAGUE'}
RP = {'REPUBLICAN'}
# Wikipedia's 2014 page mixes postal codes and full state names in its ushr templates
STATE_FIX = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
             'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
             'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
             'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
             'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
             'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
             'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
             'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
             'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
             'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'}
# Louisiana runoff seats where MEDSL's two runoff candidates carry December totals (see notes in the rows)
LA_MIXED = {'LA-05': ('RALPH LEE ABRAHAM', '\\"JAMIE\\" MAYO'), 'LA-06': ('GARRET GRAVES', 'EDWIN EDWARDS')}
SRC_PRES = 'DKE/Downballot 2012 pres on 2012-2014 lines (Google Sheet 1xn6nCNM..., shares rounded 0.1)'
SRC_HOUSE = 'MEDSL U.S. House 1976-2024 (2014 general)'


def dkey(st, d):
    st = STATE_FIX.get(st, st)
    return st + '-' + ('AL' if d in ('0', 'AL') else d.zfill(2))


def nm(c):
    return c.replace('\\"', '').title()


def strip_links(s):
    s = re.sub(r'<ref.*?(</ref>|/>)', '', s)
    s = re.sub(r'\{\{[Ss]ortname\|([^|}]+)\|([^|}]+)[^}]*\}\}', r'\1 \2', s)
    s = re.sub(r'\{\{ushr\|([A-Z]{2})\|(\w+)\|C\}\}', r'\1-\2', s)
    s = re.sub(r'\{\{[Ss]mall\|([^}]*)\}\}', r'\1', s)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)


def load_wikipedia():
    t = open(os.path.join(RAW, 'wikipedia-2014-house-elections.wikitext')).read()
    t = t[t.find('== Alabama =='):]
    parts = re.split(r'\n!\s*[^\n{]*\{\{ushr\|([A-Za-z ]+)\|(\w+)\|[^}]*\}\}', t)
    rows = {}
    for i in range(1, len(parts), 3):
        body = re.split(r'\n\|\}|\n==', parts[i + 2])[0]
        rows[dkey(parts[i], parts[i + 1])] = body
    return rows


def wp_candidates(body, november_only=True):
    # Louisiana rows list the November open primary, then the December runoff; keep the November part only
    if november_only:
        body = body.split("'''Runoff:'''")[0]
    out = []
    for line in body.split('\n'):
        if 'Party stripe' not in line:
            continue
        line = re.sub(r'<ref.*?(</ref>|/>)', '', line)
        line = re.sub(r'\{\{efn.*$', '', line)
        m = re.search(r'\(([^()]+)\)\s*\'*\s*([\d.]+)\s*%', line)
        if m:
            out.append((m.group(1).strip(), float(m.group(2)), '{{Aye}}' in line))
    return out


def is_d(label): return label in ('Democratic', 'DFL', 'Democratic-NPL', 'Undeclared/Democratic')
def is_r(label): return label == 'Republican'


def wp_margin(body):
    c = wp_candidates(body)
    return sum(p for n, p, a in c if is_d(n)) - sum(p for n, p, a in c if is_r(n))


def wp_winner(body):
    w = [n for n, p, a in wp_candidates(body, november_only=False) if a]  # winner marker sits on the runoff line in LA
    if not w: return ''
    return 'D' if is_d(w[0]) else 'R' if is_r(w[0]) else 'OTHER'


def wp_incumbents(body):
    incs = []
    for s in body.split('\n|-'):
        mem = re.search(r'(?m)^\|\s*(\{\{[Ss]ortname\|[^}]+\}\}|\[\[[^\]]+\]\])([^\n]*)', s)
        party = re.search(r'\{\{[Pp]arty shading/(?:Text/(Republican|Democratic)|(Minnesota Democratic-Farmer-Labor))\}\}', s)
        status = re.search(r'(Incumbent[^\n<]*|Vacant)', s)
        if mem and party and status:
            extra = strip_links(mem.group(2)).replace('<br/>', ' ').replace('<br />', ' ').strip()
            incs.append((strip_links(mem.group(1)).strip(), 'R' if party.group(1) == 'Republican' else 'D',  # DFL counts as D
                         strip_links(status.group(1)).strip().rstrip('.'), extra))
    return incs


def main():
    medsl = [x for x in csv.DictReader(open(os.path.join(RAW, 'mit-1976-2024-house.csv')))
             if x['year'] == '2014' and x['stage'] == 'GEN' and x['special'] == 'FALSE']
    by = collections.defaultdict(list)
    for x in medsl:
        by[dkey(x['state_po'], x['district'])].append(x)
    rows = list(csv.reader(open(os.path.join(RAW, 'downballot-pres2012-on-2012-2014-lines.csv'))))
    assert rows[1][:5] == ['CD', 'Incumbent', 'Party', 'Obama', 'Romney'], rows[1][:5]
    pres = {r[0]: r for r in rows[2:]}
    assert len(pres) == 435, len(pres)
    wp = load_wikipedia()
    wp = {k: v for k, v in wp.items() if k in pres}  # drop non-voting delegates (Guam etc.)
    assert set(wp) == set(pres) == set(by), (set(pres) ^ set(wp), set(pres) ^ set(by))

    out = []
    for k in sorted(pres):
        xs, notes = by[k], []
        cp = {}
        for x in xs:
            if x['writein'] == 'TRUE' or x['candidate'] in WRITEIN_ROWS:
                continue
            if x['party'] in DP: cp.setdefault(x['candidate'], set()).add('D')
            if x['party'] in RP: cp.setdefault(x['candidate'], set()).add('R')
        D = R = T = 0
        cand_votes = collections.Counter()
        for x in xs:
            if x['candidate'] in EXCL:
                continue
            v = int(x['candidatevotes']); T += v
            if x['writein'] == 'TRUE' or x['candidate'] in WRITEIN_ROWS:
                continue
            cand_votes[x['candidate']] += v
            p = cp.get(x['candidate'], set())
            if p == {'D'}: D += v
            elif p == {'R'}: R += v
        nD = sum(1 for p in cp.values() if p == {'D'}); nR = sum(1 for p in cp.values() if p == {'R'})
        contested = nD >= 1 and nR >= 1
        src_house = SRC_HOUSE
        if T <= 1:
            hm = ''; notes.append('unopposed; no votes tabulated (MEDSL placeholder 1 vote)')
        elif k in LA_MIXED:
            hm = f"{wp_margin(wp[k]):.1f}"; src_house = 'Wikipedia (November open-primary shares)'
            a, b = LA_MIXED[k]
            ra = cand_votes[a] / (cand_votes[a] + cand_votes[b]) * 100
            notes.append(f'MEDSL mixes rounds: its {nm(a)} ({cand_votes[a]}) and {nm(b)} ({cand_votes[b]}) rows are the December runoff totals ({ra:.1f}% for {nm(a)}, matching the runoff share Wikipedia lists) while the other candidates carry November totals, so November shares cannot be computed from it; November open-primary shares from Wikipedia')
        else:
            hm = f"{(D - R) / T * 100:.2f}"
            w = wp_margin(wp[k])
            if contested and abs(float(hm) - w) > 0.75:
                notes.append(f"Wikipedia pct gives {w:.1f}; kept MEDSL")
        if nD >= 2 or nR >= 2: notes.append(f"{nD} D / {nR} R on general ballot (party votes summed)")
        if not contested:
            notes.append('same-party general' if (nD >= 2 or nR >= 2) else ('no R on ballot' if nR == 0 else 'no D on ballot'))
        if k[:2] in ('CA', 'WA'): notes.append('top-two general')
        if k[:2] == 'LA': notes.append('Louisiana November open primary')

        # winner: MEDSL top vote-getter, cross-checked against Wikipedia's winner marker
        winner = ''
        if cand_votes:
            top = cand_votes.most_common(1)[0][0]
            p = cp.get(top, set())
            winner = 'D' if p == {'D'} else 'R' if p == {'R'} else 'OTHER'
        if T <= 1:
            dem = [c for c, p in cp.items() if p == {'D'}]
            winner = 'D' if dem and not [c for c, p in cp.items() if p == {'R'}] else winner
        wpw = wp_winner(wp[k])
        if wpw != winner and not (wpw == '' and not contested):
            notes.append(f'winner mismatch: MEDSL {winner} vs Wikipedia {wpw}')

        incs = wp_incumbents(wp[k])
        ran = {p for n, p, s, e in incs if ('re-elected' in s or 'lost re-election' in s) and 'lost renomination' not in s}
        ipr = 'OPEN' if not ran else (ran.pop() if len(ran) == 1 else 'BOTH')
        if not incs: notes.append('incumbent: none (' + ('vacant' if 'Vacant' in wp[k] else 'new seat') + ')')
        else: notes.append('incumbent: ' + '; '.join(f"{n} ({p}) {s}" + (f" [{e}]" if e else '') for n, p, s, e in incs))
        if ipr == 'BOTH': notes.append('two incumbents of opposite parties on the ballot')
        if 'Vacant' in wp[k]:
            vac = re.search(r'colspan="?3"? \|\s*Vacant[^\n]*\n+\|\s*\{\{[^}]*\}\}\s*\|\s*([^\n]*)', wp[k])
            if vac: notes.append('vacancy: ' + strip_links(vac.group(1).split('<br')[0]).strip())

        pr = pres[k]
        pm = f"{float(pr[3]) - float(pr[4]):.1f}"
        out.append(dict(district=k, state=k[:2], pres2012_d_minus_r=pm, house2014_d_minus_r=hm,
                        contested=str(contested).lower(), incumbent_party_running=ipr,
                        incumbent_name=' / '.join(n for n, p, s, e in incs), winner_party=winner,
                        source_pres=SRC_PRES, source_house=src_house if hm else 'MEDSL (no votes tabulated)',
                        notes='; '.join(notes)))

    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['district', 'state', 'pres2012_d_minus_r', 'house2014_d_minus_r', 'contested',
                                          'incumbent_party_running', 'incumbent_name', 'winner_party', 'source_pres',
                                          'source_house', 'notes'])
        w.writeheader(); w.writerows(out)
    c = collections.Counter
    print(len(out), 'rows;', c(o['contested'] for o in out), c(o['incumbent_party_running'] for o in out),
          c(o['winner_party'] for o in out),
          sum(1 for o in out if o['house2014_d_minus_r'] and o['pres2012_d_minus_r']), 'with both margins')


if __name__ == '__main__':
    main()
