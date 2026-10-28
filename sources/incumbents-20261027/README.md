# Incumbents on the 2026 general-election ballot (as of 2026-10-27)

One row per 2026 race: is the seat's current holder a general-election candidate for that same seat on November 3, 2026?
Built for Undertow (midtermundertow.com). Seat list and current holders come from
`../chambers-20261027/chambers.json` (35 Senate, 36 governors) and `../house-all-20261027/districts.csv` (435 House districts).

## Files

- `incumbents.csv`: columns `chamber,seat,state,district,incumbent,incumbent_party,on_ballot,reason,source_url`.
  `on_ballot` is YES, NO, VACANT, or UNKNOWN. Nothing was guessed; every row was read from the source named in `source_url`.

## Sources (all free, no paywalls)

- Senate: Wikipedia, "2026 United States Senate elections", race-summary tables (incumbent, status, candidate list) plus the Retirements and Defeats sections. Each of the 35 races was checked individually: the status column was read and the incumbent's name was confirmed present or absent in that race's candidate list. https://en.wikipedia.org/wiki/2026_United_States_Senate_elections
- Governors: Wikipedia, "2026 United States gubernatorial elections", race-summary table plus the Retirements and Incumbents-defeated sections. Each of the 36 races checked individually the same way. https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections
- House: Wikipedia, "2026 United States House of Representatives elections". The per-state district tables were parsed for all 435 districts (member, "Redistricted from" note, status, candidate list), then cross-checked against the page's Retirements (60 voting members: 24 D, 36 R), Nomination withdrawn, Resignations, and Incumbents defeated in primaries (7 D, 4 R) lists. All 71 names on those lists appear as NO below. Every YES row was verified to have the member's name in that district's general-election candidate list. https://en.wikipedia.org/wiki/2026_United_States_House_of_Representatives_elections
- Louisiana House schedule (jungle primary on Nov 3): https://en.wikipedia.org/wiki/2026_United_States_House_of_Representatives_elections_in_Louisiana
- Florida unopposed-candidate rule (Fla. Stat. 101.151(7)): https://www.flsenate.gov/Laws/Statutes/2025/101.151
- Ballotpedia's "not running for re-election" list was attempted but the fetch returned an empty body; it was not used.

Wikitext was pulled from the Wikipedia raw endpoint (`action=raw`) on 2026-10-27 and parsed with a script; the raw files are not kept here.

## Counts

| chamber | races | YES | NO | VACANT | UNKNOWN |
|---|---|---|---|---|---|
| SEN | 35 | 22 | 13 | 0 | 0 |
| GOV | 36 | 17 | 19 | 0 | 0 |
| HOUSE | 435 | 350 | 83 | 2 | 0 |

## Notes on edge cases

- **Redistricting (11 House rows).** `districts.csv` keys each member to the district they hold now. Where a mid-decade map moved a member to a differently numbered district, the member is NOT on the ballot for the seat number they currently hold, so the row is NO with reason `redistricted; running in XX-NN`. Downstream code that wants "is an incumbent running in this district" should treat these as a separate category: CA-03/CA-06 (Kiley and Bera swapped numbers), CA-38 (Sanchez to CA-41), CA-41 (Calvert to CA-40, where he faces fellow incumbent Young Kim), FL-22 (Frankel to FL-23), FL-23 (Moskowitz to FL-25), FL-25 (Wasserman Schultz to FL-20), TX-35 (Casar to TX-37), UT-01/02/03 (Moore to UT-02, Maloy to UT-03, Kennedy to UT-04). Two more redistricted members lost primaries in their new districts and are NO for that reason: TX-09 Al Green (lost to Menefee in TX-18), TX-32 Julie Johnson (lost to Allred in TX-33).
- **Appointed senators.** FL special (Moody), OH special (Husted), SC (Darline Graham, appointed 2026 after Lindsey Graham's death on July 11, 2026) are appointees who won nomination and are on the ballot: YES. OK (Alan Armstrong, appointed March 2026 after Mullin resigned) is barred by Oklahoma law from running: NO.
- **Unopposed incumbents.** FL-10 Frost, MA-02 McGovern, MA-05 Clark, MA-07 Pressley, WI-02 Pocan are the only candidates listed; Wikipedia marks them "Incumbent re-elected". Recorded as YES. Florida does not print unopposed names on the general ballot (Fla. Stat. 101.151(7)); the row says so.
- **Louisiana House.** After Louisiana v. Callais the state ran the 2026 House races as a jungle primary on November 3 (runoff December 12). LA-01 through LA-04 incumbents are on that ballot: YES.
- **GA-13.** Everton Blair won the August 25 special election for David Scott's unexpired term but had already lost the nomination for the full term; the November candidates are Jasmine Clark (D) and Jonathan Chavez (R). NO.
- **NC-11.** Chuck Edwards won his primary but withdrew on August 5, 2026. NO.
- **Vacant seats.** FL-20 (Cherfilus-McCormick resigned April 21, 2026) and TX-23 (Gonzales resigned April 14, 2026) are VACANT.
- **Alaska Senate.** Candidate list shows both "Dan S. Sullivan (Republican)" and "Dan J. Sullivan (Republican)"; the incumbent advanced to the general per the status column. YES.

## NO seats, with reasons

### Senate (13)
- 2026-AL-SEN: Tommy Tuberville (R), running for governor
- 2026-IL-SEN: Dick Durbin (D), retiring
- 2026-IA-SEN: Joni Ernst (R), retiring
- 2026-KY-SEN: Mitch McConnell (R), retiring
- 2026-LA-SEN: Bill Cassidy (R), lost primary
- 2026-MI-SEN: Gary Peters (D), retiring
- 2026-MN-SEN: Tina Smith (D), retiring
- 2026-MT-SEN: Steve Daines (R), retiring (withdrew at filing deadline)
- 2026-NH-SEN: Jeanne Shaheen (D), retiring
- 2026-NC-SEN: Thom Tillis (R), retiring
- 2026-OK-SEN: Alan Armstrong (R), appointed 2026; ineligible to run under Oklahoma law
- 2026-TX-SEN: John Cornyn (R), lost primary runoff
- 2026-WY-SEN: Cynthia Lummis (R), retiring

### Governors (19)
- 2026-AL-GOV: Kay Ivey (R), term-limited
- 2026-AK-GOV: Mike Dunleavy (R), term-limited
- 2026-CA-GOV: Gavin Newsom (D), term-limited
- 2026-CO-GOV: Jared Polis (D), term-limited
- 2026-FL-GOV: Ron DeSantis (R), term-limited
- 2026-GA-GOV: Brian Kemp (R), term-limited
- 2026-IA-GOV: Kim Reynolds (R), retiring
- 2026-KS-GOV: Laura Kelly (D), term-limited
- 2026-ME-GOV: Janet Mills (D), term-limited
- 2026-MI-GOV: Gretchen Whitmer (D), term-limited
- 2026-MN-GOV: Tim Walz (D), retiring
- 2026-NM-GOV: Michelle Lujan Grisham (D), term-limited
- 2026-OH-GOV: Mike DeWine (R), term-limited
- 2026-OK-GOV: Kevin Stitt (R), term-limited
- 2026-RI-GOV: Dan McKee (D), lost primary
- 2026-SC-GOV: Henry McMaster (R), term-limited
- 2026-TN-GOV: Bill Lee (R), term-limited
- 2026-WI-GOV: Tony Evers (D), retiring
- 2026-WY-GOV: Mark Gordon (R), term-limited

### House (83)
- 2026-AL-01-HOUSE: Barry Moore (R), running for U.S. Senate
- 2026-AZ-01-HOUSE: David Schweikert (R), running for governor
- 2026-AZ-05-HOUSE: Andy Biggs (R), running for governor
- 2026-CA-03-HOUSE: Kevin Kiley (I), redistricted; running in CA-06
- 2026-CA-06-HOUSE: Ami Bera (D), redistricted; running in CA-03
- 2026-CA-11-HOUSE: Nancy Pelosi (D), retiring
- 2026-CA-26-HOUSE: Julia Brownley (D), retiring
- 2026-CA-38-HOUSE: Linda Sanchez (D), redistricted; running in CA-41
- 2026-CA-41-HOUSE: Ken Calvert (R), redistricted; running in CA-40
- 2026-CA-48-HOUSE: Darrell Issa (R), retiring
- 2026-CO-01-HOUSE: Diana DeGette (D), lost primary
- 2026-CT-01-HOUSE: John Larson (D), lost primary
- 2026-FL-02-HOUSE: Neal Dunn (R), retiring
- 2026-FL-07-HOUSE: Cory Mills (R), lost primary
- 2026-FL-11-HOUSE: Daniel Webster (R), retiring
- 2026-FL-16-HOUSE: Vern Buchanan (R), retiring
- 2026-FL-19-HOUSE: Byron Donalds (R), running for governor
- 2026-FL-22-HOUSE: Lois Frankel (D), redistricted; running in FL-23
- 2026-FL-23-HOUSE: Jared Moskowitz (D), redistricted; running in FL-25
- 2026-FL-24-HOUSE: Frederica Wilson (D), retiring
- 2026-FL-25-HOUSE: Debbie Wasserman Schultz (D), redistricted; running in FL-20
- 2026-GA-01-HOUSE: Buddy Carter (R), running for U.S. Senate
- 2026-GA-10-HOUSE: Mike Collins (R), running for U.S. Senate
- 2026-GA-11-HOUSE: Barry Loudermilk (R), retiring
- 2026-GA-13-HOUSE: Everton Blair (D), lost primary for full term (elected only to complete David Scott unexpired term); listed as retiring in Wikipedia retirements
- 2026-IA-02-HOUSE: Ashley Hinson (R), running for U.S. Senate
- 2026-IA-04-HOUSE: Randy Feenstra (R), running for governor
- 2026-IL-02-HOUSE: Robin Kelly (D), running for U.S. Senate
- 2026-IL-04-HOUSE: Chuy Garcia (D), retiring
- 2026-IL-07-HOUSE: Danny Davis (D), retiring
- 2026-IL-08-HOUSE: Raja Krishnamoorthi (D), running for U.S. Senate
- 2026-IL-09-HOUSE: Jan Schakowsky (D), retiring
- 2026-KY-04-HOUSE: Thomas Massie (R), lost primary
- 2026-KY-06-HOUSE: Andy Barr (R), running for U.S. Senate
- 2026-LA-05-HOUSE: Julia Letlow (R), running for U.S. Senate
- 2026-LA-06-HOUSE: Cleo Fields (D), running for Louisiana State Senate
- 2026-MA-06-HOUSE: Seth Moulton (D), running for U.S. Senate
- 2026-MD-05-HOUSE: Steny Hoyer (D), retiring
- 2026-ME-02-HOUSE: Jared Golden (D), retiring
- 2026-MI-10-HOUSE: John James (R), running for governor
- 2026-MI-11-HOUSE: Haley Stevens (D), running for U.S. Senate
- 2026-MI-13-HOUSE: Shri Thanedar (D), lost primary
- 2026-MN-02-HOUSE: Angie Craig (D), running for U.S. Senate
- 2026-MO-06-HOUSE: Sam Graves (R), retiring
- 2026-MT-01-HOUSE: Ryan Zinke (R), retiring
- 2026-NC-11-HOUSE: Chuck Edwards (R), withdrew after primary
- 2026-NE-02-HOUSE: Don Bacon (R), retiring
- 2026-NH-01-HOUSE: Chris Pappas (D), running for U.S. Senate
- 2026-NJ-12-HOUSE: Bonnie Watson Coleman (D), retiring
- 2026-NV-02-HOUSE: Mark Amodei (R), retiring
- 2026-NY-07-HOUSE: Nydia Velazquez (D), retiring
- 2026-NY-10-HOUSE: Dan Goldman (D), lost primary
- 2026-NY-12-HOUSE: Jerry Nadler (D), retiring
- 2026-NY-13-HOUSE: Adriano Espaillat (D), lost primary
- 2026-NY-21-HOUSE: Elise Stefanik (R), retiring
- 2026-OK-01-HOUSE: Kevin Hern (R), running for U.S. Senate
- 2026-PA-03-HOUSE: Dwight Evans (D), retiring
- 2026-SC-01-HOUSE: Nancy Mace (R), running for governor
- 2026-SC-05-HOUSE: Ralph Norman (R), running for governor
- 2026-SD-AL-HOUSE: Dusty Johnson (R), running for governor
- 2026-TN-05-HOUSE: Andy Ogles (R), lost primary
- 2026-TN-06-HOUSE: John Rose (R), running for governor
- 2026-TN-09-HOUSE: Steve Cohen (D), retiring
- 2026-TX-02-HOUSE: Dan Crenshaw (R), lost primary
- 2026-TX-08-HOUSE: Morgan Luttrell (R), retiring
- 2026-TX-09-HOUSE: Al Green (D), lost primary (ran in TX-18, redistricted)
- 2026-TX-10-HOUSE: Michael McCaul (R), retiring
- 2026-TX-19-HOUSE: Jodey Arrington (R), retiring
- 2026-TX-21-HOUSE: Chip Roy (R), running for Texas attorney general
- 2026-TX-22-HOUSE: Troy Nehls (R), retiring
- 2026-TX-30-HOUSE: Jasmine Crockett (D), running for U.S. Senate
- 2026-TX-32-HOUSE: Julie Johnson (D), lost primary (ran in TX-33, redistricted)
- 2026-TX-33-HOUSE: Marc Veasey (D), retiring
- 2026-TX-35-HOUSE: Greg Casar (D), redistricted; running in TX-37
- 2026-TX-37-HOUSE: Lloyd Doggett (D), retiring
- 2026-TX-38-HOUSE: Wesley Hunt (R), running for U.S. Senate
- 2026-UT-01-HOUSE: Blake Moore (R), redistricted; running in UT-02
- 2026-UT-02-HOUSE: Celeste Maloy (R), redistricted; running in UT-03
- 2026-UT-03-HOUSE: Mike Kennedy (R), redistricted; running in UT-04
- 2026-UT-04-HOUSE: Burgess Owens (R), retiring
- 2026-WA-04-HOUSE: Dan Newhouse (R), retiring
- 2026-WI-07-HOUSE: Tom Tiffany (R), running for governor
- 2026-WY-AL-HOUSE: Harriet Hageman (R), running for U.S. Senate
