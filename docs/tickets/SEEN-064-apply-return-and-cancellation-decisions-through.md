---
id: SEEN-064
title: "Apply return and cancellation decisions through returns APIs"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-011, SEEN-012, SEEN-013, SEEN-033, SEEN-034]
status: todo
---
# SEEN-064: Apply return and cancellation decisions through returns APIs

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add decide_return and decide_cancellation as agent actions in packages/agent with action type return_decision, reversible false and euro impact from the order value, executed through Bol returns handling, Amazon returns authorisation and eBay Post-Order return decisions. The gate applies the tenant's return policy thresholds and the agent never issues a refund, only the return acceptance and the handling result.

## Acceptance criteria

- [ ] A return acceptance is applied by API on Bol in the friendly brand account with the handling result recorded
- [ ] A decision above the tenant's return value threshold returns approval
- [ ] The tool never calls a refund endpoint, checked by a test that fails on any refund code path
- [ ] Every decision writes agent_actions and audit_events before the API call

## Depends on

- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
