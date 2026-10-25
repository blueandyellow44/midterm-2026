#!/usr/bin/env python3
"""Section 11 coverage ledger: per race, the sources checked, rows found, verified on primary, and exclusions by reason.

Usage: python3 scripts/coverage_ledger.py --inputs <agent json dir> [--inputs ...] --polls <bundle polls.csv> --out <ledger.md>
Formatting only: counts come from the agents' source logs and from polls.csv as written by weight.py --derive.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
import weight  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", action="append", required=True)
    ap.add_argument("--polls", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    polls = weight.read_csv(a.polls, weight.POLLS_HEADER)
    by_race = defaultdict(list)
    for r in polls:
        by_race[r["race"]].append(r)
    lines = ["Inventory from the union of RealClearPolling, 270toWin and primary releases (Wikipedia and FiftyPlusOne used as finding aids, never as the verification source), with field dates, n, population and toplines confirmed on the primary release where it was reachable. Not every public poll.", ""]
    lines.append("| Race | Sources checked | Stored rows | Selected | BOTH / HOUSE_ONLY (stored) | Aggregator-only rows | Excluded by reason | Blocked or unreachable |")
    lines.append("|---|---|---|---|---|---|---|---|")
    gaps_all = []
    for path in sorted(p for d in a.inputs for p in glob.glob(os.path.join(d, "*.json"))):
        with open(path) as f:
            d = json.load(f)
        race = d.get("race")
        if not isinstance(race, str) or race not in weight.IN_SCOPE_RACES:
            race = os.path.basename(path)[:-5]
        rows = by_race.get(race, [])
        src = d.get("sources_checked") or []
        names = sorted({(s.get("name") or "")[:40] for s in src if s.get("name")})
        blocked = sorted({(s.get("name") or s.get("url") or "")[:40] for s in src if any(k in str(s.get("result", "")).lower() for k in ("403", "429", "blocked", "timeout", "unreach", "failed", "404"))})
        agg_only = sum(1 for r in rows if "aggregator-only" in r["notes"])
        excl = Counter(r["exclusion_reason"] for r in rows if r["selected"] == "0")
        win = Counter(r["window"] for r in rows)
        lines.append(f"| {race} | {len(src)} ({', '.join(names)[:160]}) | {len(rows)} | {sum(1 for r in rows if r['selected'] == '1')} | {win.get('BOTH', 0)} / {win.get('HOUSE_ONLY', 0)} | {agg_only} | {', '.join(f'{k} {v}' for k, v in sorted(excl.items())) or 'none'} | {', '.join(blocked) or 'none'} |")
        for g in d.get("gaps") or []:
            gaps_all.append(f"- **{race}**: {g}")
    lines += ["", "### Gaps recorded by the research pass (verbatim from the per-race logs)", ""] + gaps_all
    lines += ["", "### 2022 comparators for Section 6 (certified November 2022 general results, D minus R, percentage points)", "",
              "| State | Governor | Senate | Gap | Source |", "|---|---|---|---|---|",
              "| GA | Kemp (R) 53.41, Abrams (D) 45.88: D margin −7.53 | Nov 8 general: Warnock (D) 49.44, Walker (R) 48.49: D margin +0.95 (runoff Dec 6: 51.40 to 48.60) | −8.48 | [2022 Georgia gubernatorial election](https://en.wikipedia.org/wiki/2022_Georgia_gubernatorial_election), [2022 U.S. Senate election in Georgia](https://en.wikipedia.org/wiki/2022_United_States_Senate_election_in_Georgia), read 2026-10-25 |",
              "| OH | DeWine (R) 62.41, Whaley (D) 37.38: D margin −25.03 | Vance (R) 53.03, Ryan (D) 46.92: D margin −6.11 | −18.92 | [2022 Ohio gubernatorial election](https://en.wikipedia.org/wiki/2022_Ohio_gubernatorial_election), [2022 U.S. Senate election in Ohio](https://en.wikipedia.org/wiki/2022_United_States_Senate_election_in_Ohio), read 2026-10-25 |",
              "| NH | Sununu (R) 56.98, Sherman (D) 41.47: D margin −15.51 | Hassan (D) 53.54, Bolduc (R) 44.39: D margin +9.15 | −24.66 | [2022 New Hampshire gubernatorial election](https://en.wikipedia.org/wiki/2022_New_Hampshire_gubernatorial_election), [2022 U.S. Senate election in New Hampshire](https://en.wikipedia.org/wiki/2022_United_States_Senate_election_in_New_Hampshire), read 2026-10-25 |",
              "| NV | Lombardo (R) 48.81, Sisolak (D) 47.30: D margin −1.51 | Cortez Masto (D) 48.81, Laxalt (R) 48.04: D margin +0.77 | −2.28 | [2022 Nevada gubernatorial election](https://en.wikipedia.org/wiki/2022_Nevada_gubernatorial_election), [2022 U.S. Senate election in Nevada](https://en.wikipedia.org/wiki/2022_United_States_Senate_election_in_Nevada), read 2026-10-25 |",
              "", "Certified-result percentages as reported on the linked pages (infobox and results tables), read 2026-10-25; illustration only, not a benchmark."]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"ledger -> {a.out}: {len(by_race)} races, {len(gaps_all)} gap lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
