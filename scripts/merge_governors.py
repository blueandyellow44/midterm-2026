#!/usr/bin/env python3
"""Merge reviewed governor observations without rebuilding the sealed Senate inventory.

The input is a public evidence manifest containing complete CSV rows, method records,
and explicitly bounded corrections to existing rows. Calculations stay in weight.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest")
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text())
    bundle = Path(a.bundle_dir)
    state = json.loads((bundle / "run-state.json").read_text())
    cutoff = weight.parse_as_of(state["analytical_as_of"])
    additions = manifest.get("polls") or []
    if not additions or any(p.get("race") not in weight.GOVERNOR_RACES for p in additions):
        raise weight.ValidationError("manifest must contain only in-scope governor additions")
    polls = weight.read_csv(str(bundle / "polls.csv"), weight.POLLS_HEADER)
    methods = weight.read_csv(str(bundle / "pollsters.csv"), weight.POLLSTERS_HEADER)
    pmap = {r["estimate_id"]: r for r in polls}
    for patch in manifest.get("corrections", []):
        eid = patch["estimate_id"]
        if eid not in pmap:
            raise weight.ValidationError(f"correction target missing: {eid}")
        for k, before in patch["before"].items():
            if pmap[eid][k] not in (before, patch["after"].get(k)):
                raise weight.ValidationError(f"correction precondition failed: {eid} {k}")
        pmap[eid].update(patch["after"])
    for row in additions:
        eid = row["estimate_id"]
        if eid in pmap and pmap[eid] != row:
            # Derived columns can legitimately change after the first merge.
            stable = set(weight.POLLS_HEADER) - {"margin", "window", "selected", "exclusion_reason"}
            if any(pmap[eid][k] != row[k] for k in stable):
                raise weight.ValidationError(f"existing governor row differs: {eid}")
        else:
            pmap[eid] = row
    mmap = {r["method_id"]: r for r in methods}
    for row in manifest.get("methods", []):
        row = {k: row[k] for k in weight.POLLSTERS_HEADER}
        mid = row["method_id"]
        if mid in mmap and mmap[mid] != row:
            raise weight.ValidationError(f"existing method differs: {mid}")
        mmap[mid] = row
    with tempfile.TemporaryDirectory(prefix="midterm-governors-") as temp:
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
        for name in ("polls.csv", "pollsters.csv"):
            weight.snapshot(str(bundle / name), str(bundle))
            shutil.copy2(Path(temp) / name, bundle / name)
    print(json.dumps({"manifest_rows": len(additions), "stored_rows": len(derived), "methods": len(mmap), "validation": "passed"}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, weight.ValidationError) as exc:
        print(f"MERGE NOT APPLIED: {exc}", file=sys.stderr)
        sys.exit(1)
