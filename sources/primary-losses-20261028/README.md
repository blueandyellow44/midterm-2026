# Incumbent primary losses, 2006 to 2026

Built 2026-10-28 for Undertow. One question: is 2026 an unusually anti-incumbent primary year?

## Definition

A sitting member (voting House member or senator) who sought renomination and did not get it: lost the party primary or runoff, lost at a party convention (Bennett 2010, Riggleman 2020), or failed to advance from a top-two or jungle primary (McAllister LA 2014, Herrera Beutler WA 2022). Same-party losses in a top-two GENERAL election are not counted (CA 2012: Stark, Berman, Baca, Richardson; CA 2016: Honda), and neither is a Louisiana December runoff (Landry 2012). Non-voting delegates are excluded (Bordallo, Guam, 2018). `member_vs_member` = the winner was also a sitting member, put in one district by redistricting.

## Result

| cycle | House lost | of which MvM | House excl. MvM | Senate lost | redistricting |
|---|---|---|---|---|---|
| 2006 | 2 | 0 | 2 | 1 | no |
| 2008 | 4 | 0 | 4 | 0 | no |
| 2010 | 4 | 0 | 4 | 3 | no |
| 2012 | 13 | 8 | 5 | 1 | decennial |
| 2014 | 5 | 0 | 5 | 0 | no |
| 2016 | 5 | 1 | 4 | 0 | court-ordered (FL, NC, VA) |
| 2018 | 4 | 0 | 4 | 0 | no |
| 2020 | 8 | 0 | 8 | 0 | no |
| 2022 | 14 | 6 | 8 | 0 | decennial |
| 2024 | 4 | 1 | 3 | 0 | partial (AL) |
| 2026 | 11 | 1 | 10 | 2 | mid-decade (TX, CA Prop 50, others) |

Read: on the like-for-like measure (House losses excluding member-vs-member), 2026's 10 is the highest of the eleven cycles; the prior high was 8 (2020, 2022). Two Senate losses is the most since 2010 (3). Raw House totals in 2012 (13) and 2022 (14) are higher, but those are inflated by redistricting pairings.

## Sources

- Wikipedia, "<YEAR> United States House of Representatives elections" and "<YEAR> United States Senate elections", wikitext fetched 2026-10-28 via `action=raw`; copies in `raw/`. House: "Incumbents defeated > In primary elections" section. Senate: "lost renomination" footnotes and results tables.
- Brookings, Vital Statistics on Congress, Table 2-7 (House) and 2-8 (Senate), April 2026 edition, 1946 to 2024. https://www.brookings.edu/wp-content/uploads/2026/04/2-7-Full.pdf and .../2-8-Full.pdf (copies in `raw/`). Matches Wikipedia in every cycle 2006 to 2024, both chambers.
- Ballotpedia, "United States House of Representatives elections, 2026", Incumbents defeated table, read in Chrome 2026-10-28: 11 primary losers, same names as Wikipedia. Same page's "Races with two incumbents" lists TX-18 (Green/Menefee) and CA-40 (Calvert/Kim).
- `../incumbents-20261027/incumbents.csv`, rows with "lost primary": 12 House, 2 Senate. The extra House row is Everton Blair (GA-13), excluded here (see below).

## Caveats and what was not verified

- Ballotpedia's "Incumbents defeated in ... primaries" pages: the guessed URLs do not exist (curl returns an empty 202; the 2026 URL shows "page does not exist" in a browser). The Congress-level page only gives combined primary+general losses for 1988 to 2024, which cannot be split. So Ballotpedia cross-checks only the 2026 House list.
- 2026 Senate (Cassidy, Cornyn): confirmed by Wikipedia and the incumbents CSV only. Ballotpedia's 2026 Senate page did not return either name in a text search; not verified there.
- 2026 has no Brookings row yet (table runs to 2024).
- Blair (GA-13): he lost the regular-term primary while still a candidate, then won the August 26, 2026 special runoff. He was not a sitting member when he lost, so he is excluded. Including him would make 12.
- Julie Johnson (TX-33) lost to Colin Allred, a former member, not a sitting one, so not MvM.
- CA-40 (Calvert vs Kim): both advanced from the top-two primary. That pairing resolves on November 3 and will not change these primary counts.
- 2016: Brookings' 2017 edition listed 4 House primary losses; its 2026 edition lists 5, matching Wikipedia. Used 5.
- 2018: adding delegate Bordallo gives 5.
- Redistricting flags for 2016, 2024, 2026 come from the Wikipedia entries' own wording ("court order", "redistricting race", "mid-decade redistricting"); no separate map-by-map audit was done.
