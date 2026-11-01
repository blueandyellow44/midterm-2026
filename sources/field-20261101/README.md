# Field refresh, 2026-11-01 (Sunday)

Read-only research pass for `lib/field.ts`. Nothing in the repo was edited. Readings were taken 2026-11-01 between 12:00 and 12:40 PST in Max's Chrome, unless a row says otherwise. No paywall was bypassed. Where a number sits behind a paywall, the row keeps the newest free secondary reading and says so.

## Proposed rows (newest reading first, same shape as field.ts)

```ts
  { name: 'The Economist', house: 0.94, senate: 0.54, houseSeats: '236', senateSeats: '51', asOf: '2026-11-01', url: 'https://www.economist.com/interactive/2026/us-midterms/prediction-model/house' },
  { name: 'Kalshi', house: 0.93, senate: 0.71, asOf: '2026-11-01', url: 'https://kalshi.com/category/politics/midterms', note: 'a market, not a model' },
  { name: 'Decision Desk HQ', house: 0.83, senate: 0.62, houseSeats: '241', senateSeats: '52', asOf: '2026-11-01', url: 'https://votes.decisiondeskhq.com/forecast/2026/house' },
  { name: 'Split Ticket', house: 0.92, senate: 0.73, houseSeats: '239', senateSeats: '53', asOf: '2026-10-31', url: 'https://x.com/lxeagle17/status/2116581431287873682', note: "via Lakshya Jain's post" },
  { name: 'Silver Bulletin', house: 0.95, senate: 0.764, senateSeats: '52', asOf: '2026-10-22', url: 'https://www.newsweek.com/who-will-win-the-midterms-what-polls-show-10-days-out-12610772', note: 'paywalled; Senate via Newsweek' },
  { name: 'Cook Political Report', house: null, senate: null, houseSeats: '222 to 240', senateSeats: '7 toss-ups', asOf: '2026-10-30', url: 'https://www.cookpolitical.com/ratings/house-race-ratings', note: 'ratings only' },
```

## Locators, per row

**The Economist** (free interactive, no paywall hit; a cookie/terms dialog was left unclicked and the text read underneath it).
- House page, "Last updated on November 1st 2026": dot chart reads "Dems win ... majority in 94%"; seat chart reads "D 236 / R 199"; headline "19 in 20 chance".
- Senate page (`.../prediction-model/senate`), "Last updated on November 1st 2026": "Dems win ... majority in 54%"; "D 51 / R 49"; "Median D+2 seats".
- Caveat: each page's Oct 30 news blurb says 95% (House) and 55% (Senate). The Nov 1 charts say 94 and 54. The rows use the Nov 1 chart values. Use 0.95 / 0.55 instead if the Oct 30 prose is the preferred reading.

**Kalshi**, kalshi.com/category/politics/midterms, read 2026-11-01 about 12:10 PST: "Senate control forecast 71% Leaning Dem"; "House control forecast 93% Safe Dem"; Senate bar reads "52 DEM forecast / REP forecast 46". This is a live price, so it moves.

**Decision Desk HQ**, "Last updated Nov 1, 9:43 AM".
- House: "Democrats 83% Probability"; map total "241 Democrats ... 194".
- Senate (`/forecast/2026/senate`): "Democrats 62% Probability"; map total "52 Democrats ... 48".

**Split Ticket** (The Argument page is paywalled for the numbers). The source is Lakshya Jain's post, dated 2026-10-31T17:21Z: "House: 92% Dem (239-196) Senate: 73% Dem (53-47)". He is the model's author, so this is first-party and free. Change the url to theargumentmag.com and the note to "via author's post" if the table should keep linking to the model.

**Silver Bulletin**
- House: the free top of natesilver.net/p/nate-silver-2026-midterm-election-polls-model is marked "Updated November 1, 2026" and says "Democrats have about a 95 percent chance of retaking the House". It gives net gain ("net 25 seats"), not a seat total, so houseSeats is left off. I did not compute one.
- Senate: the Senate page (updated Oct 30) is marked PAID, and the free landing text gives no Senate number. The newest free reading is Newsweek, published 2026-10-23, on the model as updated Oct 22: "Democrats have a 95 percent chance of winning the House and a 76.4 percent chance of Senate control", average 52-48 Senate.
- asOf is therefore 2026-10-22 for the Senate figure. The House figure is from Nov 1 (the same 0.95). Note it if the dates should be split.

**Cook**
- House ratings page dated Oct 30, 2026. Summary: Solid D 186, Likely D 18, Lean D 18, Toss Up 18, Lean R 17, Likely R 14, Solid R 164.
- The range uses the same method as the Oct 23 row (220 to 237 with 17 toss-ups): Solid+Likely+Lean D = 222, plus 18 toss-ups = 240.
- Senate page dated Oct 30, 2026: Toss Up (7) is AK, IA, KS, ME, MI, OH, TX.
- Flag: field.ts says "6 toss-ups" as of Oct 23, but `data/seats.csv` (Cook, 2026-10-20) already lists those same 7. Either the 6 was a miscount or a race moved in and out. I cannot confirm which.

## Cook rating changes, tracked races, 2026-10-23 to today

**House** (baseline is house-races.csv, Cook 2026-10-23; current page dated Oct 30). The 45 other tracked districts are unchanged.

| Race | Oct 23 | Now (Oct 30 page) |
|---|---|---|
| 2026-CO-05-HOUSE | Lean R | Toss Up |
| 2026-PA-01-HOUSE | Lean R | Toss Up |
| 2026-SC-01-HOUSE | Lean R | Toss Up |
| 2026-OH-09-HOUSE | Toss-up | Lean D |
| 2026-PA-08-HOUSE | Toss-up | Lean D |

Source: https://www.cookpolitical.com/ratings/house-race-ratings

**Senate** (current page Oct 30; the baseline is data/seats.csv, Cook dated 2026-10-20, so these may predate Oct 23).
- FL special: Solid R to **Likely R** (Moody listed under LIKELY R).
- NE: Likely R to **Lean R** (Ricketts listed under LEAN R).
- No change: AK, IA, KS, ME, MI, OH special, TX (Toss Up); GA, NC (Likely D); NH (Lean D); SC (Lean R); MS (Likely R).

Source: https://www.cookpolitical.com/ratings/senate-race-ratings

**Governor** (current page Oct 29; baseline is seats.csv, Cook 2026-10-27).
- WI: Toss-up to **Lean D**.
- Caveat: Political Wire reported Cook moved WI governor to Lean D on 2026-08-12 (https://politicalwire.com/2026/08/12/wisconsin-governors-race-moves-to-leans-democratic/). So either seats.csv's Toss-up is wrong, or the race went back to Toss-up and then returned to Lean D.
- No change: GA (Toss Up); IA, MI, OH (Lean D).

Source: https://www.cookpolitical.com/ratings/governor-race-ratings

Cook's race pages and archive are subscriber-only, so I could not pin exact change dates for the Senate and governor moves. A House move in the table above happened between Oct 23 and Oct 30.
