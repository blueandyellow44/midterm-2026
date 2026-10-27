#!/usr/bin/env python3
"""Write house-races.csv to the bundle from the verified competitive-House list (sources/house-*/races.json): Cook rating,
incumbent, nominees, and the district's 2024 presidential margin on current lines. Aggregation only.

Usage: python3 scripts/build_house_races.py --source sources/house-20261027/races.json [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import json
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
    races = json.load(open(a.source, encoding="utf-8"))
    sha = weight.sha256_file(a.source)
    ids = {r["race"] for r in races}
    if ids != set(weight.HOUSE_RACES):
        raise SystemExit(f"race list differs from analysis/house_races.json: {sorted(ids ^ set(weight.HOUSE_RACES))}")
    rows = []
    for r in races:
        inc = r["incumbent"]
        if None in (r.get("pres2024_d_minus_r"), r["D"].get("candidate"), r["R"].get("candidate")):
            raise SystemExit(f"incomplete race record: {r['race']}")
        rows.append({"race": r["race"], "state": r["state"], "district": str(r["district"]), "cook_rating": r["cook_rating"], "cook_rating_date": r["cook_rating_date"],
                     "incumbent": "OPEN" if inc == "OPEN" else inc["name"], "incumbent_party": "NA" if inc == "OPEN" else inc["party"],
                     "d_candidate": r["D"]["candidate"], "d_party": r["D"]["party"], "r_candidate": r["R"]["candidate"], "r_party": r["R"]["party"],
                     "pres2024_d_minus_r": f"{float(r['pres2024_d_minus_r']):.2f}", "lines_note": (r.get("lines_note") or "NA").replace("\n", " "), "source_sha256": sha})
    rows.sort(key=lambda x: x["race"])
    path = os.path.join(a.bundle_dir, "house-races.csv")
    snap = weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.HOUSE_RACES_HEADER, rows)
    print(f"wrote house-races.csv: {len(rows)} rows" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
