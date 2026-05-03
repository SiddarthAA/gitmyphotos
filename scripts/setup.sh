#!/usr/bin/env bash
# PhotoVault setup script
# Usage: bash scripts/setup.sh
set -euo pipefail

BOLD=$(tput bold 2>/dev/null || true)
RESET=$(tput sgr0 2>/dev/null || true)
GREEN=$(tput setaf 2 2>/dev/null || true)
YELLOW=$(tput setaf 3 2>/dev/null || true)
RED=$(tput setaf 1 2>/dev/null || true)

info()    { echo "${GREEN}▶${RESET} $*"; }
warn()    { echo "${YELLOW}⚠${RESET}  $*"; }
error()   { echo "${RED}✖${RESET}  $*" >&2; }
heading() { echo; echo "${BOLD}$*${RESET}"; }

# ── 1. Check Docker ───────────────────────────────────────────────────────────
heading "Checking prerequisites"

if ! command -v docker &>/dev/null; then
  error "Docker not found. Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi
info "Docker found: $(docker --version)"

if ! docker compose version &>/dev/null 2>&1; then
  error "Docker Compose plugin not found. Update Docker Desktop or install the plugin."
  exit 1
fi
info "Docker Compose found: $(docker compose version)"

# ── 2. Ensure data/ structure ─────────────────────────────────────────────────
heading "Setting up data directory"

mkdir -p data/cache/thumbs data/cache/previews
info "data/cache/thumbs and data/cache/previews ready"

# ── 3. Create data/.env from .env.example if missing ─────────────────────────
if [ ! -f data/.env ]; then
  if [ -f .env.example ]; then
    cp .env.example data/.env
    warn "Created data/.env from .env.example"
    warn "Fill in GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET before continuing."
    echo
    echo "  Edit data/.env, then re-run: ${BOLD}bash scripts/setup.sh${RESET}"
    exit 0
  else
    error ".env.example not found — cannot create data/.env"
    exit 1
  fi
fi

# ── 4. Validate that client credentials have been set ─────────────────────────
heading "Validating data/.env"

source_env() {
  # Export only the lines that look like KEY=VALUE
  set -o allexport
  # shellcheck source=/dev/null
  source data/.env
  set +o allexport
}
source_env 2>/dev/null || true

if [ -z "${GITHUB_CLIENT_ID:-}" ] || [ -z "${GITHUB_CLIENT_SECRET:-}" ]; then
  warn "GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET is not set in data/.env"
  warn "Create a GitHub OAuth App at https://github.com/settings/developers"
  warn "  Homepage URL:  http://localhost:3000"
  warn "  Callback URL:  http://localhost:8000/api/auth/callback"
  echo
  echo "Then edit ${BOLD}data/.env${RESET} and re-run: ${BOLD}bash scripts/setup.sh${RESET}"
  exit 0
fi
info "OAuth credentials present"

# ── 5. Start containers ───────────────────────────────────────────────────────
heading "Starting PhotoVault"

docker compose up --build -d
echo
info "PhotoVault is running at ${BOLD}http://localhost:3000${RESET}"
info "Backend API at         ${BOLD}http://localhost:8000${RESET}"
echo
info "To stop:   docker compose down"
info "To logs:   docker compose logs -f"
