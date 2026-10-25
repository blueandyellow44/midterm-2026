#!/usr/bin/env python3
"""Build the ordered heat units file from the heat-material agents' outputs.

Usage: python3 scripts/heat/build_units.py --heat-dir <scratchpad/stage1/heat> --out <units.json> [--races r1,r2] [--max-answers 3]

Inputs per race: <race>.json ({race, debate: {...}, ads: {D: [...], R: [...]}, ...}), a transcript JSON of {speaker, text} turns when the
debate had a labeled transcript, and .vtt caption files for ads (and for a debate with AUTO captions only, which cannot be split
into answers and is recorded as MISSING_TRANSCRIPT with that reason).

Unit rules (recorded in the method note):
- DEBATE unit = one candidate turn of at least MIN_ANSWER_WORDS words from the labeled transcript, moderator and panelist turns excluded;
  shorter turns are interjections or fragments and are not units.
- AD unit = one ad's full caption track.
- A transcript that is more than 90 percent uppercase (C-SPAN closed captions) is case-normalized: lowercased with sentence-initial
  capitals and a capital I. Proper nouns lose their capitals; the same rule applies to every unit so hashes stay comparable.
- Priority order under the $3.00 cap: debate answer 1 for every candidate in every race, then ad 1, then answer 2, then ad 2, then answer 3.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captions  # noqa: E402

MIN_ANSWER_WORDS = 25
SLOT_WORDS = {"D": ["democrat"], "R": ["republican"]}


def normalize_case(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.9:
        return text
    t = text.lower()
    t = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    t = re.sub(r"\bi\b", "I", t)
    t = re.sub(r"\bi'(m|ve|ll|d)\b", lambda m: "I'" + m.group(1), t)
    return t


def match_speaker(label: str, name: str) -> bool:
    if not label or not name:
        return False
    lab = re.sub(r"[^a-z ]", " ", label.lower())
    surname = name.split()[-1].lower()
    return surname in lab.split() or surname in lab.replace(" ", "")


def debate_units(race: str, meta: dict, candidates: dict, transcript_path: str | None) -> tuple[dict[str, list[dict]], str | None]:
    """Return {slot: [unit, ...]} in speaking order, or a reason string when no units can be built."""
    if meta and meta.get("held") is False:
        return {}, "no general-election debate between the two slot candidates held on or before analytical_as_of (" + str(meta.get("reason") or meta.get("notes") or "per the heat-material log")[:160] + ")"
    if not meta or not meta.get("debate_date"):
        return {}, (meta or {}).get("reason") or "no general-election debate between the two slot candidates found on or before analytical_as_of"
    if not transcript_path or not os.path.exists(transcript_path):
        if meta.get("caption_source") == "AUTO" or meta.get("auto_caption_path"):
            return {}, "only YouTube auto-captions exist for this debate; they carry no speaker labels, so answers cannot be attributed"
        return {}, "debate found but no transcript with speaker turns was reachable"
    with open(transcript_path, encoding="utf-8") as f:
        turns = json.load(f)
    if isinstance(turns, dict):
        turns = turns.get("segments") or turns.get("turns") or []
    out = {"D": [], "R": []}
    merged: list[tuple[str, str]] = []
    for t in turns:
        if not isinstance(t, dict) or not t.get("speaker") or not t.get("text"):
            if isinstance(t, dict) and t.get("text") and not t.get("speaker"):
                merged.append(("__UNLABELED__", str(t["text"]).strip()))  # breaks a run so unlabeled text never merges into a candidate turn
            continue
        sp, tx = str(t["speaker"]).strip(), str(t["text"]).strip()
        if merged and merged[-1][0] == sp:
            merged[-1] = (sp, merged[-1][1] + " " + tx)
        else:
            merged.append((sp, tx))
    caption_source = meta.get("caption_source") or "BROADCASTER"
    for slot in ("D", "R"):
        name = candidates.get(slot) or ""
        k = 0
        for sp, tx in merged:
            if not match_speaker(sp, name):
                continue
            tx = normalize_case(tx)
            if len(tx.split()) < MIN_ANSWER_WORDS:
                continue
            k += 1
            sents = captions.split_sentences(tx)
            if not sents:
                continue
            out[slot].append({"race": race, "candidate": name, "slot": slot, "source_type": "DEBATE", "unit_id": f"debate-{meta['debate_date']}-a{k:02d}",
                              "unit_label": f"answer {k} of the {meta['debate_date']} debate ({meta.get('host') or meta.get('broadcaster') or 'debate'})",
                              "source_url": meta.get("transcript_url") or meta.get("c_span_url") or (meta.get("youtube_urls") or [None])[0] or "NA",
                              "caption_source": caption_source, "sentences": sents,
                              "notes": f"turn of {len(tx.split())} words; turns under {MIN_ANSWER_WORDS} words excluded as fragments"})
    return out, None


def ad_units(race: str, slot: str, name: str, ads: list[dict], heat_dir: str) -> list[dict]:
    out = []
    for k, ad in enumerate(ads or [], start=1):
        vtt = ad.get("caption_path") or ad.get("vtt_path")
        if isinstance(vtt, list):
            vtt = next((v for v in vtt if isinstance(v, str) and os.path.exists(v if os.path.isabs(v) else os.path.join(heat_dir, v))), vtt[0] if vtt else None)
        if vtt and not isinstance(vtt, str):
            vtt = None
        if vtt and not os.path.isabs(vtt):
            vtt = os.path.join(heat_dir, vtt)
        unit = {"race": race, "candidate": name, "slot": slot, "source_type": "AD", "unit_id": f"ad-{k}-{(ad.get('publish_date') or 'nodate')}",
                "unit_label": (ad.get("title") or f"ad {k}")[:120], "source_url": ad.get("url") or "NA", "caption_source": ad.get("caption_source") or "AUTO", "sentences": [],
                "notes": f"published {ad.get('publish_date') or 'unknown'}; {ad.get('duration') or ''}".strip()}
        if vtt and os.path.exists(vtt):
            text = normalize_case(captions.vtt_text(vtt))
            unit["sentences"] = captions.split_sentences(text)
            if not unit["sentences"]:
                unit["status"], unit["notes"] = "MISSING_TRANSCRIPT", unit["notes"] + "; caption file empty"
        else:
            unit["status"] = "MISSING_TRANSCRIPT"
            unit["notes"] += "; no caption file (" + (ad.get("reason") or "not retrieved") + ")"
        out.append(unit)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--heat-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--races")
    ap.add_argument("--max-answers", type=int, default=3)
    ap.add_argument("--candidates", required=True, help="JSON file {race: {D: name, R: name}}")
    a = ap.parse_args()
    with open(a.candidates) as f:
        cands = json.load(f)
    races = a.races.split(",") if a.races else sorted(cands)
    per_race = {}
    missing_rows = []
    for race in races:
        path = os.path.join(a.heat_dir, f"{race}.json")
        meta = {}
        if os.path.exists(path):
            with open(path) as f:
                meta = json.load(f)
        else:
            missing_rows.append({"race": race, "slot": "D", "source_type": "DEBATE", "unit_id": "none", "candidate": cands[race]["D"], "status": "MISSING_TRANSCRIPT", "notes": "no heat material file for this race"})
        debate = meta.get("debate") or {}
        tpath = debate.get("transcript_path") or os.path.join(a.heat_dir, f"{race}-debate-transcript.json")
        if tpath and not os.path.isabs(tpath):
            tpath = os.path.join(a.heat_dir, tpath)
        d_units, reason = debate_units(race, debate, cands[race], tpath if os.path.exists(tpath) else None)
        ads_raw = meta.get("ads") or {}
        ads = {}
        for slot in ("D", "R"):
            v = ads_raw.get(slot)
            if isinstance(v, dict):
                v = v.get("ads") or []
            ads[slot] = [x for x in (v or []) if isinstance(x, dict)]
        per_race[race] = {"debate": d_units, "debate_reason": reason,
                          "ads": {slot: ad_units(race, slot, cands[race][slot], ads.get(slot) or [], a.heat_dir) for slot in ("D", "R")}}
        if reason:
            for slot in ("D", "R"):
                missing_rows.append({"race": race, "candidate": cands[race][slot], "slot": slot, "source_type": "DEBATE", "unit_id": f"debate-{debate.get('debate_date') or 'none'}",
                                     "unit_label": "debate", "source_url": debate.get("transcript_url") or debate.get("c_span_url") or "NA", "caption_source": debate.get("caption_source") or "NA",
                                     "status": "MISSING_TRANSCRIPT", "notes": reason, "sentences": []})
        for slot in ("D", "R"):
            if not (ads.get(slot) or []):
                missing_rows.append({"race": race, "candidate": cands[race][slot], "slot": slot, "source_type": "AD", "unit_id": "ad-none", "unit_label": "ads", "source_url": "NA",
                                     "caption_source": "NA", "status": "MISSING_TRANSCRIPT", "notes": (meta.get("gaps_" + slot) or "no official campaign channel or no ads located"), "sentences": []})
    ordered = []
    for k in range(1, a.max_answers + 1):
        for race in races:
            for slot in ("D", "R"):
                du = per_race[race]["debate"].get(slot, [])
                if len(du) >= k:
                    ordered.append(du[k - 1])
        if k <= 2:
            for race in races:
                for slot in ("D", "R"):
                    au = per_race[race]["ads"][slot]
                    if len(au) >= k and au[k - 1].get("status") != "MISSING_TRANSCRIPT":
                        ordered.append(au[k - 1])
    # missing rows last; ads beyond the two most recent are not units
    for race in races:
        for slot in ("D", "R"):
            for u in per_race[race]["ads"][slot][:2]:
                if u.get("status") == "MISSING_TRANSCRIPT":
                    ordered.append(u)
    ordered.extend(missing_rows)
    with open(a.out, "w") as f:
        json.dump(ordered, f, indent=1)
    from collections import Counter
    c = Counter((u["source_type"], u.get("status", "to_score")) for u in ordered)
    lines = sum(len(u.get("sentences", [])) for u in ordered if u.get("status") != "MISSING_TRANSCRIPT")
    print(f"{len(ordered)} units -> {a.out}; {dict(c)}; {lines} sentences to score; est ${lines * 0.0045 + 0.012 * sum(1 for u in ordered if u.get('status') != 'MISSING_TRANSCRIPT'):.2f} before the 1.5x reserve")
    for race in races:
        pr = per_race[race]
        print(f"  {race}: debate D={len(pr['debate'].get('D', []))} R={len(pr['debate'].get('R', []))} {('(' + pr['debate_reason'] + ')') if pr['debate_reason'] else ''}; ads D={len(pr['ads']['D'])} R={len(pr['ads']['R'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
