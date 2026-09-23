---
id: SEEN-082
title: "Run RLS penetration tests and the restore drill"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-008, SEEN-032]
status: todo
---
# SEEN-082: Run RLS penetration tests and the restore drill

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Write a penetration test suite under tools/security that attempts cross-tenant reads and writes on every table through the API, the web server components and direct Postgres with forged and expired JWTs, and a restore drill script that restores the daily backup and a point-in-time snapshot into a fresh Supabase project and verifies row counts and audit chain integrity. Design decision: both suites run from CI on a schedule, so the drill is repeatable rather than a one-off.

## Acceptance criteria

- [ ] Pen test suite covers 100% of tables and passes with zero cross-tenant reads or writes
- [ ] A forged JWT with another tenant id returns zero rows and the attempt is logged
- [ ] Restore from the daily backup completes in under 60 minutes with row counts matching the source
- [ ] Audit chain verification passes on the restored database

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table
- [SEEN-032](SEEN-032-write-append-only-audit-events-before-every.md): Write append-only audit_events before every side effect

## Blocks

- [SEEN-085](SEEN-085-run-restore-drill-close-pen-test-findings-sign.md): Run restore drill, close pen-test findings, sign metrics pack

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
