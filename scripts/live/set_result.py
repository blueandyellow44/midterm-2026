#!/usr/bin/env python3
"""Record one race's unofficial count in live/results.json for the election-night scoreboard.

Usage: python3 scripts/live/set_result.py tx-sen --d 50.4 --r 48.1 --other 1.5 --reporting 87 --source https://... [--called D|R]
Shares are percent of ALL votes cast for the office (the full ballot), so --d + --r + --other must total 100 (within 1.5).
The polls number is on that same full-ballot basis; two-party shares would inflate the margin (Codex audit 2026-10-27).
Maine and Alaska are entered from the FIRST-round count (--round FIRST), the same basis as their polling averages.
Refuses impossible inputs. Snapshot of the prior file goes to live/.backups/ (nothing is ever unrecoverable).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "live/results.json"
SLUGS = {"tx-sen", "ia-sen", "me-sen", "ak-sen", "oh-sen-special", "mi-sen", "nc-sen", "ga-sen", "oh-gov", "ia-gov", "mi-gov", "ga-gov", "wi-gov"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--d", type=float, required=True)
    ap.add_argument("--r", type=float, required=True)
    ap.add_argument("--reporting", type=float, required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--other", type=float, required=True, help="percent for every other candidate, write-ins included")
    ap.add_argument("--round", choices=["NA", "FIRST"], default="NA")
    ap.add_argument("--called", choices=["D", "R"])
    a = ap.parse_args(argv)
    if a.slug not in SLUGS:
        raise SystemExit(f"unknown race {a.slug}; one of {sorted(SLUGS)}")
    for name, v in (("d", a.d), ("r", a.r), ("reporting", a.reporting)):
        if not 0 <= v <= 100:
            raise SystemExit(f"--{name} must be between 0 and 100")
    if not 0 <= a.other <= 100 or abs(a.d + a.r + a.other - 100) > 1.5:
        raise SystemExit("--d + --r + --other must total 100 (full-ballot shares); got %.1f" % (a.d + a.r + a.other))
    rcv = a.slug in ("me-sen", "ak-sen")
    if rcv and a.round != "FIRST":
        raise SystemExit(f"{a.slug} is ranked-choice: enter the first-round count with --round FIRST")
    if not rcv and a.round != "NA":
        raise SystemExit(f"{a.slug} is not ranked-choice: --round must be NA")
    if not a.source.startswith("https://"):
        raise SystemExit("--source must be an https URL to the official results page")
    data = json.loads(PATH.read_text())
    (ROOT / "live/.backups").mkdir(exist_ok=True)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    shutil.copy(PATH, ROOT / "live/.backups" / f"results.{now.replace(':', '')}.json")
    data["races"][a.slug] = {"d_pct": a.d, "r_pct": a.r, "other_pct": a.other, "round": a.round, "basis": "full_ballot", "reporting_pct": a.reporting, "called": a.called, "source": a.source, "updated_at": now}
    data["updated_at"] = now
    PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{a.slug}: D {a.d} R {a.r}, {a.reporting}% reporting{', called ' + a.called if a.called else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
