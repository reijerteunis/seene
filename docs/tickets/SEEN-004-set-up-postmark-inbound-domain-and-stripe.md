---
id: SEEN-004
title: "Set up Postmark inbound domain and Stripe account"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: human
changes_agent_action: false
marketplaces: []
depends_on: []
status: todo
---
# SEEN-004: Set up Postmark inbound domain and Stripe account

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Register the Postmark inbound domain for the forwarded mailbox with the inbound webhook pointing at apps/api, and create the Stripe account with SEPA Direct Debit and card enabled and EU VAT settings configured. Store the API keys and webhook signing secrets in the secrets provider (.env.local in development, Secret Manager after go-live). Nothing is wired yet; this ticket removes the waiting time for the Sprint 3 billing and Sprint 5 mailbox work.

## Acceptance criteria

- [ ] Postmark inbound domain verified with MX records and the inbound webhook URL saved
- [ ] Stripe account activated with SEPA Direct Debit and card payment methods enabled
- [ ] Stripe tax settings show EU VAT collection with the company VAT number
- [ ] Postmark server token, Stripe secret key and both webhook signing secrets stored in the secrets provider (.env.local in development, Secret Manager after go-live)

## Depends on

- none

## Blocks

- [SEEN-039](SEEN-039-create-stripe-customers-with-sepa-and-card-and.md): Create Stripe customers with SEPA and card and handle webhooks
- [SEEN-041](SEEN-041-generate-and-send-the-monthly-statement-pdf.md): Generate and send the monthly statement PDF
- [SEEN-062](SEEN-062-parse-the-forwarded-mailbox-via-postmark.md): Parse the forwarded mailbox via Postmark inbound into threads

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
