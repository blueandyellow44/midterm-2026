#!/usr/bin/env python3
"""Write seats.csv to the bundle: every seat in the three chambers Undertow projects (Max, 2026-10-27: "100 senate seats,
50 governors, and a bunch of house districts" -> "Yes"). Aggregation only; weight.py owns every projected number.

One row per seat: the 65 Senate seats not up and the 35 up (33 regular + OH and FL specials), the 14 governors not up and
the 36 up, all 435 House districts on the 2026 lines. Each row carries the holder's party (caucus for Senate), Cook's
rating where the seat is up, and the 2024 presidential margin on the seat's lines (state for Senate and governor, district
for House), plus whether Undertow tracks the race.

Sources (all free, cross-checked by the collecting agents on 2026-10-27):
  sources/chambers-20261027/chambers.json   seats not up, every 2026 race's Cook rating, all 435 House ratings
  sources/house-all-20261027/districts.csv   2024 presidential margin per district on 2026 lines, current member
  sources/signals-20261027/2024presgeresults.xlsx   FEC official 2024 presidential results by state

Usage: python3 scripts/build_chambers.py [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import weight  # noqa: E402
from build_signals import pres2024_margins  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHAMBERS = ROOT / "sources/chambers-20261027/chambers.json"
DISTRICTS = ROOT / "sources/house-all-20261027/districts.csv"
PRES2024 = ROOT / "sources/signals-20261027/2024presgeresults.xlsx"
INCUMBENTS = ROOT / "sources/incumbents-20261027/incumbents.csv"   # optional: is the holder on the November ballot (YES/NO/VACANT/UNKNOWN)
RATINGS = ("Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R")
STATE_ABBR = {"Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
              "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY",
              "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
              "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
              "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
              "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
              "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"}


def senate_race_id(abbr: str, special: bool) -> str:
    return f"2026-{abbr}-SEN" + ("-SPECIAL" if special else "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args(argv)
    for p in (CHAMBERS, DISTRICTS, PRES2024):
        if not p.is_file() or p.stat().st_size == 0:
            raise SystemExit(f"missing source: {p}")
    ch = json.load(open(CHAMBERS, encoding="utf-8"))
    sha_ch, sha_d, sha_p = (weight.sha256_file(str(p)) for p in (CHAMBERS, DISTRICTS, PRES2024))
    pres = pres2024_margins(PRES2024)
    tracked = set(weight.ALL_RACES)
    # incumbent_on_ballot = the PARTY of the incumbent running for the seat (D/R/I), else NONE / VACANT / UNKNOWN. A member a
    # new map moved to another district (reason "redistricted; running in XX-NN") counts in the district on their ballot.
    on_ballot = {}
    if INCUMBENTS.is_file():
        inc = list(csv.DictReader(open(INCUMBENTS, encoding="utf-8")))
        bad = {r["on_ballot"] for r in inc} - {"YES", "NO", "VACANT", "UNKNOWN"}
        if bad:
            raise SystemExit(f"incumbents.csv has unknown on_ballot values: {sorted(bad)}")
        on_ballot = {r["seat"]: (r["incumbent_party"] if r["on_ballot"] == "YES" else "NONE" if r["on_ballot"] == "NO" else r["on_ballot"]) for r in inc}
        for r in inc:
            m = re.search(r"running in ([A-Z]{2})-(\d{2}|AL)", r.get("reason") or "")
            if r["on_ballot"] == "NO" and m:
                dest = f"2026-{m.group(1)}-{m.group(2)}-HOUSE"
                cur = on_ballot.get(dest)
                if cur in ("NONE", "VACANT", None):
                    on_ballot[dest] = r["incumbent_party"]
                elif cur != r["incumbent_party"]:
                    print(f"two incumbents of different parties on one ballot: {dest} has {cur}, {r['incumbent']} ({r['incumbent_party']}) arrives; keeping {cur}")
    rows = []

    def row(chamber, seat, state, district, up, special, holder, rating, rating_date, margin, tracked_race, sha):
        rows.append({"chamber": chamber, "seat": seat, "state": state, "district": district, "up_2026": "1" if up else "0", "special": "1" if special else "0",
                     "holder_party": holder, "incumbent_on_ballot": (on_ballot.get(seat, "UNKNOWN") if up else "NA"), "cook_rating": rating, "cook_rating_date": rating_date, "pres2024_d_minus_r": f"{margin:.4f}",
                     "tracked_race": tracked_race, "source_sha256": sha})

    # Senate: seats not up carry the caucus (the two independents caucus with Democrats), seats up carry Cook's rating.
    for s in ch["senate"]["not_up"]["list"]:
        ab = STATE_ABBR[s["state"]]
        row("SEN", f"SEN-{ab}-{s['class']}", ab, "NA", False, False, s["caucus"], "NA", "NA", pres[ab], "NA", sha_ch)
    for r in ch["senate"]["races"]:
        ab = r["state_abbr"]; rid = senate_race_id(ab, r["special"])
        row("SEN", rid, ab, "NA", True, r["special"], r["incumbent_party"], r["cook_rating"], r["cook_rating_date"], pres[ab], rid if rid in tracked else "NA", sha_ch)
    for g in ch["governors"]["not_up"]["list"]:
        ab = STATE_ABBR[g["state"]]
        row("GOV", f"GOV-{ab}", ab, "NA", False, False, g["party"], "NA", "NA", pres[ab], "NA", sha_ch)
    for r in ch["governors"]["races"]:
        ab = r["state_abbr"]; rid = f"2026-{ab}-GOV"
        row("GOV", rid, ab, "NA", True, False, r["incumbent_party"], r["cook_rating"], r["cook_rating_date"], pres[ab], rid if rid in tracked else "NA", sha_ch)
    # House: every district, Cook's rating from the decoded 270toWin map (cross-checked 144/144 against Wikipedia).
    rating = {d: k for k, v in ch["house"]["ratings"].items() for d in v}
    vacant = {v["district"]: v["party"] for v in ch["house"]["vacancies"]}
    for d in csv.DictReader(open(DISTRICTS, encoding="utf-8")):
        did = d["district"]; st, num = did.split("-")
        rid = f"2026-{st}-{num}-HOUSE"
        holder = d["incumbent_party"] if d["incumbent_party"] in ("D", "R", "I") else vacant.get(did, "NA")
        if did not in rating:
            raise SystemExit(f"no Cook rating for {did}")
        row("HOUSE", rid, st, num, True, False, holder, rating[did], ch["house"]["cook_rating_date"], float(d["pres2024_d_minus_r"]), rid if rid in tracked else "NA", sha_d)
    # Checks against the chambers the sources describe.
    counts = {c: sum(1 for r in rows if r["chamber"] == c) for c in ("SEN", "GOV", "HOUSE")}
    if counts != {"SEN": 100, "GOV": 50, "HOUSE": 435}:
        raise SystemExit(f"seat counts off: {counts}")
    if any(r["cook_rating"] not in RATINGS for r in rows if r["up_2026"] == "1"):
        raise SystemExit("an up seat has an unknown Cook rating")
    missing = tracked - {r["tracked_race"] for r in rows}
    if missing:
        raise SystemExit(f"tracked races not in the seat list: {sorted(missing)}")
    if on_ballot:
        unknown = [r["seat"] for r in rows if r["up_2026"] == "1" and r["incumbent_on_ballot"] == "UNKNOWN"]
        if unknown:
            print(f"incumbent_on_ballot UNKNOWN for {len(unknown)} seats: {unknown[:12]}{' ...' if len(unknown) > 12 else ''}")
    rows.sort(key=lambda r: (("SEN", "GOV", "HOUSE").index(r["chamber"]), r["state"], r["seat"]))
    path = os.path.join(a.bundle_dir, "seats.csv")
    snap = weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.SEATS_HEADER, rows)
    print(f"wrote seats.csv: {len(rows)} rows ({counts})" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
