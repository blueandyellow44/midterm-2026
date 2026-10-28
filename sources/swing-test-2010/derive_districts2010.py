#!/usr/bin/env python3
"""Build districts2010.csv from the raw inputs in raw/.

Inputs (all in raw/, provenance in baselines.json):
  mit-1976-2024-house.csv                            MEDSL House returns, 2010 general rows used
  downballot-pres2008-on-2010-lines.csv              DKE 'Results' tab: Obama/McCain integer shares, 2006-2010 lines (all 435)
  downballot-pres2008-on-2010-lines-votetotals.csv   DKE 'Vote totals' tab: Obama/McCain/total votes (filled for AK-MA and the at-large states)
  ssp-2008-state-sheets/<State>.csv                  Swing State Project per-state 2008 pres-by-CD worksheets (vote counts or 0.01 pct)
  wikipedia-2010-house-elections.wikitext            incumbent status, winner marker, candidate pct cross-check

Rules copied from ../swing-test-2018/derive_districts2018.py. Sign: D minus R, percentage points.
Run from anywhere: python3 derive_districts2010.py
"""
import csv, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
SSP = os.path.join(RAW, 'ssp-2008-state-sheets')
OUT = os.path.join(HERE, 'districts2010.csv')

# 'BLANK VOTE/SCATTERING' is New York's combined blank/void/scattering line (NY 29 seats) and Wisconsin's
# scattering line (8 seats): excluded in NY (mostly blank ballots), kept in WI (write-in scattering), see README.
EXCL = {'BLANK', 'BLANKS', 'BLANK VOTES', 'VOID', 'OVERVOTES', 'UNDERVOTES', 'EXHAUSTED BALLOT'}
DP = {'DEMOCRAT', 'DEMOCRATIC', 'DEMOCRATIC-FARMER-LABOR', 'DEMOCRATIC-NPL'}
RP = {'REPUBLICAN'}
STATES = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO',
          'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
          'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
          'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
          'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
          'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
          'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
          'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
          'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
          'Wisconsin': 'WI', 'Wyoming': 'WY'}
SRC_DKE_VOTES = 'DKE/Downballot 2008 pres on 2006-2010 lines, Vote totals tab (Google Sheet 1l7W130t...)'
SRC_SSP = 'Swing State Project 2008 pres-by-CD state sheet (same DKE/SSP lineage)'
SRC_DKE_INT = 'DKE/Downballot 2008 pres on 2006-2010 lines, Results tab (integer shares)'
SRC_HOUSE = 'MEDSL U.S. House 1976-2024 (2010 general)'
# MEDSL lines whose vote count differs from the Clerk's 2010 statistics (raw/clerk-statistics-2010-election.pdf);
# in each case Wikipedia's percentages agree with the Clerk. Found by checking every MEDSL line of 1,000+ votes against the Clerk.
MEDSL_FIX = {('NY', '21', 'THEODORE J DANZ JR', 'CONSERVATIVE'): (25541, 15541),
             ('FL', '23', 'BERNARD SANSARICQ', 'REPUBLICAN'): (26804, 26414),
             ('MN', '5', 'TOM SCHRUNK', 'INDEPENDENCE'): (7556, 7446)}
MAX_GAP = 1.0  # integer shares bound the margin to +/-1.0; a vote-based margin further away conflicts


def dkey(st, d):
    st = STATES.get(st, st)
    return st + '-' + ('AL' if d in ('0', 'AL') else d.zfill(2))


def num(s):
    s = s.strip().replace(',', '')
    if s.endswith('%'):
        return ('pct', float(s[:-1]))
    try:
        return ('n', float(s))
    except ValueError:
        return None


def parse_ssp(fn):
    """District rows of one SSP state sheet: {district_number: (kind, obama, mccain, total)}."""
    rows = list(csv.reader(open(fn)))
    out = {}
    if fn.endswith('Rhode_Island.csv'):  # labels like 'CD1 Soft Total' (absentee/limited ballots allocated)
        for row in rows:
            for i, cell in enumerate(row):
                m = re.fullmatch(r'CD(\d) Soft Total', cell.strip())
                if m:
                    v = [num(x)[1] for x in row[i + 1:] if x.strip() and num(x) and num(x)[0] == 'n']
                    out[int(m.group(1))] = ('votes', v[0], v[1], v[3])
        return out
    blocks = []
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if re.fullmatch(r'(CD|CDs|CD-Comb|CD-Summary|CD-Comp|District)', cell.strip(), re.I):
                hdr = [x.strip() for x in row[c:c + 10]]
                if '' in hdr[1:]:
                    hdr = hdr[:hdr.index('', 1)]
                lo = [h.lower() for h in hdr]
                oc = next((i for i, h in enumerate(lo) if re.fullmatch(r'(sum of )?obama ?', h)), None)
                mc = next((i for i, h in enumerate(lo) if re.fullmatch(r'(sum of )?mccain', h)), None)
                if oc is not None and mc is not None:
                    blocks.append((r, c, hdr, lo, oc, mc, any('sum of' in h for h in lo)))
    if any(b[6] for b in blocks):  # pivot-table summary blocks beat raw county lists
        blocks = [b for b in blocks if b[6]]
    for r, c, hdr, lo, oc, mc, _ in blocks:
        tc = next((i for i, h in enumerate(lo) if 'total' in h), None)
        others = [i for i, h in enumerate(lo) if re.fullmatch(r'(sum of )?(others?|barr)( \(tot\.\))?', h)]
        started = False
        for row in rows[r + 1:]:
            seg = [x.strip() for x in row[c:c + 10]] + [''] * 10
            if started and not any(seg[:max(oc, mc) + 1]):
                break
            if seg[0].lower().startswith('grand total'):
                break
            m = re.fullmatch(r'(?:CD[- ]?|[A-Z]{2}-)?0?(\d{1,2})(?: Total)?', seg[0])
            if not m:
                continue
            if any(seg[i] for i in range(1, min(oc, mc)) if not re.search('sum|total|obama|mccain', lo[i])):
                continue  # a county / part row, not a district summary
            O, M = num(seg[oc]), num(seg[mc])
            if not O or not M:
                continue
            d = int(m.group(1)); started = True
            if d in out:
                continue
            if O[0] == 'pct':
                out[d] = ('pct', O[1], M[1], 100.0)
            else:
                T = num(seg[tc])[1] if tc is not None and num(seg[tc]) else \
                    O[1] + M[1] + sum(num(seg[i])[1] for i in others if num(seg[i]))
                out[d] = ('votes', O[1], M[1], T)
    return out


def load_pres():
    res = list(csv.reader(open(os.path.join(RAW, 'downballot-pres2008-on-2010-lines.csv'))))
    assert res[1][:5] == ['CD', 'Incumbent', 'Party', 'Obama', 'McCain'], res[1][:5]
    ints = {r[0]: (int(r[3]), int(r[4])) for r in res[2:]}
    assert len(ints) == 435, len(ints)
    vt = list(csv.reader(open(os.path.join(RAW, 'downballot-pres2008-on-2010-lines-votetotals.csv'))))
    assert vt[1][4:7] == ['Obama', 'McCain', 'Total'], vt[1]
    votes = {r[0]: tuple(float(x.replace(',', '')) for x in r[4:7]) for r in vt[2:] if r[4].strip()}
    per_state = collections.Counter(k[:2] for k in ints)
    ssp = {}
    for f in sorted(os.listdir(SSP)):
        st = STATES[f[:-4].replace('_', ' ')]
        for d, v in parse_ssp(os.path.join(SSP, f)).items():
            ssp[f'{st}-{d:02d}' if per_state[st] > 1 else f'{st}-AL'] = v
    pres = {}
    for k, (io, im) in ints.items():
        imar = io - im
        notes = []
        if k in votes:
            O, M, T = votes[k]; m = (O - M) / T * 100; src = SRC_DKE_VOTES
            notes.append(f'pres: Obama {O:,.0f} McCain {M:,.0f} of {T:,.0f}')
        elif k in ssp:
            kind, O, M, T = ssp[k]; m = (O - M) / T * 100; src = SRC_SSP
            notes.append(f'pres: Obama {O:,.0f} McCain {M:,.0f} of {T:,.0f}' if kind == 'votes'
                         else f'pres: SSP shares Obama {O:.2f}% McCain {M:.2f}%')
        else:
            m = None; src = SRC_DKE_INT
        if m is not None and abs(m - imar) > MAX_GAP:
            notes = [f'pres: vote-based margin {m:.2f} ({notes[0][6:]}) conflicts with DKE Results tab {io}-{im}; '
                     f'used the published Results tab (also in the DKE 2012 comparison sheet), margin good to about +/-1']
            m = None; src = SRC_DKE_INT
        if m is None:
            m = float(imar)
            if not notes:
                notes.append(f'pres: no vote totals found; DKE integer shares {io}-{im}, margin good to about +/-1')
        pres[k] = (f'{m:.1f}', src, notes)
    return pres


def strip_links(s):
    s = re.sub(r'<ref.*?(</ref>|/>)', '', s)
    s = re.sub(r'\{\{[Ss]ortname\|([^|}]+)\|([^|}]+)[^}]*\}\}', r'\1 \2', s)
    s = re.sub(r'\{\{ushr\|([A-Z]{2})\|(\w+)\|C\}\}', r'\1-\2', s)
    s = re.sub(r'\{\{[Ss]mall\|([^}]*)\}\}', r'\1', s)
    return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)


def load_wikipedia():
    t = open(os.path.join(RAW, 'wikipedia-2010-house-elections.wikitext')).read()
    t = t[t.find('== Alabama =='):]
    parts = re.split(r'\n!\s*[^\n{]*\{\{ushr\|([A-Za-z ]+)\|(\w+)\|X\}\}', t)
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
            out.append((strip_links(m.group(1)).strip(), float(m.group(2)), '{{Aye}}' in line))
    return out


def is_d(label): return label in ('Democratic', 'DFL', 'Democratic-NPL')
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
        party = re.search(r'\{\{[Pp]arty shading/(?:Text/(Republican|Democratic)|(Minnesota Democratic-Farmer-Labor)'
                          r'|(North Dakota Democratic-NPL))\}\}', s)
        status = re.search(r'(Incumbent[^\n<]*|Open seat, incumbent[^\n<]*|Vacant)', s)
        if mem and party and status:
            extra = strip_links(mem.group(2)).replace('<br/>', ' ').replace('<br />', ' ').strip()
            incs.append((strip_links(mem.group(1)).strip(), 'R' if party.group(1) == 'Republican' else 'D',  # DFL, D-NPL count as D
                         strip_links(status.group(1)).strip().rstrip('.'), extra))
    return incs


def ran_again(status):
    s = status.replace('reelect', 're-elect')
    return ('re-elected' in s or 'lost re-election' in s) and 'lost renomination' not in s


def main():
    medsl = [x for x in csv.DictReader(open(os.path.join(RAW, 'mit-1976-2024-house.csv')))
             if x['year'] == '2010' and x['stage'] == 'GEN' and x['special'] == 'FALSE']
    by = collections.defaultdict(list)
    fixed = collections.defaultdict(list)
    for x in medsl:
        f = MEDSL_FIX.get((x['state_po'], x['district'], x['candidate'], x['party']))
        if f:
            assert int(x['candidatevotes']) == f[0], x
            x = dict(x, candidatevotes=str(f[1]))
            fixed[dkey(x['state_po'], x['district'])].append(f"{x['candidate'].title()} ({x['party'].title()} line) {f[0]:,} in MEDSL corrected to {f[1]:,} per the Clerk")
        by[dkey(x['state_po'], x['district'])].append(x)
    assert sum(len(v) for v in fixed.values()) == len(MEDSL_FIX)
    pres = load_pres()
    wp = load_wikipedia()
    wp = {k: v for k, v in wp.items() if k in pres}  # drop non-voting delegates (Guam etc.)
    assert set(wp) == set(pres) == set(by), (set(pres) ^ set(wp), set(pres) ^ set(by))

    out = []
    for k in sorted(pres):
        xs, notes = by[k], list(fixed.get(k, []))
        excl = EXCL | ({'BLANK VOTE/SCATTERING'} if k[:2] == 'NY' else set())
        cp = {}
        for x in xs:
            if x['writein'] == 'TRUE':
                continue
            if x['party'] in DP: cp.setdefault(x['candidate'], set()).add('D')
            if x['party'] in RP: cp.setdefault(x['candidate'], set()).add('R')
        D = R = T = 0
        cand_votes = collections.Counter()
        for x in xs:
            if x['candidate'] in excl:
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
        if T <= 1:
            hm = ''; notes.append('unopposed; no votes tabulated (MEDSL placeholder 1 vote)')
        else:
            hm = f"{(D - R) / T * 100:.2f}"
            w = wp_margin(wp[k])
            if contested and abs(float(hm) - w) > 0.75:
                notes.append(f"Wikipedia pct gives {w:.1f}; kept MEDSL")
        if nD >= 2 or nR >= 2: notes.append(f"{nD} D / {nR} R on general ballot (party votes summed)")
        if not contested:
            notes.append('same-party general' if (nD >= 2 or nR >= 2) else ('no R on ballot' if nR == 0 else 'no D on ballot'))
        if k[:2] == 'WA': notes.append('top-two general')
        if k[:2] == 'LA': notes.append('Louisiana closed party primaries (2008-2010); November was a regular general')
        if k[:2] == 'NY' and T > 1: notes.append("MEDSL 'BLANK VOTE/SCATTERING' line excluded from the denominator")

        winner = ''
        if cand_votes:
            top = cand_votes.most_common(1)[0][0]
            p = cp.get(top, set())
            winner = 'D' if p == {'D'} else 'R' if p == {'R'} else 'OTHER'
        wpw = wp_winner(wp[k])
        if wpw != winner and not (wpw == '' and not contested):
            notes.append(f'winner mismatch: MEDSL {winner} vs Wikipedia {wpw}')

        incs = wp_incumbents(wp[k])
        ran = {p for n, p, s, e in incs if ran_again(s)}
        ipr = 'OPEN' if not ran else (ran.pop() if len(ran) == 1 else 'BOTH')
        if not incs: notes.append('incumbent: none (' + ('vacant' if 'Vacant' in wp[k] else 'new seat') + ')')
        else: notes.append('incumbent: ' + '; '.join(f"{n} ({p}) {s}" + (f" [{e}]" if e else '') for n, p, s, e in incs))
        if k == 'FL-21': notes.append('Mario Diaz-Balart (R), the FL-25 incumbent, ran here unopposed; FL-21 counted OPEN because its own incumbent retired')
        if k == 'AL-05': notes.append('Griffith was elected in 2008 as a Democrat and became a Republican in December 2009')
        if ipr == 'BOTH': notes.append('two incumbents of opposite parties on the ballot')
        if 'Vacant' in wp[k]:
            vac = re.search(r'colspan=3[^|\n]*\| Vacant[^\n]*\n+\|\s*\{\{[^}]*\}\}\s*\|\s*([^\n]*)', wp[k])
            if vac: notes.append('vacancy: ' + strip_links(vac.group(1).split('<br')[0]).strip())

        pm, src_pres, pnotes = pres[k]
        out.append(dict(district=k, state=k[:2], pres2008_d_minus_r=pm, house2010_d_minus_r=hm,
                        contested=str(contested).lower(), incumbent_party_running=ipr,
                        incumbent_name=' / '.join(n for n, p, s, e in incs), winner_party=winner,
                        source_pres=src_pres, source_house=SRC_HOUSE if hm else 'MEDSL (no votes tabulated)',
                        notes='; '.join(pnotes + notes)))

    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['district', 'state', 'pres2008_d_minus_r', 'house2010_d_minus_r', 'contested',
                                          'incumbent_party_running', 'incumbent_name', 'winner_party', 'source_pres',
                                          'source_house', 'notes'])
        w.writeheader(); w.writerows(out)
    c = collections.Counter
    print(len(out), 'rows;', c(o['contested'] for o in out), c(o['incumbent_party_running'] for o in out),
          c(o['winner_party'] for o in out), c(o['source_pres'][:30] for o in out),
          sum(1 for o in out if o['house2010_d_minus_r'] and o['pres2008_d_minus_r']), 'with both margins')


if __name__ == '__main__':
    main()
