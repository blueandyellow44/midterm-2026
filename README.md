# Undertow

Live at [midtermundertow.com](https://midtermundertow.com). The 2026 Senate, governor and House races I track: the polls, and my bet on where last fall's polling miss, campaign money and early voting say they are off. By Max Sheahan. Every figure tied to a verified release.

The project started as Election Weather, a thirteen-race polling tracker. That name survives in the Worker name, a few scripts and the screenshots under `docs/`.

![Undertow desktop and mobile](docs/election-weather-desktop-v3.jpg)

## What the site shows

- **The bet.** A polling average for every race up this year, plus terms for last fall's polling miss in that state, outside campaign money, early voting and a partisan prior. One slider below the map sets a uniform shift; chips switch between readings. The bet is the only call that gets graded.
- **Four in-house models beside the bet**, in `analysis/models.py`: polls alone, fundamentals (no 2026 polls), a forecaster-style blend, and Cook's ratings as margins. Each has a center for every seat, its own backtest, and its own odds grid. They never touch the bet.
- **Win odds** from a correlated simulation in `analysis/simulate.py`, fit to the archive of past polling errors. The site interpolates a sealed odds grid; it never computes odds itself.
- **Pages.** Scoreboard, one page per race, Tonight (poll closing times shown in the reader's own time zone), Method, Grading, and Excluded, the only page that shows quarantined poll estimates.
- **The freeze.** On November 2 a Stage 3 release writes `predictions.csv`, the record the Grading page is scored against. Until then every probability is preliminary, and the site says so.

Descriptive recall-vote differences are not causal estimates, and the method page carries the limitations and the Deferred section for every release.

## Data and releases

`data/` is untracked. Its canonical home is an immutable release in a local vault bundle, and the app reads only what a release contains.

- `scripts/sync-bundle.sh <release_id>` validates an explicit public-file allowlist and the manifest hashes, then replaces `data/` atomically. It refuses to replace a frozen bundle without `--unfreeze`.
- `scripts/release_signals.py` seals releases: `--refresh` for a new data cutoff, `--correction` for a method fix at the same cutoff with byte-identical polling inputs, `--freeze` for Stage 3. It refuses a dirty tree, and the build refuses a hand-edited `derived.json`.
- A poll refresh writes one JSON record per poll under `sources/`, an auditor pass re-reads every number against its source, `scripts/merge_poll_records.py` merges, `scripts/reclassify_sponsors.py` applies the sponsor rulings, and `analysis/weight.py --derive` recomputes the derived numbers.
- `sources/` keeps the archived inputs: FEC outside spending, MIT Election Lab results, Wikipedia House results, Cook ratings, early-vote reports and the poll records themselves.

## Stack

Next.js 16, TypeScript, Tailwind 4, OpenNext for Cloudflare, Wrangler and Vitest; Python for the analysis and the release tooling. Exact versions are locked in `package-lock.json`. Separate desktop and mobile compositions share the frozen data and copy; the visible switch remembers the reader's choice. Fonts are served locally.

## Run

```sh
npm ci
sh scripts/sync-bundle.sh <release_id>
npm test
npm run build:cloudflare
npm run preview
```

Preview runs Wrangler on http://localhost:8788 with the production static headers. Next's development server is not the verification surface.

## Build and security

All routes prerender. Next builds once; `scripts/csp-hashes.mjs` hashes every inline script in the final HTML bytes; OpenNext runs with `--skipNextBuild`; `scripts/static-routes.mjs` promotes the exact HTML into Workers static assets so no prerendered route can 404. A verifier compares bytes and hashes again before deploy. The generated fallback Worker is replaced with a minimal static 404 responder, so unknown paths never reach Next's server runtime.

`public/_headers` carries the security headers with no duplicate names across overlapping rules. Scripts use per-route SHA-256 authorization, never `unsafe-inline` or nonces, and inline `style=` is refused. Styles and fonts are local. `npm audit` must show no high or critical findings before publication.

## Publish and rollback

QA runs on the built assets: `npm run qa:serve`, then `/__qa/` in a real browser must report zero failures at every required width in both compositions. `npm run deploy` publishes to midtermundertow.com, records the Cloudflare version in `.deploys/`, and byte-checks every live route against the build. `npm run ship:status` exits non-zero while anything built is not yet live.

Rollback is the previously recorded Cloudflare version plus a sync of the prior immutable release. No release is ever modified. The current release ID, analytical cutoff and manifest SHA-256 appear in every footer.

## Election night

Results enter from the AP and state data feeds, one round at a time: `scripts/live/README.md` has the rules (entry, settle, grade), the feed addresses, and the three commands a round takes.

## Verification

```sh
npm test
npm run typecheck
npm audit
python3 -m unittest discover -s tests -p 'test_*.py'
python3 analysis/weight.py --self-test
npm run test:evals
```

The bundle tests reject tampering, unknown schema versions, mixed release identity, extra files and malformed CSV. `npm run test:evals` hands each built page's visible text to Claude with a set of reader questions and grades the answers; each of its mutations (a flipped bet, a stripped direction, a hidden freeze) has been shown to make the suite fail, which is what makes a pass mean something.

## Visual direction

The card scan and numerical hierarchy follow [Kalshi](https://kalshi.com/); the explanatory approach to polls follows [538's guide to reading polls](https://www-cdn.abcnews.com/538/read-political-polls-2024/story?id=113560546). The references are presentation only. Every value on the site is Undertow's own calculator output, in polling-margin points.

## License

MIT. See `LICENSE`.
