---
id: SEEN-115
title: "Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay, kaufland, otto]
depends_on: [SEEN-009]
status: todo
priority: P0
---
# SEEN-115: Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay, kaufland, otto |
| Status | todo |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Seventeen connector tickets will each read a marketplace's documentation into a session and reproduce it as code and fixtures, and the reviewer will check field names by reading the same documentation again. Every one of the five marketplaces publishes a machine-readable contract: Bol's Retailer API v10 (OpenAPI, ReDoc), eBay's Sell APIs (OpenAPI contracts for every RESTful API), Amazon's SP-API models (JSON in amzn/selling-partner-api-models, versioned), Kaufland's and Otto's seller APIs. Vendor the specs under packages/connectors/specs with their version and the date fetched, generate types and a typed fetch client with openapi-typescript and openapi-fetch, and validate every recorded fixture against the response schema at recording time with ajv, so a fixture that drifts from the contract fails before a test uses it. Prism serves the specs as a mock in CI for contract tests. The connector tickets then implement against types, not prose, and the reviewer never checks a field name again. The decision that matters: a marketplace's contract is a file in the repository with a version, and a change in it is a diff a human reviews, not a surprise in production.

## Acceptance criteria

- [ ] packages/connectors/specs holds the Bol v10, eBay Sell Fulfillment, Finances and Post-Order, Amazon Orders, Reports and Finances, Kaufland and Otto specs with version and fetch date, and a script refreshes them with a diff
- [ ] Types and a typed client are generated per marketplace and the connector interface from SEEN-009 is implemented against them, proven by a typecheck that fails on a renamed field
- [ ] Every recorded fixture is validated against its response schema at recording time, and a fixture that fails validation is refused with the path of the mismatch
- [ ] Prism serves each spec as a mock in CI and one contract test per marketplace passes against it
- [ ] SEEN-011, SEEN-012, SEEN-013, SEEN-054 and SEEN-060 depend on this ticket in the index

## Depends on

- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Blocks

- [SEEN-122](SEEN-122-golden-path-end-to-end-tests-on-the-docker.md): Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures
- [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md): Build Bol Retailer API v10 connector for orders to commissions
- [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md): Build eBay connector for orders, returns, transactions and payouts
- [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md): Build Amazon SP-API connector for orders, reports and Finances
- [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md): Build the Kaufland connector with tickets as the claims rail
- [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md): Build the Otto connector for orders, returns, receipts and messages

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
