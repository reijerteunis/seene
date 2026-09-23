---
id: SEEN-003
title: "Obtain Bol credentials and verify OAuth grant and rate limits"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: human
changes_agent_action: false
marketplaces: [bol]
depends_on: []
status: todo
---
# SEEN-003: Obtain Bol credentials and verify OAuth grant and rate limits

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Obtain Bol partner platform API credentials from the friendly brand, confirm the client-credentials grant type and token lifetime against the current Retailer API v10 documentation, and record the numeric rate limits per endpoint family (orders, shipments, returns, invoices, commissions). This closes the first open verification from architecture.md before the Bol connector in packages/connectors/bol is written.

## Acceptance criteria

- [ ] Client id and secret stored in the secrets provider (.env.local in development, Secret Manager after go-live) under the friendly brand's Bol connection
- [ ] A token request with the client-credentials grant returns a bearer token and its lifetime is recorded
- [ ] Rate limits per endpoint family recorded in packages/connectors/bol/README.md with the documentation date
- [ ] GET /retailer/orders with the token returns HTTP 200 for the friendly brand

## Depends on

- none

## Blocks

- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-026](SEEN-026-verify-bol-compensation-request-form-structure.md): Verify Bol compensation request form structure

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
