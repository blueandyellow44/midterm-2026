#!/usr/bin/env python3
"""Cook-band check for the seat projection (Max, 2026-10-27: "are you sure this is the best way?" -> test first).
For every seat up in 2026, the plain projection = 2024 presidential margin on the seat's lines + (generic ballot - 2024
national presidential margin). Do Cook's bands land where they should? Reports, per rating, the median projected margin,
the range, and how many seats project on the wrong side of even, with the names of the misfits.

Usage: python3 scripts/cook_band_check.py --generic <D minus R> --national2024 <D minus R> [--bonus <pts per incumbent>]
"""
from __future__ import annotations

import argparse
import csv
import statistics as st
from pathlib import Path

SEATS = Path("/Users/maxsheahan/Second Brain V2/Resources/methods/midterm-2026/seats.csv")
ORDER = ("Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generic", type=float, required=True)
    ap.add_argument("--national2024", type=float, required=True)
    ap.add_argument("--bonus", type=float, default=0.0, help="incumbency bonus, points toward the holder's party (0 = none)")
    a = ap.parse_args()
    shift = a.generic - a.national2024
    print(f"shift = generic {a.generic:+.2f} - 2024 national {a.national2024:+.2f} = {shift:+.2f} toward D; incumbency bonus {a.bonus:+.2f}")
    rows = [r for r in csv.DictReader(open(SEATS)) if r["up_2026"] == "1"]
    for chamber in ("SEN", "GOV", "HOUSE"):
        print(f"\n== {chamber}")
        for rating in ORDER:
            sub = [r for r in rows if r["chamber"] == chamber and r["cook_rating"] == rating]
            if not sub:
                continue
            proj = []
            for r in sub:
                v = float(r["pres2024_d_minus_r"]) + shift + a.bonus * {"D": 1, "R": -1}.get(r["holder_party"], 0)
                proj.append((v, r))
            vals = [v for v, _ in proj]
            want = 1 if rating.endswith("D") else -1 if rating.endswith("R") else 0
            wrong = [(v, r) for v, r in proj if want and v * want < 0]
            within3 = sum(1 for v in vals if abs(v) < 3)
            names = ", ".join(f"{r['seat'].replace('2026-', '').replace('-HOUSE', '')} {v:+.1f}" for v, r in sorted(wrong, key=lambda x: x[0]))
            print(f"  {rating:9s} n={len(sub):3d}  median {st.median(vals):+6.1f}  range [{min(vals):+.1f}, {max(vals):+.1f}]  within 3 of even: {within3:3d}"
                  + (f"  WRONG SIDE {len(wrong)}: {names}" if wrong else ""))
        # Seat totals at the plain projection.
        up = [r for r in rows if r["chamber"] == chamber]
        d = sum(1 for r in up if float(r["pres2024_d_minus_r"]) + shift + a.bonus * {"D": 1, "R": -1}.get(r["holder_party"], 0) > 0)
        print(f"  plain projection of seats up: D {d} / R {len(up) - d} of {len(up)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
