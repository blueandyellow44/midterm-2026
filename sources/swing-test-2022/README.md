# swing-test-2022

Backtest inputs for the 2026 swing model: the 2022 House result in every district, the 2020 presidential result on the same (2022) lines, and the three national baselines. Collected 2026-10-27.

## Files

- `districts2022.csv`: 435 rows, one per district.
  - `district`: `ST-NN`, at-large as `ST-AL`.
  - `pres2020_d_minus_r`: Biden minus Trump, percentage points, on the 2022 district lines (The Downballot; shares rounded to 0.1).
  - `house2022_d_minus_r`: D minus R, percentage points, 2022 general (MEDSL). Blank for FL-05 and LA-04 (unopposed, no votes tabulated).
  - `contested`: `true` when at least one D and one R were listed on the November ballot. Same-party top-two races (CA, LA) and unopposed seats are `false`.
  - `incumbent_party_running`: party of the incumbent on the November ballot (`D`/`R`), `OPEN` if none ran (retired, lost primary, vacant, new seat), `BOTH` where two incumbents of opposite parties met (FL-02, TX-34).
  - `source_note`: per-row caveats and the incumbent line from Wikipedia.
- `baselines.json`: three numeric keys (`pres2020_national_d_minus_r`, `generic_ballot_2022_final_d_minus_r`, `house2022_national_d_minus_r`) plus sources and caveats under non-numeric keys.
- `derive_districts2022.py`: rebuilds `districts2022.csv` from `raw/`. Deterministic; output verified byte-identical to the shipped file.
- `raw/`: the three inputs as downloaded (MEDSL returns, Downballot sheet export, Wikipedia wikitext). Provenance URLs in `baselines.json`.

## Method

- House margin = (D votes minus R votes) / all valid candidate votes, including write-ins and minor parties. Blank, void, over/under-vote and exhausted-ballot rows are excluded. Write-in votes count in the denominator but not toward a party.
- Fusion lines are summed to the candidate (NY by candidate name). In CT-01, CT-04, CT-05 and NY-21 MEDSL lists the line without a candidate; those votes are attributed as Wikipedia's totals attribute them, and the result matches Wikipedia within 0.1 pt.
- Multiple same-party candidates on one ballot are summed.
- Ranked-choice races use first-round shares. AK-AL from MEDSL (Peltola vs Palin + Begich). ME-02 from Wikipedia (48.4 to 44.6) because the MEDSL rows mix rounds.
- Every contested row was cross-checked against Wikipedia's percentages. The only gap above 1 pt is NJ-08 (MEDSL +50.18, Wikipedia +48.7); MEDSL kept, noted in the row. Other gaps are under one point and come from write-in handling.
- Incumbent status is Wikipedia's assignment of 2022 incumbents to the new lines.
- National House vote is the FEC table minus the five delegate races (DC, GU, AS, MP, VI); the FEC's published total including them is also recorded.
- Generic ballot is FiveThirtyEight's Election Day average, recovered from a post-election Wayback capture; see the caveat in `baselines.json`.
