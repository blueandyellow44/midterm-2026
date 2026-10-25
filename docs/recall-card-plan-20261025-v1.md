# Recall comparison on the main race cards

Goal and done: an average voter can see how polls using reported 2024 vote compare with polls that explicitly do not, directly beneath the existing race reading. Five supported races show the existing calculator-owned contrast; the other eight retain their complete polling cards without empty comparison panels. No numerical or eligibility change.

Files: new components/RecallComparison.tsx and focused server-rendering tests; lib/data.ts joins the existing sealed comparison and its inclusion list; components/RaceOverview.tsx places it in both compositions; app/globals.css styles it; .interface-design/system.md records the authorized pattern; generated public/_headers and versioned browser/HTTP evidence; existing run-state, hub, todo and Daily receive bounded updates.

Dependencies: current immutable release 20261025T121938-0700-stage2-df9d158-6ec76c0a50, existing comparison group means/counts/stratum/inclusion IDs, installed production stack, real Chrome and existing Workers deployment authorization. No new service, credential or package.

Intent: a voter scanning a race needs a clear lead first and a legible explanation of methodological disagreement second, with no implied accuracy winner. Domain: electorate, reported past vote, sample adjustments, fieldwork, pollsters, candidate leads. Color world: warm paper, charcoal ink, Democratic blue, Republican red, orange navigation. Signature: paired method readings directly under a single race lead. Replace another research table with two labelled readings; replace YES/NO jargon with explicit method labels; replace an unexplained delta with a plain-language sentence.

Component design: preserve approved warm-white/charcoal tokens and candidate blue/red; method groups stay neutral to avoid encoding either as partisan or better. One subtle dividing line within the existing card, no extra nested cards or motion. Existing Manrope labels and Plex tabular numbers. Four-pixel spacing scale. Mobile pairs stack their own text naturally inside the existing dedicated mobile composition. Sources and methodological detail use a native disclosure, with 44px targets.

Failures: absent, null or malformed groups render no comparison, never zeros; negative or rounding-level differences have correct direction/tie language; unknown recall practice cannot become NO; repeated pollster waves must not become an independently weighted poll average in the UI. Use the sealed means and counts, and explain equal pollster weighting. Small samples and pollster/timing confounding stay visible; individual dates and source links are one disclosure away.

Verification: server-render missing/malformed/zero/tie/both-direction cases first; all five production comparisons and inclusion IDs match the sealed bundle; all 13 primary readings remain; desktop/mobile at 375/768/1280/1440 in both themes, open source disclosures and keyboard navigation, no overflow/CSP/console issues; production build and all live route/header/asset/404 checks, matching tested/live HTML. Data bundle hash stays identical.

Rollback: timestamped snapshots before edits, local commits and previous Cloudflare version 693a67fb-4b52-46d5-9e79-345bd26ce167. Preserve the immutable data release. No push, domain binding, scoring spend or lessons write.
