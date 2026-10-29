"""Does leaning on a state's partisan record help thinly polled races? (Max, 2026-10-29: "test it", after the
fundamentals research recommended a race-level structural prior weighted by inverse variance.)

Prior for a Senate or governor race in year y = the state's most recent presidential margin BEFORE y (538 archive Pres-G
actual margins) + the year's environment, estimated from the polls themselves (mean of poll margin minus that prior
presidential margin across every polled Senate and governor race that year). Nothing from the result is used.
Blend: center = w * polls + (1 - w) * prior, w = v_prior / (v_prior + v_polls(n)), with both variances fit only on
earlier years, by office (Senate and governor separately) and, for the polls, by poll-count band.
Scored 2010-2024 against polls alone: mean absolute miss, winner called, Brier at sigma 5, by poll count.

Usage: python3 scripts/backtest_partisan_prior.py [--json out.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict

HIST = os.path.expanduser("~/Second Brain V2/Resources/methods/midterm-2026/poll-error-history.csv")
YEARS = range(2010, 2025, 2)
BANDS = ((1, 2), (3, 5), (6, 10), (11, 999))
SIGMA = 5.0


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def band(n):
    return next(b for b in BANDS if b[0] <= n <= b[1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(HIST)))
    pres = {(int(r["year"]), r["state"]): float(r["actual_margin"]) for r in rows if r["type"] == "Pres-G" and len(r["state"]) == 2}
    races = []
    for r in rows:
        if r["type"] not in ("Sen-G", "Gov-G") or len(r["state"]) != 2:
            continue
        y = int(r["year"])
        prior_years = sorted(py for (py, st) in pres if st == r["state"] and py < y)
        if not prior_years:
            continue
        races.append({"y": y, "st": r["state"], "office": r["type"][:3], "n": int(r["n_polls"]), "poll": float(r["poll_margin"]),
                      "act": float(r["actual_margin"]), "pres": pres[(prior_years[-1], r["state"])]})
    env = defaultdict(list)
    for x in races:
        env[x["y"]].append(x["poll"] - x["pres"])
    env = {y: sum(v) / len(v) for y, v in env.items()}
    for x in races:
        x["prior"] = x["pres"] + env[x["y"]]

    def var(v):
        return sum(e * e for e in v) / len(v) if v else None

    out = {"by_year": [], "rows": []}
    scored = []
    for y in YEARS:
        past = [x for x in races if x["y"] < y]
        vp = {o: var([x["act"] - x["prior"] for x in past if x["office"] == o]) for o in ("Sen", "Gov")}
        vq = {(o, b): var([x["act"] - x["poll"] for x in past if x["office"] == o and band(x["n"]) == b]) for o in ("Sen", "Gov") for b in BANDS}
        for x in (x for x in races if x["y"] == y):
            p, q = vp[x["office"]], vq[(x["office"], band(x["n"]))]
            if p is None or q is None:
                continue
            w = p / (p + q)
            blend = w * x["poll"] + (1 - w) * x["prior"]
            scored.append({**x, "w": w, "blend": blend})
        out["by_year"].append({"year": y, "prior_sd": {o: round(math.sqrt(v), 2) for o, v in vp.items() if v}})

    def score(sel, key):
        s = [x for x in scored if sel(x)]
        if not s:
            return None
        mae = sum(abs(x[key] - x["act"]) for x in s) / len(s)
        right = sum(1 for x in s if (x[key] > 0) == (x["act"] > 0)) / len(s)
        brier = sum((min(max(phi(x[key] / SIGMA), .03), .97) - (x["act"] > 0)) ** 2 for x in s) / len(s)
        return {"races": len(s), "mae": round(mae, 3), "winner_right": round(right, 3), "brier": round(brier, 4)}

    groups = {"all": lambda x: True}
    for o in ("Sen", "Gov"):
        for b in BANDS:
            groups[f"{o} {b[0]}-{b[1] if b[1] < 999 else '+'} polls"] = (lambda o, b: lambda x: x["office"] == o and band(x["n"]) == b)(o, b)
    groups["thin (1-2 polls), within 15"] = lambda x: x["n"] <= 2 and abs(x["poll"]) < 15
    for g, sel in groups.items():
        s = [x for x in scored if sel(x)]
        out["rows"].append({"group": g, "mean_weight_on_polls": round(sum(x["w"] for x in s) / len(s), 2) if s else None,
                            "polls": score(sel, "poll"), "prior": score(sel, "prior"), "blend": score(sel, "blend")})
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
