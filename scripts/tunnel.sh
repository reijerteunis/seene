#!/usr/bin/env bash
# Puts the local customer inbox and webhook endpoints on a public HTTPS URL, so a
# pilot brand and Postmark can reach a laptop.
#
# Read this before you run it: while the tunnel is open, that brand's data is on
# this machine. There is no cloud until the go decision in SEEN-007, so the laptop
# is the production environment for anyone you hand this URL to. Close it when the
# session ends, and do not hand the URL to a brand who has not been told where
# their data lives.
set -euo pipefail

port="${1:-${PORT:-8080}}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed. 'brew install cloudflared', then try again." >&2
  exit 1
fi

if ! curl -sS -o /dev/null --max-time 2 "http://127.0.0.1:${port}/health"; then
  echo "Nothing is answering on http://127.0.0.1:${port}/health. Run 'pnpm dev' first." >&2
  exit 1
fi

echo "==> Tunnelling http://127.0.0.1:${port}"
echo "    Postmark inbound webhook: <the https URL below>/webhooks/postmark/inbound"
echo "    Pilot data stays on this machine. Close the tunnel when you are done."
echo

# A quick tunnel: no Cloudflare account, a fresh trycloudflare.com hostname each run.
exec cloudflared tunnel --url "http://127.0.0.1:${port}"
