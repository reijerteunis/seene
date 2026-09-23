---
id: SEEN-070
title: "Snapshot Amazon pricing on a tiered clock"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-010, SEEN-013, SEEN-015]
status: todo
---
# SEEN-070: Snapshot Amazon pricing on a tiered clock

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Add Amazon Product Pricing to the pricing ingest in apps/worker: getCompetitivePricing at up to 10 requests per second in batches of 20 ASINs for all listings daily, and getFeaturedOfferExpectedPriceBatch at 0.033 requests per second for high-velocity SKUs only (top 20% by units sold), stored in competitor_snapshots with the featured offer flag and expected price. Requires the Pricing role and the EU availability recorded in SEEN-015.

## Acceptance criteria

- [ ] Daily competitive pricing snapshots exist for every Amazon listing of the friendly brand
- [ ] Featured-offer expected price is requested for high-velocity SKUs only and never more than 2 calls per minute
- [ ] Rate limiter test shows zero HTTP 429 over a simulated day of calls
- [ ] Snapshot rows carry the featured offer flag and expected price where returned

## Depends on

- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-015](SEEN-015-verify-amazon-report-names-and-finances.md): Verify Amazon report names and Finances transactions version

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
