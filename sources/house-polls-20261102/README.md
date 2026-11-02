# House polls, sweep 2026-11-02 (Stage 3 freeze day)

Sweep of all 50 tracked House districts (`house-races.csv` in the vault bundle) for public polls with fieldwork ending 2026-10-10 or later that are NOT already in `../_in-polls-since-1010-20261102.txt` (56 House rows; matched on race + pollster + field dates). Prior site cutoff 2026-11-01 12:38 PST; the 2026-11-01 sweep (`../house-polls-20261101/`) covered releases through about Nov 1 11:00 PST. Run Monday 2026-11-02, about 08:35 to 08:45 PST, single worker. Includes the coordinator's mid-task lead (Nov 1 evening NYT/Siena wave and AtlasIntel).

Rules met: free sources only; no archive.ph, no Wayback, no paywall bypass, no browser. Bot walls (NYT DataDome, UNH Cloudflare challenge) were not bypassed. Every number in a JSON came from a URL fetched this session; nothing was invented.

Schema: key-for-key identical to `../house-polls-20261101/va-01-house-dccc-2026-10-25.json` (checked by script for both files). `method_id` uses `h` (neither poll is INTERNAL). Pollster ids reused: `nyt-siena`, `university-of-new-hampshire-survey-center`.

## Sources read

- Wikipedia raw wikitext (`?action=raw`) for the House pages of all 24 states with tracked districts, plus the CA-22 and CA-48 district pages. Every polling row with October/November 2026 dates was extracted by script; no tracked-district row was new. AK and ME pages re-pulled at about 08:40 PST; the AK page had no Nov 1 Times/Siena row and the ME page was last edited Oct 30.
- VoteHub API (https://api.votehub.com/polls, 6,086 records, newest created 2026-11-02): every `us-representative` record with end_date >= 2026-10-10 in a tracked district diffed against the in-file list. Only two were new and not paywalled (below); the rest were on file or are the paywalled Emerson/Poll Vault and WaPo-Schar polls already excluded on Nov 1.
- Siena Research Institute release, Nov 1 (https://sri.siena.edu/2026/11/01/nytimes-siena-poll-of-likely-voters-alaska-iowa-kansas-maine-michigan-ohio-and-texas/): tagged "US House"; prints Senate and Governor numbers only.
- UNH landing pages https://scholars.unh.edu/survey_center_polls/1013/ and https://scholars.unh.edu/pine_tree_state_poll/.
- 270toWin ME-02 page; DCCC RSS feed pages 1 to 3 (Oct 30 to Nov 2: no new poll memos); HMP news index (no memo newer than Oct 21); AtlasIntel polls index.
- uspollingdata.com race pages for all 50 districts (it republishes VoteHub, CC BY; nothing beyond VoteHub).
- WebSearch, district by district for all 13 poll-less districts and in groups for the rest; leads opened: NJ Globe, Navajo Times, carolinajournal.com, joannamendoza.com, villegasforcongress.com, wispolitics.com (via WebFetch), WGME, Brunswick News, Press Herald, Bangor Daily News.

## Failed sources

- nytimes.com toplines pages for the Nov 1 Times/Siena wave: HTTP 403, DataDome / "enable JS" (curl and WebFetch). Not bypassed.
- scholars.unh.edu report PDF (`viewcontent.cgi?article=2012`): Cloudflare challenge, HTTP 403 (curl and WebFetch). Not bypassed.
- 270toWin AK at-large page: 404. wispolitics.com: 403 to curl (WebFetch worked). realclearpolling.com: 403.
- AtlasIntel poll pages render by JavaScript; WebFetch read the Texas page summary only.

## New polls (2 files, 2 districts), both SECONDARY-ONLY

| District | Pollster | Field (2026) | Pop | n | D | R | Sponsor | Class | File |
|---|---|---|---|---|---|---|---|---|---|
| AK-AL | Siena Research Institute (NYT/Siena) | 10-23 to 10-30 | LV | 610 | 48.0 (Hill) | 52.0 (Begich) | The New York Times | NONPARTISAN | `ak-al-house-nyt-siena-2026-10-30.json` |
| ME-02 | UNH Survey Center (Pine Tree State Poll) | 10-27 to 10-31 | LV | 802 | 47.0 (Dunlap) | 52.0 (LePage) | self | NONPARTISAN | `me-02-house-university-of-new-hampshire-survey-center-2026-10-31.json` |

### Caveats to read before merge

- **AK-AL NYT/Siena: one aggregator only (VoteHub).** Primary toplines blocked; no second source found. Round is UNVERIFIED and is probably the RCV final round, not first choice: 52 + 48 = 100, and VoteHub's AK Data for Progress record is the final round (51-49) while the file on hand uses DFP first choice (48-42, FIRST). As filed it is not comparable to the five AK-AL rows on file, which are all FIRST. Recommend hold unless the toplines can be opened (a browser by hand) and the first-choice line read.
- **ME-02 UNH: two aggregators agree** (270toWin: 802 LV, ±3.5, Dunlap 47, LePage 52, other 1; VoteHub: Oct 27-31, 802 LV, 52-47). The UNH landing page confirms the direction ("LePage has opened a small lead"). Round UNVERIFIED (no undecided shown). Same wave as the ME-SEN UNH file in `../polls-refresh-20261102-senate/`.
- Both pollster blocks carry cycle methods from pollsters.csv or the sibling Senate files, named as such in `method_locator`; this wave's method pages were unreachable.

## Excluded

### Coordinator lead: NYT/Siena Nov 1 wave and AtlasIntel

- NYT/Siena Nov 1 (AK, IA, KS, ME, MI, OH, TX): the AK House item is filed above. No other tracked-district House result was found in any free source (SRI release prints Senate and Governor only; VoteHub carries only AK for House). Whether the ME or IA toplines carry a district question is unknown, because the toplines are blocked.
- NYT/Siena Oct 31 Nebraska, Oct 28 FL/MN/SC: statewide; no tracked-district House rows in VoteHub or Wikipedia.
- AtlasIntel Nov 1 (usa-national, usa-texas; Texas Oct 28 to Nov 1, 1,678 adults): statewide and national; no district results on the readable page and none in VoteHub. Nothing to file.

### Not tracked (seen, not filed)

ME-01 UNH Oct 27-31 (Pingree 65, Russell 32); NH-01 and NH-02 UNH Oct 27-31; MI-13 Center for Strategic Politics Oct 28-30; MN-08 PPP Oct 25-26; NV-03, OH-01 RedBox; FL-07, CO-03, TX-09, TX-28 DCCC; NC-09, NE-01, MO-02 PPP; IN-05 Quantus; CA-01, CA-06, CA-11, CA-34 USC.

### Still unverifiable (paywall), already listed Nov 1

Emerson/RCP Poll Vault Oct 12-14 (AZ-02, FL-14, IA-02, MI-07, MT-01, NC-11, PA-08, TX-35); WaPo-Schar Oct 14-19 (TX-34, TX-35). Not re-opened.

### Out of window or wrong race (checked this sweep)

- KY-06 DCCC Jul 28-30, 47-47 (Brunswick News, Aug 7).
- WI-01 HMP "48-47", released Oct 3 (wispolitics, Oct 5); no field dates, almost certainly before Oct 10 (the Impact/HMP Sep 28 to Oct 1 poll is on file).
- AZ-02 Arizona Eagle PAC (Navajo Times, Jul 30); NJ-07 StimSight Democratic primary (May); NC-01 NRCC (Carolina Journal, May 8); CA-22 Villegas internal 48-44 (July release); ME-02 UNH Feb 2026 (WGME); CO-05 GSG "Oct 30-Nov 3, Crank 43 Killin 40" (a November 2025 poll, Denver Gazette 2025-11-05).
- VA-02 Wason/CNU "Oct 12-18, 45-45, 820 RV": the 2022 race (Luria was the incumbent then), as found Nov 1.
- CO-08 McLaughlin Sep 16-17; NM-02 Research & Polling Oct 1-9 and KOB "46-43" (earlier October, no field dates found); TX-23 Normington Petts Oct 5-7: all out of window or on file.

## Tracked districts still without an in-window poll (field_end >= 2026-10-10, on file or new)

13 of 50, unchanged from Nov 1: AZ-02, CO-04, CO-08, IA-01, IA-02, IA-03, MI-07, NJ-07, NM-02, TX-23, TX-34, WI-01, WI-03.

AZ-02, IA-02, MI-07 (Emerson/Poll Vault) and TX-34 (WaPo-Schar) have an in-window poll that exists only behind a paywall.
