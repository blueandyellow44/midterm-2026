---
type: audit
date: 2026-11-01
status: draft
---

# Audit: polls-refresh-20261101-gov and house-polls-20261101

Run Sunday 2026-11-01, about 12:15 to 13:00 PST. Scripted fetches only (curl, WebFetch, WebSearch); no browser. Every source_url was re-fetched this session. RedBox values were re-derived from each district's `crosstabs.csv` (release_version 5, Total banner, house_vote question). Duplicates checked against `_in-polls-since-1010-20261101.txt`, `data/polls.csv` and every existing `polls-*/` and `house-polls-*/` JSON. Candidates checked against `data/house-races.csv` and the gubernatorial nominees in held files.

Totals: 44 files. CONFIRMED 38, REFUTED 5 (all five on the `align` field only; numbers match), CANNOT-VERIFY 1.

No duplicates found: no new poll matches a held row (race + pollster + field dates), and no sample is filed twice across or within the two folders. The Marquette LV and RV files are the same MLSP92 sample by design, matching the held September LV/RV pair. Every file has field_end on or after 2026-10-10.

## Governor folder (14)

| file | verdict | evidence / discrepancy |
|---|---|---|
| ga-gov-state-navigate-2026-10-27.json | CONFIRMED | Article: Bottoms 50, Jackson 47, 679 LV. Briefing PDF: Oct 23-27, 741 respondents, 2% don't know, 2% already voted/would not say. All fields match. New pollster_id. |
| ia-gov-co-efficient-2026-10-28.json | CONFIRMED | Page: Q5 Sand 50, Lahn 45, Undecided 5; 1,020 LV fielded Oct 28. Class PARTISAN_PUBLIC/R matches 17 of 19 co/efficient rows in polls.csv (2 are NONPARTISAN/R). |
| ia-gov-yougov-2026-10-29.json | CONFIRMED | PDF: 2,020 LV, Oct 26-29; Sand 53, Lahn 46, else 0, not sure 0 (leaners included). scls UNKNOWN matches the held IA ttw series (Oct 6-12 and Sept 3-8 are UNKNOWN); the GA ttw rows are NONPARTISAN, so the series is split. |
| mi-gov-yougov-2026-10-29.json | CONFIRMED | PDF: 2,093 LV, Oct 26-29; Benson 52, James 46, else 1, not sure 0. Same class note as IA. |
| oh-gov-yougov-2026-10-29.json | CONFIRMED | PDF: 2,090 LV, Oct 26-29; Acton 52, Ramaswamy 46, else 1, not sure 0, would not vote 1 (excluded). Same class note. |
| mi-gov-data-for-progress-2026-10-25.json | CONFIRMED | Tabs PDF: 622 LV, Oct 23-25; Q4 Benson 52, James 43, Hudson 1, Brandenburg 1, Campbell <0.5, not sure 3. other 2 is the rounded third-party sum. |
| mi-gov-mitchell-2026-10-27.json | CONFIRMED | PDF: N=636 LV, Oct 26-27; Benson 49, James 44, third parties 3, undecided 4; "for a number of television stations in Michigan". |
| mi-gov-ssrs-2026-10-27.json | CANNOT-VERIFY | DocumentCloud page, S3 PDF and API all 403 to curl and WebFetch. Only corroboration is 270toWin (aggregator): CNN/SSRS 10/29, 768 LV, 53-41. Neither/other/no-opinion split and field dates not re-checked. Also: n=768 is the RV total used for the LV row (same as held Sept wave). |
| mi-gov-verasight-2026-10-23.json | CONFIRMED | MSU report PDF: 1,383 LV, Oct 8-23; Benson 48.5, James 38.7, other 3.3, undecided 9.6 (MRP initial response). 270toWin shows 51-42, which is the leaner column (50.9/41.5) already in notes. pollster_id `verasight` is shared with the held VoteHub/Verasight OH poll; a separate MSU id is advisable. |
| oh-gov-suffolk-university-political-research-center-2026-10-26.json | CONFIRMED | Marginals PDF: N=500 likely, 10/21-10/26; Acton 48.00, Kissick 3.60, Ramaswamy 44.00, write-in 0.40, undecided 3.20, refused 0.80. other 4.0 = Kissick + write-in. |
| oh-gov-activote-2026-10-31.json | CONFIRMED | Page: Oct 16-31, 400 likely midterm voters, Acton 50.8, Ramaswamy 49.2. Flags: page JSON-LD says "800 registered voters in total" across the two polls (body says likely); field overlaps the held Sept 27-Oct 19 wave by four days. |
| wi-gov-marquette-2026-10-22-lv.json | CONFIRMED | Release: Oct 14-22, 668 LV; Crowley 51, Tiffany 44, undecided 4. |
| wi-gov-marquette-2026-10-22-rv.json | CONFIRMED | Release: 818 RV; Crowley 47, Tiffany 44, undecided 9. |
| wi-gov-wick-2026-10-23.json | CONFIRMED | Embedded WICK_PACKET_DATA: client League of American Workers, likely voters, Oct 19-23; Crowley 47.7, Tiffany 44.6, undecided 7.7. Flag: n 1,213 is labeled "Weighted total"; no unweighted n published. |

## House folder (30)

RedBox rows: D, R, other (named third party + "Someone else") and undecided match the crosstabs to 0.1 in all 15; n matches unweighted_n; field 10-20 to 10-23, LV, candidates match house-races.csv.

| file | verdict | evidence / discrepancy |
|---|---|---|
| ca-48-house-redbox-research-2026-10-23.json | CONFIRMED | 47.7 / 42.6 / 2.2 / 3.8, n 1151 |
| fl-13-house-redbox-research-2026-10-23.json | CONFIRMED | 45.1 / 48.1 / 2.4 (D'Arrigo 1.6 + else 0.8) / 3.3, n 875 |
| fl-14-house-redbox-research-2026-10-23.json | CONFIRMED | 45.6 / 44.7 / 4.6 / 3.2, n 708 |
| fl-22-house-redbox-research-2026-10-23.json | CONFIRMED | 46.3 / 45.5 / 2.7 / 3.5, n 550 |
| fl-25-house-redbox-research-2026-10-23.json | CONFIRMED | 46.0 / 40.4 / 4.0 / 6.4, n 643 |
| fl-27-house-redbox-research-2026-10-23.json | CONFIRMED | 46.4 / 49.1 / 1.8 / 1.4, n 523 |
| mt-01-house-redbox-research-2026-10-23.json | CONFIRMED | 46.0 / 48.0 / 2.3 / 2.5, n 754 |
| nc-01-house-redbox-research-2026-10-23.json | CONFIRMED | 45.3 / 43.5 / 2.8 / 5.2, n 1468 |
| nc-11-house-redbox-research-2026-10-23.json | CONFIRMED | 49.9 / 44.1 / 2.3 / 2.9, n 873 |
| ny-17-house-redbox-research-2026-10-23.json | CONFIRMED | 48.2 / 45.5 / 2.4 / 3.2, n 726 |
| oh-07-house-redbox-research-2026-10-23.json | CONFIRMED | 45.7 / 41.7 / 4.1 / 6.2, n 875 |
| oh-09-house-redbox-research-2026-10-23.json | CONFIRMED | 49.4 / 43.4 / 2.1 / 3.2, n 858 |
| pa-01-house-redbox-research-2026-10-23.json | CONFIRMED | 46.0 / 46.1 / 2.2 / 4.3, n 733 |
| pa-07-house-redbox-research-2026-10-23.json | CONFIRMED | 48.6 / 43.9 / 2.0 / 2.9, n 644 |
| pa-08-house-redbox-research-2026-10-23.json | CONFIRMED | 48.7 / 45.5 / 1.7 / 3.0, n 696 |
| pa-10-house-redbox-research-2026-10-23.json | CONFIRMED | 47.6 / 45.2 / 1.7 / 4.1, n 1022 |
| mn-01-house-public-policy-polling-2026-10-14.json | CONFIRMED | HMP memo (Oct 21): PPP 10/13-14, 43-43. Flags: memo gives no n or population; pop LV comes from Wikipedia/uspollingdata only; n null. |
| mt-01-house-public-policy-polling-2026-10-14.json | CONFIRMED | Memo: PPP 10/12-14, 48-45. Same pop/n flags. |
| nv-02-house-public-policy-polling-2026-10-13.json | CONFIRMED | Memo: PPP 10/12-13 (printed "10/13-26"), 44-46. Same pop/n flags. |
| ny-21-house-public-policy-polling-2026-10-13.json | CONFIRMED | Memo: PPP 10/12-13, 44-46. Same pop/n flags. |
| fl-25-house-public-policy-polling-2026-10-27.json | CONFIRMED | X post via fxtwitter: Moskowitz 47, Singer 41, PPP 10/26-10/27, 523 LV, posted 2026-10-27. Correction to the README: CJ Warnke is HMP's Communications Director (his X bio), not a reporter, so this is the sponsor's own release channel. Distinct from the held PPP Oct 21-22 (47-42). |
| fl-25-house-national-research-2026-10-15.json | CONFIRMED | Florida Politics: Singer 49, Moskowitz 42, 400 LV, Oct 12-15, undecided 6%, commissioned by Singer campaign and NRCC. SECONDARY ONLY; no memo found. Access flag: WebFetch got HTTP 402 Payment Required and a browser-UA curl got 403; only a plain curl returned the full article. Max should rule whether that counts as a paywall. |
| al-02-house-remington-research-group-2026-10-25.json | CONFIRMED | 1819 News (Oct 29): 642 LV, Oct 23-25, Marques 48, Figures 46. SECONDARY ONLY; WebSearch found no Remington release or sponsor. Class PARTISAN_PUBLIC/R is provisional. |
| az-01-house-keating-research-2026-10-28.json | CONFIRMED | Keating memo PDF: 500 LV, Oct 26-28, Shah 49, Feely 45, 6 undecided (leaners included). No sponsor named. |
| ca-22-house-usc-democracy-lab-2026-10-28.json | REFUTED (align) | Numbers confirmed: PDF N=356, Oct 22-28, Villegas 52, Valadao 41, undecided 6, skip 1. `align: "NA"` is not in the vocabulary (polls.csv uses NONE/D/R/UNKNOWN). Fix: `"align": "NONE"`. |
| ca-48-house-usc-democracy-lab-2026-10-28.json | REFUTED (align) | Numbers confirmed: N=474, Von Wilpert 48, Desmond 40, undecided 10, skip 2. Fix: `"align": "NONE"`. Minor: the CA-48 topline page says "October 22-27" while the release header says Oct 22-28; field_end 10-28 follows the header. |
| mt-01-house-msu-billings-2026-10-21.json | REFUTED (align) | Numbers confirmed: PDF Q12 Total Forstag 49, Flint 32, Sheedy 4, Don't know 11; fielded Oct 5-21; 720 statewide responses weighted to census. Fix: `"align": "NONE"`. Population flag: pop A (no voter screen) and district n not printed; recommend `selected = 0` with exclusion reason "adult sample, no n". |
| pa-07-house-muhlenberg-college-2026-10-15.json | REFUTED (align) | Numbers confirmed: 529 LV, Oct 6-15, Brooks 49, Mackenzie 43, Neither/Other 3, Not sure 5. Fix: `"align": "NONE"`. |
| tx-15-house-texas-southern-2026-10-16.json | REFUTED (align) | Numbers confirmed: TPR, likely voters, Oct 13-16, Pulido 51, De La Cruz 44, 5% undecided. Fix: `"align": "NONE"` (the held texas-southern rows use NONE). SECONDARY ONLY (Express-News original paywalled); n missing. |
| va-01-house-dccc-2026-10-25.json | CONFIRMED | DCCC memo body: internal DCCC Analytics poll, Oct 24-25, 478 LV, Taylor 48, Wittman 47, undecided 5. INTERNAL/D matches all held DCCC rows. |

## Sponsor-class notes (report only)

- HMP-sponsored PPP: all five new files use PARTISAN_PUBLIC with an `-h-` method_id. Held PPP/HMP rows are mixed, as the brief says.
- RedBox/AFWH: new files use PARTISAN_PUBLIC/D with `-h-`; held RedBox rows use both `-h-` and `-s-`.
- The house folder uses `-s-` only for INTERNAL; the governor folder uses `-s-` for every file.
- New pollster_ids not in pollsters.csv: state-navigate, wick, remington-research-group, keating-research, usc-democracy-lab, national-research, msu-billings, muhlenberg-college.
