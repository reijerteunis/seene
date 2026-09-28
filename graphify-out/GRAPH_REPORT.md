# Graph Report - seene  (2026-09-28)

## Corpus Check
- 1386 files · ~834,386 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 5, .toml 5, .example 1)

## Summary
- 4700 nodes · 9580 edges · 317 communities (277 shown, 40 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 312 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4e6a7560`
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
- .handoff
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
- state_for
- Journal records are hashed as file bytes, and git is the notary
- SEEN-088: Integrate Jev AI typed decisions into the harness gates
- tasks
- DiscardTest
- advance
- routing.py
- agent/package.json
- connectors/package.json
- core/package.json
- api/package.json
- vitest
- api/tsconfig.json
- worker/tsconfig.json
- SEEN-007: Go live on Google Cloud after the go/no-go decision
- CommandTest
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
- .at_tdd
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
- sessions.py
- health.controller.ts
- outbound.ts
- HarnessError
- api/nest-cli.json
- worker/nest-cli.json
- skills.py
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
- .refusal
- Seen
- SEEN-093: Add harness reopen to void a receipt before merge
- PostmarkController
- hello.ts
- .slice_three_writes_its_own_file
- hooks.py
- .reach_tdd
- dev-down.sh
- dev-up.sh
- replay-inbound.sh
- tunnel.sh
- HookSyncTest
- RedRuleTest
- SidechainTokensTest
- test_forecast.py
- GuardCommandTest
- TheSkillSaysSoTest
- SEEN-094: Verify delivery against CI and verify the merge against the receipt
- GateTest
- .journal
- SEEN-106: Enforce the harness with hooks in both assistants, generated from one source
- DescriptionSaysWhatIsNotAppliedTest
- SEEN-103: Declare non-code mode at the solution stage, not after it
- .plant
- agents.py
- jev.py
- require
- TheSkillSaysSoTest
- route_stub
- SessionEnvironment
- Seen: MVP architecture
- test_enforcement.py
- FailedCheckStillAsksTest
- .rendered
- DeclaredModelTest
- MergeTest
- SlicesProvedRatherThanGreensCounted
- TddGateTest
- calibration.py
- AuthorshipTest
- .commit
- The reviewer
- The reviewer
- The scout
- The scout
- SessionDigestTest
- CachedFiguresTest
- SessionThresholdTest
- Outcome
- SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second
- Outcome
- .reach_tdd
- AgentDefinitionTest
- .set_shadow
- RenamedTicketTest
- .task
- evidence
- FifthReviewTest
- CostPerPointByModelTest
- ThirdReviewTest
- doctor.py
- OutcomeReconcilesTest
- noul
- DecideTest
- delivery.py
- SprintReportCostTest
- CompactionWindowTest
- risk.py
- test_routing.py
- ARoundThatBelongsToNoSingleSlice
- .citing_all
- ReportTest
- FourthReviewTest
- checks.py
- SkillAgreesWithItselfTest
- RouteInTheSkillTest
- TemplatePositionTest
- The implementer
- The implementer
- SixthReviewTest
- SliceBoundaryTest
- PricedPointsCellTest
- IntegerCentsTest
- DeclaredSliceTest
- AgentCountTest
- TheRoundsOwnCommitSaysWhatItCovered
- BudgetTest
- run
- .git
- ExecutionFiguresTest
- ReceiptAttestsTheReviewedTreeTest
- SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants
- execution
- SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token
- ticket_evidence
- FindingFileTest
- SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined
- The calibration window
- ReopenTest
- RepositoryTest
- IsolationTest
- ReplanCarriesForward
- APairIsJudgedByItsGreen
- slice_windows
- SEEN-113: Let a tdd record cite the evidence a return did not invalidate
- forecast.py
- .evidence
- DirectoryNamedSliceTest
- UnevidencedCriterionTest
- Outcome
- SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide
- DeliverStatusTest
- ModesMustAgreeTest
- ReworkIsToldWhatItRunsOn
- guard.py
- .test_the_delivered_file_carries_a_cost_for_each_routed_slice
- ReportTest
- SEEN-086: Build the Seen harness CLI with staged journal and receipts
- _stage_of
- PackEdgesTest
- _field
- TheDisclosureNamesWhatARedIsHeldTo
- record
- file_facts
- DispatcherShapeTest
- GeneratedCopiesTest
- MarketplaceHostTest
- QuietCheckTest
- ReworkAfterAReplanDoesNotAdvanceTheCount
- append
- why_not
- LintExemptionTest
- DraftAsksTheGateTest
- PartlySettledIsDocumentedTest

## God Nodes (most connected - your core abstractions)
1. `HarnessError` - 145 edges
2. `require()` - 101 edges
3. `Repository` - 87 edges
4. `CommandTest` - 71 edges
5. `clarify_evidence()` - 64 edges
6. `solution_evidence()` - 63 edges
7. `execute()` - 41 edges
8. `route_stub()` - 37 edges
9. `journal()` - 35 edges
10. `DeliveryWalk` - 33 edges

## Surprising Connections (you probably didn't know these)
- `The wall the procedure itself hit, and the attempt that was withdrawn` --references--> `ticket_file()`  [INFERRED]
  docs/tickets/SEEN-109-calibrate-the-review-triage-and-the-routes-on.md → harness/cli.py
- `Agent runtime and the policy gate` --references--> `read_evidence()`  [INFERRED]
  docs/architecture.md → harness/cli.py
- `Development harness` --references--> `advance()`  [INFERRED]
  CONTEXT.md → harness/cli.py
- `Consequences` --references--> `advance()`  [INFERRED]
  docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md → harness/cli.py
- `The five stages` --references--> `advance()`  [INFERRED]
  docs/harness/workflow.md → harness/cli.py

## Import Cycles
- 3-file cycle: `harness/gates.py -> harness/triage.py -> harness/hooks.py -> harness/gates.py`
- 5-file cycle: `harness/gates.py -> harness/triage.py -> harness/hooks.py -> harness/guard.py -> harness/handoff.py -> harness/gates.py`

## Communities (317 total, 40 thin omitted)

### Community 0 - "TriageTest"
Cohesion: 0.11
Nodes (11): DepthByRuleTest, EveryAttemptsEvidenceTest, A coverage check, written straight into the journal. The real command runs…, L1: a returned ticket proved slices in each attempt, and Jev sees them all.…, A return, then one more slice proved, the way rework goes., The three rules that are never Jev's to answer., A ticket with more than one criterion, so per-criterion means something., A ticket worked to the review stage, with one file changed on the branch. (+3 more)

### Community 1 - ".evaluate"
Cohesion: 0.12
Nodes (15): G2: a second tool having recorded anything is not independence., A review from a context of its own, and the one case the gate can detect. A…, It has a context of its own by construction, so the field is not asked for., F5: criterion 3 says the implementer's session, not this attempt's., What a ticket that touches billing or the policy gate still owes. A subagent is…, F2: a codex return is the documented path, not a claim that codex wrote it., F6: a typo satisfied the one control that stands where a session cannot., G1: the F2 fix read authorship from the role, which is self-reported. (+7 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (28): metadata, config, dependencies, next, react, react-dom, @seen/core, description (+20 more)

### Community 3 - "Repository"
Cohesion: 0.07
Nodes (21): What the ninth review found, and passed, Every file in the project that git can see, ignored files excluded., Record files only. A journal directory also holds kpi.json and attachments,…, Journal files git has seen change after the commit that created them. The hash…, The branch work merges into, asked of git rather than assumed., The working copy a harness command operates on., Whether a commit has already merged, locally or on the remote. Both are asked:…, Whether the remote already holds this commit as the tip of this branch. (+13 more)

### Community 5 - "CLAUDE.md"
Cohesion: 0.10
Nodes (4): Consequences, The delivery receipt attests the tree minus the journal, An Outcome cannot count its own review rounds, Consequences

### Community 6 - "boundary.ts"
Cohesion: 0.16
Nodes (18): Three defects the tests could not see, CLOUD_SDK_PREFIXES, CloudSdkImport, EXEMPT, findCloudSdkImports(), isCloudSdk(), SEARCHED, SKIP_DIRECTORIES (+10 more)

### Community 8 - "cli.py"
Cohesion: 0.04
Nodes (76): argparse, Outcome, brief(), build_pack(), build_parser(), coverage(), decide(), describe() (+68 more)

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
Cohesion: 0.11
Nodes (11): ElidedBlastRadiusTest, repowise elides a large payload and leaves a marker in its place. Observed at…, One file is four arguments: --target X --changed-file X., repowise's own marker already says how to restore it., What the model sees when it is asked how risky this change is., Not as a low score, and not as silence., One extra payload string per question is not free: SEEN-101., The half of the ticket that is about tests rather than about size. (+3 more)

### Community 17 - "Seen: product requirements (MVP)"
Cohesion: 0.11
Nodes (18): 10. Pricing and metering, 11. Data, security and compliance, 12. Non-functional requirements, 13. Success metrics and gates, 14. Release plan, 15. Risks, 16. Open questions, 17. Glossary (+10 more)

### Community 18 - ".triage"
Cohesion: 0.07
Nodes (20): AlwaysReadTest, AnswersTest, ChangedFilesTest, DeterministicPassTest, OneRequestTest, PartlySettledTest, H1: the two things a review is against are never in a focus set. The journal…, Run the triage, with the requests the stage gates made cleared first. Reaching… (+12 more)

### Community 19 - "CoverageTest"
Cohesion: 0.38
Nodes (3): CoverageTest, Coverage on packages/core, measured by one fixed command and never allowed to…, The shape vitest's json-summary reporter writes.

### Community 20 - "stub"
Cohesion: 0.07
Nodes (18): AnswerTest, FallbackTest, GateTest, OverrideTest, QuestionTest, A transport failure is not fatal: it becomes a question for a person. The…, The live transport, exercised without a network. Nothing here calls the API. It…, Cloudflare rejects Python's default user agent with error 1010. Without a user… (+10 more)

### Community 21 - "kpi.py"
Cohesion: 0.14
Nodes (22): _check(), coverage(), first_pass_ci(), _latest_triage(), measure(), _moment(), output_tokens_per_slice(), One ticket's figures, derived from its journal. Nothing here is typed in, and… (+14 more)

### Community 22 - "Tickets"
Cohesion: 0.20
Nodes (10): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+2 more)

### Community 23 - "package.json"
Cohesion: 0.06
Nodes (33): devDependencies, eslint, @eslint/js, turbo, @types/node, typescript, typescript-eslint, vitest (+25 more)

### Community 24 - ".handoff"
Cohesion: 0.15
Nodes (7): AtTddTest, HandoffPackTest, A journal standing where a slice boundary happens: tdd, with a plan., A green check, recorded the way a slice ends., The only thing that crosses a slice boundary., What a fresh session reads before it does anything else., StatusBriefTest

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
Cohesion: 0.31
Nodes (4): A commit that is on main, which is what a merged receipt attests., The normal state between writing a receipt and pressing merge., Eighty tickets are todo with no journal; saying so every run is noise., StatusAgainstJournalTest

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
Cohesion: 0.10
Nodes (14): CitedRedTest, A red recorded before the rule existed can still be cited, so the gate checks…, solution_evidence(), NonCodeSolutionTest, The hole SEEN-102 fell into, closed., The guard: this must not become a way round the gate., The template asks, so a record that does not answer is not finished., Nine solution records are already written without it, and stay valid. (+6 more)

### Community 113 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, declaration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, forceConsistentCasingInFileNames (+15 more)

### Community 114 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowJs, baseUrl, incremental, isolatedModules, jsx, lib, module (+6 more)

### Community 115 - "telemetry.ts"
Cohesion: 0.16
Nodes (15): Attributes, AttributeValue, consoleTelemetryProvider(), CostEntry, nowUnixNano(), otlpAttributes(), otlpTelemetryProvider(), otlpTracesPayload() (+7 more)

### Community 116 - "state_for"
Cohesion: 0.10
Nodes (21): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-100: Let a gate tell an open question from an unknowable one, Acceptance criteria (+13 more)

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 119 - "tasks"
Cohesion: 0.13
Nodes (14): dependsOn, outputs, cache, persistent, dependsOn, $schema, tasks, build (+6 more)

### Community 120 - "DiscardTest"
Cohesion: 0.08
Nodes (14): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers, DiscardTest (+6 more)

### Community 121 - "advance"
Cohesion: 0.06
Nodes (31): Asking the graphs, Six rules you cannot infer, The context budget, The five stages, The Seen harness, The three agents, The worked example, What the harness will refuse (+23 more)

### Community 122 - "routing.py"
Cohesion: 0.06
Nodes (48): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-111: Hold a slice to the context it was routed to, and price it before it is worked, Slices, fnmatch (+40 more)

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

### Community 131 - "CommandTest"
Cohesion: 0.09
Nodes (14): AdvanceTest, BranchTest, clarify_evidence(), CommandTest, DraftTest, NoteAndCheckTest, Runs commands in process, which is how the tests stay fast and readable., ReturnTest (+6 more)

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

### Community 143 - ".at_tdd"
Cohesion: 0.05
Nodes (46): claude_edit_payload(), codex_patch(), codex_patch_payload(), HookDispatchTest, pre_compact_payload(), PreCompactTest, PreToolUseTest, Claude Code's PreToolUse payload for an Edit, whose path is absolute. (+38 more)

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
Cohesion: 0.11
Nodes (13): Repository layout, Acceptance criteria, Blocks, Context, Depends on, Description, Known and deliberately left, Outcome (+5 more)

### Community 153 - "providers/package.json"
Cohesion: 0.11
Nodes (17): dependencies, @supabase/supabase-js, description, devDependencies, @vitest/coverage-v8, @vitest/coverage-v8, main, name (+9 more)

### Community 154 - "handoff.py"
Cohesion: 0.06
Nodes (51): Acceptance criteria, Blocks, Context, Depends on, Description, Known and deliberately left, Outcome, SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack (+43 more)

### Community 155 - "FocusSetTest"
Cohesion: 0.14
Nodes (8): FocusSetTest, The reviewer's model is a rule, and the depth is what decides it. A full review…, What the reviewer is asked to read, and what shadow mode does to it., A stub asking for a spot review of one file out of the three., Pass three is text: the task the session hands its subagent., Asserted on the diff section, which is the part `no others` governs. The ticket…, ReviewerModelTest, ReviewerTaskTest

### Community 156 - "providers/src/index.ts"
Cohesion: 0.23
Nodes (18): createSecretsProvider(), environmentVariableFor(), envSecretsProvider(), SECRETS_PROVIDERS, SecretsProvider, SecretsProviderName, Environment, notUntilGoLive() (+10 more)

### Community 157 - "SEEN-098: Add repowise and carry its risk answer into the gate"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-098: Add repowise and carry its risk answer into the gate

### Community 158 - "postmark.ts"
Cohesion: 0.22
Nodes (12): header(), isPostmarkInbound(), MARKETPLACE_DOMAINS, marketplaceOf(), normaliseSubject(), PostmarkInbound, tenantOf(), threadKey() (+4 more)

### Community 159 - "Seen: development harness"
Cohesion: 0.10
Nodes (20): Commands, Jev before the model: the review triage and the route, KPIs, Principles, Security controls, Seen: development harness, The five stages, Tickets (+12 more)

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

### Community 165 - "sessions.py"
Cohesion: 0.11
Nodes (26): How the harness meets the assistants, budget(), Where this session stands against the budget for one slice. It reads the…, log_directory(), Where Claude Code keeps this project's session logs, by its own naming., How many tool calls a ticket's window contains. Counted from the same logs and…, tool_calls_between(), against_budget() (+18 more)

### Community 166 - "health.controller.ts"
Cohesion: 0.29
Nodes (6): HealthController, Controller, Get, LEDGER_CURRENCY, packageName, sumCents()

### Community 167 - "outbound.ts"
Cohesion: 0.20
Nodes (8): Environment, mailpit(), MailpitMessage, createMailer(), Environment, Mailer, OutboundMail, nodemailer

### Community 168 - "HarnessError"
Cohesion: 0.07
Nodes (56): Exception, harness, Tokens spent on a ticket, read from the session logs. Only four numbers are…, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do., The append-only journal: one directory of numbered records per ticket. Each…, Git access, and the fingerprint that decides whether evidence is still current.… (+48 more)

### Community 169 - "api/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 170 - "worker/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 171 - "skills.py"
Cohesion: 0.32
Nodes (7): drift(), One maintained skill, and the copies each assistant reads. The copies are…, One copy: the frontmatter an assistant reads, then the maintained body., Write every copy from the source, and say which were written., Committed copies that do not match what the source would generate., render(), sync()

### Community 172 - "OverlapTest"
Cohesion: 0.43
Nodes (3): OverlapTest, One question with two right addressees is one tool too many., Asking again is not redundancy between tools.

### Community 173 - ".advance_review"
Cohesion: 0.09
Nodes (13): PartlyGeneratedCopyTest, F1: one list answered two questions, and a security control fell through it.…, The part of the copy nobody generates, changed the way a session would., The other half, and the reason the two sets are separated rather than the hook…, FocusSetGateTest, G4: a ticket triaged once must not review a later attempt untriaged., A review record in the shape the gate demands, with what it read., The gate that makes the focus set worth computing. (+5 more)

### Community 174 - "Seen"
Cohesion: 0.25
Nodes (8): Commands, Getting it running, If it will not start, Seen, Tests, The cloud is a configuration, What it costs to run, Where things run

### Community 175 - "triage.py"
Cohesion: 0.16
Nodes (24): _acceptance_check(), _check_excerpt(), _coverage_check(), deterministic(), _entry(), _fingerprint_check(), _gitleaks_check(), journal_excerpts() (+16 more)

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
Cohesion: 0.12
Nodes (16): at(), journal_with_a_compaction(), check(), handoff(), journal_with_a_route(), check(), handoff(), A timestamp minutes after ten, so a journal can span an hour or more. (+8 more)

### Community 182 - ".refusal"
Cohesion: 0.04
Nodes (44): ANullRoundIsHeldToTheStrictestRoute, The scope may not be taken on the word of the record that wants it. F1 of this…, Corroboration grants the scope as well as withholding it: this is the citation…, This ticket's own record 17 declares position 2 for a round whose behaviour…, The acceptance this rule must not cost: slice three wrote elsewhere, so slice…, A check whose tree is the project's first commit belongs to no round of this…, Nothing is exempted by being absent: the green cannot carry a half the journal…, The scoped refusal and not only the whole-tree one: a green whose scope was… (+36 more)

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

### Community 187 - ".slice_three_writes_its_own_file"
Cohesion: 0.05
Nodes (29): AnEntryGitWillNotTakeAsAPathspec, CitedAcrossAttemptsByItsOwnFiles, EveryEntryInTheScopeResolves, NoPairSurvivesItsGreensRefusal, A slice naming a directory covers what is under it, and nothing beside it., No scope is not an empty scope: an empty one would accept everything., A citation the journal cannot place is held to the strict whole-tree rule. Fail…, A check whose tree was never committed as it stood: nothing says which files it… (+21 more)

### Community 188 - "hooks.py"
Cohesion: 0.06
Nodes (53): collections, _agent_that_stopped(), _block(), command_for(), _command_in(), _context(), dispatch_name(), _draft_review() (+45 more)

### Community 189 - ".reach_tdd"
Cohesion: 0.13
Nodes (9): JevTest, What no model is asked about, and why each one is a rule., What the model is asked, and what is done with what comes back., The record itself: where it may be written and what it names., F5: a route that did not clear its own threshold says so., Both planning gates passed, with the stage requests forgotten. The gates ask…, RecordTest, RouteBelowItsBarTest (+1 more)

### Community 194 - "HookSyncTest"
Cohesion: 0.09
Nodes (13): HookSyncTest, sync against a project whose copies already hold somebody else's entries., Every command in a copy, whoever owns it., The permissions are the person's. A sync that rewrote them would make every…, F2: the withholding this replaces rested on a reason known to be false. Slice 1…, Ownership is the command prefix, so a command written any other way is an entry…, A merge that appended rather than replaced would double every entry., The silent pass this check exists for. The edit breaks the invocation prefix,… (+5 more)

### Community 196 - "SidechainTokensTest"
Cohesion: 0.20
Nodes (6): DeliveredFiguresTest, walk_to_review(), One subagent entry inside the window, and one before it that is not., The reviewer's own cost, read from the log rather than declared., F3 of the second review: criterion 5 names kpi.json, and delivery writes it. G2…, SidechainTokensTest

### Community 197 - "test_forecast.py"
Cohesion: 0.18
Nodes (10): ForecastTest, What a plan of this shape has cost, read from the delivered KPI records. The…, A kpi.json shaped enough for forecast.py: one execution entry per figure.…, `count` tickets, each carrying the same one-slice figure., TheAbsenceTest, ThePredictionTest, TheSplitNamedTest, write_kpi() (+2 more)

### Community 198 - "GuardCommandTest"
Cohesion: 0.18
Nodes (7): GuardCommandTest, Before `start`, there is no stage to guard by, and the gate that comes next…, A non-code ticket reaches tdd with no slices to plan by at all., The real entry point, for the exit code and stderr text a hook reads., `harness guard <path>`, through the process every hook and every person calls., The RED this slice must demonstrate. Before harness/guard.py and the `guard`…, run_cli()

### Community 200 - "SEEN-094: Verify delivery against CI and verify the merge against the receipt"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-094: Verify delivery against CI and verify the merge against the receipt

### Community 201 - "GateTest"
Cohesion: 0.14
Nodes (6): GateTest, NonCodeGateTest, PlaceholderShapeTest, F8: shaping the template must not stop guarding the fields it kept., Attempt 2 citing a pair from attempt 1, beside the slice it proved here., RequiredFieldTest

### Community 202 - ".journal"
Cohesion: 0.14
Nodes (6): A review re-run lists its findings again; they are still the same findings., Whether a ticket was worked with the scout and the reviewer, from its journal.…, F4: the report row is about the scout and the reviewer, not either one., Nineteen journals were written before either agent existed., RepeatedReviewTest, SubagentAttributionTest

### Community 203 - "SEEN-106: Enforce the harness with hooks in both assistants, generated from one source"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, SEEN-106: Enforce the harness with hooks in both assistants, generated from one source

### Community 204 - "DescriptionSaysWhatIsNotAppliedTest"
Cohesion: 0.43
Nodes (3): DescriptionSaysWhatIsNotAppliedTest, The ticket says the routed effort is applied by nothing, where a reader meets…, The sentence that promised Claude Code's effort and the Codex TOML.

### Community 205 - "SEEN-103: Declare non-code mode at the solution stage, not after it"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-103: Declare non-code mode at the solution stage, not after it

### Community 206 - ".plant"
Cohesion: 0.10
Nodes (7): EffectiveShadowTest, GoLiveDecisionTest, Which tickets the window counts, and which it names as excluded and why., The one question a triage asks: which shadow am I in, and what put me there., The switch and the decision it names, which is what going live takes., F3: going live must name the record the decision is in, or it is an edit., WindowTest

### Community 207 - "agents.py"
Cohesion: 0.13
Nodes (27): _body(), claude_copy(), codex_copy(), drift(), _folded(), implementer_default(), Three agents with a context of their own, and the copies each assistant reads.…, The model and effort the implementer's copies carry, which never vary. The… (+19 more)

### Community 208 - "jev.py"
Cohesion: 0.08
Nodes (37): Every question this stage owns, answered once. An answer already recorded for…, stage_decisions(), _answer_from_human(), _ask_api(), ask_batch(), ask_many(), build_questions(), build_request() (+29 more)

### Community 209 - "require"
Cohesion: 0.04
Nodes (96): Outcome, Outcome, Refuse unless the condition holds. Never repairs, never warns and continues., require(), _a_record_number(), check_findings(), cited_check(), _clarify() (+88 more)

### Community 210 - "TheSkillSaysSoTest"
Cohesion: 0.12
Nodes (7): The one maintained skill, on the two agents a session may send work to., F11: the setting lives in a file this repository does not track., F9: Claude Code has no read-only Bash, so the hole is named, not implied., H5: the skill described the rule as it was before G3., H5: [actors] tools carries human, and the gate reads [actors] assistants., H6: F5 widened this from the current attempt to every attempt., TheSkillSaysSoTest

### Community 211 - "route_stub"
Cohesion: 0.17
Nodes (12): FixedCopiesTest, The copies say the same thing whatever the ticket is doing. Generated per…, Which is what actions/checkout gives on every pull_request event., The state F3 of the eighth review found: no slice is in hand at all., A transport answering the two route questions, keyed by slice position.…, Which route a proved slice is held to. F1 of the fourth review: the gate read…, One slice proved on its own, the way a rework attempt proves one., Slice 1 is Jev's haiku, slice 2 is the money rule's opus. (+4 more)

### Community 212 - "SessionEnvironment"
Cohesion: 0.12
Nodes (8): NoPlanYetTest, Which session wrote a record, without saying what the session is called., No session id is an absence, not a claim that there was one session., Tests that decide for themselves which session they are running in. The harness…, A pack before the solution record has advanced names no slice., SessionEnvironment, SessionOnEveryRecordTest, SessionUnknownTest

### Community 213 - "Seen: MVP architecture"
Cohesion: 0.17
Nodes (12): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen: MVP architecture, Services (+4 more)

### Community 214 - "test_enforcement.py"
Cohesion: 0.10
Nodes (17): check_runs(), _gh(), latest_per_name(), pull_request(), What GitHub says about a commit and its pull request. Two readers and nothing…, Every check GitHub has run for one commit, with its status and conclusion., The pull request for the current branch, or a refusal when there is none., One run per check name, the most recent. A commit can carry several runs of the… (+9 more)

### Community 215 - "FailedCheckStillAsksTest"
Cohesion: 0.33
Nodes (3): FailedCheckStillAsksTest, J1: only the three rules silence the request; a failed check does not. Pass one…, The figure SEEN-109 divides on, which a skipped request left at zero.

### Community 216 - ".rendered"
Cohesion: 0.13
Nodes (8): ForwardReferenceTest, F5 of SEEN-108's third review: what the printed report tells a reader to run.…, The direction this guards now: a report never sends a reader to nothing., F1 of the fifth review: a row nothing could price must still render. The fourth…, The shape that raised: one unpriced row beside one priced row., F2 of the sixth review: a row a reader can check. Points is every point the…, ReconcilingRowTest, UnpricedRowTest

### Community 217 - "DeclaredModelTest"
Cohesion: 0.20
Nodes (5): DeclaredModelTest, What a subagent can say about itself, because the log cannot say it. A Claude…, Declares an agent on every call: this class is about `--model`, and SEEN-111's…, The subagent ran on the routed model; the log says the parent's., Declares an agent on every call, for the same reason `GateTest.run_check` does:…

### Community 218 - "MergeTest"
Cohesion: 0.08
Nodes (10): BookkeepingAfterReceiptTest, DeliveryChecksTest, broken(), MergeTest, A commit can carry more than one run of the same check. GitHub shows the latest…, What delivery itself writes may follow the receipt; nothing else may., Check runs in the shape gh reports them., The week includes the ticket that just delivered, so the report moves. (+2 more)

### Community 219 - "SlicesProvedRatherThanGreensCounted"
Cohesion: 0.09
Nodes (29): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (113, 361 build points), Working a ticket, Acceptance criteria, Blocks (+21 more)

### Community 220 - "TddGateTest"
Cohesion: 0.19
Nodes (8): check_record(), coverage_record(), A recorded check. A red fails by default, because a red that passed is not one., A measurement of the gated package, which the tdd gate requires for the attempt., Slice 1 proved in attempt 1, slice 2 in attempt 2, slice 3 in attempt 5.…, Every journal written before this rule: nothing says whether it moved., Slice one proved in attempt 1, slice three in attempt 2, which is now. Attempt…, TddGateTest

### Community 221 - "calibration.py"
Cohesion: 0.15
Nodes (23): What the review found, What the second review found, _covers(), escapes(), finding_key(), latest_finding_records(), latest_findings(), normalise() (+15 more)

### Community 223 - ".commit"
Cohesion: 0.07
Nodes (20): Record 50: the defect under this whole chain, and it is a step of the…, What the procedure asks for before review is left, on the real file., And what it asks for after the reviewer has read, in the same file., The shape the procedure forces on every round, which the fixture lacked. The…, This ticket's own case, and the reason the tolerance exists., Without this the acceptance above could be an exact match all along., The mirror that matters at the gate: a scope granted is a scope compared, so…, The guard the tolerance is worth nothing without: one path is tolerated, and a… (+12 more)

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

### Community 231 - "Outcome"
Cohesion: 0.11
Nodes (20): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-107: Let Jev settle what the review can settle before a model reads the diff, The ticket file as it stands now: the recorded path, or found by its id. A… (+12 more)

### Community 232 - "SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second"
Cohesion: 0.20
Nodes (10): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, Outcome, SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second (+2 more)

### Community 233 - "Outcome"
Cohesion: 0.19
Nodes (14): Outcome, The wall the procedure itself hit, and the attempt that was withdrawn, What the fifth review found, What the fourth review found, What the seventh review found, and passed, What the sixth review found, effective_shadow(), Why the go-live on record is not one, or nothing when it is. The criterion asks… (+6 more)

### Community 234 - ".reach_tdd"
Cohesion: 0.16
Nodes (6): F3 of the first review: the flag the second escape kind is read from., A review that returns a ticket records what it found, or the window cannot read…, F1: a return from review says what it found, or says it found nothing., ReturningFindingsTest, ReviewReturnDeclarationTest, UnmetCriteriaTest

### Community 235 - "AgentDefinitionTest"
Cohesion: 0.29
Nodes (3): AgentDefinitionTest, What each agent is allowed to do, which is the point of separating them., The scout and the reviewer read and nothing else. SEEN-105 could say this of…

### Community 236 - ".set_shadow"
Cohesion: 0.13
Nodes (8): ContextOfItsOwnTest, GateTest, A check recorded under a model the route did not choose. Refused only with…, The one line in the project's own thresholds, and only that line. Written…, A check, recorded under a model, which is what a session log gives. The tests…, One slice proved red then green, both recorded under one model., A slice held to a context of its own, and not only to its route's model.…, The one line in the project's own thresholds, and only that line. Written…

### Community 238 - ".task"
Cohesion: 0.16
Nodes (5): CarriedNotAppliedTest, What the spawn instruction may promise about the effort, which is nothing. F1…, A route is read only for the plan it routed. The record names the solution…, Back to solution, a different plan accepted, and no new route., StalePlanTest

### Community 239 - "evidence"
Cohesion: 0.15
Nodes (13): What the third review found, delivered_at(), evidence(), _excluded_reason(), journals(), Every ticket's records, by ticket id, and what could not be read. A journal…, Why this ticket is not in the window, or nothing when it is., Go-live or stay-shadow for the triage, by the rule and by nothing else. The… (+5 more)

### Community 240 - "FifthReviewTest"
Cohesion: 0.11
Nodes (7): FifthReviewTest, The downgraded slices against the rest, on the charges the rule names., The findings of the fifth review, at note 56., A ticket whose blocking finding lands in a file no slice named., F1: nothing says which slice caused it, which is what route_rule already says…, RouteVerdictTest, slice_entry()

### Community 241 - "CostPerPointByModelTest"
Cohesion: 0.21
Nodes (4): CostPerPointByModelTest, What a point cost on each model, beside the tokens per point. The point of the…, In shadow those differ, and only one of them cost anything., F3: dividing a partial cost by every point understates the model. On SEEN-108's…

### Community 242 - "ThirdReviewTest"
Cohesion: 0.13
Nodes (8): Go-live or stay-shadow for the triage, stated by the rule and not by a reading., The ticket's another ten: ten clean tickets after the escape., The findings of the third review, at note 36., F1: counted neither way must mean the verdict waits, not that it passes., F4: a founder auditing the decision must recompute over the same list., F6: a stray file in one journal must not block every other review., ThirdReviewTest, TriageVerdictTest

### Community 243 - "doctor.py"
Cohesion: 0.05
Nodes (58): datetime, agent_problems(), calibration_problems(), gitignore_problems(), hook_file_problems(), hook_problems(), journal_problems(), link_problems() (+50 more)

### Community 244 - "OutcomeReconcilesTest"
Cohesion: 0.36
Nodes (3): OutcomeReconcilesTest, The Outcome's findings against the journal that is supposed to supply them. F4…, Every reviewer note, in the order they were written.

### Community 245 - "noul"
Cohesion: 0.10
Nodes (19): The triage's own return names what it could see no evidence for. Without the…, TriageReturnTest, noul(), score(), transport(), low_on_the_second(), transport(), PartialAnswerTest (+11 more)

### Community 246 - "DecideTest"
Cohesion: 0.22
Nodes (6): DecideTest, `guard.decide` called directly, for every rule and both absence cases. The…, Claude Code's PreToolUse payload carries tool_input.file_path, always absolute.…, Only packages/ and apps/ are refused before tdd; a documentation ticket writes…, Past tdd there is nothing left in this guard to refuse by: review and deliver…, Rule 3 asks only whether the branch names some ticket; whether that ticket has…

### Community 247 - "delivery.py"
Cohesion: 0.08
Nodes (34): The context per session, _graph_records(), Every graph note on the tickets a report covers., Read a stage evidence file, which must live where drafts live. Anywhere else it…, Every delivered ticket's figures, derived from its journal. A ticket delivered…, read_evidence(), ticket_figures(), write_report() (+26 more)

### Community 249 - "CompactionWindowTest"
Cohesion: 0.14
Nodes (10): CompactionWindowTest, journal_with_rework(), The same two-slice ticket, returned once and proved again. The shape F2 of the…, F2 of the third review: what a rework round's tokens are charged to. Nothing,…, This fixture ends its plan at a handoff, so the advance has nothing left. The…, The slices do not carry it; the ticket's own token figure does., F3 of SEEN-106's review: a compaction is not a slice boundary. A pack written…, The declared boundary at record 8, not the compaction at record 10.… (+2 more)

### Community 250 - "risk.py"
Cohesion: 0.27
Nodes (9): _absent(), assess(), changed_files(), What repowise says about the change in front of the session. A risk decision…, What the working tree changes against HEAD, tracked and untracked., The change-risk answer, or a recorded reason there is none. Scored from the…, _run(), changed_files() (+1 more)

### Community 251 - "test_routing.py"
Cohesion: 0.10
Nodes (9): DeclarationIsInstructedTest, ImplementerCopyTest, The route: which model and which effort implement each slice. Rules first, and…, F4: a route record that predates the fields the skill says it carries. The only…, The agent the slice is worked by, and the keys its copies carry. They were…, The declaration is only worth having if something asks for it. F1 of the third…, A ticket worked to the tdd stage, which is where the route is decided., RouteRecordIsCurrentTest (+1 more)

### Community 252 - "ARoundThatBelongsToNoSingleSlice"
Cohesion: 0.13
Nodes (12): ARoundThatBelongsToNoSingleSlice, A null position is a claim on the plan, so the plan is what it is judged over.…, The journal of a round that declared null for the checks it recorded., The citation record 47 recorded as refused, accepted: this is the whole point…, The mirror that matters most: slice two is a slice this round is not, and the…, Whose files the comparison was made over is what a session reading the refusal…, A null position claims no slice, so there is nothing for another record to…, Null is a claim and not a shrug, so a record declaring it where the accepted… (+4 more)

### Community 253 - ".citing_all"
Cohesion: 0.10
Nodes (12): CiteAcrossAttempts, OrderingAcrossAttempts, A pair is one round, and the attempt is what a gate can check of that. The…, Attempt 1's red with attempt 2's green, and an ordering nothing objects to., Without this the refusal above could be the ordering rule's: the red precedes…, The rule ties the halves to each other, not to the citing attempt: the citation…, Why the pair is asked after the ordering pass and not inside it: the ordering…, SEEN-112's shape: five attempts, the early slices proved in the first two. A… (+4 more)

### Community 254 - "ReportTest"
Cohesion: 0.19
Nodes (6): The evidence per ticket and per slice, with the rule printed beside it., F2 of the first review: the only test for this line exercised the branch that…, The one thing that happens without a person: the return to shadow., Go live the way the founder must: the switch and the decision it names., ReportTest, TriageShadowTest

### Community 255 - "FourthReviewTest"
Cohesion: 0.15
Nodes (8): FourthReviewTest, The findings of the fourth review, at note 46., F1: a reviewer writes a hunk, and the tail is not all digits., Not in would_exclude and not in the diff: placed nowhere, not placed outside., F2: the triage reads the verdict, which is what four documents say., A window that is not full is a reason to conclude nothing, not to override., F3: a declaration is a claim by its author, so the report says who made it., F4: the one-line instruction must not be able to come back quietly.

### Community 256 - "checks.py"
Cohesion: 0.14
Nodes (18): demonstrates_failure(), phases_for(), Running and recording a verification command. A check is a real subprocess in…, Whether a run is evidence that a test failed. Exit zero is a passing command,…, Run one check and return the evidence to record. `declared` is the tier the…, run(), check(), _quiet_payload() (+10 more)

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

### Community 266 - "DeclaredSliceTest"
Cohesion: 0.20
Nodes (6): DeclaredSliceTest, Who says a slice is done. The pack counts greens, which is right until a slice…, F1: the rendered pack is what a resuming session actually reads., F7: a declaration the journal contradicts is visible, not prevented., H4: F1 again, with a return as the trigger instead of a second green., The limit the flag exists for, pinned so nobody is surprised by it.

### Community 268 - "TheRoundsOwnCommitSaysWhatItCovered"
Cohesion: 0.11
Nodes (9): Without this the refusal above could be a comparison with nothing to accept,…, F1 of the third review: the corroboration was one round deep. A record's…, Without this the refusal above could be the corroboration refusing, which would…, The round committed slice two's file as well, so a later change to it changes…, The shape every real journal is in, and the fixture was not: the harness writes…, What the measurement caught: on SEEN-112 slice 1's green fell back to the whole…, The walk back stops at the first commit that moved something, so it cannot…, Without this the refusal above could be a comparison that had already found… (+1 more)

### Community 269 - "BudgetTest"
Cohesion: 0.29
Nodes (4): BudgetTest, What a session can be told about its own spending, and when it cannot., A session log of the shape the assistant writes, and nothing else., A subagent's own transcript, beside the parent's, the way Claude Code writes it.

### Community 270 - "run"
Cohesion: 0.12
Nodes (19): criterion_key(), depth_from(), failed(), file_key(), file_subject(), focus_set(), questions(), Every path the solution record named, from the slices and from changes. A… (+11 more)

### Community 272 - "ExecutionFiguresTest"
Cohesion: 0.14
Nodes (6): ExecutionFiguresTest, journal_worked_in_two_sessions(), Two slices planned, two proved, and two sessions that wrote the records., What each slice was routed to, what it ran on, and what it cost. From the…, Keyed by `done` and not `position`. A handoff names the slice in front of you,…, In shadow a slice runs on the session's model, whatever it was routed to.…

### Community 273 - "ReceiptAttestsTheReviewedTreeTest"
Cohesion: 0.29
Nodes (3): What a receipt attests, and why attempt 8's exception was withdrawn. Attempt 8…, The order the procedure has to keep: the status goes in before the gate., ReceiptAttestsTheReviewedTreeTest

### Community 274 - "SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants

### Community 275 - "execution"
Cohesion: 0.33
Nodes (6): cost_cents(), execution(), _latest_route(), What those output tokens cost on that model, or that nobody priced it. A whole…, What each slice was routed to, what it ran on and what it cost. Null rather…, The route in force, which is the most recent one that routed this plan. The…

### Community 276 - "SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token

### Community 277 - "ticket_evidence"
Cohesion: 0.29
Nodes (7): declared_empty(), latest_route(), latest_triage(), Every review return that declared it found nothing, and who declared it. A…, The route that routed the plan the work was done against. The same rule kpi…, One counted ticket's row: what the triage would have dropped, and what got…, ticket_evidence()

### Community 279 - "SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined

### Community 280 - "The calibration window"
Cohesion: 0.40
Nodes (4): Not in the window, The calibration window, The routes, The triage

### Community 284 - "ReplanCarriesForward"
Cohesion: 0.20
Nodes (5): named_plan(), A plan whose slices name different files, so the guard can tell them apart., SEEN-112 at its record 44: two slices green, a return, the same plan again.…, The one case the attempt boundary got right, and it is kept. A plan whose…, ReplanCarriesForward

### Community 285 - "APairIsJudgedByItsGreen"
Cohesion: 0.17
Nodes (8): APairIsJudgedByItsGreen, A red's standing rests on its green's tree, because it can have none of its…, The shape of every real red, and of this ticket's own red 34., Without this the acceptance below could be an exact match all along., The citation this ticket has been blocked on for two rounds., So the acceptance above is worth what the green's comparison is worth: a change…, The one thing this harness refuses outright, and the exemption is not a way…, A timeout is a fact about the runner rather than about the behaviour.

### Community 286 - "slice_windows"
Cohesion: 0.33
Nodes (7): Outcome, What is not done, and what cannot be, What the returns taught, which is the part worth keeping, _closes(), Each slice's window: what it cost and which records fall inside it. Keyed by…, Which slice this record's boundary closed, and the figures it carried. A…, slice_windows()

### Community 287 - "SEEN-113: Let a tdd record cite the evidence a return did not invalidate"
Cohesion: 0.14
Nodes (15): Acceptance criteria, Amendment, Blocks, Depends on, Outcome, SEEN-113: Let a tdd record cite the evidence a return did not invalidate, Slices, content_fingerprint() (+7 more)

### Community 288 - "forecast.py"
Cohesion: 0.29
Nodes (7): _delivered_slice_figures(), predict(), What a plan of this shape has cost, read from the delivered KPI records. A…, Every delivered ticket's per-slice output tokens, keyed by ticket id. Only…, The price of a plan shaped like `slices`, from what delivered slices cost.…, math, statistics

### Community 289 - ".evidence"
Cohesion: 0.19
Nodes (6): PositionIsDeclaredTest, A rework round spanning slices belongs to none of them, and says null., F3 of the ninth review: a rule a plan can miss by not naming a file. The rules…, Checks that declare the routed model, so the rule is what is under test.…, F2 of the fifth review: the route comparison is not skipped by omission. The…, RuleTrippedByTheWorkTest

### Community 290 - "DirectoryNamedSliceTest"
Cohesion: 0.39
Nodes (3): DirectoryNamedSliceTest, A rule a plan's wording cannot dodge. F6 of the third review: the patterns were…, `packages/core-utils` is a different package, not money arithmetic.

### Community 291 - "UnevidencedCriterionTest"
Cohesion: 0.15
Nodes (6): AskedHonestlyTest, K1: `asked` says whether pass two ran, and the reason says why not. Three cases…, The one answer that sends a ticket back before any model reads the diff., A stub answering the second criterion below its threshold and no other., UnevidencedCriterionTest, broken()

### Community 292 - "Outcome"
Cohesion: 0.33
Nodes (7): Outcome, _evidence(), How this ticket was worked: briefs from the scout, and the review's own kind.…, The evidence of the most recent accepted advance out of a stage., Slices planned at solution against slices proved at tdd. Proved counts every…, slices(), subagents()

### Community 293 - "SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide, Slices

### Community 295 - "ModesMustAgreeTest"
Cohesion: 0.43
Nodes (3): ModesMustAgreeTest, A ticket that plans no tests and then records a code TDD changed its mind., With a well-formed slice, so it is the disagreement that refuses.

### Community 296 - "ReworkIsToldWhatItRunsOn"
Cohesion: 0.30
Nodes (5): A plan with no slice left in front of the session still has a route to give.…, A route record of the plan in hand, one model per planned slice., The line is an answer to "if this is rework", not a replacement for what a…, A return puts a ticket back at tdd, so that is where the line belongs., ReworkIsToldWhatItRunsOn

### Community 297 - "guard.py"
Cohesion: 0.14
Nodes (16): _allow(), decide(), _is_ticket_file(), The edit guard: whether a path may be written, and why. Early enforcement of…, The path as the rules read it: project-relative, forward slashes. A hook…, Whether `path` may be written now, and why. `records` is the branch's own…, _refuse(), _relative() (+8 more)

### Community 298 - ".test_the_delivered_file_carries_a_cost_for_each_routed_slice"
Cohesion: 0.40
Nodes (3): DeliveredCostTest, F2 of SEEN-108's second review: criterion 4 names kpi.json, and delivery writes…, A session log for this walk, because a cost without tokens is null. The name is…

### Community 300 - "SEEN-086: Build the Seen harness CLI with staged journal and receipts"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Blocks, Context, Depends on, Description, Design decisions, Not in this ticket, by design, Outcome (+2 more)

### Community 302 - "PackEdgesTest"
Cohesion: 0.22
Nodes (5): PackEdgesTest, Three things the first packs written in anger got wrong., A green per planned slice, which is what a complete plan looks like., At review the regression and the coverage are already behind you., The bytes on disk are compared against a recorded hash.

### Community 303 - "_field"
Cohesion: 0.28
Nodes (9): fixes_index(), Every ticket that names an earlier one as the ticket it fixes, by that ticket.…, _frontmatter_declares_agent_action(), What the ticket file itself says, which no session rewrites by hand., escaped_defects(), _field(), frontmatter(), The ticket's own metadata, which is where points and status live. (+1 more)

### Community 304 - "TheDisclosureNamesWhatARedIsHeldTo"
Cohesion: 0.28
Nodes (4): What a red is held to, said where a reader of the rule will meet it. The second…, F3 of the fifth review. The list says a red is held to the route of the…, Within one attempt no accepted tdd record can mention the checks being cited,…, TheDisclosureNamesWhatARedIsHeldTo

### Community 305 - "record"
Cohesion: 0.25
Nodes (7): at(), A triage as SEEN-107 writes one: what it would have dropped, and its answers., F3: reopen voids the receipt, so the ticket is being worked again., record(), review_advance(), route_record(), triage_record()

### Community 306 - "file_facts"
Cohesion: 0.25
Nodes (8): file_facts(), _hunks(), _numstat(), package_of(), Lines added and removed per path, as git counts them., Hunks per path, counted from one diff rather than one diff per file., Which package a path belongs to, by this repository's own layout.…, One entry per changed file: what the reviewer_must_read question is given. The…

### Community 308 - "GeneratedCopiesTest"
Cohesion: 0.43
Nodes (3): GeneratedCopiesTest, Files sync writes are named by naming their source. Found by running the triage…, Excluded from the check, not from the diff: it did change.

### Community 312 - "append"
Cohesion: 0.33
Nodes (6): append(), The numbers of the criteria the model could see no evidence for. The triage's…, The criteria the model could see no evidence for. `passed` is False only for an…, Run the triage, keep it, and send the ticket back if a criterion has no…, unevidenced(), unevidenced_positions()

### Community 313 - "why_not"
Cohesion: 0.50
Nodes (4): Why a request produced nothing, or nothing when it produced something. Here…, why_not(), Why pass two produced nothing, or nothing when it produced something. One line,…, _why_not()

## Knowledge Gaps
- **969 isolated node(s):** `graphify-mcp`, `repowise`, `$schema`, `collection`, `sourceRoot` (+964 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2128 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `.evaluate`, `Repository`, `CommandTest`, `TemplatePositionTest`, `RecordTest`, `cli.py`, `DeliveryWalk`, `.graph`, `DeclaredSliceTest`, `DoctorTest`, `.at_tdd`, `ReceiptAttestsTheReviewedTreeTest`, `.triage`, `CoverageTest`, `stub`, `FindingFileTest`, `.handoff`, `ReopenTest`, `RepositoryTest`, `StateForTest`, `ReplanCarriesForward`, `slice_windows`, `.evidence`, `UnevidencedCriterionTest`, `ModesMustAgreeTest`, `ReportTest`, `.advance_review`, `triage.py`, `AgentSyncTest`, `file_facts`, `DispatcherShapeTest`, `.refusal`, `append`, `.slice_three_writes_its_own_file`, `hooks.py`, `.reach_tdd`, `HookSyncTest`, `RedRuleTest`, `test_forecast.py`, `GateTest`, `jev.py`, `require`, `route_stub`, `test_enforcement.py`, `FailedCheckStillAsksTest`, `DeclaredModelTest`, `MergeTest`, `TddGateTest`, `calibration.py`, `Outcome`, `.reach_tdd`, `.set_shadow`, `evidence`, `solution_evidence`, `doctor.py`, `noul`, `delivery.py`, `DiscardTest`, `advance`, `risk.py`, `test_routing.py`, `.citing_all`?**
  _High betweenness centrality (0.313) - this node is a cross-community bridge._
- **Why does `require()` connect `require` to `checks.py`, `Repository`, `routing.py`, `Outcome`, `cli.py`, `HarnessError`, `skills.py`, `run`, `agents.py`, `jev.py`, `triage.py`, `doctor.py`, `test_enforcement.py`, `delivery.py`, `Outcome`, `handoff.py`, `hooks.py`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `Outcome` connect `Outcome` to `require`, `providers/src/index.ts`, `app.module.ts`, `boundary.ts`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 96 inferred relationships involving `HarnessError` (e.g. with `Outcome` and `journals()`) actually correct?**
  _`HarnessError` has 96 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `require()` (e.g. with `Outcome` and `Outcome`) actually correct?**
  _`require()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Repository` (e.g. with `HarnessError` and `AgentSyncTest`) actually correct?**
  _`Repository` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `repowise`, `$schema` to the rest of the system?**
  _969 weakly-connected nodes found - possible documentation gaps or missing edges._