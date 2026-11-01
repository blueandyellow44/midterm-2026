# polls-refresh-20261101-senate

Check for NEW public polls in the 14 Senate races (pollster + field dates not in `sources/_in-polls-since-1010-20261101.txt`, field_end on or after 2026-10-10), run Sunday 2026-11-01, 11:45 to 12:55 PST. Free sources only; no paywall bypass, no archive copies. Files follow the shape of `polls-refresh-20261027b/`. Nothing outside this folder was edited; nothing committed.

## Races checked (14)

AK, FL special, GA, IA, KS, ME, MI, MS, NC, NE, NH, OH special, SC, TX.

## Sources read

- Wikipedia raw wikitext (`action=raw`) for all 14 race pages; every general-election row with field_end on or after Oct 10 extracted and compared with the in-polls file. Wikipedia refs used as pointers to primaries only.
- 270toWin 2026 Senate poll pages for 13 states (Mississippi 404); its date column is the publication date.
- PollCheck (pollcheck.co.uk) Senate pages for 12 states, as a cross-check; it surfaced NPA Nebraska Oct 25-29 and the Upswing Michigan poll.
- Primaries: YouGov `ttw_*_20261026_lv.pdf` toplines (8 states); NYT/Siena topline pages (FL, NE, SC; served in full to a plain HTTP fetch); CNN/SSRS state documents on DocumentCloud (KS, ME, MI, TX); Washington Post-Schar School Kansas topline PDF; Data for Progress blog post and filesforprogress tabs PDFs (ME, MI, TX); Marist Maine tables PDF; Emerson Kansas release; co/efficient battlegrounds pages (all 14 states checked; only IA has a new wave); Stetson CPOR wave-3 report; St. Pete Polls PDF (hosted by DDHQ); InsiderAdvantage posts and home page; Palafox/Political Matrix release; Big Data Poll release; Rasmussen state pages (12 states checked; only MI new); Mitchell via sponsor CBS Detroit; MSU Political Science report PDF; High Point University release; Suffolk Ohio marginals and press release; ActiVote state pages (OH, TX new; GA, NC, FL nothing new); Patinkin release and toplines; ECU release; The Citadel PDF; Quantus Texas post and full report (Google Drive); A2 Insights PDF (Google Drive); 254 Labs release; Cor Strategies/Heritage Action crosstabs PDF; NPA Nebraska memo; UMass Lowell press release, topline and methodology PDFs; A Fight Worth Having polling index and state pages; Alaska Survey Research and Demand Justice threads on X via `api.fxtwitter.com`.
- Trafalgar news page (latest is ME Oct 21-23, already held) and Emerson state-poll list (nothing new beyond KS).
- Web searches: GA, MS, TX (Texas Southern), CNN/SSRS, Workbench, UMass Lowell.

Browser use: DocumentCloud (CNN/SSRS), the Washington Post document PDF, MSU, Quantus and KStrat pages were read in a Chrome tab because plain fetches were blocked or the page was script-rendered. The tab was closed when the coordinator asked for no browser use; everything after that was curl/WebFetch.

## Sources that failed

- DocumentCloud and its S3 assets: 403 to curl (read in browser instead).
- washingtonpost.com: no connection from curl (document PDF read in browser; the paywalled article was not read).
- Politico Florida Playbook (Workbench poll): 403 to curl, WebFetch refused. The only other copy cited is a megalodon.jp archive, not used.
- WFAA (Texas Southern): 403 to curl.
- msu.edu release page: Incapsula block to curl (report PDF fetched directly).
- YouGov `ttw_*_20261026` for GA, FL, NH, AK, SC, MS: 403 (no such files).
- AFWH state pages for TX, GA, IA, ME, AK, NE, NH, SC, MS: 404.
- 270toWin and PollCheck Mississippi pages: 404.
- KStrat page is script-rendered; full results sit behind a name/email form (not submitted).

## New polls (49 files)

| race | file | pollster_id | field | n | D | R | other | und | scls | align |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-AK-SEN | ak-sen-alaska-survey-research-2026-10-29-final.json | alaska-survey-research | 10-26 to 10-29 | — LV | 50.8 | 49.2 | — | — | NONPARTISAN | NONE |
| 2026-AK-SEN | ak-sen-alaska-survey-research-2026-10-29.json | alaska-survey-research | 10-26 to 10-29 | 1326 LV | 47.7 | 45.9 | 6.4 | — | NONPARTISAN | NONE |
| 2026-FL-SEN-SPECIAL | fl-sen-big-data-poll-2026-10-30.json | big-data-poll | 10-26 to 10-30 | 1129 LV | 44.7 | 51.6 | — | — | NONPARTISAN | NONE |
| 2026-FL-SEN-SPECIAL | fl-sen-insideradvantage-2026-10-29.json | insideradvantage | 10-28 to 10-29 | 1200 LV | 43 | 49 | 2 | 6 | UNKNOWN | R |
| 2026-FL-SEN-SPECIAL | fl-sen-nyt-siena-2026-10-25.json | nyt-siena | 10-19 to 10-25 | 813 LV | 44 | 50 | 0 | 5 | NONPARTISAN | NONE |
| 2026-FL-SEN-SPECIAL | fl-sen-political-matrix-the-listener-group-2026-10-28.json | political-matrix-the-listener-group | 10-26 to 10-28 | 500 LV | 35.8 | 41.8 | — | 22.4 | UNKNOWN | UNKNOWN |
| 2026-FL-SEN-SPECIAL | fl-sen-redbox-research-2026-10-31.json | redbox-research | 10-30 to 10-31 | 2898 LV | 45 | 48 | 2 | 2 | PARTISAN_PUBLIC | D |
| 2026-FL-SEN-SPECIAL | fl-sen-st-pete-polls-2026-10-27.json | st-pete-polls | 10-25 to 10-27 | 916 LV | 44.7 | 49.0 | 2.6 | 3.7 | NONPARTISAN | NONE |
| 2026-FL-SEN-SPECIAL | fl-sen-stetson-2026-10-30.json | stetson | 10-26 to 10-30 | 861 LV | 45 | 49 | 3 | 3 | NONPARTISAN | NONE |
| 2026-IA-SEN | ia-sen-co-efficient-2026-10-28.json | co-efficient | 10-28 to 10-28 | 1020 LV | 46 | 48 | 1 | 5 | NONPARTISAN | R |
| 2026-IA-SEN | ia-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2020 LV | 50 | 49 | 1 | 0 | NONPARTISAN | NONE |
| 2026-KS-SEN | ks-sen-emerson-2026-10-28.json | emerson | 10-26 to 10-28 | 800 LV | 49 | 45 | 3 | 3 | NONPARTISAN | NONE |
| 2026-KS-SEN | ks-sen-ssrs-2026-10-26.json | ssrs | 10-20 to 10-26 | 838 LV | 49 | 45 | 5 | 0 | NONPARTISAN | NONE |
| 2026-KS-SEN | ks-sen-washington-post-schar-school-2026-10-26.json | washington-post-schar-school | 10-22 to 10-26 | 801 LV | 52 | 43 | 4 | 0 | NONPARTISAN | NONE |
| 2026-KS-SEN | ks-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2092 LV | 50 | 49 | 1 | 0 | NONPARTISAN | NONE |
| 2026-ME-SEN | me-sen-data-for-progress-2026-10-27.json | data-for-progress | 10-23 to 10-27 | 652 LV | 50 | 45 | — | 4 | PARTISAN_PUBLIC | D |
| 2026-ME-SEN | me-sen-marist-2026-10-25-rv.json | marist | 10-22 to 10-25 | 1449 RV | 53 | 44 | 0 | 2 | NONPARTISAN | NONE |
| 2026-ME-SEN | me-sen-ssrs-2026-10-26.json | ssrs | 10-20 to 10-26 | 783 LV | 49 | 45 | 6 | 0 | NONPARTISAN | NONE |
| 2026-ME-SEN | me-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 1503 LV | 52 | 47 | 0 | 0 | NONPARTISAN | NONE |
| 2026-MI-SEN | mi-sen-data-for-progress-2026-10-25.json | data-for-progress | 10-23 to 10-25 | 622 LV | 50 | 46 | 2 | 3 | PARTISAN_PUBLIC | D |
| 2026-MI-SEN | mi-sen-mitchell-2026-10-27.json | mitchell | 10-26 to 10-27 | 636 LV | 51 | 44 | — | 3 | NONPARTISAN | NONE |
| 2026-MI-SEN | mi-sen-msu-political-science-verasight-2026-10-23.json | msu-political-science-verasight | 10-08 to 10-23 | 1383 LV | 48.0 | 41.8 | 3.4 | 6.8 | NONPARTISAN | NONE |
| 2026-MI-SEN | mi-sen-rasmussen-2026-10-29.json | rasmussen | 10-28 to 10-29 | 745 LV | 49 | 44 | 3 | 4 | UNKNOWN | R |
| 2026-MI-SEN | mi-sen-ssrs-2026-10-27.json | ssrs | 10-20 to 10-27 | 768 LV | 49 | 42 | 8 | 1 | NONPARTISAN | NONE |
| 2026-MI-SEN | mi-sen-upswing-research-2026-10-28.json | upswing-research | 10-24 to 10-28 | 505 LV | 50 | 45 | — | — | PARTISAN_PUBLIC | D |
| 2026-MI-SEN | mi-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2093 LV | 51 | 47 | 1 | 1 | NONPARTISAN | NONE |
| 2026-NC-SEN | nc-sen-high-point-2026-10-20.json | high-point | 10-01 to 10-20 | 620 LV | 54 | 40 | 3 | 4 | NONPARTISAN | NONE |
| 2026-NC-SEN | nc-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2130 LV | 55 | 44 | 1 | 1 | NONPARTISAN | NONE |
| 2026-NE-SEN | ne-sen-npa-polling-national-public-affairs-2026-10-29.json | npa-polling-national-public-affairs | 10-25 to 10-29 | 800 LV | 45 | 48 | 4 | 3 | PARTISAN_PUBLIC | R |
| 2026-NE-SEN | ne-sen-nyt-siena-2026-10-29.json | nyt-siena | 10-23 to 10-29 | 809 LV | 43 | 49 | 0 | 8 | NONPARTISAN | NONE |
| 2026-NE-SEN | ne-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 1979 LV | 49 | 49 | 1 | 0 | NONPARTISAN | NONE |
| 2026-NH-SEN | nh-sen-umass-lowell-2026-10-19.json | umass-lowell | 10-02 to 10-19 | 600 LV | 48 | 41 | 4 | 7 | NONPARTISAN | NONE |
| 2026-OH-SEN-SPECIAL | oh-sen-activote-2026-10-31.json | activote | 10-18 to 10-31 | 400 LV | 50.2 | 49.8 | — | — | NONPARTISAN | NONE |
| 2026-OH-SEN-SPECIAL | oh-sen-insideradvantage-2026-10-30.json | insideradvantage | 10-29 to 10-30 | 1200 LV | 49 | 47 | 3 | 1 | UNKNOWN | R |
| 2026-OH-SEN-SPECIAL | oh-sen-suffolk-university-political-research-center-2026-10-26.json | suffolk-university-political-research-center | 10-21 to 10-26 | 500 LV | 46.6 | 43.8 | 3.2 | 4.4 | NONPARTISAN | NONE |
| 2026-OH-SEN-SPECIAL | oh-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2090 LV | 50 | 48 | 2 | 1 | NONPARTISAN | NONE |
| 2026-SC-SEN | sc-sen-east-carolina-university-ecu-center-for-survey-research-2026-10-24.json | east-carolina-university-ecu-center-for-survey-research | 10-19 to 10-24 | 955 LV | 47 | 51 | 2 | — | NONPARTISAN | NONE |
| 2026-SC-SEN | sc-sen-nyt-siena-2026-10-26.json | nyt-siena | 10-19 to 10-26 | 707 LV | 48 | 48 | 0 | 3 | NONPARTISAN | NONE |
| 2026-SC-SEN | sc-sen-patinkin-research-strategies-2026-10-29.json | patinkin-research-strategies | 10-27 to 10-29 | 500 LV | 48 | 43 | 8 | 0 | PARTISAN_PUBLIC | D |
| 2026-SC-SEN | sc-sen-the-citadel-2026-10-25-lv.json | the-citadel | 10-14 to 10-25 | 890 LV | 39 | 43 | 2 | 15 | NONPARTISAN | NONE |
| 2026-SC-SEN | sc-sen-the-citadel-2026-10-25-rv.json | the-citadel | 10-14 to 10-25 | 1009 RV | 40 | 35 | 3 | 20 | NONPARTISAN | NONE |
| 2026-TX-SEN | tx-sen-a2-insights-2026-10-27.json | a2-insights | 10-23 to 10-27 | 631 LV | 50.2 | 47.2 | 2.3 | 0.3 | UNKNOWN | UNKNOWN |
| 2026-TX-SEN | tx-sen-activote-2026-10-28.json | activote | 10-22 to 10-28 | 400 LV | 52.1 | 47.9 | — | — | NONPARTISAN | NONE |
| 2026-TX-SEN | tx-sen-cor-strategies-2026-10-15.json | cor-strategies | 10-10 to 10-15 | 1409 LV | 44 | 40 | — | 16 | PARTISAN_PUBLIC | R |
| 2026-TX-SEN | tx-sen-data-for-progress-2026-10-26.json | data-for-progress | 10-23 to 10-26 | 712 LV | 49 | 45 | 2 | 4 | PARTISAN_PUBLIC | D |
| 2026-TX-SEN | tx-sen-quantus-2026-10-28.json | quantus | 10-26 to 10-28 | 1221 LV | 47.6 | 48.7 | 1.4 | 2.2 | UNKNOWN | R |
| 2026-TX-SEN | tx-sen-ssrs-2026-10-27.json | ssrs | 10-20 to 10-27 | 923 LV | 49 | 43 | 8 | 0 | NONPARTISAN | NONE |
| 2026-TX-SEN | tx-sen-yougov-2026-10-29.json | yougov | 10-26 to 10-29 | 2141 LV | 51 | 47 | 1 | 1 | NONPARTISAN | NONE |
| 2026-TX-SEN | tx-sen-yougov-blue-254-labs-2026-10-26.json | yougov-blue-254-labs | 10-21 to 10-26 | 1000 LV | 51 | 43 | — | 5 | PARTISAN_PUBLIC | D |

Counts by race: AK 1 poll (2 files: first round and final round), FL 7, GA 0, IA 2, KS 4, ME 4, MI 7, MS 0, NE 3, NH 1, NC 2, OH 4, SC 4 (5 files: Citadel LV and RV), TX 8.

Notes on choices:

- **Alaska**: ASR gets two files, `-2026-10-29.json` (round 1, FULL) and `-2026-10-29-final.json` (final round, TWO_WAY), because polls.csv carries FIRST and FINAL rows for each Alaska poll. Weighting text is ASR's house statement from its Oct 1-3 thread; this wave's thread does not restate it.
- **Marist Maine RV**: the in-polls key (pollster + dates) matches the Marist LV row already held, but the RV sample (1,449 RV, 53-44) was never recorded. Filed with `-rv` to complete the pair, as Marist RV rows exist for IA, MI, OH and TX.
- **YouGov 8-state wave** (Oct 26-29): same undated "ttw" series as the YouGov rows already in polls.csv; sponsor not named in the PDFs; release date taken from the 270toWin listing (11/01). recall_weighted YES (imputed 2024 presidential vote).
- **Secondary-only or thin sourcing, recorded with flags in notes**: Upswing Research Michigan (numbers only in the sponsor's X thread, no document); Mitchell Michigan (sponsor CBS Detroit's article, no Mitchell release found); Big Data Poll Florida (release does not say whether the 51.6-44.7 headline is LV or RV; recorded LV as the firm's convention, flagged); 254 Labs Texas (1,000 RV interviewed, weighted to LV targets and reported "among likely voters"; recorded LV).
- **RedBox Florida Oct 30-31** is a new fresh sample (n=2,898), separate from the held Oct 20-23 poll. The page says its party and 2024-vote weighting targets were set after fieldwork and after seeing earlier results; that is in the notes.
- **MSU Political Science/Verasight** (Smidt, Oct 8-23) is a different poll from the MSU IPPSR/YouGov State of the State poll already held. Headline recorded is the MRP initial-response estimate (48.0-41.8); the weighted-survey and leaner variants are in notes.
- **Cor Strategies Texas** (Oct 10-15, Heritage Action) was never in polls.csv; inside the window, so included.

## Seen but not written

- **KStrat (Kreate Strategies) Texas**, Oct 27-30, 900 LV, Talarico 48, Paxton 45: filed separately by the main session in `sources/polls-refresh-20261101-kstrat/`.
- **Texas Southern University Texas**, Oct 21-25 per Wikipedia/270toWin, 2,000 LV: only a WFAA news report found (Talarico 49, Paxton 47, Brown 3, undecided 1; released Oct 29). No TSU release or PDF found, and WFAA gives neither n nor field dates. Excluded as secondary-only; re-check for a TSU/Texas Tribune PDF.
- **Workbench Strategy Florida** (D; PollCheck says commissioned by Nixon's campaign), Oct 18-22, 800 LV, Moody 49, Nixon 47: only source is Politico Florida Playbook (blocked) and an archive copy (not used). Excluded.
- **Wedgewood Polls Mississippi**, Oct 12-14, 511 LV, Hyde-Smith 52, Colom 48: Newsweek has retracted its article on it, stating that Wedgewood Polls has said its results were fabricated. Excluded. (Wedgewood rows already in polls.csv for other races may deserve the same review.)
- **Univision/YouGov Florida**, Oct 2-15: party-named Senate item, skipped in earlier bundles for the same reason.
- **UMass Lowell/YouGov Texas** (Sep 18-28) and **Trafalgar Georgia** (Oct 7-9): out of window.
- **"Siena College" Ohio, 500 LV, 47-44 on 270toWin (10/28)**: this is the Suffolk/USA TODAY poll, mislabeled; filed as Suffolk.
- **Maine People's Resource Center "Oct 26-29" (search snippet, Collins vs. Platner)**: matchup is not the 2026 general; looks like a stale 2025 item. Not pursued.
- Every other October row on Wikipedia, 270toWin and PollCheck matched a poll already in the in-polls file.

## Secondary-only (could not confirm at a pollster or sponsor document)

- Texas Southern Texas (excluded, above).
- Upswing Michigan is sourced to the sponsor's own X thread, not a document; written, with that flagged in notes.
