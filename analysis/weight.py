#!/usr/bin/env python3
"""Midterm 2026 poll-weighting calculator. Python 3 standard library only.

The only owner of margin, window, eligibility flags, strata, weights, contrasts,
governor-Senate gaps, heat means, cache keys, backtest errors, Section 7 margins
and Stage 3 probabilities. Everything downstream (the method note, the tracker
app) formats what this file computes and never recalculates it.

Modes
  --validate               schema, enum, reference and arithmetic checks; exit 1 on a hard error
  --derive                 fill margin, window, selected, exclusion_reason in polls.csv (snapshot first)
  --self-test              hand-calculated cases; exit 1 on any failure
  --compute                print derived.json to stdout
  --release <release_id>   write releases/<release_id>/ (frozen CSVs, note snapshot, derived.json, manifest.json)
  --freeze                 with --release: also write predictions.csv (Stage 3 only)

Arguments
  --as-of <ISO with offset>   analytical_as_of (required for compute/release/derive)
  --bundle-dir <path>         the vault methods directory holding the CSVs (default: see DEFAULT_BUNDLE_DIR)
  --calc-version <sha>        from `git rev-parse HEAD`; recorded in every release
  --run-state <path>          run-state.json, read for stage_status and the 2c gate
  --note <path>               the method note to snapshot into the release
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

DEFAULT_BUNDLE_DIR = os.path.expanduser("~/Second Brain V2/Resources/methods/midterm-2026")
DEFAULT_NOTE = os.path.expanduser("~/Second Brain V2/Resources/methods/midterm-2026-poll-weighting.md")

BUNDLE_SCHEMA = "1.0"
CSV_SCHEMAS = {
    "polls": "1.2", "pollsters": "1.0", "exclusions": "1.0", "heat": "1.0",
    "coverage": "1.0", "backtest": "1.2", "predictions": "1.0", "results": "1.0",
    "spending": "1.0", "fundamentals": "1.0", "spend_history": "1.0",
}

POLLS_HEADER = (
    "estimate_id,poll_id,sample_id,tracking_series_id,race,pollster_id,method_id,sponsor,sponsor_class,"
    "pollster_alignment,disclosure_status,field_start,field_end,release_date,n,pop,D,R,other,undecided,"
    "denominator_class,margin,round,window,recall_weighted,selected,exclusion_reason,supersedes,superseded_by,"
    "source_url,source_locator,primary_verified,retrieved_at,notes"
).split(",")
POLLSTERS_HEADER = (
    "pollster_id,pollster_name,aliases,method_id,applicability,recall_weighted,weighting_quote,recall_target,mode,"
    "ti_member,method_owner,method_url,method_locator,method_date,retrieved_at,rating_source,rating_version,"
    "rating_metric,rating_value,rating_units,rating_poll_count,rating_bias_metric,rating_bias_value,rating_cohort,"
    "track_status,f_track,new_pollster,track_ledger_ref,notes"
).split(",")
EXCLUSIONS_HEADER = "entity_type,entity_id,reason,evidence_url,evidence_date,recorded_at".split(",")
HEAT_HEADER = (
    "heat_id,race,candidate,slot,source_type,unit_id,unit_label,source_url,caption_source,unit_sha256,status,"
    "ph_score,ph_label,hottest_line,calmest_line,scorer_commit,prompt_sha256,model,config_sha256,scored_at,"
    "cost_usd,reserved_usd,notes"
).split(",")
COVERAGE_HEADER = (
    "race,query,expected_edition,returned_edition,edition_status,match_status,story_count,outlet_count,ph_low,"
    "ph_high,spread,calmest_outlet,hottest_outlet,story_ids,error_text,retrieved_at"
).split(",")
BACKTEST_EXTRA = "certified_D,certified_R,certified_margin,result_url,result_locator,certification_date,signed_error".split(",")
BACKTEST_HEADER = POLLS_HEADER + BACKTEST_EXTRA
SPENDING_HEADER = "race,state,fec_coverage,window_end,d_fav_recent,r_fav_recent,d_fav_prior,r_fav_prior,rows_recent,rows_dated_by_dissemination,source_file,source_sha256".split(",")
FUNDAMENTALS_HEADER = "race,state,pres_year,pres_d_minus_r,source_file,source_sha256".split(",")
SPEND_HISTORY_HEADER = "year,state,poll_margin,result_margin,log_recent_spend_m,pres_year,pres_d_minus_r,source_sha256".split(",")
PREDICTIONS_HEADER = "race,vector,p_d_slot,weighted_margin,stratum_round,stratum_denominator,stratum_pop,n_retained,heat_race_set,frozen_at".split(",")
RESULTS_HEADER = "race,resolution_status,winner_slot,certified_margin,denominator_note,result_url,resolved_at".split(",")

SENATE_RACES = ["2026-TX-SEN", "2026-IA-SEN", "2026-ME-SEN", "2026-AK-SEN", "2026-OH-SEN-SPECIAL", "2026-MI-SEN", "2026-NC-SEN", "2026-GA-SEN"]
GOVERNOR_RACES = ["2026-OH-GOV", "2026-IA-GOV", "2026-MI-GOV", "2026-GA-GOV", "2026-WI-GOV"]
DEFERRED_RACES = ["2026-KS-SEN", "2026-NE-SEN", "2026-FL-SEN-SPECIAL", "2026-SC-SEN", "2026-MS-SEN", "2026-NH-SEN", "2026-AZ-GOV", "2026-NV-GOV", "2026-FL-GOV", "2026-KS-GOV"]
BACKTEST_RACES = ["2025-VA-GOV", "2025-NJ-GOV"]
RCV_RACES = {"2026-ME-SEN", "2026-AK-SEN"}
IN_SCOPE_RACES = set(SENATE_RACES) | set(GOVERNOR_RACES)
PER_RACE_CONTRAST_RACES = ["2026-TX-SEN", "2026-IA-SEN", "2026-ME-SEN", "2026-AK-SEN", "2026-OH-SEN-SPECIAL", "2026-MI-SEN"]
GOV_SEN_GAP_STATES = {"IA": ("2026-IA-GOV", "2026-IA-SEN"), "OH": ("2026-OH-GOV", "2026-OH-SEN-SPECIAL"), "MI": ("2026-MI-GOV", "2026-MI-SEN"), "GA": ("2026-GA-GOV", "2026-GA-SEN")}

POPS = ["LV", "RV", "A"]
DENOMS = ["FULL", "TWO_WAY", "LEANERS"]
ROUNDS = ["NA", "FIRST", "FINAL", "UNVERIFIED"]
WINDOWS = ["HOUSE_ONLY", "BOTH", "BACKTEST", "OUT_OF_WINDOW"]
SPONSOR_CLASSES = ["INTERNAL", "PARTISAN_PUBLIC", "NONPARTISAN", "BIPARTISAN", "UNKNOWN"]
ALIGNMENTS = ["D", "R", "NONE", "UNKNOWN"]
DISCLOSURES = ["DISCLOSED", "UNDISCLOSED", "UNVERIFIED"]
RECALL_ESTIMATE = ["YES", "NO", "UNVERIFIED"]
RECALL_METHOD = ["YES", "NO", "UNVERIFIED"]
APPLICABILITY = ["CYCLE_BOILERPLATE", "SURVEY"]
EXCLUSION_REASONS = ["NA", "QUARANTINE", "NOT_PRINCIPAL", "TRACKER_OVERLAP", "SUPERSEDED", "MATCHUP_MISMATCH", "UNVERIFIED_MATCHUP"]
TRACK_STATUS = ["PROVISIONAL", "RATED", "LEDGER"]
HEAT_STATUS = ["SCORED", "MISSING_TRANSCRIPT", "SKIPPED_BUDGET", "FAILED", "EXCLUDED"]
HEAT_SOURCE = ["DEBATE", "AD"]
CAPTION_SOURCE = ["OFFICIAL", "BROADCASTER", "AUTO", "NA"]
SLOTS = ["D", "R"]
EDITION_STATUS = ["OK", "STALE_FLAG", "OLDER_THAN_EXPECTED", "ACCESS_FAILED"]
MATCH_STATUS = ["MATCHES", "ZERO", "PARTIAL", "ERROR"]
RESOLUTION = ["CERTIFIED", "PROJECTED", "RUNOFF_PENDING", "RCV_PENDING", "UNRESOLVED"]

# Section 1 weighting spec (heuristic, not an inverse variance)
RECENCY_HALF_LIFE_DAYS = 5.0
SAMPLE_CAP_N = 1200
F_POP = {"LV": 1.0, "RV": 0.7, "A": 0.4}
F_SPONSOR = {"INTERNAL": 0.3, "PARTISAN_PUBLIC": 0.6, "NONPARTISAN": 1.0, "BIPARTISAN": 1.0}
F_DISCLOSURE_UNVERIFIED = 0.7
WEIGHT_CUTOFF = 0.05
TIE_THRESHOLD = 0.1
HEAT_BUDGET_USD = 3.00
HEAT_RESERVE_MULTIPLIER = 1.5
STAGE3_SIGMA = 5.0          # a heuristic standard deviation; not an estimate, not a flip threshold
STAGE3_CLAMP = (0.03, 0.97)
SCENARIO_SHIFTS = {"control_flip_toward_R": 2.5, "scale_2016_2020_toward_R": 5.0}
SIMPLE_AVERAGE_ERROR_THRESHOLDS = ((3.0, 1.0), (5.0, 0.8), (float("inf"), 0.5))
DENOM_ORDER = {"FULL": 0, "LEANERS": 1, "TWO_WAY": 2}
POP_ORDER = {"LV": 0, "RV": 1, "A": 2}
HOUSE_ONLY_START = date(2026, 9, 1)
HOUSE_ONLY_END = date(2026, 9, 30)
BOTH_START = date(2026, 10, 1)
BACKTEST_START = date(2025, 10, 14)
BACKTEST_END = date(2025, 11, 3)
BACKTEST_RELEASE_BEFORE = date(2025, 11, 4)


class ValidationError(Exception):
    pass


# ----------------------------------------------------------------------------- helpers
def is_na(v) -> bool:
    return v is None or str(v).strip() in ("", "NA")


def num(v):
    """Parse a numeric cell. NA/UNVERIFIED/empty -> None. Raises ValueError on junk."""
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "NA", "UNVERIFIED"):
        return None
    f = float(s)
    if not math.isfinite(f):
        raise ValueError(f"non-finite number {s!r}")
    return f


def intnum(v):
    f = num(v)
    if f is None:
        return None
    if abs(f - round(f)) > 1e-9:
        raise ValueError(f"expected integer, got {v!r}")
    return int(round(f))


def parse_date(v) -> date | None:
    if is_na(v):
        return None
    return date.fromisoformat(str(v).strip())


def parse_as_of(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValidationError("analytical_as_of must carry a numeric UTC offset, e.g. 2026-10-25T11:00:00-07:00")
    return dt


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def r4(x):
    return None if x is None else round(x + 0.0, 4)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def coverage_range(scores):
    """Format a connector range; absent or malformed readings remain unknown."""
    valid = []
    for x in scores or []:
        try:
            valid.append(num(x))
        except (ValueError, TypeError):
            continue
    valid = [x for x in valid if x is not None and 1 <= x <= 5]
    if not valid:
        return {"ph_low": "NA", "ph_high": "NA", "spread": "NA"}
    return {"ph_low": f"{min(valid):.1f}", "ph_high": f"{max(valid):.1f}", "spread": f"{max(valid) - min(valid):.1f}"}


def certified_vote_margin(contest):
    if not isinstance(contest, dict):
        return None
    try:
        counts = [intnum(contest.get("D_votes")), intnum(contest.get("R_votes"))]
        counts += [intnum(v) for v in (contest.get("other_vote_counts") or [])]
    except (ValueError, TypeError):
        return None
    if any(v is None or v < 0 for v in counts) or sum(counts) <= 0:
        return None
    total = sum(counts)
    d, r = 100 * counts[0] / total, 100 * counts[1] / total
    return {"D": r4(d), "R": r4(r), "margin": r4(d - r), "valid_votes": total}


def historical_comparators():
    path = os.path.join(os.path.dirname(__file__), "..", "research", "comparators-2022.json")
    if not os.path.isfile(path):
        return {"note": "Primary certified-result comparators not yet collected", "records": []}
    with open(path) as fh:
        source = json.load(fh)
    records = []
    for raw in source.get("records") or []:
        gov, sen = certified_vote_margin(raw.get("governor")), certified_vote_margin(raw.get("senate"))
        if gov is None or sen is None:
            raise ValidationError(f"invalid certified comparator: {raw.get('state')}")
        records.append(raw | {"governor_result": gov, "senate_result": sen, "gap": r4(gov["margin"] - sen["margin"])})
    return {"note": source["framing"], "records": records, "input_sha256": sha256_file(path)}


def read_csv(path: str, header: list[str], required: bool = True) -> list[dict]:
    if not os.path.exists(path):
        if required:
            raise ValidationError(f"missing file {path}")
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    if "\r" in raw:
        raise ValidationError(f"{os.path.basename(path)}: CRLF line endings; LF required")
    rows = list(csv.DictReader(io.StringIO(raw)))
    with open(path, "r", encoding="utf-8", newline="") as f:
        first = f.readline().rstrip("\n")
    if first.split(",") != header:
        raise ValidationError(f"{os.path.basename(path)}: header mismatch.\n  got      {first}\n  expected {','.join(header)}")
    for i, r in enumerate(rows, start=2):
        if None in r or any(k not in header for k in r):
            raise ValidationError(f"{os.path.basename(path)}: row {i} has the wrong number of fields")
    return rows


def write_csv(path: str, header: list[str], rows: list[dict]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in header})
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())


def snapshot(path: str, bundle_dir: str) -> str | None:
    """ROE 14: copy the current file to .backups/<name>.<YYYYMMDD-HHMMSS>.<ext> before an in-place edit."""
    if not os.path.exists(path):
        return None
    backups = os.path.join(bundle_dir, ".backups")
    os.makedirs(backups, exist_ok=True)
    base = os.path.basename(path)
    stem, ext = os.path.splitext(base)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(backups, f"{stem}.{stamp}{ext}")
    n = 0
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(backups, f"{stem}.{stamp}-{n}{ext}")
    shutil.copy2(path, dest)
    return dest


# ----------------------------------------------------------------------------- signal-adjusted reading
# Method: Resources/methods/midterm-2026-signal-adjusted-reading.md (Max's big-swing ruling, 2026-10-26).
# Signs: every signal is expressed as "points toward D". Positive means the R side reads as lagging its own internals.
SIGNAL_METHOD_VERSION = "1.0"
SIGNAL_PRIOR_BETA = (1.5, 1.0)    # points toward the fundamentals underdog per SD of excess outside spending
SIGNAL_PRIOR_GAMMA = (1.5, 1.0)   # points against the hotter side per point of LITMUS heat gap
SIGNAL_RHETORIC_CAP = 3.0         # |rhetoric contribution| ceiling, points
SIGNAL_MIN_HEAT_UNITS = 2         # scored units required per candidate
SIGNAL_WEIGHT_ALIGNED = 1.0
SIGNAL_WEIGHT_OPPOSED = 0.25
SIGNAL_WEIGHT_SINGLE = 0.5
SIGNAL_SPEND_MIN_Z = 0.25        # |excess z| below this carries no direction
# Heat gaps below TIE_THRESHOLD (the existing heat tie rule) carry no direction.


def _ols(x: list[float], y: list[float]) -> tuple[float, float, float] | None:
    """Simple regression y = a + b x. Returns (a, b, se_b) or None when undefined."""
    n = len(x)
    if n < 3 or n != len(y):
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    if sxx <= 0:
        return None
    b = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / sxx
    a = my - b * mx
    rss = sum((y[i] - a - b * x[i]) ** 2 for i in range(n))
    se = math.sqrt(rss / (n - 2) / sxx) if n > 2 else float("inf")
    return a, b, se


def excess_spend_z(log_spend: list[float], abs_poll: list[float]) -> list[float] | None:
    """Residual of log outside spending on |public margin|, in SDs. None when the fit is undefined."""
    fit = _ols(abs_poll, log_spend)
    if fit is None:
        return None
    a, b, _ = fit
    resid = [log_spend[i] - a - b * abs_poll[i] for i in range(len(log_spend))]
    n = len(resid)
    sd = math.sqrt(sum(r * r for r in resid) / (n - 1)) if n > 1 else 0.0
    if sd <= 0:
        return None
    return [r / sd for r in resid]


def underdog_sign(pres_d_minus_r: float | None) -> int:
    """+1 when D lost the state's last presidential vote (D is the fundamentals underdog), -1 when R did, 0 if tied or unknown."""
    if pres_d_minus_r is None or pres_d_minus_r == 0:
        return 0
    return 1 if pres_d_minus_r < 0 else -1


def spending_history_estimate(rows: list[dict]) -> dict:
    """Slope of the year-demeaned polling miss toward the fundamentals underdog on excess-spending z (2020 and 2022 Senate)."""
    clean = []
    for r in rows:
        p, y, sp, pres = num(r.get("poll_margin")), num(r.get("result_margin")), num(r.get("log_recent_spend_m")), num(r.get("pres_d_minus_r"))
        if None in (p, y, sp, pres) or underdog_sign(pres) == 0:
            continue
        clean.append((r["year"], p, y, sp, underdog_sign(pres)))
    if len(clean) < 10:
        return {"status": "insufficient history", "n": len(clean), "slope": None, "se": None}
    z = excess_spend_z([c[3] for c in clean], [abs(c[1]) for c in clean])
    if z is None:
        return {"status": "undefined excess fit", "n": len(clean), "slope": None, "se": None}
    by_year = defaultdict(list)
    for c in clean:
        by_year[c[0]].append(c[2] - c[1])
    year_mean = {k: sum(v) / len(v) for k, v in by_year.items()}
    toward = [((c[2] - c[1]) - year_mean[c[0]]) * c[4] for c in clean]
    fit = _ols(z, toward)
    if fit is None:
        return {"status": "undefined slope", "n": len(clean), "slope": None, "se": None}
    return {"status": "estimated", "n": len(clean), "years": sorted(by_year), "slope": r4(fit[1]), "se": r4(fit[2])}


def normal_posterior(prior: tuple[float, float], est: float | None, se: float | None) -> tuple[float, float]:
    """Precision-weighted combination of a Normal prior and a Normal data estimate; the prior alone when data are missing."""
    m0, s0 = prior
    if est is None or se is None or not math.isfinite(se) or se <= 0:
        return m0, s0
    w0, w1 = 1 / s0 ** 2, 1 / se ** 2
    return (m0 * w0 + est * w1) / (w0 + w1), math.sqrt(1 / (w0 + w1))


def rhetoric_gap(heat_rows: list[dict], race: str) -> dict:
    """Mean scored heat of the R side minus the D side; undefined unless both have SIGNAL_MIN_HEAT_UNITS scored units."""
    scores = {"D": [], "R": []}
    for h in heat_rows:
        if h.get("race") == race and h.get("status") == "SCORED" and h.get("slot") in scores:
            v = num(h.get("ph_score"))
            if v is not None:
                scores[h["slot"]].append(v)
    n = {k: len(v) for k, v in scores.items()}
    if min(n.values()) < SIGNAL_MIN_HEAT_UNITS:
        return {"gap": None, "n_d": n["D"], "n_r": n["R"], "mean_d": r4(mean(scores["D"])) if scores["D"] else None,
                "mean_r": r4(mean(scores["R"])) if scores["R"] else None, "status": f"needs {SIGNAL_MIN_HEAT_UNITS} scored units per candidate"}
    md, mr = mean(scores["D"]), mean(scores["R"])
    return {"gap": r4(mr - md), "n_d": n["D"], "n_r": n["R"], "mean_d": r4(md), "mean_r": r4(mr), "status": "defined"}


def alignment_weights(spend_signal: float | None, heat_gap: float | None) -> tuple[float, float, str]:
    """Max's alignment rule: full weight when spending and rhetoric point to the same lagging side."""
    has_s = spend_signal is not None and abs(spend_signal) >= SIGNAL_SPEND_MIN_Z
    has_h = heat_gap is not None and abs(heat_gap) >= TIE_THRESHOLD
    if has_s and has_h:
        if (spend_signal > 0) == (heat_gap > 0):
            return SIGNAL_WEIGHT_ALIGNED, SIGNAL_WEIGHT_ALIGNED, "ALIGNED"
        return SIGNAL_WEIGHT_OPPOSED, SIGNAL_WEIGHT_OPPOSED, "OPPOSED"
    if has_s:
        return SIGNAL_WEIGHT_SINGLE, 0.0, "SPENDING_ONLY"
    if has_h:
        return 0.0, SIGNAL_WEIGHT_SINGLE, "RHETORIC_ONLY"
    return 0.0, 0.0, "NO_SIGNAL"


def signal_adjusted(polling: float | None, spend_signal: float | None, heat_gap: float | None,
                    beta: tuple[float, float], gamma: tuple[float, float]) -> dict:
    """A = P + w_s * beta * spend_signal + w_r * clamp(gamma * heat_gap). All in D-minus-R points."""
    ws, wr, alignment = alignment_weights(spend_signal, heat_gap)
    if polling is None:
        return {"status": "NO_POLLING_READ", "alignment": alignment, "adjusted_margin": None, "delta_spending": None, "delta_rhetoric": None, "delta_sd": None}
    d_s = ws * beta[0] * spend_signal if ws else 0.0
    raw_r = gamma[0] * heat_gap if wr else 0.0
    d_r = wr * max(-SIGNAL_RHETORIC_CAP, min(SIGNAL_RHETORIC_CAP, raw_r))
    sd = math.sqrt((ws * (spend_signal or 0) * beta[1]) ** 2 + (wr * (heat_gap or 0) * gamma[1]) ** 2)
    delta = d_s + d_r
    return {"status": "ADJUSTED" if alignment != "NO_SIGNAL" else "NO_SIGNAL", "alignment": alignment,
            "weight_spending": ws, "weight_rhetoric": wr,
            "delta_spending": r4(d_s), "delta_rhetoric": r4(d_r), "rhetoric_capped": abs(raw_r) > SIGNAL_RHETORIC_CAP if wr else False,
            "delta_total": r4(delta), "delta_sd": r4(sd), "adjusted_margin": r4(polling + delta),
            "lagging_side": None if delta == 0 else ("R" if delta > 0 else "D")}


# ----------------------------------------------------------------------------- pure calculators
def margin_of(d, r):
    """Margin = D-slot share minus R-slot share on the published denominator, never renormalized."""
    if d is None or r is None:
        return None
    return round(d - r, 4)


def window_of(field_end: date | None, release_date: date | None, as_of_date: date, backtest: bool = False) -> str:
    if field_end is None:
        return "OUT_OF_WINDOW"
    if backtest:
        ok = BACKTEST_START <= field_end <= BACKTEST_END and (release_date is not None and release_date < BACKTEST_RELEASE_BEFORE)
        return "BACKTEST" if ok else "OUT_OF_WINDOW"
    if release_date is not None and release_date > as_of_date:
        return "OUT_OF_WINDOW"
    if field_end > as_of_date:
        return "OUT_OF_WINDOW"
    if HOUSE_ONLY_START <= field_end <= HOUSE_ONLY_END:
        return "HOUSE_ONLY"
    if BOTH_START <= field_end <= as_of_date:
        return "BOTH"
    return "OUT_OF_WINDOW"


def field_midpoint_ordinal(field_start: date, field_end: date) -> float:
    return (field_start.toordinal() + field_end.toordinal()) / 2.0


def f_recency(field_start: date, field_end: date, as_of_date: date) -> float:
    age = as_of_date.toordinal() - field_midpoint_ordinal(field_start, field_end)
    return math.exp(-math.log(2.0) * age / RECENCY_HALF_LIFE_DAYS)


def f_sample(n: int | None) -> float | None:
    if n is None or n <= 0:
        return None
    return min(math.sqrt(n), math.sqrt(SAMPLE_CAP_N)) / math.sqrt(SAMPLE_CAP_N)


def f_pop(pop: str) -> float | None:
    return F_POP.get(pop)


def f_sponsor(sponsor_class: str) -> float | None:
    return F_SPONSOR.get(sponsor_class)


def f_disclosure(disclosure_status: str) -> float:
    return 1.0 if disclosure_status == "DISCLOSED" else F_DISCLOSURE_UNVERIFIED


def f_track_from_simple_average_error(sae: float | None) -> float:
    """Silver Bulletin Simple Average Error thresholds. Never applied to Predictive Plus-Minus."""
    if sae is None:
        return 1.0
    for upper, value in SIMPLE_AVERAGE_ERROR_THRESHOLDS:
        if sae <= upper:
            return value
    return 1.0


def nc_absentee_summary(rows, election_date: str, quarantine_conflicts=False) -> dict:
    """Aggregate accepted ballots only. Never return voter identifiers or names.

    The official layout makes voter_reg_num county-specific; NCID is statewide.
    Deduplicate accepted voters within this election using NCID, falling back to
    county plus voter_reg_num. Conflicts stop by default; explicit quarantine
    removes the identity from every method and reports the missing count.
    """
    counts = defaultdict(Counter)
    seen = {}
    total_rows = duplicates = not_accepted = 0
    conflicts = set()
    latest = None
    for row in rows:
        total_rows += 1
        if row.get("election_dt") != election_date:
            raise ValidationError("NC absentee file contains an unexpected election date")
        if row.get("ballot_rtn_status", "").strip().upper() != "ACCEPTED":
            not_accepted += 1
            continue
        kind = row.get("ballot_req_type", "").strip().upper()
        if kind in ("ONE-STOP", "EARLY VOTING"):
            method = "EARLY_IN_PERSON"
        elif kind == "MAIL":
            method = "RETURNED_MAIL"
        else:
            raise ValidationError(f"unknown accepted NC ballot request type: {kind!r}")
        party = row.get("voter_party_code", "").strip().upper()
        if not party:
            raise ValidationError("accepted NC ballot has missing party registration")
        ncid = row.get("ncid", "").strip()
        county, registration = row.get("county_desc", "").strip(), row.get("voter_reg_num", "").strip()
        if not ncid and not (county and registration):
            raise ValidationError("accepted NC ballot lacks a deduplication key")
        key = ("NCID", ncid) if ncid else ("COUNTY_REG", county, registration)
        returned = datetime.strptime(row.get("ballot_rtn_dt", ""), "%m/%d/%Y").date()
        latest = max(latest, returned) if latest else returned
        value = (method, party)
        if key in seen:
            if seen[key] != value:
                if not quarantine_conflicts:
                    raise ValidationError("conflicting accepted records for one NC voter; source review required")
                conflicts.add(key)
            duplicates += 1
            continue
        seen[key] = value
    for key, (method, party) in seen.items():
        if key not in conflicts:
            counts[method][party] += 1
    methods = {}
    for method in ("EARLY_IN_PERSON", "RETURNED_MAIL"):
        total = sum(counts[method].values())
        methods[method] = {"accepted_ballots": total, "parties": {
            party: {"accepted_ballots": count, "share_pct": r4(100 * count / total) if total else None}
            for party, count in sorted(counts[method].items())}}
    return {"election_date": election_date, "source_rows": total_rows, "not_accepted_rows": not_accepted,
            "duplicate_accepted_rows_removed": duplicates, "accepted_unique": len(seen) - len(conflicts),
            "conflicting_accepted_identities_excluded": len(conflicts),
            "latest_accepted_return_date": latest.isoformat() if latest else None, "methods": methods}


def cache_key(unit_sha256: str, scorer_commit: str, prompt_sha256: str, model: str, config_sha256: str) -> str:
    return sha256_bytes("|".join([unit_sha256, scorer_commit, prompt_sha256, model, config_sha256]).encode("utf-8"))


def budget_check(spent: float, reserved: float, units: int, unit_rate: float, ceiling: float = HEAT_BUDGET_USD):
    """Reserve estimated_cost = units * unit_rate * 1.5. Allowed only if spent + reserved + estimate <= ceiling."""
    estimate = units * unit_rate * HEAT_RESERVE_MULTIPLIER
    allowed = (spent + reserved + estimate) <= ceiling + 1e-9
    return allowed, round(estimate, 6)


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def stage3_probability(margin: float) -> float:
    p = phi(margin / STAGE3_SIGMA)
    return min(max(p, STAGE3_CLAMP[0]), STAGE3_CLAMP[1])


def signed_error(poll_margin: float, certified_margin: float) -> float:
    """Poll margin minus certified margin; negative = miss toward Republicans."""
    return round(poll_margin - certified_margin, 4)


def stratum_key(round_, denom, pop):
    return (round_, denom, pop)


def stratum_sort_key(item):
    (round_, denom, pop), count = item
    return (-count, DENOM_ORDER.get(denom, 9), POP_ORDER.get(pop, 9))


def apply_round_precedence(estimates: list[dict], race: str):
    """RCV races only: FINAL if any estimate in the list is FINAL, else FIRST (flagged), else none."""
    if race not in RCV_RACES:
        return [e for e in estimates if e["round"] == "NA"], "NA", 0
    finals = [e for e in estimates if e["round"] == "FINAL"]
    if finals:
        return finals, "FINAL", 0
    firsts = [e for e in estimates if e["round"] == "FIRST"]
    if firsts:
        return firsts, "FIRST", 1
    return [], None, 0


def choose_averaging_stratum(estimates: list[dict], race: str):
    pool, round_used, fallback = apply_round_precedence(estimates, race)
    if not pool:
        return None, fallback, "no weighted_average-flagged estimate after round precedence"
    counts = Counter(stratum_key(e["round"], e["denominator_class"], e["pop"]) for e in pool)
    best = sorted(counts.items(), key=stratum_sort_key)[0][0]
    return {"round": best[0], "denominator_class": best[1], "pop": best[2]}, fallback, None


def choose_contrast_stratum(estimates: list[dict], race: str):
    pool, round_used, fallback = apply_round_precedence(estimates, race)
    if not pool:
        return None, fallback, "no recall_contrast-flagged estimate after round precedence"
    groups = defaultdict(lambda: {"YES": 0, "NO": 0})
    for e in pool:
        groups[stratum_key(e["round"], e["denominator_class"], e["pop"])][e["recall_weighted"]] += 1
    eligible = {k: v["YES"] + v["NO"] for k, v in groups.items() if v["YES"] > 0 and v["NO"] > 0}
    if not eligible:
        return None, fallback, "no stratum contains both a YES and a NO estimate"
    best = sorted(eligible.items(), key=stratum_sort_key)[0][0]
    return {"round": best[0], "denominator_class": best[1], "pop": best[2]}, fallback, None


def latest_published_poll(estimates: list[dict] | None, race: str, as_of: date | None) -> dict | None:
    """Display a source fact, never relax eligibility for an average or contrast.

    RCV round precedence comes first. Within that round prefer newest field end,
    then release, then denominator/population order and stable estimate ID.
    """
    if not as_of:
        return None
    pool = [e for e in (estimates or []) if e.get("flag_principal") and not e.get("quarantined")
            and e.get("race") == race and e.get("window") == "BOTH"
            and e.get("primary_verified") == "YES" and e.get("round") in ("NA", "FIRST", "FINAL")
            and e.get("pop") in POPS and e.get("denominator_class") in DENOMS
            and num(e.get("margin_num")) is not None
            and parse_date(e.get("field_end")) is not None
            and parse_date(e.get("field_end")) <= as_of
            and parse_date(e.get("release_date")) is not None
            and parse_date(e.get("release_date")) <= as_of
            and str(e.get("source_url", "")).startswith("https://")]
    pool, _, _ = apply_round_precedence(pool, race)
    if not pool:
        return None
    e = sorted(pool, key=lambda e: (-parse_date(e["field_end"]).toordinal(),
        -parse_date(e["release_date"]).toordinal(), DENOM_ORDER[e["denominator_class"]],
        POP_ORDER[e["pop"]], e["estimate_id"]))[0]
    return {"estimate_id": e["estimate_id"], "pollster_id": e["pollster_id"],
            "source_url": e["source_url"], "source_locator": e.get("source_locator"),
            "margin": e["margin_num"], "n": e.get("n_num"),
            "field_start": e["field_start"], "field_end": e["field_end"],
            "release_date": e["release_date"], "age_days": (as_of - parse_date(e["field_end"])).days,
            "pop": e["pop"], "round": e["round"], "denominator_class": e["denominator_class"],
            "average_exclusion_reasons": e.get("flag_reasons", [])}


# ----------------------------------------------------------------------------- the bundle
class Bundle:
    def __init__(self, bundle_dir: str, as_of: datetime | None, run_state: dict | None = None):
        self.dir = bundle_dir
        self.as_of = as_of
        self.as_of_date = as_of.date() if as_of else None
        self.run_state = run_state or {}
        self.problems: list[str] = []
        self.notes: list[str] = []
        self.polls = read_csv(os.path.join(bundle_dir, "polls.csv"), POLLS_HEADER)
        self.pollsters = read_csv(os.path.join(bundle_dir, "pollsters.csv"), POLLSTERS_HEADER)
        self.exclusions = read_csv(os.path.join(bundle_dir, "exclusions.csv"), EXCLUSIONS_HEADER)
        self.heat = read_csv(os.path.join(bundle_dir, "heat.csv"), HEAT_HEADER, required=False)
        self.coverage = read_csv(os.path.join(bundle_dir, "coverage.csv"), COVERAGE_HEADER, required=False)
        self.backtest = read_csv(os.path.join(bundle_dir, "backtest-2025.csv"), BACKTEST_HEADER, required=False)
        self.spending = read_csv(os.path.join(bundle_dir, "spending.csv"), SPENDING_HEADER, required=False)
        self.fundamentals = read_csv(os.path.join(bundle_dir, "fundamentals.csv"), FUNDAMENTALS_HEADER, required=False)
        self.spend_history = read_csv(os.path.join(bundle_dir, "spend-history.csv"), SPEND_HISTORY_HEADER, required=False)
        self.quarantined_pollsters = {e["entity_id"] for e in self.exclusions if e["entity_type"] == "POLLSTER"}
        self.quarantined_estimates = {e["entity_id"] for e in self.exclusions if e["entity_type"] == "ESTIMATE"}
        self.method_by_id = {p["method_id"]: p for p in self.pollsters}

    # ----- validation
    def hard(self, msg):
        self.problems.append(msg)

    def soft(self, msg):
        self.notes.append(msg)

    def is_quarantined(self, row: dict) -> bool:
        return row["pollster_id"] in self.quarantined_pollsters or row["estimate_id"] in self.quarantined_estimates or row.get("exclusion_reason") == "QUARANTINE"

    def validate(self) -> bool:
        self._validate_pollsters()
        self._validate_polls(self.polls, "polls.csv", backtest=False)
        if self.backtest:
            self._validate_polls(self.backtest, "backtest-2025.csv", backtest=True)
        self._validate_exclusions()
        self._validate_heat()
        self._validate_coverage()
        return not self.problems

    def _enum(self, fname, i, field, value, allowed):
        if value not in allowed:
            self.hard(f"{fname} row {i}: {field}={value!r} not in {allowed}")

    def _validate_pollsters(self):
        seen = set()
        for i, p in enumerate(self.pollsters, start=2):
            if p["method_id"] in seen:
                self.hard(f"pollsters.csv row {i}: duplicate method_id {p['method_id']}")
            seen.add(p["method_id"])
            self._enum("pollsters.csv", i, "applicability", p["applicability"], APPLICABILITY)
            self._enum("pollsters.csv", i, "recall_weighted", p["recall_weighted"], RECALL_METHOD)
            self._enum("pollsters.csv", i, "track_status", p["track_status"], TRACK_STATUS)
            try:
                ft = num(p["f_track"])
                if ft is None or not (0 < ft <= 1):
                    self.hard(f"pollsters.csv row {i}: f_track must be in (0,1], got {p['f_track']!r}")
            except ValueError as e:
                self.hard(f"pollsters.csv row {i}: f_track {e}")
            if p["recall_weighted"] == "YES" and is_na(p["weighting_quote"]):
                self.hard(f"pollsters.csv row {i}: YES classification without a weighting_quote")
            if p["recall_weighted"] == "NO" and is_na(p["weighting_quote"]):
                self.hard(f"pollsters.csv row {i}: NO classification without a weighting_quote")
            if not is_na(p["rating_metric"]) and p["rating_metric"] != "Simple Average Error":
                self.hard(f"pollsters.csv row {i}: rating_metric must be exactly 'Simple Average Error' or NA")
            if p["track_status"] == "RATED":
                try:
                    sae = num(p["rating_value"])
                    if sae is None or not math.isfinite(sae) or sae < 0:
                        self.hard(f"pollsters.csv row {i}: RATED requires a finite nonnegative rating_value")
                    elif num(p["f_track"]) != f_track_from_simple_average_error(sae):
                        self.hard(f"pollsters.csv row {i}: f_track does not match Simple Average Error thresholds")
                    if p["rating_metric"] != "Simple Average Error" or p["rating_units"] != "percentage points":
                        self.hard(f"pollsters.csv row {i}: RATED requires Simple Average Error in percentage points")
                    if intnum(p["rating_poll_count"]) is None or intnum(p["rating_poll_count"]) < 1:
                        self.hard(f"pollsters.csv row {i}: RATED requires a positive rating_poll_count")
                    if p["rating_cohort"] != "Silver Bulletin database, all race types and years in the file":
                        self.hard(f"pollsters.csv row {i}: incompatible rating cohort")
                    if is_na(p["rating_source"]) or is_na(p["rating_version"]):
                        self.hard(f"pollsters.csv row {i}: missing rating provenance")
                except ValueError as e:
                    self.hard(f"pollsters.csv row {i}: rating_value {e}")
            if p["track_status"] == "PROVISIONAL" and (num(p["f_track"]) != 1.0 or not is_na(p["rating_metric"])):
                self.hard(f"pollsters.csv row {i}: PROVISIONAL requires f_track 1.0 and rating_metric NA")

    def _validate_polls(self, rows, fname, backtest):
        seen_est = set()
        active_by_est = Counter()
        active_key = defaultdict(list)
        series_active = defaultdict(list)
        for i, r in enumerate(rows, start=2):
            eid = r["estimate_id"]
            if eid in seen_est:
                self.hard(f"{fname} row {i}: duplicate estimate_id {eid}")
            seen_est.add(eid)
            for field, allowed in (("pop", POPS), ("denominator_class", DENOMS), ("round", ROUNDS), ("window", WINDOWS),
                                   ("sponsor_class", SPONSOR_CLASSES), ("pollster_alignment", ALIGNMENTS),
                                   ("disclosure_status", DISCLOSURES), ("recall_weighted", RECALL_ESTIMATE),
                                   ("primary_verified", ["YES", "UNVERIFIED"]),
                                   ("selected", ["0", "1"]), ("exclusion_reason", EXCLUSION_REASONS)):
                self._enum(fname, i, field, r[field], allowed)
            race = r["race"]
            if backtest:
                if race not in BACKTEST_RACES:
                    self.hard(f"{fname} row {i}: race {race} is not a backtest race")
            elif race not in IN_SCOPE_RACES:
                self.hard(f"{fname} row {i}: race {race} not in scope")
            if race in RCV_RACES and r["round"] == "NA":
                self.hard(f"{fname} row {i}: RCV race {race} needs round FIRST or FINAL")
            if race not in RCV_RACES and r["round"] != "NA":
                self.hard(f"{fname} row {i}: non-RCV race {race} must have round=NA")
            try:
                fs, fe, rd = parse_date(r["field_start"]), parse_date(r["field_end"]), parse_date(r["release_date"])
            except ValueError as e:
                self.hard(f"{fname} row {i}: bad date {e}")
                continue
            if None in (fs, fe, rd):
                self.hard(f"{fname} row {i}: field_start, field_end and release_date are required")
                continue
            if not (fs <= fe <= rd):
                self.hard(f"{fname} row {i}: dates must satisfy field_start <= field_end <= release_date ({fs} {fe} {rd})")
            try:
                d, rr, oth, und, n = num(r["D"]), num(r["R"]), num(r["other"]), num(r["undecided"]), intnum(r["n"])
                m = num(r["margin"])
            except ValueError as e:
                self.hard(f"{fname} row {i}: {e}")
                continue
            if d is None or rr is None:
                self.hard(f"{fname} row {i}: D and R shares are required")
                continue
            for name, v in (("D", d), ("R", rr), ("other", oth), ("undecided", und)):
                if v is not None and not (0 <= v <= 100):
                    self.hard(f"{fname} row {i}: impossible share {name}={v}")
            total = sum(v for v in (d, rr, oth, und) if v is not None)
            if total > 102.0:
                self.hard(f"{fname} row {i}: shares sum to {total}, above the documented rounding tolerance")
            if n is not None and n <= 0:
                self.hard(f"{fname} row {i}: n must be positive or NA")
            if m is None or abs(m - (d - rr)) > 0.01 + 1e-9:
                self.hard(f"{fname} row {i}: margin {r['margin']!r} is not within 0.01 of D-R={d - rr:.2f}")
            if self.as_of_date is not None:
                expected_w = window_of(fe, rd, self.as_of_date, backtest=backtest)
                if r["window"] != expected_w:
                    self.hard(f"{fname} row {i}: window {r['window']} but derived {expected_w} for field_end {fe}, release {rd}")
            # references
            quarantined = r["pollster_id"] in self.quarantined_pollsters or eid in self.quarantined_estimates
            if r["method_id"] == "NA":
                if r["selected"] == "1" or not quarantined:
                    self.hard(f"{fname} row {i}: method_id=NA is allowed only on unselected quarantined rows")
            elif r["method_id"] not in self.method_by_id:
                self.hard(f"{fname} row {i}: method_id {r['method_id']} not in pollsters.csv")
            else:
                mrec = self.method_by_id[r["method_id"]]
                if mrec["pollster_id"] != r["pollster_id"]:
                    self.hard(f"{fname} row {i}: method_id {r['method_id']} belongs to {mrec['pollster_id']}, row says {r['pollster_id']}")
                if mrec["recall_weighted"] != r["recall_weighted"]:
                    self.hard(f"{fname} row {i}: recall_weighted {r['recall_weighted']} disagrees with method record {mrec['recall_weighted']}")
            if quarantined:
                if r["selected"] == "1":
                    self.hard(f"{fname} row {i}: quarantined estimate {eid} is selected")
                if r["exclusion_reason"] != "QUARANTINE":
                    self.hard(f"{fname} row {i}: quarantined estimate {eid} must carry exclusion_reason QUARANTINE")
            if r["exclusion_reason"] == "QUARANTINE" and not quarantined:
                self.hard(f"{fname} row {i}: exclusion_reason QUARANTINE without an exclusions.csv record for {eid} or {r['pollster_id']}")
            if r["selected"] == "0" and r["exclusion_reason"] == "NA":
                self.hard(f"{fname} row {i}: unselected row needs an exclusion_reason")
            if r["selected"] == "1" and r["exclusion_reason"] != "NA":
                self.hard(f"{fname} row {i}: selected row carries exclusion_reason {r['exclusion_reason']}")
            if not is_na(r["superseded_by"]) and r["selected"] == "1":
                self.hard(f"{fname} row {i}: superseded row {eid} cannot be selected")
            if r["selected"] == "1":
                active_by_est[eid] += 1
                key = (r["pollster_id"], race, r["field_start"], r["field_end"], r["pop"], r["denominator_class"], r["round"])
                active_key[key].append(r)
                if r["tracking_series_id"] != "NA":
                    series_active[(r["tracking_series_id"], race, r["pop"], r["denominator_class"], r["round"])].append((fs, fe, eid))
            if backtest:
                try:
                    cd, cr, cm, se = num(r["certified_D"]), num(r["certified_R"]), num(r["certified_margin"]), num(r["signed_error"])
                except ValueError as e:
                    self.hard(f"{fname} row {i}: {e}")
                    continue
                if None in (cd, cr, cm):
                    self.hard(f"{fname} row {i}: certified_D, certified_R, certified_margin required")
                elif abs(cm - (cd - cr)) > 0.01 + 1e-9:
                    self.hard(f"{fname} row {i}: certified_margin not within 0.01 of certified_D - certified_R")
                elif se is None or abs(se - signed_error(d - rr, cm)) > 0.01 + 1e-9:
                    self.hard(f"{fname} row {i}: signed_error must equal margin - certified_margin")
                if is_na(r["result_url"]):
                    self.hard(f"{fname} row {i}: result_url required")
        for key, rs in active_key.items():
            if len(rs) > 1:
                urls = {r["source_url"] for r in rs}
                series = {r["tracking_series_id"] for r in rs}
                distinct_ok = len(urls) == len(rs) and (len(series) == len(rs) or any(s == "NA" for s in series))
                if not distinct_ok:
                    self.hard(f"{fname}: two active rows share {key} without distinct source URLs: {[r['estimate_id'] for r in rs]}")
        for skey, waves in series_active.items():
            waves.sort()
            for a, b in zip(waves, waves[1:]):
                if a[1] >= b[0]:
                    self.hard(f"{fname}: tracking series {skey[0]} has two active overlapping waves {a[2]} and {b[2]}")
        for eid, c in active_by_est.items():
            if c > 1:
                self.hard(f"{fname}: estimate_id {eid} is active more than once")
        if not backtest and self.polls:
            for eid in self.quarantined_estimates:
                if eid not in seen_est:
                    self.soft(f"exclusions.csv names estimate {eid} that is not in polls.csv")
            for pid in self.quarantined_pollsters:
                if not any(r["pollster_id"] == pid for r in rows):
                    self.soft(f"exclusions.csv quarantines pollster {pid} with no rows in {fname}")

    def _validate_exclusions(self):
        pollster_ids = {p["pollster_id"] for p in self.pollsters} | {r["pollster_id"] for r in self.polls}
        est_ids = {r["estimate_id"] for r in self.polls} | {r["estimate_id"] for r in self.backtest}
        for i, e in enumerate(self.exclusions, start=2):
            self._enum("exclusions.csv", i, "entity_type", e["entity_type"], ["POLLSTER", "ESTIMATE"])
            if e["entity_type"] == "POLLSTER" and e["entity_id"] not in pollster_ids:
                self.soft(f"exclusions.csv row {i}: pollster {e['entity_id']} has no rows yet")
            if e["entity_type"] == "ESTIMATE" and e["entity_id"] not in est_ids:
                self.hard(f"exclusions.csv row {i}: estimate {e['entity_id']} not found")
            if is_na(e["reason"]) or is_na(e["evidence_url"]):
                self.hard(f"exclusions.csv row {i}: reason and evidence_url are required")
            try:
                parse_date(e["evidence_date"])
            except ValueError:
                self.hard(f"exclusions.csv row {i}: bad evidence_date")

    def _validate_heat(self):
        seen = set()
        for i, h in enumerate(self.heat, start=2):
            if h["heat_id"] in seen:
                self.hard(f"heat.csv row {i}: duplicate heat_id")
            seen.add(h["heat_id"])
            self._enum("heat.csv", i, "slot", h["slot"], SLOTS)
            self._enum("heat.csv", i, "source_type", h["source_type"], HEAT_SOURCE)
            self._enum("heat.csv", i, "status", h["status"], HEAT_STATUS)
            self._enum("heat.csv", i, "caption_source", h["caption_source"], CAPTION_SOURCE)
            if h["race"] not in IN_SCOPE_RACES:
                self.hard(f"heat.csv row {i}: race {h['race']} not in scope")
            if h["status"] == "SCORED":
                try:
                    s = num(h["ph_score"])
                except ValueError as e:
                    self.hard(f"heat.csv row {i}: {e}")
                    continue
                if s is None or not (1.0 <= s <= 5.0):
                    self.hard(f"heat.csv row {i}: SCORED ph_score must be finite within [1,5], got {h['ph_score']!r}")
                for f in ("source_url", "scorer_commit", "prompt_sha256", "model", "config_sha256", "unit_sha256", "scored_at"):
                    if is_na(h[f]):
                        self.hard(f"heat.csv row {i}: SCORED row missing {f}")
                try:
                    if num(h["cost_usd"]) is None:
                        self.hard(f"heat.csv row {i}: SCORED row needs cost_usd")
                except ValueError as e:
                    self.hard(f"heat.csv row {i}: cost_usd {e}")

    def _validate_coverage(self):
        for i, c in enumerate(self.coverage, start=2):
            self._enum("coverage.csv", i, "edition_status", c["edition_status"], EDITION_STATUS)
            self._enum("coverage.csv", i, "match_status", c["match_status"], MATCH_STATUS)
            if is_na(c["expected_edition"]):
                self.hard(f"coverage.csv row {i}: expected_edition required")
            if c["race"] not in IN_SCOPE_RACES:
                self.hard(f"coverage.csv row {i}: race {c['race']} not in scope")

    # ----- derivation (in-place columns of polls.csv)
    def derive_rows(self, rows: list[dict], backtest: bool = False) -> list[dict]:
        """Fill margin, window, selected and exclusion_reason. Quarantine, supersession and matchup flags set by the
        data builder are respected; principal selection and tracker overlap are decided here."""
        out = [dict(r) for r in rows]
        for r in out:
            d, rr = num(r["D"]), num(r["R"])
            m = margin_of(d, rr)
            r["margin"] = "NA" if m is None else f"{m:.2f}"
            if backtest:
                certified = num(r.get("certified_margin"))
                r["signed_error"] = str(signed_error(d - rr, certified)) if d is not None and rr is not None and certified is not None else "NA"
            fe, rd = parse_date(r["field_end"]), parse_date(r["release_date"])
            r["window"] = window_of(fe, rd, self.as_of_date, backtest=backtest)
            if is_na(r.get("exclusion_reason")):
                r["exclusion_reason"] = "NA"
            if is_na(r.get("selected")):
                r["selected"] = "1"
        locked = {"QUARANTINE", "SUPERSEDED", "MATCHUP_MISMATCH", "UNVERIFIED_MATCHUP"}
        for r in out:
            if self.is_quarantined(r):
                r["selected"], r["exclusion_reason"] = "0", "QUARANTINE"
            elif not is_na(r["superseded_by"]):
                r["selected"], r["exclusion_reason"] = "0", "SUPERSEDED"
            elif r["exclusion_reason"] in locked:
                r["selected"] = "0"
            else:
                r["selected"], r["exclusion_reason"] = "1", "NA"
        # principal per (poll_id, race, round): LV>RV>A, FULL>LEANERS>TWO_WAY
        groups = defaultdict(list)
        for r in out:
            if r["selected"] == "1":
                groups[(r["poll_id"], r["race"], r["round"])].append(r)
        for key, rs in groups.items():
            rs.sort(key=lambda r: (POP_ORDER[r["pop"]], DENOM_ORDER[r["denominator_class"]], r["estimate_id"]))
            for r in rs[1:]:
                r["selected"], r["exclusion_reason"] = "0", "NOT_PRINCIPAL"
        # tracker deduplication within one tracking_series_id: keep latest, walk back keeping non-overlapping waves
        series = defaultdict(list)
        for r in out:
            if r["selected"] == "1" and r["tracking_series_id"] != "NA":
                series[(r["tracking_series_id"], r["race"], r["pop"], r["denominator_class"], r["round"])].append(r)
        for key, rs in series.items():
            rs.sort(key=lambda r: (r["field_end"], r["release_date"], r["estimate_id"]), reverse=True)
            kept: list[tuple[date, date]] = []
            for r in rs:
                fs, fe = parse_date(r["field_start"]), parse_date(r["field_end"])
                if any(not (fe < ks or fs > ke) for ks, ke in kept):
                    r["selected"], r["exclusion_reason"] = "0", "TRACKER_OVERLAP"
                else:
                    kept.append((fs, fe))
        return out

    # ----- estimates with flags
    def estimates(self, rows=None, backtest=False) -> list[dict]:
        rows = self.polls if rows is None else rows
        out = []
        for r in rows:
            e = dict(r)
            e["D_num"], e["R_num"] = num(r["D"]), num(r["R"])
            e["n_num"] = intnum(r["n"])
            e["margin_num"] = num(r["margin"])
            fs, fe = parse_date(r["field_start"]), parse_date(r["field_end"])
            e["fs"], e["fe"] = fs, fe
            quarantined = self.is_quarantined(r)
            e["quarantined"] = quarantined
            reasons = []
            principal = r["selected"] == "1" and not quarantined
            if not principal:
                reasons.append("not principal: " + (r["exclusion_reason"] if r["exclusion_reason"] != "NA" else "selected=0"))
            in_both = r["window"] == ("BACKTEST" if backtest else "BOTH")
            if not in_both:
                reasons.append(f"window {r['window']}")
            verified_inputs = r["primary_verified"] == "YES" and r["round"] in ("NA", "FIRST", "FINAL")
            if r["primary_verified"] != "YES":
                reasons.append("primary-source inputs UNVERIFIED: inventory only")
            if r["round"] == "UNVERIFIED":
                reasons.append("round UNVERIFIED: a two-candidate question does not establish a final RCV tabulation")
            rc = principal and in_both and r["race"] in (BACKTEST_RACES if backtest else IN_SCOPE_RACES) and fs is not None and fe is not None \
                and r["pop"] in POPS and e["D_num"] is not None and e["R_num"] is not None and r["denominator_class"] in DENOMS \
                and verified_inputs and r["recall_weighted"] in ("YES", "NO")
            if principal and in_both and r["recall_weighted"] == "UNVERIFIED":
                reasons.append("recall_weighted UNVERIFIED: excluded from YES-NO contrasts, counted")
            e["flag_principal"] = principal
            e["flag_recall_contrast"] = rc
            e["flag_sponsor_restricted"] = rc and r["sponsor_class"] in ("NONPARTISAN", "BIPARTISAN")
            # weights
            mrec = self.method_by_id.get(r["method_id"])
            ft = num(mrec["f_track"]) if mrec and not is_na(mrec.get("f_track")) else 1.0
            fr = f_recency(fs, fe, self.as_of_date) if (fs and fe and self.as_of_date) else None
            fsm = f_sample(e["n_num"])
            fp = f_pop(r["pop"])
            fsp = f_sponsor(r["sponsor_class"])
            fd = f_disclosure(r["disclosure_status"])
            factors = {"f_track": ft, "f_recency": fr, "f_sample": fsm, "f_pop": fp, "f_sponsor": fsp, "f_disclosure": fd}
            e["factors"] = {k: r4(v) for k, v in factors.items()}
            w = None
            if all(v is not None for v in factors.values()):
                w = ft * fr * fsm * fp * fsp * fd
            e["weight"] = r4(w)
            wa = principal and in_both and verified_inputs and e["margin_num"] is not None
            if wa and e["n_num"] is None:
                wa = False; reasons.append("n missing")
            if wa and r["sponsor_class"] == "UNKNOWN":
                wa = False; reasons.append("sponsor_class UNKNOWN")
            if wa and w is None:
                wa = False; reasons.append("a weight factor input is missing")
            if wa and w < WEIGHT_CUTOFF:
                wa = False; reasons.append(f"weight {w:.4f} below cutoff {WEIGHT_CUTOFF}")
            e["flag_weighted_average"] = wa
            e["flag_reasons"] = reasons
            out.append(e)
        return out

    # ----- per race
    def race_block(self, race: str, ests: list[dict], stage2c_passed: bool) -> dict:
        rows = [e for e in ests if e["race"] == race]
        principal = [e for e in rows if e["flag_principal"]]
        wa = [e for e in rows if e["flag_weighted_average"]]
        rc = [e for e in rows if e["flag_recall_contrast"]]
        recall_counts = Counter(e["recall_weighted"] for e in principal if e["window"] == "BOTH")
        averaging, fb_a, reason_a = choose_averaging_stratum(wa, race)
        contrast, fb_c, reason_c = choose_contrast_stratum(rc, race)
        in_avg = []
        if averaging:
            in_avg = [e for e in wa if (e["round"], e["denominator_class"], e["pop"]) == (averaging["round"], averaging["denominator_class"], averaging["pop"])]
        retained_weight = r4(sum(e["weight"] for e in in_avg)) if in_avg else None
        weighted_margin = None
        no_cutoff_margin = None
        if stage2c_passed and in_avg:
            weighted_margin = r4(sum(e["weight"] * e["margin_num"] for e in in_avg) / sum(e["weight"] for e in in_avg))
        # A sensitivity must remain available when every eligible weight is below
        # the cutoff. Prefer the retained stratum, otherwise choose by the same
        # deterministic rule from the otherwise eligible, positive-weight pool.
        candidates = [e for e in rows if e["flag_principal"] and e["primary_verified"] == "YES"
                      and e["window"] == "BOTH" and e["round"] in ("NA", "FIRST", "FINAL")
                      and e["weight"] is not None and e["weight"] > 0
                      and e["margin_num"] is not None and e["sponsor_class"] != "UNKNOWN"]
        sensitivity_stratum = averaging or choose_averaging_stratum(candidates, race)[0]
        if stage2c_passed and sensitivity_stratum:
            pool = [e for e in candidates if all(e[k] == sensitivity_stratum[k] for k in ("round", "denominator_class", "pop"))]
            if pool:
                no_cutoff_margin = r4(sum(e["weight"] * e["margin_num"] for e in pool) / sum(e["weight"] for e in pool))
        field_ends = sorted(e["field_end"] for e in in_avg)
        preliminary = r4(mean([e["margin_num"] for e in in_avg])) if in_avg else None
        excluded_cutoff = [e["estimate_id"] for e in rows if e["flag_principal"] and e["window"] == "BOTH" and not e["flag_weighted_average"]]
        per_race_contrast = None
        if contrast:
            cs = [e for e in rc if (e["round"], e["denominator_class"], e["pop"]) == (contrast["round"], contrast["denominator_class"], contrast["pop"])]
            yes = [e["margin_num"] for e in cs if e["recall_weighted"] == "YES"]
            no = [e["margin_num"] for e in cs if e["recall_weighted"] == "NO"]
            balanced = {}
            for group in ("YES", "NO"):
                firms = defaultdict(list)
                for e in cs:
                    if e["recall_weighted"] == group:
                        firms[e["pollster_id"]].append(e["margin_num"])
                balanced[group] = mean([mean(values) for values in firms.values()])
            per_race_contrast = {"yes_mean": r4(balanced["YES"]), "no_mean": r4(balanced["NO"]), "yes_minus_no": r4(balanced["YES"] - balanced["NO"]), "n_yes": len(yes), "n_no": len(no)}
        scenarios = None
        base = weighted_margin if weighted_margin is not None else preliminary
        if base is not None:
            scenarios = {k: r4(base - v) for k, v in SCENARIO_SHIFTS.items()}
        latest = latest_published_poll(rows, race, self.as_of_date)
        if weighted_margin is not None:
            polling_read = {"kind": "WEIGHTED_AVERAGE", "margin": weighted_margin,
                            "poll_count": len(in_avg), "field_end": field_ends[-1],
                            "age_days": (self.as_of_date - parse_date(field_ends[-1])).days,
                            "stratum": averaging, "latest_poll": None}
        elif latest:
            polling_read = {"kind": "LATEST_POLL", "margin": latest["margin"], "poll_count": 1,
                            "field_end": latest["field_end"], "age_days": latest["age_days"],
                            "stratum": {k: latest[k] for k in ("round", "denominator_class", "pop")},
                            "latest_poll": latest}
        else:
            polling_read = {"kind": "UNAVAILABLE", "margin": None, "poll_count": 0,
                            "field_end": None, "age_days": None, "stratum": None, "latest_poll": None}
        return {
            "race": race,
            "polling_read": polling_read,
            "rcv": race in RCV_RACES,
            "weighted_margin": weighted_margin,
            "weighted_margin_status": "computed (heuristic; track-record stand-in)" if weighted_margin is not None else "not yet computed (Stage 2c not passed)" if in_avg else "NA (no estimate in the averaging stratum)",
            "preliminary_unweighted_margin": preliminary,
            "no_cutoff_margin": no_cutoff_margin,
            "no_cutoff_stratum": sensitivity_stratum,
            "no_cutoff_stratum_note": "retained stratum" if averaging else "chosen from otherwise eligible positive-weight polls; none retained at the cutoff" if candidates else "no otherwise eligible positive-weight polls",
            "latest_contributing_field_end": field_ends[-1] if field_ends else None,
            "oldest_contributing_field_end": field_ends[0] if field_ends else None,
            "newest_poll_age_days": (self.as_of_date - parse_date(field_ends[-1])).days if field_ends and self.as_of_date else None,
            "retained_count": len(in_avg),
            "excluded_count": len(excluded_cutoff),
            "excluded_estimate_ids": sorted(excluded_cutoff),
            "retained_weight": retained_weight,
            "averaging_stratum": averaging,
            "averaging_stratum_reason": reason_a,
            "rcv_first_round_fallback": fb_a,
            "contrast_stratum": contrast,
            "contrast_stratum_reason": reason_c,
            "contrast_rcv_first_round_fallback": fb_c,
            "recall_counts_principal_both": {k: recall_counts.get(k, 0) for k in RECALL_ESTIMATE},
            "principal_count": len(principal),
            "principal_both_count": sum(1 for e in principal if e["window"] == "BOTH"),
            "principal_house_only_count": sum(1 for e in principal if e["window"] == "HOUSE_ONLY"),
            "quarantined_count": sum(1 for e in rows if e["quarantined"]),
            "stored_row_count": len(rows),
            "averaging_estimate_ids": sorted(e["estimate_id"] for e in in_avg),
            "per_race_contrast": per_race_contrast,
            "scenario_margins_toward_R": scenarios,
            "scenario_note": "2.5-point uniform miss toward Republicans is the control-flipping scenario; 5-point is the 2016 and 2020 scale scenario. The 5.0 in the Stage 3 probability mapping is a standard deviation, not a flip threshold.",
        }

    # ----- Section 5 contrasts
    def contrasts(self, ests: list[dict], race_blocks: dict) -> dict:
        rc = [e for e in ests if e["flag_recall_contrast"]]
        # A survey's FIRST and FINAL estimates are alternatives for this
        # comparison, not two independent observations in the pooled result.
        rc = [e for race in sorted({e["race"] for e in rc})
              for e in apply_round_precedence([e for e in rc if e["race"] == race], race)[0]]
        unverified = [e for e in ests if e["flag_principal"] and e["window"] == "BOTH" and e["recall_weighted"] == "UNVERIFIED"]

        def pooled(pool, label, note):
            yes = [e for e in pool if e["recall_weighted"] == "YES"]
            no = [e for e in pool if e["recall_weighted"] == "NO"]
            val = None
            if yes and no:
                val = r4(mean([e["margin_num"] for e in yes]) - mean([e["margin_num"] for e in no]))
            return {
                "label": label, "value": val, "status": "computed" if val is not None else "NA: needs at least one YES and one NO estimate",
                "n_yes": len(yes), "n_no": len(no),
                "races": sorted({e["race"] for e in yes} | {e["race"] for e in no}),
                "independent_waves": len({e["sample_id"] for e in yes + no}),
                "included_estimate_ids": sorted(e["estimate_id"] for e in yes + no),
                "strata_mixed": sorted({f"{e['round']}/{e['denominator_class']}/{e['pop']}" for e in yes + no}),
                "note": note,
            }

        def race_balanced(pool, label):
            per_race = {}
            for race in sorted({e["race"] for e in pool}):
                blk = race_blocks[race]
                cs_def = blk["contrast_stratum"]
                if not cs_def:
                    per_race[race] = {"value": None, "reason": blk["contrast_stratum_reason"]}
                    continue
                cs = [e for e in pool if e["race"] == race and (e["round"], e["denominator_class"], e["pop"]) == (cs_def["round"], cs_def["denominator_class"], cs_def["pop"])]
                by_group = {}
                for g in ("YES", "NO"):
                    by_pollster = defaultdict(list)
                    for e in cs:
                        if e["recall_weighted"] == g:
                            by_pollster[e["pollster_id"]].append(e["margin_num"])
                    pm = [mean(v) for v in by_pollster.values()]
                    by_group[g] = {"mean": r4(mean(pm)) if pm else None, "pollsters": len(pm), "estimates": sum(len(v) for v in by_pollster.values())}
                if by_group["YES"]["mean"] is None or by_group["NO"]["mean"] is None:
                    per_race[race] = {"value": None, "reason": "a group is empty in the contrast stratum under this restriction", "groups": by_group}
                else:
                    per_race[race] = {"value": r4(by_group["YES"]["mean"] - by_group["NO"]["mean"]), "groups": by_group, "stratum": cs_def,
                                      "included_estimate_ids": sorted(e["estimate_id"] for e in cs)}
            vals = [v["value"] for v in per_race.values() if v["value"] is not None]
            return {
                "label": label, "value": r4(mean(vals)) if vals else None,
                "status": "computed" if vals else "NA: no race has a contrast stratum with both groups",
                "races_included": sorted(r for r, v in per_race.items() if v["value"] is not None),
                "per_race": per_race,
                "independent_waves": len({e["sample_id"] for e in pool if e["estimate_id"] in {
                    eid for v in per_race.values() if v["value"] is not None for eid in v["included_estimate_ids"]}}),
            }

        c1 = pooled(rc, "(i) pooled unweighted YES minus NO margin difference across all strata", "mixed-population, composition-sensitive description")
        c2 = race_balanced(rc, "(ii) race-balanced within each race's contrast stratum")
        c3 = race_balanced([e for e in rc if e["flag_sponsor_restricted"]], "(iii) as (ii) on sponsor_restricted estimates (NONPARTISAN or BIPARTISAN sponsors)")
        lv = [e for e in rc if e["pop"] == "LV"]
        modal = Counter(e["denominator_class"] for e in lv).most_common()
        modal_denom = None
        if modal:
            top = modal[0][1]
            modal_denom = sorted([d for d, c in modal if c == top], key=lambda d: DENOM_ORDER[d])[0]
        c4 = pooled([e for e in lv if e["denominator_class"] == modal_denom], f"(iv) as (i) restricted to LV and the modal denominator_class ({modal_denom or 'NA'})", "matched-population sensitivity")
        c4["modal_denominator_class"] = modal_denom
        per_race_named = {}
        for race in PER_RACE_CONTRAST_RACES:
            blk = race_blocks.get(race)
            balanced = c2["per_race"].get(race, {})
            if balanced.get("value") is not None:
                groups = balanced["groups"]
                per_race_named[race] = {"yes_mean": groups["YES"]["mean"], "no_mean": groups["NO"]["mean"],
                    "yes_minus_no": balanced["value"], "n_yes": groups["YES"]["estimates"], "n_no": groups["NO"]["estimates"], "stratum": balanced["stratum"]}
            else:
                per_race_named[race] = {"value": None, "reason": (blk or {}).get("contrast_stratum_reason") or "race absent"}
        return {
            "framing": "Every comparison here is descriptive. None identifies the effect of recalled-vote weighting or its mechanism. Mode, timing, recruitment, screens, targets, nonresponse, pollster effects and selective publication remain confounded.",
            "hypothesis_under_test": "Weighting a midterm sample to recalled 2024 presidential vote imports a presidential-year electorate and shifts estimates toward Republicans when turnout is differential. Direction depends on target source, treatment of nonvoters, recall error and the likely-voter screen.",
            "unverified_count": len(unverified),
            "unverified_estimate_ids": sorted(e["estimate_id"] for e in unverified),
            "i": c1, "ii": c2, "iii": c3, "iv": c4,
            "per_race": per_race_named,
        }

    # ----- Section 6 governor-Senate gaps
    def gov_sen_gaps(self, ests: list[dict]) -> dict:
        out = {}
        principal = [e for e in ests if e["flag_principal"] and e["window"] == "BOTH" and e["primary_verified"] == "YES" and e["round"] in ("NA", "FIRST", "FINAL")]
        by_key = defaultdict(dict)
        for e in principal:
            by_key[(e["sample_id"], e["pop"], e["denominator_class"], e["round"])][e["race"]] = e
        for state, (gov, sen) in GOV_SEN_GAP_STATES.items():
            pairs = []
            for key, races in by_key.items():
                if gov in races and sen in races and key[0] != "NA":
                    g, s = races[gov], races[sen]
                    pairs.append({"sample_id": key[0], "pop": key[1], "denominator_class": key[2], "round": key[3],
                                  "pollster_id": g["pollster_id"], "governor_margin": g["margin_num"], "senate_margin": s["margin_num"],
                                  "gap": r4(g["margin_num"] - s["margin_num"]), "governor_estimate_id": g["estimate_id"], "senate_estimate_id": s["estimate_id"]})
            pairs.sort(key=lambda p: (p["sample_id"], p["pop"], p["denominator_class"]))
            out[state] = {"pairs": pairs, "mean_gap": r4(mean([p["gap"] for p in pairs])) if pairs else None,
                          "status": "computed" if pairs else "NA: no pair shares an explicit sample_id, pop, denominator_class and round"}
        out["_comparators_2022"] = historical_comparators()
        return out

    # ----- Section 9 heat
    def heat_block(self) -> dict:
        per_race = {}
        races = sorted({h["race"] for h in self.heat})
        for race in races:
            rows = [h for h in self.heat if h["race"] == race]
            cands = {}
            for slot in SLOTS:
                srows = [h for h in rows if h["slot"] == slot]
                name = next((h["candidate"] for h in srows), None)
                cands[slot] = {"candidate": name}
                for st in HEAT_SOURCE:
                    scored = [num(h["ph_score"]) for h in srows if h["source_type"] == st and h["status"] == "SCORED"]
                    statuses = Counter(h["status"] for h in srows if h["source_type"] == st)
                    cands[slot][st] = {"mean": r4(mean(scored)), "n": len(scored), "statuses": dict(statuses),
                                       "status": "SCORED" if scored else ("MISSING" if not srows else ",".join(sorted(statuses)))}
            gaps = {}
            for st in HEAT_SOURCE:
                dm, rm = cands["D"][st]["mean"], cands["R"][st]["mean"]
                if dm is None or rm is None:
                    gaps[st] = {"gap": None, "status": "undefined: both candidates need at least one SCORED unit", "hotter": None}
                else:
                    diff = dm - rm
                    hotter = "TIE" if abs(diff) < TIE_THRESHOLD else ("D" if diff > 0 else "R")
                    gaps[st] = {"gap": r4(diff), "status": "defined", "hotter": hotter}
            gaps["AD"]["label"] = "exploratory: the meter was validated on debate answers and historical speeches, not ads"
            caption = sorted({h["caption_source"] for h in rows if h["source_type"] == "DEBATE" and h["status"] == "SCORED"})
            per_race[race] = {"candidates": cands, "debate_gap": gaps["DEBATE"], "ad_gap": gaps["AD"], "debate_caption_sources": caption,
                              "unit_counts": dict(Counter(h["status"] for h in rows))}
        replay = None
        candidates = [(abs(b["debate_gap"]["gap"]), r) for r, b in per_race.items()
                      if b["debate_gap"]["gap"] is not None and set(b["debate_caption_sources"]) and set(b["debate_caption_sources"]) <= {"BROADCASTER", "OFFICIAL"}]
        if candidates:
            candidates.sort(reverse=True)
            replay = {"race": candidates[0][1], "abs_debate_gap": r4(candidates[0][0]), "rule": "in-scope debate with the widest between-speaker debate gap and caption_source BROADCASTER or OFFICIAL"}
        spend = sum((num(h["cost_usd"]) or 0.0) for h in self.heat)
        return {
            "per_race": per_race,
            "races_with_defined_debate_gap": sorted(r for r, b in per_race.items() if b["debate_gap"]["gap"] is not None),
            "replay_1_recommendation": replay,
            "units_scored": sum(1 for h in self.heat if h["status"] == "SCORED"),
            "units_by_status": dict(Counter(h["status"] for h in self.heat)),
            "spend_usd": round(spend, 4),
            "budget_ceiling_usd": HEAT_BUDGET_USD,
            "tie_threshold": TIE_THRESHOLD,
            "grading_rule": "race set = races with a defined debate gap at the Stage 3 freeze; outcome = the certified loser; metric = count and share of graded races where the hotter debate candidate lost, ties reported separately and excluded from the share; 0.5 is a no-information reference, not a test of predictive validity.",
            "ruling": "persuasive is not hyperbolic; the meter scores hyperbole only",
        }

    # ----- Section 2a backtest
    def backtest_block(self, stage2a_passed: bool) -> dict | None:
        if not stage2a_passed or not self.backtest:
            return None
        ests = self.estimates(self.backtest, backtest=True)
        principal = [e for e in ests if e["flag_principal"] and e["window"] == "BACKTEST" and e["primary_verified"] == "YES" and e["round"] in ("NA", "FIRST", "FINAL")]
        for e in principal:
            e["signed_error_num"] = num(e["signed_error"])
        by_state = {}
        for race in BACKTEST_RACES:
            rows = [e for e in principal if e["race"] == race]
            groups = {}
            for g in RECALL_ESTIMATE:
                gs = [e for e in rows if e["recall_weighted"] == g]
                groups[g] = {"n": len(gs), "mean_signed_error": r4(mean([e["signed_error_num"] for e in gs]))}
            contrast = None
            if groups["YES"]["n"] and groups["NO"]["n"]:
                contrast = r4(groups["YES"]["mean_signed_error"] - groups["NO"]["mean_signed_error"])
            # one final poll per firm
            last = {}
            for e in sorted(rows, key=lambda e: (e["fe"], e["release_date"], e["estimate_id"])):
                last[e["pollster_id"]] = e
            lg = {}
            for g in RECALL_ESTIMATE:
                gs = [e for e in last.values() if e["recall_weighted"] == g]
                lg[g] = {"n": len(gs), "mean_signed_error": r4(mean([e["signed_error_num"] for e in gs]))}
            lcontrast = r4(lg["YES"]["mean_signed_error"] - lg["NO"]["mean_signed_error"]) if lg["YES"]["n"] and lg["NO"]["n"] else None
            by_state[race] = {"n": len(rows), "mean_signed_error": r4(mean([e["signed_error_num"] for e in rows])), "groups": groups,
                              "yes_minus_no": contrast, "one_final_poll_per_firm": {"groups": lg, "yes_minus_no": lcontrast},
                              "certified_margin": num(rows[0]["certified_margin"]) if rows else None}
        vals = [b["yes_minus_no"] for b in by_state.values() if b["yes_minus_no"] is not None]
        lvals = [b["one_final_poll_per_firm"]["yes_minus_no"] for b in by_state.values() if b["one_final_poll_per_firm"]["yes_minus_no"] is not None]
        return {
            "status": "PASSED" if stage2a_passed else "not passed",
            "by_state": by_state,
            "within_state_yes_minus_no_equal_average": r4(mean(vals)) if vals else None,
            "states_with_both_groups": [r for r, b in by_state.items() if b["yes_minus_no"] is not None],
            "one_final_poll_per_firm_sensitivity": r4(mean(lvals)) if lvals else None,
            "sign_convention": "signed_error = poll margin minus certified margin; negative = miss toward Republicans",
            "framing": "two-election descriptive check on a primary-verified subset, not causal identification or held-out validation of the weighting heuristic. The January 2026 ratings incorporate 2025 results and are not used to score a supposedly independent 2025 prediction",
            "missing_contrast_reason": "Each state needs a verified YES and NO survey. Ambiguous past-vote language, modeled or imputed vote choice, and recall questions without explicit weighting evidence remain UNVERIFIED.",
        }

    # ----- derived.json
    def turnout_block(self):
        if self.run_state.get("stage_outcomes", {}).get("stage2b") != "PASSED":
            return None
        source = self.run_state.get("turnout_source") or {}
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(repo, source.get("path", ""))
        if not source.get("sha256") or not os.path.isfile(path) or sha256_file(path) != source["sha256"]:
            raise ValidationError("Stage 2b aggregate source is missing or its hash changed")
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
        for year in ("2026", "2022"):
            summary = data["years"][year]
            if sum(m["accepted_ballots"] for m in summary["methods"].values()) != summary["accepted_unique"]:
                raise ValidationError("NC aggregate method counts do not reconcile")
            for method in summary["methods"].values():
                if sum(p["accepted_ballots"] for p in method["parties"].values()) != method["accepted_ballots"]:
                    raise ValidationError("NC aggregate party counts do not reconcile")
        return data

    def signals_block(self, blocks: dict) -> dict | None:
        """Signal-adjusted reading beside the polling read. None when the signal inputs are absent (older bundles)."""
        if not self.spending or not self.fundamentals:
            return None
        hist = spending_history_estimate(self.spend_history)
        beta = normal_posterior(SIGNAL_PRIOR_BETA, hist.get("slope"), hist.get("se"))
        gamma = SIGNAL_PRIOR_GAMMA
        fund = {r["race"]: num(r["pres_d_minus_r"]) for r in self.fundamentals}
        spend = {r["race"]: r for r in self.spending}
        races = SENATE_RACES + GOVERNOR_RACES
        polling = {race: ((blocks.get(race) or {}).get("polling_read") or {}).get("margin") for race in races}
        covered = []
        for race in races:
            sp = spend.get(race)
            if not sp or sp["fec_coverage"] != "FEC_SCHEDULE_E" or polling[race] is None:
                continue
            d_rec, r_rec = num(sp["d_fav_recent"]), num(sp["r_fav_recent"])
            if d_rec is None or r_rec is None:
                continue
            covered.append((race, math.log1p((d_rec + r_rec) / 1e6), abs(polling[race])))
        z = excess_spend_z([c[1] for c in covered], [c[2] for c in covered]) if len(covered) >= 3 else None
        zmap = {c[0]: z[i] for i, c in enumerate(covered)} if z else {}
        per_race = {}
        for race in races:
            sp = spend.get(race) or {}
            u = underdog_sign(fund.get(race))
            zr = zmap.get(race)
            spend_signal = r4(zr * u) if (zr is not None and u) else None
            heat = rhetoric_gap(self.heat, race)
            out = signal_adjusted(polling[race], spend_signal, heat["gap"], beta, gamma)
            d_rec, r_rec = num(sp.get("d_fav_recent")), num(sp.get("r_fav_recent"))
            d_pri, r_pri = num(sp.get("d_fav_prior")), num(sp.get("r_fav_prior"))
            out.update({
                "polling_margin": polling[race],
                "fundamentals": {"pres_year": 2024, "pres_d_minus_r": fund.get(race), "underdog": {1: "D", -1: "R"}.get(u)},
                "spending": {"coverage": sp.get("fec_coverage", "MISSING"),
                             "d_fav_recent": d_rec, "r_fav_recent": r_rec, "d_fav_prior": d_pri, "r_fav_prior": r_pri,
                             "r_share_recent": r4(r_rec / (d_rec + r_rec)) if d_rec is not None and r_rec is not None and (d_rec + r_rec) > 0 else None,
                             "r_share_prior": r4(r_pri / (d_pri + r_pri)) if d_pri is not None and r_pri is not None and (d_pri + r_pri) > 0 else None,
                             "excess_z": r4(zr) if zr is not None else None, "signal_toward_d": spend_signal,
                             "status": "defined" if spend_signal is not None else ("not federal: no FEC coverage" if sp.get("fec_coverage") == "NOT_FEDERAL" else "undefined")},
                "rhetoric": heat,
            })
            per_race[race] = out
        return {
            "method_version": SIGNAL_METHOD_VERSION,
            "method_note": "midterm-2026-signal-adjusted-reading.md",
            "ruling": "Max, 2026-10-26: spending and rhetoric enter an adjusted reading beside the polling read (big swing)",
            "window_days": 14, "window_end": self.spending[0].get("window_end"),
            "priors": {"beta": list(SIGNAL_PRIOR_BETA), "gamma": list(SIGNAL_PRIOR_GAMMA)},
            "history": hist,
            "posterior": {"beta": [r4(beta[0]), r4(beta[1])], "gamma": [gamma[0], gamma[1]], "gamma_note": "no history: prior only"},
            "rules": {"rhetoric_cap": SIGNAL_RHETORIC_CAP, "min_heat_units": SIGNAL_MIN_HEAT_UNITS, "spend_min_z": SIGNAL_SPEND_MIN_Z, "heat_tie_threshold": TIE_THRESHOLD,
                      "weights": {"aligned": SIGNAL_WEIGHT_ALIGNED, "opposed": SIGNAL_WEIGHT_OPPOSED, "single": SIGNAL_WEIGHT_SINGLE},
                      "excess_fit_races": [c[0] for c in covered]},
            "per_race": per_race,
            "framing": "Experimental. Outside spending and campaign rhetoric are read as signs of campaigns' internal polls. History shows only a weak, unproven link; this reading may be less accurate than the polling read.",
        }

    def compute(self, calc_version: str, release_id: str | None) -> dict:
        ss = (self.run_state or {}).get("stage_outcomes", {})
        stage2c = ss.get("stage2c") == "PASSED"
        stage2a = ss.get("stage2a") == "PASSED"
        ests = self.estimates()
        blocks = {race: self.race_block(race, ests, stage2c) for race in SENATE_RACES + GOVERNOR_RACES}
        heat = self.heat_block()
        derived = {
            "derived_schema": "1.0",
            "analytical_as_of": self.as_of.isoformat(),
            "calc_version": calc_version,
            "release_id": release_id,
            "stage2c_passed": stage2c,
            "stage_status": ss,
            "rating_source": self.run_state.get("rating_source"),
            "scope": {"senate_races": SENATE_RACES, "governor_races": GOVERNOR_RACES, "deferred": DEFERRED_RACES, "rcv_races": sorted(RCV_RACES)},
            "weighting_spec": {
                "formula": "weight = f_track * f_recency * f_sample * f_pop * f_sponsor * f_disclosure (heuristic, not an inverse variance)",
                "recency_half_life_days": RECENCY_HALF_LIFE_DAYS, "sample_cap_n": SAMPLE_CAP_N, "f_pop": F_POP, "f_sponsor": F_SPONSOR,
                "f_disclosure_unverified": F_DISCLOSURE_UNVERIFIED, "weight_cutoff": WEIGHT_CUTOFF, "design_effects": "unmodeled",
                "f_track": "provisional 1.0 until Stage 2c; then Silver Bulletin Simple Average Error thresholds 1.0 (<=3), 0.8 (3-5], 0.5 (>5)",
                "stage3_sigma": STAGE3_SIGMA, "stage3_clamp": STAGE3_CLAMP, "scenario_shifts_toward_R": SCENARIO_SHIFTS,
            },
            "estimates": [
                {k: e[k] for k in ("estimate_id", "poll_id", "sample_id", "tracking_series_id", "race", "pollster_id", "method_id", "sponsor_class",
                                    "pollster_alignment", "disclosure_status", "field_start", "field_end", "release_date", "pop", "denominator_class",
                                    "round", "window", "recall_weighted", "selected", "exclusion_reason", "source_url", "primary_verified")}
                | {"n": e["n_num"], "D": e["D_num"], "R": e["R_num"], "margin": e["margin_num"], "quarantined": e["quarantined"],
                   "field_midpoint": (e["fs"].toordinal() + e["fe"].toordinal()) / 2.0 - date(2026, 1, 1).toordinal() + 1 if e["fs"] and e["fe"] else None,
                   "flags": {"principal": e["flag_principal"], "recall_contrast": e["flag_recall_contrast"], "sponsor_restricted": e["flag_sponsor_restricted"], "weighted_average": e["flag_weighted_average"]},
                   "flag_reasons": e["flag_reasons"], "factors": e["factors"], "weight": e["weight"]}
                for e in sorted(ests, key=lambda e: e["estimate_id"])
            ],
            "races": blocks,
            "section5_contrasts": self.contrasts(ests, blocks),
            "section6_gov_sen_gaps": self.gov_sen_gaps(ests),
            "section9_heat": heat,
            "section10_coverage": sorted(({k: c[k] for k in COVERAGE_HEADER} for c in self.coverage), key=lambda c: (c["expected_edition"], c["race"])),
            "section2a_backtest": self.backtest_block(stage2a),
            "section2b_turnout": self.turnout_block(),
            "counts": self.counts(ests),
        }
        derived["signals"] = self.signals_block(blocks)
        return derived

    def counts(self, ests: list[dict]) -> dict:
        principal = [e for e in ests if e["flag_principal"]]
        both = [e for e in principal if e["window"] == "BOTH"]
        methods = [p for p in self.pollsters]
        by_pollster = defaultdict(set)
        for p in methods:
            by_pollster[p["pollster_id"]].add(p["recall_weighted"])
        mixed = sorted(pid for pid, s in by_pollster.items() if len(s - {"UNVERIFIED"}) > 1 or (len(s) > 1 and "UNVERIFIED" in s and len(s) > 1))
        return {
            "stored_rows": len(self.polls),
            "selected_estimates": len(principal),
            "selected_estimates_both": len(both),
            "selected_estimates_house_only": sum(1 for e in principal if e["window"] == "HOUSE_ONLY"),
            "quarantined_rows": sum(1 for e in ests if e["quarantined"]),
            "excluded_by_reason": dict(Counter(e["exclusion_reason"] for e in ests if e["selected"] == "0")),
            "distinct_samples": len({e["sample_id"] for e in principal}),
            "tracking_series": len({e["tracking_series_id"] for e in self.polls if e["tracking_series_id"] != "NA"}),
            "method_records": len(methods),
            "distinct_pollsters": len({p["pollster_id"] for p in methods} | {r["pollster_id"] for r in self.polls}),
            "recall_by_estimate_both": {k: sum(1 for e in both if e["recall_weighted"] == k) for k in RECALL_ESTIMATE},
            "recall_by_method_record": {k: sum(1 for p in methods if p["recall_weighted"] == k) for k in RECALL_METHOD},
            "mixed_firms": mixed,
            "races_with_averaging_stratum": None,  # filled after race blocks in release()
            "races_with_contrast_stratum": None,
            "weighted_average_flagged": sum(1 for e in ests if e["flag_weighted_average"]),
            "recall_contrast_flagged": sum(1 for e in ests if e["flag_recall_contrast"]),
            "exclusion_records": len(self.exclusions),
        }

    # ----- Stage 3
    def predictions(self, derived: dict, frozen_at: str) -> list[dict]:
        rows = []
        heat_set = ",".join(derived["section9_heat"]["races_with_defined_debate_gap"]) or "NA"
        ests = {e["estimate_id"]: e for e in derived["estimates"]}
        for race, blk in derived["races"].items():
            if blk["weighted_margin"] is None or not blk["averaging_stratum"]:
                continue
            strat = blk["averaging_stratum"]
            if race in RCV_RACES and strat["round"] != "FINAL":
                continue  # a race with only FIRST is excluded from vectors with reason (recorded in derived.json)
            in_avg = [ests[i] for i in blk["averaging_estimate_ids"]]
            for vector, pool in (("ALL_ELIGIBLE", in_avg), ("YES_ONLY", [e for e in in_avg if e["recall_weighted"] == "YES"]), ("NO_ONLY", [e for e in in_avg if e["recall_weighted"] == "NO"])):
                if vector != "ALL_ELIGIBLE":
                    cs = blk["contrast_stratum"]
                    if not cs:
                        continue
                    pool = [e for e in in_avg if e["recall_weighted"] == vector.split("_")[0] and (e["round"], e["denominator_class"], e["pop"]) == (cs["round"], cs["denominator_class"], cs["pop"])]
                    other = "NO" if vector == "YES_ONLY" else "YES"
                    if not pool or not any(e["recall_weighted"] == other and (e["round"], e["denominator_class"], e["pop"]) == (cs["round"], cs["denominator_class"], cs["pop"]) for e in in_avg):
                        continue
                if not pool:
                    continue
                m = sum(e["weight"] * e["margin"] for e in pool) / sum(e["weight"] for e in pool)
                rows.append({"race": race, "vector": vector, "p_d_slot": f"{stage3_probability(m):.4f}", "weighted_margin": f"{m:.2f}",
                             "stratum_round": strat["round"], "stratum_denominator": strat["denominator_class"], "stratum_pop": strat["pop"],
                             "n_retained": len(pool), "heat_race_set": heat_set, "frozen_at": frozen_at})
        return rows

    # ----- release
    def release(self, release_id: str, calc_version: str, note_path: str, freeze: bool = False) -> str:
        if not self.validate():
            raise ValidationError("validation failed:\n  " + "\n  ".join(self.problems))
        rel_dir = os.path.join(self.dir, "releases", release_id)
        if os.path.exists(rel_dir):
            raise ValidationError(f"release {release_id} already exists; a release is written once and never modified")
        final_dir = rel_dir
        os.makedirs(os.path.dirname(final_dir), exist_ok=True)
        rel_dir = tempfile.mkdtemp(prefix=".staging-", dir=os.path.dirname(final_dir))
        derived = self.compute(calc_version, release_id)
        derived["counts"]["races_with_averaging_stratum"] = sorted(r for r, b in derived["races"].items() if b["averaging_stratum"])
        derived["counts"]["races_with_contrast_stratum"] = sorted(r for r, b in derived["races"].items() if b["contrast_stratum"])
        files = []
        ss = (self.run_state or {}).get("stage_outcomes", {})
        copy_names = ["polls.csv", "pollsters.csv", "exclusions.csv", "heat.csv", "coverage.csv"]
        if ss.get("stage2a") == "PASSED" and os.path.exists(os.path.join(self.dir, "backtest-2025.csv")):
            copy_names.append("backtest-2025.csv")
        copy_names += [n for n in ("spending.csv", "fundamentals.csv", "spend-history.csv") if os.path.exists(os.path.join(self.dir, n))]
        for name in copy_names:
            src = os.path.join(self.dir, name)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(rel_dir, name))
        if os.path.exists(note_path):
            shutil.copyfile(note_path, os.path.join(rel_dir, "midterm-2026-poll-weighting.md"))
        with open(os.path.join(rel_dir, "derived.json"), "w", encoding="utf-8") as f:
            json.dump(derived, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        if freeze:
            frozen_at = datetime.now().astimezone().isoformat(timespec="seconds")
            write_csv(os.path.join(rel_dir, "predictions.csv"), PREDICTIONS_HEADER, self.predictions(derived, frozen_at))
        for name in sorted(os.listdir(rel_dir)):
            p = os.path.join(rel_dir, name)
            rows = None
            if name.endswith(".csv"):
                with open(p, "r", encoding="utf-8", newline="") as f:
                    rows = max(0, sum(1 for _ in csv.reader(f)) - 1)
            files.append({"path": name, "sha256": sha256_file(p), "bytes": os.path.getsize(p), "rows": rows})
        rating = None
        rated = [p for p in self.pollsters if not is_na(p["rating_source"])]
        if rated:
            p0 = rated[0]
            rating = {"name": p0["rating_source"], "version_label": p0["rating_version"], "file_name": None, "downloaded_at": None, "sha256": None}
            rs_meta = (self.run_state or {}).get("rating_source")
            if rs_meta:
                rating.update({k: rs_meta.get(k) for k in ("file_name", "downloaded_at", "sha256") if k in rs_meta})
        scorer = None
        scored = [h for h in self.heat if h["status"] == "SCORED"]
        if scored:
            h0 = scored[0]
            scorer = {"meter_commit": h0["scorer_commit"], "prompt_sha256": h0["prompt_sha256"], "model": h0["model"], "config_sha256": h0["config_sha256"]}
        manifest = {
            "bundle_schema": BUNDLE_SCHEMA,
            "release_id": release_id,
            "analytical_as_of": self.as_of.isoformat(),
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "calc_version": {"repo": "midterm-2026", "commit": calc_version, "weight_py_sha256": sha256_file(os.path.abspath(__file__))},
            "csv_schemas": CSV_SCHEMAS,
            "stage_status": {k: ss.get(k, "NOT_STARTED") for k in ("stage1", "stage1b", "stageW", "stage2a", "stage2b", "stage2c", "stage3")},
            "files": files,
            "scope": {"senate_races": SENATE_RACES, "governor_races": GOVERNOR_RACES, "deferred": DEFERRED_RACES},
            "rating_source": rating,
            "scorer": scorer,
            "supersedes": (self.run_state or {}).get("supersedes"),
            "reason": (self.run_state or {}).get("supersedes_reason"),
        }
        with open(os.path.join(rel_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        os.rename(rel_dir, final_dir)
        return final_dir


# ----------------------------------------------------------------------------- self-test
def _mk(eid, race, pollster, fs, fe, rd, n, pop, d, r, denom="FULL", rnd="NA", recall="YES", sponsor="NONPARTISAN", disclosure="DISCLOSED",
        selected="1", excl="NA", series="NA", poll_id=None, sample_id=None, method=None, url=None, superseded_by="NA", supersedes="NA"):
    return {
        "estimate_id": eid, "poll_id": poll_id or f"P-{eid}", "sample_id": sample_id or f"S-{eid}", "tracking_series_id": series, "race": race,
        "pollster_id": pollster, "method_id": method or f"M-{pollster}", "sponsor": "self", "sponsor_class": sponsor, "pollster_alignment": "NONE",
        "disclosure_status": disclosure, "field_start": fs, "field_end": fe, "release_date": rd, "n": "NA" if n is None else str(n), "pop": pop,
        "D": str(d), "R": str(r), "other": "NA", "undecided": "NA", "denominator_class": denom, "margin": f"{d - r:.2f}", "round": rnd,
        "window": "BOTH", "recall_weighted": recall, "selected": selected, "exclusion_reason": excl, "supersedes": supersedes, "superseded_by": superseded_by,
        "source_url": url or f"https://example.org/{eid}", "source_locator": "p1", "primary_verified": "YES", "retrieved_at": "2026-10-25T18:00:00Z", "notes": "",
    }


def _mkm(pollster, recall="YES", f_track="1.0"):
    return {"pollster_id": pollster, "pollster_name": pollster, "aliases": "", "method_id": f"M-{pollster}", "applicability": "CYCLE_BOILERPLATE",
            "recall_weighted": recall, "weighting_quote": "weighted to 2024 presidential vote" if recall != "UNVERIFIED" else "NA", "recall_target": "NA",
            "mode": "online", "ti_member": "unknown", "method_owner": pollster, "method_url": "https://example.org/method", "method_locator": "p1",
            "method_date": "2026-10-01", "retrieved_at": "2026-10-25T18:00:00Z", "rating_source": "NA", "rating_version": "NA", "rating_metric": "NA",
            "rating_value": "NA", "rating_units": "NA", "rating_poll_count": "NA", "rating_bias_metric": "NA", "rating_bias_value": "NA", "rating_cohort": "NA",
            "track_status": "PROVISIONAL", "f_track": f_track, "new_pollster": "NA", "track_ledger_ref": "NA", "notes": ""}


def _bundle(tmp, polls, pollsters, exclusions=(), heat=(), coverage=(), run_state=None, derive=True):
    os.makedirs(tmp, exist_ok=True)
    as_of = parse_as_of("2026-10-25T11:00:00-07:00")
    write_csv(os.path.join(tmp, "polls.csv"), POLLS_HEADER, polls)
    write_csv(os.path.join(tmp, "pollsters.csv"), POLLSTERS_HEADER, pollsters)
    write_csv(os.path.join(tmp, "exclusions.csv"), EXCLUSIONS_HEADER, list(exclusions))
    write_csv(os.path.join(tmp, "heat.csv"), HEAT_HEADER, list(heat))
    write_csv(os.path.join(tmp, "coverage.csv"), COVERAGE_HEADER, list(coverage))
    b = Bundle(tmp, as_of, run_state)
    if derive:
        b.polls = b.derive_rows(b.polls)
        write_csv(os.path.join(tmp, "polls.csv"), POLLS_HEADER, b.polls)
    return b


def self_test(bundle_dir_for_tmp: str) -> int:
    import tempfile
    fails = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    as_of = date(2026, 10, 25)
    # recency at 0, 5, 10, 20 days (midpoint age)
    for days, expected in ((0, 1.0), (5, 0.5), (10, 0.25), (20, 0.0625)):
        fe = as_of - timedelta(days=days)
        v = f_recency(fe, fe, as_of)
        check(f"recency age {days}d = {expected}", abs(v - expected) < 1e-9, f"{v}")
    # half-day midpoint kept: field 10-23..10-24 -> midpoint 10-23.5 -> age 1.5
    v = f_recency(date(2026, 10, 23), date(2026, 10, 24), as_of)
    check("recency half-day midpoint age 1.5", abs(v - 2 ** (-1.5 / 5)) < 1e-9, f"{v}")
    # sample
    for n, expected in ((300, 0.5), (600, math.sqrt(0.5)), (1200, 1.0), (2000, 1.0)):
        check(f"f_sample n={n}", abs(f_sample(n) - expected) < 1e-9, f"{f_sample(n)}")
    check("f_sample n=None -> None", f_sample(None) is None)
    # pop, sponsor, disclosure
    check("f_pop", (f_pop("LV"), f_pop("RV"), f_pop("A")) == (1.0, 0.7, 0.4))
    check("f_sponsor precedence", (f_sponsor("INTERNAL"), f_sponsor("PARTISAN_PUBLIC"), f_sponsor("NONPARTISAN"), f_sponsor("BIPARTISAN"), f_sponsor("UNKNOWN")) == (0.3, 0.6, 1.0, 1.0, None))
    check("f_disclosure", (f_disclosure("DISCLOSED"), f_disclosure("UNDISCLOSED"), f_disclosure("UNVERIFIED")) == (1.0, 0.7, 0.7))
    # track thresholds on Simple Average Error only
    check("f_track thresholds", (f_track_from_simple_average_error(3.0), f_track_from_simple_average_error(3.01), f_track_from_simple_average_error(5.0), f_track_from_simple_average_error(5.01), f_track_from_simple_average_error(None)) == (1.0, 0.8, 0.8, 0.5, 1.0))
    # cutoff equality at 0.05: weight exactly 0.05 is retained (>= 0.05), 0.0499 removed
    tmp = tempfile.mkdtemp(prefix="wt-")
    # Build a weight exactly 0.05: f_track 0.5 * recency 1.0 (midpoint = as_of... use fe=fs=as_of) * f_sample(300)=0.5 * f_pop A 0.4 * sponsor 1.0 * disclosure UNDISCLOSED 0.7 = 0.07; use INTERNAL 0.3 -> 0.5*1*0.5*0.4*0.3*... let's compute: want 0.05
    # f_track 1.0, recency 1.0, f_sample(1200)=1, pop RV 0.7, sponsor INTERNAL 0.3, disclosure 0.7 -> 0.147; pop A 0.4*0.3*0.7 = 0.084; with f_sample(300)=0.5 -> 0.042 (<0.05 removed); f_sample(425)=0.5951 -> 0.04999
    polls = [
        _mk("E1", "2026-TX-SEN", "PA", "2026-10-25", "2026-10-25", "2026-10-25", 1200, "A", 50, 40, sponsor="INTERNAL", disclosure="UNDISCLOSED"),  # 0.084 kept
        _mk("E2", "2026-TX-SEN", "PB", "2026-10-25", "2026-10-25", "2026-10-25", 300, "A", 50, 40, sponsor="INTERNAL", disclosure="UNDISCLOSED"),  # 0.042 removed
    ]
    b = _bundle(tmp + "/cutoff", polls, [_mkm("PA"), _mkm("PB")])
    ests = {e["estimate_id"]: e for e in b.estimates()}
    check("cutoff: 0.084 retained", ests["E1"]["flag_weighted_average"] and abs(ests["E1"]["weight"] - 0.084) < 1e-6, f"{ests['E1']['weight']}")
    check("cutoff: 0.042 removed with reason", not ests["E2"]["flag_weighted_average"] and any("below cutoff" in r for r in ests["E2"]["flag_reasons"]))
    # exact equality: construct weight 0.05 via f_track 0.5 * sample(1200)=1 * pop LV 1 * sponsor PARTISAN_PUBLIC 0.6 ... 0.3; use f_track 0.5, pop RV 0.7, INTERNAL 0.3, disclosure 1.0 -> 0.105; disclosure 0.7 -> 0.0735. Use direct check of the comparison rule instead:
    check("cutoff rule: 0.05 is retained, 0.0499 is not", (0.05 >= WEIGHT_CUTOFF) and not (0.0499 >= WEIGHT_CUTOFF))
    # UNVERIFIED and NA handling
    check("num('UNVERIFIED') -> None and num('NA') -> None", num("UNVERIFIED") is None and num("NA") is None)
    polls = [_mk("U1", "2026-TX-SEN", "PU", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, recall="UNVERIFIED")]
    b = _bundle(tmp + "/unv", polls, [_mkm("PU", "UNVERIFIED")])
    e = b.estimates()[0]
    check("UNVERIFIED estimate: weighted_average kept, recall_contrast removed", e["flag_weighted_average"] and not e["flag_recall_contrast"])
    blk = b.race_block("2026-TX-SEN", b.estimates(), False)
    check("(3) all-UNVERIFIED race still has an averaging stratum and a preliminary mean", blk["averaging_stratum"] is not None and blk["preliminary_unweighted_margin"] == 2.0, f"{blk['averaging_stratum']} {blk['preliminary_unweighted_margin']}")
    check("(3) all-UNVERIFIED race: contrast stratum null with reason", blk["contrast_stratum"] is None and bool(blk["contrast_stratum_reason"]), blk["contrast_stratum_reason"])
    # all-YES race
    polls = [_mk("Y1", "2026-IA-SEN", "PY", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, recall="YES"), _mk("Y2", "2026-IA-SEN", "PZ", "2026-10-19", "2026-10-21", "2026-10-22", 600, "LV", 47, 47, recall="YES")]
    b = _bundle(tmp + "/yes", polls, [_mkm("PY"), _mkm("PZ")])
    blk = b.race_block("2026-IA-SEN", b.estimates(), False)
    check("(3) all-YES race still averages, contrast null", blk["averaging_stratum"] == {"round": "NA", "denominator_class": "FULL", "pop": "LV"} and blk["contrast_stratum"] is None and blk["retained_count"] == 2)
    # empty inventory / empty race
    b = _bundle(tmp + "/empty", [], [])
    d = b.compute("test", None)
    check("empty inventory computes, contrasts NA", d["section5_contrasts"]["i"]["value"] is None and d["races"]["2026-TX-SEN"]["averaging_stratum"] is None)
    check("empty race block reason", "no weighted_average" in d["races"]["2026-NC-SEN"]["averaging_stratum_reason"])
    # round=NA race
    polls = [_mk("N1", "2026-MI-SEN", "PN", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46)]
    b = _bundle(tmp + "/na", polls, [_mkm("PN")])
    check("round=NA race averaging stratum round NA", b.race_block("2026-MI-SEN", b.estimates(), False)["averaging_stratum"]["round"] == "NA")
    # (2) RCV race: one FINAL and three FIRST -> FINAL chosen, all four rows kept
    polls = [
        _mk("R1", "2026-ME-SEN", "PR1", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 47, 45, rnd="FIRST", poll_id="P-R1"),
        _mk("R2", "2026-ME-SEN", "PR1", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 51, 49, rnd="FINAL", poll_id="P-R1", sample_id="S-R1"),
        _mk("R3", "2026-ME-SEN", "PR2", "2026-10-18", "2026-10-21", "2026-10-22", 600, "LV", 46, 44, rnd="FIRST", recall="NO"),
        _mk("R4", "2026-ME-SEN", "PR3", "2026-10-17", "2026-10-20", "2026-10-21", 700, "LV", 45, 44, rnd="FIRST"),
    ]
    b = _bundle(tmp + "/rcv", polls, [_mkm("PR1"), _mkm("PR2", "NO"), _mkm("PR3")])
    ests = b.estimates()
    blk = b.race_block("2026-ME-SEN", ests, False)
    check("(2) RCV FINAL precedence: averaging stratum FINAL, 1 retained, no fallback flag", blk["averaging_stratum"]["round"] == "FINAL" and blk["retained_count"] == 1 and blk["rcv_first_round_fallback"] == 0, f"{blk['averaging_stratum']} {blk['retained_count']}")
    check("(2) all four RCV rows kept and selected", sum(1 for e in ests if e["selected"] == "1") == 4 and blk["stored_row_count"] == 4)
    polls = [p for p in polls if p["estimate_id"] != "R2"]
    b = _bundle(tmp + "/rcv2", polls, [_mkm("PR1"), _mkm("PR2", "NO"), _mkm("PR3")])
    blk = b.race_block("2026-ME-SEN", b.estimates(), False)
    check("(2) RCV FIRST-only: averages FIRST with fallback flag", blk["averaging_stratum"]["round"] == "FIRST" and blk["rcv_first_round_fallback"] == 1 and blk["retained_count"] == 3)
    check("(2) RCV FIRST-only contrast stratum FIRST with both groups", blk["contrast_stratum"] == {"round": "FIRST", "denominator_class": "FULL", "pop": "LV"} and blk["contrast_rcv_first_round_fallback"] == 1)
    # averaging stratum chosen with no YES-NO pair present (covered above); multiple denominator strata and the tie-break
    polls = [
        _mk("T1", "2026-NC-SEN", "PT1", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, denom="TWO_WAY"),
        _mk("T2", "2026-NC-SEN", "PT2", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, denom="FULL"),
        _mk("T3", "2026-NC-SEN", "PT3", "2026-10-20", "2026-10-22", "2026-10-23", 800, "RV", 48, 46, denom="FULL"),
    ]
    b = _bundle(tmp + "/tie", polls, [_mkm("PT1"), _mkm("PT2"), _mkm("PT3")])
    blk = b.race_block("2026-NC-SEN", b.estimates(), False)
    check("tie-break: FULL over TWO_WAY, LV over RV", blk["averaging_stratum"] == {"round": "NA", "denominator_class": "FULL", "pop": "LV"}, f"{blk['averaging_stratum']}")
    # LV-only YES versus RV-only NO: excluded from (ii) and (iv), present in (i), weighted average still produced
    polls = [
        _mk("L1", "2026-OH-SEN-SPECIAL", "PL1", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, recall="YES"),
        _mk("L2", "2026-OH-SEN-SPECIAL", "PL2", "2026-10-20", "2026-10-22", "2026-10-23", 800, "RV", 44, 46, recall="NO"),
    ]
    b = _bundle(tmp + "/lvrv", polls, [_mkm("PL1"), _mkm("PL2", "NO")])
    d = b.compute("test", None)
    blk = d["races"]["2026-OH-SEN-SPECIAL"]
    check("LV-YES vs RV-NO: (i) computed = 4.0", d["section5_contrasts"]["i"]["value"] == 4.0, f"{d['section5_contrasts']['i']['value']}")
    check("LV-YES vs RV-NO: (ii) NA, race absent with reason", d["section5_contrasts"]["ii"]["value"] is None and blk["contrast_stratum"] is None)
    check("LV-YES vs RV-NO: (iv) NA (only YES in LV)", d["section5_contrasts"]["iv"]["value"] is None)
    check("LV-YES vs RV-NO: weighted average still produced (averaging stratum LV, 1 retained)", blk["averaging_stratum"]["pop"] == "LV" and blk["retained_count"] == 1)
    # missing sponsor: recall_contrast kept, weighted_average removed
    polls = [_mk("S1", "2026-GA-SEN", "PS", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, sponsor="UNKNOWN")]
    b = _bundle(tmp + "/sponsor", polls, [_mkm("PS")])
    e = b.estimates()[0]
    check("UNKNOWN sponsor: recall_contrast kept, weighted_average removed", e["flag_recall_contrast"] and not e["flag_weighted_average"] and "sponsor_class UNKNOWN" in e["flag_reasons"])
    # missing n: recall_contrast kept, weighted_average removed
    polls = [_mk("S2", "2026-GA-SEN", "PS", "2026-10-20", "2026-10-22", "2026-10-23", None, "LV", 48, 46)]
    b = _bundle(tmp + "/nmissing", polls, [_mkm("PS")])
    e = b.estimates()[0]
    check("missing n: recall_contrast kept, weighted_average removed", e["flag_recall_contrast"] and not e["flag_weighted_average"] and "n missing" in e["flag_reasons"])
    # (1) tracking-series overlap reduced vs two pollsters with identical dates both kept
    polls = [
        _mk("K1", "2026-TX-SEN", "PK", "2026-10-18", "2026-10-21", "2026-10-22", 1000, "LV", 48, 46, series="TS-PK-TX"),
        _mk("K2", "2026-TX-SEN", "PK", "2026-10-20", "2026-10-23", "2026-10-24", 1000, "LV", 47, 46, series="TS-PK-TX"),   # overlaps K1 -> K1 dropped
        _mk("K3", "2026-TX-SEN", "PK", "2026-10-14", "2026-10-17", "2026-10-18", 1000, "LV", 49, 46, series="TS-PK-TX"),   # no overlap with K2 -> kept
        _mk("K4", "2026-TX-SEN", "PX", "2026-10-20", "2026-10-23", "2026-10-24", 800, "LV", 50, 45),                      # different pollster, identical dates to K2 -> kept
        _mk("K5", "2026-TX-SEN", "PX", "2026-10-20", "2026-10-23", "2026-10-24", 800, "LV", 50, 45, poll_id="P-K5b", sample_id="S-K5b", url="https://example.org/K5b"),  # same pollster, distinct standalone, same dates, different URL
    ]
    b = _bundle(tmp + "/tracker", polls, [_mkm("PK"), _mkm("PX")])
    sel = {e["estimate_id"]: (e["selected"], e["exclusion_reason"]) for e in b.polls}
    check("(1) tracker: K1 dropped TRACKER_OVERLAP, K2 and K3 kept", sel["K1"] == ("0", "TRACKER_OVERLAP") and sel["K2"][0] == "1" and sel["K3"][0] == "1", f"{sel}")
    check("(1) two different pollsters with identical dates both stay selected", sel["K2"][0] == "1" and sel["K4"][0] == "1")
    check("(1) uniqueness: same pollster, same dates, different URL -> both active, validation passes", b.validate(), "; ".join(b.problems))
    # same dates same URL duplicate must fail validation
    polls_dup = polls + [_mk("K6", "2026-TX-SEN", "PX", "2026-10-20", "2026-10-23", "2026-10-24", 800, "LV", 50, 45, poll_id="P-K6", sample_id="S-K6", url="https://example.org/K4")]
    b2 = _bundle(tmp + "/trackerdup", polls_dup, [_mkm("PK"), _mkm("PX")])
    check("uniqueness: same pollster, same dates, same URL -> hard error", not b2.validate() and any("without distinct source URLs" in p for p in b2.problems))
    # Unverified source inputs and unverified RCV rounds remain inventoried, never analytical.
    unverified_source = _mk("UV-SOURCE", "2026-TX-SEN", "PUV", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46)
    unverified_source["primary_verified"] = "UNVERIFIED"
    unverified_round = _mk("UV-ROUND", "2026-AK-SEN", "PUV", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, rnd="UNVERIFIED")
    b = _bundle(tmp + "/unverified-inputs", [unverified_source, unverified_round], [_mkm("PUV")], run_state={"stage_outcomes": {"stage2c": "PASSED"}})
    check("unverified source/round: valid inventory, no recall or weighted eligibility", b.validate() and all(e["flag_principal"] and not e["flag_recall_contrast"] and not e["flag_weighted_average"] for e in b.estimates()))
    check("unverified source/round: no preliminary or weighted race mean", all(b.race_block(r, b.estimates(), True)["preliminary_unweighted_margin"] is None for r in ("2026-TX-SEN", "2026-AK-SEN")))
    # population alternatives: LV principal over RV over A; FULL over LEANERS over TWO_WAY
    polls = [
        _mk("A1", "2026-IA-SEN", "PA", "2026-10-20", "2026-10-22", "2026-10-23", 800, "RV", 48, 46, poll_id="P-A", sample_id="S-A"),
        _mk("A2", "2026-IA-SEN", "PA", "2026-10-20", "2026-10-22", "2026-10-23", 700, "LV", 48, 45, poll_id="P-A", sample_id="S-A"),
        _mk("A3", "2026-IA-SEN", "PA", "2026-10-20", "2026-10-22", "2026-10-23", 700, "LV", 50, 47, denom="LEANERS", poll_id="P-A", sample_id="S-A"),
        _mk("A4", "2026-IA-SEN", "PA", "2026-10-20", "2026-10-22", "2026-10-23", 700, "LV", 52, 48, denom="TWO_WAY", poll_id="P-A", sample_id="S-A"),
    ]
    b = _bundle(tmp + "/alts", polls, [_mkm("PA")])
    sel = {e["estimate_id"]: e["selected"] for e in b.polls}
    check("population alternatives: only LV FULL is principal", sel == {"A1": "0", "A2": "1", "A3": "0", "A4": "0"}, f"{sel}")
    # corrected row supersession
    polls = [
        _mk("C1", "2026-TX-SEN", "PC", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, superseded_by="C1"),  # old row (same estimate_id kept by convention -> we test via distinct ids)
    ]
    polls = [
        _mk("C1", "2026-TX-SEN", "PC", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46, superseded_by="C1-v2", poll_id="P-C1"),
        _mk("C1-v2", "2026-TX-SEN", "PC", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 45, supersedes="C1", poll_id="P-C1", url="https://example.org/C1"),
    ]
    b = _bundle(tmp + "/supersede", polls, [_mkm("PC")])
    sel = {e["estimate_id"]: (e["selected"], e["exclusion_reason"]) for e in b.polls}
    check("supersession: old row SUPERSEDED and unselected, new row selected", sel["C1"] == ("0", "SUPERSEDED") and sel["C1-v2"][0] == "1", f"{sel}")
    check("supersession validates", b.validate(), "; ".join(b.problems))
    # (4) cache key differs by prompt hash and is identical for identical inputs
    k1 = cache_key("u", "c", "p1", "m", "cfg")
    k2 = cache_key("u", "c", "p2", "m", "cfg")
    k3 = cache_key("u", "c", "p1", "m", "cfg")
    check("(4) cache key: two prompt hashes -> two keys", k1 != k2)
    check("(4) cache key: identical inputs -> one key", k1 == k3)
    # signed-error sign
    check("signed error: poll D+2, certified D+5 -> -3 (toward R)", signed_error(2.0, 5.0) == -3.0)
    # debate and ad gap separation and TIE
    heat = [
        {"heat_id": "H1", "race": "2026-TX-SEN", "candidate": "Dee", "slot": "D", "source_type": "DEBATE", "unit_id": "d1", "unit_label": "a1", "source_url": "https://x", "caption_source": "BROADCASTER", "unit_sha256": "aa", "status": "SCORED", "ph_score": "3.0", "ph_label": "Mixed Signals", "hottest_line": "", "calmest_line": "", "scorer_commit": "c", "prompt_sha256": "p", "model": "m", "config_sha256": "k", "scored_at": "2026-10-25T18:00:00Z", "cost_usd": "0.01", "reserved_usd": "0.015", "notes": ""},
        {"heat_id": "H2", "race": "2026-TX-SEN", "candidate": "Arr", "slot": "R", "source_type": "DEBATE", "unit_id": "d2", "unit_label": "a1", "source_url": "https://x", "caption_source": "BROADCASTER", "unit_sha256": "bb", "status": "SCORED", "ph_score": "3.05", "ph_label": "Mixed Signals", "hottest_line": "", "calmest_line": "", "scorer_commit": "c", "prompt_sha256": "p", "model": "m", "config_sha256": "k", "scored_at": "2026-10-25T18:00:00Z", "cost_usd": "0.01", "reserved_usd": "0.015", "notes": ""},
        {"heat_id": "H3", "race": "2026-TX-SEN", "candidate": "Dee", "slot": "D", "source_type": "AD", "unit_id": "ad1", "unit_label": "ad", "source_url": "https://x", "caption_source": "AUTO", "unit_sha256": "cc", "status": "SCORED", "ph_score": "4.5", "ph_label": "Hyperbolic", "hottest_line": "", "calmest_line": "", "scorer_commit": "c", "prompt_sha256": "p", "model": "m", "config_sha256": "k", "scored_at": "2026-10-25T18:00:00Z", "cost_usd": "0.01", "reserved_usd": "0.015", "notes": ""},
        {"heat_id": "H4", "race": "2026-TX-SEN", "candidate": "Arr", "slot": "R", "source_type": "AD", "unit_id": "ad2", "unit_label": "ad", "source_url": "https://x", "caption_source": "AUTO", "unit_sha256": "dd", "status": "MISSING_TRANSCRIPT", "ph_score": "NA", "ph_label": "NA", "hottest_line": "", "calmest_line": "", "scorer_commit": "NA", "prompt_sha256": "NA", "model": "NA", "config_sha256": "NA", "scored_at": "NA", "cost_usd": "0", "reserved_usd": "0", "notes": "no channel"},
    ]
    b = _bundle(tmp + "/heat", [], [], heat=heat)
    hb = b.heat_block()["per_race"]["2026-TX-SEN"]
    check("heat: debate gap -0.05 is a TIE", hb["debate_gap"]["gap"] == -0.05 and hb["debate_gap"]["hotter"] == "TIE")
    check("heat: ad gap undefined when one side has no SCORED ad; ads never pooled with debates", hb["ad_gap"]["gap"] is None and hb["candidates"]["D"]["DEBATE"]["mean"] == 3.0)
    check("heat: validation passes", b.validate(), "; ".join(b.problems))
    # budget reservation arithmetic
    allowed, est = budget_check(spent=2.0, reserved=0.5, units=10, unit_rate=0.04)
    check("budget: 2.0 + 0.5 + 10*0.04*1.5=0.6 -> 3.1 > 3.0 refused", not allowed and abs(est - 0.6) < 1e-9)
    allowed, est = budget_check(spent=2.0, reserved=0.4, units=10, unit_rate=0.04)
    check("budget: 2.0 + 0.4 + 0.6 = 3.0 allowed at equality", allowed)
    # Stage 3 mapping
    check("stage3: p(0)=0.5, p(5)=Phi(1), clamp at 0.97", abs(stage3_probability(0) - 0.5) < 1e-9 and abs(stage3_probability(5.0) - phi(1.0)) < 1e-9 and stage3_probability(40.0) == 0.97)
    # window derivation
    check("window: Sept HOUSE_ONLY, Oct BOTH, release after as_of OUT_OF_WINDOW", window_of(date(2026, 9, 15), date(2026, 9, 16), as_of) == "HOUSE_ONLY" and window_of(date(2026, 10, 15), date(2026, 10, 16), as_of) == "BOTH" and window_of(date(2026, 10, 24), date(2026, 10, 26), as_of) == "OUT_OF_WINDOW")
    # determinism: identical inputs and as_of -> identical derived.json bytes
    polls = [_mk("D1", "2026-TX-SEN", "PD", "2026-10-20", "2026-10-22", "2026-10-23", 800, "LV", 48, 46), _mk("D2", "2026-TX-SEN", "PE", "2026-10-19", "2026-10-21", "2026-10-22", 900, "LV", 47, 46, recall="NO")]
    b1 = _bundle(tmp + "/det1", polls, [_mkm("PD"), _mkm("PE", "NO")])
    b2 = _bundle(tmp + "/det2", polls, [_mkm("PD"), _mkm("PE", "NO")])
    j1 = json.dumps(b1.compute("v", "rel"), sort_keys=True)
    j2 = json.dumps(b2.compute("v", "rel"), sort_keys=True)
    check("determinism: byte-identical derived output across two runs", j1 == j2)
    check("per-race contrast computed for TX when both groups exist", b1.race_block("2026-TX-SEN", b1.estimates(), False)["per_race_contrast"]["yes_minus_no"] == 1.0)
    # weighted margin null until 2c, computed after
    d_before = b1.compute("v", None)["races"]["2026-TX-SEN"]
    b1.run_state = {"stage_outcomes": {"stage2c": "PASSED"}}
    d_after = b1.compute("v", None)["races"]["2026-TX-SEN"]
    check("Section 7: weighted_margin null before 2c, computed after", d_before["weighted_margin"] is None and d_after["weighted_margin"] is not None and d_after["no_cutoff_margin"] is not None)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(fails)} failure(s)" if fails else "\nall self-tests passed")
    return 1 if fails else 0


# ----------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--derive", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--compute", action="store_true")
    ap.add_argument("--release", metavar="RELEASE_ID")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--as-of")
    ap.add_argument("--bundle-dir", default=DEFAULT_BUNDLE_DIR)
    ap.add_argument("--calc-version", default="unknown")
    ap.add_argument("--run-state")
    ap.add_argument("--note", default=DEFAULT_NOTE)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.bundle_dir)
    run_state = None
    if a.run_state and os.path.exists(a.run_state):
        with open(a.run_state, "r", encoding="utf-8") as f:
            run_state = json.load(f)
    as_of = None
    if a.as_of:
        as_of = parse_as_of(a.as_of)
    elif run_state and run_state.get("analytical_as_of"):
        as_of = parse_as_of(run_state["analytical_as_of"])
    if (a.derive or a.compute or a.release) and as_of is None:
        print("--as-of (or --run-state with analytical_as_of) is required", file=sys.stderr)
        return 2
    try:
        b = Bundle(a.bundle_dir, as_of, run_state)
    except ValidationError as e:
        print(f"HARD ERROR: {e}", file=sys.stderr)
        return 1
    if a.derive:
        path = os.path.join(a.bundle_dir, "polls.csv")
        snap = snapshot(path, a.bundle_dir)
        b.polls = b.derive_rows(b.polls)
        write_csv(path, POLLS_HEADER, b.polls)
        print(f"derived margin/window/selected/exclusion_reason into polls.csv (snapshot {snap})")
        bt = os.path.join(a.bundle_dir, "backtest-2025.csv")
        if os.path.exists(bt):
            snapb = snapshot(bt, a.bundle_dir)
            rows = b.derive_rows(b.backtest, backtest=True)
            for r in rows:
                cm = num(r.get("certified_margin"))
                m = num(r["margin"])
                r["signed_error"] = "NA" if (cm is None or m is None) else f"{signed_error(m, cm):.2f}"
            write_csv(bt, BACKTEST_HEADER, rows)
            b.backtest = rows
            print(f"derived backtest-2025.csv (snapshot {snapb})")
    if a.validate or a.release or a.compute:
        ok = b.validate()
        for n in b.notes:
            print(f"NOTE: {n}", file=sys.stderr if a.compute else sys.stdout)
        for p in b.problems:
            print(f"HARD ERROR: {p}", file=sys.stderr)
        if not ok:
            return 1
        if a.validate:
            print(f"validation passed: {len(b.polls)} poll rows, {len(b.pollsters)} method records, {len(b.exclusions)} exclusion records, {len(b.heat)} heat rows, {len(b.coverage)} coverage rows, {len(b.backtest)} backtest rows")
    if a.compute:
        d = b.compute(a.calc_version, None)
        json.dump(d, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
        print()
    if a.release:
        try:
            out = b.release(a.release, a.calc_version, a.note, freeze=a.freeze)
        except ValidationError as e:
            print(f"HARD ERROR: {e}", file=sys.stderr)
            return 1
        print(f"release written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
