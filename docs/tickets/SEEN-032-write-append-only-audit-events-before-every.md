---
id: SEEN-032
title: "Write append-only audit_events before every side effect"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-008]
status: todo
---
# SEEN-032: Write append-only audit_events before every side effect

| | |
|---|---|
| Epic | E4 Agent runtime, policy gate, approvals and audit log |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Implement the audit log in packages/core/audit: audit_events is append-only (insert-only role, no update or delete grants, a trigger that raises on modification) and every agent action, gate decision, approval and outcome writes an event before the side effect, with a hash chain over the previous event per tenant. The runtime cannot execute a tool until the proposed event is committed.

## Acceptance criteria

- [ ] UPDATE or DELETE on audit_events fails for every database role including the service role
- [ ] A proposed event exists before the tool's HTTP call in an integration test with a mocked connector
- [ ] Each event stores the sha256 of the previous event for the tenant and a verification script reports zero breaks
- [ ] GET /tenants/:id/audit returns events filtered by claim, run or action

## Depends on

- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Blocks

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-082](SEEN-082-run-rls-penetration-tests-and-the-restore-drill.md): Run RLS penetration tests and the restore drill

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
