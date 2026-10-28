# swing-test-2010

Backtest inputs for the 2026 swing model, Democratic-president midterm case: the 2010 House result in every district, the 2008 presidential result on the same (2002-2010) lines, and the three national baselines. Collected 2026-10-28. Sign convention everywhere: D minus R, percentage points, positive = Democrat ahead. Built to the rules of `../swing-test-2018/` and `../swing-test-2022/`.

## Files

- `districts2010.csv`: 435 rows, one per district on the lines used in November 2010 (the lines DKE labels "used in 2006, 2008 and 2010").
  - `district`: `ST-NN`, at-large as `ST-AL`. `state`: postal code.
  - `pres2008_d_minus_r`: Obama minus McCain on the 2010 lines, from vote counts where they exist (see Method), else integer shares.
  - `house2010_d_minus_r`: 2010 general, from MEDSL with three line corrections from the Clerk (below). Blank for FL-21, LA-07, OK-04 (unopposed; no votes tabulated).
  - `contested`: `true` when at least one D and one R were on the November ballot. 29 rows are `false` (no D or no R); there were no same-party generals in 2010.
  - `incumbent_party_running`: party of the incumbent on the November ballot (`D`/`R`), `OPEN` if none ran (retired, lost renomination, ran elsewhere, vacant). No `BOTH` rows: there was no incumbent-vs-incumbent race in 2010.
  - `incumbent_name`: the incumbent Wikipedia assigns to the district, whether or not they ran (status is in `notes`); blank for the two vacant seats.
  - `winner_party`: party of MEDSL's top vote-getter (fusion lines summed), checked against Wikipedia's winner marker (no mismatches).
  - `source_pres`, `source_house`: per-row source tags. `notes`: pres vote counts used, caveats, and Wikipedia's incumbent line.
- `baselines.json`: three numeric keys (`pres2008_national_d_minus_r`, `generic_ballot_2010_final_d_minus_r`, `house2010_national_d_minus_r`) plus sources, alternatives and caveats under non-numeric keys.
- `derive_districts2010.py`: rebuilds `districts2010.csv` from `raw/`. Deterministic; a re-run was verified byte-identical (md5 799bdc52d565a1cb90b09fad99bebbb5).
- `raw/`: inputs as downloaded: MEDSL returns, the three tabs of the DKE 2008-on-2006-2010-lines sheet, the DKE 2012 old-vs-new comparison sheet, the Downballot index page, the Swing State Project index page (Wayback) and its 42 per-state worksheets, Wikipedia wikitext, FEC Federal Elections 2008 and 2010 PDFs, the Clerk's 2010 statistics PDF, and the RCP and HuffPost Pollster generic-ballot captures (Wayback).

## Counts

- 435 rows; 406 contested, 29 not; 432 with both margins (the three blanks are the unopposed seats).
- Incumbent on the ballot: D 236, R 156, OPEN 43.
- Incumbents who lost the general: 52 of 236 Democrats (all to Republicans), 2 of 156 Republicans (HI-01 Djou and LA-02 Cao, both to Democrats). This matches Wikipedia's text: "54 incumbents lost in the general election; all but two were Democrats."
- Contested rows with a margin, by incumbent: D 232, R 133, OPEN 41.
- Winners: R 242, D 193 (the 2010 seat result).
- Presidential margin source: DKE vote totals 192 rows, Swing State Project worksheets 230 (212 from vote counts, 18 from 0.01-point shares in MS, NH, NV, TN), DKE integer shares 13 (WA 9, plus IL-12, MS-03, OH-12, OH-15).

## Method

- House margin = (D votes minus R votes) / all valid candidate votes, including write-ins and minor parties. Write-ins count in the denominator only. Fusion lines are summed to the candidate by name (NY Conservative/Working Families/Independence, CT and SC Working Families, including MEDSL's NY Conservative lines coded party `NA`). ND's Democratic-NPL and MN's DFL count as D.
- New York: MEDSL's `BLANK VOTE/SCATTERING` line (248,099 votes statewide, the Clerk's combined "Blank/Scattering") is excluded from the denominator as blank ballots. Wisconsin's line of the same name (1,707 votes, scattering write-ins in the Clerk) is kept, like any write-in.
- MEDSL corrections. Every MEDSL line with 1,000 or more votes was searched for in the Clerk's 2010 statistics; three were not found, and in each the Clerk's figure agrees with Wikipedia's percentages, so the Clerk's count is used: NY-21 Danz Conservative line 25,541 to 15,541 (moves the margin from +13.2 to +18.6), FL-23 Sansaricq 26,804 to 26,414, MN-05 Schrunk (Independence) 7,556 to 7,446. Each is recorded in that row's `notes`. State D and R line totals otherwise match the Clerk exactly, apart from the 1-vote unopposed placeholders and NY's "Democratic, Working Families" combined line that the Clerk files under Other.
- Wikipedia cross-check: 396 of 406 contested rows are within 0.2 pt of Wikipedia's candidate percentages. Four exceed 0.75 pt and are flagged in `notes`: AL-05, CA-48 and NC-04 (MEDSL equals the Clerk; Wikipedia's percentages are off or incomplete) and NY-16 (Wikipedia's shares omit the blank/scattering line differently).
- Presidential margins, in order of preference:
  1. DKE "Vote totals" tab (Obama, McCain, total votes): filled for AK through MA and the at-large states.
  2. For the states that tab leaves blank, the Swing State Project's 2008 per-state worksheets, the data DKE inherited. Where both exist (186 districts), the SSP worksheets reproduce the DKE vote-totals margin to within 0.01 pt, which validates the parser and the lineage. Rhode Island uses SSP's "Soft Total" rows (absentee and limited ballots allocated).
  3. DKE "Results" tab integer shares (margin good to about plus or minus 1): Washington, where SSP links only a Scribd precinct file and no district sum was found, and four districts where the vote-based margin disagrees with the published integers by more than rounding allows (IL-12 12.63 vs 54-44, MS-03 -22.91 vs 38-62, OH-12 9.98 vs 53-46, OH-15 7.12 vs 54-45). DKE's 2012 comparison sheet repeats the same integers, so the published figure is used and the conflict is noted in the row.
- Louisiana: 2010 used closed party primaries (the 2008-2010 interlude), so November was a regular general; LA-07 Boustany was unopposed and not on the ballot.
- Incumbency rule (same as 2018 and 2022): an incumbent counts as running if Wikipedia's status reads "re-elected" or "lost re-election" (either spelling). Lost renomination, all OPEN: AL-05 Griffith (R; elected in 2008 as a Democrat, switched December 2009), MI-13 Kilpatrick (D), SC-04 Inglis (R), WV-01 Mollohan (D).
- FL-25 and FL-21: Mario Diaz-Balart (R, FL-25) ran unopposed in FL-21, where Lincoln Diaz-Balart retired. Both rows are OPEN, since neither district's own incumbent was on its ballot.
- Vacant at election time, OPEN: IN-03 (Souder resigned) and NY-29 (Massa resigned). Members already seated through special elections (for example HI-01 Djou) count as incumbents.

## Baselines

- President 2008: +7.273 (FEC: Obama 69,498,516, McCain 59,948,323, of 131,313,820).
- Generic ballot 2010: -9.4, RealClearPolitics' final "RCP Average" (10/25 to 10/31: R 50.7, D 41.3), read from a Wayback capture of the free RCP page taken 2011-04-30, after the election; no pre-election capture exists. Used because it is the only final average read from a free page. The commonly cited Pollster.com/HuffPost final estimate (about R+6 to R+7) was not verified: the archived Pollster table lists the polls but not the trend estimate. A softer-average model test should treat -9.4 as the high end of the aggregator range.
- House 2010: -6.776, FEC table for the 50 states (delegate rows removed). FEC including delegates: -6.570. Clerk of the House recapitulation: -6.613.

## Unverified or not retrieved

- Pollster.com / HuffPost Pollster's final generic-ballot estimate (trend line was in an unarchived Flash data file); 2010 FiveThirtyEight (on nytimes.com, metered, not fetched). Wikipedia has no 2010 nationwide House polling page.
- Washington's nine presidential margins are integer-based; the WA Secretary of State 2008 export is county-level, and King, Pierce and Snohomish are split.
- Why the DKE vote-totals tab and DKE Results tab disagree for IL-12 (and SSP for OH-12, OH-15, MS-03) was not traced.
- Why FEC and Clerk state totals differ beyond fusion (Indiana: FEC total 1,931,429, Clerk and MEDSL 1,747,720) was not traced.
- The DKE `Incumbent` column names later officeholders and was not used.
- No paywalled source was used or bypassed. RealClearPolitics itself was not fetched; only its archived copy at web.archive.org.
