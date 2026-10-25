#!/usr/bin/env python3
"""Verify a data-stage gate, render its method note, and seal one immutable release."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("stage1", "stage1b", "stage2"), required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--template", help="Explicit versioned method template")
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    bundle_dir = Path(a.bundle_dir)
    state_path = bundle_dir / "run-state.json"
    rs = json.loads(state_path.read_text())
    ledger_path = Path(a.ledger)
    if not ledger_path.is_file():
        raise weight.ValidationError("source coverage ledger is missing")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise weight.ValidationError("commit the reviewed code locally before sealing a calculator version")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    cutoff = weight.parse_as_of(rs["analytical_as_of"])
    proposed = json.loads(json.dumps(rs))
    if a.stage != "stage2":
        proposed["stage_outcomes"][a.stage] = "PASSED"
    else:
        if not all(rs["stage_outcomes"].get(stage) == "PASSED" for stage in ("stage1", "stage1b", "stageW", "stage2a", "stage2b", "stage2c")):
            raise weight.ValidationError("Stage 2 requires the earlier gates and all three data substages")
        for name in ("backtest_source", "turnout_source"):
            source = rs.get(name, {})
            source_path = root / source.get("path", "")
            if not source_path.is_file() or weight.sha256_file(str(source_path)) != source.get("sha256"):
                raise weight.ValidationError(f"missing or changed Stage 2 source: {name}")
    b = weight.Bundle(str(bundle_dir), cutoff, proposed)
    if not b.validate():
        raise weight.ValidationError("\n".join(b.problems))
    needed = weight.SENATE_RACES + (weight.GOVERNOR_RACES if a.stage in ("stage1b", "stage2") else [])
    for race in needed:
        if not any(p["race"] == race for p in b.polls):
            raise weight.ValidationError(f"inventory coverage missing: {race}")
        if not any(p["race"] == race for p in b.heat):
            raise weight.ValidationError(f"heat attempt/status missing: {race}")
    if a.stage == "stage1b":
        if rs["stage_outcomes"].get("stage1") != "PASSED":
            raise weight.ValidationError("Stage 1 must pass before Stage 1b")
        if not set(needed) <= {p["race"] for p in b.coverage}:
            raise weight.ValidationError("coverage connector attempt/status missing for an in-scope race")
    if a.stage == "stage2" and {p["race"] for p in b.backtest} != set(weight.BACKTEST_RACES):
        raise weight.ValidationError("Stage 2 backtest needs primary-verified inventory in both states")
    budget = rs.get("budget_ledger", {})
    if float(budget.get("heat_reserved_usd", 0)) != 0:
        raise weight.ValidationError("scoring is still in flight or has an unreconciled reservation")
    if float(budget.get("heat_spent_usd", 0)) > weight.HEAT_BUDGET_USD:
        raise weight.ValidationError("heat spend exceeds the authorized ceiling")
    subprocess.run([sys.executable, str(root / "analysis/weight.py"), "--self-test"], cwd=root, check=True, stdout=subprocess.DEVNULL)
    input_names = ["polls.csv", "pollsters.csv", "exclusions.csv", "heat.csv", "coverage.csv"]
    if a.stage == "stage2":
        input_names.append("backtest-2025.csv")
    digest = weight.sha256_bytes(b"".join((bundle_dir / n).read_bytes() for n in input_names) + (json.dumps(rs.get("turnout_source", {}), sort_keys=True).encode() if a.stage == "stage2" else b""))[:10]
    release_id = f"{cutoff.strftime('%Y%m%dT%H%M%S%z')}-{a.stage}-{commit[:7]}-{digest}"
    target = bundle_dir / "releases" / release_id
    if target.exists():
        raise weight.ValidationError(f"release already sealed: {target}; reuse it without rewriting")
    d = b.compute(commit, release_id)
    if abs(d["section9_heat"]["spend_usd"] - float(budget.get("heat_spent_usd", 0))) > 0.01:
        raise weight.ValidationError("heat row charges do not reconcile to the operational ledger within one cent")
    for e in d["estimates"]:
        if (e["primary_verified"] != "YES" or e["round"] == "UNVERIFIED") and any(e["flags"][k] for k in ("recall_contrast", "weighted_average")):
            raise weight.ValidationError("unverified source/round leaked into analytical eligibility")
    with tempfile.TemporaryDirectory(prefix="midterm-render-") as temp:
        temp_path = Path(temp)
        (temp_path / "derived.json").write_text(json.dumps(d))
        shutil.copy2(bundle_dir / "pollsters.csv", temp_path / "pollsters.csv")
        deferred = temp_path / "deferred.txt"
        deferred.write_text(
            "Heat summaries describe scored units only. Units without attributable captions or without budget remain explicitly missing or deferred; partial readings do not establish a complete debate comparison.\n\n"
            f"Heat units by status: {d['section9_heat']['units_by_status']}. Recorded spend: ${float(budget.get('heat_spent_usd', 0)):.6f} of $3.00.\n\n"
            "Primary-unverified poll rows and unsupported RCV-round labels remain inventoried and excluded from all calculations. " +
            ("Stage 2 uses a primary-verified retrospective subset with sparse verified recall classes; no weighted-heuristic accuracy improvement is established. Full held-out baseline evaluation, spending diagnostics and a project-specific historical ledger remain deferred. Stage 3 remains gated until November 2." if a.stage == "stage2" else "Stage 2 and Stage 3 work remains gated as specified above.")
        )
        command = [sys.executable, str(root / "scripts/render_note.py"), "--release-dir", temp, "--ledger", str(ledger_path), "--deferred", str(deferred)]
        if a.template:
            command += ["--template", a.template]
        if a.stage == "stage2":
            command.append("--active")
        subprocess.run(command, cwd=root, check=True)
        if "_PLACEHOLDER" in Path(weight.DEFAULT_NOTE).read_text():
            raise weight.ValidationError("unrendered method-note placeholders remain")
    sealed = Path(b.release(release_id, commit, weight.DEFAULT_NOTE))
    manifest = json.loads((sealed / "manifest.json").read_text())
    for f in manifest["files"]:
        if weight.sha256_file(str(sealed / f["path"])) != f["sha256"]:
            raise weight.ValidationError(f"sealed file hash mismatch: {f['path']}")
    weight.snapshot(str(state_path), str(bundle_dir))
    if a.stage != "stage2":
        rs["stage_outcomes"][a.stage] = "PASSED"
    else:
        rs["stage2_release_gate"] = "PASSED; F5 deployment verification pending"
    rs["current_release_id"] = release_id
    rs.setdefault("release_ids", []).append(release_id)
    rs["current_stage"] = "stage1b" if a.stage == "stage1" else "stageW" if a.stage == "stage1b" else "stage2-deploy"
    rs["last_checkpoint"] = datetime.now().astimezone().isoformat(timespec="seconds")
    gate_label = "Stage 2 data release sealed; live F5 verification pending" if a.stage == "stage2" else f"{a.stage} gate passed"
    rs.setdefault("checkpoints", []).append({"at": rs["last_checkpoint"], "note": f"{gate_label}; immutable release {release_id}; partial/missing heat and source verification gaps explicitly retained"})
    rs["resume_command"] = f"Continue {rs['current_stage']} from run-state.json and immutable release {release_id}; retain this analytical cutoff within the current session."
    state_path.write_text(json.dumps(rs, indent=2) + "\n")
    print(json.dumps({"gate": a.stage, "outcome": "PASSED", "release_id": release_id, "counts": d["counts"], "contrasts": {k: d["section5_contrasts"][k]["value"] for k in ("i", "ii", "iii", "iv")}, "heat": d["section9_heat"]["units_by_status"], "spend_usd": budget.get("heat_spent_usd")}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (weight.ValidationError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"GATE NOT PASSED: {exc}", file=sys.stderr)
        sys.exit(1)
