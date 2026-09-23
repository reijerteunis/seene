---
id: SEEN-045
title: "Add module switches per tenant with scheduling and billing hooks"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 3
sprint_dates: "9 - 20 Nov 2026"
gate: G3
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-033, SEEN-040]
status: todo
---
# SEEN-045: Add module switches per tenant with scheduling and billing hooks

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 3 (9 - 20 Nov 2026), gate G3 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Add tenant_modules (tenant, module recover, reconcile, comply, serve, grow or price, enabled, started_at, price) in packages/core with an ops console toggle and a customer-visible status; scheduled tasks, tools and policy rows for a module run only when it is enabled, and the module line on the invoice starts from started_at. Design decision: the switch is checked in the policy gate, so a disabled module refuses at the same place every other refusal happens.

## Acceptance criteria

- [ ] Toggling Reconcile on in the ops console starts the nightly job for that tenant within one schedule cycle
- [ ] A module tool called for a tenant with the module off returns refuse with reason module_disabled
- [ ] Invoice module line prorates from started_at for the first month
- [ ] Module status visible in the customer inbox

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md): Issue invoices with recovery-share lines from credited claims only

## Blocks

- [SEEN-047](SEEN-047-issue-the-first-invoice-and-send-the-signed.md): Issue the first invoice and send the signed statement
- [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md): Add propose_listing_fix and apply_listing_fix tools with diff
- [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md): Add propose_price and apply_price tools with buy-box tracking
- [SEEN-078](SEEN-078-attribute-ad-cost-into-margin-and-publish-the.md): Attribute ad cost into margin and publish the weekly Grow report
- [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md): Build the day-120 metrics dashboard and CSV export

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
