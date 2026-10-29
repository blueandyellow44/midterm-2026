"""Backtest of the v3 uncertainty model against the flat 5-point rule (2026-10-29).

For each even year 2010-2024, the error structure is fit ONLY on earlier years (what we would have known then), then
every Senate and governor general in the 538 archive that year is scored:
  old: P(D) = Phi(poll margin / 5), races independent
  new: simulate.py's structure (shared + division + state + race-own), total spread per race TOTAL (default 5.0);
       --by-polls scales the race-own part by the poll count instead (simulate.py 1.0, rejected on this test)
Per race: Brier score, log loss, calibration by probability band.
Per year: the count of D wins. Does the actual count land inside each model's 90% range? A model that is too sure of
itself misses that range more than 1 year in 10.
Centers are the archive's own poll averages (no lean, no signals), so this tests the spread, not the center.

Usage: python3 scripts/backtest_uncertainty.py [--json out.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
import simulate as S  # noqa: E402

HIST = os.path.expanduser("~/Second Brain V2/Resources/methods/midterm-2026/poll-error-history.csv")
YEARS = range(2010, 2025, 2)
FLAT_SIGMA = 5.0
CLAMP = (0.03, 0.97)   # the Stage 3 clamp, applied to both models for a fair log loss
N = 20000


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--total", type=float, default=S.RACE_TOTAL_SD)
    ap.add_argument("--by-polls", action="store_true")
    ap.add_argument("--df", type=int, default=0, help="Student t degrees of freedom for every miss (0 = normal)")
    a = ap.parse_args()
    hist = list(csv.DictReader(open(HIST)))
    per_race = {"old": [], "new": []}
    years = []
    for y in YEARS:
        fit = S.fit_error_structure(hist, y)
        races = [r for r in hist if int(r["year"]) == y and r["type"] in ("Sen-G", "Gov-G") and r["state"] in S.DIVISION]
        if not fit or not races:
            continue
        m = np.array([float(r["poll_margin"]) for r in races])
        act = np.array([float(r["actual_margin"]) for r in races])
        polls = np.array([int(r["n_polls"]) for r in races])
        won = (act > 0).astype(float)
        shared = fit["shared_sd_measured"]
        if a.by_polls:
            idio = np.array([S.idio_sd_for_polls(fit, int(k)) for k in polls])
        else:
            idio = np.full(len(races), math.sqrt(max(a.total ** 2 - shared ** 2 - fit["division_sd"] ** 2 - fit["state_sd"] ** 2, S.MIN_IDIO_SD ** 2)))
        sd_new = np.sqrt(shared ** 2 + fit["division_sd"] ** 2 + fit["state_sd"] ** 2 + idio ** 2)
        p_old = np.clip([phi(x / FLAT_SIGMA) for x in m], *CLAMP)
        if a.df:
            from scipy import stats
            p_new = np.clip([stats.t.cdf(x / (s / math.sqrt(a.df / (a.df - 2))), a.df) for x, s in zip(m, sd_new)], *CLAMP)
        else:
            p_new = np.clip([phi(x / s) for x, s in zip(m, sd_new)], *CLAMP)
        for p, k in ((p_old, "old"), (p_new, "new")):
            per_race[k] += [(float(pi), float(w)) for pi, w in zip(p, won)]
        # Seat-count range: new = correlated draws; old = independent draws at sigma 5.
        rng = np.random.default_rng(1000 + y)
        states = sorted({r["state"] for r in races})
        divs = sorted({S.DIVISION[s] for s in states})
        si = np.array([states.index(r["state"]) for r in races])
        di = np.array([divs.index(S.DIVISION[r["state"]]) for r in races])
        def draw(sd, shape):
            return rng.standard_t(a.df, shape) * sd / math.sqrt(a.df / (a.df - 2)) if a.df else rng.normal(0, sd, shape)
        val = (m + draw(shared, (N, 1)) + draw(fit["division_sd"], (N, len(divs)))[:, di]
               + draw(fit["state_sd"], (N, len(states)))[:, si] + draw(1.0, (N, len(races))) * idio)
        cnt_new = (val > 0).sum(axis=1)
        cnt_old = (m + rng.normal(0, FLAT_SIGMA, (N, len(races))) > 0).sum(axis=1)
        actual = int(won.sum())
        row = {"year": y, "races": len(races), "d_wins": actual, "shared_miss_toward_r": round(float(np.mean(m - act)), 2)}
        for k, c in (("old", cnt_old), ("new", cnt_new)):
            lo, hi = (int(v) for v in np.quantile(c, (0.05, 0.95)))
            row[k] = {"range90": [lo, hi], "inside": lo <= actual <= hi, "pit": round(float(np.mean(c < actual) + 0.5 * np.mean(c == actual)), 3)}
        years.append(row)

    def scores(pairs):
        p = np.array([x[0] for x in pairs]); w = np.array([x[1] for x in pairs])
        bands = []
        for lo, hi in ((0.03, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 0.97001)):
            sel = (p >= lo) & (p < hi)
            if sel.sum():
                bands.append({"band": f"{lo:.2f}-{min(hi, 0.97):.2f}", "races": int(sel.sum()), "mean_p": round(float(p[sel].mean()), 3), "d_won": round(float(w[sel].mean()), 3)})
        return {"races": len(p), "brier": round(float(np.mean((p - w) ** 2)), 4),
                "log_loss": round(float(-np.mean(w * np.log(p) + (1 - w) * np.log(1 - p))), 4), "calibration": bands}

    out = {"method": __doc__.strip().splitlines()[0], "total_sd": a.total, "by_polls": a.by_polls, "tail_df": a.df, "years": years,
           "old": scores(per_race["old"]), "new": scores(per_race["new"]),
           "seat_range_hits": {k: sum(1 for r in years if r[k]["inside"]) for k in ("old", "new")}, "seat_range_years": len(years)}
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
