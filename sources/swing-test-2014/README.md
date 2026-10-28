# swing-test-2014

Backtest inputs for the 2026 swing model, Democratic-president midterm case: the 2014 House result in every district, the 2012 presidential result on the same (2014) lines, and the three national baselines. Purpose: test whether the president's party's House incumbents (Democrats in 2014) lost their personal incumbency advantage. Collected 2026-10-28. Sign convention everywhere: D minus R, percentage points, positive = Democrat ahead. Built to the rules of `../swing-test-2018/` and `../swing-test-2022/`.

## Files

- `districts2014.csv`: 435 rows, one per district on the lines used in November 2014.
  - `district`: `ST-NN`, at-large as `ST-AL`. `state`: postal code.
  - `pres2012_d_minus_r`: Obama minus Romney, on the 2014 lines (Daily Kos Elections / The Downballot; shares rounded to 0.1, so the margin is good to about 0.1).
  - `house2014_d_minus_r`: 2014 general, from MEDSL (LA-05 and LA-06 from Wikipedia, see below). Blank for FL-12, FL-14, FL-25, FL-27 and OK-01 (unopposed; no votes tabulated).
  - `contested`: `true` when at least one D and one R were on the November ballot. Same-party top-two races (CA-04, CA-17, CA-19, CA-25, CA-34, CA-35, CA-40, WA-04), same-party Louisiana primaries (LA-02, LA-03) and races with no D or no R are `false`.
  - `incumbent_party_running`: party of the incumbent on the November ballot (`D`/`R`), `OPEN` if none ran (retired, lost renomination, vacant). No `BOTH` rows in 2014 (no incumbent-vs-incumbent general).
  - `incumbent_name`: the incumbent Wikipedia assigns to the district, whether or not they ran (status is in `notes`); blank for the three vacant seats.
  - `winner_party`: party of MEDSL's top vote-getter (fusion lines summed), checked against Wikipedia's winner marker (no mismatches).
  - `source_pres`, `source_house`: per-row source tags. `notes`: caveats plus Wikipedia's incumbent line.
- `baselines.json`: three numeric keys (`pres2012_national_d_minus_r`, `generic_ballot_2014_final_d_minus_r`, `house2014_national_d_minus_r`) plus sources and caveats under non-numeric keys.
- `derive_districts2014.py`: rebuilds `districts2014.csv` from `raw/`. Deterministic; a re-run was verified byte-identical.
- `raw/`: inputs as downloaded: MEDSL returns, the Downballot 2012/2014-lines sheet export (plus the 2016-lines sheet, used only for the line-change check), Wikipedia wikitext, FEC Federal Elections 2012 and 2014 PDFs, the Clerk's 2014 statistics PDF, and the RCP and HuffPost Pollster Wayback captures.

## Counts

- 435 rows; 358 contested, 77 not; 430 with both margins (the five blanks are the unopposed FL/OK seats).
- Incumbent on the ballot: R 205, D 182, OPEN 48.
- Of the 182 D incumbents, 11 lost to Republicans: AZ-02 Barber, FL-26 Garcia, GA-12 Barrow, IL-10 Schneider, IL-12 Enyart, NH-01 Shea-Porter, NV-04 Horsford, NY-01 Bishop, NY-24 Maffei, TX-23 Gallego, WV-03 Rahall. Of the 205 R incumbents, 2 lost to Democrats: FL-02 Southerland, NE-02 Terry. These 13 are exactly the district rows Wikipedia marks "Incumbent lost re-election".
- Contested rows with a margin, by incumbent: R 173, D 143, OPEN 42.
- Winners: R 247, D 188.

## Method

- House margin = (D votes minus R votes) / all valid candidate votes, including write-ins and minor parties. Write-ins count in the denominator only; MEDSL's `OTHER` rows (MA, ME, OR scattered write-ins) are treated the same way. Excluded as non-votes: blank, void, over/under-vote rows, including 2014's spellings `BLANK VOTE`, `OVER VOTE` and New York's `BLANK VOTE/VOID VOTE/SCATTERING` (New York reports scattered write-ins combined with blanks, so they cannot be separated; they are excluded, a small denominator effect).
- Fusion lines are summed to the candidate by name (NY, CT, SC-05); in MEDSL 2014 every fusion line carries its candidate, so no line attributions were needed. Multiple same-party candidates are summed. MN's DFL and ND's Democratic-Nonpartisan League count as D. NJ's "D-R Party" is a minor party, not D or R.
- Every contested MEDSL row was cross-checked against Wikipedia's candidate percentages: 346 of 356 agree within 0.2 pt, the largest unflagged gap is CT-03 at 0.37. Five rows are flagged in `notes` (over 0.75 pt) and MEDSL is kept: CA-43 (Wikipedia lists only Waters 71.0% and omits the Republican, John Wood Jr.; MEDSL has both), UT-01 (1.6 pt), UT-02 (1.1), KS-01 (0.9), OR-03 (0.8).
- Louisiana: the November open primary is the general, as in the siblings. LA-05 and LA-06 went to December 6 runoffs (both won by Republicans, Abraham and Graves). MEDSL's rows for those two seats mix rounds: the two runoff candidates carry their December totals (Abraham 134,616 to Mayo 75,006 = 64.2%, Graves 139,209 to Edwards 83,781 = 62.4%, matching the runoff shares Wikipedia lists) while every other candidate carries November totals, so November shares cannot be computed from MEDSL. Both rows use Wikipedia's November shares, summed by party: LA-05 D 28.2 vs R 70.2 = -42.0; LA-06 D 34.5 vs R 64.1 = -29.6. Winner is R in both.
- Incumbency rule (same as siblings): an incumbent counts as running if Wikipedia's status reads "re-elected" or "lost re-election". Lost renomination, all OPEN: LA-05 McAllister, MA-06 Tierney, MI-11 Bentivolio, TX-04 Hall (and Cantor, VA-07, who then resigned).
- Vacant at election time, all OPEN, each with a same-day special the winner also won: NC-12 (Watt resigned January 6, 2014), NJ-01 (Andrews resigned February 18, 2014), VA-07 (Cantor resigned August 18, 2014). MEDSL's 2014 file has only the regular general rows, which are used. Special-election winners already seated count as incumbents (FL-13 Jolly and FL-19 Clawson in 2014; AL-01, IL-02, LA-05, MA-05, MO-08, SC-01 in 2013).
- Lines: no state redrew between the 2012 and 2014 elections. The Downballot sheet is labeled "district lines used in 2012 and 2014", and its 2012 columns equal the 2016-lines sheet's 2012 columns everywhere except Florida, North Carolina and Virginia (redrawn by court order for 2016; they were on their 2012 maps in 2014).

## Baselines

- President 2012: +3.860 (FEC, Obama 51.06% to Romney 47.20%).
- Generic ballot 2014: -2.4, RealClearPolitics' final average (poll window 10/15 to 11/2: R 45.6, D 43.2), read from a Wayback capture of the free RCP page taken 2014-11-06, two days after the election; the average covers only pre-election polls. Alternative recorded: HuffPost Pollster's estimate, D 44.0 to R 45.8 = -1.8, from its only pre-election capture (2014-11-01, missing the final weekend's polls). FiveThirtyEight had no generic average in 2014.
- House 2014: -5.783, Clerk of the House recapitulation, 50 states (R 39,926,526, D 35,368,840, total 78,812,769). Unlike the 2018 sibling, the FEC table is not the headline: it adds the NJ-01, NC-12 and VA-07 same-day specials and Louisiana's December runoffs, and it transposes Nevada's Republican and Other columns. As published it gives -5.330 (50 states); corrected, it reproduces the Clerk within 8 D and 4,995 R votes. Neither source sums fusion lines to candidates (New York D 1,788,105 in both), so the national figure is slightly less favorable to the fusion-endorsed side than a district sum would be.

## Unverified or not retrieved

- realclearpolitics.com / realclearpolling.com itself was not fetched (it blocks scripted fetches); only the 2014 Wayback capture was read.
- HuffPost Pollster's election-eve estimate was not retrieved: the Wayback Machine has no capture between 2014-11-01 and the election, and its CDX index was offline during collection.
- The Indiana gap between the FEC and Clerk Republican totals (793,759 vs 788,762) was not traced.
- Why Utah, Kansas-01 and Oregon-03 differ between MEDSL and Wikipedia by about 1 pt was not traced (likely different canvass versions).
- The Downballot sheet's `Incumbent` column reflects later officeholders (for example Mooney in WV-02) and was not used.
- No paywalled source was used or bypassed.
