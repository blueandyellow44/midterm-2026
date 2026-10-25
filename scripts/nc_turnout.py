#!/usr/bin/env python3
"""Read private official ZIPs and save aggregate-only NC turnout context."""
import argparse
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    root = Path(args.source_dir)
    out = {"source_page": "https://www.ncsbe.gov/results-data/absentee-and-provisional-data",
           "layout_url": "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/layout_absentee.txt",
           "layout_sha256": weight.sha256_file(str(root / "nc-layout-absentee.txt")),
           "retrieved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "note": "Party registration, not vote choice. Non-contemporaneous comparison of the 2026 current file against the final 2022 file; not validation or a prediction. No comparable published party-registration composition identified among the current contributing NC polls; party identification is not substituted.", "years": {}}
    for year, election, modified in [(2026, "11/03/2026", "2026-10-25T09:22:59Z"), (2022, "11/08/2022", "2022-11-19T10:33:42Z")]:
        path = root / f"nc-{year}.zip"
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith(".csv")]
            if len(names) != 1:
                raise weight.ValidationError("NC ZIP must contain exactly one CSV")
            with archive.open(names[0]) as binary:
                # The export contains legacy single-byte names/address data,
                # including bytes undefined in cp1252. Latin-1 preserves every
                # byte; calculations use the ASCII code/date/identifier fields.
                summary = weight.nc_absentee_summary(csv.DictReader(io.TextIOWrapper(binary, encoding="latin-1")), election, quarantine_conflicts=True)
        summary.update(source_url=f"https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/{year}_{election[:2]}_{election[3:5]}/absentee_{year}{election[:2]}{election[3:5]}.zip", file_sha256=weight.sha256_file(str(path)), source_last_modified=modified)
        out["years"][str(year)] = summary
        print(year, summary["accepted_unique"], summary["duplicate_accepted_rows_removed"])
    if Path(args.output).exists():
        raise weight.ValidationError("use a new versioned output filename")
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, weight.ValidationError, zipfile.BadZipFile) as exc:
        sys.exit(f"NC turnout aggregation stopped: {exc}")
