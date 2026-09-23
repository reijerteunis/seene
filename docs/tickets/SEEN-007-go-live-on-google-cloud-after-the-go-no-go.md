---
id: SEEN-007
title: "Go live on Google Cloud after the go/no-go decision"
epic: E0
epic_name: "Foundations and registrations"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-097, SEEN-014]
status: todo
---
# SEEN-007: Go live on Google Cloud after the go/no-go decision

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Opens only after Ruud records a go decision in the journal (the local Docker environment from SEEN-097 is the development and pilot environment until then). Provision the GCP project in europe-west4 with Cloud Run services for api, worker and web (min instances 1 for api and worker), Memorystore Redis, Secret Manager, Cloud Logging and Trace, Cloud Armor in front of web, and a Supabase project in the EU with Postgres, Auth and Storage, all declared in Terraform under infra/. Switch the secrets, storage and telemetry providers to their cloud implementations by configuration only; no application code changes. Migrate the pilot tenants' data from the local environment with a rehearsed export and import. Design decision: the cloud is a configuration of abstractions the code already uses, so go-live is an infrastructure ticket, not a refactor.

## Acceptance criteria

- [ ] A go decision by Ruud is recorded in the SEEN-007 journal before any resource is created
- [ ] terraform apply from infra/ creates every resource in europe-west4 and the Supabase project is in an EU region
- [ ] The three Cloud Run services deploy from the GitHub Actions pipeline on merge to main and the same test suite passes against the cloud environment
- [ ] Secrets, storage and telemetry switch to Secret Manager, Supabase Storage and Cloud Logging by configuration; a request through apps/api produces a trace in Cloud Trace carrying a tenant_id attribute
- [ ] Pilot tenants' data is migrated with a rehearsed export and import and the local environment is retired for those tenants; daily backups and point-in-time recovery are enabled

## Depends on

- [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md): Set up the local Docker development environment
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
