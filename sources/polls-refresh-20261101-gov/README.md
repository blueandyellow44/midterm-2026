# polls-refresh-20261101-gov

Check for NEW public polls in the five Undertow governor races (GA, IA, MI, OH, WI), run Sunday 2026-11-01, 12:00 to 12:15 PST. NEW = pollster + field dates absent from `sources/_in-polls-since-1010-20261101.txt`, field_end on or after 2026-10-10. Free sources only; no paywall bypass. Scripted fetches (curl) for public pages; Max's Chrome (one tab, closed after) only for two pages behind bot walls (MSU news page, CNN/SSRS DocumentCloud text).

## Sources read

- Wikipedia raw wikitext (`action=raw`) for all five `2026_<State>_gubernatorial_election` pages; general-election polling rows extracted and compared to the held list.
- 270toWin 2026 governor polls pages for all five states (publication dates, used as a cross-check).
- Primaries: YouGov LV reports `ttw_{ia,oh,mi}_20261026_lv.pdf`; State Navigate GA article + briefing PDF; co/efficient Senate Battlegrounds Iowa page + index; Mitchell Research press-releases page + 10-29 governor PDF; CNN/SSRS Michigan October toplines (DocumentCloud text layer, read in browser); Data for Progress blog + `dfp_2026_mi_ge_tabs.pdf`; MSU Political Science news page (browser) + `MI_2026_pre_election_report.pdf`; Suffolk/USA TODAY Ohio marginals PDF; ActiVote poll pages (OH, GA; IA/MI/WI pages 404) + polls index; Wick/League of American Workers WI results page (embedded JSON); Marquette MLSP92 press release + MLSP92Methodology.pdf.
- Discovery checks: A Fight Worth Having (RedBox) state pages (GA/IA/WI still 404; MI/OH unchanged, 10/20-23 wave already held); Emerson state-polls index (latest in-scope is Iowa Oct 5-6, out of window); co/efficient index (only Iowa new); WebSearch for "<state> governor poll" in each state.

## Sources that failed

- `polisci.msu.edu` news page: Incapsula bot wall to curl and WebFetch; read in browser. The report PDF fetched directly.
- DocumentCloud page/API/S3: Cloudflare 403 to curl; text read in browser.
- Wick page: client-rendered; numbers read from the embedded `WICK_PACKET_DATA` JSON.
- No weighting statement found for Suffolk (marginals only) or Wick (page says only "Weight Variable").

## New polls (14 files)

| file | race | pollster (sponsor) | field | n | D | R | scls | recall |
|---|---|---|---|---|---|---|---|---|
| ga-gov-state-navigate-2026-10-27.json | GA | State Navigate (self) | 10/23-27 | 679 LV | Bottoms 50 | Jackson 47 | NONPARTISAN | NO |
| ia-gov-yougov-2026-10-29.json | IA | YouGov (none named) | 10/26-29 | 2,020 LV | Sand 53 | Lahn 46 | UNKNOWN | YES |
| ia-gov-co-efficient-2026-10-28.json | IA | co/efficient (self) | 10/28 | 1,020 LV | Sand 50 | Lahn 45 | PARTISAN_PUBLIC (R) | NO |
| mi-gov-yougov-2026-10-29.json | MI | YouGov (none named) | 10/26-29 | 2,093 LV | Benson 52 | James 46 | UNKNOWN | YES |
| mi-gov-mitchell-2026-10-27.json | MI | Mitchell (MI TV stations / CBS Detroit) | 10/26-27 | 636 LV | 49 | 44 | NONPARTISAN | UNVERIFIED |
| mi-gov-ssrs-2026-10-27.json | MI | SSRS (CNN) | 10/20-27 | 768 LV | 53 | 41 | NONPARTISAN | YES |
| mi-gov-data-for-progress-2026-10-25.json | MI | Data for Progress (self) | 10/23-25 | 622 LV | 52 | 43 | PARTISAN_PUBLIC (D) | YES |
| mi-gov-verasight-2026-10-23.json | MI | MSU Poli Sci / Verasight (MSU) | 10/8-23 | 1,383 LV | 48.5 | 38.7 | NONPARTISAN | NO |
| oh-gov-yougov-2026-10-29.json | OH | YouGov (none named) | 10/26-29 | 2,090 LV | Acton 52 | Ramaswamy 46 | UNKNOWN | YES |
| oh-gov-suffolk-university-political-research-center-2026-10-26.json | OH | Suffolk (USA TODAY Network Ohio) | 10/21-26 | 500 LV | 48.0 | 44.0 | NONPARTISAN | UNVERIFIED |
| oh-gov-activote-2026-10-31.json | OH | ActiVote (self) | 10/16-31 | 400 LV | 50.8 | 49.2 | NONPARTISAN | NO |
| wi-gov-marquette-2026-10-22-lv.json | WI | Marquette (self) | 10/14-22 | 668 LV | Crowley 51 | Tiffany 44 | NONPARTISAN | UNVERIFIED |
| wi-gov-marquette-2026-10-22-rv.json | WI | Marquette (self) | 10/14-22 | 818 RV | 47 | 44 | NONPARTISAN | UNVERIFIED |
| wi-gov-wick-2026-10-23.json | WI | Wick (League of American Workers) | 10/19-23 | 1,213 LV | 47.7 | 44.6 | PARTISAN_PUBLIC (R) | UNVERIFIED |

All 14 confirmed at the pollster's or sponsor's own release. Per race: GA 1, IA 2, MI 5, OH 3, WI 3.

Notes for the integrator:

- `recall_weighted` uses the store's existing vocabulary (YES / NO / UNVERIFIED), not UNKNOWN.
- New pollster_ids: `state-navigate`, `wick` (neither is in `pollsters.csv`). `verasight` is reused for the MSU Political Science / Verasight poll; it is a different program from the held `michigan-state-ippsr` (MSU IPPSR / YouGov, Oct 2-19). Give it its own id if the method record should name MSU as owner.
- MSU/Verasight: the file holds the headline MRP initial response; the leaner MRP (50.9 / 41.5 / 7.7) and the plain weighted toplines are in `notes`.
- Data for Progress MI: **Wikipedia's MI governor row (50-46) is wrong**; those are the Senate numbers. The tabs PDF and 270toWin say 52-43.
- CNN/SSRS n=768 is the RV total; LV results are the whole sample weighted by turnout probability, the same treatment as the held Sept wave.
- ActiVote OH (Oct 16-31) overlaps the held Sept 27-Oct 19 wave by four days; it is a separate published wave.

## Seen but excluded

- Bowling Green State University / YouGov Ohio, Sept 29-Oct 9 (Acton 50, Ramaswamy 44): field_end before 2026-10-10.
- Emerson Iowa, Oct 5-6, and SSRS/CNN Iowa, Sept 29-Oct 5: out of window.
- Already held (from Wikipedia and 270toWin): GA Echelon, ActiVote 10/6-20, Quantus, AJC/UGA, InsiderAdvantage 10/12-13; IA co/efficient 10/15-19, Echelon, GS/New River, NPA, YouGov 10/6-12, Marist; MI Glengariff, MSU IPPSR/YouGov, Marist, RedBox; OH RedBox, Echelon, Verasight/VoteHub, Fox, ActiVote 9/27-10/19, Marist, GS/New River.
- Wick WI leaner follow-up (Q10): not combined into the headline; values in notes.
- No paywall-only polls found. The AJC "knotted" article is the held Oct 7-15 UGA poll.

## Secondary-only

None.
