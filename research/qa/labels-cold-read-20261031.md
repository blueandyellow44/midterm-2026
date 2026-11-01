# Cold read of every short label on the built site, 2026-10-31

Method: every aria-label, title, and short element string (3 to 70 characters) was extracted from the built HTML of all 76
routes (948 distinct strings), then handed to a reader with no project context, asked to mark what a first-time visitor
would misread and offer a plainer rewrite. Triage by Max's standing rulings is in the right column.

| Route | Text | Why it misreads | Rewrite offered | Triage |
|---|---|---|---|---|
| /race/* | Recall YES / NO / UNVERIFIED; "Recall" column head | reads as a recall election | Asks 2024 vote: yes / no / unknown | fix |
| / | ▲ YES · ● NO · ■ UNVERIFIED | legend answers an unshown question | ▲ Uses 2024 vote · ● Does not · ■ Unknown | fix |
| / | Race balanced | reads as racial balance | One weight per contest | fix |
| / | My bet 1.9; Bet chip | reads as betting odds | My call: 1.9 pts | ruling: "bet" is the thesis; keep |
| /race/* | Chance to win, at my bet | bookmaker odds | Chance to win, my call | ruling; keep |
| /race/* | 0.9 → I | "I" ambiguous; arrow unexplained | 0.9 toward the independent | fix |
| / | 4.8 → D | bare number pointing at a letter | Pull: 4.8 toward D | consider |
| / | 5.5 toward R (sub-line) | polls favored R, or R beat the polls? | R beat polls by 5.5 | fix (direction anchor) |
| / | ◀ Republicans · Democrats ▶ | reads as who wins | ◀ Polls miss R · Polls miss D ▶ | fix |
| / | Last fall 7.3 | unknown election, 7.3 of what | Nov 2025: 7.3 toward D | consider |
| / | ’20 ’16 ’24 ’22 Bet ’25 | out of order, mixed with Bet | years in order | ruling (ruler marks by value); keep |
| / | Undertow minus the polls; Undertow as a column | site name as a number | Our number minus the polls | ruling; keep |
| / | The pull; Why the pull | undefined noun | The lean we add | ruling ("the pull is the headline"); keep |
| / | Likely · Lean (legend) | no party attached | Likely either · Lean either | fix |
| / | · 51 for control (50-50 goes R) | fragment, tie rule unexplained | 51 to control; a tie goes to R | fix |
| / | Fund. | reads as money | Basics | ruling (chip label); consider "Fundamentals" on wide screens |
| / | This state’s polling record · D +0.8 | sign direction unclear | Polls undercounted D by 0.8 | fix (direction anchor) |
| /scoreboard/ | Closer; Board; The count | referents unstated | Which was closer; Polls; Actual result | fix |
| /race/*, / | freezes Nov 2; Freezes in 5 days; Freeze status | software freeze | locks Nov 2 | Max's call ("freeze" is the project's word) |
| /race/* | lines: weekly average · ▲ weights on 2024 vote · ● does not | fragments | Line: weekly avg · ▲ Uses 2024 vote · ● Does not | fix |
| /race/* | point lead | fragment | lead, in points | fix |
| /race/* | 1 poll · none independently paid for | reads as nobody paid | all campaign-sponsored | fix |
| /race/* | Extra money vs typical | which money, typical of what | Outside money vs a normal race | fix |
| / | Get the grade · Send me the grade | grade of what | Email me the results check | consider |
| /excluded/ | Quarantine ledger; Manifest SHA-256; Analytical cutoff | jargon | Polls set aside; File checksum; Data cutoff | fix |
| /method/ | analytical_as_of | code identifier as heading | Data as of | fix |
| /method/ | Winner right; Brier; RCV FIRST fallback; BOTH / HOUSE_ONLY (stored); Indep. waves | run-together words, unexpanded abbreviations | Picked the winner; Brier score (lower is better); ... | fix |
| / | October principal estimates | "principal" reads as money or a school head | Main October estimates | fix |
| /race/* | Outside spending · matches the polls | size or direction? | agrees with the polls | fix |
| / | Pooled · Sponsor restricted · Matched population | keys with no visible question | All polls · Non-campaign polls · Same voters sampled | fix |

Patterns (reader's words): the site's own vocabulary (pull, lean, bet, freeze, reading, Undertow as a number) is used as if
already defined; direction and sign are never anchored (toward R, D +0.8, arrows, slider ends); keys, legends and sub-lines
are fragments that depend on a number or question elsewhere; Method and Excluded leak code identifiers into headings.

What the QA sweep checks instead (scripts/qa/page/qa.js): horizontal scroll, text spilling or offscreen, fonts under 11px,
covered or small tap targets, leaked NaN/undefined/"1 polls". It has no notion of meaning, consistency or direction.
