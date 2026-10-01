---
id: SEEN-132
title: "Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through"
epic: E11
epic_name: "Seller of record"
sprint: 8
sprint_dates: "1 - 12 Feb 2027"
gate: G8
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-128, SEEN-131, SEEN-040, SEEN-127]
status: todo
---
# SEEN-132: Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through

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

The supplier's statement is the storefront's product: per period, per marketplace, the orders sold, the net proceeds after VAT, the marketplace fees passed through at cost from the ingested settlement lines, the storefront fee, the returns credited back, the recovery credits Seen obtained on the supplier's orders (net of the recovery share), and the payout. Every line points at a settlement line or an invoice, so the statement is derivable, never typed. Payouts go by SEPA transfer on the schedule the agreement sets, with a self-billing invoice or commission settlement per the legal shape from SEEN-124, and the statement is signed the way the monthly statement (SEEN-041) already is. The decision that matters: the statement is computed from ingested settlements and invoices only, the same rule as billing, so Seen never pays a supplier for money the marketplace has not paid Seen.

## Acceptance criteria

- [ ] A supplier statement per period and marketplace derives every line from settlement lines and invoices, and a test proves a line cannot exist without its source
- [ ] The payout equals net proceeds minus marketplace fees at cost, the storefront fee and returns, plus recovery credits net of the share, to the cent on a fixture
- [ ] Payouts are executed by SEPA on the schedule with the self-billing document per the legal shape, and a payout without a settlement behind it is refused
- [ ] The signed statement PDF reuses SEEN-041's generator and is sent to the supplier

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Statement lines derived from settlements and invoices (2 pt). RED: a statement line without a source settlement line or invoice is refused
2. Fees, storefront fee, returns and recovery credits in the payout arithmetic (2 pt). RED: the payout on a fixture equals the hand-computed figure to the cent
3. SEPA payout, self-billing document and the signed PDF (1 pt). RED: a payout without settled proceeds behind it is refused

## Depends on

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return
- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only
- [SEEN-127](SEEN-127-write-the-storefront-agreement-supply-terms-the.md): Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee

## Blocks

- [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md): Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
