#!/usr/bin/env bash
# Brings up everything the stack needs, in the order it needs it, and says where
# each piece is listening. Safe to run again: every step is idempotent.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop, or 'colima start', and try again." >&2
  exit 1
fi

# Studio mounts this directory, and docker chowns a mount source it creates itself,
# which a virtiofs mount (colima, Rancher) denies. Creating it first avoids that.
mkdir -p supabase/snippets

echo "==> Redis, Mailpit and the OpenTelemetry collector"
docker compose up -d --wait

echo "==> Supabase (Postgres, Auth, Storage, Studio)"
supabase start >/dev/null

echo
echo "  Supabase API     http://127.0.0.1:54321"
echo "  Supabase Studio  http://127.0.0.1:54323"
echo "  Postgres         postgresql://postgres:postgres@127.0.0.1:54322/postgres"
echo "  Redis            127.0.0.1:${REDIS_PORT:-6379}"
echo "  Mailpit          http://127.0.0.1:${MAILPIT_HTTP_PORT:-8025}  (SMTP ${MAILPIT_SMTP_PORT:-1025})"
echo "  Collector        http://127.0.0.1:${OTLP_HTTP_PORT:-4318}  (metrics :${OTLP_METRICS_PORT:-8888})"
echo
echo "  'supabase status -o env' prints the keys for .env.local."
echo "  'pnpm dev' now serves api, worker and web against all of it."
