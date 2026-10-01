---
id: SEEN-040
title: "Issue invoices with recovery-share lines from credited claims only"
epic: E6
epic_name: "Billing, statements and metering"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-031, SEEN-039]
status: todo
---
# SEEN-040: Issue invoices with recovery-share lines from credited claims only

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

Implement monthly invoicing in apps/worker: for each tenant the invoices row is built from claims credited in the period (recovery share percentage times credited amount, one line per marketplace) plus module lines from the module switches, pushed to Stripe as an invoice with line metadata referencing claim ids, and an invoice_claims link table records which claims were billed. Only credits matched in SEEN-031 can be billed and a claim is billed once.

## Acceptance criteria

- [ ] Invoice for a test period contains only claims with status credited and credited_by_settlement_line_id set, and every recovery share line is a row of invoice_claims rather than json on the invoice
- [ ] A claim appears on at most one invoice, enforced by a unique constraint on invoice_claims.claim_id
- [ ] Recovery-share line amounts equal share percentage times credited amount per marketplace to the cent
- [ ] Stripe invoice created in test mode with line metadata listing the claim ids

## Depends on

- [SEEN-031](SEEN-031-match-credits-to-claims-as-the-only-billable.md): Match credits to claims as the only billable event
- [SEEN-039](SEEN-039-create-stripe-customers-with-sepa-and-card-and.md): Create Stripe customers with SEPA and card and handle webhooks

## Blocks

- [SEEN-041](SEEN-041-generate-and-send-the-monthly-statement-pdf.md): Generate and send the monthly statement PDF
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks
- [SEEN-047](SEEN-047-issue-the-first-invoice-and-send-the-signed.md): Issue the first invoice and send the signed statement
- [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md): Build the day-120 metrics dashboard and CSV export
- [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md): Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Bill the recovery share only on credits matched to claims, issue Stripe invoices and a signed monthly statement from the same tables that hold the ledger.
