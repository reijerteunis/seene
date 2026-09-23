---
id: SEEN-007
title: "Provision GCP europe-west4 and Supabase EU with telemetry"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-006, SEEN-092]
status: todo
---
# SEEN-007: Provision GCP europe-west4 and Supabase EU with telemetry

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Provision the GCP project in europe-west4 with Cloud Run services for api, worker and web (min instances 1 for api and worker), Memorystore Redis, Secret Manager, Cloud Logging and Trace, Cloud Armor in front of web, and a Supabase project in the EU with Postgres, Auth and Storage, all declared in Terraform under infra/. Wire OpenTelemetry in apps/api and apps/worker so every trace and log line carries tenant_id and a cost attribute and ships to Cloud Logging. Design decision: per-tenant cost is a log attribute from day one so the day-120 gross-margin metric needs no retrofit.

## Acceptance criteria

- [ ] terraform apply from infra/ creates every resource in europe-west4 and the Supabase project is in an EU region
- [ ] The three Cloud Run services deploy from the GitHub Actions pipeline on merge to main
- [ ] A request through apps/api produces a trace in Cloud Trace carrying a tenant_id attribute
- [ ] A Cloud Logging query filtered by tenant_id returns the per-tenant cost log lines for a test job
- [ ] Daily backups and point-in-time recovery are enabled on the Supabase Postgres

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Blocks

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
