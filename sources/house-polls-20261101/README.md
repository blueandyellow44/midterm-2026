# House polls, sweep 2026-11-01

Sweep of all 50 tracked House districts (`house-races.csv` in the vault bundle) for public polls with fieldwork ending 2026-10-10 or later that are NOT already in `../_in-polls-since-1010-20261101.txt` (25 House rows; matched on race + pollster + field dates). Last site cutoff was 2026-10-28. Run Sunday 2026-11-01, about 12:00 to 12:45 PST, by five parallel workers (10 districts each) plus a coordinator audit.

Rules met: free sources only; no archive.ph, no Wayback, no paywall bypass. Paywalls left closed: RCP Poll Vault paid Substack (Emerson Oct 12-14 district polls), washingtonpost.com (Schar School, 403), expressnews.com, Detroit News, National Journal. dccc.org returned a Cloudflare 403 to one worker and the VA-01 memo page to another; nothing was forced. No browser was used. Every number in a JSON came from a URL fetched this session; aggregator-only figures (n, undecided) were NOT written into fields.

Schema: key-for-key identical to `../house-polls-20261027/az-01-house-redbox-research-2026-10-23.json` (checked by script for all 30 files). `method_id` uses `s` for INTERNAL and `h` otherwise. Per-district search logs (`searched`, `failed`, `unverified`, `excluded`) are in `summary-batch-1.json` through `summary-batch-5.json`.

## Sources read

- A Fight Worth Having polling index (https://afightworthhaving.com/polling) and each district's page, `crosstabs.csv` (release version 5) and `/methodology`. The index lists 24 House polls, all Oct 20-23; 17 are tracked districts, 15 of them new here (AZ-01, AZ-06, MI-04, MI-10 were already on file). Untracked: CA-07, CA-11, NV-03, OH-01.
- House Majority PAC memo of Oct 21 (https://www.thehousemajoritypac.com/news/hmp-memo-house-battleground-extends-deep-into-trump-territory): every tracked row checked; MN-01, MT-01, NV-02, NY-21 are new, the rest already on file or out of window.
- DCCC memos (dccc.org), Keating Research memo and topline PDFs, USC Democracy Lab `capolling.pdf` and its data file, MSU Billings Mountain States Poll report PDF, Muhlenberg College release page, Texas Public Radio, 1819 News, Florida Politics, Daily Montanan, Colorado Politics, Kentucky Lantern.
- Wikipedia raw wikitext per state, 270toWin, uspollingdata.com, VoteHub API, X posts through api.fxtwitter.com / api.vxtwitter.com, WebSearch (worked this session).

## Failed sources

- DDHQ (integration-votes.decisiondeskhq.com): HTTP 429 for every district tried.
- 270toWin district poll pages: 404 for most districts.
- uspollingdata.com: 404 for AK-AL, CO-05, CO-08, IA-03, MI-04.
- Wikipedia per-district election pages for CA-22 and CA-48: 404 (no page; the state page was used).
- insideelections.com AZ-02 poll page 403; axios.com 403; washingtonpost.com 403 (paywall); dccc.org site search 403 (Cloudflare); emersoncollegepolling.com/pa-08-2026-poll/ 404; aol.com WI-03 404.

## New polls (30 files, 24 districts)

D and R are the race's D-slot and R-slot candidates from house-races.csv. n = null means no free primary source gives it.

| District | Pollster | Field (2026) | Pop | n | D | R | Sponsor | Class | File |
|---|---|---|---|---|---|---|---|---|---|
| AL-02 | Remington Research Group | 10-23 to 10-25 | LV | 642 | 46.0 | 48.0 | Not named in source | PARTISAN_PUBLIC | `al-02-house-remington-research-group-2026-10-25.json` |
| AZ-01 | Keating Research | 10-26 to 10-28 | LV | 500 | 49.0 | 45.0 | None named; memo from Keating Research to Interested Parties | PARTISAN_PUBLIC | `az-01-house-keating-research-2026-10-28.json` |
| CA-22 | USC Democracy and Fair Elections Lab (California Elections and Policy Poll) | 10-22 to 10-28 | LV | 356 | 52.0 | 41.0 | USC Dornsife Center for the Political Future (no political, corporate, or external sponsorship) | NONPARTISAN | `ca-22-house-usc-democracy-lab-2026-10-28.json` |
| CA-48 | RedBox Research | 10-20 to 10-23 | LV | 1151 | 47.7 | 42.6 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `ca-48-house-redbox-research-2026-10-23.json` |
| CA-48 | USC Democracy and Fair Elections Lab (California Elections and Policy Poll) | 10-22 to 10-28 | LV | 474 | 48.0 | 40.0 | USC Dornsife Center for the Political Future (no political, corporate, or external sponsorship) | NONPARTISAN | `ca-48-house-usc-democracy-lab-2026-10-28.json` |
| FL-13 | RedBox Research | 10-20 to 10-23 | LV | 875 | 45.1 | 48.1 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `fl-13-house-redbox-research-2026-10-23.json` |
| FL-14 | RedBox Research | 10-20 to 10-23 | LV | 708 | 45.6 | 44.7 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `fl-14-house-redbox-research-2026-10-23.json` |
| FL-22 | RedBox Research | 10-20 to 10-23 | LV | 550 | 46.3 | 45.5 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `fl-22-house-redbox-research-2026-10-23.json` |
| FL-25 | National Research Inc. | 10-12 to 10-15 | LV | 400 | 42.0 | 49.0 | Scott Singer campaign and NRCC | INTERNAL | `fl-25-house-national-research-2026-10-15.json` |
| FL-25 | Public Policy Polling | 10-26 to 10-27 | LV | 523 | 47.0 | 41.0 | House Majority PAC | PARTISAN_PUBLIC | `fl-25-house-public-policy-polling-2026-10-27.json` |
| FL-25 | RedBox Research | 10-20 to 10-23 | LV | 643 | 46.0 | 40.4 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `fl-25-house-redbox-research-2026-10-23.json` |
| FL-27 | RedBox Research | 10-20 to 10-23 | LV | 523 | 46.4 | 49.1 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `fl-27-house-redbox-research-2026-10-23.json` |
| MN-01 | Public Policy Polling | 10-13 to 10-14 | LV | null | 43.0 | 43.0 | House Majority PAC | PARTISAN_PUBLIC | `mn-01-house-public-policy-polling-2026-10-14.json` |
| MT-01 | Montana State University Billings (Mountain State Poll) | 10-05 to 10-21 | A | null | 49.0 | 32.0 | self (MSU Billings Office of the Provost, College of Liberal Arts and Social Sciences, Dept. of Social Sciences and Cultural Studies) | NONPARTISAN | `mt-01-house-msu-billings-2026-10-21.json` |
| MT-01 | Public Policy Polling | 10-12 to 10-14 | LV | null | 48.0 | 45.0 | House Majority PAC | PARTISAN_PUBLIC | `mt-01-house-public-policy-polling-2026-10-14.json` |
| MT-01 | RedBox Research | 10-20 to 10-23 | LV | 754 | 46.0 | 48.0 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `mt-01-house-redbox-research-2026-10-23.json` |
| NC-01 | RedBox Research | 10-20 to 10-23 | LV | 1468 | 45.3 | 43.5 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `nc-01-house-redbox-research-2026-10-23.json` |
| NC-11 | RedBox Research | 10-20 to 10-23 | LV | 873 | 49.9 | 44.1 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `nc-11-house-redbox-research-2026-10-23.json` |
| NV-02 | Public Policy Polling | 10-12 to 10-13 | LV | null | 44.0 | 46.0 | House Majority PAC | PARTISAN_PUBLIC | `nv-02-house-public-policy-polling-2026-10-13.json` |
| NY-17 | RedBox Research | 10-20 to 10-23 | LV | 726 | 48.2 | 45.5 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `ny-17-house-redbox-research-2026-10-23.json` |
| NY-21 | Public Policy Polling | 10-12 to 10-13 | LV | null | 44.0 | 46.0 | House Majority PAC | PARTISAN_PUBLIC | `ny-21-house-public-policy-polling-2026-10-13.json` |
| OH-07 | RedBox Research | 10-20 to 10-23 | LV | 875 | 45.7 | 41.7 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `oh-07-house-redbox-research-2026-10-23.json` |
| OH-09 | RedBox Research | 10-20 to 10-23 | LV | 858 | 49.4 | 43.4 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `oh-09-house-redbox-research-2026-10-23.json` |
| PA-01 | RedBox Research | 10-20 to 10-23 | LV | 733 | 46.0 | 46.1 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `pa-01-house-redbox-research-2026-10-23.json` |
| PA-07 | Muhlenberg College Institute of Public Opinion | 10-06 to 10-15 | LV | 529 | 49.0 | 43.0 | Muhlenberg College Institute of Public Opinion (self-funded) | NONPARTISAN | `pa-07-house-muhlenberg-college-2026-10-15.json` |
| PA-07 | RedBox Research | 10-20 to 10-23 | LV | 644 | 48.6 | 43.9 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `pa-07-house-redbox-research-2026-10-23.json` |
| PA-08 | RedBox Research | 10-20 to 10-23 | LV | 696 | 48.7 | 45.5 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `pa-08-house-redbox-research-2026-10-23.json` |
| PA-10 | RedBox Research | 10-20 to 10-23 | LV | 1022 | 47.6 | 45.2 | A Fight Worth Having (progressive super PAC) | PARTISAN_PUBLIC | `pa-10-house-redbox-research-2026-10-23.json` |
| TX-15 | Texas Southern University (Barbara Jordan Public Policy Research and Survey Center) | 10-13 to 10-16 | LV | null | 51.0 | 44.0 | San Antonio Express-News, El Pais and Puente News Collaborative | NONPARTISAN | `tx-15-house-texas-southern-2026-10-16.json` |
| VA-01 | DCCC Analytics Department | 10-24 to 10-25 | LV | 478 | 48.0 | 47.0 | DCCC | INTERNAL | `va-01-house-dccc-2026-10-25.json` |
New pollster_ids (not in data/pollsters.csv): `remington-research-group`, `keating-research`, `usc-democracy-lab`, `national-research`, `msu-billings`, `muhlenberg-college`.

Audit (coordinator): all 15 RedBox files re-checked against freshly downloaded `crosstabs.csv` (D, R, n match to 0.1); the four PPP/HMP rows re-read from the HMP memo; 1819 News (AL-02), DCCC VA-01 memo, the FL-25 PPP post, Muhlenberg, Keating memo PDF, USC PDF and MSU PDF re-fetched and matched. The CA-48 RedBox file was added by the coordinator after the batch-1 worker missed it.

### Caveats to read before merge

- **AL-02 Remington**: SECONDARY SOURCE ONLY (1819 News, Oct 29). No Remington release and no sponsor named; class PARTISAN_PUBLIC/R is provisional.
- **AZ-01 Keating**: no sponsor named in the memo or topline; filed as a Democratic firm's self-release (PARTISAN_PUBLIC/D). Ballot includes leaners; 61% of respondents had already voted.
- **CA-22, CA-48 USC**: headline is the release table without pushing undecideds (52-41, 48-40); the pushed versions (54-44, 52-44) are in notes.
- **FL-25 National Research**: from a Florida Politics article that loaded in full to a plain request (HTTP 200). The 10-27 sweep logged that site as 402; no bypass was used. Wikipedia's 24% undecided conflicts with the article's 6%; the article was used.
- **FL-25 PPP Oct 26-27**: only source is a reporter's X post (CJ Warnke) quoting HMP's toplines; no memo found.
- **MT-01 MSU Billings**: district subsample of a statewide poll with no voter screen, so pop = A; field period runs Oct 5-21; district n not printed (uspollingdata says 287, not used).
- **TX-15 TSU**: sponsors and toplines from free Texas Public Radio coverage; Express-News original paywalled, not opened; n not published free.
- **Sponsor-class convention**: HMP-sponsored polls are PARTISAN_PUBLIC with an `-h-` method_id here, the majority convention in polls.csv. Earlier files are mixed (FL-13, OH-15, TX-23, TX-35 HMP polls are INTERNAL; several 20261027 PARTISAN_PUBLIC files use `-s-`). Reconcile at merge.
- RedBox shares are the crosstabs' unrounded weighted_pct rounded to 0.1; the poll pages show whole numbers.

## Excluded

### Seen, unverifiable (numbers exist only behind a paywall or on aggregators)

| District | Poll | Why not written |
|---|---|---|
| AZ-02 | Emerson for RCP Poll Vault, Oct 12-14, 345 LV, Nez 50 Crane 48 | Paid Poll Vault post only; no Emerson release |
| FL-14 | Emerson/Poll Vault, Oct 12-14, 315 LV, Castor 48 Beltran 43 | Same |
| IA-02 | Emerson/Poll Vault, Oct 12-14, 344 LV, James 50 Mitchell 47 | Same |
| MI-07 | Emerson/Poll Vault, Oct 12-14, 314 LV, Lawrence 53 Barrett 45 | Same |
| MT-01 | Emerson/Poll Vault, Oct 12-14, 329 LV, Forstag 50 Flint 46 | Same |
| NC-11 | Emerson/Poll Vault, Oct 12-14, 388 LV, Ager 56 Balkcom 43 | Same |
| PA-08 | Emerson/Poll Vault, Oct 12-14, 396 LV, Cognetti 52 Bresnahan 48 | Same; emersoncollegepolling.com/pa-08-2026-poll/ 404 |
| TX-35 | Emerson/Poll Vault, Oct 12-14, 417 LV, Garcia 51 De La Cruz 49 | Same |
| TX-34 | Washington Post-Schar School, Oct 14-19, 626 LV, Gonzalez 50 Flores 43 | washingtonpost.com 403/paywall; aggregators only |
| TX-35 | Washington Post-Schar School, Oct 14-19, De La Cruz 48 Garcia 47 | Same; aggregators disagree on n (606 vs 605) |

### Out of window (field_end before 2026-10-10), not written

AK-AL NYT/Siena Sep 24-Oct 1 (Begich 47 Hill 35, Wikipedia); AZ-01 FirstStrategic Oct 1 (on file); CO-04 Impact Sep 21-24 (on file); CO-08 McLaughlin Sep 16-17 (on file); FL-27 Bendixen & Amandi (DCCC) Aug 25-30 45-45; IA-01 Wavefield Sep 29-Oct 2 (on file); ME-02 UNH Sep 17-21 51-45 and Impact (HMP) Sep 8-12; MT-01 American Pulse Sep 19-24 Flint 46 Forstag 45; NC-01 co/efficient (Buckhout) Oct 6-8 Davis 42 Buckhout 43 (Wikipedia) and ECU Sep 29-Oct 2 50-46 (search snippet); NJ-07 StimSight Sep 8-12 (on file); NM-02 Research & Polling Oct 1-9 (on file); NY-17 HMP release Jul 8 51-45; NY-21 Impact Research Sep 29-Oct 4 Gendebien 45 Constantino 48 (Wikipedia); PA-01 GSG (Harvie) Oct 1-8 46-46 (Wikipedia); SC-01 GQR Sep 30-Oct 4 and co/efficient Sep 30-Oct 1 (on file); TX-23 Normington Petts Oct 5-7 46-46 (on file); VA-01 WaPo-Schar Sep 23-28 Taylor 50 Wittman 46; WI-01 Impact Sep 28-Oct 1 (on file); WI-03 FM3 Jun 20-25 (on file).

### Wrong cycle, wrong matchup, or no toplines

- PA-10 "NYT/Siena Perry 45 Scott 43, Oct 23-26" (politicspa.com): 2018 article, Perry vs George Scott.
- IA-01 Selzer Oct 28-31, co/efficient Oct 15-19, Marist Oct 8-11: 2024 race.
- VA-02 CNU "tied 45-45, Oct 12-18": 2022 race. WI-03 DCCC "Cooke +1, Oct 4-8": 2024 race.
- AZ-02 Noble Predictive Insights / Inside Elections Oct 8-10, 42-42: appears to be the 2024 cycle; page 403.
- AZ-06 PPP (HMP) Oct 14-15 Mendoza 42 Ciscomani 41: 2025.
- CO-05 Colorado Politics "Killin 46 Crank 44": two-way ballot of the GSG Oct 14-18 poll already on file (multi-candidate 43-38). Wikipedia's 44-44 is that memo's generic ballot.
- PA-01 F&M Oct 7-18 "Dem 48 Rep 41": appears to be a statewide generic ballot; not verified.
- NV-02 Concord Public Opinion Partners Sep 26-30: statewide generic, not the matchup. MN-01 Big Data Poll Sep 29-30: generic-style, unverified.
- WI-03 Wisconsin Watch Oct 26: says Democratic polls show Cooke up to +4 and a September GOP poll Van Orden +5, with no pollster, dates or numbers.
- OH-07 unnamed poll Sep 22-Oct 1, 616 LV: no toplines.
- ME-02 a search summary mentioned an "Oct 16-21" poll; no source found.
- CO-05: Crank campaign says it has internals it will not share.

## Tracked districts still without an in-window poll (field_end >= 2026-10-10, on file or new)

13 of 50: AZ-02, CO-04, CO-08, IA-01, IA-02, IA-03, MI-07, NJ-07, NM-02, TX-23, TX-34, WI-01, WI-03.

Of these, AZ-02, IA-02, MI-07 (Emerson) and TX-34 (WaPo-Schar) have an in-window poll that exists only behind a paywall. TX-23's newest poll ends Oct 7, NM-02's Oct 9, IA-01's Oct 2, WI-01's Oct 1.
