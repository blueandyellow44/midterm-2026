#!/usr/bin/env python3
"""Build the primary-verified 2025 subset without reusing 2026 survey methods."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


def build(bundle_dir, evidence):
    root = Path(bundle_dir)
    state = json.loads((root / "run-state.json").read_text())
    bundle = weight.Bundle(str(root), weight.parse_as_of(state["analytical_as_of"]), state)
    # Freeze the pre-backtest identity set, so new historical firms cannot
    # silently become eligible for recall classification in this check.
    registry = {p["pollster_id"]: p for p in bundle.pollsters if "-s-2025-" not in p["method_id"]}
    methods = [p for p in bundle.pollsters if "-s-2025-" not in p["method_id"]]
    rows = []
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for record in evidence["records"]:
        pid = record["pollster_id"]
        if pid not in registry:
            raise weight.ValidationError(f"historical classification outside fixed 2026 registry: {pid}")
        mid = f"{pid}-s-2025-{record['state']}-{record['field_end']}"
        method = dict(registry[pid])
        method.update(method_id=mid, applicability="SURVEY", recall_weighted=record["recall_weighted"],
                      weighting_quote=record["weighting_quote"], recall_target="NA", mode=record["mode"],
                      method_url=record["method_url"], method_locator=record["source_locator"],
                      method_date=record["release_date"], retrieved_at=now,
                      notes=record["classification_reason"] + " Applicable to this 2025 survey only; never backfilled from 2026. " + registry[pid]["notes"].split("[SB2026]")[-1])
        methods.append(method)
        cert_source = evidence["certified"][record["state"]]
        cert = weight.certified_vote_margin(cert_source)
        if cert is None:
            raise weight.ValidationError("invalid certified vote counts")
        sample_id = f"{pid}-{record['field_start']}-{record['field_end']}"
        race = f"2025-{record['state']}-GOV"
        for variant in record["variants"]:
            pop, denom, d, r, other, undecided, *sample = variant
            poll_id = f"{sample_id}-{race}"
            row = {k: "NA" for k in weight.BACKTEST_HEADER}
            row.update(estimate_id=f"{poll_id}-{pop}-{denom}-NA", poll_id=poll_id, sample_id=sample_id,
                       tracking_series_id=f"TS-{pid}-{race}-2025-series", race=race, pollster_id=pid,
                       method_id=mid, sponsor=record["pollster_id"], sponsor_class="UNKNOWN", pollster_alignment="UNKNOWN",
                       disclosure_status="DISCLOSED" if record["recall_weighted"] in ("YES", "NO") else "UNVERIFIED",
                       field_start=record["field_start"], field_end=record["field_end"], release_date=record["release_date"],
                       n=str(sample[0] if sample else record["n"]), pop=pop, D=str(d), R=str(r), other=str(other), undecided=str(undecided),
                       denominator_class=denom, round="NA", recall_weighted=record["recall_weighted"], selected="1", exclusion_reason="NA",
                       source_url=record["source_url"], source_locator=record["source_locator"], primary_verified="YES", retrieved_at=now,
                       notes=record["classification_reason"], certified_D=str(cert["D"]), certified_R=str(cert["R"]),
                       certified_margin=str(cert["margin"]), result_url=cert_source["source_url"], result_locator=cert_source["result_locator"],
                       certification_date=cert_source["certification_date"])
            rows.append(row)
    bundle.pollsters = methods
    bundle.method_by_id = {p["method_id"]: p for p in methods}
    bundle.backtest = bundle.derive_rows(rows, backtest=True)
    if not bundle.validate():
        raise weight.ValidationError("\n".join(bundle.problems))
    return methods, bundle.backtest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    evidence = json.loads(Path(args.evidence).read_text())
    methods, rows = build(args.bundle_dir, evidence)
    out = Path(args.output_dir)
    out.mkdir(exist_ok=True)
    for name, header, records in [("pollsters.csv", weight.POLLSTERS_HEADER, methods), ("backtest-2025.csv", weight.BACKTEST_HEADER, rows)]:
        target = out / name
        if target.exists():
            weight.snapshot(str(target), str(out))
        weight.write_csv(str(target), header, records)
    print(json.dumps({"stored_variants": len(rows), "selected_surveys": sum(r["selected"] == "1" for r in rows), "method_records": len(methods)}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, weight.ValidationError) as exc:
        sys.exit(f"Backtest build stopped: {exc}")
