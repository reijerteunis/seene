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
status: review
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
| Status | review |

## Description

Make the whole stack run on a laptop before any cloud exists: the Supabase CLI local stack (Postgres, Auth, Storage, Studio) via supabase start, Redis 7 for BullMQ, Mailpit for outbound mail and a fixture endpoint that replays Postmark inbound webhooks, an OpenTelemetry collector that prints traces and per-tenant cost lines locally, and pnpm dev:up, dev:down and db:reset scripts in the root package.json. Implement the three abstractions the cloud will later configure: a secrets provider (a .env.local-backed implementation now, Secret Manager after go-live), a storage provider (local Supabase Storage now, the EU project later) and telemetry (console and collector now, Cloud Logging later). Add an optional Cloudflare Tunnel script that exposes the customer inbox and webhook endpoints to pilot brands from the local environment, with the security note that pilot data then lives on the development machine until go-live. Design decision: development and pilots run locally, the cloud is a configuration switch, and the go-live is a separate decision (SEEN-007).

## Acceptance criteria

- [x] pnpm dev:up starts Supabase, Redis, Mailpit and the collector and pnpm dev serves api, worker and web against them on a clean machine within 10 minutes
- [x] pnpm test runs the full suite against the local stack and CI runs the identical services, so a test that passes locally passes in CI
- [x] The secrets, storage and telemetry providers are selected by environment variables only and a unit test proves the code has no direct import of a cloud SDK outside the provider packages
- [x] A Postmark inbound fixture replayed through the local endpoint creates a message thread, and an outbound mail appears in Mailpit
- [x] The tunnel script exposes the inbox on an HTTPS URL, and the README states that pilot data stays on the development machine until go-live

## Outcome

The whole stack runs on a laptop with no cloud anywhere in it, and the cloud is three
environment variables rather than a refactor.

`docker-compose.yml` starts Redis 8, Mailpit and an OpenTelemetry collector;
`supabase/config.toml` starts Postgres, Auth, Storage and Studio. `pnpm dev:up` starts
both and prints where each piece listens, `pnpm dev:down` stops them and keeps the
database, `pnpm db:reset` throws the database away. `pnpm dev` serves api, worker and
web against all of it.

`packages/providers` is new and holds the three abstractions: `SecretsProvider`
(`env` now, `gcp-secret-manager` named and refused until SEEN-007), `StorageProvider`
(local Supabase Storage now, `gcs` later) and `TelemetryProvider` (`console` or `otlp`
now, `cloud-logging` later). Each factory reads exactly one variable and refuses a
value it does not know by naming both the variable and the value, because a factory
that quietly falls back to the local implementation is how a pilot's credentials end
up on a laptop with nothing in the log to say so. It is the only package allowed to
import a cloud SDK, and `no-cloud-sdk.test.ts` walks `apps/` and `packages/` and fails
on one anywhere else, through `import`, `export ... from`, `require` or dynamic
`import`.

`apps/api` gained the Postmark inbound endpoint and a Mailpit-backed mailer. The thread
it creates lives in an in-memory store behind `ThreadStore`; SEEN-008 creates
`message_threads` with its `tenant_id` and RLS policy and SEEN-062 does the real
matching against orders and claims.

### What was measured rather than assumed

Ten containers, about 805 MiB of memory between them, on a 2 CPU and 4 GiB Docker VM
with room to spare. Supabase's `analytics`, `realtime` and `edge_runtime` are off:
analytics alone is Logflare plus a second Postgres, and nothing in the product uses any
of the three.

The clean-machine claim is settled by CI rather than by this laptop, because CI is an
actually clean machine. The node job went from empty checkout to green in 4 minutes 4
seconds: install, pull every image, `docker compose up`, `supabase start`, lint,
typecheck, the full suite and the build. The laptop figures are 49s for a first
`supabase start` and 24s warm, with the three compose services healthy inside 10s.

CI runs the same `docker-compose.yml` and the same `supabase/config.toml` rather than
restating the images as workflow service containers, so the two definitions cannot
drift. The `redis:8` service container SEEN-006 added is gone, and
`docs/architecture.md` now says Redis 8 in both places it mentioned Redis 7.

### Verified by running it, not only by tests

`pnpm replay:inbound` posted the committed fixture to the running server and got
`{"threadId":"3ec7...","created":true}`; the reply fixture got the same thread id and
`"created":false`. The collector printed `seen.tenant_id`, `seen.operation`,
`seen.model`, `seen.cost_cents: Int(7)` and `seen.currency: Str(EUR)`. `pnpm tunnel`
put the api on `https://…trycloudflare.com`, where `/health` answered 200 over verified
TLS and the inbound fixture answered 202; the tunnel was closed immediately after and
the URL then answered 530.

### Known and deliberately left

A forwarded mail carrying no mailbox hash names no tenant, and the endpoint answers 400,
which Postmark retries. The right answer is the ops queue SEEN-062 builds, and a 202
without somewhere to put the mail would silently drop it, which is worse than a retry.

`packages/providers/src/stack.test.ts` was written after the implementations it covers,
so it is regression cover rather than a red-green cycle. Sequence 13 of the journal says
so and why.

Two obstacles that are the machine's rather than the code's are written up in the
README: a colima profile whose disk has drifted below the instance's actual disk refuses
to start, and the file that must match is `~/.colima/_lima/<profile>/colima.yaml`; and
Studio will not start unless `supabase/snippets` exists first, which `dev:up` now
creates.

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
