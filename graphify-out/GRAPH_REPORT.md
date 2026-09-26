# Graph Report - seene  (2026-09-26)

## Corpus Check
- 1145 files · ~621,538 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 5, .toml 5, .example 1)

## Summary
- 3874 nodes · 7690 edges · 285 communities (250 shown, 35 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 261 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc08b013`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TriageTest
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
- .triage
- CoverageTest
- stub
- kpi.py
- Tickets
- package.json
- DeclaredSliceTest
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
- solution_evidence
- compilerOptions
- compilerOptions
- telemetry.ts
- SEEN-100: Let a gate tell an open question from an unknowable one
- Journal records are hashed as file bytes, and git is the notary
- SEEN-088: Integrate Jev AI typed decisions into the harness gates
- tasks
- DiscardTest
- The Seen harness
- routing.py
- agent/package.json
- connectors/package.json
- core/package.json
- api/package.json
- vitest
- api/tsconfig.json
- worker/tsconfig.json
- SEEN-007: Go live on Google Cloud after the go/no-go decision
- .start
- SEEN-089: Enforce the TDD gates in the harness
- SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain
- agent/tsconfig.json
- connectors/tsconfig.json
- core/tsconfig.json
- .measure
- SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports
- SEEN-099: Set the context budget and measure what the tools changed
- DoctorTest
- ClarifiedCriteriaTest
- next-env.d.ts
- NonCodeSolutionTest
- pull_request_template.md
- context.py
- pre-commit
- dependencies
- scripts
- SEEN-096: Add codegraph and route the graph command to it
- Week 39 of 2026
- Sprint 0: 37 of 81 points delivered
- Outcome
- providers/package.json
- handoff.py
- FocusSetTest
- providers/src/index.ts
- SEEN-098: Add repowise and carry its risk answer into the gate
- postmark.ts
- Seen: development harness
- BudgetRulesTest
- journal
- SEEN-102: Decide on the repowise PR bot for a private repository
- SyncTest
- ComparisonTest
- advance
- health.controller.ts
- outbound.ts
- HarnessError
- api/nest-cli.json
- worker/nest-cli.json
- calibration.py
- OverlapTest
- .advance_review
- Seen
- triage.py
- .journal
- AgentSyncTest
- ToolCallsTest
- providers/tsconfig.json
- devDependencies
- record
- MarketplaceHostTest
- Seen
- SEEN-093: Add harness reopen to void a receipt before merge
- PostmarkController
- hello.ts
- Seen: Claude Code entry point
- PartlySettledIsDocumentedTest
- .reach_tdd
- dev-down.sh
- dev-up.sh
- replay-inbound.sh
- tunnel.sh
- RepositoryTest
- RedRuleTest
- SidechainTokensTest
- checks.py
- ModesMustAgreeTest
- TheSkillSaysSoTest
- SEEN-094: Verify delivery against CI and verify the merge against the receipt
- SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack
- .journal
- SEEN-106: Enforce the harness with hooks in both assistants, generated from one source
- Outcome
- SEEN-103: Declare non-code mode at the solution stage, not after it
- .plant
- agents.py
- jev.py
- gates.py
- TheSkillSaysSoTest
- route_stub
- SessionEnvironment
- Seen: MVP architecture
- github.py
- noul
- .rendered
- DeclaredModelTest
- MergeTest
- SEEN-095: Check a ticket's status against its own journal
- DeliverStatusTest
- escapes
- AuthorshipTest
- ExecutionFiguresTest
- The reviewer
- The reviewer
- The scout
- The scout
- SessionDigestTest
- CachedFiguresTest
- SessionThresholdTest
- SEEN-107: Let Jev settle what the review can settle before a model reads the diff
- SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second
- Outcome
- .reach_tdd
- AgentDefinitionTest
- GateTest
- RenamedTicketTest
- .task
- .evidence
- FifthReviewTest
- CostPerPointByModelTest
- ThirdReviewTest
- execution
- OutcomeReconcilesTest
- PartialAnswerTest
- clarify_evidence
- render
- SprintReportCostTest
- ReworkWindowTest
- RiskInTheDecisionTest
- DirectoryNamedSliceTest
- ImplementerCopyTest
- EveryAttemptsEvidenceTest
- ReportTest
- FourthReviewTest
- GuardIsLastTest
- SkillAgreesWithItselfTest
- RouteInTheSkillTest
- TemplatePositionTest
- The implementer
- The implementer
- SixthReviewTest
- test_routing.py
- PricedPointsCellTest
- IntegerCentsTest
- DeclarationIsInstructedTest
- AgentCountTest
- SlicePositionTest
- BudgetTest
- render
- make_project
- record
- ReceiptAttestsTheReviewedTreeTest
- The Seen harness
- The Seen harness
- SEEN-101: Let a journal survive its ticket being renamed
- ticket_evidence
- FindingFileTest
- .test_the_delivered_file_carries_a_cost_for_each_routed_slice
- The calibration window
- plant
- ._history_paths
- IsolationTest
- LintExemptionTest

## God Nodes (most connected - your core abstractions)
1. `HarnessError` - 125 edges
2. `require()` - 91 edges
3. `Repository` - 79 edges
4. `CommandTest` - 64 edges
5. `solution_evidence()` - 55 edges
6. `clarify_evidence()` - 53 edges
7. `execute()` - 37 edges
8. `journal()` - 35 edges
9. `route_stub()` - 33 edges
10. `finding()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-100-let-a-gate-tell-an-open-question-from-an.md → harness/cli.py
- `Description` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py
- `Outcome` --references--> `state_for()`  [INFERRED]
  docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md → harness/cli.py
- `The wall the procedure itself hit, and the attempt that was withdrawn` --references--> `ticket_file()`  [INFERRED]
  docs/tickets/SEEN-109-calibrate-the-review-triage-and-the-routes-on.md → harness/cli.py
- `Agent runtime and the policy gate` --references--> `read_evidence()`  [INFERRED]
  docs/architecture.md → harness/cli.py

## Import Cycles
- None detected.

## Communities (285 total, 35 thin omitted)

### Community 0 - "TriageTest"
Cohesion: 0.11
Nodes (11): The triage's own return names what it could see no evidence for. Without the…, TriageReturnTest, DepthByRuleTest, GeneratedCopiesTest, A coverage check, written straight into the journal. The real command runs…, The three rules that are never Jev's to answer., A ticket worked to the review stage, with one file changed on the branch., Everything up to the review stage, with the checks a triage reads. (+3 more)

### Community 1 - ".evaluate"
Cohesion: 0.06
Nodes (27): advance_record(), check_record(), coverage_record(), GateTest, NonCodeGateTest, PlaceholderShapeTest, F8: shaping the template must not stop guarding the fields it kept., A recorded check. A red fails by default, because a red that passed is not one. (+19 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (28): metadata, config, dependencies, next, react, react-dom, @seen/core, description (+20 more)

### Community 3 - "Repository"
Cohesion: 0.06
Nodes (20): What the ninth review found, and passed, Every file in the project that git can see, ignored files excluded., The branch work merges into, asked of git rather than assumed., The working copy a harness command operates on., Whether a commit has already merged, locally or on the remote. Both are asked:…, Whether the remote already holds this commit as the tip of this branch., Refuse to operate from a subdirectory or from another repository., The branch, or None on a detached HEAD. Reporting commands use this, so… (+12 more)

### Community 6 - "boundary.ts"
Cohesion: 0.16
Nodes (18): Three defects the tests could not see, CLOUD_SDK_PREFIXES, CloudSdkImport, EXEMPT, findCloudSdkImports(), isCloudSdk(), SEARCHED, SKIP_DIRECTORIES (+10 more)

### Community 8 - "cli.py"
Cohesion: 0.04
Nodes (96): argparse, Run one check and return the evidence to record. `declared` is the tier the…, run(), brief(), budget(), build_pack(), build_parser(), check() (+88 more)

### Community 9 - "DeliveryWalk"
Cohesion: 0.24
Nodes (5): DeliveryTest, DeliveryWalk, The walk to a delivered ticket, without the tests. Separated so other files can…, No test reaches GitHub. Green by default; a test that cares says otherwise., Take a ticket through every stage, with real recorded checks. `mark_reviewed`…

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
Cohesion: 0.22
Nodes (9): Acceptance criteria, Amended after delivery, Blocks, Clarified, Context, Depends on, Description, Outcome (+1 more)

### Community 15 - "worker/package.json"
Cohesion: 0.08
Nodes (23): dependencies, bullmq, ioredis, @seen/core, @seen/providers, description, devDependencies, @nestjs/cli (+15 more)

### Community 16 - ".stub_repowise"
Cohesion: 0.16
Nodes (7): ElidedBlastRadiusTest, repowise elides a large payload and leaves a marker in its place. Observed at…, One file is four arguments: --target X --changed-file X., repowise's own marker already says how to restore it., The half of the ticket that is about tests rather than about size., The harness must work on a machine that has never heard of repowise., RiskTest

### Community 17 - "Seen: product requirements (MVP)"
Cohesion: 0.11
Nodes (18): 10. Pricing and metering, 11. Data, security and compliance, 12. Non-functional requirements, 13. Success metrics and gates, 14. Release plan, 15. Risks, 16. Open questions, 17. Glossary (+10 more)

### Community 18 - ".triage"
Cohesion: 0.06
Nodes (23): AlwaysReadTest, AnswersTest, AskedHonestlyTest, ChangedFilesTest, DeterministicPassTest, OneRequestTest, PartlySettledTest, H1: the two things a review is against are never in a focus set. The journal… (+15 more)

### Community 19 - "CoverageTest"
Cohesion: 0.38
Nodes (3): CoverageTest, Coverage on packages/core, measured by one fixed command and never allowed to…, The shape vitest's json-summary reporter writes.

### Community 20 - "stub"
Cohesion: 0.07
Nodes (18): AnswerTest, FallbackTest, GateTest, OverrideTest, QuestionTest, A transport failure is not fatal: it becomes a question for a person. The…, The live transport, exercised without a network. Nothing here calls the API. It…, Cloudflare rejects Python's default user agent with error 1010. Without a user… (+10 more)

### Community 21 - "kpi.py"
Cohesion: 0.11
Nodes (27): datetime, _check(), coverage(), first_pass_ci(), _latest_triage(), measure(), _moment(), output_tokens_per_slice() (+19 more)

### Community 22 - "Tickets"
Cohesion: 0.20
Nodes (10): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+2 more)

### Community 23 - "package.json"
Cohesion: 0.06
Nodes (33): devDependencies, eslint, @eslint/js, turbo, @types/node, typescript, typescript-eslint, vitest (+25 more)

### Community 24 - "DeclaredSliceTest"
Cohesion: 0.07
Nodes (18): AtTddTest, DeclaredSliceTest, HandoffPackTest, PackEdgesTest, A journal standing where a slice boundary happens: tdd, with a plan., A green check, recorded the way a slice ends., The only thing that crosses a slice boundary., Who says a slice is done. The pack counts greens, which is right until a slice… (+10 more)

### Community 25 - "Seen: MVP development plan"
Cohesion: 0.25
Nodes (8): Day-0 checklist (human, before or during Sprint 0), Gates, Not in the MVP, Risks to the plan, Seen: MVP development plan, Shape of the plan, Sprint calendar, Team and capacity

### Community 26 - "SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Carried in from SEEN-087, Context, Depends on, Description, Outcome, SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages

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
Cohesion: 0.11
Nodes (15): Acceptance criteria, Blocks, Context, Depends on, Description, Design decisions, Not in this ticket, by design, Outcome (+7 more)

### Community 34 - "SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table, Slices

### Community 35 - "SEEN-009: Define connector interface, capability matrix and credential access"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-009: Define connector interface, capability matrix and credential access, Slices

### Community 36 - "SEEN-010: Add per-marketplace rate limiting with header-driven backoff"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-010: Add per-marketplace rate limiting with header-driven backoff

### Community 37 - "SEEN-011: Build Bol Retailer API v10 connector for orders to commissions"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-011: Build Bol Retailer API v10 connector for orders to commissions, Slices

### Community 38 - "SEEN-012: Build eBay connector for orders, returns, transactions and payouts"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-012: Build eBay connector for orders, returns, transactions and payouts, Slices

### Community 39 - "SEEN-013: Build Amazon SP-API connector for orders, reports and Finances"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-013: Build Amazon SP-API connector for orders, reports and Finances, Slices

### Community 40 - "SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-014: Run ingest workers with idempotent upserts, raw archive and cadences, Slices

### Community 41 - "SEEN-015: Verify Amazon report names and Finances transactions version"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-015: Verify Amazon report names and Finances transactions version

### Community 42 - "SEEN-016: Encode fee schedules per marketplace and category in core"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-016: Encode fee schedules per marketplace and category in core

### Community 43 - "SEEN-017: Compute fee_expectations per order line from schedules and APIs"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-017: Compute fee_expectations per order line from schedules and APIs, Slices

### Community 44 - "SEEN-018: Match settlement_lines to order_lines deterministically"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-018: Match settlement_lines to order_lines deterministically, Slices

### Community 45 - "SEEN-019: Implement fee detectors as pure tested functions"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-019: Implement fee detectors as pure tested functions, Slices

### Community 46 - "SEEN-020: Implement shipment, return and inventory detectors"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-020: Implement shipment, return and inventory detectors, Slices

### Community 47 - "SEEN-021: Persist findings with rule, confidence, evidence refs and deadline"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-021: Persist findings with rule, confidence, evidence refs and deadline

### Community 48 - "SEEN-022: Generate the audit PDF with scorecard and line annex"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-022: Generate the audit PDF with scorecard and line annex, Slices

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
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-027: Build the claims rail with api, assisted and track modes, Slices

### Community 54 - "SEEN-028: Contest eBay payment disputes and cases by API"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-028: Contest eBay payment disputes and cases by API, Slices

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
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-033: Implement policy gate v1 with caps and reversibility, Slices

### Community 60 - "SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-034: Build agent runtime v1 with the fixed tool set and cost accounting, Slices

### Community 61 - "SEEN-035: Build the approval inbox with approve, edit and reject"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-035: Build the approval inbox with approve, edit and reject, Slices

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

### Community 112 - "solution_evidence"
Cohesion: 0.17
Nodes (8): solution_evidence(), NonCodeSlicePlanTest, plan(), A ticket with no behaviour to prove plans no slices. Its own class because a…, A slice plan of the shape the solution record carries., What the solution gate does with the plan it is now given., A plan may disagree with the estimate; the gate says so and proceeds. The caps…, SlicePlanTest

### Community 113 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, declaration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, forceConsistentCasingInFileNames (+15 more)

### Community 114 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowJs, baseUrl, incremental, isolatedModules, jsx, lib, module (+6 more)

### Community 115 - "telemetry.ts"
Cohesion: 0.24
Nodes (11): sha256(), consoleTelemetryProvider(), createTelemetryProvider(), nowUnixNano(), otlpAttributes(), otlpTelemetryProvider(), otlpTracesPayload(), otlpValue() (+3 more)

### Community 116 - "SEEN-100: Let a gate tell an open question from an unknowable one"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-100: Let a gate tell an open question from an unknowable one

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 119 - "tasks"
Cohesion: 0.13
Nodes (14): dependsOn, outputs, cache, persistent, dependsOn, $schema, tasks, build (+6 more)

### Community 120 - "DiscardTest"
Cohesion: 0.08
Nodes (14): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers, DiscardTest (+6 more)

### Community 121 - "The Seen harness"
Cohesion: 0.29
Nodes (6): Asking the graphs, The context budget, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 122 - "routing.py"
Cohesion: 0.07
Nodes (44): fnmatch, implementer_default(), The model and effort the implementer's copies carry, which never vary. The…, Work that trips a routing rule was routed by that rule, or it is refused. The…, _require_the_work_trips_no_unrouted_rule(), _decision(), _excerpt(), for_slice() (+36 more)

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
Cohesion: 0.20
Nodes (3): packageName, packageName, vitest

### Community 128 - "api/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 129 - "worker/tsconfig.json"
Cohesion: 0.22
Nodes (8): compilerOptions, baseUrl, outDir, rootDir, exclude, extends, include, ../../tsconfig.base.json

### Community 130 - "SEEN-007: Go live on Google Cloud after the go/no-go decision"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-007: Go live on Google Cloud after the go/no-go decision, Slices

### Community 131 - ".start"
Cohesion: 0.12
Nodes (6): BranchTest, DraftTest, NoteAndCheckTest, ReturnTest, StartTest, StatusTest

### Community 132 - "SEEN-089: Enforce the TDD gates in the harness"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Context, Depends on, Description, Moved to SEEN-094, Outcome, SEEN-089: Enforce the TDD gates in the harness

### Community 133 - "SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Carried in from SEEN-006 and SEEN-089, Carried in from SEEN-094, Context, Depends on, Description, SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain

### Community 134 - "agent/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 135 - "connectors/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 136 - "core/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 137 - ".measure"
Cohesion: 0.10
Nodes (11): journal_with_a_return(), LastSliceTest, Slices, sessions and what a slice cost, from the journal and nothing else., Null, not one: a record without a session cannot say it was the same one., A returned ticket proved slices in each attempt, and paid for each. Reading…, Null rather than zero: nothing was cut badly, there was nothing to cut., Rework is time spent, so tdd counts both visits rather than the last., F3: the slice no handoff follows. A handoff is written at a boundary, and the… (+3 more)

### Community 138 - "SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports, What the first report says

### Community 139 - "SEEN-099: Set the context budget and measure what the tools changed"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-099: Set the context budget and measure what the tools changed

### Community 140 - "DoctorTest"
Cohesion: 0.18
Nodes (3): AppendOnlyScopeTest, DoctorTest, Records are append-only. The files beside them are not records.

### Community 141 - "ClarifiedCriteriaTest"
Cohesion: 0.13
Nodes (6): ClarifiedCriteriaTest, Naming an unknown used to read as leaving it open, three times over., Unresolved is not enough: nothing said about what would resolve it., SEEN-100's guard, which is that none of the seven is lost. It was written as an…, SEEN-107's four, which no stage advance may start asking.…, The other calibrated question, unchanged by this one.

### Community 143 - "NonCodeSolutionTest"
Cohesion: 0.21
Nodes (6): NonCodeSolutionTest, The hole SEEN-102 fell into, closed., The guard: this must not become a way round the gate., The template asks, so a record that does not answer is not finished., Nine solution records are already written without it, and stay valid., Absent is not the same as a record that said nothing.

### Community 144 - "pull_request_template.md"
Cohesion: 0.29
Nodes (6): Acceptance criteria, Evidence, Limits, Receipt, Review findings, Summary

### Community 145 - "context.py"
Cohesion: 0.15
Nodes (16): compare(), cost_by_model(), overlaps(), _per_point(), _per_slice(), qualifying(), Whether three knowledge tools paid for the context they occupy. codegraph,…, Tickets started after both tools existed, with figures to compare. A ticket… (+8 more)

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

### Community 152 - "Outcome"
Cohesion: 0.10
Nodes (14): Repository layout, Acceptance criteria, Blocks, Context, Depends on, Description, Known and deliberately left, Outcome (+6 more)

### Community 153 - "providers/package.json"
Cohesion: 0.11
Nodes (17): dependencies, @supabase/supabase-js, description, devDependencies, @vitest/coverage-v8, @vitest/coverage-v8, main, name (+9 more)

### Community 154 - "handoff.py"
Cohesion: 0.10
Nodes (28): Known and deliberately left, Outcome, accepted_greens(), current_slice(), _decisions(), estimate_tokens(), _graph_answers(), _heading() (+20 more)

### Community 155 - "FocusSetTest"
Cohesion: 0.11
Nodes (12): FocusSetTest, transport(), G1: a judgement nobody made must not take a file out of a review., The reviewer's model is a rule, and the depth is what decides it. A full review…, What the reviewer is asked to read, and what shadow mode does to it., A stub asking for a spot review of one file out of the three., Pass three is text: the task the session hands its subagent., Asserted on the diff section, which is the part `no others` governs. The ticket… (+4 more)

### Community 156 - "providers/src/index.ts"
Cohesion: 0.19
Nodes (21): createSecretsProvider(), environmentVariableFor(), envSecretsProvider(), SECRETS_PROVIDERS, SecretsProviderName, Environment, notUntilGoLive(), ProviderConfigurationError (+13 more)

### Community 157 - "SEEN-098: Add repowise and carry its risk answer into the gate"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-098: Add repowise and carry its risk answer into the gate

### Community 158 - "postmark.ts"
Cohesion: 0.22
Nodes (12): header(), isPostmarkInbound(), MARKETPLACE_DOMAINS, marketplaceOf(), normaliseSubject(), PostmarkInbound, tenantOf(), threadKey() (+4 more)

### Community 159 - "Seen: development harness"
Cohesion: 0.12
Nodes (17): Commands, Jev before the model: the review triage and the route, KPIs, Principles, Security controls, Seen: development harness, The context per session, The five stages (+9 more)

### Community 160 - "BudgetRulesTest"
Cohesion: 0.22
Nodes (3): BudgetRulesTest, A rule in a prompt is not a rule., A date would count the tickets that installed them, which it must not.

### Community 161 - "journal"
Cohesion: 0.10
Nodes (16): EscapeTest, finding(), journal(), What counts as an escape, and what the rule refuses to count either way., The triage said so itself and returned the ticket; it missed nothing., F4 of the first review: nothing requires the flag, so a forgotten one would…, F1 of the first review: lstrip strips characters, not a prefix., Nothing repository-relative can be compared with it, so it is placed nowhere. (+8 more)

### Community 162 - "SEEN-102: Decide on the repowise PR bot for a private repository"
Cohesion: 0.17
Nodes (12): A note on how it got here, Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-102: Decide on the repowise PR bot for a private repository (+4 more)

### Community 164 - "ComparisonTest"
Cohesion: 0.16
Nodes (4): ComparisonTest, What the report says about the figures, and when it refuses to say it., G4: SEEN-098's own rule, applied to the agents this time., Two numbers divided is not evidence when there are two tickets.

### Community 165 - "advance"
Cohesion: 0.06
Nodes (37): Six rules you cannot infer, The five stages, Six rules you cannot infer, The five stages, Consequences, SEEN-086 is the bootstrap ticket and has no journal, Six rules you cannot infer, The five stages (+29 more)

### Community 166 - "health.controller.ts"
Cohesion: 0.29
Nodes (6): HealthController, Controller, Get, LEDGER_CURRENCY, packageName, sumCents()

### Community 167 - "outbound.ts"
Cohesion: 0.20
Nodes (8): Environment, mailpit(), MailpitMessage, createMailer(), Environment, Mailer, OutboundMail, nodemailer

### Community 168 - "HarnessError"
Cohesion: 0.06
Nodes (62): Exception, harness, Tokens spent on a ticket, read from the session logs. Only four numbers are…, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., The append-only journal: one directory of numbered records per ticket. Each…, Git access, and the fingerprint that decides whether evidence is still current.… (+54 more)

### Community 169 - "api/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 170 - "worker/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 171 - "calibration.py"
Cohesion: 0.05
Nodes (62): effective_shadow(), evidence(), _excluded_reason(), journals(), What the triage and the routes actually cost, read from the journals.…, Every ticket's records, by ticket id, and what could not be read. A journal…, Why this ticket is not in the window, or nothing when it is., Go-live or stay-shadow for the triage, by the rule and by nothing else. The… (+54 more)

### Community 172 - "OverlapTest"
Cohesion: 0.43
Nodes (3): OverlapTest, One question with two right addressees is one tool too many., Asking again is not redundancy between tools.

### Community 173 - ".advance_review"
Cohesion: 0.13
Nodes (9): FocusSetGateTest, G4: a ticket triaged once must not review a later attempt untriaged., A review record in the shape the gate demands, with what it read., The gate that makes the focus set worth computing., F4: the focus set is a floor, and a floor under a diff that has moved is none., The procedure writes it between the triage and the advance, every time., review_evidence(), StaleTriageTest (+1 more)

### Community 174 - "Seen"
Cohesion: 0.25
Nodes (8): Commands, Getting it running, If it will not start, Seen, Tests, The cloud is a configuration, What it costs to run, Where things run

### Community 175 - "triage.py"
Cohesion: 0.05
Nodes (74): Outcome, The ticket file as it stands now: the recorded path, or found by its id. A…, The ticket and where it came from: the path, the id, or the snapshot. Which…, ticket_file(), _ticket_text(), _acceptance_check(), always_read(), append() (+66 more)

### Community 176 - ".journal"
Cohesion: 0.12
Nodes (9): G3: the window is the reviewer's, and the rework between two is not., Where the scout runs, and from SEEN-108 the implementer subagent., M1 and M2: what a long ticket loses, and what it must not. The first cap kept…, One accepted tdd record per slice, each citing a red and a green., What kpi.json keeps of a triage, derived and never typed., N1: the field went in at attempt 10 with no test, found by mutation. The share…, ReviewWindowsTest, SliceCapTest (+1 more)

### Community 177 - "AgentSyncTest"
Cohesion: 0.06
Nodes (12): AgentSyncTest, ImplementerTest, F10: a file with no source under harness/agents/ has had no review. The name…, The guard the two above lost: drift must not be able to stand in for strays. A…, G7: .claude/agents/ belongs to the person; only the seen- names are ours., What comes back from a context of its own, and how small it has to be. A brief…, The one agent whose model and effort are not its own to choose. All three carry…, The first agent that does, because writing the slice is what it is for. (+4 more)

### Community 179 - "providers/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 180 - "devDependencies"
Cohesion: 0.33
Nodes (6): devDependencies, @nestjs/cli, @nestjs/testing, supertest, @types/nodemailer, @types/supertest

### Community 181 - "record"
Cohesion: 0.16
Nodes (13): at(), journal_with_a_route(), check(), handoff(), journal_with_rework(), A timestamp minutes after ten, so a journal can span an hour or more., Two slices, routed, each closed by its own handoff boundary. One session, so…, The same two-slice ticket, returned once and proved again. The shape F2 of the… (+5 more)

### Community 183 - "Seen"
Cohesion: 0.33
Nodes (6): Development harness, Example dialogue, Flagged ambiguities, Language, Product, Seen

### Community 184 - "SEEN-093: Add harness reopen to void a receipt before merge"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-093: Add harness reopen to void a receipt before merge

### Community 185 - "PostmarkController"
Cohesion: 0.40
Nodes (4): PostmarkController, Controller, Inject, Post

### Community 186 - "hello.ts"
Cohesion: 0.24
Nodes (8): connection, HELLO_QUEUE, HelloPayload, HelloResult, HelloWorker, startHelloWorker(), worker, bullmq

### Community 187 - "Seen: Claude Code entry point"
Cohesion: 0.33
Nodes (6): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (109, 353 build points), Working a ticket

### Community 189 - ".reach_tdd"
Cohesion: 0.16
Nodes (7): JevTest, What no model is asked about, and why each one is a rule., What the model is asked, and what is done with what comes back., The record itself: where it may be written and what it names., Both planning gates passed, with the stage requests forgotten. The gates ask…, RecordTest, RulesTest

### Community 196 - "SidechainTokensTest"
Cohesion: 0.20
Nodes (6): DeliveredFiguresTest, walk_to_review(), One subagent entry inside the window, and one before it that is not., The reviewer's own cost, read from the log rather than declared., F3 of the second review: criterion 5 names kpi.json, and delivery writes it. G2…, SidechainTokensTest

### Community 197 - "checks.py"
Cohesion: 0.10
Nodes (24): demonstrates_failure(), phases_for(), Running and recording a verification command. A check is a real subprocess in…, Whether a run is evidence that a test failed. Exit zero is a passing command,…, cited_check(), A check a stage record points at, confirmed to be usable evidence here. A check…, record_at(), ask() (+16 more)

### Community 198 - "ModesMustAgreeTest"
Cohesion: 0.43
Nodes (3): ModesMustAgreeTest, A ticket that plans no tests and then records a code TDD changed its mind., With a well-formed slice, so it is the disagreement that refuses.

### Community 200 - "SEEN-094: Verify delivery against CI and verify the merge against the receipt"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-094: Verify delivery against CI and verify the merge against the receipt

### Community 201 - "SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack

### Community 202 - ".journal"
Cohesion: 0.14
Nodes (6): A review re-run lists its findings again; they are still the same findings., Whether a ticket was worked with the scout and the reviewer, from its journal.…, F4: the report row is about the scout and the reviewer, not either one., Nineteen journals were written before either agent existed., RepeatedReviewTest, SubagentAttributionTest

### Community 203 - "SEEN-106: Enforce the harness with hooks in both assistants, generated from one source"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-106: Enforce the harness with hooks in both assistants, generated from one source

### Community 204 - "Outcome"
Cohesion: 0.10
Nodes (20): How the harness meets the assistants, Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, Outcome (+12 more)

### Community 205 - "SEEN-103: Declare non-code mode at the solution stage, not after it"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-103: Declare non-code mode at the solution stage, not after it

### Community 206 - ".plant"
Cohesion: 0.10
Nodes (7): EffectiveShadowTest, GoLiveDecisionTest, Which tickets the window counts, and which it names as excluded and why., The one question a triage asks: which shadow am I in, and what put me there., The switch and the decision it names, which is what going live takes., F3: going live must name the record the decision is in, or it is an edit., WindowTest

### Community 207 - "agents.py"
Cohesion: 0.17
Nodes (21): _body(), claude_copy(), codex_copy(), drift(), _folded(), Three agents with a context of their own, and the copies each assistant reads.…, Long prose as a folded scalar, the form the skill's own frontmatter uses., The markdown copy Claude Code reads, frontmatter first. Only the description is… (+13 more)

### Community 208 - "jev.py"
Cohesion: 0.06
Nodes (46): _latest_evidence(), What Jev is given to judge: the ticket, the stage and the record at hand. The…, Decisions already taken for this stage and this attempt, latest per question., Every question this stage owns, answered once. An answer already recorded for…, recorded_decisions(), stage_decisions(), state_for(), _answer_from_human() (+38 more)

### Community 209 - "gates.py"
Cohesion: 0.07
Nodes (49): Outcome, _evidence(), check_findings(), _clarify(), evaluate(), _filled(), for_mode(), _implementer_tools() (+41 more)

### Community 210 - "TheSkillSaysSoTest"
Cohesion: 0.12
Nodes (7): The one maintained skill, on the two agents a session may send work to., F11: the setting lives in a file this repository does not track., F9: Claude Code has no read-only Bash, so the hole is named, not implied., H5: the skill described the rule as it was before G3., H5: [actors] tools carries human, and the gate reads [actors] assistants., H6: F5 widened this from the current attempt to every attempt., TheSkillSaysSoTest

### Community 211 - "route_stub"
Cohesion: 0.19
Nodes (10): FixedCopiesTest, A transport answering the two route questions, keyed by slice position.…, F5: a route that did not clear its own threshold says so., A ticket worked to the tdd stage, which is where the route is decided., The copies say the same thing whatever the ticket is doing. Generated per…, Which is what actions/checkout gives on every pull_request event., The state F3 of the eighth review found: no slice is in hand at all., route_stub() (+2 more)

### Community 212 - "SessionEnvironment"
Cohesion: 0.12
Nodes (8): NoPlanYetTest, Which session wrote a record, without saying what the session is called., No session id is an absence, not a claim that there was one session., Tests that decide for themselves which session they are running in. The harness…, A pack before the solution record has advanced names no slice., SessionEnvironment, SessionOnEveryRecordTest, SessionUnknownTest

### Community 213 - "Seen: MVP architecture"
Cohesion: 0.10
Nodes (21): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen: MVP architecture, Services (+13 more)

### Community 214 - "github.py"
Cohesion: 0.28
Nodes (8): check_runs(), _gh(), latest_per_name(), pull_request(), What GitHub says about a commit and its pull request. Two readers and nothing…, Every check GitHub has run for one commit, with its status and conclusion., The pull request for the current branch, or a refusal when there is none., One run per check name, the most recent. A commit can carry several runs of the…

### Community 215 - "noul"
Cohesion: 0.11
Nodes (18): Tooling, noul(), score(), transport(), transport(), FailedCheckStillAsksTest, low_on_the_second(), J1: only the three rules silence the request; a failed check does not. Pass one… (+10 more)

### Community 216 - ".rendered"
Cohesion: 0.13
Nodes (8): ForwardReferenceTest, F5 of SEEN-108's third review: what the printed report tells a reader to run.…, The direction this guards now: a report never sends a reader to nothing., F1 of the fifth review: a row nothing could price must still render. The fourth…, The shape that raised: one unpriced row beside one priced row., F2 of the sixth review: a row a reader can check. Points is every point the…, ReconcilingRowTest, UnpricedRowTest

### Community 217 - "DeclaredModelTest"
Cohesion: 0.27
Nodes (3): DeclaredModelTest, What a subagent can say about itself, because the log cannot say it. A Claude…, The subagent ran on the routed model; the log says the parent's.

### Community 218 - "MergeTest"
Cohesion: 0.08
Nodes (10): BookkeepingAfterReceiptTest, DeliveryChecksTest, broken(), MergeTest, A commit can carry more than one run of the same check. GitHub shows the latest…, What delivery itself writes may follow the receipt; nothing else may., Check runs in the shape gh reports them., The week includes the ticket that just delivered, so the report moves. (+2 more)

### Community 219 - "SEEN-095: Check a ticket's status against its own journal"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-095: Check a ticket's status against its own journal

### Community 221 - "escapes"
Cohesion: 0.13
Nodes (22): What the review found, What the second review found, _covers(), escapes(), finding_key(), latest_finding_records(), latest_findings(), normalise() (+14 more)

### Community 223 - "ExecutionFiguresTest"
Cohesion: 0.12
Nodes (6): ExecutionFiguresTest, journal_worked_in_two_sessions(), Two slices planned, two proved, and two sessions that wrote the records., What each slice was routed to, what it ran on, and what it cost. From the…, Keyed by `done` and not `position`. A handoff names the slice in front of you,…, In shadow a slice runs on the session's model, whatever it was routed to.…

### Community 224 - "The reviewer"
Cohesion: 0.40
Nodes (4): The reviewer, What to look for, What to read, What to return

### Community 225 - "The reviewer"
Cohesion: 0.40
Nodes (4): The reviewer, What to look for, What to read, What to return

### Community 226 - "The scout"
Cohesion: 0.50
Nodes (3): How to answer, The scout, What to return

### Community 227 - "The scout"
Cohesion: 0.50
Nodes (3): How to answer, The scout, What to return

### Community 229 - "CachedFiguresTest"
Cohesion: 0.40
Nodes (3): CachedFiguresTest, What the kpi.json beside a receipt claims to be., SEEN-099's rule, which SEEN-107 narrowed by one figure rather than broke.…

### Community 231 - "SEEN-107: Let Jev settle what the review can settle before a model reads the diff"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-107: Let Jev settle what the review can settle before a model reads the diff

### Community 232 - "SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second"
Cohesion: 0.20
Nodes (10): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, Outcome, SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second (+2 more)

### Community 233 - "Outcome"
Cohesion: 0.10
Nodes (21): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token, The wall the procedure itself hit, and the attempt that was withdrawn (+13 more)

### Community 234 - ".reach_tdd"
Cohesion: 0.16
Nodes (6): F3 of the first review: the flag the second escape kind is read from., A review that returns a ticket records what it found, or the window cannot read…, F1: a return from review says what it found, or says it found nothing., ReturningFindingsTest, ReviewReturnDeclarationTest, UnmetCriteriaTest

### Community 235 - "AgentDefinitionTest"
Cohesion: 0.29
Nodes (3): AgentDefinitionTest, What each agent is allowed to do, which is the point of separating them., The scout and the reviewer read and nothing else. SEEN-105 could say this of…

### Community 236 - "GateTest"
Cohesion: 0.22
Nodes (5): GateTest, A check recorded under a model the route did not choose. Refused only with…, The one line in the project's own thresholds, and only that line. Written…, A check, recorded under a model, which is what a session log gives. The tests…, One slice proved red then green, both recorded under one model.

### Community 238 - ".task"
Cohesion: 0.16
Nodes (5): CarriedNotAppliedTest, A route is read only for the plan it routed. The record names the solution…, Back to solution, a different plan accepted, and no new route., What the spawn instruction may promise about the effort, which is nothing. F1…, StalePlanTest

### Community 239 - ".evidence"
Cohesion: 0.22
Nodes (6): PositionIsDeclaredTest, F3 of the ninth review: a rule a plan can miss by not naming a file. The rules…, Checks that declare the routed model, so the rule is what is under test.…, F2 of the fifth review: the route comparison is not skipped by omission. The…, A rework round spanning slices belongs to none of them, and says null., RuleTrippedByTheWorkTest

### Community 240 - "FifthReviewTest"
Cohesion: 0.11
Nodes (7): FifthReviewTest, The downgraded slices against the rest, on the charges the rule names., The findings of the fifth review, at note 56., A ticket whose blocking finding lands in a file no slice named., F1: nothing says which slice caused it, which is what route_rule already says…, RouteVerdictTest, slice_entry()

### Community 241 - "CostPerPointByModelTest"
Cohesion: 0.21
Nodes (4): CostPerPointByModelTest, What a point cost on each model, beside the tokens per point. The point of the…, In shadow those differ, and only one of them cost anything., F3: dividing a partial cost by every point understates the model. On SEEN-108's…

### Community 242 - "ThirdReviewTest"
Cohesion: 0.13
Nodes (8): Go-live or stay-shadow for the triage, stated by the rule and not by a reading., The ticket's another ten: ten clean tickets after the escape., The findings of the third review, at note 36., F1: counted neither way must mean the verdict waits, not that it passes., F4: a founder auditing the decision must recompute over the same list., F6: a stray file in one journal must not block every other review., ThirdReviewTest, TriageVerdictTest

### Community 243 - "execution"
Cohesion: 0.17
Nodes (12): _closes(), cost_cents(), execution(), _latest_route(), Each slice's window: what it cost and which records fall inside it. Keyed by…, Which slice this record's boundary closed, and the figures it carried. A…, What those output tokens cost on that model, or that nobody priced it. A whole…, What each slice was routed to, what it ran on and what it cost. Null rather… (+4 more)

### Community 244 - "OutcomeReconcilesTest"
Cohesion: 0.36
Nodes (3): OutcomeReconcilesTest, The Outcome's findings against the journal that is supposed to supply them. F4…, Every reviewer note, in the order they were written.

### Community 245 - "PartialAnswerTest"
Cohesion: 0.27
Nodes (5): PartialAnswerTest, transport(), drops_clarified(), F1: a reply that left one question out must not cost the rest. A transport…, The other half of must_answer: a stage needs a judgement.

### Community 246 - "clarify_evidence"
Cohesion: 0.16
Nodes (6): BaselineTest, NonCodeCoverageTest, A ticket with no behaviour to prove owes no coverage figure. Its own setUp…, The baseline moves only when a ticket delivers., AdvanceTest, clarify_evidence()

### Community 247 - "render"
Cohesion: 0.50
Nodes (4): drift(), One copy: the frontmatter an assistant reads, then the maintained body., Committed copies that do not match what the source would generate., render()

### Community 249 - "ReworkWindowTest"
Cohesion: 0.32
Nodes (4): F2 of the third review: what a rework round's tokens are charged to. Nothing,…, This fixture ends its plan at a handoff, so the advance has nothing left. The…, The slices do not carry it; the ticket's own token figure does., ReworkWindowTest

### Community 250 - "RiskInTheDecisionTest"
Cohesion: 0.32
Nodes (4): What the model sees when it is asked how risky this change is., Not as a low score, and not as silence., One extra payload string per question is not free: SEEN-101., RiskInTheDecisionTest

### Community 251 - "DirectoryNamedSliceTest"
Cohesion: 0.39
Nodes (3): DirectoryNamedSliceTest, A rule a plan's wording cannot dodge. F6 of the third review: the patterns were…, `packages/core-utils` is a different package, not money arithmetic.

### Community 253 - "EveryAttemptsEvidenceTest"
Cohesion: 0.32
Nodes (3): EveryAttemptsEvidenceTest, L1: a returned ticket proved slices in each attempt, and Jev sees them all.…, A return, then one more slice proved, the way rework goes.

### Community 254 - "ReportTest"
Cohesion: 0.19
Nodes (6): The evidence per ticket and per slice, with the rule printed beside it., F2 of the first review: the only test for this line exercised the branch that…, The one thing that happens without a person: the return to shadow., Go live the way the founder must: the switch and the decision it names., ReportTest, TriageShadowTest

### Community 255 - "FourthReviewTest"
Cohesion: 0.15
Nodes (8): FourthReviewTest, The findings of the fourth review, at note 46., F1: a reviewer writes a hunk, and the tail is not all digits., Not in would_exclude and not in the diff: placed nowhere, not placed outside., F2: the triage reads the verdict, which is what four documents say., A window that is not full is a reason to conclude nothing, not to override., F3: a declaration is a claim by its author, so the report says who made it., F4: the one-line instruction must not be able to come back quietly.

### Community 256 - "GuardIsLastTest"
Cohesion: 0.48
Nodes (3): GuardIsLastTest, A module's own run must collect its own tests. F3 of the sixth review: five…, The guard's line, found at column zero so a quotation is not one.

### Community 259 - "TemplatePositionTest"
Cohesion: 0.43
Nodes (3): F1 of the sixth review: what the template teaches about the position. Every…, The placeholder must not be a value the gate accepts., TemplatePositionTest

### Community 260 - "The implementer"
Cohesion: 0.33
Nodes (5): How you work, The implementer, What you are given, What you never do, What you return

### Community 261 - "The implementer"
Cohesion: 0.33
Nodes (5): How you work, The implementer, What you are given, What you never do, What you return

### Community 262 - "SixthReviewTest"
Cohesion: 0.20
Nodes (6): A round that returned a ticket on an open finding, and a round that passed., F1: the review gate refuses an advance carrying an unresolved finding, so a…, F2: membership, not the rate, is what says a group is empty., F4: two faults, two messages, so a reader fixes the right one., The findings of the sixth review, at note 65., SixthReviewTest

### Community 263 - "test_routing.py"
Cohesion: 0.24
Nodes (5): The route: which model and which effort implement each slice. Rules first, and…, F4: a route record that predates the fields the skill says it carries. The only…, What the session that picks up the next slice is told to run it on., RouteRecordIsCurrentTest, SliceBoundaryTest

### Community 268 - "SlicePositionTest"
Cohesion: 0.33
Nodes (5): Which route a proved slice is held to. F1 of the fourth review: the gate read…, One slice proved on its own, the way a rework attempt proves one., Slice 1 is Jev's haiku, slice 2 is the money rule's opus., A round that belongs to no single slice says so, and is held to no route. This…, SlicePositionTest

### Community 269 - "BudgetTest"
Cohesion: 0.38
Nodes (3): BudgetTest, What a session can be told about its own spending, and when it cannot., A session log of the shape the assistant writes, and nothing else.

### Community 270 - "render"
Cohesion: 0.20
Nodes (9): calibration_line(), _duration(), The context budget and what the figures say about it, or that they cannot. The…, What a point cost on each model, with the date the prices were read. Printed…, A report anyone can read without opening a journal. The last section names what…, One line for the weekly report: which shadow the triage is in, and why., render(), render_context() (+1 more)

### Community 271 - "make_project"
Cohesion: 0.25
Nodes (5): add_remote(), make_project(), No test calls the decision API, and none inherits a shell credential. A test…, A bare repository to push to, so delivery can be verified without a network., A git repository shaped like Seen: a ticket, the harness files, one commit.

### Community 272 - "record"
Cohesion: 0.25
Nodes (7): at(), A triage as SEEN-107 writes one: what it would have dropped, and its answers., F3: reopen voids the receipt, so the ticket is being worked again., record(), review_advance(), route_record(), triage_record()

### Community 273 - "ReceiptAttestsTheReviewedTreeTest"
Cohesion: 0.29
Nodes (3): What a receipt attests, and why attempt 8's exception was withdrawn. Attempt 8…, The order the procedure has to keep: the status goes in before the gate., ReceiptAttestsTheReviewedTreeTest

### Community 274 - "The Seen harness"
Cohesion: 0.29
Nodes (6): Asking the graphs, The context budget, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 275 - "The Seen harness"
Cohesion: 0.29
Nodes (6): Asking the graphs, The context budget, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 276 - "SEEN-101: Let a journal survive its ticket being renamed"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-101: Let a journal survive its ticket being renamed

### Community 277 - "ticket_evidence"
Cohesion: 0.29
Nodes (7): declared_empty(), latest_route(), latest_triage(), Every review return that declared it found nothing, and who declared it. A…, The route that routed the plan the work was done against. The same rule kpi…, One counted ticket's row: what the triage would have dropped, and what got…, ticket_evidence()

### Community 279 - ".test_the_delivered_file_carries_a_cost_for_each_routed_slice"
Cohesion: 0.40
Nodes (3): DeliveredCostTest, F2 of SEEN-108's second review: criterion 4 names kpi.json, and delivery writes…, A session log for this walk, because a cost without tokens is null. The name is…

### Community 280 - "The calibration window"
Cohesion: 0.40
Nodes (4): Not in the window, The calibration window, The routes, The triage

### Community 281 - "plant"
Cohesion: 0.50
Nodes (4): The one byte representation of a record. Never re-run on a written file., serialise(), plant(), Write a journal to disk, chained the way journal.append chains one.

## Knowledge Gaps
- **952 isolated node(s):** `graphify-mcp`, `repowise`, `$schema`, `collection`, `sourceRoot` (+947 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1814 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `TriageTest`, `.evaluate`, `Repository`, `.start`, `TemplatePositionTest`, `RecordTest`, `cli.py`, `DeliveryWalk`, `.graph`, `test_routing.py`, `DoctorTest`, `SlicePositionTest`, `NonCodeSolutionTest`, `ReceiptAttestsTheReviewedTreeTest`, `.triage`, `CoverageTest`, `stub`, `FindingFileTest`, `DeclaredSliceTest`, `StateForTest`, `StatusAgainstJournalTest`, `advance`, `calibration.py`, `.advance_review`, `triage.py`, `AgentSyncTest`, `.reach_tdd`, `RepositoryTest`, `RedRuleTest`, `checks.py`, `ModesMustAgreeTest`, `jev.py`, `gates.py`, `github.py`, `noul`, `DeclaredModelTest`, `MergeTest`, `.reach_tdd`, `GateTest`, `.evidence`, `solution_evidence`, `PartialAnswerTest`, `clarify_evidence`, `DiscardTest`?**
  _High betweenness centrality (0.203) - this node is a cross-community bridge._
- **Why does `Outcome` connect `Outcome` to `cli.py`, `app.module.ts`, `boundary.ts`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Why does `require()` connect `cli.py` to `Repository`, `advance`, `checks.py`, `handoff.py`, `HarnessError`, `calibration.py`, `triage.py`, `agents.py`, `gates.py`, `jev.py`, `github.py`, `Outcome`, `routing.py`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `HarnessError` (e.g. with `journals()` and `went_live_problem()`) actually correct?**
  _`HarnessError` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `Repository` (e.g. with `HarnessError` and `AgentSyncTest`) actually correct?**
  _`Repository` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `solution_evidence()` (e.g. with `Outcome` and `Outcome`) actually correct?**
  _`solution_evidence()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `repowise`, `$schema` to the rest of the system?**
  _952 weakly-connected nodes found - possible documentation gaps or missing edges._