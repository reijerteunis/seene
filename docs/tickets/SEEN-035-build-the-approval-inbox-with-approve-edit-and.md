---
id: SEEN-035
title: "Build the approval inbox with approve, edit and reject"
epic: E4
epic_name: "Agent runtime, policy gate, approvals and audit log"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-033, SEEN-034]
status: todo
---
# SEEN-035: Build the approval inbox with approve, edit and reject

| | |
|---|---|
| Epic | E4 Agent runtime, policy gate, approvals and audit log |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Build the customer inbox in apps/web: a queue of pending approvals per tenant showing the finding, the drafted claim text, the evidence list and the euro impact, with approve, edit (a text diff against the draft is stored) and reject with a reason, and one-click confirm for assisted case packs. Each decision writes an approvals row and an audit event and resumes the agent run.

## Acceptance criteria

- [ ] Pending approvals list loads in under 2 seconds for 200 items and is scoped by RLS to the tenant
- [ ] Approve resumes the run and the claim is submitted or the case pack marked confirmed within one job cycle
- [ ] Edit stores the diff between draft and submitted text on the approvals row
- [ ] Reject with a reason sets the action outcome to rejected and no marketplace call is made

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Pending approvals queue scoped by RLS, with finding, draft, evidence and euro impact (2 pt). RED: a user of tenant A never sees tenant B's approvals and 200 items load under 2 seconds
2. Approve and one-click confirm resuming the run (2 pt). RED: approve resumes the run and the claim is submitted or the case pack confirmed
3. Edit with a stored diff and reject with a reason (1 pt). RED: an edit stores the diff and a reject makes no marketplace call

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting

## Blocks

- [SEEN-122](SEEN-122-golden-path-end-to-end-tests-on-the-docker.md): Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures
- [SEEN-037](SEEN-037-file-the-first-ten-claims-across-two.md): File the first ten claims across two marketplaces from the inbox
- [SEEN-046](SEEN-046-build-customer-facing-findings-and-claims-views.md): Build customer-facing findings and claims views
- [SEEN-056](SEEN-056-show-comply-defects-and-fix-diffs-in-the-inbox.md): Show Comply defects and fix diffs in the inbox
- [SEEN-065](SEEN-065-implement-the-trust-ramp-with-autonomy-per.md): Implement the trust ramp with autonomy per action type
- [SEEN-067](SEEN-067-show-serve-threads-and-drafts-in-the-inbox.md): Show Serve threads and drafts in the inbox

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect.
