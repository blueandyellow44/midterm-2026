#!/usr/bin/env python3
"""Does the president's party lose its House incumbency edge in a midterm? (Max, 2026-10-28: "This feels like an anti
incumbent year"; "We still need to keep digging"). For each midterm in sources/swing-test-<year>/: uniform swing from the
prior presidential margin plus (final generic ballot - prior national presidential margin); the residual by who is running;
each party's incumbency edge measured against open seats the same year; and held-out projections (20 random halves) with no
bonus, one symmetric bonus, and a bonus by party."""
import csv, json, random, statistics as st, sys
PRES_PARTY = {2010: "D", 2014: "D", 2018: "R", 2022: "D"}
PRIOR = {2010: 2008, 2014: 2012, 2018: 2016, 2022: 2020}


def load(y):
    D = f"sources/swing-test-{y}/"
    b = json.load(open(D + "baselines.json"))
    val = lambda v: v if isinstance(v, (int, float)) else (v.get("value") if isinstance(v, dict) and isinstance(v.get("value"), (int, float)) else None)
    nums = {k: val(v) for k, v in b.items()}
    pres = [v for k, v in nums.items() if v is not None and "pres" in k]; gen = [v for k, v in nums.items() if v is not None and "generic" in k]
    if len(pres) != 1 or len(gen) != 1:
        raise SystemExit(f"{y}: baselines need exactly one pres and one generic number")
    pk, hk = f"pres{PRIOR[y]}_d_minus_r", f"house{y}_d_minus_r"
    rows = [r for r in csv.DictReader(open(D + f"districts{y}.csv")) if r["contested"] == "true" and r.get(hk) not in ("", None) and r.get(pk) not in ("", None)]
    shift = gen[0] - pres[0]
    return [(float(r[hk]) - (float(r[pk]) + shift), r["incumbent_party_running"]) for r in rows], pres[0], gen[0], shift


def main():
    years = [int(a) for a in sys.argv[1:]] or [2010, 2014, 2018, 2022]
    for y in years:
        try:
            res, pres, gen, shift = load(y)
        except FileNotFoundError:
            print(f"{y}: data not collected yet"); continue
        mean = lambda lab: st.mean(e for e, i in res if i == lab)
        n = lambda lab: sum(1 for _, i in res if i == lab)
        op = mean("OPEN"); d_edge = mean("D") - op; r_edge = -(mean("R") - op)
        pp = PRES_PARTY[y]
        inc = lambda i: {"D": 1, "R": -1}.get(i, 0)
        out = {"none": [], "symmetric": [], "by party": []}
        for seed in range(20):
            random.seed(seed); idx = list(range(len(res))); random.shuffle(idx); h = len(idx) // 2
            A = [res[i] for i in idx[:h]]; B = [res[i] for i in idx[h:]]
            b = sum(e * inc(i) for e, i in A) / sum(inc(i) ** 2 for _, i in A)
            bd = st.mean(e for e, i in A if i == "D"); br = st.mean(e for e, i in A if i == "R")
            out["none"].append(st.mean(abs(e) for e, _ in B)); out["symmetric"].append(st.mean(abs(e - b * inc(i)) for e, i in B))
            out["by party"].append(st.mean(abs(e - (bd if i == "D" else br if i == "R" else 0)) for e, i in B))
        sym = sum(e * inc(i) for e, i in res) / sum(inc(i) ** 2 for _, i in res)
        print(f"{y} (president {pp}; generic {gen:+.1f}, prior pres {pres:+.1f}, swing {shift:+.1f}; contested {len(res)}: D inc {n('D')}, R inc {n('R')}, open {n('OPEN')})")
        print(f"   edge over open seats: president's party {d_edge if pp == 'D' else r_edge:+.2f}, out party {r_edge if pp == 'D' else d_edge:+.2f}   symmetric fit {sym:.2f}")
        print("   held-out miss: " + ", ".join(f"{k} {st.mean(v):.2f}" for k, v in out.items()))


if __name__ == "__main__":
    main()
