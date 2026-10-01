---
id: SEEN-039
title: "Create Stripe customers with SEPA and card and handle webhooks"
epic: E6
epic_name: "Billing, statements and metering"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-004, SEEN-008]
status: todo
---
# SEEN-039: Create Stripe customers with SEPA and card and handle webhooks

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

Integrate Stripe in apps/api: create a Stripe customer per tenant, collect a SEPA Direct Debit mandate or a card through a hosted setup session, handle the webhooks (setup_intent.succeeded, invoice.paid, invoice.payment_failed, payment_method.detached) with signature verification and idempotent processing, and store the Stripe ids on tenants. Tax is handled by Stripe Tax with the tenant's VAT number for reverse charge.

## Acceptance criteria

- [ ] A tenant can complete SEPA or card setup from the inbox and tenants.stripe_customer_id and the default payment method are set
- [ ] Webhook handler rejects an invalid signature with HTTP 400 and processes a replayed event exactly once
- [ ] A tenant with a valid EU VAT number is invoiced with reverse charge in Stripe test mode
- [ ] No Stripe id beyond the customer id appears in logs

## Depends on

- [SEEN-004](SEEN-004-set-up-postmark-inbound-domain-and-stripe.md): Set up Postmark inbound domain and Stripe account
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Blocks

- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only
- [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md): Consumer invoices with VAT by destination and the OSS return

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Bill the recovery share only on credits matched to claims, issue Stripe invoices and a signed monthly statement from the same tables that hold the ledger.
