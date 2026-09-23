---
id: SEEN-027
title: "Build the claims rail with api, assisted and track modes"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-021, SEEN-026]
status: todo
---
# SEEN-027: Build the claims rail with api, assisted and track modes

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Implement the claims rail in packages/core/claims and apps/worker: the claims and claim_events tables in use, one ClaimRail interface with mode api (agent submits through the connector), assisted (agent prepares a case pack, a human confirms in one click, then tracking) and track (outcome watched in settlements and mail), plus the evidence table and store in Supabase Storage with sha256 on write. Mode is chosen from the capability matrix per marketplace so adding a marketplace is a matrix row, not a new flow.

## Acceptance criteria

- [ ] ClaimRail resolves mode api for eBay and assisted for Bol and Amazon from the capability matrix
- [ ] Every state change on a claim writes a claim_events row with actor, from status and to status
- [ ] Evidence upload stores the object, records sha256 and source, and rejects a second upload with a different hash for the same path
- [ ] A finding moves to claimed when its claim is submitted and back to open if submission fails

## Depends on

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline
- [SEEN-026](SEEN-026-verify-bol-compensation-request-form-structure.md): Verify Bol compensation request form structure

## Blocks

- [SEEN-028](SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md): Contest eBay payment disputes and cases by API
- [SEEN-029](SEEN-029-build-the-bol-assisted-case-pack-with-tracking.md): Build the Bol assisted case pack with tracking
- [SEEN-030](SEEN-030-build-the-amazon-assisted-case-pack-with-report.md): Build the Amazon assisted case pack with report tracking
- [SEEN-031](SEEN-031-match-credits-to-claims-as-the-only-billable.md): Match credits to claims as the only billable event
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-046](SEEN-046-build-customer-facing-findings-and-claims-views.md): Build customer-facing findings and claims views
- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages
- [SEEN-062](SEEN-062-parse-the-forwarded-mailbox-via-postmark.md): Parse the forwarded mailbox via Postmark inbound into threads
- [SEEN-083](SEEN-083-expire-amazon-pii-after-30-days-and-delete.md): Expire Amazon PII after 30 days and delete tenants on request

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
