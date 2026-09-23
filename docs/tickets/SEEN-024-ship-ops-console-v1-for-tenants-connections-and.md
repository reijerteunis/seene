---
id: SEEN-024
title: "Ship ops console v1 for tenants, connections and sync status"
epic: E5
epic_name: "Customer inbox and ops console"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-014, SEEN-021]
status: todo
---
# SEEN-024: Ship ops console v1 for tenants, connections and sync status

| | |
|---|---|
| Epic | E5 Customer inbox and ops console |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Build the first ops console pages in apps/web behind Supabase Auth with an ops role: create a tenant, add a connection (marketplace, country, credential reference), see last_sync per stream, rows ingested, rate-limit hits and job failures, and the findings list per tenant. Server components read through RLS with an ops policy so the console never bypasses the tenant boundary.

## Acceptance criteria

- [ ] An ops user can create a tenant and a connection and trigger a backfill from the console
- [ ] Connection page shows last_sync per stream and the last 20 job runs with status
- [ ] Findings list filters by marketplace, rule and status and links to the evidence refs
- [ ] A user without the ops role receives HTTP 403 on every console route

## Depends on

- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give tenants one inbox for approvals, findings, claims and statements and give ops one console for tenants, connections, runs and costs.
