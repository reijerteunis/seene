---
id: SEEN-081
title: "Load test ingest on 50 tenants and run rate-limit chaos"
epic: E9
epic_name: "Grow, retailer view, hardening and day-120 metrics"
sprint: 7
sprint_dates: "18 - 29 Jan 2027"
gate: G7
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-010, SEEN-014]
status: todo
---
# SEEN-081: Load test ingest on 50 tenants and run rate-limit chaos

| | |
|---|---|
| Epic | E9 Grow, retailer view, hardening and day-120 metrics |
| Sprint | 7 (18 - 29 Jan 2027), gate G7 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Build a synthetic tenant generator and a load test harness under tools/load that runs a 90-day backfill for 50 tenants against mocked marketplace servers, measures queue latency, Postgres load and cost per tenant, and a chaos mode that returns HTTP 429 and 503 at random on 10% of calls to prove the backoff and idempotency from SEEN-010 and SEEN-014 hold under failure. Design decision: the mocked servers replay recorded fixtures, so the load test never touches a live marketplace.

## Acceptance criteria

- [ ] 50-tenant backfill completes with zero duplicate rows and p95 job latency under 60 seconds
- [ ] Chaos run with 10% 429 and 503 responses completes with zero data loss and every failed job retried
- [ ] Worker and database CPU stay under 70% during the run on the production instance sizes
- [ ] Cost per tenant per day recorded from the per-tenant cost logs

## Depends on

- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences

## Blocks

- [SEEN-085](SEEN-085-run-restore-drill-close-pen-test-findings-sign.md): Run restore drill, close pen-test findings, sign metrics pack

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack.
