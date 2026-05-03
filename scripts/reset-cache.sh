#!/usr/bin/env bash
# Wipe the local preview cache (LRU-managed, fully recoverable from GitHub).
# Thumbnails are intentionally NOT wiped — they are permanent.
# Usage: bash scripts/reset-cache.sh
set -euo pipefail

BOLD=$(tput bold 2>/dev/null || true)
RESET=$(tput sgr0 2>/dev/null || true)
GREEN=$(tput setaf 2 2>/dev/null || true)
YELLOW=$(tput setaf 3 2>/dev/null || true)

info()  { echo "${GREEN}▶${RESET} $*"; }
warn()  { echo "${YELLOW}⚠${RESET}  $*"; }

warn  "This will delete:"
warn  "  • data/cache/previews/   (all preview-size images)"
warn  "  • data/cache/manifest.json (re-fetched from GitHub on next request)"
echo

read -r -p "Continue? [y/N] " confirm
case "$confirm" in
  [yY][eE][sS]|[yY]) ;;
  *) echo "Aborted."; exit 0 ;;
esac

rm -rf data/cache/previews
mkdir -p data/cache/previews
info "data/cache/previews/ wiped"

if [ -f data/cache/manifest.json ]; then
  rm data/cache/manifest.json
  info "data/cache/manifest.json removed"
fi

echo
info "Cache reset complete. Thumbnails preserved. App will recover from GitHub."
echo
echo "${BOLD}Note:${RESET} if containers are running, the next request will re-warm the cache."
