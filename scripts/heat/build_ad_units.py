#!/usr/bin/env python3
"""Turn captured ad transcripts into heat units for score_units.py.

Usage: python3 scripts/heat/build_ad_units.py --sources sources/heat-ads-20261026 --bundle-dir <vault bundle> --out <units.json>
Reads <sources>/manifest.csv and <sources>/<video_id>.txt. A unit reuses the unit_id of any existing heat row with the
same source URL, so it replaces that placeholder instead of adding a duplicate. Caption noise ([music], >>) is removed;
words are not edited.
"""
from __future__ import annotations
import argparse, csv, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weight  # noqa: E402
from captions import split_sentences  # noqa: E402

NOISE = re.compile(r"\[(?:music|applause|cheering|laughter)\]|>>", re.I)
# A bare self-identification ("I'm Tom Tiffany.") carries no rhetoric and makes the pinned meter return malformed output
# (HTTP 422, 2026-10-26: Benson "Fair Shot", Tiffany "Wisconsin Is Everything to Me"). Merge it into the next sentence.
NAME_LINE = re.compile(r"^I'?m (?:Dr\. )?[A-Z][\w.'-]*(?: [A-Z][\w.'-]*){0,3}\.$")


def merge_name_lines(sentences: list[str]) -> list[str]:
    out: list[str] = []
    carry = ""
    for s in sentences:
        if NAME_LINE.match(s.strip()):
            carry = (carry + " " + s.strip()).strip()
            continue
        out.append((carry + " " + s).strip() if carry else s)
        carry = ""
    if carry:
        if out:
            out[-1] = out[-1] + " " + carry
        else:
            out.append(carry)
    return out


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", NOISE.sub(" ", text)).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    heat = weight.read_csv(os.path.join(a.bundle_dir, "heat.csv"), weight.HEAT_HEADER)
    by_url = {}
    for h in heat:
        if h["source_type"] == "AD" and h["source_url"].startswith("http"):
            by_url[(h["race"], h["slot"], h["source_url"].split("v=")[-1][:11])] = h["unit_id"]
    units = []
    with open(os.path.join(a.sources, "manifest.csv"), newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            path = os.path.join(a.sources, f"{m['video_id']}.txt")
            if not os.path.isfile(path):
                raise SystemExit(f"missing transcript: {path}")
            sentences = merge_name_lines(split_sentences(clean(open(path, encoding="utf-8").read())))
            if len(sentences) < 2:
                raise SystemExit(f"transcript too short to score: {m['video_id']}")
            vid = m["video_id"]
            url = (m.get("source_url") or "").strip() or (f"https://www.youtube.com/watch?v={vid}" if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) else "")
            if not url.startswith("http"):
                raise SystemExit(f"no source URL for {vid}: add one to manifest.csv")
            uid = by_url.get((m["race"], m["slot"], vid)) or f"ad-{vid}"
            units.append({"race": m["race"], "candidate": m["candidate"], "slot": m["slot"], "source_type": "AD", "unit_id": uid, "unit_label": m["label"],
                          "source_url": url, "caption_source": m["caption_source"], "sentences": sentences, "notes": m["notes"]})
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(units, f, indent=1)
    print(f"{len(units)} ad units, {sum(u['unit_id'] == 'ad-' + u['source_url'][-11:] or u['unit_id'] == 'ad-ramaswamy-mother-ad' for u in units)} new ids, {sum(len(u['sentences']) for u in units)} sentences -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
