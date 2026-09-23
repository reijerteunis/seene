---
id: SEEN-052
title: "Write listing content through Bol and eBay APIs"
epic: E1
epic_name: "Connectors and ingest"
sprint: 4
sprint_dates: "23 Nov - 4 Dec 2026"
gate: G4
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, ebay]
depends_on: [SEEN-051]
status: todo
---
# SEEN-052: Write listing content through Bol and eBay APIs

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 4 (23 Nov - 4 Dec 2026), gate G4 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, ebay |
| Status | todo |

## Description

Implement the write side in packages/connectors: Bol Offers (price, stock, fulfilment fields) and the Product Content API (attributes, images, process status polling) and the eBay Inventory API (inventory item, offer, compatibility), with process status polling and error mapping into the fix outcome so apply_listing_fix can report exactly what the marketplace accepted. Design decision: every write is followed by a read-back before the fix is marked applied, so the record reflects what the marketplace holds and not what was sent.

## Acceptance criteria

- [ ] A title fix applied on Bol is visible in the next listings ingest with the new content hash
- [ ] A compatibility list applied on eBay for a parts listing shows in the Inventory item
- [ ] API errors map to a fix outcome with the marketplace error code and message
- [ ] Recorded-fixture tests cover success and rejection for both marketplaces

## Depends on

- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff

## Blocks

- [SEEN-057](SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md): Verify listing fixes on three marketplaces and file Kaufland tickets

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
