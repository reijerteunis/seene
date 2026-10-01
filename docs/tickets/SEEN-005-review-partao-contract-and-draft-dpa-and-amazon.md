---
id: SEEN-005
title: "Review Partao contract and draft DPA and Amazon data statement"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [amazon]
depends_on: []
status: todo
---
# SEEN-005: Review Partao contract and draft DPA and Amazon data statement

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Read the Partao contract for IP and non-compete clauses that could touch CTL and record the conclusion, draft a data processing agreement template for pilots, and write the Amazon data protection policy compliance statement covering the 30-day PII expiry and encryption at rest. Include the recovery-share terms stating that fees are billable on credits received only, matching the billing invariant in architecture.md.

## Acceptance criteria

- [ ] Written note on the Partao IP and non-compete position, dated and filed in the legal folder
- [ ] DPA template covering sub-processors (GCP, Supabase, Anthropic, Stripe, Postmark) ready to send to a pilot
- [ ] Amazon data protection compliance statement lists the PII fields kept, encryption at rest and the 30-day expiry
- [ ] Recovery-share terms define the billable event as a credit in an ingested settlement line linked to a claim

## Depends on

- none

## Blocks

- [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md): Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
