# Election-night workflow

How Undertow enters results and grades itself against the polls, written after the 2026 midterm (Nov 3 to 7, 2026) so the next election runs from this page, not from memory. Everything here is a shell command; no browser.

## The rules the code enforces

- **Entry rule.** A race goes on the board once AP shows 50% of votes counted or an AP call. Shares are percent of ALL votes cast for the office (D + R + other = 100); `--reporting` is AP's "% of votes counted" (eevp). Never estimate.
- **Shares come from the state's official count where the state posts one** (`fetch_official.py`). Where a state posts no live count (in 2026: WI, NJ, NH, ME, MS; AL posted nothing on the night), the row uses AP's count and the page labels it "AP count". Maine and Alaska enter from the FIRST-round count (`--round FIRST`), the basis of their polling averages.
- **Settle rule** (`lib/live.ts`, `analysis/weight.py`): a race joins the tally once it is called AND 80%+ counted, or 95%+ counted either way. A call at 37% counted is mostly early vote.
- **A called race is not a finished count.** Every round re-reads every race whose count can still move, called ones included (Ohio Senate sat at +2.1 for four hours in 2026 because called rows were skipped).
- **The grade** (the `derived` block in `live/results.json`): for each settled race with polls, the polls' error and Undertow's error against the counted margin; the averages, the closer-count, and the implied national miss. A race with no polls settles on the board but never enters the grade.
- **Calls against Undertow are computed, never recalled**: the called side in `live/results.json` against the sign of `signals.per_race[race].adjusted_margin` in `data/derived.json` (`round_report.py`).

## The feeds

| Source | What | Script |
|---|---|---|
| AP | `https://interactives.apelections.org/election-results/data-live/<election date>/results/races/<ST>/metadata.json` (races, candidates, call status) and `.../<raceKey>/summary.json` (votes, winner `X`, eevp). Gzipped. A browser user-agent is required (CloudFront returns 403 otherwise). | `fetch_ap.py` |
| Clarity ENR states (SC, IA, CO in 2026) | `https://results.enr.clarityelections.com/<ST>/<id>/current_ver.txt`, then `<ver>/json/en/summary.json`. Contest names can carry double spaces. | `fetch_official.py` |
| North Carolina | `https://er.ncsbe.gov/enr/<YYYYMMDD>/data/results_0.txt` (JSON, `gid` per contest) | `fetch_official.py` |
| Other states | The official pages found on the night are listed in the project memory file `reference-election-night-official-pages.md`. Wire them into `fetch_official.py` before the next election instead of reading them in a browser. | |

AP's own pages render from these feeds; the pages are never the source. The addresses were found by reading the page's `_astro` bundles for `data-live` URLs. Python needs its certificate bundle installed (`/Applications/Python 3.x/Install Certificates.command`), or use `curl --compressed` in a subprocess.

## A round

```
python3 scripts/live/apply_round.py                   # feeds -> set_result.py for every race whose numbers moved
scripts/live/publish.sh "Live results: round HHMM"    # vitest (exit code gates), commit, build, deploy, byte-check
python3 scripts/live/round_report.py                  # grade line, calls against Undertow, % counted going down, leader flips
```

`apply_round.py --dry` prints what would change without writing. `set_call.py <ballot id> --winner D|R --source <AP url>` records an AP call for a ballot race with no official count; it feeds `/ballot/` only, never the grade. Slugs are the race id with `2026-` removed and lowercased (`2026-OH-SEN-SPECIAL` becomes `oh-sen-special`). Independents in the D slot (Osborn, Hill) are named in `fetch_ap.py` (`D_SLOT_NAME`) and `analysis/weight.py` (`PARTISAN_INDEPENDENT_D`).

Landing: on election night 2026, results committed to local main and deployed from it, with GitHub synced by PR afterwards (branch protection refused direct pushes). From Nov 4 results go by PR like everything else: branch, round, the `ci` check, merge on Max's word, deploy from main. One session runs rounds and deploys; two builds in one checkout collide on `.next`.

## Lessons carried into this page (Tasks/lessons.md, 2026-11-04)

1. Repeated collection runs on the source's feed, not on a rendered page; re-pick the transport the second time a job repeats.
2. A called race is not a finished count; a status flag decides scoring, never whether a row refreshes.
3. A test run gates a deploy by its exit code, never through `grep` or a trailing `echo` (`publish.sh` exists because of this).
4. "No official page" is a claim that needs a search and the SOS home page checked, not one stale site (Texas 2026).
5. Never say "every call matches" without computing it; two calls against Undertow went unreported for three hours in 2026.
