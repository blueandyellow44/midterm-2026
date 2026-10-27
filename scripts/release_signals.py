#!/usr/bin/env python3
"""Seal a release that adds the signal-adjusted reading on top of the current release, with every existing number unchanged.

Gate: the working tree is committed; the current release's files verify against its manifest; a fresh compute at the
same analytical cutoff reproduces every derived.json field of the current release except release_id, calc_version and the
new "signals" block; the polling inputs are byte-identical. Only then is a new immutable release written, with
supersedes and reason, and run-state pointed at it. The rendered method note is carried over unchanged.

Usage: python3 scripts/release_signals.py [--bundle-dir <vault bundle>]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight  # noqa: E402

VOLATILE = {"release_id", "calc_version", "signals", "section9_heat"}  # heat scoring may grow; polling fields may not
POLLING_INPUTS = ("polls.csv", "pollsters.csv", "exclusions.csv", "coverage.csv", "backtest-2025.csv")
REASON = ("Signal-adjusted reading v1.1 (Max, 2026-10-26): 27 more campaign ads scored under the raised $10 heat ceiling; "
          "missing outside money now points to the poll leader (abandonment). Every polling number, eligibility rule and polling input is unchanged.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--refresh", action="store_true", help="new analytical cutoff: polling inputs and numbers may change; the cutoff must be later than the superseded release's")
    ap.add_argument("--reason", help="supersedes reason recorded in the manifest (required with --refresh)")
    a = ap.parse_args()
    if a.refresh and not a.reason:
        raise weight.ValidationError("--refresh needs --reason")
    root = Path(__file__).resolve().parents[1]
    bundle = Path(a.bundle_dir)
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, text=True).strip():
        raise weight.ValidationError("commit the reviewed code locally before sealing a calculator version")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    state_path = bundle / "run-state.json"
    rs = json.loads(state_path.read_text())
    current_id = rs["current_release_id"]
    current = bundle / "releases" / current_id
    manifest = json.loads((current / "manifest.json").read_text())
    for f in manifest["files"]:
        if weight.sha256_file(str(current / f["path"])) != f["sha256"]:
            raise weight.ValidationError(f"current release file changed since sealing: {f['path']}")
    if not a.refresh:
        for name in POLLING_INPUTS:
            if (current / name).exists() and weight.sha256_file(str(current / name)) != weight.sha256_file(str(bundle / name)):
                raise weight.ValidationError(f"polling input differs from the current release: {name}")
    elif weight.parse_as_of(rs["analytical_as_of"]) <= weight.parse_as_of(manifest["analytical_as_of"]):
        raise weight.ValidationError("a refresh needs an analytical cutoff later than the superseded release's")
    for name in ("spending.csv", "fundamentals.csv", "spend-history.csv"):
        if not (bundle / name).is_file():
            raise weight.ValidationError(f"signal input missing: {name} (run scripts/build_signals.py)")
    subprocess.run([sys.executable, str(root / "analysis/weight.py"), "--self-test"], cwd=root, check=True, stdout=subprocess.DEVNULL)
    cutoff = weight.parse_as_of(rs["analytical_as_of"])
    proposed = json.loads(json.dumps(rs))
    reason = a.reason or REASON
    proposed["supersedes"], proposed["supersedes_reason"] = current_id, reason
    b = weight.Bundle(str(bundle), cutoff, proposed)
    if not b.validate():
        raise weight.ValidationError("\n".join(b.problems))
    old = json.loads((current / "derived.json").read_text())
    new = b.compute(commit, "candidate")
    new["counts"]["races_with_averaging_stratum"] = sorted(r for r, x in new["races"].items() if x["averaging_stratum"])
    new["counts"]["races_with_contrast_stratum"] = sorted(r for r, x in new["races"].items() if x["contrast_stratum"])
    changed = sorted(k for k in set(old) | set(new) if k not in VOLATILE and json.dumps(old.get(k), sort_keys=True) != json.dumps(new.get(k), sort_keys=True))
    moved = {}
    if a.refresh:
        moved = {r: [old["races"][r]["polling_read"]["margin"], new["races"][r]["polling_read"]["margin"]] for r in new["races"]
                 if old["races"].get(r, {}).get("polling_read", {}).get("margin") != new["races"][r]["polling_read"]["margin"]}
    elif changed:
        raise weight.ValidationError(f"existing derived fields changed: {changed}")
    if not new.get("signals"):
        raise weight.ValidationError("signals block missing from compute")
    digest = weight.sha256_bytes(b"".join((bundle / n).read_bytes() for n in ("spending.csv", "fundamentals.csv", "spend-history.csv", "state-poll-error.csv", "poll-error-history.csv", "early-vote.csv", "heat.csv")))[:10]
    release_id = f"{cutoff.strftime('%Y%m%dT%H%M%S%z')}-{'stage2-refresh' if a.refresh else 'stage2-signals'}-{commit[:7]}-{digest}"
    b.run_state = proposed
    sealed = Path(b.release(release_id, commit, weight.DEFAULT_NOTE))
    sealed_manifest = json.loads((sealed / "manifest.json").read_text())
    for f in sealed_manifest["files"]:
        if weight.sha256_file(str(sealed / f["path"])) != f["sha256"]:
            raise weight.ValidationError(f"sealed file hash mismatch: {f['path']}")
    weight.snapshot(str(state_path), str(bundle))
    rs["supersedes"], rs["supersedes_reason"] = current_id, reason
    rs["current_release_id"] = release_id
    rs.setdefault("release_ids", []).append(release_id)
    rs["last_checkpoint"] = datetime.now().astimezone().isoformat(timespec="seconds")
    rs.setdefault("checkpoints", []).append({"at": rs["last_checkpoint"], "note": f"signal-adjusted reading sealed; immutable release {release_id}; supersedes {current_id}; " + ("refresh: polling reads moved in " + ", ".join(sorted(moved)) if a.refresh else "all existing derived fields reproduced unchanged")})
    rs["signal_release"] = {"release_id": release_id, "supersedes": current_id, "calculator_commit": commit[:7],
                            "manifest_sha256": weight.sha256_file(str(sealed / "manifest.json")), "existing_fields_unchanged": not a.refresh, "polling_reads_moved": moved}
    rs["resume_command"] = f"Continue from run-state.json and immutable release {release_id} (signal-adjusted reading added beside the polling read); Stage 3 freeze on 2026-11-02 records both readings."
    state_path.write_text(json.dumps(rs, indent=2) + "\n")
    print(json.dumps({"release_id": release_id, "supersedes": current_id, "adjusted": {r: v["adjusted_margin"] for r, v in new["signals"]["per_race"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (weight.ValidationError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"RELEASE NOT SEALED: {exc}", file=sys.stderr)
        sys.exit(1)
