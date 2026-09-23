---
id: SEEN-075
title: "Meter headroom_entries and show the Price view"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, ebay]
depends_on: [SEEN-069, SEEN-074]
status: todo
---
# SEEN-075: Meter headroom_entries and show the Price view

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, ebay |
| Status | todo |

## Description

Add the headroom meter in apps/worker: a daily job writes headroom_entries per price change and day as price delta times units sold while the listing held the featured offer, from ingested orders and snapshots, so the meter reconciles to orders. Add the Price page in apps/web with proposals, bands, applied moves with buy box before and after, and headroom captured per marketplace.

## Acceptance criteria

- [ ] Sum of headroom_entries for a listing equals delta times the units in ingested orders on featured days in a fixture
- [ ] Headroom entries reference the price_change and the order lines counted
- [ ] Price page shows proposals awaiting approval, applied moves and headroom per marketplace
- [ ] Bands per SKU are editable by the tenant on the Price page

## Depends on

- [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md): Snapshot competing offers from Bol by EAN and eBay by GTIN
- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
