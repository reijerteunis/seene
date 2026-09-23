---
id: SEEN-056
title: "Show Comply defects and fix diffs in the inbox"
epic: E5
epic_name: "Customer inbox and ops console"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-035, SEEN-051]
status: todo
---
# SEEN-056: Show Comply defects and fix diffs in the inbox

| | |
|---|---|
| Epic | E5 Customer inbox and ops console |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add the Comply pages in apps/web: defects by marketplace and severity, proposed fixes as diffs awaiting approval, applied fixes with before and after content, and drift events; approval of a fix reuses the approval inbox from SEEN-035 so there is one queue for every action type. Design decision: no Comply page writes to a marketplace directly; every change goes through apply_listing_fix and the gate.

## Acceptance criteria

- [ ] Defects page shows counts by severity per marketplace and links to each listing
- [ ] A proposed fix shows the field diff and can be approved, edited or rejected
- [ ] Applied fixes list shows before and after content and the audit events
- [ ] Drift events are listed with the field that changed and when

## Depends on

- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject
- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff

## Blocks

- [SEEN-057](SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md): Verify listing fixes on three marketplaces and file Kaufland tickets

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give tenants one inbox for approvals, findings, claims and statements and give ops one console for tenants, connections, runs and costs.
