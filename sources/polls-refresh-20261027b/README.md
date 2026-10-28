# polls-refresh-20261027b

Check for NEW public polls (pollster + field dates not already in `Resources/methods/midterm-2026/polls.csv`, field_end on or after 2026-10-10) across the 19 statewide Undertow races, run 2026-10-27 ~17:30 PDT. Free sources only; no paywall bypass; no browser (WebFetch + curl of public pages). WebSearch was unavailable this session (budget exhausted), so discovery rests on the aggregators and primary sites below.

## Races checked (19)

Senate: AK, FL special, GA, IA, KS, ME, MI, MS, NC, NE, NH, OH special, SC, TX.
Governor: GA, IA, MI, OH, WI.

## Sources read

- 270toWin 2026 Senate polls pages for all 14 Senate states and 2026 Governor polls pages for GA, IA, MI, OH, WI (Mississippi Senate page returned 404). Note: 270toWin's date column is the publication date, not field dates.
- Wikipedia raw wikitext (`action=raw`) for all 19 race pages; general-election polling rows with October 2026 field_end >= 10 extracted and compared to polls.csv.
- NetChoice / Echelon Insights topline PDF (`NetChoice-October-2026-Antitrust-Tech-Survey-Topline.pdf`) and release page, for state ballot questions and methodology.
- A Fight Worth Having (RedBox Research) polling index, state pages (Ohio, Michigan, North Carolina), per-state methodology pages, and `/polling/how-we-poll`. State pages tried and 404: georgia, iowa, texas, maine, wisconsin, new-hampshire, nebraska, alaska, south-carolina, mississippi (Kansas and Florida were captured in the earlier bundle `polls-new-senate-20261027`).
- Sibling bundles consulted to avoid duplicates: `polls-refresh-20261027` (Marist ME, Glengariff MI x2, Univision/YouGov TX), `polls-refresh-20261027-wi` (Marquette Sept wave, YouGov/CFC, Z to A), `polls-new-senate-20261027` (Echelon FL/NE, RedBox FL/KS, etc.).
- RealClearPolling not used (403 to scripted fetches). RaceToTheWH and VoteHub poll listings returned 404/403.

## New polls found (12 files)

Echelon Insights / NetChoice multistate survey, fielded 2026-10-16 to 10-23, released 2026-10-27 (FL and NE oversamples were already captured in `polls-new-senate-20261027`; these are the remaining four states):

| file | race | n | D | R | other | und |
|---|---|---|---|---|---|---|
| ga-sen-echelon-insights-2026-10-23.json | 2026-GA-SEN | 508 LV | Ossoff 55 | Collins 40 | 3 | 2 |
| ga-gov-echelon-insights-2026-10-23.json | 2026-GA-GOV | 508 LV | Bottoms 49 | Jackson 48 | 0 | 3 |
| ia-sen-echelon-insights-2026-10-23.json | 2026-IA-SEN | 403 LV | Turek 45 | Hinson 43 | 9 | 3 |
| ia-gov-echelon-insights-2026-10-23.json | 2026-IA-GOV | 403 LV | Sand 50 | Lahn 46 | 0 | 3 |
| me-sen-echelon-insights-2026-10-23.json | 2026-ME-SEN | 413 LV | Jackson 51 | Collins 44 | 1 | 4 |
| oh-sen-echelon-insights-2026-10-23.json | 2026-OH-SEN-SPECIAL | 508 LV | Brown 47 | Husted 47 | 4 | 3 |
| oh-gov-echelon-insights-2026-10-23.json | 2026-OH-GOV | 508 LV | Acton 45 | Ramaswamy 47 | 4 | 3 |

RedBox Research / A Fight Worth Having (D super PAC), fielded 2026-10-20 to 10-23, released 2026-10-25. Not in polls.csv; the 11:41 PDT refresh today could find only an X post for Ohio, and the primary pages were confirmed in this pass. Release date is 10-25, not today; included because the NEW rule is pollster + field dates absent from polls.csv.

| file | race | n | D | R | other | und |
|---|---|---|---|---|---|---|
| oh-sen-redbox-research-2026-10-23.json | 2026-OH-SEN-SPECIAL | 2,998 LV | Brown 46.9 | Husted 44.2 | 4.4 | 4.4 |
| oh-gov-redbox-research-2026-10-23.json | 2026-OH-GOV | 2,998 LV | Acton 48.2 | Ramaswamy 43.8 | 5.0 | 3.1 |
| mi-sen-redbox-research-2026-10-23.json | 2026-MI-SEN | 2,696 LV | El-Sayed 48.9 | Rogers 44.0 | 4.2 | 2.9 |
| mi-gov-redbox-research-2026-10-23.json | 2026-MI-GOV | 2,696 LV | Benson 48.6 | James 42.8 | 4.8 | 3.8 |
| nc-sen-redbox-research-2026-10-23.json | 2026-NC-SEN | 3,292 LV | Cooper 49.8 | Whatley 43.5 | 3.8 | 3.0 |

All 12 confirmed at the pollster's own release (topline PDF or AFWH state page); none is secondary-only. RedBox `recall_weighted` = YES per the house statement ("to the certified 2024 presidential result, using respondents' reports of their 2024 vote"). Echelon `recall_weighted` = NO (weighting dimensions listed; no recalled vote). Pollster ids and method_id pattern follow `pollsters.csv` (`echelon-insights`, `redbox-research`).

Caveat on RedBox weighting quotes: the Ohio and North Carolina `weighting_quote` fields are the fetch tool's close paraphrase of the per-state methodology page (the page could not be read verbatim without a browser); the Michigan quote and the `/polling/how-we-poll` house statement are verbatim.

## Per-race result

| race | new polls |
|---|---|
| AK-SEN | 0 (DFP 10/8-16, PPP 10/14-15, IA 10/9-10 all recorded) |
| FL-SEN special | 0 (Echelon, RedBox, ActiVote 10/27, co/efficient, UNF all recorded) |
| GA-SEN | 1 (Echelon) |
| IA-SEN | 1 (Echelon) |
| KS-SEN | 0 |
| ME-SEN | 1 (Echelon) |
| MI-SEN | 1 (RedBox) |
| MS-SEN | 0 (Change Research 10/21-22 recorded) |
| NC-SEN | 1 (RedBox) |
| NE-SEN | 0 (Echelon NE already captured) |
| NH-SEN | 0 |
| OH-SEN special | 2 (Echelon, RedBox) |
| SC-SEN | 0 (Targoz 10/16-25 recorded) |
| TX-SEN | 0 (Univision/YouGov 10/13-21 captured in sibling bundle) |
| GA-GOV | 1 (Echelon) |
| IA-GOV | 1 (Echelon) |
| MI-GOV | 1 (RedBox) |
| OH-GOV | 2 (Echelon, RedBox) |
| WI-GOV | 0 (Marquette final wave releases 2026-10-28) |

## Seen but not written

- 270toWin lists "YouGov 10/20, 560 LV, Cooper 54 Whatley 43" for NC. This is the Elon University/YouGov poll (Sep 29 to Oct 8, n=561) already recorded as `elon`; 270toWin's two-way rounding differs from Wikipedia's full-ballot row (52-39). Not a new poll.
- Washington Post/Schar School Maine (270toWin, published 10/09, 800 LV, Jackson 50 Collins 46): field dates not shown on 270toWin and the Wikipedia Oct-10+ extract does not include it, so field_end is before 2026-10-10. Out of window; not verified at a primary.
- Quantus Insights Alaska (270toWin 10/02) and James Madison Institute Florida (270toWin 10/09): publication dates before 10/10, field dates earlier. Out of window.
- Univision/YouGov Florida (Oct 2-15, 825 RV, 51-42): party-named Senate item, not a named matchup; skipped in the earlier bundle for the same reason.
- RedBox Research also published Kansas governor, Florida governor, Arizona governor and Nevada governor statewide results in the same wave; none is an Undertow race.
- Marquette Law School Wisconsin final wave: WisPolitics notice says release Wednesday 2026-10-28. Re-run then.

## Secondary-only (could not confirm at a primary source)

None.
