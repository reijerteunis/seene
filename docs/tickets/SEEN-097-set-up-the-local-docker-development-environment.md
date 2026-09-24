---
id: SEEN-097
title: "Set up the local Docker development environment"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-006]
status: doing
---
# SEEN-097: Set up the local Docker development environment

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Make the whole stack run on a laptop before any cloud exists: the Supabase CLI local stack (Postgres, Auth, Storage, Studio) via supabase start, Redis 7 for BullMQ, Mailpit for outbound mail and a fixture endpoint that replays Postmark inbound webhooks, an OpenTelemetry collector that prints traces and per-tenant cost lines locally, and pnpm dev:up, dev:down and db:reset scripts in the root package.json. Implement the three abstractions the cloud will later configure: a secrets provider (a .env.local-backed implementation now, Secret Manager after go-live), a storage provider (local Supabase Storage now, the EU project later) and telemetry (console and collector now, Cloud Logging later). Add an optional Cloudflare Tunnel script that exposes the customer inbox and webhook endpoints to pilot brands from the local environment, with the security note that pilot data then lives on the development machine until go-live. Design decision: development and pilots run locally, the cloud is a configuration switch, and the go-live is a separate decision (SEEN-007).

## Acceptance criteria

- [ ] pnpm dev:up starts Supabase, Redis, Mailpit and the collector and pnpm dev serves api, worker and web against them on a clean machine within 10 minutes
- [ ] pnpm test runs the full suite against the local stack and CI runs the identical services, so a test that passes locally passes in CI
- [ ] The secrets, storage and telemetry providers are selected by environment variables only and a unit test proves the code has no direct import of a cloud SDK outside the provider packages
- [ ] A Postmark inbound fixture replayed through the local endpoint creates a message thread, and an outbound mail appears in Mailpit
- [ ] The tunnel script exposes the inbox on an HTTPS URL, and the README states that pilot data stays on the development machine until go-live

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages

## Blocks

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table
- [SEEN-007](SEEN-007-go-live-on-google-cloud-after-the-go-no-go.md): Go live on Google Cloud after the go/no-go decision

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
