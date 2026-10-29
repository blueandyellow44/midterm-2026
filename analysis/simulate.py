"""Correlated simulation of every seat (model v3, 2026-10-29; Max: "Last shot to make this hold water statistically").

Why: each race's reading is a center, not a certainty, and polling misses move together. 538's raw-polls archive
(poll-error-history.csv, even years 1998-2024) puts a shared year miss of about 2.8 points on every race, a further miss
shared by races in the same state that year (a Senate and a governor race in Georgia miss together), a small miss shared
by a census division, and a race's own miss that shrinks with the number of polls. Counting seats as if each race were
independent makes a chamber look more certain than it is. This module draws all of those at once, many times over.

weight.py owns the numbers: it calls fit_error_structure() and run() and seals the result in derived["simulation"].
Nothing here changes a reading; it only adds the spread around the readings weight.py already computed.

Model, every seat up in 2026, D minus R points:
    outcome = center + S + Div[division] + St[state] + e_race
    S       ~ N(0, national_sd)        one per simulation: the uncertainty of the national lean (poll_error_model lean_sd)
    Div     ~ N(0, division_sd)        one per census division per simulation
    St      ~ N(0, state_sd)           one per state per simulation, shared by every race in that state
    e_race  ~ N(0, idio_sd(race))      readings: whatever brings the race's total spread to RACE_TOTAL_SD, plus the
                                       spending and early-vote fit uncertainty; projections and Cook-rated governors: the
                                       2022 district residual less the division and state parts
Per race the spread stays 5 points, as before. Only the way races move together is new.
The D slot wins when outcome > 0 (independents in the D slot count as the release records them, as the console does).
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np

SIM_VERSION = "1.2"   # 1.2: odds across the dial; 1.1: race spread held at RACE_TOTAL_SD (backtest); 1.0 scaled it by poll count
SIM_N = 20000
SIM_SEED = 20261102   # fixed so the same release always gives the same numbers
SIM_QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)

# Census divisions (US Census Bureau regions and divisions). DC sits with South Atlantic.
DIVISION = {
    "CT": "NE", "ME": "NE", "MA": "NE", "NH": "NE", "RI": "NE", "VT": "NE",
    "NJ": "MA", "NY": "MA", "PA": "MA",
    "IL": "ENC", "IN": "ENC", "MI": "ENC", "OH": "ENC", "WI": "ENC",
    "IA": "WNC", "KS": "WNC", "MN": "WNC", "MO": "WNC", "NE": "WNC", "ND": "WNC", "SD": "WNC",
    "DE": "SA", "FL": "SA", "GA": "SA", "MD": "SA", "NC": "SA", "SC": "SA", "VA": "SA", "DC": "SA", "WV": "SA",
    "AL": "ESC", "KY": "ESC", "MS": "ESC", "TN": "ESC",
    "AR": "WSC", "LA": "WSC", "OK": "WSC", "TX": "WSC",
    "AZ": "MT", "CO": "MT", "ID": "MT", "MT": "MT", "NV": "MT", "NM": "MT", "UT": "MT", "WY": "MT",
    "AK": "PAC", "CA": "PAC", "HI": "PAC", "OR": "PAC", "WA": "PAC",
}

# Untracked House and Senate seats carry the swing projection. Its district-level miss in 2022, once the actual national
# shift and the incumbency edge are taken out (scripts/swing_test_2022.py data, 400 contested districts): SD 5.45 over all
# districts, 5.95 over districts within 20 points of even. 5.7 sits between them. The national part is drawn separately.
PROJECTION_RESIDUAL_SD = 5.7
# Untracked governors carry Cook's rating (Max, 2026-10-28: "Keep Cook"). A rating is turned into a center so it can move
# with the shared draws. These centers are an ASSUMPTION, not a fit: no rating-to-margin study is in the bundle. Governors
# have no control line, so they only affect the governor seat range.
RATED_CENTER = {"Solid D": 15.0, "Likely D": 8.0, "Lean D": 3.5, "Toss-up": 0.0, "Lean R": -3.5, "Likely R": -8.0, "Solid R": -15.0}
MIN_IDIO_SD = 1.0
# Total spread of one tracked race's reading (all parts together), kept at the existing Stage 3 sigma. Tested 2026-10-29 in
# scripts/backtest_uncertainty.py (each year fit only on earlier years, 404 Senate and governor races 2010-2024): total 4.5
# Brier 0.0607, 5.0 0.0612, 5.5 0.0621, 6.0 0.0633; scaling the spread by poll count 0.0621, worse even on races with 1-2
# polls (0.0182 vs 0.0164). With the correlation, every total from 4.5 to 6.0 puts the year's seat count inside its 90%
# range 8 of 8 years; races treated as independent at 5.0 missed 3 of 8 (2014, 2020, 2022). So the spread stays and the
# correlation is added. 4.5 scored a hair better; the difference is within noise and 5 is what the cards already carry.
RACE_TOTAL_SD = 5.0


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def fit_error_structure(history: list[dict] | None, target_year: int) -> dict | None:
    """Split the archive's polling miss into shared, division, state and race-own parts. Even-year Senate and governor
    generals in the 50 states and DC, years before target_year. 538 bias sign is irrelevant here: only spreads are fit."""
    rows = []
    for r in history or []:
        y, b, n = _num(r.get("year")), _num(r.get("bias")), _num(r.get("n_polls"))
        if None in (y, b, n) or int(y) >= target_year or int(y) % 2 or r.get("type") not in ("Sen-G", "Gov-G") or r.get("state") not in DIVISION or n < 1:
            continue
        rows.append({"y": int(y), "s": r["state"], "n": int(n), "b": b})
    if len(rows) < 100:
        return None
    by_year = defaultdict(list)
    for x in rows:
        by_year[x["y"]].append(x["b"])
    ym = {y: sum(v) / len(v) for y, v in by_year.items()}
    shared_sd = float(np.std(list(ym.values())))
    for x in rows:
        x["r"] = x["b"] - ym[x["y"]]
    # Division: method of moments on division-year means (variance of the means less the within-group noise they carry).
    groups = defaultdict(list)
    for x in rows:
        groups[(x["y"], DIVISION[x["s"]])].append(x["r"])
    multi = [v for v in groups.values() if len(v) >= 2]
    within = float(np.mean([np.var(v, ddof=1) for v in multi]))
    between = float(np.var([np.mean(v) for v in multi]) - np.mean([within / len(v) for v in multi]))
    division_sd = math.sqrt(max(between, 0.0))
    # State: covariance of the residuals of two races in the same state and year (it carries the division part too).
    by_state = defaultdict(list)
    for x in rows:
        by_state[(x["y"], x["s"])].append(x["r"])
    pairs = [(a, b) for v in by_state.values() for i, a in enumerate(v) for b in v[i + 1:]]
    pa, pb = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
    pair_cov = float(np.mean((pa - pa.mean()) * (pb - pb.mean())))
    state_sd = math.sqrt(max(pair_cov - division_sd ** 2, 0.0))
    # Race-own part: residual variance = a + b / polls; the shared-location part (pair_cov) is taken out of a.
    n = np.array([x["n"] for x in rows], dtype=float)
    r2 = np.array([x["r"] for x in rows]) ** 2
    a, b = np.linalg.lstsq(np.vstack([np.ones_like(n), 1.0 / n]).T, r2, rcond=None)[0]
    idio_const = max(float(a) - pair_cov, 0.0)
    return {"races": len(rows), "years": len(ym), "from": min(ym), "to": max(ym),
            "shared_sd_measured": round(shared_sd, 4), "division_sd": round(division_sd, 4), "state_sd": round(state_sd, 4),
            "idio_const": round(idio_const, 4), "idio_per_poll": round(float(b), 4),
            "location_cov": round(pair_cov, 4), "state_pairs": len(pairs),
            "check": {f"total_sd_{k}_polls": round(math.sqrt(shared_sd ** 2 + pair_cov + idio_const + float(b) / k), 2) for k in (1, 3, 10, 20)},
            "source": "poll-error-history.csv (538 raw polls archive), even-year Senate and governor generals"}


def idio_sd_for_polls(fit: dict, polls: int) -> float:
    return math.sqrt(max(fit["idio_const"] + fit["idio_per_poll"] / max(polls, 1), MIN_IDIO_SD ** 2))


def _seat_specs(chambers: dict, per_race: dict, poll_counts: dict, fit: dict, national_sd: float) -> list[dict]:
    loc_var = fit["division_sd"] ** 2 + fit["state_sd"] ** 2
    proj_idio = math.sqrt(max(PROJECTION_RESIDUAL_SD ** 2 - loc_var, MIN_IDIO_SD ** 2))
    specs = []
    for ch, block in (chambers.get("chambers") or {}).items():
        for it in block.get("items") or []:
            spec = {"chamber": ch, "seat": it["seat"], "state": it["state"], "race": it.get("race"), "kind": it["kind"]}
            if it["kind"] == "not_up":
                spec.update(fixed=it["side"])
            elif it["kind"] == "reading":
                sig = per_race.get(it["race"]) or {}
                polls = int(poll_counts.get(it["race"]) or 1)
                other = max((sig.get("delta_sd") or 0.0) ** 2 - national_sd ** 2, 0.0)   # spending and early-vote fit uncertainty
                own = max(RACE_TOTAL_SD ** 2 - national_sd ** 2 - loc_var, MIN_IDIO_SD ** 2)
                spec.update(center=float(it["undertow"]), idio=math.sqrt(own + other), polls=polls)
            elif it["kind"] == "projection":
                spec.update(center=float(it["undertow"]), idio=proj_idio)
            elif it["kind"] == "rated":
                spec.update(center=RATED_CENTER[it["rating"]], idio=proj_idio)
            else:
                raise ValueError(f"unknown seat kind {it['kind']}")
            specs.append(spec)
    return specs


def _draw(specs, fit, national_sd, n, seed, correlated=True, values=False):
    """Returns an (n, seats) boolean array: True where the D slot wins. not_up seats are filled by their holder.
    With values=True also returns the (n, up seats) outcome margins and the up-seat column indexes."""
    rng = np.random.default_rng(seed)
    up = [i for i, s in enumerate(specs) if "fixed" not in s]
    center = np.array([specs[i]["center"] for i in up])
    idio = np.array([specs[i]["idio"] for i in up])
    out = np.zeros((n, len(specs)), dtype=bool)
    for i, s in enumerate(specs):
        if "fixed" in s:
            out[:, i] = s["fixed"] == "D"
    if correlated:
        states = sorted({specs[i]["state"] for i in up})
        divs = sorted({DIVISION.get(st, "PAC") for st in states})
        s_idx = np.array([states.index(specs[i]["state"]) for i in up])
        d_idx = np.array([divs.index(DIVISION.get(specs[i]["state"], "PAC")) for i in up])
        S = rng.normal(0, national_sd, (n, 1))
        D = rng.normal(0, fit["division_sd"], (n, len(divs)))[:, d_idx]
        T = rng.normal(0, fit["state_sd"], (n, len(states)))[:, s_idx]
        E = rng.normal(0, 1, (n, len(up))) * idio
        val = center + S + D + T + E
    else:   # same spread per race, no shared parts: what counting races one by one assumes
        total = np.sqrt(national_sd ** 2 + fit["division_sd"] ** 2 + fit["state_sd"] ** 2 + idio ** 2)
        val = center + rng.normal(0, 1, (n, len(up))) * total
    out[:, up] = val > 0
    return (out, val, up) if values else out


# The dial (Max, 2026-10-27: one dial drives every panel). The odds follow it: at dial value m every reading and
# projection moves by m minus the national lean, exactly as the site's marginAt and seatMarginAt do, and the spread
# around it stays the same. At m = the lean this reproduces the odds above. Cook-rated governors and seats not up do not move.
DIAL_STEP = 0.5
DIAL_SPAN = 10.0


def _dial_grid(specs, wins, val, up, national, chambers_meta, tracked):
    tie, maj = chambers_meta.get("tie_breaker", "R"), chambers_meta.get("majority") or {}
    values = [round(-DIAL_SPAN + k * DIAL_STEP, 2) for k in range(int(2 * DIAL_SPAN / DIAL_STEP) + 1)]
    movable = np.array([specs[i]["kind"] in ("reading", "projection") for i in up])
    col_of = {i: j for j, i in enumerate(up)}
    grid = {"step": DIAL_STEP, "values": values, "chambers": {ch: [] for ch in maj}, "per_race": {r: [] for r in tracked},
            "rule": "odds at each dial value; the dial moves every reading and projection by (dial - national lean) and keeps the spread"}
    race_cols = {specs[i]["race"]: col_of[i] for i in up if specs[i]["kind"] == "reading" and specs[i]["race"] in tracked}
    w = wins.copy()
    for m in values:
        shifted = val + np.where(movable, m - national, 0.0)
        w[:, up] = shifted > 0
        for ch in maj:
            cols = [i for i, s in enumerate(specs) if s["chamber"] == ch]
            grid["chambers"][ch].append(_summary(w[:, cols], maj[ch], ch, tie)["p_control_d"])
        for r, j in race_cols.items():
            grid["per_race"][r].append(round(float(np.mean(shifted[:, j] > 0)), 4))
    return grid


def _summary(wins: np.ndarray, majority: int | None, chamber: str, tie_breaker: str) -> dict:
    d = wins.sum(axis=1)
    seats = wins.shape[1]
    q = np.quantile(d, SIM_QUANTILES)
    res = {"d_seats_mean": round(float(d.mean()), 2), "d_seats_quantiles": {f"p{int(k * 100):02d}": int(v) for k, v in zip(SIM_QUANTILES, q)},
           "d_seats_90": [int(q[0]), int(q[-1])], "seats": seats}
    if majority:
        if chamber == "SEN":   # 50-50 goes to the tie-breaker's party
            p_d = float(np.mean(d >= majority)) if tie_breaker == "R" else float(np.mean(d >= seats - majority + 1))
        else:
            p_d = float(np.mean(d >= majority))
        res.update({"p_control_d": round(p_d, 4), "p_control_r": round(1 - p_d, 4), "majority": majority})
    hist = Counter(int(x) for x in d)
    res["distribution"] = {str(k): round(v / len(d), 5) for k, v in sorted(hist.items())}
    return res


def run(chambers: dict | None, signals: dict | None, poll_counts: dict, history: list[dict] | None, target_year: int,
        national_sd: float | None, n: int = SIM_N, seed: int = SIM_SEED) -> dict | None:
    if not chambers or not signals or national_sd is None:
        return None
    fit = fit_error_structure(history, target_year)
    if not fit:
        return None
    specs = _seat_specs(chambers, signals.get("per_race") or {}, poll_counts, fit, national_sd)
    wins, val, up = _draw(specs, fit, national_sd, n, seed, correlated=True, values=True)
    indep = _draw(specs, fit, national_sd, n, seed + 1, correlated=False)
    tie, maj = chambers.get("tie_breaker", "R"), chambers.get("majority") or {}
    out = {"version": SIM_VERSION, "sims": n, "seed": seed, "national_sd": round(national_sd, 4), "race_total_sd": RACE_TOTAL_SD, "error_structure": fit,
           "projection_residual_sd": PROJECTION_RESIDUAL_SD, "rated_center": RATED_CENTER,
           "rated_center_note": "assumption, not a fit: Cook ratings turned into centers so untracked governors move with the shared draws",
           "chambers": {}, "independent": {}, "per_seat": {}}
    for ch in ("SEN", "GOV", "HOUSE"):
        cols = [i for i, s in enumerate(specs) if s["chamber"] == ch]
        out["chambers"][ch] = _summary(wins[:, cols], maj.get(ch), ch, tie)
        out["independent"][ch] = _summary(indep[:, cols], maj.get(ch), ch, tie)
        out["independent"][ch].pop("distribution", None)
    # The same draws with the national lean taken out of every center: what the chambers look like if the polls are
    # right on average. Cook-rated governors carry no lean, so they are unchanged.
    nat = next((i["parts"]["national_lean"] for c in chambers["chambers"].values() for i in c["items"] if i.get("parts") and "national_lean" in i["parts"]), 0.0)
    flat = [dict(s, center=s["center"] - nat) if s["kind"] in ("reading", "projection") else s for s in specs]
    pw = _draw(flat, fit, national_sd, n, seed, correlated=True)
    out["polls_no_lean"] = {"national_lean_removed": nat, "chambers": {}}
    for ch in ("SEN", "GOV", "HOUSE"):
        cols = [i for i, s in enumerate(specs) if s["chamber"] == ch]
        summ = _summary(pw[:, cols], maj.get(ch), ch, tie)
        summ.pop("distribution", None)
        out["polls_no_lean"]["chambers"][ch] = summ
    tracked = sorted({s["race"] for s in specs if s["kind"] == "reading" and s["race"]})
    out["dial"] = _dial_grid(specs, wins, val, up, nat, chambers, tracked)
    p = wins.mean(axis=0)
    for i, s in enumerate(specs):
        if "fixed" in s:
            continue
        key = s["race"] or s["seat"]
        sd_total = math.sqrt(national_sd ** 2 + fit["division_sd"] ** 2 + fit["state_sd"] ** 2 + s["idio"] ** 2)
        out["per_seat"][key] = {"chamber": s["chamber"], "kind": s["kind"], "center": round(s["center"], 4), "sd": round(sd_total, 4),
                                "p_d": round(float(p[i]), 4), "polls": s.get("polls")}
    return out
