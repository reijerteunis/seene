---
id: SEEN-033
title: "Implement policy gate v1 with caps and reversibility"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: []
depends_on: [SEEN-032]
status: todo
---
# SEEN-033: Implement policy gate v1 with caps and reversibility

| | |
|---|---|
| Epic | E4 Agent runtime, policy gate, approvals and audit log |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | none |
| Status | todo |

## Description

Implement the policy gate in packages/core/policy: it reads the tenant's policies row for the action type (mode autonomous, approval or refuse), applies the MVP caps (per claim EUR 1,000, per day EUR 5,000 filed per tenant), checks reversibility and the never list (refunds, purchase orders, account settings, delistings) and returns autonomous, approval or refuse with a reason. Default policies for a new tenant are approval for every action type, and the decision is written to agent_actions and audit_events before anything executes.

## Acceptance criteria

- [ ] A claim of EUR 1,001 returns refuse with reason cap_per_claim and EUR 999 returns approval under default policy
- [ ] Filing the sixth claim of EUR 1,000 in one day returns refuse with reason cap_per_day
- [ ] Any action on the never list returns refuse regardless of the policies row
- [ ] Gate decision is written to agent_actions.decision and an audit event before the tool executes

## Depends on

- [SEEN-032](SEEN-032-write-append-only-audit-events-before-every.md): Write append-only audit_events before every side effect

## Blocks

- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff
- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-065](SEEN-065-implement-the-trust-ramp-with-autonomy-per.md): Implement the trust ramp with autonomy per action type
- [SEEN-072](SEEN-072-implement-the-price-governor-with-bands.md): Implement the price governor with bands, ceilings and cooldowns
- [SEEN-079](SEEN-079-propose-campaign-budgets-through-the-gate-no.md): Propose campaign budgets through the gate, no autonomous creation

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
