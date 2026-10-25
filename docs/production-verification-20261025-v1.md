# Local production verification

Verified 2026-10-25 before the local Chrome handoff. Data release `20261025T121938-0700-stage1b-73514ef-a4cb7de3a4`; manifest SHA-256 `6809e633cfa9a9748d2ffa131f9e138a5c38906a9a83f1b186b39c003ad62f0e`.

- Nine Vitest cases passed: CSV boundaries and volume, bundle tampering/schema/identity failures, display formatting, and actual server-rendered chart titles. TypeScript check passed.
- Final HTML bytes match all per-route CSP hashes. No script unsafe-inline, nonce, inline-style exception or runtime API is used. The static 404 fallback prevents unknown paths entering Next server/ISR code.
- All 17 published routes returned 200 with the exact CSP and global headers. SVG/PNG favicons and OG image returned 200 with the intended MIME type. Unknown route returned 404. See local-http-20261025-v5.json.
- Real Chrome completed home → mobile → race → method → grading. Preference selection persisted. All 17 routes passed both compositions in light and dark modes at widths 375, 768, 1280 and 1440: 272 checks, zero overflow, completed hydration and zero console warnings/errors. See local-browser-20261025-v3.json.
- Keyboard activated the evidence disclosure. Skip navigation focuses MAIN#main. Interactive source and footer links use 44px targets. Text/semantic colors were checked for AA contrast; dark colors use separate tokens.
- npm audit reported zero vulnerabilities. Staged source and emitted HTML scans found none of the checked private-key/API-token patterns. No project .env, .dev.vars, account credential or cache is tracked. Data/ is private build input with a strict manifest/file allowlist.
- React escapes text; Markdown does not enable raw HTML; external source links use noopener noreferrer. There are no forms, auth, SQL, payment, upload or API endpoints requiring those security controls.

The chart hydration failure was reproduced in the development diagnostic: multi-part SVG title children were serialized as empty titles. Changed each to one formatted string; the server-rendering regression and complete final browser run pass. Earlier failed browser evidence is retained in versioned reports. The temporary preference-loader diagnostic change was removed after isolating the chart cause.

Local Chrome handoff: http://localhost:8788/ in the current task tab. This record does not claim the subsequent live deployment has passed.
