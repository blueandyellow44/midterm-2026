# Polling-read coverage correction

Goal: give each race a truthful public polling read without changing locked weighted-average eligibility. Done: all current races show either their qualifying average or a clearly labeled latest primary-verified poll, with dates, population and source; no unverified or quarantined record can become a fallback.
Affected files: analysis/weight.py, focused regression tests, RaceOverview/Race page display, bundle validation, explicit new method template/release, run-state, hub/tasks/Daily and verification evidence. No current CSV fact is changed unless independently established on a primary source.
Dependencies: existing immutable Stage 2 bundle, original primary releases, installed local production stack, Cloudflare deploy authorization, browser controls.
Failure modes: absent or ambiguous LV sample size stays unknown and cannot enter an average; stale/adult/single-poll evidence is labeled and never relabeled as a likely-voter average; source/round uncertainty and quarantine prohibit fallback; any integrity or CSP failure stops deployment.
Verification: empty/malformed/unknown-primary/quarantined cases first; deterministic latest-poll choice and RCV round separation; unchanged weighted margins/eligibility compared with prior release; all 13 current public reads; production build/tests and local/live browser/headers.
Rollback: snapshots before edits, immutable new correction release with supersedes/reason, preserve previous Cloudflare version. No push, domain binding or lessons write.
