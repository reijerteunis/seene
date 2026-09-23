---
id: SEEN-041
title: "Generate and send the monthly statement PDF"
epic: E6
epic_name: "Billing, statements and metering"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-004, SEEN-040]
status: todo
---
# SEEN-041: Generate and send the monthly statement PDF

| | |
|---|---|
| Epic | E6 Billing, statements and metering |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Build the statement in apps/api: per tenant and month, a PDF with euros identified, filed, credited and refused per marketplace, hours removed (claims filed times a per-rule handling time constant the tenant can see), the actions log from audit_events and the invoice reference, stored with sha256 on the statements table and sent by Postmark with a sign-off link that records who accepted it. Design decision: the statement is rendered from the same views the invoice uses, so the two documents can never disagree.

## Acceptance criteria

- [ ] Statement totals equal the findings and claims views for the period to the cent
- [ ] Hours removed uses the per-rule constants table and prints the constants in a footnote
- [ ] Statement emailed by Postmark and the sign-off link writes accepted_by and accepted_at
- [ ] Statement PDF stored with sha256 and downloadable from the customer inbox

## Depends on

- [SEEN-004](SEEN-004-set-up-postmark-inbound-domain-and-stripe.md): Set up Postmark inbound domain and Stripe account
- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only

## Blocks

- [SEEN-047](SEEN-047-issue-the-first-invoice-and-send-the-signed.md): Issue the first invoice and send the signed statement

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Bill the recovery share only on credits matched to claims, issue Stripe invoices and a signed monthly statement from the same tables that hold the ledger.
