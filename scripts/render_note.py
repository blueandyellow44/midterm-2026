#!/usr/bin/env python3
"""Fill the method note's RESULTS_* placeholders from a release's derived.json. Formatting only; no arithmetic.

Usage: python3 scripts/render_note.py --release-dir <releases/<id>> --note <vault note> [--ledger <coverage-ledger.md>] [--deferred <deferred.md>]
The note is snapshotted to .backups/ before the in-place edit (ROE 14). Placeholders are replaced from a template copy kept at
<note>.template.md the first time this runs, so a later release re-renders from the template, never from a previous render.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
import weight  # noqa: E402

FRAME = "> Descriptive only. This number does not identify the effect of recalled-vote weighting or its mechanism; mode, timing, recruitment, screens, targets, nonresponse, pollster effects and selective publication remain confounded."


def f(v, nd=1, unit=""):
    if v is None:
        return "NA"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int,)) and not isinstance(v, bool):
        return str(v)
    try:
        return f"{float(v):+.{nd}f}{unit}" if unit == " pt" else f"{float(v):.{nd}f}{unit}"
    except (TypeError, ValueError):
        return str(v)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def section5(d):
    c = d["section5_contrasts"]
    rows = []
    for key, label in (("i", "(i) pooled, all strata"), ("ii", "(ii) race-balanced, contrast strata"), ("iii", "(iii) as (ii), nonpartisan/bipartisan sponsors"), ("iv", "(iv) as (i), LV and modal denominator")):
        x = c[key]
        races = x.get("races_included", x.get("races", []))
        rows.append([label, f(x["value"], 2, " pt") if x["value"] is not None else "NA", x.get("n_yes", "") if "n_yes" in x else "", x.get("n_no", "") if "n_no" in x else "",
                     x.get("independent_waves", ""), ", ".join(races) or "none", x["status"] if x["value"] is None else (x.get("note") or "")])
    t = table(["Contrast", "YES minus NO (D margin, pts)", "YES est.", "NO est.", "Indep. waves", "Races", "Status or note"], rows)
    per = []
    for race, v in c["per_race"].items():
        if v.get("yes_minus_no") is not None:
            per.append([race, f(v["yes_minus_no"], 2, " pt"), v["n_yes"], v["n_no"], f"{v['stratum']['round']}/{v['stratum']['denominator_class']}/{v['stratum']['pop']}"])
        else:
            per.append([race, "NA", "", "", v.get("reason", "")])
    t2 = table(["Race", "YES minus NO", "YES", "NO", "Contrast stratum or reason"], per)
    return f"UNVERIFIED principal estimates in the BOTH window, counted and excluded from every contrast: **{c['unverified_count']}**.\n\n{t}\n\n{FRAME}\n\nPer race (TX, IA, ME, AK, OH-SPECIAL, MI), within the contrast stratum:\n\n{t2}\n\n{FRAME}"


def section6(d):
    g = d["section6_gov_sen_gaps"]
    rows = []
    for state in ("IA", "OH", "MI", "GA"):
        b = g[state]
        if b["pairs"]:
            for p in b["pairs"]:
                rows.append([state, p["pollster_id"], p["sample_id"], f"{p['pop']}/{p['denominator_class']}/{p['round']}", f(p["governor_margin"], 1, " pt"), f(p["senate_margin"], 1, " pt"), f(p["gap"], 1, " pt")])
        else:
            rows.append([state, "", "", "", "", "", "NA: " + b["status"]])
    current = table(["State", "Pollster", "Sample", "Stratum", "Governor D margin", "Senate D margin", "Gap (gov minus Sen)"], rows)
    old = g.get("_comparators_2022", {})
    historical = []
    for r in old.get("records", []):
        sources = f"[Governor]({r['governor']['source_url']}) / [Senate]({r['senate']['source_url']})"
        historical.append([r["state"], f(r["governor_result"]["margin"], 2, " pt"), f(r["senate_result"]["margin"], 2, " pt"), f(r["gap"], 2, " pt"), sources])
    return current + "\n\n2022 November general-election comparators. " + old.get("note", "Illustration, not benchmark.") + "\n\n" + table(["State", "Governor D margin", "Senate D margin", "Gap", "Primary returns"], historical) + "\n\nGeorgia uses an unprocessed archive of the official state export, plus the state's qualified write-in certificate. Nevada uses an archived copy of its official Supreme Court canvass. Ohio and New Hampshire use current official PDF returns. Source locators, vote counts and provenance are frozen in derived.json."


def section7(d):
    rows = []
    for race, b in d["races"].items():
        strat = b["averaging_stratum"]
        rows.append([race, f"{strat['round']}/{strat['denominator_class']}/{strat['pop']}" if strat else "NA", b["retained_count"], b["excluded_count"], f(b["retained_weight"], 3),
                     f(b["preliminary_unweighted_margin"], 1, " pt"), f(b["weighted_margin"], 1, " pt") if b["weighted_margin"] is not None else "not yet computed",
                     f(b["no_cutoff_margin"], 1, " pt") if b["no_cutoff_margin"] is not None else "NA", "yes" if b["rcv_first_round_fallback"] else ""])
    note = "Weighted margins are heuristic, track-record stand-in values (Section 1) once Stage 2c passes; until then the preliminary column is an unweighted mean of the averaging stratum."
    return table(["Race", "Averaging stratum", "Retained", "Excluded (cutoff or flag)", "Retained weight", "Preliminary unweighted D margin", "Weighted D margin", "No-cutoff sensitivity", "RCV FIRST fallback"], rows) + "\n\n" + note


def section9(d):
    h = d["section9_heat"]
    rows = []
    for race, b in h["per_race"].items():
        cd, cr = b["candidates"]["D"], b["candidates"]["R"]
        rows.append([race, f"{cd['candidate'] or 'D'} {f(cd['DEBATE']['mean'], 2)} (n={cd['DEBATE']['n']})", f"{cr['candidate'] or 'R'} {f(cr['DEBATE']['mean'], 2)} (n={cr['DEBATE']['n']})",
                     (f(b["debate_gap"]["gap"], 2) + f" ({b['debate_gap']['hotter']})") if b["debate_gap"]["gap"] is not None else "undefined",
                     f"{f(cd['AD']['mean'], 2)} (n={cd['AD']['n']}) vs {f(cr['AD']['mean'], 2)} (n={cr['AD']['n']})",
                     (f(b["ad_gap"]["gap"], 2) + f" ({b['ad_gap']['hotter']})") if b["ad_gap"]["gap"] is not None else "undefined",
                     ", ".join(b["debate_caption_sources"]) or "none", ", ".join(f"{k} {v}" for k, v in sorted(b["unit_counts"].items()))])
    t = table(["Race", "D debate mean", "R debate mean", "Debate gap (D minus R)", "Ad means D vs R (exploratory)", "Ad gap (exploratory)", "Debate captions", "Units by status"], rows)
    rep = h["replay_1_recommendation"]
    rep_line = f"**Replay 1 recommendation:** {rep['race']} (absolute debate gap {f(rep['abs_debate_gap'], 2)}; {rep['rule']})." if rep else "**Replay 1 recommendation:** none yet; no in-scope debate has a defined gap with BROADCASTER or OFFICIAL captions."
    return f"Units scored: {h['units_scored']}; by status: {h['units_by_status']}; spend ${h['spend_usd']:.2f} of the ${h['budget_ceiling_usd']:.2f} ceiling. Races with a defined debate gap: {', '.join(h['races_with_defined_debate_gap']) or 'none'}. A difference under {h['tie_threshold']} is a TIE.\n\n{t}\n\n{rep_line}\n\nThe meter scores how something is said, never the position taken; persuasive is not hyperbolic. Ad readings are exploratory: the meter was validated on debate answers and historical speeches, not ads."


def section10(d):
    rows = [[c["expected_edition"], c["race"], c["returned_edition"], c["edition_status"], c["match_status"], c["story_count"], c["outlet_count"], c["ph_low"], c["ph_high"], c["spread"], c["calmest_outlet"], c["hottest_outlet"]] for c in d["section10_coverage"]]
    if not rows:
        return "No coverage call has been recorded yet."
    return table(["Expected edition", "Race", "Returned edition", "Edition status", "Match", "Stories", "Outlets", "P/H low", "P/H high", "Spread", "Calmest outlet", "Hottest outlet"], rows) + "\n\nDescriptive context from the LITMUS paper's edition; no claim that coverage heat predicts anything. Automated reading of the writer's framing, not a verdict on any person or outlet."


def section2a(d):
    b = d["section2a_backtest"]
    if not b:
        return "Not yet run (Stage 2)."
    rows = []
    for race, s in b["by_state"].items():
        rows.append([race, s["n"], f(s["certified_margin"], 1, " pt"), f(s["mean_signed_error"], 2, " pt"),
                     f"{s['groups']['YES']['n']} / {f(s['groups']['YES']['mean_signed_error'], 2, ' pt')}", f"{s['groups']['NO']['n']} / {f(s['groups']['NO']['mean_signed_error'], 2, ' pt')}",
                     f"{s['groups']['UNVERIFIED']['n']} / {f(s['groups']['UNVERIFIED']['mean_signed_error'], 2, ' pt')}", f(s["yes_minus_no"], 2, " pt"), f(s["one_final_poll_per_firm"]["yes_minus_no"], 2, " pt")])
    t = table(["Race", "Polls", "Certified D margin", "Mean signed error", "YES n / mean", "NO n / mean", "UNVERIFIED n / mean", "YES minus NO", "One final poll per firm"], rows)
    return f"Status: {b['status']}. {b['sign_convention']}.\n\n{t}\n\nWithin-state YES minus NO averaged equally across states with both groups: **{f(b['within_state_yes_minus_no_equal_average'], 2, ' pt')}** (states: {', '.join(b['states_with_both_groups']) or 'none'}); one-final-poll-per-firm sensitivity **{f(b['one_final_poll_per_firm_sensitivity'], 2, ' pt')}**. {b['framing'].capitalize()}. {b.get('missing_contrast_reason', '')}"


def section2b(d):
    data = d.get("section2b_turnout")
    if not data:
        return "Not yet run (Stage 2)."
    rows = []
    for year, summary in data["years"].items():
        for method, group in summary["methods"].items():
            for party, value in group["parties"].items():
                rows.append([year, method, party, f"{value['accepted_ballots']:,}", f(value["share_pct"], 2) + "%", f"{group['accepted_ballots']:,}"])
    times = "\n\n".join(f"**{year}**: [official file]({summary['source_url']}), source Last-Modified {summary['source_last_modified']}; latest accepted return date {summary['latest_accepted_return_date']}; {summary['duplicate_accepted_rows_removed']} repeated accepted rows removed; {summary['conflicting_accepted_identities_excluded']} ambiguous identities excluded from every method total. SHA-256 `{summary['file_sha256']}`." for year, summary in data["years"].items())
    return data["note"] + "\n\n" + table(["Year", "Method", "Registration code", "Accepted ballots", "Share within method", "Method denominator"], rows) + "\n\n" + times + f"\n\nRetrieved {data['retrieved_at']}. [Official layout]({data['layout_url']}); [identifier definitions]({data['identity_source']}). " + data["deduplication"] + "\n\n**Poll comparison: not comparable.** " + data["poll_comparison"]["harper_locator"] + f" [Harper questionnaire]({data['poll_comparison']['harper_source']}). " + data["poll_comparison"]["surveyusa_locator"]


def ratings(d, registry):
    source = d.get("rating_source")
    if not source:
        return "Track-record import not yet completed."
    firms = {p["pollster_id"]: p for p in registry}
    rows = [[p["pollster_name"], p["track_status"], f(p["rating_value"], 2), p["rating_poll_count"], p["f_track"], f(p["rating_bias_value"], 2)] for _, p in sorted(firms.items())]
    return f"[Silver Bulletin source]({source['source_url']}), {source['version_label']}; file `{source['file_name']}`, downloaded {source['downloaded_at']}, SHA-256 `{source['sha256']}`. Metric **Simple Average Error**, percentage points; cohort **{source['cohort']}**. Mean-Reverted Bias is descriptive only.\n\n" + table(["Firm or partnership", "Status", "Simple Average Error", "Historical polls", "Track factor", "Mean-Reverted Bias"], rows) + "\n\nSparse histories are unstable; a one-poll history is not reliable evidence of persistent quality. Unmatched or incompatible identities retain PROVISIONAL 1.0, which is not an endorsement. Partner ratings are not borrowed. Publisher ban flags and identity reasons remain in each method record's notes; the threshold rule itself does not substitute for the integrity quarantine. No historical bias correction is applied. The project's threshold factors have not been shown to outperform a simple average."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-dir", required=True)
    ap.add_argument("--note", default=weight.DEFAULT_NOTE)
    ap.add_argument("--ledger")
    ap.add_argument("--deferred")
    ap.add_argument("--section2b")
    ap.add_argument("--template", help="Explicit versioned template; the original remains preserved")
    ap.add_argument("--active", action="store_true", help="Candidate active note only when all Stage 2 data gates passed")
    a = ap.parse_args()
    with open(os.path.join(a.release_dir, "derived.json")) as fh:
        d = json.load(fh)
    # Keep the original render source as a preserved snapshot, not an orphan
    # second method note beside the canonical report.
    template = a.template or os.path.join(os.path.dirname(a.note), "midterm-2026", ".backups", "method-template-20261025.txt")
    if not os.path.exists(template):
        shutil.copyfile(a.note, template)
    with open(template, encoding="utf-8") as fh:
        t = fh.read()
    rel = d.get("release_id") or os.path.basename(a.release_dir.rstrip("/"))
    registry_path = os.path.join(a.release_dir, "pollsters.csv")
    registry = weight.read_csv(registry_path, weight.POLLSTERS_HEADER) if os.path.exists(registry_path) else []
    repl = {
        "RELEASE_ID_PLACEHOLDER": rel,
        "RESULTS_REGISTRY_PLACEHOLDER": table(["Pollster", "Method ID", "Recall class", "Applicability", "Primary method evidence"], [
            [p["pollster_name"], p["method_id"], p["recall_weighted"], p["applicability"], f"{p['method_url']} ({p['method_locator']})".replace("|", " / ")]
            for p in sorted(registry, key=lambda p: p["method_id"])
        ]),
        "RESULTS_SECTION5_PLACEHOLDER": section5(d),
        "RESULTS_SECTION6_PLACEHOLDER": section6(d),
        "RESULTS_SECTION7_PLACEHOLDER": section7(d),
        "RESULTS_SECTION9_PLACEHOLDER": section9(d),
        "RESULTS_SECTION10_PLACEHOLDER": section10(d),
        "RESULTS_SECTION2A_PLACEHOLDER": section2a(d),
        "RESULTS_SECTION2B_PLACEHOLDER": open(a.section2b, encoding="utf-8").read().strip() if a.section2b and os.path.exists(a.section2b) else section2b(d),
        "RESULTS_RATINGS_PLACEHOLDER": ratings(d, registry),
        "RESULTS_SECTION11_PLACEHOLDER": open(a.ledger, encoding="utf-8").read().strip() if a.ledger and os.path.exists(a.ledger) else "Ledger pending.",
        "DEFERRED_RUNTIME_PLACEHOLDER": open(a.deferred, encoding="utf-8").read().strip() if a.deferred and os.path.exists(a.deferred) else "",
    }
    for k, v in repl.items():
        t = t.replace(k, v)
    t = t.replace("analytical_as_of PLACEHOLDER", d["analytical_as_of"])
    if a.active:
        if not all(d.get("stage_status", {}).get(stage) == "PASSED" for stage in ("stage2a", "stage2b", "stage2c")):
            raise weight.ValidationError("an active candidate note requires every Stage 2 data gate")
        t = t.replace("status: draft", "status: active", 1)
    weight.snapshot(a.note, os.path.dirname(a.note) + "/midterm-2026")
    with open(a.note, "w", encoding="utf-8") as fh:
        fh.write(t)
    left = [k for k in repl if k in t]
    print(f"rendered {a.note} from release {rel}; unreplaced placeholders: {left or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
