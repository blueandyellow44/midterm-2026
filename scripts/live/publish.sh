#!/usr/bin/env bash
# Election-night publish (2026-11-03): commit the live files, then test, build and deploy, stopping at the FIRST
# failure. A test run's exit code gates the deploy directly; never through grep or a trailing echo (lessons
# 2026-10-29, recurred 2026-11-03 when an `; echo` made a failing vitest look green and the deploy went out).
set -euo pipefail
cd "$(dirname "$0")/../.."
msg="${1:?usage: publish.sh \"commit message\"}"
log=.ballot-print; mkdir -p "$log"
VITEST="${PUBLISH_VITEST:-npx vitest run}"
if ! $VITEST > "$log/vitest.log" 2>&1; then echo "STOP: vitest failed (see $log/vitest.log), nothing committed or deployed"; grep -E "FAIL|×" "$log/vitest.log" | head -5; exit 1; fi
git add live/results.json live/calls.json
git diff --cached --quiet && { echo "nothing new to publish"; exit 0; }
git commit -q -m "$msg

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01LPzG9qPZ3RnuRtDWpF7mxc"
if ! npm run build:cloudflare > "$log/build.log" 2>&1; then echo "STOP: build failed (see $log/build.log), committed $(git rev-parse --short HEAD) but NOT deployed"; exit 1; fi
if ! SHIP_GUARD_ALLOW=1 npm run deploy > "$log/deploy.log" 2>&1; then echo "STOP: deploy failed (see $log/deploy.log)"; exit 1; fi
grep "live matches" "$log/deploy.log"
