#!/usr/bin/env bash
# Replays a Postmark inbound fixture against the local endpoint, which is how you
# exercise the forwarded-mailbox path without waiting for a real mail.
#
#   pnpm replay:inbound                                   the compensation confirmation
#   pnpm replay:inbound apps/api/src/webhooks/fixtures/postmark-inbound-reply.json
set -euo pipefail

cd "$(dirname "$0")/.."

fixture="${1:-apps/api/src/webhooks/fixtures/postmark-inbound.json}"
url="${SEEN_API_URL:-http://127.0.0.1:8080}/webhooks/postmark/inbound"

echo "==> POST $fixture to $url"
curl --fail-with-body -sS -X POST "$url" \
  -H 'content-type: application/json' \
  --data-binary "@${fixture}"
echo
