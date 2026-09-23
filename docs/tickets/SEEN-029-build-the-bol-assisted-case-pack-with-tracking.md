---
id: SEEN-029
title: "Build the Bol assisted case pack with tracking"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-026, SEEN-027]
status: todo
---
# SEEN-029: Build the Bol assisted case pack with tracking

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Implement the Bol assisted mode in packages/core/claims/bol: the case pack holds the compensation request text in Dutch per SEEN-026, an evidence bundle as a zip with a sha256 manifest and a deep link to the partner platform form, and the human confirms it in one click from the inbox. After confirmation the claim is tracked through invoice specification lines of type compensation or correction and through inbound mail matched by order id.

## Acceptance criteria

- [ ] Case pack contains request text, evidence zip and deep link, and is downloadable from the approval inbox
- [ ] Confirming the pack sets submitted_by, submitted_at and status submitted on the claim in one action
- [ ] A compensation line in a later invoice specification for the same order id links the claim and sets status credited
- [ ] An inbound Bol mail mentioning the order id is attached to the claim as a claim_event

## Depends on

- [SEEN-026](SEEN-026-verify-bol-compensation-request-form-structure.md): Verify Bol compensation request form structure
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes

## Blocks

- [SEEN-037](SEEN-037-file-the-first-ten-claims-across-two.md): File the first ten claims across two marketplaces from the inbox

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
