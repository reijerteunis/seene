# Graph Report - seene  (2026-09-23)

## Corpus Check
- 207 files · ~84,761 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .toml 1)

## Summary
- 1223 nodes · 2482 edges · 124 communities (116 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e9ee7aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- require
- .evaluate
- .start
- Repository
- EntryPointTest
- CLAUDE.md
- Seen: Claude Code entry point
- RecordTest
- execute
- DeliveryTest
- GraphTest
- graphify
- journal.py
- SEEN-087: Install graphify, build the repo graph and wire it into both assistants
- cli.py
- graph.py
- Seen: product requirements (MVP)
- doctor.py
- advance
- stub
- Seen: MVP architecture
- Tickets
- Seen: development harness
- SEEN-086: Build the Seen harness CLI with staged journal and receipts
- Seen: MVP development plan
- SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages
- .run_harness
- SEEN-001: Register Amazon SP-API developer and file Ads API application
- SEEN-002: Obtain eBay production keys and file Application Growth Check
- SEEN-003: Obtain Bol credentials and verify OAuth grant and rate limits
- SEEN-004: Set up Postmark inbound domain and Stripe account
- SEEN-005: Review Partao contract and draft DPA and Amazon data statement
- SEEN-007: Provision GCP europe-west4 and Supabase EU with telemetry
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
- IsolationTest
- test_lifecycle.py
- DoctorTest
- Seen
- jev.py
- Journal records are hashed as file bytes, and git is the notary
- SEEN-088: Integrate Jev AI typed decisions into the harness gates
- HarnessError
- TransportTest
- GateTest
- delivery.py
- StatusTest

## God Nodes (most connected - your core abstractions)
1. `require()` - 54 edges
2. `HarnessError` - 52 edges
3. `Repository` - 40 edges
4. `execute()` - 25 edges
5. `CommandTest` - 22 edges
6. `clarify_evidence()` - 21 edges
7. `DeliveryTest` - 20 edges
8. `DoctorTest` - 20 edges
9. `RecordTest` - 19 edges
10. `Seen: product requirements (MVP)` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Agent runtime and the policy gate` --references--> `read_evidence()`  [INFERRED]
  docs/architecture.md → harness/cli.py
- `Development harness` --references--> `advance()`  [INFERRED]
  CONTEXT.md → harness/cli.py
- `Working a ticket` --references--> `main()`  [INFERRED]
  CLAUDE.md → harness/cli.py
- `Security controls` --references--> `main()`  [INFERRED]
  docs/harness/workflow.md → harness/cli.py
- `Design decisions` --references--> `check()`  [INFERRED]
  docs/tickets/SEEN-086-build-the-seen-harness-cli-with-staged-journal.md → harness/cli.py

## Import Cycles
- None detected.

## Communities (124 total, 8 thin omitted)

### Community 0 - "require"
Cohesion: 0.16
Nodes (25): Refuse unless the condition holds. Never repairs, never warns and continues., require(), cited_check(), _clarify(), evaluate(), _filled(), latest_evidence(), load_template() (+17 more)

### Community 1 - ".evaluate"
Cohesion: 0.08
Nodes (15): add_remote(), make_project(), ProjectTest, A git repository shaped like Seen: a ticket, the harness files, one commit., Base class giving each test its own project and ticket., No test calls the decision API, and none inherits a shell credential. A test…, A bare repository to push to, so delivery can be verified without a network., advance_record() (+7 more)

### Community 2 - ".start"
Cohesion: 0.17
Nodes (3): BranchTest, NoteAndCheckTest, StartTest

### Community 3 - "Repository"
Cohesion: 0.07
Nodes (14): Every file in the project that git can see, ignored files excluded., Journal files git has seen change after the commit that created them. The hash…, The branch work merges into, asked of git rather than assumed., Whether a commit has already merged, locally or on the remote. Both are asked:…, The working copy a harness command operates on., Whether the remote already holds this commit as the tip of this branch., Refuse to operate from a subdirectory or from another repository., The branch, or None on a detached HEAD. Reporting commands use this, so… (+6 more)

### Community 5 - "CLAUDE.md"
Cohesion: 0.08
Nodes (31): Acceptance criteria, Blocks, Carried in from SEEN-087, Context, Depends on, Description, SEEN-089: Enforce TDD and CI quality gates in the harness, Acceptance criteria (+23 more)

### Community 6 - "Seen: Claude Code entry point"
Cohesion: 0.33
Nodes (6): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (93, 326 build points), Working a ticket

### Community 8 - "execute"
Cohesion: 0.12
Nodes (25): describe(), draft(), execute(), extra_review_fields(), go_back(), graph(), journal_folder(), list_tickets() (+17 more)

### Community 9 - "DeliveryTest"
Cohesion: 0.19
Nodes (3): DeliveryTest, Take a ticket through every stage, with real recorded checks., ReopenTest

### Community 10 - "GraphTest"
Cohesion: 0.29
Nodes (3): GraphTest, A graphify on PATH that reports what it was asked, and nothing else., The graph is derived from the tree, not evidence about it. The post-commit hook…

### Community 13 - "journal.py"
Cohesion: 0.12
Nodes (16): datetime, The append-only journal: one directory of numbered records per ticket. Each…, The one byte representation of a record. Never re-run on a written file., Write bytes to a name that must not already exist, atomically. A direct…, serialise(), write_once(), harness_tests, A throwaway project to run harness commands against. Tests never touch the… (+8 more)

### Community 14 - "SEEN-087: Install graphify, build the repo graph and wire it into both assistants"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Clarified, Context, Depends on, Description, Outcome, SEEN-087: Install graphify, build the repo graph and wire it into both assistants

### Community 15 - "cli.py"
Cohesion: 0.13
Nodes (18): argparse, build_parser(), decide(), _latest_evidence(), parse(), The commands a session runs, and the order they may be run in. Two families:…, One ticket, one branch, checked on every command that writes. The expensive…, Ask one typed question about this ticket and keep the answer. (+10 more)

### Community 16 - "graph.py"
Cohesion: 0.40
Nodes (5): ask(), build_command(), Asking graphify a question and keeping the answer in the journal. The harness…, Run one graphify verb in the project root and return what to record., time

### Community 17 - "Seen: product requirements (MVP)"
Cohesion: 0.11
Nodes (18): 10. Pricing and metering, 11. Data, security and compliance, 12. Non-functional requirements, 13. Success metrics and gates, 14. Release plan, 15. Risks, 16. Open questions, 17. Glossary (+10 more)

### Community 18 - "doctor.py"
Cohesion: 0.23
Nodes (12): gitignore_problems(), journal_problems(), link_problems(), python_problems(), The self-check a session runs before it starts working. It reports problems…, Run every check and collect what is wrong., Journals whose chain, numbering or contents no longer verify., Records git has seen change after the commit that created them. The chain makes… (+4 more)

### Community 19 - "advance"
Cohesion: 0.13
Nodes (17): Consequences, The delivery receipt attests the tree minus the journal, Consequences, SEEN-086 is the bootstrap ticket and has no journal, The five stages, Design decisions, phases_for(), Running and recording a verification command. A check is a real subprocess in… (+9 more)

### Community 20 - "stub"
Cohesion: 0.18
Nodes (6): AnswerTest, FallbackTest, QuestionTest, A transport shaped like the API: one request, a map of answers back., The API answers by level index; the record answers by option name., stub()

### Community 21 - "Seen: MVP architecture"
Cohesion: 0.20
Nodes (10): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen: MVP architecture, Services (+2 more)

### Community 22 - "Tickets"
Cohesion: 0.20
Nodes (10): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+2 more)

### Community 23 - "Seen: development harness"
Cohesion: 0.25
Nodes (8): Commands, KPIs, Principles, Repository layout, Security controls, Seen: development harness, Tickets, Why a harness

### Community 24 - "SEEN-086: Build the Seen harness CLI with staged journal and receipts"
Cohesion: 0.22
Nodes (9): Acceptance criteria, Blocks, Context, Depends on, Description, Not in this ticket, by design, Outcome, SEEN-086: Build the Seen harness CLI with staged journal and receipts (+1 more)

### Community 25 - "Seen: MVP development plan"
Cohesion: 0.25
Nodes (8): Day-0 checklist (human, before or during Sprint 0), Gates, Not in the MVP, Risks to the plan, Seen: MVP development plan, Shape of the plan, Sprint calendar, Team and capacity

### Community 26 - "SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Carried in from SEEN-087, Context, Depends on, Description, SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages

### Community 27 - ".run_harness"
Cohesion: 0.25
Nodes (4): AdvanceTest, clarify_evidence(), DraftTest, solution_evidence()

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

### Community 33 - "SEEN-007: Provision GCP europe-west4 and Supabase EU with telemetry"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-007: Provision GCP europe-west4 and Supabase EU with telemetry

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

### Community 113 - "test_lifecycle.py"
Cohesion: 0.18
Nodes (11): harness, The decision layer: typed questions, recorded with their probabilities. Jev…, Delivery: the stage gate that writes the receipt, and what it refuses., The self-check a session runs before it starts working., The graph command: a thin wrapper that records what graphify answered. The…, CommandTest, One ticket from start to delivered, through the commands a session runs., Runs commands in process, which is how the tests stay fast and readable. (+3 more)

### Community 115 - "Seen"
Cohesion: 0.33
Nodes (6): Development harness, Example dialogue, Flagged ambiguities, Language, Product, Seen

### Community 116 - "jev.py"
Cohesion: 0.09
Nodes (31): Decisions already taken for this stage and this attempt, latest per question., Every question this stage owns, answered once. An answer already recorded for…, recorded_decisions(), stage_decisions(), _answer_from_human(), ask(), _ask_api(), ask_many() (+23 more)

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 120 - "HarnessError"
Cohesion: 0.16
Nodes (12): Exception, lock(), An advisory lock, never broken automatically. Two sessions may share a…, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., Git access, and the fingerprint that decides whether evidence is still current., ClarifyGateTest (+4 more)

### Community 122 - "TransportTest"
Cohesion: 0.50
Nodes (3): The live transport, exercised without a network. Nothing here calls the API. It…, Cloudflare rejects Python's default user agent with error 1010. Without a user…, TransportTest

### Community 123 - "GateTest"
Cohesion: 0.14
Nodes (8): Tooling, GateTest, noul(), must_fix is the one question that refuses when it passes. clarified and…, score(), SecrecyTest, echoing(), transport()

### Community 124 - "delivery.py"
Cohesion: 0.27
Nodes (8): Read a stage evidence file, which must live where drafts live. Anywhere else it…, read_evidence(), _evidence(), Delivery: the deliver stage's own gate, and the receipt it writes. There is no…, Every record must already be in the history that was pushed. The receipt is the…, _require_committed(), verify(), The Seen development harness. One procedure per ticket, five stages, and an…

## Knowledge Gaps
- **528 isolated node(s):** `graphify-mcp`, `Ground rules`, `Tickets (93, 326 build points)`, `graphify`, `Product` (+523 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 659 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `require`, `.evaluate`, `.start`, `Repository`, `RecordTest`, `execute`, `DeliveryTest`, `GraphTest`, `journal.py`, `cli.py`, `doctor.py`, `advance`, `stub`, `.run_harness`, `test_lifecycle.py`, `DoctorTest`, `jev.py`, `GateTest`, `delivery.py`, `StatusTest`?**
  _High betweenness centrality (0.317) - this node is a cross-community bridge._
- **Why does `Seen: MVP architecture` connect `Seen: MVP architecture` to `CLAUDE.md`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `read_evidence()` connect `delivery.py` to `require`, `cli.py`, `advance`, `Seen: MVP architecture`, `HarnessError`?**
  _High betweenness centrality (0.196) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `HarnessError` (e.g. with `list_tickets()` and `main()`) actually correct?**
  _`HarnessError` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Repository` (e.g. with `HarnessError` and `DeliveryTest`) actually correct?**
  _`Repository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `execute()` (e.g. with `advance()` and `check()`) actually correct?**
  _`execute()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `Ground rules`, `Tickets (93, 326 build points)` to the rest of the system?**
  _528 weakly-connected nodes found - possible documentation gaps or missing edges._