"""Other ways to read the same polls (Max, 2026-10-29: "what if we made our own?"; "Go").

Four models beside the bet, each built here from the sealed data and nothing else: a center for every seat up this year,
a default dial of 0 (its own reading, no lean), a national spread measured on its own backtest, and odds from the same
correlated simulation the bet uses (analysis/simulate.py, run_model). None of them is graded; the bet is. The site only
reads this block.

  polls         the polling average as published; untracked seats carry the 2024 result + generic-ballot shift + incumbency
  fundamentals  no 2026 race polls: 2024 result + the archive's average midterm swing against the president's party + incumbency
  blend         forecaster-style: polls blended with the 2024-result prior by poll count (the Senate partisan-prior variances,
                applied to every office alike); untracked seats as in polls; untracked governors keep Cook (the swing base failed 2022)
  ratings       Cook's ratings turned into margins (simulate.RATED_CENTER) for every seat up

Backtest: every Senate and governor race in the 538 archive, 2010 to 2024, each year scored with only earlier years
(fundamentals on the midterm years, where the swing is defined). Ratings has no archive and says so.
"""
from __future__ import annotations

import math
from collections import defaultdict

MODELS_VERSION = "1.0"
PRESIDENT_PARTY = {2002: "R", 2006: "R", 2010: "D", 2014: "D", 2018: "R", 2022: "D", 2026: "R"}   # president's party at each midterm
BACKTEST_YEARS = range(2010, 2025, 2)
BACKTEST_SIGMA = 5.0
MIN_RACES_PER_YEAR = 10
KEYS = ("polls", "fundamentals", "blend", "ratings")
NAMES = {"polls": "Polls only", "fundamentals": "Fundamentals", "blend": "Forecaster blend", "ratings": "Ratings"}
SHORT = {"polls": "Polls", "fundamentals": "Fund.", "blend": "Blend", "ratings": "Ratings"}


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _archive(history: list[dict] | None) -> tuple[dict, list[dict]]:
    """(presidential margins by (year, state), Senate and governor general races with their prior presidential margin)."""
    rows = list(history or [])
    pres = {(int(r["year"]), r["state"]): float(r["actual_margin"]) for r in rows if r.get("type") == "Pres-G" and len(r.get("state", "")) == 2}
    races = []
    for r in rows:
        if r.get("type") not in ("Sen-G", "Gov-G") or len(r.get("state", "")) != 2:
            continue
        y = int(r["year"])
        py = [p for (p, st) in pres if st == r["state"] and p < y]
        try:
            pm, am, n = float(r["poll_margin"]), float(r["actual_margin"]), int(float(r["n_polls"]))
        except (KeyError, TypeError, ValueError):
            continue
        if py:
            races.append({"y": y, "st": r["state"], "office": r["type"][:3], "n": n, "poll": pm, "act": am, "pres": pres[(max(py), r["state"])]})
    return pres, races


def midterm_swing(races: list[dict], before_year: int) -> dict | None:
    """The fundamentals environment, with no polls: in each past midterm the mean realized swing of Senate and governor
    results against the president's party, measured from each state's prior presidential margin. Positive = toward the
    party out of the White House."""
    by_year = defaultdict(list)
    for x in races:
        if x["y"] in PRESIDENT_PARTY and x["y"] < before_year:
            sign = 1.0 if PRESIDENT_PARTY[x["y"]] == "R" else -1.0
            by_year[x["y"]].append(sign * (x["act"] - x["pres"]))
    years = {y: sum(v) / len(v) for y, v in by_year.items() if len(v) >= MIN_RACES_PER_YEAR}
    if len(years) < 2:
        return None
    vals = list(years.values())
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))
    return {"swing_against_president": round(mean, 4), "sd_across_years": round(sd, 4), "years": {str(y): round(v, 2) for y, v in sorted(years.items())},
            "races": sum(len(v) for v in by_year.values())}


def _band(n: int, bands) -> str:
    return next(f"{lo}-{hi}" for lo, hi in bands if lo <= max(n, 1) <= hi)


def blend_weight(partisan: dict, polls: int, bands) -> float:
    """Weight on the polls: v_prior / (v_prior + v_polls(n)), the partisan-prior variances fit on the Senate archive."""
    return partisan["v_prior"] / (partisan["v_prior"] + partisan["v_polls"][_band(polls, bands)])


def backtest(history: list[dict] | None, bands) -> dict | None:
    """Year held out: polls, fundamentals and the blend on every archive Senate and governor race, 2010 to 2024. Returns
    scores, and each model's national spread (the standard deviation across years of its mean miss), which the simulation
    uses as that model's national_sd."""
    _, races = _archive(history)
    if len(races) < 100:
        return None
    env = defaultdict(list)
    for x in races:
        env[x["y"]].append(x["poll"] - x["pres"])
    env = {y: sum(v) / len(v) for y, v in env.items()}
    scored = []
    for y in BACKTEST_YEARS:
        past = [x for x in races if x["y"] < y]
        if not past:
            continue
        v_prior = sum((x["act"] - x["pres"] - env[x["y"]]) ** 2 for x in past) / len(past)
        v_polls = {}
        for lo, hi in bands:
            e = [(x["act"] - x["poll"]) ** 2 for x in past if lo <= x["n"] <= hi]
            v_polls[f"{lo}-{hi}"] = sum(e) / len(e) if e else None
        swing = midterm_swing(races, y)
        for x in (x for x in races if x["y"] == y):
            vq = v_polls[_band(x["n"], bands)]
            w = v_prior / (v_prior + vq) if vq else 1.0
            row = {**x, "w": w, "blend": w * x["poll"] + (1 - w) * (x["pres"] + env[y])}
            if y in PRESIDENT_PARTY and swing:
                sign = 1.0 if PRESIDENT_PARTY[y] == "R" else -1.0
                row["fund"] = x["pres"] + sign * swing["swing_against_president"]
            scored.append(row)

    def score(rows, key):
        s = [x for x in rows if key in x]
        if not s:
            return None
        years = defaultdict(list)
        for x in s:
            years[x["y"]].append(x["act"] - x[key])
        ym = [sum(v) / len(v) for v in years.values()]
        nat_sd = math.sqrt(sum((m - sum(ym) / len(ym)) ** 2 for m in ym) / (len(ym) - 1)) if len(ym) > 1 else None
        return {"races": len(s), "years": len(years), "mae": round(sum(abs(x[key] - x["act"]) for x in s) / len(s), 3),
                "winner_right": round(sum(1 for x in s if (x[key] > 0) == (x["act"] > 0)) / len(s), 3),
                "brier": round(sum((min(max(_phi(x[key] / BACKTEST_SIGMA), .03), .97) - (x["act"] > 0)) ** 2 for x in s) / len(s), 4),
                "national_sd": round(nat_sd, 4) if nat_sd else None}

    mid = [x for x in scored if "fund" in x]
    return {"years": f"{BACKTEST_YEARS.start}-{BACKTEST_YEARS.stop - 1}", "sigma": BACKTEST_SIGMA, "source": "poll-error-history.csv (538 archive), Senate and governor generals, each year fit on earlier years only",
            "all_years": {"polls": score(scored, "poll"), "blend": score(scored, "blend")},
            "midterms": {"polls": score(mid, "poll"), "fundamentals": score(mid, "fund"), "blend": score(mid, "blend")},
            "ratings": None, "ratings_note": "Cook's past ratings are not in the archive, so the ratings model has no record here"}


def build(chambers: dict | None, signals: dict | None, history: list[dict] | None, target_year: int, poll_counts: dict, fit: dict | None,
          partisan: dict | None, bands, incumbency_bonus: dict, rated_center: dict, race_total_sd: float, projection_residual_sd: float, min_idio_sd: float,
          run_model) -> dict | None:
    """derived.models: centers, counts at the default dial, odds and the backtest for the four models. None when the
    chambers block, the error fit or the archive is absent."""
    if not chambers or not fit or not history:
        return None
    _, races = _archive(history)
    swing = midterm_swing(races, target_year)
    bt = backtest(history, bands)
    if not swing or not bt:
        return None
    shift = float(chambers.get("shift_toward_d") or 0.0)
    loc_var = fit["division_sd"] ** 2 + fit["state_sd"] ** 2
    proj_idio = math.sqrt(max(projection_residual_sd ** 2 - loc_var, min_idio_sd ** 2))
    shared = float(fit["shared_sd_measured"])
    nat_sd = {"polls": shared, "ratings": shared,
              "fundamentals": float((bt["midterms"]["fundamentals"] or {}).get("national_sd") or swing["sd_across_years"]),
              "blend": float((bt["all_years"]["blend"] or {}).get("national_sd") or shared)}
    out = {"version": MODELS_VERSION, "note": "other ways to read the same polls; none is graded, the bet is", "fundamentals_env": swing, "backtest": bt,
           "blend_weights": "polls weight = v_prior / (v_prior + v_polls by poll count), partisan_model variances", "models": {}}
    meta = {"tie_breaker": chambers.get("tie_breaker", "R"), "majority": chambers.get("majority") or {}}
    tracked = sorted(it["race"] for c in chambers["chambers"].values() for it in c["items"] if it["kind"] == "reading" and it.get("race"))
    for key in KEYS:
        if key == "blend" and not partisan:
            continue
        centers, specs, counts = {}, [], {}
        for ch, block in chambers["chambers"].items():
            d = r = u = 0
            for it in block["items"]:
                sid = it.get("race") or it["seat"]
                spec = {"chamber": ch, "seat": it["seat"], "state": it["state"], "race": it.get("race"), "kind": it["kind"]}
                if it["kind"] == "not_up":
                    spec["fixed"] = it["side"]
                    specs.append(spec)
                    continue
                ib = it.get("incumbent_on_ballot")
                bonus = incumbency_bonus["D"] if ib == "D" else -incumbency_bonus["R"] if ib == "R" else 0.0
                pres = it.get("pres2024_d_minus_r")
                fund = (pres + swing["swing_against_president"] + bonus) if pres is not None else None
                base = (pres + shift + bonus) if pres is not None else None
                rated = rated_center.get(it.get("rating"))
                if key == "ratings":
                    c = rated
                elif key == "fundamentals":
                    c = fund if fund is not None else rated
                elif it["kind"] == "reading":
                    polls = float(it["polls"])
                    if key == "polls":
                        c = polls
                    else:
                        n = int(poll_counts.get(it["race"]) or 1)
                        w = blend_weight(partisan, n, bands)
                        c = w * polls + (1 - w) * base if base is not None else polls
                elif it["kind"] == "projection":
                    c = float(it["base"])
                else:   # rated governor: Cook, as the bet does
                    c = rated
                if c is None:
                    raise ValueError(f"model {key}: no center for {sid}")
                centers[sid] = round(float(c), 4)
                own = math.sqrt(max(race_total_sd ** 2 - nat_sd[key] ** 2 - loc_var, min_idio_sd ** 2)) if it["kind"] == "reading" and key in ("polls", "blend") else proj_idio
                spec.update(center=float(c), idio=own, movable=True)
                specs.append(spec)
                if c >= 0.05:
                    d += 1
                elif c <= -0.05:
                    r += 1
                else:
                    u += 1
            counts[ch] = {"D": d, "R": r, "undecided": u}
        sim = run_model(specs, fit, nat_sd[key], meta, tracked)
        out["models"][key] = {"key": key, "name": NAMES[key], "short": SHORT[key], "default_dial": 0.0, "national_sd": round(nat_sd[key], 4),
                              "centers": centers, "up_at_default": counts, "simulation": sim}
    return out
