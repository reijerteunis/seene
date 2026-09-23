---
id: SEEN-069
title: "Snapshot competing offers from Bol by EAN and eBay by GTIN"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, ebay]
depends_on: [SEEN-010, SEEN-011, SEEN-012, SEEN-055]
status: todo
---
# SEEN-069: Snapshot competing offers from Bol by EAN and eBay by GTIN

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

Add the pricing ingest in apps/worker: Bol Competing Offers by EAN and Offers (own price, buy-box status) and eBay Browse API search by GTIN into competitor_snapshots (listing, observed offers with seller, price, delivery promise, best offer flag, timestamp) on a tiered clock (every 2 hours for the top 20% of SKUs by units sold, daily for the rest), inside the rate limits from SEEN-010. Design decision: the tier of a SKU is recomputed weekly from ingested orders, so the clock follows real velocity rather than a hand-kept list.

## Acceptance criteria

- [ ] Snapshots exist for every listing of the friendly brand on Bol and eBay with observed offers and best offer flag
- [ ] High-velocity SKUs are refreshed at least 12 times per day and the rest once
- [ ] Snapshot volume per day stays under the recorded Bol rate limit in a 24-hour run
- [ ] Re-ingest within the same tier window does not create a duplicate snapshot

## Depends on

- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-055](SEEN-055-monitor-unauthorised-sellers-from-competing.md): Monitor unauthorised sellers from competing offers

## Blocks

- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking
- [SEEN-075](SEEN-075-meter-headroom-entries-and-show-the-price-view.md): Meter headroom_entries and show the Price view
- [SEEN-076](SEEN-076-run-the-daily-bol-buy-box-feedback-loop.md): Run the daily Bol buy-box feedback loop

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
