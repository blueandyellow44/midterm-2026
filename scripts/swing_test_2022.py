"""2022 test of the seat-projection method (Max, 2026-10-27: "And you're sure this is the best way to do this?" -> "Yes" to testing).
predicted 2022 House margin = district 2020 presidential margin + (2022 generic-ballot average - 2020 national presidential margin)
Variants: + incumbency bonus b x (+1 D incumbent running, -1 R incumbent, 0 open), b fit on half the districts and scored on the other half."""
import csv, json, statistics as st, random
D = "/Users/maxsheahan/midterm-2026/sources/swing-test-2022/"
base = json.load(open(D + "baselines.json"))
def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def pick(d, *keys):
    for k in keys:
        for kk, v in d.items():
            if k in kk.lower() and isinstance(v, (int, float)): return v
            if k in kk.lower() and isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, (int, float)): return vv
    return None
nat2020 = pick(base, "pres", "2020"); generic = pick(base, "generic"); house_nat = pick(base, "house")
print("baselines:", base)
rows = [r for r in csv.DictReader(open(D + "districts2022.csv")) if str(r.get("contested")).lower() in ("true", "1", "yes")
        and num(r.get("pres2020_d_minus_r")) is not None and num(r.get("house2022_d_minus_r")) is not None]
print("contested districts with both margins:", len(rows))
def inc(r): return {"D": 1, "R": -1}.get((r.get("incumbent_party_running") or "").strip().upper()[:1], 0)
def score(shift, b, rs):
    err = [num(r["house2022_d_minus_r"]) - (num(r["pres2020_d_minus_r"]) + shift + b * inc(r)) for r in rs]
    right = sum(1 for r in rs if (num(r["pres2020_d_minus_r"]) + shift + b * inc(r)) * num(r["house2022_d_minus_r"]) > 0)
    close = [r for r in rs if abs(num(r["house2022_d_minus_r"])) < 15]
    rclose = sum(1 for r in close if (num(r["pres2020_d_minus_r"]) + shift + b * inc(r)) * num(r["house2022_d_minus_r"]) > 0)
    return st.mean(abs(e) for e in err), st.mean(err), right / len(rs), (rclose / len(close) if close else float("nan")), len(close)
for label, shift in (("generic ballot shift", (generic - nat2020) if generic is not None and nat2020 is not None else None),
                     ("actual national House shift (hindsight)", (house_nat - nat2020) if house_nat is not None and nat2020 is not None else None)):
    if shift is None: continue
    print(f"\n== {label}: shift {shift:+.2f}")
    mae, bias, acc, accc, nclose = score(shift, 0, rows)
    print(f"  no incumbency: MAE {mae:.2f}  bias {bias:+.2f}  winner right {acc:.1%}  winner right in races within 15 ({nclose}) {accc:.1%}")
    random.seed(7); idx = list(range(len(rows))); random.shuffle(idx); half = len(idx) // 2
    A = [rows[i] for i in idx[:half]]; B = [rows[i] for i in idx[half:]]
    res = [num(r["house2022_d_minus_r"]) - (num(r["pres2020_d_minus_r"]) + shift) for r in A]
    xs = [inc(r) for r in A]; b = sum(x * y for x, y in zip(xs, res)) / sum(x * x for x in xs)
    mae0 = score(shift, 0, B); mae1 = score(shift, b, B)
    print(f"  incumbency bonus fit on half: b = {b:.2f} pts per incumbent")
    print(f"  held-out half, no bonus: MAE {mae0[0]:.2f} winner right {mae0[2]:.1%} (close {mae0[3]:.1%})")
    print(f"  held-out half, with bonus: MAE {mae1[0]:.2f} winner right {mae1[2]:.1%} (close {mae1[3]:.1%})")
    for p in ("D", "R"):
        sub = [r for r in rows if inc(r) == (1 if p == "D" else -1)]
        e = [num(r["house2022_d_minus_r"]) - (num(r["pres2020_d_minus_r"]) + shift) for r in sub]
        print(f"  {p} incumbents running ({len(sub)}): mean residual {st.mean(e):+.2f}")
