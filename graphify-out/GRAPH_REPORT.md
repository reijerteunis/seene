# Graph Report - seene  (2026-09-24)

## Corpus Check
- 540 files · ~179,036 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .toml 1)

## Summary
- 2015 nodes · 3797 edges · 163 communities (154 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 96 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `950085a5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- gates.py
- .evaluate
- web/package.json
- Repository
- EntryPointTest
- Seen: Claude Code entry point
- RecordTest
- require
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
- SEEN-102: Decide on the repowise PR bot for a private repository
- compilerOptions
- compilerOptions
- IsolationTest
- jev.py
- Journal records are hashed as file bytes, and git is the notary
- SEEN-088: Integrate Jev AI typed decisions into the harness gates
- tasks
- DiscardTest
- advance
- state_for
- agent/package.json
- connectors/package.json
- core/package.json
- api/package.json
- vitest
- api/tsconfig.json
- worker/tsconfig.json
- SEEN-007: Go live on Google Cloud after the go/no-go decision
- CommandTest
- SEEN-089: Enforce TDD and CI quality gates in the harness
- SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain
- agent/tsconfig.json
- connectors/tsconfig.json
- core/tsconfig.json
- TicketFiguresTest
- SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports
- SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- DoctorTest
- ClarifiedCriteriaTest
- next-env.d.ts
- pull_request_template.md
- pre-commit
- dependencies
- scripts
- SEEN-096: Add codegraph and route the graph command to it
- Week 39 of 2026
- Sprint 0: 32 of 78 points delivered
- SEEN-093: Add harness reopen to void a receipt before merge
- SEEN-094: Verify delivery against CI and verify the merge against the receipt
- cli.py
- graph.py
- SEEN-098: Add repowise and carry its risk answer into the gate
- SEEN-097: Set up the local Docker development environment
- coverage.py
- SEEN-099: Set the context budget and measure what the tools changed
- SyncTest
- core/src/index.ts
- ProjectTest
- HarnessError
- devDependencies

## God Nodes (most connected - your core abstractions)
1. `HarnessError` - 79 edges
2. `require()` - 72 edges
3. `Repository` - 60 edges
4. `CommandTest` - 40 edges
5. `execute()` - 31 edges
6. `clarify_evidence()` - 26 edges
7. `DeliveryWalk` - 21 edges
8. `DoctorTest` - 21 edges
9. `RecordTest` - 19 edges
10. `advance()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Agent runtime and the policy gate` --references--> `read_evidence()`  [INFERRED]
  docs/architecture.md → harness/cli.py
- `Working a ticket` --references--> `sync()`  [INFERRED]
  CLAUDE.md → harness/skills.py
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-100-let-a-gate-tell-an-open-question-from-an.md → harness/cli.py
- `Description` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py

## Import Cycles
- None detected.

## Communities (163 total, 9 thin omitted)

### Community 0 - "gates.py"
Cohesion: 0.10
Nodes (31): demonstrates_failure(), phases_for(), Running and recording a verification command. A check is a real subprocess in…, Whether a run is evidence that a test failed. Exit zero is a passing command,…, _evidence(), cited_check(), _clarify(), evaluate() (+23 more)

### Community 1 - ".evaluate"
Cohesion: 0.08
Nodes (19): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-095: Check a ticket's status against its own journal, advance_record() (+11 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (28): metadata, config, dependencies, next, react, react-dom, @seen/core, description (+20 more)

### Community 3 - "Repository"
Cohesion: 0.06
Nodes (17): Every file in the project that git can see, ignored files excluded., Record files only. A journal directory also holds kpi.json and attachments,…, Journal files git has seen change after the commit that created them. The hash…, The branch work merges into, asked of git rather than assumed., Whether a commit has already merged, locally or on the remote. Both are asked:…, The working copy a harness command operates on., Whether the remote already holds this commit as the tip of this branch., Refuse to operate from a subdirectory or from another repository. (+9 more)

### Community 6 - "Seen: Claude Code entry point"
Cohesion: 0.40
Nodes (5): Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (100, 357 build points), Working a ticket

### Community 8 - "require"
Cohesion: 0.06
Nodes (62): Run one check and return the evidence to record., run(), check(), coverage(), decide(), describe(), discard_journal(), execute() (+54 more)

### Community 9 - "DeliveryWalk"
Cohesion: 0.05
Nodes (17): DeliveryTest, DeliveryWalk, The walk to a delivered ticket, without the tests. Separated so other files can…, No test reaches GitHub. Green by default; a test that cares says otherwise., Take a ticket through every stage, with real recorded checks., ReportTest, BookkeepingAfterReceiptTest, DeliveryChecksTest (+9 more)

### Community 10 - ".graph"
Cohesion: 0.11
Nodes (12): GraphFixture, GraphTest, Which tool answers which question. codegraph indexes symbols, so it answers…, A guard, not a change: graphify knows files and pull requests., Without the MCP server running, the index is as old as the last sync., why, health and risk: what the history says rather than what the code is., Stubs and helpers. No tests of its own, so nothing is run twice., A graphify on PATH that reports what it was asked, and nothing else. (+4 more)

### Community 12 - ".mcp.json"
Cohesion: 0.40
Nodes (4): graphify-mcp, repowise, graphify, repowise

### Community 13 - "app.module.ts"
Cohesion: 0.23
Nodes (8): AppModule, HealthController, Controller, Get, Module, @nestjs/common, @nestjs/testing, supertest

### Community 14 - "SEEN-087: Install graphify, build the repo graph and wire it into both assistants"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-087: Install graphify, build the repo graph and wire it into both assistants

### Community 15 - "worker/package.json"
Cohesion: 0.08
Nodes (25): dependencies, bullmq, ioredis, @seen/core, description, @seen/core, main, name (+17 more)

### Community 16 - ".stub_repowise"
Cohesion: 0.11
Nodes (11): ElidedBlastRadiusTest, repowise elides a large payload and leaves a marker in its place. Observed at…, One file is four arguments: --target X --changed-file X., repowise's own marker already says how to restore it., What the model sees when it is asked how risky this change is., Not as a low score, and not as silence., One extra payload string per question is not free: SEEN-101., The half of the ticket that is about tests rather than about size. (+3 more)

### Community 17 - "Seen: product requirements (MVP)"
Cohesion: 0.11
Nodes (18): 10. Pricing and metering, 11. Data, security and compliance, 12. Non-functional requirements, 13. Success metrics and gates, 14. Release plan, 15. Risks, 16. Open questions, 17. Glossary (+10 more)

### Community 18 - "doctor.py"
Cohesion: 0.06
Nodes (48): datetime, gitignore_problems(), hook_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, The skill copies both assistants read, against the one file that makes them. (+40 more)

### Community 19 - "CoverageTest"
Cohesion: 0.33
Nodes (3): CoverageTest, Coverage on packages/core, measured by one fixed command and never allowed to…, The shape vitest's json-summary reporter writes.

### Community 20 - "stub"
Cohesion: 0.06
Nodes (22): Tooling, AnswerTest, FallbackTest, GateTest, noul(), OverrideTest, QuestionTest, A transport failure is not fatal: it becomes a question for a person. The… (+14 more)

### Community 21 - "kpi.py"
Cohesion: 0.10
Nodes (27): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen: MVP architecture, Services (+19 more)

### Community 22 - "Tickets"
Cohesion: 0.20
Nodes (10): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+2 more)

### Community 23 - "package.json"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, @eslint/js, turbo, @types/node, typescript, typescript-eslint, vitest (+19 more)

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

### Community 112 - "SEEN-102: Decide on the repowise PR bot for a private repository"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-102: Decide on the repowise PR bot for a private repository

### Community 113 - "compilerOptions"
Cohesion: 0.10
Nodes (20): compilerOptions, baseUrl, declaration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, forceConsistentCasingInFileNames, lib (+12 more)

### Community 114 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowJs, baseUrl, incremental, isolatedModules, jsx, lib, module (+6 more)

### Community 116 - "jev.py"
Cohesion: 0.10
Nodes (27): _answer_from_human(), _ask_api(), ask_many(), build_questions(), build_request(), credential(), _passed(), post() (+19 more)

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 119 - "tasks"
Cohesion: 0.17
Nodes (11): dependsOn, outputs, dependsOn, $schema, tasks, build, lint, test (+3 more)

### Community 120 - "DiscardTest"
Cohesion: 0.11
Nodes (7): DiscardTest, EnvironmentValueTest, FalsePositiveTest, Removing a journal, which the harness could not do until now. It exists because…, No record carries a credential, whatever kind of record it is., A rule that refuses ordinary words is a rule people turn off. CI found this…, A journal record legitimately contains file paths, so PATH is skipped.

### Community 121 - "advance"
Cohesion: 0.05
Nodes (43): Asking the graphs, Four rules you cannot infer, The five stages, The Seen harness, The worked example, What the harness will refuse, Asking the graphs, Four rules you cannot infer (+35 more)

### Community 122 - "state_for"
Cohesion: 0.07
Nodes (33): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-100: Let a gate tell an open question from an unknowable one, Acceptance criteria (+25 more)

### Community 123 - "agent/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 124 - "connectors/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 125 - "core/package.json"
Cohesion: 0.14
Nodes (13): description, devDependencies, @vitest/coverage-v8, main, name, private, scripts, lint (+5 more)

### Community 126 - "api/package.json"
Cohesion: 0.15
Nodes (11): description, @seen/core, main, name, private, version, @nestjs/core, @nestjs/platform-express (+3 more)

### Community 127 - "vitest"
Cohesion: 0.22
Nodes (3): packageName, packageName, vitest

### Community 128 - "api/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 129 - "worker/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 130 - "SEEN-007: Go live on Google Cloud after the go/no-go decision"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-007: Go live on Google Cloud after the go/no-go decision

### Community 131 - "CommandTest"
Cohesion: 0.05
Nodes (24): BaselineTest, CitedRedTest, The baseline moves only when a ticket delivers., A red recorded before the rule existed can still be cited, so the gate checks…, A refusal has to say what happened, not what the rule is called., RedRuleTest, RefusalMessageTest, AdvanceTest (+16 more)

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

### Community 139 - "SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

### Community 140 - "DoctorTest"
Cohesion: 0.18
Nodes (3): AppendOnlyScopeTest, DoctorTest, Records are append-only. The files beside them are not records.

### Community 141 - "ClarifiedCriteriaTest"
Cohesion: 0.17
Nodes (4): ClarifiedCriteriaTest, Naming an unknown used to read as leaving it open, three times over., Unresolved is not enough: nothing said about what would resolve it., The other calibrated question, unchanged by this one.

### Community 144 - "pull_request_template.md"
Cohesion: 0.29
Nodes (6): Acceptance criteria, Evidence, Limits, Receipt, Review findings, Summary

### Community 147 - "dependencies"
Cohesion: 0.29
Nodes (7): dependencies, @nestjs/common, @nestjs/core, @nestjs/platform-express, reflect-metadata, rxjs, @seen/core

### Community 148 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, lint, start, test, typecheck

### Community 149 - "SEEN-096: Add codegraph and route the graph command to it"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-096: Add codegraph and route the graph command to it

### Community 150 - "Week 39 of 2026"
Cohesion: 0.33
Nodes (5): Against the targets, Findings, Not measurable yet, Week 39 of 2026, What delivered

### Community 151 - "Sprint 0: 32 of 78 points delivered"
Cohesion: 0.33
Nodes (5): Against the targets, Findings, Not measurable yet, Sprint 0: 32 of 78 points delivered, What delivered

### Community 152 - "SEEN-093: Add harness reopen to void a receipt before merge"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-093: Add harness reopen to void a receipt before merge

### Community 153 - "SEEN-094: Verify delivery against CI and verify the merge against the receipt"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-094: Verify delivery against CI and verify the merge against the receipt

### Community 154 - "cli.py"
Cohesion: 0.09
Nodes (24): argparse, build_parser(), lock(), main(), parse(), The commands a session runs, and the order they may be run in. Two families:…, An advisory lock, never broken automatically. Two sessions may share a…, Refuse an advance the stage's blocking questions did not allow. Each blocking… (+16 more)

### Community 155 - "graph.py"
Cohesion: 0.39
Nodes (8): ask(), build_command(), _index_counts(), Asking the knowledge graphs a question and keeping the answer in the journal.…, Nodes and edges, as codegraph status reports them. Weaker than a hash: two…, Run one verb in the project root and return what to record., _run(), tool_for()

### Community 157 - "SEEN-098: Add repowise and carry its risk answer into the gate"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-098: Add repowise and carry its risk answer into the gate

### Community 159 - "SEEN-097: Set up the local Docker development environment"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-097: Set up the local Docker development environment

### Community 161 - "coverage.py"
Cohesion: 0.24
Nodes (9): baseline(), compare(), measured(), Line coverage on the packages the harness holds a floor under. One fixed…, The last delivered figure, or None when nothing has delivered yet., The line percentage vitest's json-summary reporter wrote., Attach the baseline and the delta to a finished measurement run., Move the baseline. Called at delivery and nowhere else. (+1 more)

### Community 162 - "SEEN-099: Set the context budget and measure what the tools changed"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-099: Set the context budget and measure what the tools changed

### Community 166 - "core/src/index.ts"
Cohesion: 0.70
Nodes (3): LEDGER_CURRENCY, packageName, sumCents()

### Community 167 - "ProjectTest"
Cohesion: 0.15
Nodes (11): drift(), One copy: the frontmatter an assistant reads, then the maintained body., Committed copies that do not match what the source would generate., render(), add_remote(), make_project(), ProjectTest, A bare repository to push to, so delivery can be verified without a network. (+3 more)

### Community 168 - "HarnessError"
Cohesion: 0.07
Nodes (41): Exception, harness, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., check_runs(), _gh(), pull_request() (+33 more)

### Community 170 - "devDependencies"
Cohesion: 0.50
Nodes (4): devDependencies, @nestjs/testing, supertest, @types/supertest

## Knowledge Gaps
- **769 isolated node(s):** `graphify-mcp`, `repowise`, `name`, `version`, `private` (+764 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1064 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Seen: MVP architecture` connect `kpi.py` to `CLAUDE.md`?**
  _High betweenness centrality (0.255) - this node is a cross-community bridge._
- **Why does `read_evidence()` connect `require` to `gates.py`, `HarnessError`, `kpi.py`, `advance`, `cli.py`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Why does `HarnessError` connect `HarnessError` to `gates.py`, `.evaluate`, `Repository`, `CommandTest`, `RecordTest`, `require`, `DeliveryWalk`, `.graph`, `DoctorTest`, `doctor.py`, `CoverageTest`, `jev.py`, `stub`, `DiscardTest`, `cli.py`, `StateForTest`?**
  _High betweenness centrality (0.242) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `HarnessError` (e.g. with `list_tickets()` and `main()`) actually correct?**
  _`HarnessError` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `repowise`, `name` to the rest of the system?**
  _769 weakly-connected nodes found - possible documentation gaps or missing edges._