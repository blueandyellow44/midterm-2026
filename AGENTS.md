<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Gate (Max, 2026-11-04)

CI (`.github/workflows/ci.yml`: typecheck and tests) is a required check on `main`; nothing merges red.
A change that adds behavior adds its test first, then the code that passes it. Never edit the workflow,
skip a test, or widen a type to make a red build pass; fix the cause or stop and say so. Greptile is advisory.
