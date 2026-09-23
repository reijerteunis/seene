---
id: SEEN-071
title: "Model net margin per marketplace from cost layers"
epic: E8
epic_name: "Price module"
sprint: 6
sprint_dates: "4 - 15 Jan 2027"
gate: G6
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland, otto]
depends_on: [SEEN-017, SEEN-044]
status: todo
---
# SEEN-071: Model net margin per marketplace from cost layers

| | |
|---|---|
| Epic | E8 Price module |
| Sprint | 6 (4 - 15 Jan 2027), gate G6 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland, otto |
| Status | todo |

## Description

Add products.cost_layers (purchase cost, inbound freight, packaging, per-unit overhead with effective dates) editable in the inbox and a pure netMargin(listing, price, date) function in packages/core/pricing that subtracts commission and fixed fee from fee_expectations or the schedule, ad cost per unit, and expected returns cost from the trailing return rate per SKU and marketplace. Design decision: netMargin is a pure function over stored rows, so the governor and the Price page always show the same figure.

## Acceptance criteria

- [ ] netMargin returns margin in EUR and percentage for a listing at a price with each component listed
- [ ] Cost layer with a later effective date is used for orders after that date in a unit test
- [ ] Expected returns cost uses the SKU's trailing 90-day return rate per marketplace
- [ ] Margin for the friendly brand's top 50 SKUs visible per marketplace in the inbox

## Depends on

- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs
- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth

## Blocks

- [SEEN-072](SEEN-072-implement-the-price-governor-with-bands.md): Implement the price governor with bands, ceilings and cooldowns
- [SEEN-078](SEEN-078-attribute-ad-cost-into-margin-and-publish-the.md): Attribute ad cost into margin and publish the weekly Grow report

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders.
