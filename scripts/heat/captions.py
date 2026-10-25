#!/usr/bin/env python3
"""Caption and transcript helpers for heat units.

- vtt_text(path): collapse a WebVTT file (YouTube auto-captions repeat rolling cues) into plain text.
- split_sentences(text): sentence list for the meter (one call per sentence, as the live meter does).
- speaker_turns(path): load a transcript JSON [{speaker, text}] and group consecutive turns per speaker.

CLI:  python3 scripts/heat/captions.py vtt <file.vtt>        -> JSON array of sentences
      python3 scripts/heat/captions.py turns <transcript.json> -> JSON {speaker: [[sentences of answer 1], ...]}
"""
from __future__ import annotations

import json
import re
import sys

TAG = re.compile(r"<[^>]+>")
TS = re.compile(r"^\d\d:\d\d(:\d\d)?[.,]\d{3}\s+-->\s+")
ABBREV = {"mr", "mrs", "ms", "dr", "sen", "gov", "rep", "st", "u.s", "jr", "sr", "vs", "no", "lt", "col", "gen", "inc", "co"}


def vtt_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    out: list[str] = []
    last = ""
    for line in raw.splitlines():
        s = line.strip()
        if not s or s == "WEBVTT" or s.startswith(("Kind:", "Language:", "NOTE", "STYLE")) or TS.match(s) or re.fullmatch(r"\d+", s):
            continue
        s = TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
        s = re.sub(r"\s+", " ", s).strip()
        if not s or s == last:
            continue
        # rolling cues: the new line often begins with the tail of the previous one
        if last and s.startswith(last):
            s = s[len(last):].strip()
            if not s:
                continue
        out.append(s)
        last = (line.strip() and TAG.sub("", line.strip())) or last
    text = " ".join(out)
    # drop bracketed sound tags
    text = re.sub(r"\[(music|applause|laughter|inaudible|crosstalk)[^\]]*\]", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str, min_words: int = 3) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])", text)
    sentences: list[str] = []
    buf = ""
    for p in parts:
        buf = (buf + " " + p).strip() if buf else p
        tail = buf.rstrip(".!?\"')").split(" ")[-1].lower().rstrip(".")
        if tail in ABBREV:
            continue
        sentences.append(buf)
        buf = ""
    if buf:
        sentences.append(buf)
    merged: list[str] = []
    for s in sentences:
        if merged and len(s.split()) < min_words:
            merged[-1] = merged[-1] + " " + s
        else:
            merged.append(s)
    return merged


def speaker_turns(path: str) -> dict[str, list[list[str]]]:
    with open(path, "r", encoding="utf-8") as f:
        turns = json.load(f)
    out: dict[str, list[list[str]]] = {}
    prev = None
    for t in turns:
        sp = (t.get("speaker") or "").strip()
        txt = (t.get("text") or "").strip()
        if not sp or not txt:
            continue
        if sp == prev:
            out[sp][-1].extend(split_sentences(txt))
        else:
            out.setdefault(sp, []).append(split_sentences(txt))
        prev = sp
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    mode, path = sys.argv[1], sys.argv[2]
    if mode == "vtt":
        json.dump(split_sentences(vtt_text(path)), sys.stdout, indent=1)
    elif mode == "turns":
        json.dump(speaker_turns(path), sys.stdout, indent=1)
    else:
        sys.exit(2)
    print()
