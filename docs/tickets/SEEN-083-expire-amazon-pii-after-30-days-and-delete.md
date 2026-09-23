---
id: SEEN-083
title: "Expire Amazon PII after 30 days and delete tenants on request"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-013, SEEN-027]
status: todo
---
# SEEN-083: Expire Amazon PII after 30 days and delete tenants on request

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Add a nightly job in apps/worker that nulls buyer name and address fields on Amazon orders older than 30 days unless an open claim references them, with encryption at rest for those columns, and a deletion-on-request job that removes a tenant's rows and storage objects within 30 days and writes a signed deletion report. Design decision: expiry is a nulling job on typed columns rather than row deletion, so orders and findings keep their history.

## Acceptance criteria

- [ ] Amazon buyer PII older than 30 days is nulled nightly except where an open claim references the order
- [ ] PII columns are encrypted at rest and readable only through the API
- [ ] Deletion job removes all rows and storage objects for a test tenant and the report lists counts per table
- [ ] Tenant deletion completes within 30 days of the request and is logged in audit_events

## Depends on

- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
