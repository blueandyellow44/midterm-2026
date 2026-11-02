# polls-refresh-20261102-gov

Check for NEW public polls in the five Undertow governor races (GA, IA, MI, OH, WI), run Monday 2026-11-02, 08:35 to 08:45 PST (Stage 3 freeze day). NEW = pollster + field dates absent from `sources/_in-polls-since-1010-20261102.txt`, field_end on or after 2026-10-10. Free sources only; no paywall bypass; curl, WebFetch and WebSearch only (no browser).

## Sources read

- Wikipedia raw wikitext (`action=raw`) for all five `2026_<State>_gubernatorial_election` pages; every Oct/Nov 2026 general-election row compared to the held list.
- 270toWin 2026 governor polls pages, all five states (cross-check).
- PollCheck (pollcheck.co.uk) governor pages, all five states, "updated 2 November 2026" (cross-check; surfaced Rasmussen MI).
- Primaries: Research Co. release page + `Tables_MidTerms_USA_01Nov2026.pdf`; InsiderAdvantage final Ohio post + home page post list; Concord Public Opinion Partners `polls/ohio-ge-2026-oct`; Rasmussen Reports Michigan governor page (free portion); Siena Research Institute 2026-11-01 release post (links only).
- Discovery: Emerson state-polls index (newest in-scope still Iowa Oct 5-6); InsiderAdvantage Oct 21-22 release (Senate only, no governor); WebSearch for "<state> governor poll" in each state and for Times/Siena coverage.

## Sources that failed

- NYT Times/Siena toplines and crosstabs pages (`times-siena-{ia,mi,oh}-poll-toplines.html`): HTTP 403 with a DataDome captcha page to curl (twice) and WebFetch. Not bypassed. The Siena Research Institute post only links to NYT. The three Times/Siena polls are therefore SECONDARY-ONLY (below).
- Rasmussen: methodology and crosstabs behind the subscriber wall; not read.
- Concord: crosstabs "available upon request", not public.

## New polls (9 files)

| file | race | pollster (sponsor) | field | n | D | R | scls | recall | primary? |
|---|---|---|---|---|---|---|---|---|---|
| mi-gov-research-co-2026-11-01.json | MI | Research Co. (self) | 10/30-11/1 | 450 LV | Benson 53 | James 41 | NONPARTISAN | NO | yes |
| oh-gov-research-co-2026-11-01.json | OH | Research Co. (self) | 10/30-11/1 | 450 LV | Acton 48 | Ramaswamy 42 | NONPARTISAN | NO | yes |
| wi-gov-research-co-2026-11-01.json | WI | Research Co. (self) | 10/30-11/1 | 450 LV | Crowley 50 | Tiffany 45 | NONPARTISAN | NO | yes |
| oh-gov-insideradvantage-2026-10-30.json | OH | InsiderAdvantage (self) | 10/29-30 | 1,200 LV | 49 | 46 | PARTISAN_PUBLIC (R) | NO | yes |
| oh-gov-concord-public-opinion-partners-2026-10-24.json | OH | Concord (Education Reform Now Advocacy) | 10/22-24 | 469 LV | 49 | 39 | PARTISAN_PUBLIC (D) | NO | yes |
| mi-gov-rasmussen-2026-10-29.json | MI | Rasmussen (self) | 10/28-29 | 745 LV | 50 | 40 | PARTISAN_PUBLIC (R) | UNKNOWN | yes (free portion) |
| ia-gov-nyt-siena-2026-11-01.json | IA | Siena (NYT) | 10/26-11/1 | 705 LV | Sand 51 | Lahn 43 | NONPARTISAN | YES | NO, secondary |
| mi-gov-nyt-siena-2026-11-01.json | MI | Siena (NYT) | 10/23-11/1 | 1,011 LV | 52 | 39 | NONPARTISAN | YES | NO, secondary |
| oh-gov-nyt-siena-2026-11-01.json | OH | Siena (NYT) | 10/26-11/1 | 717 LV | 49 | 43 | NONPARTISAN | YES | NO, secondary |

Per race: GA 0, IA 1, MI 3, OH 4, WI 1.

Notes for the integrator:

- New pollster_id: `research-co` (not in `pollsters.csv`). Research Co. uses all-voter rows (Base 450, undecided included); the release page headlines the decided-voter split (MI 56-43, OH 53-46, WI 53-47), which is in each file's notes.
- Concord OH: the primary says n=469 and sponsor "Education Reform Now Advocacy"; Wikipedia/PollCheck say 496 and Democrats for Education Reform. Missed by the 11-01 sweep (released Oct 24).
- InsiderAdvantage OH and Rasmussen MI are the governor questions of surveys whose Senate rows were collected 2026-11-01.
- Times/Siena: numbers agree across Wikipedia, 270toWin and PollCheck, but are NOT verified on the primary; `denominator_class` LEANERS is inferred from house format. Verify on the NYT toplines page before ingesting, or hold. MI `other` is null (Wikipedia shows "<1%").
- `recall_weighted` uses the store's vocabulary (YES / NO / UNVERIFIED / UNKNOWN).

## Seen but excluded

- Georgia: nothing new. Wikipedia, 270toWin, PollCheck and WebSearch show only held polls (State Navigate, Echelon, ActiVote, Quantus, AJC/UGA, InsiderAdvantage 10/12-13).
- Wisconsin YouGov (D, City Forward Collective), Sept 22-Oct 9, adults: field_end before 2026-10-10.
- Bowling Green/YouGov OH (Sept 29-Oct 9), co/efficient OH (Oct 5-6), Emerson IA (Oct 5-6), SSRS IA/OH (Sept 29-Oct 5): out of window.
- Concord OH Aug 29-31: out of window.
- Times/Siena, evening of Nov 1 (coordinator lead): the Siena Research Institute release covers Alaska, Iowa, Kansas, Maine, Michigan, Ohio and Texas. In scope: IA, MI, OH, filed above as secondary-only. No Times/Siena GA or WI poll in that release or the Oct 28 (FL/MN/SC) or Oct 31 (NE) releases.
- AtlasIntel (coordinator lead): atlasintel.org/polls lists only two US releases dated 2026-11-01, `usa-national-2026-11-01` (national, Oct 28-Nov 1, 3,566 adults, no state governor results) and `usa-texas-2026-11-01`. No AtlasIntel poll for GA, IA, MI, OH or WI; none on Wikipedia, 270toWin or PollCheck either.
- Already held: every other in-window row on Wikipedia, 270toWin and PollCheck.
- No paywall-only polls found.

## Secondary-only

The three Times/Siena files above (IA, MI, OH): primary blocked by a captcha bot wall, not a paywall.
