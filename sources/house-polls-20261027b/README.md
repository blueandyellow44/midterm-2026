# House polls, second sweep (2026-10-27b)

Second, deeper sweep for the sixteen Cook Toss-up/Lean districts the 2026-10-27 sweep left with no public poll since 2026-09-01. Internal (candidate, party committee, aligned PAC) polls count when their toplines are published. Window: fieldwork ending 2026-09-01 or later; where nothing in-window is verifiable, the newest verifiable poll since 2026-06-01 is written with `out_of_window` in `poll.notes`.

Constraints met: free sources only; no archive.ph, no Wayback, no paywalled text opened (Detroit News 402, Florida Politics 402, Poll Vault paid Substack, Washington Post, National Journal Hotline hub, Punchbowl all left closed). WebFetch/WebSearch only; the session's WebSearch budget was exhausted before this sweep started (confirmed again from a test subagent), so discovery ran on fetched listings: Wikipedia per-state pages (section by section through the raw-wikitext endpoint), uspollingdata.com, HMP/DCCC/NRCC/CLF/PPP release pages, campaign sites, local outlets' site-search pages, and X posts read through the fxtwitter/vxtwitter JSON readers. Bing results pages returned unrelated content for every quoted query; DuckDuckGo served a CAPTCHA; Brave 429; Mojeek 403; Bluesky's public search API 403; Ballotpedia race pages came back empty; FiftyPlusOne's domain is parked; VoteHub and DDHQ poll pages 403/404. RealClearPolling was not attempted (blocks scripted fetches).

Every number in a JSON file comes from a URL fetched this session. Where a field (dates, pollster name, population) could only be read on Wikipedia or uspollingdata.com, the JSON `notes` say so in capitals and the numbers Wikipedia lists but no primary source confirms (n, undecided) were NOT written into fields.

Schema: identical to `../house-polls-20261027/az-01-house-redbox-research-2026-10-23.json` (verified key-for-key). `method_id` uses `s` for INTERNAL and `h` otherwise, the dominant pattern in the first sweep. New pollster_ids (not in pollsters.csv): `hart-research`, `noble-predictive-insights`, `tavern-research`, `fm3-research`.

## Totals

- In-window polls written: 6 (FL-13 x1, OH-15 x2, TX-23 x1, TX-35 x1, NC-11 x1).
- Out-of-window polls written (flagged): 12 (AL-02 x2, AZ-02, CA-22, FL-14, FL-22 x2, IA-02, MI-07, OH-07, TX-34, WI-03).
- Districts with no in-window verifiable poll: 11 (AL-02, AZ-02, CA-22, FL-14, FL-22, IA-02, IA-03, MI-07, OH-07, TX-34, WI-03).
- Districts with nothing at all since 2026-06-01: 1 (IA-03).

## Seen, unverifiable (numbers exist somewhere, but only behind a paywall, in an unreadable image, or on an aggregator)

| District | Poll | Where seen | Why not written |
|---|---|---|---|
| AZ-02 | Emerson College for RCP Poll Vault, Oct 12-14, 345 LV, Nez 50 Crane 48 | Wikipedia AZ table; uspollingdata | Source is the paid Poll Vault post (pollvault.substack.com/p/levee-math); nothing free |
| AZ-02 | GBAO (Nez campaign), Aug 21-24, 500 LV, Crane 46 Nez 44 | Wikipedia | Memo is a politico.com/f PDF; WebFetch cannot reach politico.com |
| AZ-02 | Peak Insights (R), Aug 17-20, 400 LV, Crane 53 Nez 42 | Wikipedia; x.com/Bencjacobs/status/2091935151609565622 | Post text says only "up double digits"; numbers are in an image |
| CA-22 | Tulchin (HMP) memo itself, Jun 15-21, n=800 | Politico PDF | politico.com unreachable; toplines written from the Villegas campaign release instead |
| FL-13 | PPP (HMP) Oct 14-15 sample size n=603 | Wikipedia citing floridapolitics.com/archives/826223 | 402; poll written with n=null from the HMP memo |
| FL-14 | Emerson/Poll Vault, Oct 12-14, 315 LV, Castor 48 Beltran 43 | Wikipedia FL-14 table | Paid Substack only |
| IA-02 | Emerson/Poll Vault, Oct 12-14, 344 LV, James 50 Mitchell 47 | Wikipedia IA table | Paid Substack only |
| MI-07 | Emerson/Poll Vault, Oct 12-14, 314 LV, Lawrence 53 Barrett 45 | Wikipedia MI table; uspollingdata | Paid Substack only |
| MI-07 | "Whitehouse Polling Research (Lawrence campaign), Sep 21-24, 500 LV, Lawrence 48 Barrett 45" | Appeared in the first (whole-page) WebFetch summary of the Michigan Wikipedia page, citing a detroitnews.com story dated 2026-09-25; ABSENT from the later section-level fetch of District 7, which lists only Emerson, GSG and Data for Progress | Detroit News URL returned 402; no other outlet found; treat as unconfirmed and possibly a summarizer artifact. Flagged so a browser session can check the Detroit News story directly |
| MI-07 | Data for Progress, Jun 24-30, 772 LV, Lawrence 48 Barrett 46 | Wikipedia | Cited only to X posts by @WeWill2026 (not fetched) |
| NC-11 | Emerson/Poll Vault, Oct 12-14, 388 LV, Ager 56 Balkcom 43 | Wikipedia NC-11 table | Paid Substack only |
| OH-07 | Bedrock Polling (Iron Workers), Aug 7-10, 866 LV, Poindexter 43 Miller 35 | Wikipedia | documentcloud.org and s3.documentcloud.org both 403 |
| OH-07 | co/efficient (R), Aug 5-6, 615 LV, Poindexter 47 Miller 33 | Wikipedia | Cited only to a Shane Goldmacher tweet (no ID given) |
| OH-07 | co/efficient (R), Jul 29-30, MoE 3.8, Poindexter 44 Miller 39 Und 16 | washingtonsun.com (ex-NOTUS) Aug 2 article, free | Article names no firm ("a Republican firm"), gives no n; older than the Tavern poll written |
| TX-34 | Washington Post-Schar School, Oct 14-19, 626 LV, Gonzalez 50 Flores 43 | Wikipedia TX-34 table | WaPo article and topline PDF paywalled/403; Schar School news page lists no Texas release |
| TX-35 | Washington Post-Schar School, Oct 14-19, 606 LV, De La Cruz 48 Garcia 47 | Wikipedia TX-35 table | Same |
| TX-35 | Emerson/Poll Vault, Oct 12-14, 417 LV, Garcia 51 De La Cruz 49 | Wikipedia | Paid Substack only |
| TX-35 | Normington Petts (HMP), Aug 27-31, 500 LV, Garcia 44 De La Cruz 45 | Wikipedia | Cited only to hub.nationaljournal.com (paid) |

## District by district

### AL-02 (Lean R; Figures (D) vs Marques (R); new 2026 map)
Searched: Wikipedia AL page (District 2 polling table and refs), uspollingdata (404), HMP news and AL-02 release, DCCC memo PDF, alreporter.com site search (Sep 11 "race rater" story read), prediction.com Sep 9 item.
Found: Tulchin/HMP Aug 24-31, 47-47 (written, out_of_window by one day); DCCC Jul 29-30, 421 LV, 46-46-8 (written). No fieldwork on/after Sep 1 anywhere. Impact Research Jun 22-25 (44-45) is older and sits behind National Journal.
Why competitive without an in-window poll: two consecutive Democratic internals showing a tie on lines that voted Trump +14, plus Sabato's move from Likely R to Leans R on Sep 11 citing Figures' incumbency and Black turnout (district still about 40% Black after the Callais-driven redraw). The DCCC memo also puts Doug Jones ahead of Tuberville 48-45 inside the district.

### AZ-02 (Lean R; Nez (D) vs Crane (R))
Searched: Wikipedia AZ table, uspollingdata, Navajo Times, HMP (no AZ-02 release; guessed URL 404), azmirror.com search (403), fxtwitter for the Peak Insights post.
Found: Noble Predictive Insights for Arizona Eagle PAC, Jul 13-15, Nez 38 Crane 37 Goodwin 7 Und 19 (written, out_of_window). GBAO Aug (Crane +2), Peak Insights Aug (Crane +11) and Emerson Oct (Nez +2) are seen, unverifiable.
Why competitive: a Trump +15 seat where the Democratic internals show a 1-2 point race and the Republican internal shows Crane at only 53 in a Freedom Caucus rematch; Economist rates it a toss-up (Oct 24 per Wikipedia).

### CA-22 (Toss-up; Villegas (D) vs Valadao (R); Prop 50 map)
Searched: Wikipedia CA (1-26) District 22 section, uspollingdata, Villegas campaign news page (all items through Oct 8 read), gvwire.com search, Politico memo (unreachable).
Found: only the Tulchin/HMP Jun 15-21 poll, 48-44 (written, out_of_window; pollster/dates from Wikipedia and uspollingdata, toplines from the campaign release). Nothing since June from any side.
Why competitive: Prop 50 redrew the seat to roughly Harris +2 (pres2024 -1.85 in house-races.csv); Valadao's Medicaid-cut vote is the central attack (GV Wire Oct 24); forecasters moved it to Toss Up around Oct 1 (Villegas release). The ratings rest on the lines and the environment, not on new polling.

### FL-13 (Lean R; Gray (D) vs Luna (R); May 2026 map)
Searched: HMP Oct 21 memo (table read in full), HMP Sep 1 release, Wikipedia FL District 13 section (table and refs), Florida Politics (402).
Found: PPP/HMP Oct 14-15, Gray 47 Luna 46 (WRITTEN, in window, n not published free). Also on record: Hart/HMP Aug 25-27 Gray 51-46 (free HMP page, field end before window, not written); Fabrizio Lee for Luna Aug 4-6 Luna 49-41 and GQR for Gray Aug 4-6 Gray 47-44 (Wikipedia refs, not fetched).
Note: the first sweep saw this PPP poll and declined it for lack of n; it meets this sweep's internal-poll standard.

### FL-14 (Toss-up; Castor (D) vs Beltran (R); May 2026 map)
Searched: Wikipedia FL District 14 section, uspollingdata, St. Pete Polls PDF, floridapolitics.com search (402), Emerson site (checked in sweep 1).
Found: St. Pete Polls for Florida Politics Jul 14-15, 469 LV, Castor 46.2 Beltran 37.5 Und 16.4 (written, out_of_window). Emerson Oct is seen, unverifiable.
Why competitive: the new map cut Castor's Tampa seat to roughly Trump +10 (pres2024 -10.51); Cook moved it to Toss-up on Aug 25 on the lines alone, with Trump and DeSantis endorsing Beltran; the only public poll still has Castor up 9.

### FL-22 (Toss-up; open; Dandiya (D) vs Askar (R); new seat)
Searched: Wikipedia FL District 22 section (found at raw section 443), uspollingdata, HMP release, Tavern toplines PDF (parsed locally), American Bazaar Sep 27.
Found: Impact Research/HMP Aug 24-31, Dandiya 46 Askar 44 (written, out_of_window by one day; Wikipedia mislabels it Tulchin); Tavern Research Aug 10-12, 551 LV, 50-50 with leaners (written). Nothing with fieldwork in September or October.
Why competitive: a brand-new Trump +10 seat with no incumbent, a self-funding Republican (Askar $7.4M raised vs Dandiya $4.6M as of Oct 14 per Wikipedia), and two August polls at a tie or D +2.

### IA-02 (Toss-up; open; James (D) vs Mitchell (R))
Searched: Wikipedia IA District 2 table, HMP release PDF (parsed), HMP news page (Oct 24 Mitchell video item, no poll), iowacapitaldispatch.com search.
Found: GSG/HMP Jul 14-19, James 46 Mitchell 45 (written, out_of_window). Emerson Oct 12-14 (James 50-47) seen, unverifiable.
Why competitive: open seat at Trump +10 with Democratic internals tied since July, a generic ballot tied 45-45 in the same poll, and an opposition-research story HMP pushed Oct 24; Cook, DDHQ and Inside Elections all at Toss-up.

### IA-03 (Lean D; Trone Garriott (D) vs Nunn (R))
Searched: Wikipedia IA District 3 table (only Ragnar Research Mar 12-14, Nunn 48-42, before the June cutoff), uspollingdata (404), iowacapitaldispatch.com search and the Oct 14 debate story, pollsmax (sweep 1).
Found: nothing since 2026-06-01. No file written.
Why competitive: the lines voted Trump +4 (pres2024 -4.41 in house-races.csv), Nunn's 2024 margin was narrow (recalled, not fetched this session), and the only poll on record is a March Republican internal with Nunn under 50; the Lean D rating is an environment-and-fundraising call (Democrats outraised GOP incumbents in Iowa per the Capital Dispatch), not a polling call. The rating itself is the only "indicator" here.

### MI-07 (Toss-up; Lawrence (D) vs Barrett (R))
Searched: Wikipedia MI District 7 (whole-page fetch, then section-level fetch of general election and Democratic primary), uspollingdata, HMP release, Semafor (404), Detroit News (402), michiganadvance/wlns/wilx/mlive/metrotimes/lansingcitypulse site searches, Center Square (tollbit gate, not followed).
Found: GSG/HMP Aug 11-13, Lawrence 49 Barrett 47 (written, out_of_window). Emerson Oct (53-45) seen, unverifiable. The "Whitehouse Polling Research Sep 21-24" row is unconfirmed (see table above).
Why competitive: Harris +1 lines (pres2024 -1.28 in house-races.csv) held by a first-term Republican; Barrett has outraised Lawrence $8.2M to $4.2M but every Democratic poll on record has Lawrence ahead; Wikipedia's prose calls it one of the most expensive House races at $51.5M.

### NC-11 (Lean D flip; open; Ager (D) vs Balkcom (R); 2025 map)
Searched: Wikipedia NC District 11 (general election and replacement-nominee sections), uspollingdata, PPP release page (Sep 16), fxtwitter read of the Bench post, wlos.com search, HMP (guessed URL 404).
Found: PPP for The Bench Sep 10-11, Ager 47 Republican 44 (WRITTEN, in window). Balkcom replaced Edwards on Aug 11, so the unnamed Republican in a Sep 10-11 poll is the November opponent. Emerson Oct (Ager 56-43) seen, unverifiable.
Why competitive beyond polling: Edwards quit after winning the primary, the replacement nominee had raised $399K to Ager's $5.87M by Oct 14, and Cook and Sabato both moved to Lean D (flip) in late October.

### OH-07 (Toss-up; Poindexter (D) vs Miller (R); new Ohio map)
Searched: Wikipedia OH District 7 general section (row-by-row refs), uspollingdata, Tavern toplines PDF (parsed), documentcloud (403), washingtonsun.com Aug 2 article, Spectrum News Sep 28, ohiocapitaljournal search (403), Bing/Bluesky (unusable).
Found: Tavern Research Aug 4-5, 635 LV, Poindexter 54 Miller 46 with leaners (written, out_of_window). Three other August polls seen, unverifiable. Nothing from September or October.
Why competitive: scandal. Miller faces abuse allegations from his ex-wife (which he denies) and stayed on the ballot past the Aug 8 withdrawal deadline; every August poll, including the Republican firm's, had Poindexter ahead on Trump +11 lines; at least $4.1M in ads with Democrats outspending 3-to-1 by Sep 28 (Spectrum News). Poindexter also led fundraising $3.72M to $3.32M.

### OH-15 (Lean R; Leonard (D) vs Carey (R); new Ohio map)
Searched: HMP Oct 21 memo, fxtwitter read of the Sep 28 HMP post, Wikipedia OH District 15 general section, HMP Jun release.
Found: Hart Research/HMP Oct 9-12, Leonard 48 Carey 45 (WRITTEN); Hart/HMP Sep 22-24, Leonard 46 Carey 45 (WRITTEN; dates from Wikipedia). Both in window.
Note: the first sweep saw both and declined them for missing n or dates; they meet this sweep's internal-poll standard.

### TX-23 (Lean R; open; Padilla Stout (D) vs Herrera (R); 2025 map)
Searched: HMP Oct 21 memo, Wikipedia TX District 23 polling section (raw section 454), uspollingdata.
Found: Normington Petts/HMP Oct 5-7, 46-46 (WRITTEN, in window). PPP Mar 10-11 (Texas Tribune PDF) predates June.
Why competitive beyond polling: open seat, Herrera outraising Padilla Stout $3.1M to $0.98M, yet a Democratic internal tied on Trump +15 lines.

### TX-34 (Lean D; Gonzalez (D) vs Flores (R); 2025 map)
Searched: Wikipedia TX District 34 polling section (raw section 685), FOX 26 Houston Aug 28 story, tsu.edu news (stale), tpr.org, krgv.com and houstonpublicmedia searches, Schar School news page, NRCC search (May memo only), HMP (guessed URL 404).
Found: Texas Southern University (Barbara Jordan center) Aug 18-22, 700 LV, Gonzalez 45 Flores 42 (written, out_of_window; dates from Wikipedia). WaPo-Schar Oct 14-19 (Gonzalez 50-43) seen, unverifiable.
Why competitive: Trump +10 lines, a Republican nominee the NRCC polled in April-May (co/efficient 41-40 Flores), a June Flores internal with Flores +3, and then independent polls in August and October with Gonzalez ahead 3 and 7; Cook's Lean D reflects the latter two.

### TX-35 (Toss-up; open; Garcia (D) vs De La Cruz (R); new seat)
Searched: HMP Oct 21 memo, Wikipedia TX District 35 polling section (raw section 712), uspollingdata.
Found: Normington Petts/HMP Oct 12-14, Garcia 47 De La Cruz 45 (WRITTEN, in window). WaPo-Schar (De La Cruz 48-47), Emerson (Garcia 51-49) and NP Aug 27-31 (De La Cruz 45-44) seen, unverifiable.
Why competitive: four polls in ten weeks within 2 points either way on a Trump +10.6 seat with near-identical fundraising ($1.92M vs $1.89M).

### WI-03 (Lean D; Cooke (D) vs Van Orden (R))
Searched: Wikipedia WI District 3 table, uspollingdata, HMP release, fxtwitter read of the Jul 6 post, wisconsinexaminer.com search (403).
Found: FM3/HMP Jun 20-25, Cooke 50 Van Orden 46 (written, out_of_window). Nothing since.
Why competitive: a 2024 Van Orden-Cooke rematch on Trump +7 lines (pres2024 -7.40; the 2024 margin was narrow, recalled, not fetched this session); three Democratic internals from February to June have Cooke ahead 1-4; Wikipedia's prose puts spending at $31.6M; DDHQ went to Likely D on Oct 8 and Cook to Lean D on Oct 23 with no new public number behind either move.
