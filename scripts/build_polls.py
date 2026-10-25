#!/usr/bin/env python3
"""Build polls.csv, pollsters.csv and exclusions.csv from the research agents' JSON files, then derive with weight.py.

Usage:
  python3 scripts/build_polls.py --inputs <dir with <race>.json files> [--inputs <dir2> ...] --bundle-dir <vault methods dir>
      --run-state <run-state.json> [--overrides <overrides.json>] [--report <report.md>]

IDs are deterministic functions of the data so they stay stable across releases:
  pollster_id          slug of the canonical pollster name (aliases map to one id)
  sample_id            <pollster_id>-<field_start>-<field_end>[-<sponsor slug>]      one release, possibly several races
  poll_id              <sample_id>-<race>
  estimate_id          <poll_id>-<pop>-<denominator_class>-<round>
  tracking_series_id   TS-<pollster_id>-<race>-<series slug> or NA
  method_id            <pollster_id>-c26 (CYCLE_BOILERPLATE) or <pollster_id>-s-<field_end> (SURVEY)

Quarantine, matchup mismatch and supersession are data decisions and are set here; principal selection and tracker overlap are
decided by weight.py --derive. Anything the builder had to coerce or could not resolve is written to the report for a human pass.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
import weight  # noqa: E402

QUARANTINE_FIRMS = {
    "wedgewood": {"reason": "Admitted 2026-10-20, after the FiftyPlusOne investigation, that most releases had no real data", "evidence_date": "2026-10-20"},
    "median-strategies": {"reason": "August 2026 admission that releases were not based on real survey data", "evidence_date": "2026-08-31"},
}
ALIASES = {
    # canonical slug: patterns (lowercase substrings)
    "wedgewood": ["wedgewood"],
    "median-strategies": ["median strategies"],
    "nyt-siena": ["siena", "new york times/siena", "nyt/siena", "times/siena"],
    "fox-beacon-shaw": ["fox news", "beacon research", "shaw & company", "beacon/shaw"],
    "cbs-yougov": ["cbs news/yougov", "cbs/yougov"],
    "yougov": ["yougov"],
    "emerson": ["emerson"],
    "quinnipiac": ["quinnipiac"],
    "marist": ["marist"],
    "quantus": ["quantus"],
    "trafalgar": ["trafalgar"],
    "insideradvantage": ["insideradvantage", "insider advantage"],
    "rasmussen": ["rasmussen"],
    "morning-consult": ["morning consult"],
    "data-for-progress": ["data for progress"],
    "public-policy-polling": ["public policy polling", "ppp"],
    "cygnal": ["cygnal"],
    "fabrizio-ward-impact": ["fabrizio", "impact research"],
    "aarp": ["aarp"],
    "mason-dixon": ["mason-dixon", "mason dixon"],
    "epic-mra": ["epic-mra", "epic mra"],
    "mitchell": ["mitchell research"],
    "glengariff": ["glengariff"],
    "des-moines-register-selzer": ["selzer", "des moines register"],
    "pan-atlantic": ["pan atlantic"],
    "umaine": ["university of maine", "umaine"],
    "alaska-survey-research": ["alaska survey research", "ivan moore"],
    "cygnal-alaska": ["cygnal alaska"],
    "ut-tyler": ["ut tyler", "university of texas at tyler"],
    "ut-austin-texas-politics-project": ["texas politics project", "university of texas/texas politics", "ut austin"],
    "hobby-school-uh": ["hobby school", "university of houston"],
    "texas-southern": ["texas southern"],
    "texas-lyceum": ["texas lyceum"],
    "elon": ["elon university", "elon poll"],
    "meredith": ["meredith"],
    "high-point": ["high point"],
    "wral-surveyusa": ["surveyusa", "wral"],
    "carolina-forward": ["carolina forward"],
    "civitas": ["civitas", "john locke"],
    "ajc-uga": ["atlanta journal", "ajc", "university of georgia"],
    "landmark": ["landmark communications"],
    "bowling-green": ["bowling green"],
    "baldwin-wallace": ["baldwin wallace"],
    "ohio-northern": ["ohio northern"],
    "co-efficient": ["co/efficient", "coefficient"],
    "big-data-poll": ["big data poll"],
    "activote": ["activote"],
    "echelon": ["echelon"],
    "research-co": ["research co"],
    "harrisx": ["harrisx", "harris x"],
    "atlasintel": ["atlasintel", "atlas intel"],
    "remington": ["remington"],
    "victory-insights": ["victory insights"],
    "targoz": ["targoz"],
    "noble-predictive": ["noble predictive"],
    "change-research": ["change research"],
    "global-strategy-group": ["global strategy group", "gsg"],
    "garin-hart-yang": ["garin", "hart research"],
    "lake-research": ["lake research"],
    "normington-petts": ["normington"],
    "the-tyson-group": ["tyson group"],
    "wpa-intelligence": ["wpa intelligence", "wpai"],
    "tarrance": ["tarrance"],
    "public-opinion-strategies": ["public opinion strategies", "pos"],
    "torchlight": ["torchlight"],
    "ragnar": ["ragnar"],
    "fiftyplusone": ["fiftyplusone", "50+1"],
}


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "unknown"


def pollster_slug(name: str, members: str | None) -> str:
    text = f"{name or ''} {members or ''}".lower()
    hits = [(len(pat), cid) for cid, pats in ALIASES.items() for pat in pats if pat in text]
    if hits:
        # prefer the longest matching pattern; partnerships (fox/beacon/shaw, nyt/siena) are listed before member firms
        hits.sort(reverse=True)
        # partnership precedence: if the sponsor-partnership slug matched, use it
        for pri in ("fox-beacon-shaw", "nyt-siena", "cbs-yougov", "fabrizio-ward-impact", "wral-surveyusa", "ajc-uga", "des-moines-register-selzer"):
            if any(cid == pri for _, cid in hits):
                return pri
        return hits[0][1]
    return slug(name)


def nz(v, default="NA"):
    if v is None or (isinstance(v, str) and not v.strip()):
        return default
    return v


def numstr(v):
    if v is None or v == "":
        return "NA"
    if isinstance(v, str):
        s = v.strip().replace("%", "")
        if s.upper() in ("NA", "UNVERIFIED", "N/A", "NONE", ""):
            return "NA"
        try:
            f = float(s.replace(",", ""))
        except ValueError:
            return "NA"
    else:
        f = float(v)
    return str(int(f)) if abs(f - round(f)) < 1e-9 else f"{f:g}"


def enum(v, allowed, default):
    s = str(v or "").strip().upper().replace(" ", "_")
    return s if s in allowed else default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", action="append", required=True)
    ap.add_argument("--bundle-dir", default=weight.DEFAULT_BUNDLE_DIR)
    ap.add_argument("--run-state", required=True)
    ap.add_argument("--overrides")
    ap.add_argument("--report")
    a = ap.parse_args()
    with open(a.run_state) as f:
        rs = json.load(f)
    as_of = weight.parse_as_of(rs["analytical_as_of"])
    overrides = {}
    if a.overrides and os.path.exists(a.overrides):
        with open(a.overrides) as f:
            overrides = json.load(f)
    report: list[str] = []
    files = sorted(p for d in a.inputs for p in glob.glob(os.path.join(d, "*.json")))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    method_records: dict[str, dict] = {}
    method_conflicts: dict[str, set] = defaultdict(set)
    poll_rows: list[dict] = []
    exclusions: dict[tuple, dict] = {}
    pollster_names: dict[str, str] = {}

    def method_for(pid: str, prec: dict | None, field_end: str, sole: bool) -> tuple[str, str, str]:
        """Return (method_id, recall_weighted, disclosure_status), creating the method record if needed."""
        applicability = enum((prec or {}).get("applicability"), weight.APPLICABILITY, "CYCLE_BOILERPLATE")
        if sole and (prec or {}).get("applicability") is None:
            applicability = "SURVEY"
        mid = f"{pid}-c26" if applicability == "CYCLE_BOILERPLATE" else f"{pid}-s-{field_end}"
        recall = enum((prec or {}).get("recall_weighted"), weight.RECALL_METHOD, "UNVERIFIED")
        quote = nz((prec or {}).get("weighting_quote"))
        if recall in ("YES", "NO") and quote == "NA":
            report.append(f"{pid}: {recall} without a weighting_quote -> downgraded to UNVERIFIED")
            recall = "UNVERIFIED"
        disclosure = enum((prec or {}).get("disclosure_status"), weight.DISCLOSURES, "UNVERIFIED")
        ov = overrides.get("methods", {}).get(mid, {})
        rec = {
            "pollster_id": pid, "pollster_name": pollster_names.get(pid, pid), "aliases": ";".join((prec or {}).get("aliases") or []) or "NA", "method_id": mid,
            "applicability": applicability, "recall_weighted": recall, "weighting_quote": quote, "recall_target": nz((prec or {}).get("recall_target")),
            "mode": nz((prec or {}).get("mode")), "ti_member": str((prec or {}).get("ti_member", "unknown")).lower(), "method_owner": nz((prec or {}).get("method_owner")),
            "method_url": nz((prec or {}).get("method_url")), "method_locator": nz((prec or {}).get("method_locator")), "method_date": nz((prec or {}).get("method_date")),
            "retrieved_at": nz((prec or {}).get("retrieved_at"), now), "rating_source": "NA", "rating_version": "NA", "rating_metric": "NA", "rating_value": "NA",
            "rating_units": "NA", "rating_poll_count": "NA", "rating_bias_metric": "NA", "rating_bias_value": "NA", "rating_cohort": "NA", "track_status": "PROVISIONAL",
            "f_track": "1.0", "new_pollster": "NA", "track_ledger_ref": "NA", "notes": nz((prec or {}).get("notes"), ""),
        }
        rec.update(ov)
        if mid in method_records and method_records[mid]["recall_weighted"] != rec["recall_weighted"]:
            method_conflicts[mid].add(method_records[mid]["recall_weighted"]); method_conflicts[mid].add(rec["recall_weighted"])
            # keep the stronger evidence: a classified record over UNVERIFIED; otherwise keep the first and report
            if method_records[mid]["recall_weighted"] == "UNVERIFIED" and rec["recall_weighted"] != "UNVERIFIED":
                method_records[mid] = rec
        elif mid not in method_records:
            method_records[mid] = rec
        r = method_records[mid]
        return mid, r["recall_weighted"], r["disclosure_status"] if "disclosure_status" in r else disclosure

    for path in files:
        with open(path) as f:
            data = json.load(f)
        race = data.get("race") or os.path.basename(path).replace(".json", "")
        prec_by_pid: dict[str, dict] = {}
        for p in data.get("pollsters") or []:
            pid = pollster_slug(p.get("pollster_name"), None)
            pollster_names.setdefault(pid, p.get("pollster_name") or pid)
            p.setdefault("disclosure_status", p.get("disclosure_status"))
            prec_by_pid[pid] = p
        for q in data.get("quarantine_candidates") or []:
            pid = pollster_slug(q.get("pollster_name"), None)
            exclusions[("POLLSTER", pid)] = {"entity_type": "POLLSTER", "entity_id": pid, "reason": q.get("reason") or QUARANTINE_FIRMS.get(pid, {}).get("reason", "documented fabrication or withdrawal"),
                                             "evidence_url": q.get("evidence_url") or "NA", "evidence_date": q.get("evidence_date") or QUARANTINE_FIRMS.get(pid, {}).get("evidence_date", "NA"), "recorded_at": now}
        polls = data.get("polls") or []
        counts_by_pid = Counter(pollster_slug(p.get("pollster_name"), p.get("members_or_partners")) for p in polls)
        for p in polls:
            pid = pollster_slug(p.get("pollster_name"), p.get("members_or_partners"))
            pollster_names.setdefault(pid, p.get("pollster_name") or pid)
            fs, fe, rd = p.get("field_start"), p.get("field_end"), p.get("release_date")
            if not (fs and fe and rd):
                report.append(f"{race} {pid}: missing dates {fs} {fe} {rd} -> row skipped")
                continue
            sponsor = nz(p.get("sponsor"), "self")
            sponsor_slug = "" if str(sponsor).lower() in ("self", "na", "none", pid) else "-" + slug(str(sponsor))[:24]
            sample_id = f"{pid}-{fs}-{fe}{sponsor_slug}"
            poll_id = f"{sample_id}-{race}"
            pop = enum(p.get("pop"), weight.POPS, "")
            denom = enum(p.get("denominator_class"), weight.DENOMS, "")
            rnd = enum(p.get("round"), weight.ROUNDS, "NA")
            if race in weight.RCV_RACES and rnd == "NA":
                report.append(f"{race} {pid} {fe}: RCV race with round NA -> set FIRST (verify)")
                rnd = "FIRST"
            if race not in weight.RCV_RACES:
                rnd = "NA"
            if not pop or not denom:
                report.append(f"{race} {pid} {fe}: pop={p.get('pop')!r} denominator={p.get('denominator_class')!r} unusable -> row skipped")
                continue
            eid = f"{poll_id}-{pop}-{denom}-{rnd}"
            prec = prec_by_pid.get(pid)
            sole = counts_by_pid[pid] == 1 and len(counts_by_pid) == 1
            mid, recall, disclosure = method_for(pid, prec, fe, sole)
            quarantined = pid in QUARANTINE_FIRMS or ("POLLSTER", pid) in exclusions
            if pid in QUARANTINE_FIRMS and ("POLLSTER", pid) not in exclusions:
                exclusions[("POLLSTER", pid)] = {"entity_type": "POLLSTER", "entity_id": pid, "reason": QUARANTINE_FIRMS[pid]["reason"], "evidence_url": "NA",
                                                 "evidence_date": QUARANTINE_FIRMS[pid]["evidence_date"], "recorded_at": now}
            series = p.get("tracking_series_name")
            tsid = f"TS-{pid}-{race}-{slug(series)[:20]}" if series else "NA"
            notes = nz(p.get("notes"), "")
            excl = "NA"
            if quarantined:
                excl = "QUARANTINE"
            elif p.get("matchup_mismatch"):
                excl = "MATCHUP_MISMATCH"
            row = {
                "estimate_id": eid, "poll_id": poll_id, "sample_id": sample_id, "tracking_series_id": tsid, "race": race, "pollster_id": pid,
                "method_id": "NA" if (quarantined and prec is None) else mid, "sponsor": sponsor, "sponsor_class": enum(p.get("sponsor_class"), weight.SPONSOR_CLASSES, "UNKNOWN"),
                "pollster_alignment": enum(p.get("pollster_alignment"), weight.ALIGNMENTS, "UNKNOWN"), "disclosure_status": disclosure,
                "field_start": fs, "field_end": fe, "release_date": rd, "n": numstr(p.get("n")), "pop": pop, "D": numstr(p.get("D")), "R": numstr(p.get("R")),
                "other": numstr(p.get("other")), "undecided": numstr(p.get("undecided")), "denominator_class": denom, "margin": "NA", "round": rnd, "window": "NA",
                "recall_weighted": recall if not (quarantined and prec is None) else "UNVERIFIED", "selected": "1", "exclusion_reason": excl, "supersedes": "NA", "superseded_by": "NA",
                "source_url": nz(p.get("source_url")), "source_locator": nz(p.get("source_locator")), "retrieved_at": nz(p.get("retrieved_at"), now),
                "notes": (notes + ("" if p.get("verified_on_primary") else " [toplines not confirmed on the primary release; aggregator-only]")).strip(),
            }
            row.update(overrides.get("estimates", {}).get(eid, {}))
            if row["D"] == "NA" or row["R"] == "NA":
                report.append(f"{eid}: D or R missing -> row skipped")
                continue
            poll_rows.append(row)
        for g in data.get("gaps") or []:
            report.append(f"{race} GAP: {g}")

    # duplicates across agents (same estimate_id): keep the first, report
    seen = {}
    deduped = []
    for r in poll_rows:
        if r["estimate_id"] in seen:
            if seen[r["estimate_id"]]["source_url"] != r["source_url"] or seen[r["estimate_id"]]["D"] != r["D"]:
                report.append(f"{r['estimate_id']}: duplicate estimate from two inputs with differing values; kept the first")
            continue
        seen[r["estimate_id"]] = r
        deduped.append(r)
    poll_rows = deduped
    # method records that no selected row references are still kept (every pollster in the registry); fill names
    for m in method_records.values():
        m["pollster_name"] = pollster_names.get(m["pollster_id"], m["pollster_id"])
    for mid, s in method_conflicts.items():
        report.append(f"METHOD CONFLICT {mid}: agents classified {sorted(s)}; kept {method_records[mid]['recall_weighted']}. Resolve by evidence or split into SURVEY records.")

    bundle = a.bundle_dir
    os.makedirs(bundle, exist_ok=True)
    for name, header, rows in (("polls.csv", weight.POLLS_HEADER, poll_rows), ("pollsters.csv", weight.POLLSTERS_HEADER, sorted(method_records.values(), key=lambda m: m["method_id"])),
                               ("exclusions.csv", weight.EXCLUSIONS_HEADER, sorted(exclusions.values(), key=lambda e: (e["entity_type"], e["entity_id"])))):
        path = os.path.join(bundle, name)
        if os.path.exists(path):
            weight.snapshot(path, bundle)
        weight.write_csv(path, header, rows)
    # derive margin, window, selected, exclusion_reason
    b = weight.Bundle(bundle, as_of, rs)
    derived = b.derive_rows(b.polls)
    weight.write_csv(os.path.join(bundle, "polls.csv"), weight.POLLS_HEADER, derived)
    b = weight.Bundle(bundle, as_of, rs)
    ok = b.validate()
    summary = {
        "rows": len(derived), "selected": sum(1 for r in derived if r["selected"] == "1"), "by_window": dict(Counter(r["window"] for r in derived)),
        "by_exclusion": dict(Counter(r["exclusion_reason"] for r in derived if r["selected"] == "0")), "by_race": dict(Counter(r["race"] for r in derived)),
        "method_records": len(method_records), "recall_by_method": dict(Counter(m["recall_weighted"] for m in method_records.values())),
        "exclusion_records": len(exclusions), "validation": "passed" if ok else "FAILED",
    }
    print(json.dumps(summary, indent=2))
    for p in b.problems:
        print("HARD ERROR:", p)
        report.append("VALIDATION: " + p)
    for n in b.notes:
        print("NOTE:", n)
    if a.report:
        with open(a.report, "w") as f:
            f.write("# build_polls report\n\n" + "\n".join(f"- {r}" for r in report) + "\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
