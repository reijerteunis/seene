---
id: SEEN-065
title: "Implement the trust ramp with autonomy per action type"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: []
depends_on: [SEEN-033, SEEN-035]
status: todo
---
# SEEN-065: Implement the trust ramp with autonomy per action type

| | |
|---|---|
| Epic | E4 Agent runtime, policy gate, approvals and audit log |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | none |
| Status | todo |

## Description

Implement the trust ramp in packages/core/policy: per tenant and action type the autonomy score is the approval rate over the most recent decisions; when it reaches at least 95% over at least 50 decisions the policies row switches to autonomous inside caps, and any refused execution (marketplace rejection or human reversal) revokes it back to approval. The inbox shows score, count and mode per action type.

## Acceptance criteria

- [ ] Simulated 50 decisions with 48 approvals switch the action type to autonomous and 47 do not
- [ ] One refused execution moves the mode back to approval and writes an audit event
- [ ] Autonomous actions still respect the euro caps from SEEN-033
- [ ] Inbox shows score, decision count and mode per action type for the tenant

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject

## Blocks

- [SEEN-067](SEEN-067-show-serve-threads-and-drafts-in-the-inbox.md): Show Serve threads and drafts in the inbox
- [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md): Build the day-120 metrics dashboard and CSV export

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
