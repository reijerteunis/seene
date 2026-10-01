---
id: SEEN-131
title: "Consumer invoices with VAT by destination and the OSS return"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-128, SEEN-124, SEEN-039]
status: todo
---
# SEEN-131: Consumer invoices with VAT by destination and the OSS return

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

As seller of record Seen invoices the consumer: a sequential invoice per order per country, VAT at the destination rate for EU distance sales under the One Stop Shop or the domestic rate where the sale is domestic, credit notes on refunds and returns, and the quarterly OSS return as a CSV the accountant files. Rates are a table with validity dates, never a constant. Invoices are stored as evidence with a hash and uploaded to the marketplace where it offers invoice upload. The decision that matters: the invoice engine is a pure function over the order, the destination and the rate table, tested with properties (a credit note never exceeds its invoice, the VAT sum per return equals the sum of its invoices), because a wrong invoice is a tax problem in Seen's name.

## Acceptance criteria

- [ ] Every storefront order produces a sequential invoice per country with the destination VAT rate from the dated rate table, stored with a hash
- [ ] Refunds and returns produce credit notes that never exceed the invoice, proven by a property test
- [ ] The quarterly OSS CSV reconciles to the invoices to the cent, proven by a fixture
- [ ] Invoices are uploaded to Bol and Amazon where the API offers it, and the failure to upload is an exception, not a silent skip

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Invoice engine as a pure function over order, destination and the dated rate table (2 pt). RED: an order to Germany from the Netherlands is invoiced at the German rate on the order date
2. Credit notes and the property tests (1 pt). RED: a credit note larger than its invoice is refused
3. Sequences, storage with hash, marketplace upload and the OSS CSV (2 pt). RED: the OSS CSV total equals the invoice total for the quarter

## Depends on

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due
- [SEEN-039](SEEN-039-create-stripe-customers-with-sepa-and-card-and.md): Create Stripe customers with SEPA and card and handle webhooks

## Blocks

- [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md): Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through
- [SEEN-133](SEEN-133-returns-withdrawals-and-guarantee-cases-handled.md): Returns, withdrawals and guarantee cases handled as the seller of record
- [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md): Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
