---
id: SEEN-129
title: "List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-128, SEEN-126, SEEN-044, SEEN-052]
status: todo
---
# SEEN-129: List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 8 (1 - 12 Feb 2027), gate G8 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

Take the supplier's product truth from its shop system (SEEN-044) and the GPSR and EPR data the agreement requires, create or match the offers under Seen's Bol and Amazon accounts through the listing APIs already built for Comply (SEEN-052, SEEN-053), price them inside the brand's floor and Seen's bands, and keep stock in step with the supplier's shop so Seen never sells what the brand cannot ship. Listings carry the manufacturer and responsible-person data, and a product missing it is not listed. The decision that matters: the supplier's shop is the source of truth for stock and content, and a storefront listing is a projection of it, never an edit of it.

## Acceptance criteria

- [ ] A supplier's products are listed under Seen's Bol and Amazon accounts from the shop catalogue, matched by EAN where an offer exists and created where it does not
- [ ] A product without the GPSR data set is refused with the missing fields named
- [ ] Stock on the storefront listings follows the supplier's shop within the sync cadence, and a sold-out product is set to zero before the next order can land
- [ ] Prices sit inside the brand's floor and Seen's bands, proven by a test that refuses a price below the floor

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Offer matching and creation under Seen's accounts from the shop catalogue (2 pt). RED: an EAN with an existing offer is matched, one without is created, both under owner seen
2. GPSR and EPR data on listings, refusal when missing (2 pt). RED: a product without a responsible person is refused with the field named
3. Stock and price projection inside the floor and the bands (1 pt). RED: a price below the brand's floor is refused

## Depends on

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-126](SEEN-126-register-the-storefront-entity-for-epr-gpsr.md): Register the storefront entity for EPR, GPSR responsible-person data and product liability cover
- [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md): Build the Shopify Admin GraphQL connector as product and stock truth
- [SEEN-052](SEEN-052-write-listing-content-through-bol-and-ebay-apis.md): Write listing content through Bol and eBay APIs

## Blocks

- [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md): Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
