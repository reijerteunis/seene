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

What an event may hold is settled by SEEN-008. The trade record schema classifies `audit_events.payload` as not buyer PII on the condition that this ticket and SEEN-034 keep it so: the payload records what was decided and the identifiers it was decided about, never the buyer's own words. A draft reply belongs in `messages.body` and a submitted claim text in `claims.claim_text`, where SEEN-083's 30-day expiry job can reach them; copied into an append-only table neither can be expired without breaking the guarantee this log exists for. The reason is in that column's comment in `supabase/migrations/20260929000002_trade_record_v1_free_text_classification.sql`, SEEN-008's second review recorded the promise living nowhere this ticket's author would read it as F34, and `packages/core/db/schema.test.ts` goes red if the criterion below leaves this ticket.

## Acceptance criteria

- [ ] UPDATE or DELETE on audit_events fails for every database role including the service role
- [ ] An audit_events payload holds what was decided and the identifiers it was decided about and never the buyer's own words, with a test that refuses a draft reply or a claim text written into it
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
