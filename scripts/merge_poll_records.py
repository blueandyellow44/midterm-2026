#!/usr/bin/env python3
"""Merge one-file-per-poll research records (sources/polls-*/ and sources/house-polls-*/) into polls.csv and pollsters.csv
without rebuilding the sealed inventory. Same row conventions as the 2026-10-27 Senate additions; weight.py derives windows,
margins and selection, and validates the whole bundle before anything is written. Calculations stay in weight.py.

Usage: python3 scripts/merge_poll_records.py --inputs sources/house-polls-20261027 [--inputs <dir> ...] [--bundle-dir <vault bundle>] [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import weight  # noqa: E402
from build_polls import slug, numstr, enum  # noqa: E402

SKIP_PREFIXES = ("summary", "recovery", "audit", "candidates")
RATING_FIELDS = ("rating_source", "rating_version", "rating_metric", "rating_value", "rating_units", "rating_poll_count", "rating_bias_metric",
                 "rating_bias_value", "rating_cohort", "track_status", "f_track")


def rows_for(rec: dict, known: dict[str, dict]) -> tuple[dict, dict]:
    p, m = rec["poll"], rec.get("pollster") or {}
    race, pid = rec["race"], rec["pid"]
    if race not in weight.IN_SCOPE_RACES:
        raise weight.ValidationError(f"{rec.get('file')}: race not in scope: {race}")
    fs, fe = p["field_start"], p["field_end"]
    sample_id = f"{pid}-{fs}-{fe}-{slug(rec.get('sponsor') or 'self')}"
    pop = enum(p.get("pop"), weight.POPS, "UNKNOWN")
    den = enum(p.get("denominator_class"), weight.DENOMS, "UNKNOWN")
    rnd = enum(p.get("round"), weight.ROUNDS, "NA")
    d, r = float(p["D"]), float(p["R"])
    method_id = rec.get("method_id") or f"{pid}-s-{race}-{fe}"
    recall = enum(m.get("recall_weighted"), weight.RECALL_ESTIMATE, "UNVERIFIED")
    disclosure = enum(m.get("disclosure_status"), weight.DISCLOSURES, "UNVERIFIED")
    poll = {"estimate_id": f"{sample_id}-{race}-{pop}-{den}-{rnd}", "poll_id": f"{sample_id}-{race}", "sample_id": sample_id, "tracking_series_id": "NA",
            "race": race, "pollster_id": pid, "method_id": method_id, "sponsor": rec.get("sponsor") or "self",
            "sponsor_class": enum(rec.get("scls"), weight.SPONSOR_CLASSES, "UNKNOWN"), "pollster_alignment": enum(rec.get("align"), weight.ALIGNMENTS, "UNKNOWN"),
            "disclosure_status": disclosure, "field_start": fs, "field_end": fe, "release_date": p.get("release_date") or fe, "n": numstr(p.get("n")), "pop": pop,
            "D": f"{d:.1f}", "R": f"{r:.1f}", "other": numstr(p.get("other")), "undecided": numstr(p.get("undecided")), "denominator_class": den,
            "margin": f"{d - r:.2f}", "round": rnd, "window": "BOTH", "recall_weighted": recall, "selected": "1", "exclusion_reason": "NA",
            "supersedes": "NA", "superseded_by": "NA", "source_url": p["source_url"], "source_locator": p.get("source_locator") or "NA",
            "primary_verified": "YES", "retrieved_at": p.get("retrieved_at") or "NA", "notes": (p.get("notes") or "").replace("\n", " ")}
    base = known.get(pid, {})
    method = {"pollster_id": pid, "pollster_name": rec.get("name") or pid, "aliases": "NA", "method_id": method_id, "applicability": "SURVEY",
              "recall_weighted": recall, "weighting_quote": m.get("weighting_quote") or "NA", "recall_target": "NA", "mode": m.get("mode") or "NA",
              "ti_member": "unknown", "method_owner": m.get("method_owner") or rec.get("name") or pid, "method_url": m.get("method_url") or "NA",
              "method_locator": m.get("method_locator") or "NA", "method_date": m.get("method_date") or fe, "retrieved_at": m.get("retrieved_at") or p.get("retrieved_at") or "NA",
              **{k: base.get(k, "NA") for k in RATING_FIELDS}, "new_pollster": "NA" if base else "true", "track_ledger_ref": "NA",
              "notes": "added 2026-10-27 with the competitive House races" if race in weight.HOUSE_RACES else "added 2026-10-27"}
    if not base:
        method["track_status"], method["f_track"] = "PROVISIONAL", "1.0"
    return poll, method


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", action="append", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    bundle = Path(a.bundle_dir)
    state = json.loads((bundle / "run-state.json").read_text())
    cutoff = weight.parse_as_of(state["analytical_as_of"])
    polls = weight.read_csv(str(bundle / "polls.csv"), weight.POLLS_HEADER)
    methods = weight.read_csv(str(bundle / "pollsters.csv"), weight.POLLSTERS_HEADER)
    # a firm's rating comes from its cycle record (or any record that carries one)
    known = {}
    for r in methods:
        if r.get("rating_source") not in (None, "", "NA") and (r["pollster_id"] not in known or r["applicability"] == "CYCLE_BOILERPLATE"):
            known[r["pollster_id"]] = r
    pmap, mmap = {r["estimate_id"]: r for r in polls}, {r["method_id"]: r for r in methods}
    files = sorted(f for d in a.inputs for f in glob.glob(os.path.join(d, "*.json")) if not os.path.basename(f).startswith(SKIP_PREFIXES))
    added, same = [], 0
    for f in files:
        rec = json.load(open(f, encoding="utf-8"))
        rec.setdefault("file", os.path.basename(f))
        poll, method = rows_for(rec, known)
        eid = poll["estimate_id"]
        if eid in pmap:
            stable = set(weight.POLLS_HEADER) - {"margin", "window", "selected", "exclusion_reason", "retrieved_at", "notes"}
            if any(pmap[eid][k] != poll[k] for k in stable):
                raise weight.ValidationError(f"{f}: existing row differs: {eid}")
            same += 1
            continue
        pmap[eid] = poll
        added.append(eid)
        if method["method_id"] not in mmap:
            mmap[method["method_id"]] = method
    with tempfile.TemporaryDirectory(prefix="midterm-merge-") as temp:
        for name in ("heat.csv", "coverage.csv", "exclusions.csv", "run-state.json"):
            shutil.copy2(bundle / name, Path(temp) / name)
        weight.write_csv(str(Path(temp) / "polls.csv"), weight.POLLS_HEADER, list(pmap.values()))
        weight.write_csv(str(Path(temp) / "pollsters.csv"), weight.POLLSTERS_HEADER, sorted(mmap.values(), key=lambda r: r["method_id"]))
        b = weight.Bundle(temp, cutoff, state)
        derived = b.derive_rows(b.polls)
        weight.write_csv(str(Path(temp) / "polls.csv"), weight.POLLS_HEADER, derived)
        b = weight.Bundle(temp, cutoff, state)
        if not b.validate():
            raise weight.ValidationError("\n".join(b.problems))
        if not a.dry_run:
            for name in ("polls.csv", "pollsters.csv"):
                weight.snapshot(str(bundle / name), str(bundle))
                shutil.copy2(Path(temp) / name, bundle / name)
    print(json.dumps({"files": len(files), "added": len(added), "already_present": same, "stored_rows": len(derived), "methods": len(mmap),
                      "validation": "passed", "written": not a.dry_run}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, weight.ValidationError) as exc:
        print(f"NOT MERGED: {exc}", file=sys.stderr)
        sys.exit(1)
