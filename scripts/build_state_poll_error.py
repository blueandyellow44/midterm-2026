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
    df = df[df.type_simple.isin(RACE_TYPES) & (df.year % 2 == 0) & (df.location.astype(str).str.len() == 2)].copy()
    df["days"] = (pd.to_datetime(df.electiondate) - pd.to_datetime(df.polldate)).dt.days
    df = df[(df.days >= 0) & (df.days <= FINAL_DAYS)].dropna(subset=["bias"])
    race = df.groupby(["year", "location", "race"]).bias.mean().reset_index()
    sc = race.groupby(["year", "location"]).bias.agg(["mean", "size"]).reset_index()
    sha = weight.sha256_file(source)
    return [{"year": str(int(r.year)), "state": r.location, "state_bias": f"{r["mean"]:.4f}", "n_races": str(int(r["size"])),
             "source_sha256": sha} for _, r in sc.sort_values(["year", "location"]).iterrows()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args(argv)
    if not os.path.isfile(a.source):
        raise SystemExit(f"missing source: {a.source}")
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
