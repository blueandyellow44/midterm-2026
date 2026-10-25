# Election Weather design system

Approved scope: prompt revision 2026-10-25b F4. Max approved Data Visualization Creator as the dataviz equivalent on 2026-10-25 at 13:31 PDT. Interface Design and Taste were read before implementation; Security Review is applied before local handoff and deploy.

Intent: a reader comparing evidence across thirteen races needs a legible field ledger, explicit provenance and honest missing states. This is a polling and rhetoric research tracker. No forecasts before the scheduled freeze.

Domain: field periods, recalled vote, sample eligibility, debate turns, coverage temperature. Color world: weather-station paper, graphite instrument text, ocean teal, amber warning light, slate cloud. Signature: a station masthead and an evidence ledger pairing race conditions with a separate rhetoric reading. Replace generic KPI cards with a count strip; replace party-colored recall categories with color plus shape; replace a shrunken desktop table with a dedicated mobile race index.

Palette: warm white #f5f4ef and graphite #172b2b; teal #145f5a; amber #805411; slate #52616b. Dark: #101d20, #e7edeb, #87c9be, #e8bf79, #acb8c0. Depth uses borders only. Manrope for interface and IBM Plex Mono for measurements. Base 16px; spacing unit 4px; 44px minimum interactive targets. No animation. Both modes complete. Recall YES = teal triangle, NO = amber circle, UNVERIFIED = slate square. Charts include accessible text tables and labels.

Desktop composition: full masthead, context column, wide race ledger and separate research notes. Mobile composition: compact station header, concise status, vertical race records with a separate expandable evidence section. Device class chooses the initial layout; the explicit switch persists. Native links use prerendered HTML without runtime data requests.

Definition of done: all F4 routes prerendered, immutable release verified, production CSP hashes match final bytes, Vitest and type checks pass, browser flow in Max's real Chrome and all viewport checks pass, one local tab handed over before authorized workers.dev deployment, live checks pass. Failure modes: stale/mixed bundle fails validation before build; CSP drift fails final static verifier; missing evidence renders NA/UNVERIFIED; failed route blocks deploy. Rollback: previous local commit plus previous immutable data release and recorded Cloudflare version. No GitHub push or domain binding.


## Visual refinement, 2026-10-25

Max requested stronger design using the plugins, then explicitly invoked High-End Visual Design. Read design/1.0.1/skills/soft-ui/SKILL.md (frontmatter name high-end-visual-design), in addition to Interface Design and Taste. Chosen direction: soft structural surfaces with an editorial split, a nested weather instrument bezel, locally served Manrope and Plex Mono, floating navigation, contour-line signature, circular CTA arrow enclosure and a deliberately distinct mobile field-record composition. Preserve the explicit no-animation requirement from the execution prompt; it overrides the skills’ default motion recipes. No additional design approval gate is inferred.


## Consumer hierarchy, 2026-10-25

Max flagged the research terminology as difficult for average voters. The default home now presents the matchup, candidate lead in the existing calculated preliminary/weighted margin and the count of comparable estimates. These are display labels, not new statistics. Technical readings and plain-language definitions sit behind See the evidence; the complete research ledger and recall comparisons remain in explicit drawers. Separate desktop and mobile compositions use the same reading component and evidence. Missing averages stay missing. No invented confidence ratings or probabilities.


## Palette recommendation, 2026-10-25

Max questioned green’s dominance. Explained it came from the weather-station concept and recommended a warm-white/charcoal publication surface, restrained burnt-orange navigation accents and semantic blue/red candidate data. Applied that reversible palette to the next preview. Weather contours stay decorative; recalled-vote classes retain their separately labeled color-and-shape encoding.


## Polling-only core clarification, 2026-10-25

A user-authorized side-chat decision was conveyed by Codex chat 01a174d6-18d1-7c12-b96d-0e9cd5fdec7f: one clear polling estimate per race, number and age of contributing polls, documented recency/sample/method/track-record weighting; rhetoric optional and separate, spending outside the core product. Attempted read_thread to inspect the originating turns; the ephemeral chat cannot expose turns through that API. This matches the current main-chat simplification and is incorporated as a scope clarification, without expanding the model. Dates shown on cards come from sorting the calculator-selected contributing rows; the app does not calculate a new statistic.


## Recall comparison on public cards, 2026-10-25

Max explicitly authorized bringing the recall-weighting comparison onto the main cards. Preserve the headline and palette. A full-width, line-separated section pairs “Uses 2024 vote” and “Does not use it,” with sealed pollster-balanced group means, candidate leads, poll and firm counts, a plain-language directional gap and visible timing/pollster limits. Neutral method labels; candidate blue/red encodes only the candidate lead. A native disclosure contains individual field dates and primary sources, population/ballot scope, race-wide unknown-method count, equal-pollster explanation and full confounding text. Only supported comparisons render; never add empty panels to the other eight races. Desktop and mobile keep their existing separate compositions. No estimator or release change.
