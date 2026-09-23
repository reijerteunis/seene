---
id: SEEN-046
title: "Build customer-facing findings and claims views"
epic: E5
epic_name: "Customer inbox and ops console"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-027, SEEN-031, SEEN-035]
status: todo
---
# SEEN-046: Build customer-facing findings and claims views

| | |
|---|---|
| Epic | E5 Customer inbox and ops console |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Add the customer inbox pages in apps/web: findings per marketplace with rule, amount, confidence and deadline, claims with a status timeline from claim_events, evidence downloads, credited amounts and the statement and invoice list, all through RLS with the tenant's own users from Supabase Auth. Tenant users are invited by email from the ops console.

## Acceptance criteria

- [ ] A tenant user sees only their tenant's findings and claims in an RLS test with two tenants
- [ ] Claim page shows the claim_events timeline, evidence files and the credited settlement line when present
- [ ] Invited user receives a Postmark email and can log in with a magic link
- [ ] Pages render in under 2 seconds for 5,000 findings

## Depends on

- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-031](SEEN-031-match-credits-to-claims-as-the-only-billable.md): Match credits to claims as the only billable event
- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject

## Blocks

- [SEEN-080](SEEN-080-build-the-retailer-read-only-view-via-a-scoped.md): Build the retailer read-only view via a scoped link

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give tenants one inbox for approvals, findings, claims and statements and give ops one console for tenants, connections, runs and costs.
