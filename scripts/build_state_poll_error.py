#!/usr/bin/env python3
"""Build state-poll-error.csv: per state and even-year cycle, the mean signed polling bias of its statewide general races.

Aggregation only, no estimation: weight.py turns these rows into each state's lean (state_poll_error_leans).
Source: the 538 pollster-ratings raw polls archive. Bias is 538's: poll margin minus actual margin, positive = polls
overstated Democrats. Polls in the final 21 days of President, Senate and Governor generals; a race's bias is the mean
over its polls, a state-cycle's bias the mean over its races.

Usage: python3 scripts/build_state_poll_error.py --source sources/state-poll-error-20261026/rawpolls-011226.xlsx [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402

RACE_TYPES = ("Pres-G", "Sen-G", "Gov-G")
FINAL_DAYS = 21


def build(source: str) -> list[dict]:
    import pandas as pd
    df = pd.read_excel(source)
    need = {"year", "location", "race", "type_simple", "polldate", "electiondate", "bias"}
    if not need <= set(df.columns):
        raise SystemExit(f"raw polls archive missing columns: {sorted(need - set(df.columns))}")
    df = df[df.type_simple.isin(RACE_TYPES) & (df.year % 2 == 0) & (df.location.astype(str).str.len() == 2) & (df.location != "US")].copy()
    df["days"] = (pd.to_datetime(df.electiondate) - pd.to_datetime(df.polldate)).dt.days
    df = df[(df.days >= 0) & (df.days <= FINAL_DAYS)].dropna(subset=["bias"])
    race = df.groupby(["year", "location", "race"]).bias.mean().reset_index()
    sc = race.groupby(["year", "location"]).bias.agg(["mean", "size"]).reset_index()
    sha = weight.sha256_file(source)
    return [{"year": str(int(r.year)), "state": r.location, "state_bias": f"{r["mean"]:.4f}", "n_races": str(int(r["size"])),
             "source_sha256": sha} for _, r in sc.sort_values(["year", "location"]).iterrows()]


def race_history(source: str) -> list[dict]:
    """Race-level rows: every statewide or national general in the archive, final 21 days. weight.py derives the national
    carryover, the state leans and the backtest from these rows."""
    import pandas as pd
    df = pd.read_excel(source)
    df = df[df.type_simple.isin(RACE_TYPES)].copy()
    df["days"] = (pd.to_datetime(df.electiondate) - pd.to_datetime(df.polldate)).dt.days
    df = df[(df.days >= 0) & (df.days <= FINAL_DAYS)].dropna(subset=["bias", "margin_poll", "margin_actual"])
    g = df.groupby(["year", "location", "race", "type_simple"]).agg(n=("bias", "size"), poll=("margin_poll", "mean"), actual=("margin_actual", "first"), bias=("bias", "mean")).reset_index()
    sha = weight.sha256_file(source)
    return [{"year": str(int(r.year)), "state": str(r.location), "race": str(r.race), "type": r.type_simple, "n_polls": str(int(r.n)),
             "poll_margin": f"{r.poll:.4f}", "actual_margin": f"{r.actual:.4f}", "bias": f"{r.bias:.4f}", "source_sha256": sha}
            for r in g.sort_values(["year", "location", "race"]).itertuples()]


def carryover(source: str) -> dict:
    """National carryover: share of an off-year mean miss that repeats in the next even year (no-intercept fit)."""
    import pandas as pd
    import math
    df = pd.read_excel(source)
    df = df[df.type_simple.isin(RACE_TYPES)].copy()
    df["days"] = (pd.to_datetime(df.electiondate) - pd.to_datetime(df.polldate)).dt.days
    df = df[(df.days >= 0) & (df.days <= FINAL_DAYS)].dropna(subset=["bias"])
    yr = df.groupby(["year", "race"]).bias.mean().groupby("year").mean()
    pairs = [(-yr[y], -yr[y + 1]) for y in range(1999, 2025, 2) if y in yr.index and y + 1 in yr.index]
    sxx = sum(a * a for a, _ in pairs)
    k = sum(a * b for a, b in pairs) / sxx
    s = math.sqrt(sum((b - k * a) ** 2 for a, b in pairs) / (len(pairs) - 1))
    return {"pairs": [(round(a, 3), round(b, 3)) for a, b in pairs], "n": len(pairs), "share": k, "se": s / math.sqrt(sxx)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--carryover", action="store_true", help="print the national off-year carryover fit and exit")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.source):
        raise SystemExit(f"missing source: {a.source}")
    if a.carryover:
        print(carryover(a.source))
        return 0
    hist = race_history(a.source)
    hpath = os.path.join(a.bundle_dir, "poll-error-history.csv")
    hsnap = weight.snapshot(hpath, a.bundle_dir)
    weight.write_csv(hpath, weight.POLL_ERROR_HISTORY_HEADER, hist)
    print(f"wrote poll-error-history.csv: {len(hist)} races" + (f" (snapshot {hsnap})" if hsnap else ""))
    rows = build(a.source)
    if len({r["year"] for r in rows}) < 8:
        raise SystemExit(f"state polling history too thin: {len(rows)} rows")
    path = os.path.join(a.bundle_dir, "state-poll-error.csv")
    snap = weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.STATE_POLL_ERROR_HEADER, rows)
    print(f"wrote state-poll-error.csv: {len(rows)} rows" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
