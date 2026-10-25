#!/usr/bin/env python3
"""Score heat units (debate answers, ads) with the pinned LITMUS Live meter and write heat.csv rows.

Usage:
  python3 scripts/heat/score_units.py --units <units.json> --bundle-dir <vault methods dir> --run-state <run-state.json>
      --meter http://127.0.0.1:8796 --passcode-file ~/litmus-meter/.dev.vars --scorer-commit <sha> --prompt-sha256 <hex>
      --model claude-haiku-4-5 --config <scorer-config.json> [--dry-run]

units.json: ordered list of units; the order is the scoring priority under the budget cap.
  {race, candidate, slot, source_type, unit_id, unit_label, source_url, caption_source, sentences: [..], status?: "MISSING_TRANSCRIPT", notes?}

Every paid call is reserved first in run-state (units * unit_rate * 1.5); if spent + reserved would exceed the $3.00 ceiling the
remaining units get SKIPPED_BUDGET rows and scoring stops. A unit already in heat-cache/ under the same cache key costs nothing.
The passcode and keys never leave the meter's own files; this script only reads METER_PASSCODE to log in to the local meter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis"))
import weight  # noqa: E402

PER_LINE_USD = 0.0045   # era check 2026-10-10: $1.79 for about 400 lines incl. verdicts; a conservative per-line figure
PER_VERDICT_USD = 0.012


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_passcode(path: str) -> str:
    with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
        m = re.search(r"^METER_PASSCODE=(.*)$", f.read(), re.M)
    if not m or not m.group(1).strip():
        raise SystemExit("METER_PASSCODE not found in the passcode file")
    return m.group(1).strip()


class Meter:
    def __init__(self, base: str, passcode: str):
        self.base = base.rstrip("/")
        req = urllib.request.Request(f"{self.base}/api/login", data=json.dumps({"passcode": passcode}).encode(), headers={"content-type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 200:
                raise SystemExit(f"meter login failed {r.status}")
            self.cookie = r.headers.get("set-cookie", "").split(";")[0]
        sess = self.get("/api/session")
        if sess.get("stub"):
            raise SystemExit("the meter is in STUB_MODE; these would be fake scores. Refusing.")

    def get(self, path):
        req = urllib.request.Request(f"{self.base}{path}", headers={"cookie": self.cookie})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())

    def post(self, path, body):
        req = urllib.request.Request(f"{self.base}{path}", data=json.dumps(body).encode(), headers={"content-type": "application/json", "cookie": self.cookie}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode() or "{}")
            except Exception:
                body = {}
            return e.code, body


def score_unit(meter: Meter, sentences: list[str]) -> dict:
    lines, cost = [], 0.0
    for i, text in enumerate(sentences):
        context = sentences[max(0, i - weight_ctx()):i]
        status, b = meter.post("/api/score", {"text": text.strip(), "context": context})
        cost += float(b.get("cost_usd") or 0)
        if status != 200:
            lines.append({"seq": i, "heard": text, "status": "dropped", "error": b.get("error"), "http": status})
            if status == 402:
                raise RuntimeError("meter budget reached (402)")
            continue
        lines.append({"seq": i, "heard": text, "text": b.get("text"), "status": "scored" if b.get("claim") else "noclaim", "score": b.get("score"),
                      "reason": b.get("reason"), "marks": b.get("marks"), "devices": b.get("devices"), "appeal": b.get("appeal")})
    scored = [l for l in lines if l["status"] == "scored"]
    verdict = None
    if scored:
        status, syn = meter.post("/api/synopsis", {"lines": [{"seq": l["seq"], "text": l["text"], "score": l["score"], "reason": l["reason"]} for l in scored],
                                                   "transcript": [l.get("text") or l["heard"] for l in lines if l["status"] != "dropped"]})
        cost += float(syn.get("cost_usd") or 0)
        if status == 200:
            verdict = {"verdict": syn.get("verdict"), "style_name": syn.get("style_name"), "summary": syn.get("summary_text"), "why": syn.get("why"), "line_stats": syn.get("summary")}
        else:
            verdict = {"error": syn.get("error"), "http": status}
    return {"lines": lines, "report": verdict, "cost_usd": round(cost, 6)}


def weight_ctx() -> int:
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--run-state", required=True)
    ap.add_argument("--meter", default="http://127.0.0.1:8796")
    ap.add_argument("--passcode-file", default="~/litmus-meter/.dev.vars")
    ap.add_argument("--scorer-commit", required=True)
    ap.add_argument("--prompt-sha256", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--config", required=True, help="scorer config JSON; its sha256 is config_sha256")
    ap.add_argument("--dry-run", action="store_true", help="plan only: cache hits, estimates, budget decisions; no calls")
    a = ap.parse_args()

    with open(a.units, "r", encoding="utf-8") as f:
        units = json.load(f)
    with open(a.config, "rb") as f:
        config_bytes = f.read()
    config_sha = weight.sha256_bytes(config_bytes)
    with open(a.run_state, "r", encoding="utf-8") as f:
        rs = json.load(f)
    ledger = rs.setdefault("budget_ledger", {})
    ledger.setdefault("heat_ceiling_usd", weight.HEAT_BUDGET_USD)
    for k in ("heat_spent_usd", "heat_reserved_usd"):
        ledger.setdefault(k, 0.0)
    for k in ("heat_units_scored", "heat_cache_hits"):
        ledger.setdefault(k, 0)

    def save_rs():
        rs["last_checkpoint"] = datetime.now().astimezone().isoformat(timespec="seconds")
        with open(a.run_state, "w", encoding="utf-8") as f:
            json.dump(rs, f, indent=2)

    cache_dir = os.path.join(a.bundle_dir, "heat-cache")
    os.makedirs(cache_dir, exist_ok=True)
    heat_path = os.path.join(a.bundle_dir, "heat.csv")
    existing = weight.read_csv(heat_path, weight.HEAT_HEADER, required=False) if os.path.exists(heat_path) else []
    by_id = {h["heat_id"]: h for h in existing}

    meter = None
    stopped = False
    rows_out = []
    for u in units:
        heat_id = f"{u['race']}-{u['slot']}-{u['source_type']}-{u['unit_id']}"
        prior = by_id.get(heat_id)
        if prior and prior["status"] == "SCORED":
            rows_out.append(prior)  # never re-scored
            continue
        base = {"heat_id": heat_id, "race": u["race"], "candidate": u["candidate"], "slot": u["slot"], "source_type": u["source_type"], "unit_id": u["unit_id"],
                "unit_label": u.get("unit_label", ""), "source_url": u.get("source_url") or "NA", "caption_source": u.get("caption_source") or "NA",
                "unit_sha256": "NA", "status": "", "ph_score": "NA", "ph_label": "NA", "hottest_line": "", "calmest_line": "", "scorer_commit": "NA",
                "prompt_sha256": "NA", "model": "NA", "config_sha256": "NA", "scored_at": "NA", "cost_usd": "0", "reserved_usd": "0", "notes": u.get("notes", "")}
        sentences = [s for s in (u.get("sentences") or []) if isinstance(s, str) and s.strip()]
        if u.get("status") == "MISSING_TRANSCRIPT" or not sentences:
            base["status"] = "MISSING_TRANSCRIPT"
            base["notes"] = u.get("notes") or "no transcript or captions available"
            rows_out.append(base)
            continue
        text = "\n".join(s.strip() for s in sentences)
        unit_sha = weight.sha256_bytes(text.encode("utf-8"))
        key = weight.cache_key(unit_sha, a.scorer_commit, a.prompt_sha256, a.model, config_sha)
        base.update({"unit_sha256": unit_sha, "scorer_commit": a.scorer_commit, "prompt_sha256": a.prompt_sha256, "model": a.model, "config_sha256": config_sha})
        cache_file = os.path.join(cache_dir, f"{key}.json")
        if stopped:
            base["status"], base["notes"] = "SKIPPED_BUDGET", "budget ceiling reached before this unit"
            rows_out.append(base)
            continue
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            ledger["heat_cache_hits"] += 1
            print(f"cache hit  {heat_id}")
            cost_here = 0.0
        else:
            unit_rate = len(sentences) * PER_LINE_USD + PER_VERDICT_USD
            allowed, reserve = weight.budget_check(ledger["heat_spent_usd"], ledger["heat_reserved_usd"], 1, unit_rate, ledger["heat_ceiling_usd"])
            if not allowed:
                print(f"BUDGET STOP at {heat_id}: spent {ledger['heat_spent_usd']:.4f} reserved {ledger['heat_reserved_usd']:.4f} + {reserve:.4f} > {ledger['heat_ceiling_usd']}")
                stopped = True
                base["status"], base["notes"] = "SKIPPED_BUDGET", f"reserve {reserve:.4f} would exceed the ${ledger['heat_ceiling_usd']:.2f} ceiling"
                rows_out.append(base)
                continue
            if a.dry_run:
                print(f"would score {heat_id}: {len(sentences)} lines, reserve ${reserve:.4f}")
                base["status"], base["notes"] = "SKIPPED_BUDGET", "dry run"
                rows_out.append(base)
                ledger["heat_reserved_usd"] = round(ledger["heat_reserved_usd"] + reserve, 6)
                continue
            ledger["heat_reserved_usd"] = round(ledger["heat_reserved_usd"] + reserve, 6)
            save_rs()
            if meter is None:
                meter = Meter(a.meter, read_passcode(a.passcode_file))
            t0 = time.time()
            try:
                result = score_unit(meter, sentences)
                result.update({"cache_key": key, "unit_sha256": unit_sha, "heat_id": heat_id, "scorer_commit": a.scorer_commit, "prompt_sha256": a.prompt_sha256,
                               "model": a.model, "config_sha256": config_sha, "scored_at": now_iso(), "sentences": sentences})
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=1)
                cost_here = result["cost_usd"]
            except Exception as e:  # a failure still records its cost
                cost_here = 0.0
                base["status"], base["notes"] = "FAILED", f"{type(e).__name__}: {e}"[:300]
                base["cost_usd"], base["reserved_usd"], base["scored_at"] = "0", f"{reserve:.4f}", now_iso()
                ledger["heat_reserved_usd"] = round(ledger["heat_reserved_usd"] - reserve, 6)
                save_rs()
                rows_out.append(base)
                print(f"FAILED     {heat_id}: {e}")
                if "402" in str(e):
                    stopped = True
                continue
            ledger["heat_reserved_usd"] = round(ledger["heat_reserved_usd"] - reserve, 6)
            ledger["heat_spent_usd"] = round(ledger["heat_spent_usd"] + cost_here, 6)
            ledger["heat_units_scored"] += 1
            base["reserved_usd"] = f"{reserve:.4f}"
            save_rs()
            print(f"scored     {heat_id}: {len(sentences)} lines, ${cost_here:.4f}, {time.time() - t0:.0f}s")
        verdict = (result.get("report") or {}).get("verdict") or {}
        scored_lines = [l for l in result.get("lines", []) if l.get("status") == "scored" and isinstance(l.get("score"), (int, float))]
        if verdict.get("score") is None:
            base["status"] = "FAILED"
            base["notes"] = "no whole-unit verdict returned" + (f": {(result.get('report') or {}).get('error')}" if result.get("report") else "")
        else:
            base["status"] = "SCORED"
            base["ph_score"] = f"{float(verdict['score']):.2f}"
            base["ph_label"] = verdict.get("band") or "NA"
            if scored_lines:
                hot = max(scored_lines, key=lambda l: l["score"])
                calm = min(scored_lines, key=lambda l: l["score"])
                base["hottest_line"] = (hot.get("text") or hot["heard"])[:400]
                base["calmest_line"] = (calm.get("text") or calm["heard"])[:400]
            base["notes"] = (u.get("notes", "") + f" lines={len(result.get('lines', []))} scored={len(scored_lines)} style={(result.get('report') or {}).get('style_name')}").strip()
        base["cost_usd"] = f"{cost_here:.4f}"
        base["scored_at"] = result.get("scored_at", now_iso())
        rows_out.append(base)

    # keep rows for heat_ids not in this units file (other stages), replace the rest
    ids_now = {r["heat_id"] for r in rows_out}
    kept = [h for h in existing if h["heat_id"] not in ids_now]
    final = kept + rows_out
    final.sort(key=lambda r: (r["race"], r["source_type"], r["slot"], r["unit_id"]))
    if os.path.exists(heat_path):
        weight.snapshot(heat_path, a.bundle_dir)
    weight.write_csv(heat_path, weight.HEAT_HEADER, final)
    save_rs()
    from collections import Counter
    print("heat.csv:", dict(Counter(r["status"] for r in final)), f"spent ${ledger['heat_spent_usd']:.4f}", f"cache hits {ledger['heat_cache_hits']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
