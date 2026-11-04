#!/usr/bin/env python3
"""Record one AP call in live/calls.json for the election-night ballot's Standings tab.

Usage: python3 scripts/live/set_call.py 2026-NH-SEN --winner D --source https://apnews.com/...
For ballot races with no official count to enter in live/results.json (NH, ME, WI, the untracked governors, MN Senate,
Senate and House control). /ballot/ ONLY: never feeds the grade, the dial, the scoreboard or analysis/.
Ids are ballot race ids (lib/ballot.ts): 2026-<STATE>-SEN|GOV[-SPECIAL], SENATE-CONTROL, HOUSE-CONTROL.
Refuses an id not on the ballot, a non-https source, and a winner that contradicts a call already in live/results.json.
Snapshot of the prior file goes to live/.backups/ (nothing is ever unrecoverable).
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "live/calls.json"
# Same rule as ballotRaces() in lib/ballot.ts; tests/ballot.test.ts checks the two lists agree.
BALLOT_RATINGS = {"Toss-up", "Lean D", "Lean R", "Likely D", "Likely R"}
CONTROL = ["SENATE-CONTROL", "HOUSE-CONTROL"]
slug_of = lambda race: race.replace("2026-", "").lower()


def ballot_ids(seats=ROOT / "data/seats.csv") -> list[str]:
    if not seats.exists():
        return []
    rows = csv.DictReader(seats.open())
    return CONTROL + [s["seat"] for s in rows if s["up_2026"] == "1" and s["cook_rating"] in BALLOT_RATINGS and s["chamber"] in ("SEN", "GOV")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("race", nargs="?")
    ap.add_argument("--winner", choices=["D", "R"])
    ap.add_argument("--source")
    ap.add_argument("--list", action="store_true", help="print the ballot race ids and exit")
    a = ap.parse_args(argv)
    ids = ballot_ids()
    if a.list:
        print(json.dumps(ids)); return 0
    if not a.race or not a.winner or not a.source:
        raise SystemExit("need a ballot race id, --winner D|R and --source")
    if a.race not in ids:
        raise SystemExit(f"unknown ballot race {a.race}; one of {sorted(ids)}")
    if not a.source.startswith("https://"):
        raise SystemExit("--source must be an https URL to the AP call")
    called = (json.loads((ROOT / "live/results.json").read_text())["races"].get(slug_of(a.race)) or {}).get("called")
    if called and called != a.winner:
        raise SystemExit(f"{a.race} is already called {called} in live/results.json; fix that file, not this one")
    data = json.loads(PATH.read_text())
    (ROOT / "live/.backups").mkdir(exist_ok=True)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    shutil.copy(PATH, ROOT / "live/.backups" / f"calls.{now.replace(':', '')}.json")
    data["calls"][a.race] = {"winner": a.winner, "called_at": now, "source": a.source}
    PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{a.race}: called {a.winner} ({len(data['calls'])} hand calls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
