---
id: SEEN-047
title: "Issue the first invoice and send the signed statement"
epic: E6
epic_name: "Billing, statements and metering"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 1
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-040, SEEN-041, SEEN-042, SEEN-045]
status: todo
---
# SEEN-047: Issue the first invoice and send the signed statement

| | |
|---|---|
| Epic | E6 Billing, statements and metering |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Run the invoicing job for the first paying tenant, check the recovery-share lines against the credited claims by hand, send the statement, obtain the sign-off and confirm the Stripe payment status. Switch Reconcile on for that tenant in the ops console.

## Acceptance criteria

- [ ] First Stripe invoice issued to a paying tenant with every line traced to a credited claim
- [ ] Statement accepted through the sign-off link by the tenant
- [ ] Reconcile enabled for the tenant and the nightly job has run at least once

## Depends on

- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only
- [SEEN-041](SEEN-041-generate-and-send-the-monthly-statement-pdf.md): Generate and send the monthly statement PDF
- [SEEN-042](SEEN-042-ship-the-reconcile-module-with-margin-and-fee.md): Ship the Reconcile module with margin and fee-change alerts
- [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md): Add module switches per tenant with scheduling and billing hooks

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Bill the recovery share only on credits matched to claims, issue Stripe invoices and a signed monthly statement from the same tables that hold the ledger.
