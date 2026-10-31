#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
[ "$#" -ge 1 ] || { echo "Usage: scripts/sync-bundle.sh release_id [--unfreeze]" >&2; exit 2; }
exec node scripts/sync-bundle.mjs "$@"
