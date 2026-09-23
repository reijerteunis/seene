---
id: SEEN-053
title: "Write listing content through Amazon Listings Items and Feeds"
epic: E1
epic_name: "Connectors and ingest"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-051]
status: todo
---
# SEEN-053: Write listing content through Amazon Listings Items and Feeds

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Implement Amazon listing writes in packages/connectors/amazon: Listings Items API patch for single attribute fixes and the Feeds API (JSON_LISTINGS_FEED) for bulk changes, with feed processing report parsing into per-listing outcomes. Requires the Product Listing role requested in SEEN-001.

## Acceptance criteria

- [ ] A bullet point fix applied by Listings Items patch is visible in the next ingest
- [ ] A feed of 50 fixes returns per-listing outcomes parsed from the processing report
- [ ] Feed errors map to fix outcomes with the Amazon error code
- [ ] Recorded-fixture tests cover patch success, patch rejection and a feed with mixed outcomes

## Depends on

- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff

## Blocks

- [SEEN-057](SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md): Verify listing fixes on three marketplaces and file Kaufland tickets

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
