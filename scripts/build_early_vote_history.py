#!/usr/bin/env python3
"""Write early-vote-history.csv to the bundle from the collected McDonald / UF Election Lab early vote by party
(sources/early-vote-history-*/early-vote-by-party.csv). Aggregation only; weight.py fits the early-vote term.

Usage: python3 scripts/build_early_vote_history.py --source sources/early-vote-history-20261027/early-vote-by-party.csv [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args(argv)
    sha = weight.sha256_file(a.source)
    rows = []
    with open(a.source, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d, rep, tot = weight.num(r.get("dem_share")), weight.num(r.get("rep_share")), weight.num(r.get("total_ballots"))
            if None in (d, rep, tot):
                raise SystemExit(f"incomplete early-vote row: {r.get('year')} {r.get('state')}")
            rows.append({"year": r["year"], "state": r["state"], "dem_share": f"{d:.2f}", "rep_share": f"{rep:.2f}", "total_ballots": str(int(tot)),
                         "as_of": r["as_of"], "source_sha256": sha})
    rows.sort(key=lambda r: (r["year"], r["state"]))
    path = os.path.join(a.bundle_dir, "early-vote-history.csv")
    snap = weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.EARLY_VOTE_HISTORY_HEADER, rows)
    print(f"wrote early-vote-history.csv: {len(rows)} rows" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
