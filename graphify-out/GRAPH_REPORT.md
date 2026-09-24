# Graph Report - seene  (2026-09-24)

## Corpus Check
- 661 files · ~227,183 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .toml 2, .example 1)

## Summary
- 2332 nodes · 4333 edges · 194 communities (174 shown, 20 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 112 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `165eb38f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- gates.py
- .evaluate
- web/package.json
- Repository
- EntryPointTest
- CLAUDE.md
- boundary.ts
- RecordTest
- cli.py
- DeliveryWalk
- .graph
- .mcp.json
- app.module.ts
- SEEN-087: Install graphify, build the repo graph and wire it into both assistants
- worker/package.json
- .stub_repowise
- Seen: product requirements (MVP)
- doctor.py
- CoverageTest
- stub
- kpi.py
- Tickets
- package.json
- SEEN-086: Build the Seen harness CLI with staged journal and receipts
- Seen: MVP development plan
- SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages
- StateForTest
- SEEN-001: Register Amazon SP-API developer and file Ads API application
- SEEN-002: Obtain eBay production keys and file Application Growth Check
- SEEN-003: Obtain Bol credentials and verify OAuth grant and rate limits
- SEEN-004: Set up Postmark inbound domain and Stripe account
- SEEN-005: Review Partao contract and draft DPA and Amazon data statement
- StatusAgainstJournalTest
- SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table
- SEEN-009: Define connector interface, capability matrix and credential access
- SEEN-010: Add per-marketplace rate limiting with header-driven backoff
- SEEN-011: Build Bol Retailer API v10 connector for orders to commissions
- SEEN-012: Build eBay connector for orders, returns, transactions and payouts
- SEEN-013: Build Amazon SP-API connector for orders, reports and Finances
- SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences
- SEEN-015: Verify Amazon report names and Finances transactions version
- SEEN-016: Encode fee schedules per marketplace and category in core
- SEEN-017: Compute fee_expectations per order line from schedules and APIs
- SEEN-018: Match settlement_lines to order_lines deterministically
- SEEN-019: Implement fee detectors as pure tested functions
- SEEN-020: Implement shipment, return and inventory detectors
- SEEN-021: Persist findings with rule, confidence, evidence refs and deadline
- SEEN-022: Generate the audit PDF with scorecard and line annex
- SEEN-023: Measure the recoverable pool per marketplace
- SEEN-024: Ship ops console v1 for tenants, connections and sync status
- SEEN-025: Run three real 90-day audits and deliver the PDFs
- SEEN-026: Verify Bol compensation request form structure
- SEEN-027: Build the claims rail with api, assisted and track modes
- SEEN-028: Contest eBay payment disputes and cases by API
- SEEN-029: Build the Bol assisted case pack with tracking
- SEEN-030: Build the Amazon assisted case pack with report tracking
- SEEN-031: Match credits to claims as the only billable event
- SEEN-032: Write append-only audit_events before every side effect
- SEEN-033: Implement policy gate v1 with caps and reversibility
- SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting
- SEEN-035: Build the approval inbox with approve, edit and reject
- SEEN-036: Create the eval set of 30 real findings with expected drafts
- SEEN-037: File the first ten claims across two marketplaces from the inbox
- SEEN-038: Verify Shopify Payments payout scopes and create the custom app
- SEEN-039: Create Stripe customers with SEPA and card and handle webhooks
- SEEN-040: Issue invoices with recovery-share lines from credited claims only
- SEEN-041: Generate and send the monthly statement PDF
- SEEN-042: Ship the Reconcile module with margin and fee-change alerts
- SEEN-043: Export finance CSV of settlements and matched lines
- SEEN-044: Build the Shopify Admin GraphQL connector as product and stock truth
- SEEN-045: Add module switches per tenant with scheduling and billing hooks
- SEEN-046: Build customer-facing findings and claims views
- SEEN-047: Issue the first invoice and send the signed statement
- SEEN-048: Verify Kaufland settlement and ticket endpoints and obtain keys
- SEEN-049: Encode listing spec rules per marketplace in core
- SEEN-050: Ingest listings with content hash and drift detection
- SEEN-051: Add propose_listing_fix and apply_listing_fix tools with diff
- SEEN-052: Write listing content through Bol and eBay APIs
- SEEN-053: Write listing content through Amazon Listings Items and Feeds
- SEEN-054: Build the Kaufland connector with tickets as the claims rail
- SEEN-055: Monitor unauthorised sellers from competing offers
- SEEN-056: Show Comply defects and fix diffs in the inbox
- SEEN-057: Verify listing fixes on three marketplaces and file Kaufland tickets
- SEEN-058: Verify eBay messaging deprecation and choose the message path
- SEEN-059: Verify Otto rate limits and obtain Otto API keys
- SEEN-060: Build the Otto connector for orders, returns, receipts and messages
- SEEN-061: Ingest message_threads from Amazon, eBay, Kaufland and Otto
- SEEN-062: Parse the forwarded mailbox via Postmark inbound into threads
- SEEN-063: Add reply_message tool bound to tenant service policies
- SEEN-064: Apply return and cancellation decisions through returns APIs
- SEEN-065: Implement the trust ramp with autonomy per action type
- SEEN-066: Track claim and dispute deadlines with alerts
- SEEN-067: Show Serve threads and drafts in the inbox
- SEEN-068: Verify the Kaufland virtual buy box endpoint
- SEEN-069: Snapshot competing offers from Bol by EAN and eBay by GTIN
- SEEN-070: Snapshot Amazon pricing on a tiered clock
- SEEN-071: Model net margin per marketplace from cost layers
- SEEN-072: Implement the price governor with bands, ceilings and cooldowns
- SEEN-073: Write prices through Bol Offers and eBay Inventory offers
- SEEN-074: Add propose_price and apply_price tools with buy-box tracking
- SEEN-075: Meter headroom_entries and show the Price view
- SEEN-076: Run the daily Bol buy-box feedback loop
- SEEN-077: Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted
- SEEN-078: Attribute ad cost into margin and publish the weekly Grow report
- SEEN-079: Propose campaign budgets through the gate, no autonomous creation
- SEEN-080: Build the retailer read-only view via a scoped link
- SEEN-081: Load test ingest on 50 tenants and run rate-limit chaos
- SEEN-082: Run RLS penetration tests and the restore drill
- SEEN-083: Expire Amazon PII after 30 days and delete tenants on request
- SEEN-084: Build the day-120 metrics dashboard and CSV export
- SEEN-085: Run restore drill, close pen-test findings, sign metrics pack
- latest_per_name
- compilerOptions
- compilerOptions
- hello.ts
- jev.py
- Journal records are hashed as file bytes, and git is the notary
- SEEN-088: Integrate Jev AI typed decisions into the harness gates
- tasks
- DiscardTest
- advance
- risk.py
- agent/package.json
- connectors/package.json
- core/package.json
- api/package.json
- vitest
- api/tsconfig.json
- worker/tsconfig.json
- SEEN-007: Go live on Google Cloud after the go/no-go decision
- .start
- SEEN-089: Enforce TDD and CI quality gates in the harness
- SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain
- agent/tsconfig.json
- connectors/tsconfig.json
- core/tsconfig.json
- TicketFiguresTest
- SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports
- SEEN-099: Set the context budget and measure what the tools changed
- DoctorTest
- ClarifiedCriteriaTest
- next-env.d.ts
- providers/src/index.ts
- pull_request_template.md
- context.py
- pre-commit
- dependencies
- scripts
- SEEN-096: Add codegraph and route the graph command to it
- Week 39 of 2026
- Sprint 0: 37 of 81 points delivered
- storage.ts
- providers/package.json
- paths.py
- graph.py
- RepositoryTest
- SEEN-098: Add repowise and carry its risk answer into the gate
- postmark.ts
- Outcome
- BudgetRulesTest
- coverage.py
- SEEN-102: Decide on the repowise PR bot for a private repository
- SyncTest
- ComparisonTest
- cost.py
- health.controller.ts
- outbound.ts
- HarnessError
- api/nest-cli.json
- worker/nest-cli.json
- LintExemptionTest
- OverlapTest
- skills.py
- Seen
- SEEN-101: Let a journal survive its ticket being renamed
- .fingerprint
- ReportTest
- ToolCallsTest
- providers/tsconfig.json
- devDependencies
- The Seen harness
- MarketplaceHostTest
- Seen
- SEEN-093: Add harness reopen to void a receipt before merge
- PostmarkController
- helpers.py
- Seen: Claude Code entry point
- serialise
- write_once
- dev-down.sh
- dev-up.sh
- replay-inbound.sh
- tunnel.sh

## God Nodes (most connected - your core abstractions)
1. `HarnessError` - 82 edges
2. `require()` - 73 edges
3. `Repository` - 60 edges
4. `CommandTest` - 44 edges
5. `execute()` - 31 edges
6. `clarify_evidence()` - 30 edges
7. `solution_evidence()` - 23 edges
8. `DeliveryWalk` - 21 edges
9. `DoctorTest` - 21 edges
10. `RecordTest` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-100-let-a-gate-tell-an-open-question-from-an.md → harness/cli.py
- `Description` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py
- `Agent runtime and the policy gate` --references--> `read_evidence()`  [INFERRED]
  docs/architecture.md → harness/cli.py
- `Development harness` --references--> `advance()`  [INFERRED]
  CONTEXT.md → harness/cli.py

## Import Cycles
- None detected.

## Communities (194 total, 20 thin omitted)

### Community 0 - "gates.py"
Cohesion: 0.09
Nodes (37): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-103: Declare non-code mode at the solution stage, not after it, _evidence() (+29 more)

### Community 1 - ".evaluate"
Cohesion: 0.08
Nodes (20): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-095: Check a ticket's status against its own journal, advance_record() (+12 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (28): metadata, config, dependencies, next, react, react-dom, @seen/core, description (+20 more)

### Community 3 - "Repository"
Cohesion: 0.10
Nodes (13): Every file in the project that git can see, ignored files excluded., Record files only. A journal directory also holds kpi.json and attachments,…, Journal files git has seen change after the commit that created them. The hash…, The branch work merges into, asked of git rather than assumed., Whether a commit has already merged, locally or on the remote. Both are asked:…, The working copy a harness command operates on., Whether the remote already holds this commit as the tip of this branch., Refuse to operate from a subdirectory or from another repository. (+5 more)

### Community 6 - "boundary.ts"
Cohesion: 0.16
Nodes (18): Three defects the tests could not see, CLOUD_SDK_PREFIXES, CloudSdkImport, EXEMPT, findCloudSdkImports(), isCloudSdk(), SEARCHED, SKIP_DIRECTORIES (+10 more)

### Community 8 - "cli.py"
Cohesion: 0.06
Nodes (68): argparse, Run one check and return the evidence to record., run(), build_parser(), check(), coverage(), decide(), describe() (+60 more)

### Community 9 - "DeliveryWalk"
Cohesion: 0.06
Nodes (16): DeliveryTest, DeliveryWalk, The walk to a delivered ticket, without the tests. Separated so other files can…, No test reaches GitHub. Green by default; a test that cares says otherwise., Take a ticket through every stage, with real recorded checks., BookkeepingAfterReceiptTest, DeliveryChecksTest, broken() (+8 more)

### Community 10 - ".graph"
Cohesion: 0.11
Nodes (12): GraphFixture, GraphTest, Which tool answers which question. codegraph indexes symbols, so it answers…, A guard, not a change: graphify knows files and pull requests., Without the MCP server running, the index is as old as the last sync., why, health and risk: what the history says rather than what the code is., Stubs and helpers. No tests of its own, so nothing is run twice., A graphify on PATH that reports what it was asked, and nothing else. (+4 more)

### Community 12 - ".mcp.json"
Cohesion: 0.40
Nodes (4): graphify-mcp, repowise, graphify, repowise

### Community 13 - "app.module.ts"
Cohesion: 0.14
Nodes (13): AppModule, AppendResult, InMemoryThreadStore, MessageThread, THREAD_STORE, ThreadMessage, ThreadStore, apps_api_src_webhooks_fixtures_postmark_inbound (+5 more)

### Community 14 - "SEEN-087: Install graphify, build the repo graph and wire it into both assistants"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-087: Install graphify, build the repo graph and wire it into both assistants

### Community 15 - "worker/package.json"
Cohesion: 0.08
Nodes (23): dependencies, bullmq, ioredis, @seen/core, @seen/providers, description, devDependencies, @nestjs/cli (+15 more)

### Community 16 - ".stub_repowise"
Cohesion: 0.11
Nodes (11): ElidedBlastRadiusTest, repowise elides a large payload and leaves a marker in its place. Observed at…, One file is four arguments: --target X --changed-file X., repowise's own marker already says how to restore it., What the model sees when it is asked how risky this change is., Not as a low score, and not as silence., One extra payload string per question is not free: SEEN-101., The half of the ticket that is about tests rather than about size. (+3 more)

### Community 17 - "Seen: product requirements (MVP)"
Cohesion: 0.11
Nodes (18): 10. Pricing and metering, 11. Data, security and compliance, 12. Non-functional requirements, 13. Success metrics and gates, 14. Release plan, 15. Risks, 16. Open questions, 17. Glossary (+10 more)

### Community 18 - "doctor.py"
Cohesion: 0.05
Nodes (51): datetime, gitignore_problems(), hook_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, The skill copies both assistants read, against the one file that makes them. (+43 more)

### Community 19 - "CoverageTest"
Cohesion: 0.38
Nodes (3): CoverageTest, Coverage on packages/core, measured by one fixed command and never allowed to…, The shape vitest's json-summary reporter writes.

### Community 20 - "stub"
Cohesion: 0.05
Nodes (31): Commands, KPIs, Principles, Repository layout, Security controls, Seen: development harness, The five stages, Tickets (+23 more)

### Community 21 - "kpi.py"
Cohesion: 0.10
Nodes (27): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen: MVP architecture, Services (+19 more)

### Community 22 - "Tickets"
Cohesion: 0.20
Nodes (10): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+2 more)

### Community 23 - "package.json"
Cohesion: 0.06
Nodes (33): devDependencies, eslint, @eslint/js, turbo, @types/node, typescript, typescript-eslint, vitest (+25 more)

### Community 24 - "SEEN-086: Build the Seen harness CLI with staged journal and receipts"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-086: Build the Seen harness CLI with staged journal and receipts

### Community 25 - "Seen: MVP development plan"
Cohesion: 0.25
Nodes (8): Day-0 checklist (human, before or during Sprint 0), Gates, Not in the MVP, Risks to the plan, Seen: MVP development plan, Shape of the plan, Sprint calendar, Team and capacity

### Community 26 - "SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages

### Community 27 - "StateForTest"
Cohesion: 0.27
Nodes (6): Record 1 as start writes it, with the pieces state_for reads., The rename SEEN-096 made, and the silent fallback it exposed., A duplicated id is a mistake worth seeing, not a choice to make. Only when the…, SEEN-10 must not glob up SEEN-100., Every journal so far carries ticket_id, but the envelope is the promise., StateForTest

### Community 28 - "SEEN-001: Register Amazon SP-API developer and file Ads API application"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-001: Register Amazon SP-API developer and file Ads API application

### Community 29 - "SEEN-002: Obtain eBay production keys and file Application Growth Check"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-002: Obtain eBay production keys and file Application Growth Check

### Community 30 - "SEEN-003: Obtain Bol credentials and verify OAuth grant and rate limits"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-003: Obtain Bol credentials and verify OAuth grant and rate limits

### Community 31 - "SEEN-004: Set up Postmark inbound domain and Stripe account"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-004: Set up Postmark inbound domain and Stripe account

### Community 32 - "SEEN-005: Review Partao contract and draft DPA and Amazon data statement"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-005: Review Partao contract and draft DPA and Amazon data statement

### Community 33 - "StatusAgainstJournalTest"
Cohesion: 0.31
Nodes (4): A commit that is on main, which is what a merged receipt attests., The normal state between writing a receipt and pressing merge., Eighty tickets are todo with no journal; saying so every run is noise., StatusAgainstJournalTest

### Community 34 - "SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table

### Community 35 - "SEEN-009: Define connector interface, capability matrix and credential access"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-009: Define connector interface, capability matrix and credential access

### Community 36 - "SEEN-010: Add per-marketplace rate limiting with header-driven backoff"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-010: Add per-marketplace rate limiting with header-driven backoff

### Community 37 - "SEEN-011: Build Bol Retailer API v10 connector for orders to commissions"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-011: Build Bol Retailer API v10 connector for orders to commissions

### Community 38 - "SEEN-012: Build eBay connector for orders, returns, transactions and payouts"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-012: Build eBay connector for orders, returns, transactions and payouts

### Community 39 - "SEEN-013: Build Amazon SP-API connector for orders, reports and Finances"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-013: Build Amazon SP-API connector for orders, reports and Finances

### Community 40 - "SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences

### Community 41 - "SEEN-015: Verify Amazon report names and Finances transactions version"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-015: Verify Amazon report names and Finances transactions version

### Community 42 - "SEEN-016: Encode fee schedules per marketplace and category in core"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-016: Encode fee schedules per marketplace and category in core

### Community 43 - "SEEN-017: Compute fee_expectations per order line from schedules and APIs"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-017: Compute fee_expectations per order line from schedules and APIs

### Community 44 - "SEEN-018: Match settlement_lines to order_lines deterministically"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-018: Match settlement_lines to order_lines deterministically

### Community 45 - "SEEN-019: Implement fee detectors as pure tested functions"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-019: Implement fee detectors as pure tested functions

### Community 46 - "SEEN-020: Implement shipment, return and inventory detectors"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-020: Implement shipment, return and inventory detectors

### Community 47 - "SEEN-021: Persist findings with rule, confidence, evidence refs and deadline"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-021: Persist findings with rule, confidence, evidence refs and deadline

### Community 48 - "SEEN-022: Generate the audit PDF with scorecard and line annex"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-022: Generate the audit PDF with scorecard and line annex

### Community 49 - "SEEN-023: Measure the recoverable pool per marketplace"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-023: Measure the recoverable pool per marketplace

### Community 50 - "SEEN-024: Ship ops console v1 for tenants, connections and sync status"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-024: Ship ops console v1 for tenants, connections and sync status

### Community 51 - "SEEN-025: Run three real 90-day audits and deliver the PDFs"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-025: Run three real 90-day audits and deliver the PDFs

### Community 52 - "SEEN-026: Verify Bol compensation request form structure"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-026: Verify Bol compensation request form structure

### Community 53 - "SEEN-027: Build the claims rail with api, assisted and track modes"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-027: Build the claims rail with api, assisted and track modes

### Community 54 - "SEEN-028: Contest eBay payment disputes and cases by API"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-028: Contest eBay payment disputes and cases by API

### Community 55 - "SEEN-029: Build the Bol assisted case pack with tracking"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-029: Build the Bol assisted case pack with tracking

### Community 56 - "SEEN-030: Build the Amazon assisted case pack with report tracking"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-030: Build the Amazon assisted case pack with report tracking

### Community 57 - "SEEN-031: Match credits to claims as the only billable event"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-031: Match credits to claims as the only billable event

### Community 58 - "SEEN-032: Write append-only audit_events before every side effect"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-032: Write append-only audit_events before every side effect

### Community 59 - "SEEN-033: Implement policy gate v1 with caps and reversibility"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-033: Implement policy gate v1 with caps and reversibility

### Community 60 - "SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting

### Community 61 - "SEEN-035: Build the approval inbox with approve, edit and reject"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-035: Build the approval inbox with approve, edit and reject

### Community 62 - "SEEN-036: Create the eval set of 30 real findings with expected drafts"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-036: Create the eval set of 30 real findings with expected drafts

### Community 63 - "SEEN-037: File the first ten claims across two marketplaces from the inbox"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-037: File the first ten claims across two marketplaces from the inbox

### Community 64 - "SEEN-038: Verify Shopify Payments payout scopes and create the custom app"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-038: Verify Shopify Payments payout scopes and create the custom app

### Community 65 - "SEEN-039: Create Stripe customers with SEPA and card and handle webhooks"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-039: Create Stripe customers with SEPA and card and handle webhooks

### Community 66 - "SEEN-040: Issue invoices with recovery-share lines from credited claims only"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-040: Issue invoices with recovery-share lines from credited claims only

### Community 67 - "SEEN-041: Generate and send the monthly statement PDF"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-041: Generate and send the monthly statement PDF

### Community 68 - "SEEN-042: Ship the Reconcile module with margin and fee-change alerts"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-042: Ship the Reconcile module with margin and fee-change alerts

### Community 69 - "SEEN-043: Export finance CSV of settlements and matched lines"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-043: Export finance CSV of settlements and matched lines

### Community 70 - "SEEN-044: Build the Shopify Admin GraphQL connector as product and stock truth"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-044: Build the Shopify Admin GraphQL connector as product and stock truth

### Community 71 - "SEEN-045: Add module switches per tenant with scheduling and billing hooks"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-045: Add module switches per tenant with scheduling and billing hooks

### Community 72 - "SEEN-046: Build customer-facing findings and claims views"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-046: Build customer-facing findings and claims views

### Community 73 - "SEEN-047: Issue the first invoice and send the signed statement"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-047: Issue the first invoice and send the signed statement

### Community 74 - "SEEN-048: Verify Kaufland settlement and ticket endpoints and obtain keys"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-048: Verify Kaufland settlement and ticket endpoints and obtain keys

### Community 75 - "SEEN-049: Encode listing spec rules per marketplace in core"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-049: Encode listing spec rules per marketplace in core

### Community 76 - "SEEN-050: Ingest listings with content hash and drift detection"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-050: Ingest listings with content hash and drift detection

### Community 77 - "SEEN-051: Add propose_listing_fix and apply_listing_fix tools with diff"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-051: Add propose_listing_fix and apply_listing_fix tools with diff

### Community 78 - "SEEN-052: Write listing content through Bol and eBay APIs"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-052: Write listing content through Bol and eBay APIs

### Community 79 - "SEEN-053: Write listing content through Amazon Listings Items and Feeds"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-053: Write listing content through Amazon Listings Items and Feeds

### Community 80 - "SEEN-054: Build the Kaufland connector with tickets as the claims rail"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-054: Build the Kaufland connector with tickets as the claims rail

### Community 81 - "SEEN-055: Monitor unauthorised sellers from competing offers"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-055: Monitor unauthorised sellers from competing offers

### Community 82 - "SEEN-056: Show Comply defects and fix diffs in the inbox"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-056: Show Comply defects and fix diffs in the inbox

### Community 83 - "SEEN-057: Verify listing fixes on three marketplaces and file Kaufland tickets"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-057: Verify listing fixes on three marketplaces and file Kaufland tickets

### Community 84 - "SEEN-058: Verify eBay messaging deprecation and choose the message path"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-058: Verify eBay messaging deprecation and choose the message path

### Community 85 - "SEEN-059: Verify Otto rate limits and obtain Otto API keys"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-059: Verify Otto rate limits and obtain Otto API keys

### Community 86 - "SEEN-060: Build the Otto connector for orders, returns, receipts and messages"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-060: Build the Otto connector for orders, returns, receipts and messages

### Community 87 - "SEEN-061: Ingest message_threads from Amazon, eBay, Kaufland and Otto"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-061: Ingest message_threads from Amazon, eBay, Kaufland and Otto

### Community 88 - "SEEN-062: Parse the forwarded mailbox via Postmark inbound into threads"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-062: Parse the forwarded mailbox via Postmark inbound into threads

### Community 89 - "SEEN-063: Add reply_message tool bound to tenant service policies"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-063: Add reply_message tool bound to tenant service policies

### Community 90 - "SEEN-064: Apply return and cancellation decisions through returns APIs"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-064: Apply return and cancellation decisions through returns APIs

### Community 91 - "SEEN-065: Implement the trust ramp with autonomy per action type"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-065: Implement the trust ramp with autonomy per action type

### Community 92 - "SEEN-066: Track claim and dispute deadlines with alerts"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-066: Track claim and dispute deadlines with alerts

### Community 93 - "SEEN-067: Show Serve threads and drafts in the inbox"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-067: Show Serve threads and drafts in the inbox

### Community 94 - "SEEN-068: Verify the Kaufland virtual buy box endpoint"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-068: Verify the Kaufland virtual buy box endpoint

### Community 95 - "SEEN-069: Snapshot competing offers from Bol by EAN and eBay by GTIN"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-069: Snapshot competing offers from Bol by EAN and eBay by GTIN

### Community 96 - "SEEN-070: Snapshot Amazon pricing on a tiered clock"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-070: Snapshot Amazon pricing on a tiered clock

### Community 97 - "SEEN-071: Model net margin per marketplace from cost layers"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-071: Model net margin per marketplace from cost layers

### Community 98 - "SEEN-072: Implement the price governor with bands, ceilings and cooldowns"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-072: Implement the price governor with bands, ceilings and cooldowns

### Community 99 - "SEEN-073: Write prices through Bol Offers and eBay Inventory offers"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-073: Write prices through Bol Offers and eBay Inventory offers

### Community 100 - "SEEN-074: Add propose_price and apply_price tools with buy-box tracking"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-074: Add propose_price and apply_price tools with buy-box tracking

### Community 101 - "SEEN-075: Meter headroom_entries and show the Price view"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-075: Meter headroom_entries and show the Price view

### Community 102 - "SEEN-076: Run the daily Bol buy-box feedback loop"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-076: Run the daily Bol buy-box feedback loop

### Community 103 - "SEEN-077: Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-077: Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted

### Community 104 - "SEEN-078: Attribute ad cost into margin and publish the weekly Grow report"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-078: Attribute ad cost into margin and publish the weekly Grow report

### Community 105 - "SEEN-079: Propose campaign budgets through the gate, no autonomous creation"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-079: Propose campaign budgets through the gate, no autonomous creation

### Community 106 - "SEEN-080: Build the retailer read-only view via a scoped link"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-080: Build the retailer read-only view via a scoped link

### Community 107 - "SEEN-081: Load test ingest on 50 tenants and run rate-limit chaos"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-081: Load test ingest on 50 tenants and run rate-limit chaos

### Community 108 - "SEEN-082: Run RLS penetration tests and the restore drill"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-082: Run RLS penetration tests and the restore drill

### Community 109 - "SEEN-083: Expire Amazon PII after 30 days and delete tenants on request"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-083: Expire Amazon PII after 30 days and delete tenants on request

### Community 110 - "SEEN-084: Build the day-120 metrics dashboard and CSV export"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-084: Build the day-120 metrics dashboard and CSV export

### Community 111 - "SEEN-085: Run restore drill, close pen-test findings, sign metrics pack"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-085: Run restore drill, close pen-test findings, sign metrics pack

### Community 113 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, declaration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, forceConsistentCasingInFileNames (+15 more)

### Community 114 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowJs, baseUrl, incremental, isolatedModules, jsx, lib, module (+6 more)

### Community 115 - "hello.ts"
Cohesion: 0.24
Nodes (8): connection, HELLO_QUEUE, HelloPayload, HelloResult, HelloWorker, startHelloWorker(), worker, bullmq

### Community 116 - "jev.py"
Cohesion: 0.09
Nodes (29): Decisions already taken for this stage and this attempt, latest per question., Every question this stage owns, answered once. An answer already recorded for…, recorded_decisions(), stage_decisions(), _answer_from_human(), _ask_api(), ask_many(), build_questions() (+21 more)

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 119 - "tasks"
Cohesion: 0.13
Nodes (14): dependsOn, outputs, cache, persistent, dependsOn, $schema, tasks, build (+6 more)

### Community 120 - "DiscardTest"
Cohesion: 0.11
Nodes (7): DiscardTest, EnvironmentValueTest, FalsePositiveTest, Removing a journal, which the harness could not do until now. It exists because…, No record carries a credential, whatever kind of record it is., A rule that refuses ordinary words is a rule people turn off. CI found this…, A journal record legitimately contains file paths, so PATH is skipped.

### Community 121 - "advance"
Cohesion: 0.09
Nodes (26): Asking the graphs, Five rules you cannot infer, The context budget, The five stages, The Seen harness, The worked example, What the harness will refuse, Five rules you cannot infer (+18 more)

### Community 122 - "risk.py"
Cohesion: 0.36
Nodes (7): _absent(), assess(), changed_files(), What repowise says about the change in front of the session. A risk decision…, What the working tree changes against HEAD, tracked and untracked., The change-risk answer, or a recorded reason there is none. Scored from the…, _run()

### Community 123 - "agent/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 124 - "connectors/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 125 - "core/package.json"
Cohesion: 0.14
Nodes (13): description, devDependencies, @vitest/coverage-v8, @vitest/coverage-v8, main, name, private, scripts (+5 more)

### Community 126 - "api/package.json"
Cohesion: 0.12
Nodes (14): description, @nestjs/cli, @seen/core, @seen/providers, main, name, private, version (+6 more)

### Community 127 - "vitest"
Cohesion: 0.15
Nodes (4): packageName, packageName, sha256(), vitest

### Community 128 - "api/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 129 - "worker/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 130 - "SEEN-007: Go live on Google Cloud after the go/no-go decision"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-007: Go live on Google Cloud after the go/no-go decision

### Community 131 - ".start"
Cohesion: 0.05
Nodes (20): NonCodeCoverageTest, A ticket with no behaviour to prove owes no coverage figure. Its own setUp…, RedRuleTest, AdvanceTest, BranchTest, clarify_evidence(), DraftTest, NoteAndCheckTest (+12 more)

### Community 132 - "SEEN-089: Enforce TDD and CI quality gates in the harness"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-089: Enforce TDD and CI quality gates in the harness

### Community 133 - "SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain

### Community 134 - "agent/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 135 - "connectors/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 136 - "core/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 137 - "TicketFiguresTest"
Cohesion: 0.14
Nodes (9): at(), journal_with_a_return(), A timestamp minutes after ten, so a journal can span an hour or more., A review re-run lists its findings again; they are still the same findings., start, clarify, solution, tdd, review, back to tdd, review again, deliver,…, Rework is time spent, so tdd counts both visits rather than the last., record(), RepeatedReviewTest (+1 more)

### Community 138 - "SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports

### Community 139 - "SEEN-099: Set the context budget and measure what the tools changed"
Cohesion: 0.07
Nodes (26): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers, Acceptance criteria, Blocks (+18 more)

### Community 140 - "DoctorTest"
Cohesion: 0.18
Nodes (3): AppendOnlyScopeTest, DoctorTest, Records are append-only. The files beside them are not records.

### Community 141 - "ClarifiedCriteriaTest"
Cohesion: 0.17
Nodes (4): ClarifiedCriteriaTest, Naming an unknown used to read as leaving it open, three times over., Unresolved is not enough: nothing said about what would resolve it., The other calibrated question, unchanged by this one.

### Community 143 - "providers/src/index.ts"
Cohesion: 0.21
Nodes (17): STORAGE_PROVIDERS, StorageProviderName, Attributes, AttributeValue, consoleTelemetryProvider(), CostEntry, createTelemetryProvider(), nowUnixNano() (+9 more)

### Community 144 - "pull_request_template.md"
Cohesion: 0.29
Nodes (6): Acceptance criteria, Evidence, Limits, Receipt, Review findings, Summary

### Community 145 - "context.py"
Cohesion: 0.24
Nodes (10): compare(), overlaps(), _per_point(), qualifying(), Whether three knowledge tools paid for the context they occupy. codegraph,…, Tickets started after both tools existed, with figures to compare. A ticket…, The two rows, the baseline beside them, and what the rule points to., What a graph record asked about, as the command carries it. (+2 more)

### Community 147 - "dependencies"
Cohesion: 0.22
Nodes (9): dependencies, @nestjs/common, @nestjs/core, @nestjs/platform-express, nodemailer, reflect-metadata, rxjs, @seen/core (+1 more)

### Community 148 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, start, test, typecheck

### Community 149 - "SEEN-096: Add codegraph and route the graph command to it"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-096: Add codegraph and route the graph command to it

### Community 150 - "Week 39 of 2026"
Cohesion: 0.33
Nodes (5): Against the targets, Findings, Not measurable yet, Week 39 of 2026, What delivered

### Community 151 - "Sprint 0: 37 of 81 points delivered"
Cohesion: 0.29
Nodes (6): Against the targets, Findings, Not measurable yet, Sprint 0: 37 of 81 points delivered, The context budget, What delivered

### Community 152 - "storage.ts"
Cohesion: 0.24
Nodes (14): createSecretsProvider(), environmentVariableFor(), envSecretsProvider(), SECRETS_PROVIDERS, SecretsProviderName, Environment, notUntilGoLive(), ProviderConfigurationError (+6 more)

### Community 153 - "providers/package.json"
Cohesion: 0.11
Nodes (17): dependencies, @supabase/supabase-js, description, devDependencies, @vitest/coverage-v8, @vitest/coverage-v8, main, name (+9 more)

### Community 154 - "paths.py"
Cohesion: 0.16
Nodes (12): ask(), main(), Ask one question about real records under two sets of criteria, side by side.…, Exactly what the stage gate sends: the ticket as it stands and the record.…, One question, one set of criteria, one probability back., state_of(), Stage names, project-relative locations and the shapes files must have.…, Entry point: python3 harness/run.py <command>. (+4 more)

### Community 155 - "graph.py"
Cohesion: 0.18
Nodes (14): demonstrates_failure(), phases_for(), Running and recording a verification command. A check is a real subprocess in…, Whether a run is evidence that a test failed. Exit zero is a passing command,…, ask(), build_command(), _index_counts(), Asking the knowledge graphs a question and keeping the answer in the journal.… (+6 more)

### Community 157 - "SEEN-098: Add repowise and carry its risk answer into the gate"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-098: Add repowise and carry its risk answer into the gate

### Community 158 - "postmark.ts"
Cohesion: 0.22
Nodes (12): header(), isPostmarkInbound(), MARKETPLACE_DOMAINS, marketplaceOf(), normaliseSubject(), PostmarkInbound, tenantOf(), threadKey() (+4 more)

### Community 159 - "Outcome"
Cohesion: 0.10
Nodes (13): Acceptance criteria, Blocks, Context, Depends on, Description, Known and deliberately left, Outcome, SEEN-097: Set up the local Docker development environment (+5 more)

### Community 160 - "BudgetRulesTest"
Cohesion: 0.22
Nodes (3): BudgetRulesTest, A rule in a prompt is not a rule., A date would count the tickets that installed them, which it must not.

### Community 161 - "coverage.py"
Cohesion: 0.24
Nodes (9): baseline(), compare(), measured(), Line coverage on the packages the harness holds a floor under. One fixed…, The last delivered figure, or None when nothing has delivered yet., The line percentage vitest's json-summary reporter wrote., Attach the baseline and the delta to a finished measurement run., Move the baseline. Called at delivery and nowhere else. (+1 more)

### Community 162 - "SEEN-102: Decide on the repowise PR bot for a private repository"
Cohesion: 0.17
Nodes (12): A note on how it got here, Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-102: Decide on the repowise PR bot for a private repository (+4 more)

### Community 164 - "ComparisonTest"
Cohesion: 0.33
Nodes (3): ComparisonTest, What the report says about the figures, and when it refuses to say it., Two numbers divided is not evidence when there are two tickets.

### Community 165 - "cost.py"
Cohesion: 0.32
Nodes (7): log_directory(), Tokens spent on a ticket, read from the session logs. Only four numbers are…, Where Claude Code keeps this project's session logs, by its own naming., How many tool calls a ticket's window contains. Counted from the same logs and…, Token counts from entries falling inside a ticket's window. Null rather than…, tokens_between(), tool_calls_between()

### Community 166 - "health.controller.ts"
Cohesion: 0.29
Nodes (6): HealthController, Controller, Get, LEDGER_CURRENCY, packageName, sumCents()

### Community 167 - "outbound.ts"
Cohesion: 0.20
Nodes (8): Environment, mailpit(), MailpitMessage, createMailer(), Environment, Mailer, OutboundMail, nodemailer

### Community 168 - "HarnessError"
Cohesion: 0.07
Nodes (44): Exception, harness, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., check_runs(), _gh(), pull_request() (+36 more)

### Community 169 - "api/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 170 - "worker/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 172 - "OverlapTest"
Cohesion: 0.43
Nodes (3): OverlapTest, One question with two right addressees is one tool too many., Asking again is not redundancy between tools.

### Community 173 - "skills.py"
Cohesion: 0.32
Nodes (7): drift(), One maintained skill, and the copies each assistant reads. The copies are…, One copy: the frontmatter an assistant reads, then the maintained body., Write every copy from the source, and say which were written., Committed copies that do not match what the source would generate., render(), sync()

### Community 174 - "Seen"
Cohesion: 0.25
Nodes (8): Commands, Getting it running, If it will not start, Seen, Tests, The cloud is a configuration, What it costs to run, Where things run

### Community 175 - "SEEN-101: Let a journal survive its ticket being renamed"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-101: Let a journal survive its ticket being renamed

### Community 176 - ".fingerprint"
Cohesion: 0.29
Nodes (3): Every path git reports as changed, with renames resolved to both sides., Git's own hash for files on disk, in one call rather than one each., A hash of the tree's content, ignoring the journal and the drafts. Content, not…

### Community 179 - "providers/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 180 - "devDependencies"
Cohesion: 0.33
Nodes (6): devDependencies, @nestjs/cli, @nestjs/testing, supertest, @types/nodemailer, @types/supertest

### Community 181 - "The Seen harness"
Cohesion: 0.33
Nodes (5): Asking the graphs, The context budget, The Seen harness, The worked example, What the harness will refuse

### Community 183 - "Seen"
Cohesion: 0.33
Nodes (6): Development harness, Example dialogue, Flagged ambiguities, Language, Product, Seen

### Community 184 - "SEEN-093: Add harness reopen to void a receipt before merge"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-093: Add harness reopen to void a receipt before merge

### Community 185 - "PostmarkController"
Cohesion: 0.40
Nodes (4): PostmarkController, Controller, Inject, Post

### Community 186 - "helpers.py"
Cohesion: 0.08
Nodes (19): add_remote(), make_project(), ProjectTest, A throwaway project to run harness commands against. Tests never touch the…, A bare repository to push to, so delivery can be verified without a network., A git repository shaped like Seen: a ticket, the harness files, one commit., Base class giving each test its own project and ticket., No test calls the decision API, and none inherits a shell credential. A test… (+11 more)

### Community 187 - "Seen: Claude Code entry point"
Cohesion: 0.40
Nodes (5): Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (100, 357 build points), Working a ticket

## Knowledge Gaps
- **863 isolated node(s):** `graphify-mcp`, `repowise`, `$schema`, `collection`, `sourceRoot` (+858 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1223 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `gates.py`, `.evaluate`, `Repository`, `.start`, `RecordTest`, `cli.py`, `DeliveryWalk`, `.graph`, `DoctorTest`, `ReportTest`, `doctor.py`, `CoverageTest`, `jev.py`, `stub`, `DiscardTest`, `advance`, `StateForTest`, `RepositoryTest`?**
  _High betweenness centrality (0.265) - this node is a cross-community bridge._
- **Why does `Outcome` connect `Outcome` to `cli.py`, `app.module.ts`, `boundary.ts`?**
  _High betweenness centrality (0.257) - this node is a cross-community bridge._
- **Why does `require()` connect `cli.py` to `gates.py`, `coverage.py`, `Repository`, `HarnessError`, `skills.py`, `.fingerprint`, `doctor.py`, `jev.py`, `advance`, `paths.py`, `graph.py`, `Outcome`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `HarnessError` (e.g. with `list_tickets()` and `main()`) actually correct?**
  _`HarnessError` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `repowise`, `$schema` to the rest of the system?**
  _863 weakly-connected nodes found - possible documentation gaps or missing edges._