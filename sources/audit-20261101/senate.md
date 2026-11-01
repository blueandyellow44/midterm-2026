# Senate refresh audit, 2026-11-01

Adversarial audit of `sources/polls-refresh-20261101-senate/`: 49 JSON files plus README.md, folder as of Sunday 2026-11-01 ~13:05 PST. Every source_url was re-fetched by curl (no browser). Counts: **CONFIRMED 33 / REFUTED 8 / CANNOT-VERIFY 8**.

Checks run on every file:
- **Duplicates:** each file was compared with `_in-polls-since-1010-20261101.txt` by race, pollster and field dates. None matches a held row. Marist ME shares pollster and dates with the held LV row, but its population is RV. No file duplicates another in the folder, and none duplicates the kstrat folder.
- **Window:** every field_end is 2026-10-15 or later.
- **Sponsor class:** checked against the existing rows for the same pollster in `data/polls.csv`. That file is byte-identical to the vault copy at `Second Brain V2/Resources/methods/midterm-2026/polls.csv`.

## Verdicts

| file | verdict | discrepancy or evidence |
|---|---|---|
| ak-sen-alaska-survey-research-2026-10-29.json | CONFIRMED | fxtwitter tweet 1/10: Oct 26-29, N=1,326 LV. Tweet 2/10, round 1: 47.7 / 45.9 / DJS Jr 3.4 / Heikes 3.0. |
| ak-sen-alaska-survey-research-2026-10-29-final.json | CONFIRMED (fix n) | Tweet 3/10, final round: 50.8 / 49.2. This is not a separate poll. The vault polls.csv carries FIRST and FINAL rows sharing one sample_id for 4 AK samples (DFP, InsiderAdvantage, ASR Oct 1-3, ASR Sep 10-12). `weight.py` V2_RCV_ROUND="FIRST" keeps FINAL rows out of the v2 average, so there is no double count. Keep the file. Fixes: set n=1326 (the precedent ASR FINAL rows carry the full-sample n), and merge it with the same poll_id/sample_id as the FIRST file. Drop it only if the coordinator wants first-round rows alone. |
| fl-sen-big-data-poll-2026-10-30.json | REFUTED (class) | Toplines confirmed: 51.6 / 44.7 leaned; 1201 RV / 1129 LV; Oct 26-30. The release names "1776 Law Center and Public Polling Project". Recorded NONPARTISAN/NONE, but 17 of 25 existing big-data-poll rows are PARTISAN_PUBLIC/R. Fix: scls PARTISAN_PUBLIC, align R. The LV population is still an inference (the release does not label the headline). |
| fl-sen-insideradvantage-2026-10-29.json | REFUTED (class) | Toplines confirmed: 49 / 43 / 2 / 6, 1200 LV, 10/28-10/29. Recorded sponsor null and UNKNOWN, but every existing InsiderAdvantage row is sponsor "self", align R, and 9 of 11 are PARTISAN_PUBLIC. UNKNOWN weighs 0.6; self weighs 1.0. Fix: sponsor "self", scls PARTISAN_PUBLIC. |
| fl-sen-nyt-siena-2026-10-25.json | CANNOT-VERIFY | nytimes.com returns 403 to curl and WebFetch. |
| fl-sen-political-matrix-the-listener-group-2026-10-28.json | CONFIRMED | Moody 41.8, Nixon 35.8, 22.4 undecided. "500 recorded responses from likely Florida voters", Oct 26-28. LV is correct. The undecided share is real. |
| fl-sen-redbox-research-2026-10-31.json | CONFIRMED | 48 / 45; Gillespie 1, someone else 1, undecided 2. 2,898 LV, Oct 30-31, AFWH sponsor. Class matches existing RedBox rows. |
| fl-sen-st-pete-polls-2026-10-27.json | CONFIRMED | PDF: 49.0 / 44.7 / 2.6 / 3.7, 916 LV, Oct 25-27. |
| fl-sen-stetson-2026-10-30.json | CONFIRMED | 49 / 45, 3 undecided, 3 other. 861 RV modeled to likely voters, Oct 26-30. Table n is 859; minor. |
| ia-sen-co-efficient-2026-10-28.json | CONFIRMED (align) | 48 / 46 / 1 / 5, 1,020 LV, Oct 28. Sponsor class differs from the gov file for the same sample and from the prior IA-SEN wave (both "self", PARTISAN_PUBLIC). The weight is unaffected; align for consistency. |
| ia, ks, me, mi, nc, ne, oh, tx -sen-yougov-2026-10-29.json (8) | CONFIRMED (class ruling) | All 8 PDFs checked. D/R/other/undecided match. Each n is per state: 2020, 2092, 1503, 2093, 2130, 1979, 2090, 2141. All are LV, Oct 26-29. Flag: the gov folder classes the same IA/MI/OH samples UNKNOWN, and existing ttw rows are split (IA/MI/OH UNKNOWN; KS/NE/TX/FL/NH NONPARTISAN). The weight is 0.6 vs 1.0. One sample needs one class; this needs a ruling. |
| ks-sen-emerson-2026-10-28.json | CONFIRMED | 49 / 45 / 3 / 3, n=800 LV, Oct 26-28. |
| ks-sen-ssrs-2026-10-26.json | CANNOT-VERIFY | DocumentCloud returns 403 (page, API and WebFetch). |
| ks-sen-washington-post-schar-school-2026-10-26.json | CANNOT-VERIFY | washingtonpost.com: curl gets no connection; WebFetch gets 403. |
| me-sen-data-for-progress-2026-10-27.json | CONFIRMED | Q[2]: 50 / 45 / 4, N=652 LV, Oct 23-27. |
| me-sen-marist-2026-10-25-rv.json | CONFIRMED | SNVT26R, registered voters: 53 / 44 / <1 / 2. 1,449 RV. Distinct from the held LV row (49 / 47). Merge it into the LV row's sample_id. |
| me-sen-ssrs-2026-10-26.json | CANNOT-VERIFY | DocumentCloud returns 403. |
| mi-sen-data-for-progress-2026-10-25.json | CONFIRMED | 50 / 46; other 1+1+<0.5+0; 3 not sure. N=622, Oct 23-25. |
| mi-sen-mitchell-2026-10-27.json | CONFIRMED (secondary flag) | The CBS Detroit article gives 51 / 44 / 3, 636 LV, Oct 26-27. Sponsor reporting only; there is no Mitchell document. |
| mi-sen-msu-political-science-verasight-2026-10-23.json | REFUTED (id) | Report MRP: 48.0 / 41.8 / 3.4 / 6.8, 1,383, Oct 8-23. The gov file for the same sample uses pid `verasight`. Fix: one pid and one sample_id across both files (recommend `verasight`, sponsor MSU, matching the gov file). |
| mi-sen-rasmussen-2026-10-29.json | REFUTED (class) | 49 / 44, 745 LV, Oct 28-29, confirmed. Same fix as InsiderAdvantage: existing Rasmussen rows are sponsor "self"/R, so use "self", PARTISAN_PUBLIC. |
| mi-sen-ssrs-2026-10-27.json | CANNOT-VERIFY | DocumentCloud returns 403. |
| mi-sen-upswing-research-2026-10-28.json | CONFIRMED (secondary flag) | Josh Orton thread: "Upswing - Oct 24-28, N505, LV", El-Sayed 50-45. The only source is the sponsor's X thread; there is no document. |
| nc-sen-high-point-2026-10-20.json | CONFIRMED | 54 / 40; Dublin 1 + Bray 2; 4 unsure. LV n=620, Oct 1-20. The pid matches the existing high-point rows. |
| ne-sen-npa-polling-national-public-affairs-2026-10-29.json | CONFIRMED | Memo: Ricketts 48, Osborn 45, minor-party 4, undecided 3. n=800 LV, Oct 25-29, leaners included. Class matches the prior NE NPA rows. |
| ne-sen-nyt-siena-2026-10-29.json | CANNOT-VERIFY | NYT returns 403. |
| nh-sen-umass-lowell-2026-10-19.json | REFUTED (pid) | 48 / 41 / 4 / 7, N=600 LV, Oct 2-19. The topline says "YouGov interviewed 695 respondents" matched to 600. The existing UMass Lowell polls (ME, TX) are pid `yougov` with sponsor UMass Lowell. Fix: pid `yougov`, sponsor "UMass Lowell Center for Public Opinion". |
| oh-sen-activote-2026-10-31.json | CONFIRMED | 50.2 / 49.8, 400 LV, Oct 18-31. |
| oh-sen-insideradvantage-2026-10-30.json | REFUTED (class) | 49 / 47 / 3 / 1, 1200 LV, 10/29-10/30, confirmed. Fix: sponsor "self", PARTISAN_PUBLIC. |
| oh-sen-suffolk-university-political-research-center-2026-10-26.json | CONFIRMED | Marginals Q7: 46.60 / 43.80; Levy 1.6 + Redpath 1.6; undecided 4.4. N=500. Press release: Oct 21-26 LV. |
| sc-sen-east-carolina-university-...-2026-10-24.json | CONFIRMED | 51 / 47, 2 other, 955 LV, Oct 19-24. |
| sc-sen-nyt-siena-2026-10-26.json | CANNOT-VERIFY | NYT returns 403. |
| sc-sen-patinkin-research-strategies-2026-10-29.json | REFUTED (class) | q8: 48 / 43 / 3 / 3 / 2 / 0, n=500, Oct 27-29, confirmed. The release says Project VOTE is "an independent expenditure organization that supports Dr. Annie Andrews". The same-race precedent (Fresh Start SC, a pro-Andrews super PAC) is INTERNAL. The weight.py rule says a PAC internal counts 0.3. Fix: scls INTERNAL. Counter-precedent: the KY-06 and SC-01 candidate-PAC rows are PARTISAN_PUBLIC; existing data is inconsistent. |
| sc-sen-the-citadel-2026-10-25-lv.json | CONFIRMED | Q12 LV: 39 / 43 / 1 / 1 / 15, 890 LV, Oct 14-25. |
| sc-sen-the-citadel-2026-10-25-rv.json | CONFIRMED | Q12 RV: 40 / 35 / 1 / 2 / 20 / not voting 2, 1,009 RV. |
| tx-sen-a2-insights-2026-10-27.json | CONFIRMED | Drive PDF: 50.2 / 47.2 / 2.3 / 0.3, 631 LV, 10/23-10/27, "Sponsor: N/A". |
| tx-sen-activote-2026-10-28.json | CONFIRMED | 52.1 / 47.9, 400 LV, Oct 22-28. |
| tx-sen-cor-strategies-2026-10-15.json | CONFIRMED | Talarico 44, Paxton 40, undecided 16. 1,409 LV, Oct 10-15. "Heritage Action paid for all costs". PARTISAN_PUBLIC/R with a non-self sponsor gives the 0.6 tier, which is correct. |
| tx-sen-data-for-progress-2026-10-26.json | CONFIRMED | 49 / 45 / 2 / 4, N=712, Oct 23-26. |
| tx-sen-quantus-2026-10-28.json | REFUTED (class) | Drive report: 48.7 / 47.6 / 1.4 / 2.2, 1,221 LV, Oct 26-28, confirmed. Recorded UNKNOWN, but recent Quantus rows are sponsor "self", PARTISAN_PUBLIC/R. Fix to match. |
| tx-sen-ssrs-2026-10-27.json | CANNOT-VERIFY | DocumentCloud returns 403. |
| tx-sen-yougov-blue-254-labs-2026-10-26.json | CONFIRMED | 51 / 43 / 5. 1,000 RV interviewed, weighted to LV targets, Oct 21-26. |

## Specific checks

- **(a) Alaska ranked-choice voting.** The claim that the existing data keeps FIRST and FINAL rows is verified in the vault polls.csv. The -final file is a companion estimate, not a second poll. Keep it, with the fix above.
- **(b) Political Matrix.** Confirmed.
- **(c) Marist Maine RV.** Confirmed.
- **(d) Citadel LV and RV.** Both confirmed.
- **(e) Cor Strategies.** The sponsor class is correct.
- **(f) Patinkin.** Refuted; recorded at 0.6 where the same-race precedent gives 0.3.
- **(g) YouGov per-state numbers.** Confirmed; the sponsor class is inconsistent with the gov folder.

## Secondary-only sources

- Upswing: sponsor's X thread only.
- Mitchell: sponsor's article only.
- Big Data Poll: the release's own population is ambiguous.

## Side note

NYT existing rows split between selecting FULL (ME, MI, TX) and LEANERS (OH, IA). The three new NYT files record only the LEANERS row; the initial ask is in their notes if a FULL row is wanted.
