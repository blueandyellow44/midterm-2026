#!/usr/bin/env python3
"""Import an explicitly reviewed Silver Bulletin identity map; no fuzzy matching."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


def workbook_profiles(path, source):
    from openpyxl import load_workbook
    if weight.sha256_file(str(path)) != source["sha256"]:
        raise weight.ValidationError("ratings workbook hash mismatch")
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book[source["sheet"]]
        rows = iter(sheet.values)
        header = next(rows)
        expected = {0: "Pollster", 2: "Pollster Rating ID", 3: "# of Polls", 5: "Banned by Silver Bulletin", 9: "Mean-Reverted Bias", 13: "Simple Average Error"}
        for index, label in expected.items():
            if header[index] != label:
                raise weight.ValidationError(f"ratings header {index}: expected {label!r}, got {header[index]!r}")
        profiles = {}
        for row in rows:
            if row[2] is None:
                continue
            rid = int(row[2])
            if rid in profiles:
                raise weight.ValidationError(f"duplicate rating ID {rid}")
            # In this workbook A contains rank despite its label; B contains the name.
            profiles[rid] = {"name": row[1], "n": row[3], "banned": row[5], "bias": row[9], "sae": row[13]}
        if not profiles:
            raise weight.ValidationError("empty ratings workbook")
        return profiles
    finally:
        book.close()


def import_rows(rows, source, profiles):
    if not rows:
        raise weight.ValidationError("empty pollster registry")
    mapping = source["mapping"]
    if {r["pollster_id"] for r in rows} != set(mapping):
        raise weight.ValidationError("identity map does not cover exactly the registry")
    result = []
    for original in rows:
        r = dict(original)
        identity = mapping[r["pollster_id"]]
        if r["pollster_name"] != identity["registry_name"]:
            raise weight.ValidationError(f"registry name changed for {r['pollster_id']}")
        profile = profiles.get(identity["rating_id"]) if identity["rating_id"] is not None else None
        if identity["rating_id"] is not None and (profile is None or profile["name"] != identity["expected_rating_name"]):
            raise weight.ValidationError(f"reviewed rating identity mismatch for {r['pollster_id']}")
        sae = profile["sae"] if profile else None
        compatible = isinstance(sae, (float, int)) and not isinstance(sae, bool) and 0 <= sae < float("inf")
        r.update(rating_source=source["name"], rating_version=source["version_label"],
                 rating_metric="Simple Average Error" if compatible else "NA",
                 rating_value=str(sae) if compatible else "NA", rating_units="percentage points" if compatible else "NA",
                 rating_poll_count=str(profile["n"]) if compatible else "NA",
                 rating_bias_metric="Mean-Reverted Bias" if compatible else "NA",
                 rating_bias_value=str(profile["bias"]) if compatible and profile["bias"] is not None else "NA",
                 rating_cohort=source["cohort"], track_status="RATED" if compatible else "PROVISIONAL",
                 f_track=str(weight.f_track_from_simple_average_error(sae if compatible else None)))
        note = f"[SB2026] {identity['reason']}"
        if profile:
            note += f" Profile ID {identity['rating_id']}, {profile['name']}; publisher banned flag={profile['banned']}."
        note += " Provisional 1.0 denotes missing compatible evidence, not demonstrated quality. Bias is descriptive and is not applied to the estimate."
        r["notes"] = original.get("notes", "").split("[SB2026]")[0].rstrip() + " " + note
        result.append(r)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = json.loads(Path(args.map).read_text())
    rows = weight.read_csv(args.input, weight.POLLSTERS_HEADER)
    out = import_rows(rows, source, workbook_profiles(source["local_source"], source))
    if Path(args.output).resolve() == Path(args.input).resolve():
        weight.snapshot(args.input, str(Path(args.input).parent))
    weight.write_csv(args.output, weight.POLLSTERS_HEADER, out)
    print(json.dumps({"method_records": len(out), "statuses": dict(Counter(r["track_status"] for r in out)), "factors": dict(Counter(r["f_track"] for r in out))}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, weight.ValidationError) as exc:
        sys.exit(f"Ratings import stopped: {exc}")
