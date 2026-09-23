---
id: SEEN-026
title: "Verify Bol compensation request form structure"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-003]
status: todo
---
# SEEN-026: Verify Bol compensation request form structure

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Log in to the friendly brand's Bol partner platform, walk through the compensation request flow for a lost shipment and for a return shortfall, and record every field, its allowed values and the deep link pattern. Decide whether the case pack in packages/core/claims/bol can pre-fill fields or must produce copy-ready text plus evidence files.

## Acceptance criteria

- [ ] Field list and deep link pattern for both request types documented in packages/core/claims/bol/README.md with screenshots
- [ ] Decision recorded as pre-fill or copy-ready text, with the reason
- [ ] One test request submitted by hand and its confirmation email captured for the tracking parser

## Depends on

- [SEEN-003](SEEN-003-obtain-bol-credentials-and-verify-oauth-grant.md): Obtain Bol credentials and verify OAuth grant and rate limits

## Blocks

- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-029](SEEN-029-build-the-bol-assisted-case-pack-with-tracking.md): Build the Bol assisted case pack with tracking

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
