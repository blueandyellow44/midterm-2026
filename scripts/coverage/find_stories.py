#!/usr/bin/env python3
"""Coverage temperature via the LITMUS connector (Section 10): one coverage.csv row per race and call, whatever the result.

Usage:
  python3 scripts/coverage/find_stories.py --bundle-dir <vault methods dir> --expected-edition 2026-10-25 [--races 2026-TX-SEN,...]
      [--endpoint https://studio.myop.dev/m/c8zs1jq8oi7m]

The connector is the Myop MCP server exported in ~/MCP App/myop-export (tools.md). find_stories takes {query, edition_date?}; its
reply is a tool result with text content and, where the host renders cards, structured content. This script calls it over JSON-RPC,
records the edition it reports, and never calls read_article on ads or debates (Max's ruling).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis"))
import weight  # noqa: E402

ENDPOINT = "https://studio.myop.dev/m/c8zs1jq8oi7m"
SURNAMES = {
    "2026-TX-SEN": "Talarico Paxton", "2026-IA-SEN": "Turek Hinson", "2026-ME-SEN": "Troy Jackson Collins Maine", "2026-AK-SEN": "Peltola Sullivan",
    "2026-OH-SEN-SPECIAL": "Sherrod Brown Husted", "2026-MI-SEN": "El-Sayed Rogers", "2026-NC-SEN": "Cooper Whatley", "2026-GA-SEN": "Ossoff Collins Georgia",
    "2026-OH-GOV": "Acton Ramaswamy", "2026-IA-GOV": "Sand Lahn Iowa governor", "2026-MI-GOV": "Benson James Michigan", "2026-GA-GOV": "Bottoms Jackson Georgia governor", "2026-WI-GOV": "Crowley Tiffany",
}


def rpc(endpoint: str, method: str, params: dict, rid: int, session: str | None = None):
    headers = {"content-type": "application/json", "accept": "application/json, text/event-stream"}
    if session:
        headers["mcp-session-id"] = session
    req = urllib.request.Request(endpoint, data=json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode()
        sid = r.headers.get("mcp-session-id")
    if body.lstrip().startswith("event:") or "\ndata:" in body or body.lstrip().startswith("data:"):
        datas = [l[5:].strip() for l in body.splitlines() if l.startswith("data:")]
        body = datas[-1] if datas else "{}"
    return json.loads(body or "{}"), sid


def extract(result: dict) -> dict:
    """Pull edition date, stories, outlets and P/H range out of whatever shape the tool returned."""
    out = {"edition": None, "stories": [], "text": ""}
    sc = result.get("structuredContent") or {}
    texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
    out["text"] = "\n".join(texts)
    payload = sc if sc else None
    if payload is None:
        for t in texts:
            try:
                payload = json.loads(t)
                break
            except Exception:
                continue
    if isinstance(payload, dict):
        for k in ("edition_date", "edition", "editionDate", "date"):
            if payload.get(k):
                out["edition"] = str(payload[k])[:10]
                break
        stories = payload.get("stories") or payload.get("items") or payload.get("results") or []
        if isinstance(stories, list):
            out["stories"] = stories
        if payload.get("stale") or payload.get("stale_flag") or payload.get("isStale"):
            out["stale"] = True
    if out["edition"] is None:
        m = re.search(r"(20\d\d-\d\d-\d\d)", out["text"])
        if m:
            out["edition"] = m.group(1)
    if "stale" not in out:
        out["stale"] = bool(re.search(r"\bstale\b", out["text"], re.I))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--expected-edition", required=True)
    ap.add_argument("--races", default=",".join(weight.SENATE_RACES + weight.GOVERNOR_RACES))
    ap.add_argument("--endpoint", default=ENDPOINT)
    a = ap.parse_args()
    races = [r for r in a.races.split(",") if r]
    path = os.path.join(a.bundle_dir, "coverage.csv")
    existing = weight.read_csv(path, weight.COVERAGE_HEADER, required=False) if os.path.exists(path) else []
    rows = []
    session = None
    try:
        init, session = rpc(a.endpoint, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "midterm-2026", "version": "0.1"}}, 1)
        try:
            rpc(a.endpoint, "notifications/initialized", {}, 2, session)
        except Exception:
            pass
        init_error = None
    except Exception as e:
        init_error = f"{type(e).__name__}: {e}"
    for i, race in enumerate(races, start=10):
        query = SURNAMES.get(race, race)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        row = {"race": race, "query": query, "expected_edition": a.expected_edition, "returned_edition": "NA", "edition_status": "ACCESS_FAILED", "match_status": "ERROR",
               "story_count": "0", "outlet_count": "0", "ph_low": "NA", "ph_high": "NA", "spread": "NA", "calmest_outlet": "NA", "hottest_outlet": "NA", "story_ids": "NA",
               "error_text": "", "retrieved_at": now}
        if init_error:
            row["error_text"] = init_error[:300]
            rows.append(row)
            print(f"{race}: ACCESS_FAILED {init_error}")
            continue
        try:
            res, _ = rpc(a.endpoint, "tools/call", {"name": "find_stories", "arguments": {"query": query}}, i, session)
            if "error" in res:
                row["error_text"] = json.dumps(res["error"])[:300]
                rows.append(row)
                print(f"{race}: ERROR {row['error_text']}")
                continue
            result = res.get("result", {})
            ex = extract(result)
            ed = ex["edition"]
            row["returned_edition"] = ed or "NA"
            if result.get("isError"):
                row["edition_status"] = "ACCESS_FAILED"
                row["error_text"] = ex["text"][:300]
            elif ed is None:
                row["edition_status"] = "ACCESS_FAILED"
                row["error_text"] = "no edition date in the reply"
            elif ex.get("stale"):
                row["edition_status"] = "STALE_FLAG"
            elif ed < a.expected_edition:
                row["edition_status"] = "OLDER_THAN_EXPECTED"
            else:
                row["edition_status"] = "OK"
            stories = ex["stories"]
            scores, outlets, ids = [], set(), []
            calm, hot = None, None
            for s in stories:
                if not isinstance(s, dict):
                    continue
                ids.append(str(s.get("story_id") or s.get("id") or s.get("slug") or ""))
                for k in ("outlet_count", "outlets", "n_outlets"):
                    v = s.get(k)
                    if isinstance(v, int):
                        outlets.add((ids[-1], v))
                lo, hi = s.get("ph_low") or s.get("min_score") or (s.get("range") or {}).get("low"), s.get("ph_high") or s.get("max_score") or (s.get("range") or {}).get("high")
                for v in (lo, hi):
                    try:
                        scores.append(float(v))
                    except (TypeError, ValueError):
                        pass
                c = s.get("calmest_outlet") or (s.get("calmest") or {}).get("outlet") if isinstance(s.get("calmest"), dict) else s.get("calmest_outlet")
                h = s.get("hottest_outlet") or (s.get("hottest") or {}).get("outlet") if isinstance(s.get("hottest"), dict) else s.get("hottest_outlet")
                if lo is not None and (calm is None or float(lo) < calm[0]):
                    try:
                        calm = (float(lo), c)
                    except (TypeError, ValueError):
                        pass
                if hi is not None and (hot is None or float(hi) > hot[0]):
                    try:
                        hot = (float(hi), h)
                    except (TypeError, ValueError):
                        pass
            row["story_count"] = str(len(stories))
            row["outlet_count"] = str(sum(v for _, v in outlets)) if outlets else ("0" if not stories else "NA")
            if scores:
                row["ph_low"], row["ph_high"], row["spread"] = f"{min(scores):.1f}", f"{max(scores):.1f}", f"{max(scores) - min(scores):.1f}"
            row["calmest_outlet"] = (calm[1] if calm and calm[1] else "NA")
            row["hottest_outlet"] = (hot[1] if hot and hot[1] else "NA")
            row["story_ids"] = ";".join(i for i in ids if i) or "NA"
            if row["edition_status"] == "ACCESS_FAILED":
                row["match_status"] = "ERROR"
            elif not stories:
                row["match_status"] = "ZERO"
            else:
                surnames = [w.lower() for w in query.split() if len(w) > 3]
                blob = json.dumps(stories).lower() + ex["text"].lower()
                hits = sum(1 for w in surnames if w in blob)
                row["match_status"] = "MATCHES" if hits >= min(2, len(surnames)) else "PARTIAL"
            if not stories and not ex["stories"] and ex["text"]:
                row["error_text"] = ex["text"][:300]
            print(f"{race}: {row['edition_status']} {row['match_status']} edition={row['returned_edition']} stories={row['story_count']}")
        except Exception as e:
            row["error_text"] = f"{type(e).__name__}: {e}"[:300]
            print(f"{race}: ERROR {row['error_text']}")
        rows.append(row)
    keep = [r for r in existing if not (r["expected_edition"] == a.expected_edition and r["race"] in races)]
    final = keep + rows
    final.sort(key=lambda r: (r["expected_edition"], r["race"]))
    if os.path.exists(path):
        weight.snapshot(path, a.bundle_dir)
    weight.write_csv(path, weight.COVERAGE_HEADER, final)
    print(f"coverage.csv: {len(final)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
