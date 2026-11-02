# polls-refresh-20261102-senate

Check for NEW public polls in the 14 Senate races (pollster + field dates not in `sources/_in-polls-since-1010-20261102.txt`, field_end on or after 2026-10-10), run Monday 2026-11-02 (Stage 3 freeze day), 08:35 to 08:50 PST. Free sources only; no paywall bypass, no archive copies, no browser. Files follow the shape of `polls-refresh-20261101-senate/`. Nothing outside this folder was edited; nothing committed.

## Races checked (14)

AK, FL special, GA, IA, KS, ME, MI, MS, NC, NE, NH, OH special, SC, TX.

## Sources read

- Wikipedia raw wikitext (`action=raw`) for all 14 race pages; every general-election row with field_end on or after Oct 10 parsed and compared with the in-polls file.
- 270toWin 2026 Senate poll pages for 13 states (Mississippi 404); its date column is the publication date. Surfaced GrayHouse (IA, NE) and ECU (NC), which Wikipedia did not carry.
- PollCheck Senate pages for 11 states (FL, MS, OH 404) as a cross-check.
- Siena Research Institute: release page for the Nov 1 seven-state NYT/Siena wave (AK, IA, KS, ME, MI, OH, TX), the NYT category list (no other Senate wave dated Oct 31 to Nov 2 besides NE Oct 30/31, already held), and the ReconMR Texas recontact page (interviews, not a poll).
- AtlasIntel polls index (atlasintel.org/polls): the Nov 1 wave has only a Texas PDF and a national PDF; Texas PDF read (charts rendered to images).
- Research Co. release and tables PDF (MI, OH; MN, NY, PA, WI out of scope).
- Trafalgar Texas PDF (Oct 31 to Nov 1); Trafalgar news page lists nothing else new.
- ECU Center for Survey Research NC release and toplines PDF.
- GrayHouse Iowa and Nebraska posts (methodology in the posts).
- Concord Public Opinion Partners polls page (Ohio Oct memo).
- UNH Survey Center landing pages for the NH and ME final polls (survey_center_polls/1011, /1013).
- Emerson state-poll list (latest IA is Oct 9, out of window; KS already held).
- Web searches: UNH NH and ME, Saint Anselm, AtlasIntel, Emerson final, Texas Southern, multi-state Nov 1 sweep.

## Sources that failed

- nytimes.com Times/Siena toplines pages (all seven states, Nov 1 wave): HTTP 403 with a DataDome captcha to curl and WebFetch. Not bypassed. D and R taken from Siena's own release instead; dates, n, other and undecided are secondary (Wikipedia, agreeing with PollCheck and 270toWin) and flagged in each file.
- scholars.unh.edu report PDFs (`viewcontent.cgi?article=2010` NH, `2012` ME): Cloudflare challenge (403) to curl and WebFetch. Not bypassed.
- GrayHouse toplines PDFs: Wix script-rendered downloads; numbers taken from the posts.
- Texas Southern: no TSU release or PDF found; guessed Texas Tribune upload paths 404.
- 270toWin and PollCheck Mississippi pages: 404. PollCheck Florida and Ohio: 404.

## New polls (18 files)

| Race | File | Pollster | Field | n | D | R | Other | Und | scls | align | Primary? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-AK-SEN | ak-sen-nyt-siena-2026-10-30.json | nyt-siena | 10-23 to 10-30 | 610 LV | 48 | 46 | 0 | 6 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-IA-SEN | ia-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-26 to 11-01 | 705 LV | 48 | 47 | 0 | 5 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-IA-SEN | ia-sen-grayhouse-2026-10-31.json | grayhouse | 10-28 to 10-31 | 601 LV | 46 | 48 | 2 | 4 | PARTISAN_PUBLIC | R | yes |
| 2026-KS-SEN | ks-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-27 to 11-01 | 736 LV | 49 | 44 | 4 | 3 | NONPARTISAN | NONE | D/R/Graham yes (SRI); rest secondary |
| 2026-ME-SEN | me-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-27 to 11-01 | 714 LV | 51 | 45 | 0 | 4 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-ME-SEN | me-sen-university-of-new-hampshire-survey-center-2026-10-31.json | university-of-new-hampshire-survey-center | 10-27 to 10-31 | 1654 LV | 54 | 45 | 0 | 0 | NONPARTISAN | NONE | NO, secondary-only |
| 2026-MI-SEN | mi-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-23 to 11-01 | 1011 LV | 53 | 42 | 0 | 6 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-MI-SEN | mi-sen-research-co-2026-11-01.json | research-co | 10-30 to 11-01 | 450 LV | 48 | 46 | 1 | 5 | NONPARTISAN | NONE | yes |
| 2026-NC-SEN | nc-sen-east-carolina-university-ecu-center-for-survey-research-2026-10-29.json | east-carolina-university-ecu-center-for-survey-research | 10-26 to 10-29 | 1041 LV | 54.0 | 44.9 | 1.1 | — | NONPARTISAN | NONE | yes |
| 2026-NE-SEN | ne-sen-grayhouse-2026-11-01.json | grayhouse | 10-29 to 11-01 | 534 LV | 46 | 50 | — | — | PARTISAN_PUBLIC | R | yes |
| 2026-NH-SEN | nh-sen-unh-2026-10-31.json | unh | 10-27 to 10-31 | 2040 LV | 54 | 42 | 2 | 2 | NONPARTISAN | NONE | NO, secondary-only |
| 2026-OH-SEN-SPECIAL | oh-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-26 to 11-01 | 717 LV | 49 | 44 | 0 | 7 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-OH-SEN-SPECIAL | oh-sen-research-co-2026-11-01.json | research-co | 10-30 to 11-01 | 450 LV | 45 | 44 | 2 | 9 | NONPARTISAN | NONE | yes |
| 2026-OH-SEN-SPECIAL | oh-sen-concord-public-opinion-partners-2026-10-24.json | concord-public-opinion-partners | 10-22 to 10-24 | 469 LV | 46 | 42 | 8 | 4 | PARTISAN_PUBLIC | D | yes |
| 2026-TX-SEN | tx-sen-nyt-siena-2026-11-01.json | nyt-siena | 10-27 to 11-01 | 1215 LV | 50 | 43 | 0 | 6 | NONPARTISAN | NONE | D/R yes (SRI); rest secondary |
| 2026-TX-SEN | tx-sen-trafalgar-2026-11-01.json | trafalgar | 10-31 to 11-01 | 1089 LV | 47.5 | 48.1 | 2.4 | 2.0 | NONPARTISAN | R | yes |
| 2026-TX-SEN | tx-sen-atlasintel-2026-11-01.json | atlasintel | 10-28 to 11-01 | 1678 A | 51.3 | 45.4 | 1.5 | 1.1 | NONPARTISAN | NONE | yes |
| 2026-TX-SEN | tx-sen-texas-southern-2026-10-25.json | texas-southern | 10-21 to 10-25 | 2000 LV | 49 | 47 | 3 | 1 | NONPARTISAN | NONE | NO, secondary-only |

Counts by race: AK 1, FL 0, GA 0, IA 2, KS 1, ME 2, MI 2, MS 0, NC 1, NE 1, NH 1, OH 3, SC 0, TX 4.

Notes on choices:

- **NYT/Siena Nov 1 wave (7 states)**: D and R read at Siena's own release (primary, free). Field dates, n, other, undecided are SECONDARY because the nytimes.com toplines are behind a DataDome captcha; each file says so and asks the integrator to verify or hold those fields. LEANERS is inferred from the Times/Siena house format, not read. AK and ME rounds left UNVERIFIED (Siena's RCV asterisk sits on the governor lines only).
- **AtlasIntel Texas**: pop recorded as A, because the PDF states its target population as the Texas adult population; no LV subsample is reported. Valid-vote version (52.2-46.2) in notes. New pollster_id.
- **GrayHouse** (IA, NE): self-funded public polls by a firm whose founder is described on its own site as the Senate Republican Conference's pollster, so PARTISAN_PUBLIC / R as with co/efficient, Quantus and NPA. Nebraska headline is the leaner ballot 50-46 (initial ballot 48-44, undecided 5 in notes). New pollster_id.
- **Research Co.** (MI, OH): all-voter rows from the tables PDF; the release headlines decided-voter splits (MI 51-48, OH 49-48). New pollster_id.
- **ECU North Carolina**: forced-choice combined ballot (Q5R), so LEANERS with no undecided row.
- **Concord Ohio** (Oct 22-24): missed by the Nov 1 sweep. n is 469 at the primary; Wikipedia and PollCheck say 496.
- **UNH NH and ME** and **Texas Southern**: written but flagged SECONDARY-ONLY: NOT VERIFIED ON PRIMARY in source_locator and notes. UNH primaries exist but sit behind a Cloudflare challenge; TSU has no primary found, but FOX 4 now gives n and field dates (the reason the Nov 1 sweep excluded it). Hold these three if the freeze requires primary verification.

## NYT/Siena and AtlasIntel, Oct 31 to Nov 2 (coordinator check)

- NYT/Siena Senate releases in the window: NE (Oct 23-29, released Oct 30/31) is already held; the Nov 1 seven-state wave is filed above (AK, IA, KS, ME, MI, OH, TX). Siena's NYT category list shows no other Senate wave in the window. FL and SC (Oct 28 release) are already held.
- AtlasIntel: the Nov 1 wave has only Texas (filed) and a national poll (out of scope). No other AtlasIntel state PDF is listed for the 14 races.

## Seen but not written

- **Workbench Strategy Florida** (Oct 18-22): still only on Politico Florida Playbook (blocked) and an archive copy. Excluded, as on Nov 1.
- **Univision/YouGov Texas** (Oct 13-21, RV 50-45): already held as yougov 10-13 to 10-21 RV.
- **Stetson Florida**: 270toWin shows 861 LV, Wikipedia 852 RV; the held row is stetson Oct 26-30 LV 45-49. Same poll, not new.
- **Emerson Iowa** (released Oct 9): field before Oct 10, out of window.
- **Saint Anselm NH**: the Boston 25 story refers to Saint Anselm polling already held (Oct 19-20); no newer Saint Anselm wave found.
- **ReconMR Texas recontact** (Siena, Nov 1): qualitative interviews, "not a poll". Excluded.
- GA, MS, SC: nothing new on Wikipedia, 270toWin or PollCheck after the Nov 1 cutoff. Every other October row on those pages matched a poll already in the in-polls file.
