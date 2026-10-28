# swing-test-2018

Backtest inputs for the 2026 swing model, Republican-president midterm case: the 2018 House result in every district, the 2016 presidential result on the same (2018) lines, and the three national baselines. Collected 2026-10-28. Sign convention everywhere: D minus R, percentage points, positive = Democrat ahead. Built to the rules of `../swing-test-2022/`.

## Files

- `districts2018.csv`: 435 rows, one per district on the lines used in November 2018 (including Pennsylvania's court-ordered 2018 map).
  - `district`: `ST-NN`, at-large as `ST-AL`. `state`: postal code.
  - `pres2016_d_minus_r`: Clinton minus Trump, on the 2018 lines (Daily Kos Elections / The Downballot; shares rounded to 0.1, so the margin is good to about 0.1).
  - `house2018_d_minus_r`: 2018 general, from MEDSL (ME-02 from Wikipedia, see below). Blank for FL-10, FL-14, FL-21, FL-24 (unopposed; Florida tabulates no votes).
  - `contested`: `true` when at least one D and one R were on the November ballot. Same-party top-two races (CA-06, CA-08, CA-27, CA-44, WA-09) and races with no D or no R are `false`.
  - `incumbent_party_running`: party of the incumbent on the November ballot (`D`/`R`), `OPEN` if none ran (retired, lost renomination, vacant, new seat), `BOTH` where incumbents of opposite parties met (PA-17, Lamb vs Rothfus).
  - `incumbent_name`: the incumbent(s) Wikipedia assigns to the district, whether or not they ran (status is in `notes`); blank for vacant and new seats.
  - `winner_party`: party of MEDSL's top vote-getter (fusion lines summed), checked against Wikipedia's winner marker; blank for NC-09.
  - `source_pres`, `source_house`: per-row source tags. `notes`: caveats plus Wikipedia's incumbent line.
- `baselines.json`: three numeric keys (`pres2016_national_d_minus_r`, `generic_ballot_2018_final_d_minus_r`, `house2018_national_d_minus_r`) plus sources and caveats under non-numeric keys.
- `derive_districts2018.py`: rebuilds `districts2018.csv` from `raw/`. Deterministic; a re-run was verified byte-identical.
- `raw/`: inputs as downloaded: MEDSL returns, the Downballot sheet export, Wikipedia wikitext, FEC Federal Elections 2016 and 2018 PDFs, the Clerk's 2018 statistics PDF, and the 538 generic-ballot page capture.

## Counts

- 435 rows; 394 contested, 41 not; 431 with both margins (the four blanks are the Florida unopposed seats).
- Incumbent on the ballot: R 198, D 172, BOTH 1, OPEN 64. Of the R incumbents, 29 lost to Democrats (30 with Rothfus in PA-17, matching Wikipedia's count). No D incumbent lost.
- Contested rows with a margin, by incumbent: R 195, D 136, OPEN 62, BOTH 1.
- Winners: D 235, R 199, NC-09 blank.

## Method

- House margin = (D votes minus R votes) / all valid candidate votes, including write-ins and minor parties. Write-ins count in the denominator only. Fusion lines are summed to the candidate by name (NY, CT); unlike 2022, MEDSL 2018 has no fusion lines recorded without a candidate, so no line attributions were needed. Multiple same-party candidates are summed. ND's Democratic-NPL and MN's DFL count as D; AK's Galvin (Democratic nominee, ballot label Undeclared) counts as D.
- Every contested row was cross-checked against Wikipedia's candidate percentages; the largest gap is IL-03 at 0.51 pt, all others are under 0.2 pt.
- Louisiana: the November open primary is the general (MEDSL has it as the general; no 2018 House runoffs).
- Maine ME-02 (ranked-choice): first-round shares from Wikipedia, Golden 45.6 to Poliquin 46.3 = -0.7, as the 2022 sibling did. MEDSL lists only Golden 139,231 and Poliquin 136,326 against a totalvotes field of 281,371 and omits Bond and Hoar, so first-round shares cannot be computed from it. Winner is D (Golden won the instant runoff).
- Pennsylvania: both inputs are on the court-ordered 2018 map (the Downballot sheet's PA-01 is Clinton +2.0, the new Bucks County seat). Incumbents follow Wikipedia's "Redistricted from" assignments, recorded in `notes`. PA-04 and PA-14 are new seats; PA-05 (Meehan) and PA-07 (Dent) were vacant; PA-17 is the one incumbent-vs-incumbent race.
- Incumbency rule (same as 2022): an incumbent counts as running if Wikipedia's status reads "re-elected" or "lost re-election". One override: NY-14, where Crowley lost the Democratic primary and appeared only on the Working Families line; recorded as OPEN, since no incumbent was on a D or R line.
- Vacant at election time, all OPEN: FL-06, MI-13, NY-25, OK-01, PA-05, PA-07, WV-03. Special-election winners already seated (e.g. AZ-08, TX-27, Lamb from PA-18) count as incumbents.
- NC-09: the November count (Harris R by 905 votes, -0.32) was never certified because of absentee-ballot fraud; the seat stayed vacant until a 2019 election. The margin is kept as tabulated, `winner_party` is blank, incumbency is OPEN (Pittenger lost renomination).

## Baselines

- President 2016: +2.099 (FEC).
- Generic ballot 2018: +8.612, FiveThirtyEight's 'All polls' average for 2018-11-06 (D 50.657, R 42.045, shown rounded as 50.7 to 42.0, i.e. D+8.7), read from a Wayback capture of the free 538 page taken on Election Day before polls closed. Unlike the 2022 sibling, this is a pre-election capture.
- House 2018: +8.834, FEC table for the 50 states (delegate rows removed). The FEC total including delegates is +8.983; the Clerk of the House recapitulation gives +8.641. The FEC figure is the headline value because the district rows sum fusion lines to candidates, as the sibling did.

## Unverified or not retrieved

- RealClearPolitics' final generic average (about D+7.3) was not retrieved: RealClearPolling returns 403 to scripted fetches.
- The Wikipedia page "Nationwide opinion polling for the 2018 United States House of Representatives elections" no longer exists (404 on 2026-10-28), so it was not used.
- Why the Clerk's and FEC's state totals differ beyond fusion (for example PA D 2,712,665 vs 3,016,286) was not traced.
- The Downballot sheet's `Incumbent` column reflects later officeholders (e.g. Meuser, Murphy) and was not used; its unlabeled trailing columns were ignored.
- No paywalled source was used or bypassed.
