---
id: SEEN-125
title: "Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack"
epic: E11
epic_name: "Seller of record"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [bol, amazon]
depends_on: [SEEN-124]
status: todo
---
# SEEN-125: Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack

| | |
|---|---|
| Epic | E11 Seller of record |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol, amazon |
| Status | todo |

## Description

The storefront sells from accounts Seen owns. Open a Bol partner account and an Amazon EU seller account in Seen's legal entity, with the bank account, the VAT numbers and the identity checks each requires, and go through the same API registrations the brand-side connectors already use (SEEN-001, SEEN-003), so Seen's accounts are connections like any other with owner seen. Prepare the authorisation pack a brand signs so Seen may list its products: the letter of authorisation, the Brand Registry reseller authorisation on Amazon, the invoices or supply agreement that prove authenticity when a marketplace asks, and the brand's manufacturer and responsible-person data for the listings. Kaufland and Otto follow once one supplier is live. The decision that matters: Seen lists only what a brand has authorised in writing, because an unauthorised listing under Seen's name is Seen's problem, not the brand's.

## Acceptance criteria

- [ ] Bol and Amazon EU seller accounts exist in Seen's entity, verified, with API access working through the existing connectors under owner seen
- [ ] The authorisation pack exists as templates and the first friendly brand has signed it
- [ ] Amazon Brand Registry lists Seen as an authorised reseller of the friendly brand, or the reason it cannot is recorded
- [ ] Account health, tax settings and return addresses are configured and screenshotted into the ticket's evidence

## Depends on

- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due

## Blocks

- [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md): Connection ownership and storefront mode on the trade record

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged.
