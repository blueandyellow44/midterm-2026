#!/usr/bin/env python3
"""Reclassify the sponsor class of rows already in polls.csv, from an explicit list (no fuzzy matching), then re-derive and
validate the whole bundle before anything is written. Same write path as merge_poll_records.py.

Rulings applied (Max, 2026-11-01, by question, recorded in the hub):
  1. YouGov's state "ttw" series (no sponsor named in the PDFs) is a firm polling on its own: NONPARTISAN (weight 1.0).
  2. A poll paid by a PAC or super PAC that spends for a candidate or party in that race is an internal (INTERNAL, 0.3);
     a group with no spending in the race is a partisan sponsor (PARTISAN_PUBLIC, 0.6). Spending is read from the FEC
     independent-expenditure file the spending signal already uses (sources/signals-20261027/ie2026.csv), general
     election only.

Usage: python3 scripts/reclassify_sponsors.py [--bundle-dir <vault bundle>] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402

# (estimate_id prefix, race, new class, reason). Every prefix must match at least one row in that race, or nothing is written.
CHANGES = [
    # 1. YouGov ttw series, previously UNKNOWN
    ("yougov-2026-10-06-2026-10-12-2026-IA-SEN", "2026-IA-SEN", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-10-06-2026-10-12-2026-IA-GOV", "2026-IA-GOV", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-22-2026-10-04-2026-MI-SEN", "2026-MI-SEN", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-22-2026-10-04-2026-MI-GOV", "2026-MI-GOV", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-18-2026-09-30-2026-OH-SEN-SPECIAL", "2026-OH-SEN-SPECIAL", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-18-2026-09-30-2026-OH-GOV", "2026-OH-GOV", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-02-2026-09-08-2026-ME-SEN", "2026-ME-SEN", "NONPARTISAN", "YouGov ttw series"),
    ("yougov-2026-09-15-2026-09-18-unknown-2026-NC-SEN", "2026-NC-SEN", "NONPARTISAN", "YouGov ttw series"),
    # 2. PACs that spend in the race (general-election IEs in ie2026.csv): internal
    ("public-policy-polling-2026-10-19-2026-10-20-house-majority-p", "2026-CO-05-HOUSE", "INTERNAL", "HMP spends in CO-05"),
    ("public-policy-polling-2026-10-21-2026-10-22-house-majority-p", "2026-FL-25-HOUSE", "INTERNAL", "HMP spends in FL-25"),
    ("lake-research-partners-2026-09-30-2026-10-04-house-majority-", "2026-KY-06-HOUSE", "INTERNAL", "HMP spends in KY-06"),
    ("public-policy-polling-2026-10-19-2026-10-20-house-majority-p", "2026-KY-06-HOUSE", "INTERNAL", "HMP spends in KY-06"),
    ("public-policy-polling-2026-10-21-2026-10-22-house-majority-p", "2026-SC-01-HOUSE", "INTERNAL", "HMP spends in SC-01"),
    ("normington-petts-2026-09-24-2026-09-28-house-majority-pac-de", "2026-TX-15-HOUSE", "INTERNAL", "HMP spends in TX-15"),
    ("public-policy-polling-2026-10-21-2026-10-22-house-majority-p", "2026-VA-01-HOUSE", "INTERNAL", "HMP spends in VA-01"),
    ("impact-research-2026-09-28-2026-10-01-house-majority-pac-dem", "2026-WI-01-HOUSE", "INTERNAL", "HMP spends in WI-01"),
    ("torchlight-2026-09-15-2026-09-19-common-sense-for-america-20", "2026-MI-SEN", "INTERNAL", "Common Sense for America PAC spends for Rogers"),
    ("change-research-2026-09-29-2026-10-05-kentuckians-not-corrup", "2026-KY-06-HOUSE", "INTERNAL", "Kentuckians Not Corruption spends for Dembo"),
    ("coefficient-2026-09-30-2026-10-01-thank-you-for-your-attenti", "2026-SC-01-HOUSE", "INTERNAL", "Thank You ... PAC spends against LaCore"),
    # 2. PACs with no spending in the race: partisan sponsor
    ("tulchin-research-2026-08-24-2026-08-31-house-majority-pac-20", "2026-AL-02-HOUSE", "PARTISAN_PUBLIC", "HMP has no IE in AL-02"),
    ("tulchin-research-2026-09-08-2026-09-13-house-majority-pac-pe", "2026-FL-27-HOUSE", "PARTISAN_PUBLIC", "HMP has no IE in FL-27 (already 0.6)"),
    ("gbao-2026-09-18-2026-09-21-house-majority-pac-2026-MN-01-HOU", "2026-MN-01-HOUSE", "PARTISAN_PUBLIC", "HMP has no IE in MN-01 (already 0.6)"),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    bundle = Path(a.bundle_dir)
    state = json.loads((bundle / "run-state.json").read_text())
    cutoff = weight.parse_as_of(state["analytical_as_of"])
    polls = weight.read_csv(str(bundle / "polls.csv"), weight.POLLS_HEADER)
    changed = []
    for prefix, race, cls, why in CHANGES:
        hit = [r for r in polls if r["estimate_id"].startswith(prefix) and r["race"] == race]
        if not hit:
            raise weight.ValidationError(f"no row for {prefix} in {race}")
        for r in hit:
            if r["sponsor_class"] != cls:
                changed.append((r["estimate_id"], r["sponsor_class"], cls, why))
                r["sponsor_class"] = cls
    with tempfile.TemporaryDirectory(prefix="midterm-reclass-") as temp:
        for name in ("heat.csv", "coverage.csv", "exclusions.csv", "run-state.json", "pollsters.csv"):
            shutil.copy2(bundle / name, Path(temp) / name)
        weight.write_csv(str(Path(temp) / "polls.csv"), weight.POLLS_HEADER, polls)
        b = weight.Bundle(temp, cutoff, state)
        derived = b.derive_rows(b.polls)
        weight.write_csv(str(Path(temp) / "polls.csv"), weight.POLLS_HEADER, derived)
        b = weight.Bundle(temp, cutoff, state)
        if not b.validate():
            raise weight.ValidationError("\n".join(b.problems))
        if not a.dry_run:
            weight.snapshot(str(bundle / "polls.csv"), str(bundle))
            shutil.copy2(Path(temp) / "polls.csv", bundle / "polls.csv")
    for c in changed:
        print(" | ".join(c))
    print(json.dumps({"rows_changed": len(changed), "validation": "passed", "written": not a.dry_run}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, weight.ValidationError) as exc:
        print(f"NOT WRITTEN: {exc}", file=sys.stderr)
        sys.exit(1)
