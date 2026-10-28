#!/usr/bin/env python3
"""Build districts2022.csv from the three raw inputs in raw/.

Inputs (all in raw/, provenance in baselines.json):
  mit-1976-2024-house.csv                MEDSL House returns, 2022 general rows used
  downballot-pres2020-on-2022-lines.csv  Biden/Trump shares by 2022 district (The Downballot)
  wikipedia-2022-house-elections.wikitext  incumbent status + candidate pct cross-check

Run from anywhere: python3 derive_districts2022.py
"""
import csv, json, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
OUT = os.path.join(HERE, 'districts2022.csv')

EXCL = {'BLANK', 'BLANKS', 'BLANK VOTES', 'VOID', 'OVERVOTES', 'UNDERVOTES', 'EXHAUSTED BALLOT'}
DP = {'DEMOCRAT', 'DEMOCRATIC', 'DEMOCRATIC-FARMER-LABOR'}
RP = {'REPUBLICAN'}
# Fusion lines MEDSL records under the line name with no candidate; attribution per Wikipedia totals (match within 0.1 pt)
LINEFIX = {('CT-01', 'WORKING FAMILIES'): 'D', ('CT-04', 'INDEPENDENT'): 'R', ('CT-05', 'WORKING FAMILIES'): 'D',
           ('CT-05', 'INDEPENDENT'): 'R', ('NY-21', 'MODERATE'): 'D'}


def dkey(st, d):
    return st + '-' + ('AL' if d in ('0', 'AL') else d.zfill(2))


def load_wikipedia():
    t = open(os.path.join(RAW, 'wikipedia-2022-house-elections.wikitext')).read()
    t = t[t.find('==Alabama=='):]
    parts = re.split(r'\n!\s*[^\n{]*\{\{ushr\|([A-Z]{2})\|(\w+)\|X\}\}', t)
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
        m = re.search(r'\(([^()]+)\)\s*\'*\s*([\d.]+)\s*%', line)
        if m:
            out.append((m.group(1).strip(), float(m.group(2))))
    return out


def wp_margin(body):
    c = wp_candidates(body)
    return sum(p for n, p in c if n in ('Democratic', 'DFL')) - sum(p for n, p in c if n == 'Republican')


def wp_incumbents(body):
    incs = []
    for s in body.split('\n|-'):
        mem = re.search(r'(?m)^\|\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', s)
        party = re.search(r'(?im)^\|\s*\{\{party shading/(Republican|Democratic|Minnesota Democratic–Farmer–Labor)(?:/Text)?\}\}', s)
        status = re.search(r'(Incumbent[^\n<]*|Vacant)', s)
        if mem and party and status:
            incs.append(((mem.group(2) or mem.group(1)).strip(),
                         'R' if party.group(1) == 'Republican' else 'D',
                         re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', status.group(1)).strip().rstrip('.')))
    return incs


def main():
    medsl = [x for x in csv.DictReader(open(os.path.join(RAW, 'mit-1976-2024-house.csv'))) if x['year'] == '2022']
    by = collections.defaultdict(list)
    for x in medsl:
        by[dkey(x['state_po'], x['district'])].append(x)
    pres = {x['District']: x for x in csv.DictReader(open(os.path.join(RAW, 'downballot-pres2020-on-2022-lines.csv')))}
    assert len(pres) == 435, len(pres)
    wp = load_wikipedia()

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
        for x in xs:
            if x['candidate'] in EXCL:
                continue
            v = int(x['candidatevotes']); T += v
            if x['writein'] == 'TRUE':
                continue
            p = cp.get(x['candidate'], set())
            if (k, x['candidate']) in LINEFIX:
                p = {LINEFIX[(k, x['candidate'])]}
                notes.append(f"{x['candidate'].title()} fusion line ({v}) attributed to {LINEFIX[(k, x['candidate'])]} per Wikipedia totals")
            if p == {'D'}: D += v
            elif p == {'R'}: R += v
        nD = sum(1 for p in cp.values() if p == {'D'}); nR = sum(1 for p in cp.values() if p == {'R'})
        contested = nD >= 1 and nR >= 1
        if T <= 1:
            hm = ''; notes.append('unopposed; no votes tabulated (MEDSL placeholder 1 vote)')
        elif k == 'ME-02':
            hm = f"{48.4 - 44.6:.1f}"; notes.append('MEDSL ME-02 rows mix RCV rounds (unusable); first-round shares Golden 48.4 Poliquin 44.6 from Wikipedia')
        else:
            hm = f"{(D - R) / T * 100:.2f}"
            if k == 'AK-AL': notes.append('RCV: first-round party sums (Peltola D vs Palin+Begich R)')
            w = wp_margin(wp[k])
            if contested and abs(float(hm) - w) > 0.75 and k not in ('AK-AL', 'VT-AL'):
                notes.append(f"Wikipedia pct gives {w:.1f}; kept MEDSL")
        if nD >= 2 or nR >= 2: notes.append(f"{nD} D / {nR} R on general ballot (party votes summed)")
        if not contested:
            notes.append('same-party general' if (nD >= 2 or nR >= 2) else ('no R on ballot' if nR == 0 else 'no D on ballot'))
        if k[:2] in ('CA', 'WA'): notes.append('top-two general')
        if k[:2] == 'LA': notes.append('Louisiana November open primary')
        incs = wp_incumbents(wp[k])
        ran = {p for n, p, s in incs if 're-elected' in s or 'lost re-election' in s}
        ipr = 'OPEN' if not ran else (ran.pop() if len(ran) == 1 else 'BOTH')
        if not incs: notes.append('incumbent: none (' + ('vacant' if 'Vacant' in wp[k] else 'new seat') + ')')
        else: notes.append('incumbent: ' + '; '.join(f"{n} ({p}) {s}" for n, p, s in incs))
        if ipr == 'BOTH': notes.append('two incumbents of opposite parties on the ballot')
        pr = pres[k]
        assert abs(float(pr['Biden']) - float(pr['Trump']) - float(pr['Margin'])) < 0.11, k
        out.append(dict(district=k, pres2020_d_minus_r=pr['Margin'], house2022_d_minus_r=hm,
                        contested=str(contested).lower(), incumbent_party_running=ipr, source_note='; '.join(notes)))

    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['district', 'pres2020_d_minus_r', 'house2022_d_minus_r', 'contested', 'incumbent_party_running', 'source_note'])
        w.writeheader(); w.writerows(out)
    c = collections.Counter
    print(len(out), 'rows;', c(o['contested'] for o in out), c(o['incumbent_party_running'] for o in out),
          sum(1 for o in out if o['house2022_d_minus_r'] and o['pres2020_d_minus_r']), 'with both margins')


if __name__ == '__main__':
    main()
