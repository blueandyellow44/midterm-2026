#!/usr/bin/env python3
"""Build districts2018.csv from the three raw inputs in raw/.

Inputs (all in raw/, provenance in baselines.json):
  mit-1976-2024-house.csv                  MEDSL House returns, 2018 general rows used
  downballot-pres2016-on-2018-lines.csv    Clinton/Trump shares by 2018 district (Daily Kos Elections / The Downballot)
  wikipedia-2018-house-elections.wikitext  incumbent status, winner marker, candidate pct cross-check

Rules copied from ../swing-test-2022/derive_districts2022.py. Sign: D minus R, percentage points.
Run from anywhere: python3 derive_districts2018.py
"""
import csv, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
OUT = os.path.join(HERE, 'districts2018.csv')

EXCL = {'BLANK', 'BLANKS', 'BLANK VOTES', 'VOID', 'OVERVOTES', 'UNDERVOTES', 'EXHAUSTED BALLOT'}
DP = {'DEMOCRAT', 'DEMOCRATIC', 'DEMOCRATIC-FARMER-LABOR', 'DEMOCRATIC-NPL'}
RP = {'REPUBLICAN'}
# Wikipedia uses state names instead of postal codes in a few ushr templates
STATE_FIX = {'Georgia': 'GA'}
SRC_PRES = 'DKE/Downballot 2016 pres on 2018 lines (Google Sheet 1zLNAuRq..., shares rounded 0.1)'
SRC_HOUSE = 'MEDSL U.S. House 1976-2024 (2018 general)'


def dkey(st, d):
    st = STATE_FIX.get(st, st)
    return st + '-' + ('AL' if d in ('0', 'AL') else d.zfill(2))


def strip_links(s):
    s = re.sub(r'<ref.*?(</ref>|/>)', '', s)
    s = re.sub(r'\{\{[Ss]ortname\|([^|}]+)\|([^|}]+)[^}]*\}\}', r'\1 \2', s)
    s = re.sub(r'\{\{ushr\|([A-Z]{2})\|(\w+)\|C\}\}', r'\1-\2', s)
    s = re.sub(r'\{\{[Ss]mall\|([^}]*)\}\}', r'\1', s)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)


def load_wikipedia():
    t = open(os.path.join(RAW, 'wikipedia-2018-house-elections.wikitext')).read()
    t = t[t.find('== Alabama =='):]
    parts = re.split(r'\n!\s*[^\n{]*\{\{ushr\|([A-Za-z]+)\|(\w+)\|X\}\}', t)
    rows = {}
    for i in range(1, len(parts), 3):
        body = re.split(r'\n\|\}|\n==', parts[i + 2])[0]
        rows[dkey(parts[i], parts[i + 1])] = body
    return rows


def wp_candidates(body):
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
    w = [n for n, p, a in wp_candidates(body) if a]
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
             if x['year'] == '2018' and x['stage'] == 'GEN' and x['special'] == 'FALSE']
    by = collections.defaultdict(list)
    for x in medsl:
        by[dkey(x['state_po'], x['district'])].append(x)
    rows = list(csv.reader(open(os.path.join(RAW, 'downballot-pres2016-on-2018-lines.csv'))))
    assert rows[1][:5] == ['CD', 'Incumbent', 'Party', 'Clinton', 'Trump'], rows[1][:5]
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
            if x['writein'] == 'TRUE':
                continue
            if x['party'] in DP: cp.setdefault(x['candidate'], set()).add('D')
            if x['party'] in RP: cp.setdefault(x['candidate'], set()).add('R')
        D = R = T = 0
        cand_votes = collections.Counter()
        for x in xs:
            if x['candidate'] in EXCL:
                continue
            v = int(x['candidatevotes']); T += v
            if x['writein'] == 'TRUE':
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
        elif k == 'ME-02':
            hm = f"{45.6 - 46.3:.1f}"; src_house = 'Wikipedia (first-round shares)'
            notes.append(f'RCV: MEDSL ME-02 lists only Golden {cand_votes["JARED F GOLDEN"]} and Poliquin {cand_votes["BRUCE POLIQUIN"]} against a totalvotes field of {xs[0]["totalvotes"]} and omits Bond and Hoar, so first-round shares cannot be computed from it; first-round shares Golden 45.6 Poliquin 46.3 from Wikipedia; Golden won the instant runoff')
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
        if k == 'AK-AL': notes.append('Galvin (D nominee, ballot label Undeclared) counted as D')
        if k[:2] == 'PA': notes.append('court-ordered 2018 PA map')

        # winner: MEDSL top vote-getter, cross-checked against Wikipedia's winner marker
        winner = ''
        if cand_votes:
            top = cand_votes.most_common(1)[0][0]
            p = cp.get(top, set())
            winner = 'D' if p == {'D'} else 'R' if p == {'R'} else 'OTHER'
        if T <= 1:
            dem = [c for c, p in cp.items() if p == {'D'}]
            winner = 'D' if dem and not [c for c, p in cp.items() if p == {'R'}] else winner
        if k == 'ME-02':
            winner = 'D'
        if k == 'NC-09':
            notes.append('NC-09: November result (Harris R by 905 votes) never certified over absentee-ballot fraud; seat vacant, new election 2019; margin kept as tabulated, winner_party blank')
            winner = ''
        wpw = wp_winner(wp[k])
        if k not in ('NC-09', 'ME-02') and wpw != winner and not (wpw == '' and not contested):
            notes.append(f'winner mismatch: MEDSL {winner} vs Wikipedia {wpw}')

        incs = wp_incumbents(wp[k])
        ran = {p for n, p, s, e in incs if ('re-elected' in s or 'lost re-election' in s) and 'lost renomination' not in s}
        ipr = 'OPEN' if not ran else (ran.pop() if len(ran) == 1 else 'BOTH')
        if not incs: notes.append('incumbent: none (' + ('vacant' if 'Vacant' in wp[k] else 'new seat') + ')')
        else: notes.append('incumbent: ' + '; '.join(f"{n} ({p}) {s}" + (f" [{e}]" if e else '') for n, p, s, e in incs))
        if k == 'NY-14': notes.append('Crowley lost the D primary and appeared only on the Working Families line; treated as OPEN (no incumbent on a D or R line)')
        if ipr == 'BOTH': notes.append('two incumbents of opposite parties on the ballot')
        if 'Vacant' in wp[k]:
            vac = re.search(r'colspan=3 \| Vacant[^\n]*\n+\|\s*\{\{[^}]*\}\}\s*\|\s*([^\n]*)', wp[k])
            if vac: notes.append('vacancy: ' + strip_links(vac.group(1).split('<br')[0]).strip())

        pr = pres[k]
        pm = f"{float(pr[3]) - float(pr[4]):.1f}"
        out.append(dict(district=k, state=k[:2], pres2016_d_minus_r=pm, house2018_d_minus_r=hm,
                        contested=str(contested).lower(), incumbent_party_running=ipr,
                        incumbent_name=' / '.join(n for n, p, s, e in incs), winner_party=winner,
                        source_pres=SRC_PRES, source_house=src_house if hm else 'MEDSL (no votes tabulated)',
                        notes='; '.join(notes)))

    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['district', 'state', 'pres2016_d_minus_r', 'house2018_d_minus_r', 'contested',
                                          'incumbent_party_running', 'incumbent_name', 'winner_party', 'source_pres',
                                          'source_house', 'notes'])
        w.writeheader(); w.writerows(out)
    c = collections.Counter
    print(len(out), 'rows;', c(o['contested'] for o in out), c(o['incumbent_party_running'] for o in out),
          c(o['winner_party'] for o in out),
          sum(1 for o in out if o['house2018_d_minus_r'] and o['pres2016_d_minus_r']), 'with both margins')


if __name__ == '__main__':
    main()
