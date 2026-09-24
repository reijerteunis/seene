---
id: SEEN-034
title: "Build agent runtime v1 with the fixed tool set and cost accounting"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: []
depends_on: [SEEN-027, SEEN-032, SEEN-033]
status: todo
---
# SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting

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

Implement packages/agent: a tool-calling loop per task with Claude and the fixed tools read_finding, read_evidence, draft_claim, submit_claim (mode aware), add_evidence, request_approval and escalate, each declaring action type, reversibility and a euro impact estimator, plus prompts per claim rule and an agent_runs row per run with model, tokens, cost and duration. Every tool call is an agent_actions row and passes through the policy gate before any side effect.

## Acceptance criteria

- [ ] A run on a finding produces a draft claim and a request_approval action in under 60 seconds
- [ ] Each of the seven tools has a declared action type, reversibility flag and euro impact estimator with unit tests
- [ ] agent_runs records model, input and output tokens, cost in EUR and duration for every run
- [ ] A tool call that throws is recorded as an agent_actions row with outcome error and the run escalates

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Tool declarations: action type, reversibility and euro impact for the seven tools (2 pt). RED: a tool without a declaration is refused at registration
2. The run loop with the policy gate before every side effect and agent_runs accounting (2 pt). RED: a tool call that throws is recorded as an agent_actions row with outcome error
3. Prompts per claim rule and the end-to-end run producing a draft and a request_approval (1 pt). RED: a run on a fixture finding ends in a request_approval action

## Depends on

- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-032](SEEN-032-write-append-only-audit-events-before-every.md): Write append-only audit_events before every side effect
- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility

## Blocks

- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject
- [SEEN-036](SEEN-036-create-the-eval-set-of-30-real-findings-with.md): Create the eval set of 30 real findings with expected drafts
- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff
- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking
- [SEEN-079](SEEN-079-propose-campaign-budgets-through-the-gate-no.md): Propose campaign budgets through the gate, no autonomous creation
- [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md): Build the day-120 metrics dashboard and CSV export

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
