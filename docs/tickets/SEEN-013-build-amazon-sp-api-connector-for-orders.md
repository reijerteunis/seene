---
id: SEEN-013
title: "Build Amazon SP-API connector for orders, reports and Finances"
epic: E1
epic_name: "Connectors and ingest"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [amazon]
depends_on: [SEEN-001, SEEN-009, SEEN-010, SEEN-115]
status: todo
---
# SEEN-013: Build Amazon SP-API connector for orders, reports and Finances

| | |
|---|---|
| Epic | E1 Connectors and ingest |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | amazon |
| Status | todo |

## Description

Implement the Amazon adapter in packages/connectors/amazon: Orders API, the Reports API for the settlement report (GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2), the FBA reimbursements report, the FBA returns report and the fee preview report, and the Finances API for financial events, with report polling and gzip decoding. It runs on the sandbox until the roles from SEEN-001 are approved, and report names are configuration so the outcome of the Sprint 1 verification is a config change.

## Acceptance criteria

- [ ] Adapter passes recorded-fixture tests for orders, settlement report rows, reimbursement rows, return rows and financial events
- [ ] Settlement report rows map to settlement_lines with amount type and the settlement id as the settlement external id
- [ ] Report request, polling and download run as one BullMQ job that resumes after a worker restart
- [ ] Sandbox run for orders and one report completes end to end without an unhandled error

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Orders API on the sandbox and the client with LWA refresh (2 pt). RED: an orders page maps to orders and order_lines and a stale token is refreshed once
2. Reports API: request, poll, download and gzip decode as one resumable BullMQ job (2 pt). RED: a worker restart mid-poll resumes the same report request
3. Settlement, reimbursement, returns and fee preview rows to trade-record types, report names as configuration (1 pt). RED: a settlement flat-file row maps to a settlement_line with the settlement id as external id

## Depends on

- [SEEN-001](SEEN-001-register-amazon-sp-api-developer-and-file-ads.md): Register Amazon SP-API developer and file Ads API application
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access
- [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md): Add per-marketplace rate limiting with header-driven backoff
- [SEEN-115](SEEN-115-generate-the-marketplace-clients-from-the.md): Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them

## Blocks

- [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md): Run ingest workers with idempotent upserts, raw archive and cadences
- [SEEN-015](SEEN-015-verify-amazon-report-names-and-finances.md): Verify Amazon report names and Finances transactions version
- [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md): Apply return and cancellation decisions through returns APIs
- [SEEN-070](SEEN-070-snapshot-amazon-pricing-on-a-tiered-clock.md): Snapshot Amazon pricing on a tiered clock
- [SEEN-083](SEEN-083-expire-amazon-pii-after-30-days-and-delete.md): Expire Amazon PII after 30 days and delete tenants on request

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record.
