#!/usr/bin/env python3
"""Build the signal inputs for the signal-adjusted reading (method: Resources/methods/midterm-2026-signal-adjusted-reading.md).

Aggregation only, no estimation: weight.py owns every analytical number. Writes three bundle CSVs:
  spending.csv      per Senate race: outside spending by favored side in the 14 days ending at the analytical cutoff
                    and the 14 days before that (FEC Schedule E, latest amendment per transaction)
  fundamentals.csv  per in-scope race: 2024 presidential D-minus-R margin in the state (FEC official results)
  spend-history.csv 2020 and 2022 Senate races from the 2026-10-25 spending study, with the 2020 presidential margin,
                    the inputs weight.py uses to update the spending prior

Usage: python3 scripts/build_signals.py --sources sources/signals-20261026 [--bundle-dir <vault bundle>]
Every bundle file is snapshotted to .backups/ before it is replaced (ROE 14). A missing or changed source fails loudly.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402

WINDOW_DAYS = 14
FEC_DATE_FORMATS = ("%d-%b-%y", "%m/%d/%Y", "%Y-%m-%d", "%d-%b-%Y", "%m/%d/%y")
SPENDING_HEADER = ["race", "state", "fec_coverage", "window_end", "d_fav_recent", "r_fav_recent", "d_fav_prior", "r_fav_prior",
                   "rows_recent", "rows_dated_by_dissemination", "source_file", "source_sha256"]
FUNDAMENTALS_HEADER = ["race", "state", "pres_year", "pres_d_minus_r", "source_file", "source_sha256"]
HISTORY_HEADER = ["year", "state", "poll_margin", "result_margin", "log_recent_spend_m", "pres_year", "pres_d_minus_r", "source_sha256"]
SOURCES = {"ie": "ie2026.csv", "pres2024": "2024presgeresults.xlsx", "pres2020": "federalelections2020.xlsx", "history": "history-races-v5.csv"}


def fec_date(s: str) -> date | None:
    s = (s or "").strip()
    for fmt in FEC_DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def favored_side(party: str, sup_opp: str) -> str | None:
    p, so = (party or "").strip().upper()[:3], (sup_opp or "").strip().upper()[:1]
    if so not in ("S", "O"):
        return None
    if p == "DEM":
        return "D" if so == "S" else "R"
    if p == "REP":
        return "R" if so == "S" else "D"
    return None


def latest_amendments(rows: list[dict]) -> list[dict]:
    keep: dict[tuple, dict] = {}

    def fnum(r):
        try:
            return int(r.get("file_num") or 0)
        except ValueError:
            return 0
    for r in rows:
        k = (r["spe_id"], r["tran_id"])
        if k not in keep or fnum(r) > fnum(keep[k]):
            keep[k] = r
    return list(keep.values())


def aggregate_spending(rows: list[dict], state: str, window_end: date) -> dict:
    recent_start = window_end - timedelta(days=WINDOW_DAYS)
    prior_start = recent_start - timedelta(days=WINDOW_DAYS)
    out = {"d_fav_recent": 0.0, "r_fav_recent": 0.0, "d_fav_prior": 0.0, "r_fav_prior": 0.0, "rows_recent": 0, "rows_dated_by_dissemination": 0}
    for r in rows:
        if r.get("can_office") != "S" or r.get("can_office_state") != state:
            continue
        if (r.get("ele_type") or "G")[:1] not in ("G", "S"):
            continue
        side = favored_side(r.get("cand_pty_aff", ""), r.get("sup_opp", ""))
        if side is None:
            continue
        d = fec_date(r.get("exp_date", ""))
        by_dissem = d is None
        if by_dissem:
            d = fec_date(r.get("dissem_dt", ""))
        if d is None or d > window_end:
            continue
        try:
            amt = float(r.get("exp_amo") or 0)
        except ValueError:
            continue
        if recent_start < d <= window_end:
            out[f"{side.lower()}_fav_recent"] += amt
            out["rows_recent"] += 1
            out["rows_dated_by_dissemination"] += int(by_dissem)
        elif prior_start < d <= recent_start:
            out[f"{side.lower()}_fav_prior"] += amt
    return out


def pres2024_margins(path: Path) -> dict[str, float]:
    import pandas as pd
    df = pd.read_excel(path, sheet_name=0, header=0)
    out = {}
    for _, r in df.iterrows():
        st = str(r["STATE"]).strip()
        total = num(r.get("TOTAL VOTES"))
        if len(st) != 2 or not total:
            continue
        out[st] = round(100 * ((num(r.get("HARRIS")) or 0) - (num(r.get("TRUMP")) or 0)) / total, 4)
    return out


def pres2020_margins(path: Path) -> dict[str, float]:
    import pandas as pd
    df = pd.read_excel(path, sheet_name="3. Table 2 Electoral & Pop Vote", header=None).iloc[4:]
    out = {}
    for _, r in df.iterrows():
        st = str(r[0]).strip()
        total = num(r[6])
        if len(st) == 2 and total and num(r[3]) is not None:
            out[st] = round(100 * (num(r[3]) - (num(r[4]) or 0)) / total, 4)
    return out


def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def history_rows(path: Path, pres2020: dict[str, float], sha: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("exclusion") or r.get("year") not in ("2020", "2022") or r.get("state") not in pres2020:
                continue
            p, y, s = num(r.get("baseline")), num(r.get("margin_actual")), num(r.get("log_recent_spend_m"))
            if None in (p, y, s):
                continue
            rows.append({"year": r["year"], "state": r["state"], "poll_margin": f"{p:.4f}", "result_margin": f"{y:.4f}", "log_recent_spend_m": f"{s:.6f}",
                         "pres_year": "2020", "pres_d_minus_r": f"{pres2020[r['state']]:.4f}", "source_sha256": sha})
    return sorted(rows, key=lambda r: (r["year"], r["state"]))


def state_of(race: str) -> str:
    return race.split("-")[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args(argv)
    src = Path(a.sources)
    paths = {k: src / v for k, v in SOURCES.items()}
    for k, p in paths.items():
        if not p.is_file() or p.stat().st_size == 0:
            raise SystemExit(f"missing source {k}: {p}")
    sha = {k: weight.sha256_file(str(p)) for k, p in paths.items()}
    with open(Path(a.bundle_dir) / "run-state.json", encoding="utf-8") as f:
        cutoff = weight.parse_as_of(json.load(f)["analytical_as_of"]).date()
    with open(paths["ie"], newline="", encoding="latin-1") as f:
        if not f.readline().startswith("cand_id,"):
            raise SystemExit("FEC file does not start with the Schedule E header (a blocked download returns HTML)")
        f.seek(0)
        ie = latest_amendments(list(csv.DictReader(f)))
    pres24 = pres2024_margins(paths["pres2024"])
    pres20 = pres2020_margins(paths["pres2020"])
    spending, fundamentals = [], []
    for race in weight.SENATE_RACES + weight.GOVERNOR_RACES:
        st = state_of(race)
        if st not in pres24:
            raise SystemExit(f"2024 presidential margin missing for {st}")
        fundamentals.append({"race": race, "state": st, "pres_year": "2024", "pres_d_minus_r": f"{pres24[st]:.4f}",
                             "source_file": SOURCES["pres2024"], "source_sha256": sha["pres2024"]})
        if race in weight.GOVERNOR_RACES:
            spending.append({"race": race, "state": st, "fec_coverage": "NOT_FEDERAL", "window_end": cutoff.isoformat(),
                             **{k: "NA" for k in SPENDING_HEADER[4:10]}, "source_file": "NA", "source_sha256": "NA"})
            continue
        agg = aggregate_spending(ie, st, cutoff)
        spending.append({"race": race, "state": st, "fec_coverage": "FEC_SCHEDULE_E", "window_end": cutoff.isoformat(),
                         **{k: (f"{v:.2f}" if isinstance(v, float) else str(v)) for k, v in agg.items()},
                         "source_file": SOURCES["ie"], "source_sha256": sha["ie"]})
    history = history_rows(paths["history"], pres20, sha["history"])
    if len(history) < 30:
        raise SystemExit(f"spending history too thin: {len(history)} races")
    for name, header, rows in (("spending.csv", SPENDING_HEADER, spending), ("fundamentals.csv", FUNDAMENTALS_HEADER, fundamentals),
                               ("spend-history.csv", HISTORY_HEADER, history)):
        path = os.path.join(a.bundle_dir, name)
        snap = weight.snapshot(path, a.bundle_dir)
        weight.write_csv(path, header, rows)
        print(f"wrote {name}: {len(rows)} rows" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
