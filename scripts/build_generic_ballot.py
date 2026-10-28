#!/usr/bin/env python3
"""Write generic-ballot.csv to the bundle from the collected national generic-congressional-ballot polls
(sources/generic-ballot-*/polls.json). Aggregation only: weight.py computes the average and the swing from it.

Usage: python3 scripts/build_generic_ballot.py --source sources/generic-ballot-20261027/polls.json [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args(argv)
    polls = json.load(open(a.source, encoding="utf-8"))
    if isinstance(polls, dict):
        polls = polls.get("polls") or polls.get("records")
    rows, seen = [], set()
    for p in polls:
        for k in ("pollster", "field_start", "field_end", "D", "R", "pop"):
            if p.get(k) in (None, ""):
                raise SystemExit(f"incomplete poll record: {p}")
        if p["pop"] not in weight.POPS:
            raise SystemExit(f"unknown population {p['pop']} in {p['pollster']} {p['field_end']}")
        pid = f"{slug(p['pollster'])}-{p['field_end']}-{p['pop'].lower()}"
        if pid in seen:
            raise SystemExit(f"duplicate poll: {pid}")
        seen.add(pid)
        rows.append({"poll_id": pid, "pollster": p["pollster"], "sponsor": p.get("sponsor") or "NA", "field_start": p["field_start"], "field_end": p["field_end"],
                     "release_date": p.get("release_date") or "NA", "n": str(int(p["n"])) if p.get("n") else "NA", "pop": p["pop"],
                     "D": f"{float(p['D']):g}", "R": f"{float(p['R']):g}", "other": f"{float(p['other']):g}" if p.get("other") is not None else "NA",
                     "undecided": f"{float(p['undecided']):g}" if p.get("undecided") is not None else "NA",
                     "source_url": p.get("source_url") or "NA", "confirmed_at_source": "YES" if p.get("confirmed_at_source") else "NO",
                     "notes": (p.get("notes") or "NA").replace("\n", " ")})
    if len(rows) < 10:
        raise SystemExit(f"too few generic-ballot polls: {len(rows)}")
    rows.sort(key=lambda r: (r["field_end"], r["poll_id"]))
    path = os.path.join(a.bundle_dir, "generic-ballot.csv")
    snap = weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.GENERIC_BALLOT_HEADER, rows)
    print(f"wrote generic-ballot.csv: {len(rows)} rows" + (f" (snapshot {snap})" if snap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
