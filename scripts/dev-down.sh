#!/usr/bin/env bash
# Stops everything dev:up started. The database survives: 'pnpm db:reset' is how
# you throw it away, so stopping for the day never costs you your data.
set -euo pipefail

cd "$(dirname "$0")/.."

supabase stop >/dev/null 2>&1 || true
docker compose down

echo "Stopped. Volumes kept; 'pnpm db:reset' resets the database."
