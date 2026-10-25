#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec node scripts/sync-bundle.mjs "${1:?Usage: scripts/sync-bundle.sh release_id}"
