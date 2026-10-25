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
        agg_only = sum(1 for r in rows if r["primary_verified"] != "YES")
        excl = Counter(r["exclusion_reason"] for r in rows if r["selected"] == "0")
        win = Counter(r["window"] for r in rows)
        lines.append(f"| {race} | {len(src)} ({', '.join(names)[:160]}) | {len(rows)} | {sum(1 for r in rows if r['selected'] == '1')} | {win.get('BOTH', 0)} / {win.get('HOUSE_ONLY', 0)} | {agg_only} | {', '.join(f'{k} {v}' for k, v in sorted(excl.items())) or 'none'} | {', '.join(blocked) or 'none'} |")
        for g in d.get("gaps") or []:
            gaps_all.append(f"- **{race}**: {g}")
    lines += ["", "### Gaps recorded by the research pass (verbatim from the per-race logs)", ""] + gaps_all
    lines += ["", "2022 certified-result comparators are computed from reviewed primary returns in weight.py and rendered in Section 6. No secondary-source percentages are injected by this ledger."]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"ledger -> {a.out}: {len(by_race)} races, {len(gaps_all)} gap lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
