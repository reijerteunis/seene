# Graph Report - seene  (2026-10-01)

## Corpus Check
- 1807 files · ~1,343,107 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 5, .toml 5, .example 1)

## Summary
- 5223 nodes · 10537 edges · 335 communities (306 shown, 29 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 349 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4e5fd652`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TriageTest
- .review
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
- schema.test.ts
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
- .at_tdd
- pull_request_template.md
- context.py
- pre-commit
- dependencies
- rls.test.ts
- SEEN-096: Add codegraph and route the graph command to it
- Week 39 of 2026
- Sprint 0: 37 of 81 points delivered
- Outcome
- providers/package.json
- pack
- FocusSetTest
- providers/src/index.ts
- SEEN-098: Add repowise and carry its risk answer into the gate
- repository.ts
- Seen: development harness
- BudgetRulesTest
- journal
- SEEN-102: Decide on the repowise PR bot for a private repository
- SyncTest
- ComparisonTest
- Outcome
- health.controller.ts
- outbound.ts
- HarnessError
- api/nest-cli.json
- worker/nest-cli.json
- .plan_with
- OverlapTest
- .advance_review
- Seen
- triage.py
- .journal
- AgentSyncTest
- ToolCallsTest
- providers/tsconfig.json
- marketplaces.test.ts
- record
- .evaluate
- Seen
- SEEN-093: Add harness reopen to void a receipt before merge
- NoSecondReaderTest
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
- Outcome
- clarify_evidence
- TheSkillSaysSoTest
- SEEN-094: Verify delivery against CI and verify the merge against the receipt
- test_stage_gates.py
- .journal
- SEEN-106: Enforce the harness with hooks in both assistants, generated from one source
- model
- SEEN-103: Declare non-code mode at the solution stage, not after it
- .plant
- agents.py
- uniqueness.test.ts
- require
- TheSkillSaysSoTest
- route_stub
- SessionEnvironment
- Seen: MVP architecture
- CommandTest
- FailedCheckStillAsksTest
- .rendered
- .set_shadow
- BookkeepingAfterReceiptTest
- .done
- TddGateTest
- Outcome
- NonCodeSolutionTest
- .commit
- The reviewer
- The reviewer
- The scout
- The scout
- SessionDigestTest
- CachedFiguresTest
- SessionThresholdTest
- SEEN-107: Let Jev settle what the review can settle before a model reads the diff
- SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second
- OneReaderOfTheQuestionTest
- .reach_tdd
- AgentDefinitionTest
- GateTest
- RenamedTicketTest
- .task
- calibration.py
- FifthReviewTest
- CostPerPointByModelTest
- ThirdReviewTest
- doctor.py
- OutcomeReconcilesTest
- test_triage.py
- DecideTest
- delivery.py
- SprintReportCostTest
- CompactionWindowTest
- named
- RouteTest
- .refusal
- .citing_all
- ReportTest
- FourthReviewTest
- graph.py
- SkillAgreesWithItselfTest
- RouteInTheSkillTest
- TemplatePositionTest
- The implementer
- The implementer
- SixthReviewTest
- SliceBoundaryTest
- PricedPointsCellTest
- IntegerCentsTest
- slices_proved
- AgentCountTest
- TheRoundsOwnCommitSaysWhatItCovered
- BudgetTest
- render
- DeliveryChecksTest
- MergeTest
- ReceiptAttestsTheReviewedTreeTest
- SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants
- execution
- SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token
- The Seen harness
- FindingFileTest
- SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined
- The calibration window
- ReopenTest
- The Seen harness
- IsolationTest
- ReplanCarriesForward
- APairIsJudgedByItsGreen
- handoff.py
- SEEN-113: Let a tdd record cite the evidence a return did not invalidate
- PartialAnswerTest
- .evidence
- DirectoryNamedSliceTest
- GuardIsLastTest
- Outcome
- SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide
- PartlyGeneratedCopyTest
- ModesMustAgreeTest
- withTheUniquenessReplacedBy
- SEEN-101: Let a journal survive its ticket being renamed
- .test_the_delivered_file_carries_a_cost_for_each_routed_slice
- SEEN-129: List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data
- SEEN-130: Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back
- SEEN-131: Consumer invoices with VAT by destination and the OSS return
- SEEN-132: Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through
- tenancyGapsIn
- TheDisclosureNamesWhatARedIsHeldTo
- record
- The Codex review, and the four findings it returned
- SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack
- GeneratedCopiesTest
- SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds
- SEEN-115: Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them
- SEEN-116: Property-based and mutation tests on the money core, as a gate
- SEEN-117: The spec session writes the RED; the implementer cannot touch it
- SEEN-118: A finding needs a failing test, taste is not a finding, and the third round is the founder's
- SEEN-119: Independent slices run in parallel worktrees
- SEEN-120: Affected-only checks and a local CI that finishes in minutes
- F1, and what it says about the test that missed it
- SEEN-121: Bake-off: the TypeScript LSP plugin against codegraph, keep one
- SEEN-122: Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures
- SEEN-123: Cap harness work at ten percent of a sprint and make every harness ticket state its payback
- SEEN-124: Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due
- SEEN-125: Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack
- SEEN-126: Register the storefront entity for EPR, GPSR responsible-person data and product liability cover
- SEEN-127: Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee
- SEEN-128: Connection ownership and storefront mode on the trade record
- SEEN-133: Returns, withdrawals and guarantee cases handled as the seller of record
- SEEN-134: Storefront pilot: one supplier live on Bol under Seen's account, first statement paid
- SEEN-135: Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings
- SEEN-136: No test touches the clock, the network or randomness unfaked, and a flaky test is a defect
- SEEN-137: One worked example per acceptance criterion before the solution stage, so the RED is a transcription
- SEEN-138: The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change
- current_slice
- verdict_routes
- SEEN-139: Hand the immutability guard forward to every migration that adds a table
- claimsStillStanding

## God Nodes (most connected - your core abstractions)
1. `HarnessError` - 145 edges
2. `require()` - 101 edges
3. `Repository` - 87 edges
4. `CommandTest` - 71 edges
5. `clarify_evidence()` - 65 edges
6. `solution_evidence()` - 65 edges
7. `execute()` - 41 edges
8. `route_stub()` - 37 edges
9. `journal()` - 35 edges
10. `DeliveryWalk` - 33 edges

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
- 3-file cycle: `harness/gates.py -> harness/triage.py -> harness/hooks.py -> harness/gates.py`
- 5-file cycle: `harness/gates.py -> harness/triage.py -> harness/hooks.py -> harness/guard.py -> harness/handoff.py -> harness/gates.py`

## Communities (335 total, 29 thin omitted)

### Community 0 - "TriageTest"
Cohesion: 0.09
Nodes (13): The triage's own return names what it could see no evidence for. Without the…, TriageReturnTest, DepthByRuleTest, EveryAttemptsEvidenceTest, A coverage check, written straight into the journal. The real command runs…, L1: a returned ticket proved slices in each attempt, and Jev sees them all.…, A return, then one more slice proved, the way rework goes., The three rules that are never Jev's to answer. (+5 more)

### Community 1 - ".review"
Cohesion: 0.09
Nodes (15): G2: a second tool having recorded anything is not independence., A review from a context of its own, and the one case the gate can detect. A…, It has a context of its own by construction, so the field is not asked for., F5: criterion 3 says the implementer's session, not this attempt's., What a ticket that touches billing or the policy gate still owes. A subagent is…, F2: a codex return is the documented path, not a claim that codex wrote it., F6: a typo satisfied the one control that stands where a session cannot., G1: the F2 fix read authorship from the role, which is self-reported. (+7 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (28): metadata, config, dependencies, next, react, react-dom, @seen/core, description (+20 more)

### Community 3 - "Repository"
Cohesion: 0.05
Nodes (24): What the ninth review found, and passed, Every file in the project that git can see, ignored files excluded., Record files only. A journal directory also holds kpi.json and attachments,…, Journal files git has seen change after the commit that created them. The hash…, The branch work merges into, asked of git rather than assumed., The working copy a harness command operates on., Whether a commit has already merged, locally or on the remote. Both are asked:…, Whether the remote already holds this commit as the tip of this branch. (+16 more)

### Community 5 - "CLAUDE.md"
Cohesion: 0.09
Nodes (4): Consequences, The delivery receipt attests the tree minus the journal, An Outcome cannot count its own review rounds, Consequences

### Community 6 - "boundary.ts"
Cohesion: 0.16
Nodes (18): Three defects the tests could not see, CLOUD_SDK_PREFIXES, CloudSdkImport, EXEMPT, findCloudSdkImports(), isCloudSdk(), SEARCHED, SKIP_DIRECTORIES (+10 more)

### Community 8 - "cli.py"
Cohesion: 0.04
Nodes (89): argparse, Consequences, SEEN-086 is the bootstrap ticket and has no journal, Outcome, demonstrates_failure(), phases_for(), Whether a run is evidence that a test failed. Exit zero is a passing command,…, Run one check and return the evidence to record. `declared` is the tier the… (+81 more)

### Community 9 - "DeliveryWalk"
Cohesion: 0.16
Nodes (6): DeliveryTest, DeliveryWalk, The walk to a delivered ticket, without the tests. Separated so other files can…, No test reaches GitHub. Green by default; a test that cares says otherwise., Take a ticket through every stage, with real recorded checks. `mark_reviewed`…, ReportTest

### Community 10 - ".graph"
Cohesion: 0.11
Nodes (12): GraphFixture, GraphTest, Which tool answers which question. codegraph indexes symbols, so it answers…, A guard, not a change: graphify knows files and pull requests., Without the MCP server running, the index is as old as the last sync., why, health and risk: what the history says rather than what the code is., Stubs and helpers. No tests of its own, so nothing is run twice., A graphify on PATH that reports what it was asked, and nothing else. (+4 more)

### Community 12 - ".mcp.json"
Cohesion: 0.40
Nodes (4): graphify-mcp, repowise, graphify, repowise

### Community 13 - "app.module.ts"
Cohesion: 0.08
Nodes (30): AppModule, header(), isPostmarkInbound(), MARKETPLACE_DOMAINS, marketplaceOf(), normaliseSubject(), PostmarkInbound, tenantOf() (+22 more)

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
Cohesion: 0.06
Nodes (25): AlwaysReadTest, AnswersTest, AskedHonestlyTest, ChangedFilesTest, DeterministicPassTest, DirectorySliceTest, OneRequestTest, PartlySettledTest (+17 more)

### Community 19 - "CoverageTest"
Cohesion: 0.38
Nodes (3): CoverageTest, Coverage on packages/core, measured by one fixed command and never allowed to…, The shape vitest's json-summary reporter writes.

### Community 20 - "stub"
Cohesion: 0.07
Nodes (18): AnswerTest, FallbackTest, GateTest, OverrideTest, QuestionTest, A transport failure is not fatal: it becomes a question for a person. The…, The live transport, exercised without a network. Nothing here calls the API. It…, Cloudflare rejects Python's default user agent with error 1010. Without a user… (+10 more)

### Community 21 - "kpi.py"
Cohesion: 0.12
Nodes (24): _check(), coverage(), first_pass_ci(), _latest_triage(), measure(), _moment(), output_tokens_per_slice(), One ticket's figures, derived from its journal. Nothing here is typed in, and… (+16 more)

### Community 22 - "Tickets"
Cohesion: 0.18
Nodes (11): Epics, Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations, Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF, Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, Sprint 3: Reconcile module, Stripe billing, statements, Shopify, Sprint 4: Comply v1, Kaufland connector, listing fixes by API, Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector, Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter (+3 more)

### Community 23 - "package.json"
Cohesion: 0.06
Nodes (33): devDependencies, eslint, @eslint/js, turbo, @types/node, typescript, typescript-eslint, vitest (+25 more)

### Community 24 - "DeclaredSliceTest"
Cohesion: 0.05
Nodes (25): AtTddTest, DeclaredSliceTest, HandoffPackTest, PackEdgesTest, QuietCheckTest, A journal standing where a slice boundary happens: tdd, with a plan., A green check, recorded the way a slice ends., The only thing that crosses a slice boundary. (+17 more)

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
Cohesion: 0.14
Nodes (15): Acceptance criteria, Blocks, Context, Depends on, Description, Design decisions, Not in this ticket, by design, Outcome (+7 more)

### Community 34 - "SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table"
Cohesion: 0.18
Nodes (11): Acceptance criteria, After the review, 27 September 2026, Blocks, Context, Depends on, Description, Outcome, SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table (+3 more)

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
Cohesion: 0.16
Nodes (8): solution_evidence(), NonCodeSlicePlanTest, plan(), A ticket with no behaviour to prove plans no slices. Its own class because a…, A slice plan of the shape the solution record carries., What the solution gate does with the plan it is now given., A plan may disagree with the estimate; the gate says so and proceeds. The caps…, SlicePlanTest

### Community 113 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, declaration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, forceConsistentCasingInFileNames (+15 more)

### Community 114 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowJs, baseUrl, incremental, isolatedModules, jsx, lib, module (+6 more)

### Community 115 - "schema.test.ts"
Cohesion: 0.03
Nodes (75): Answer, backendState(), COUNTED_MEMBERS, fixtureTenantId(), ForeignRows, FreeTextColumn, Holding, LAST_MEMBER (+67 more)

### Community 116 - "SEEN-100: Let a gate tell an open question from an unknowable one"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-100: Let a gate tell an open question from an unknowable one

### Community 118 - "SEEN-088: Integrate Jev AI typed decisions into the harness gates"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-088: Integrate Jev AI typed decisions into the harness gates

### Community 119 - "tasks"
Cohesion: 0.12
Nodes (15): dependsOn, outputs, cache, persistent, dependsOn, $schema, tasks, build (+7 more)

### Community 120 - "DiscardTest"
Cohesion: 0.08
Nodes (14): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-092: Sync the harness skill to Claude Code and Codex and retire the Seene leftovers, DiscardTest (+6 more)

### Community 121 - "The Seen harness"
Cohesion: 0.22
Nodes (8): Asking the graphs, Six rules you cannot infer, The context budget, The five stages, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 122 - "routing.py"
Cohesion: 0.03
Nodes (88): Jev before the model: the review triage and the route, Outcome, fnmatch, implementer_default(), The model and effort the implementer's copies carry, which never vary. The…, extra_review_fields(), The ticket and where it came from: the path, the id, or the snapshot. Which…, What a review must answer beyond the template, asked of the gate itself. A… (+80 more)

### Community 123 - "agent/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 124 - "connectors/package.json"
Cohesion: 0.18
Nodes (10): description, main, name, private, scripts, lint, test, typecheck (+2 more)

### Community 125 - "core/package.json"
Cohesion: 0.10
Nodes (20): description, devDependencies, pg, @types/pg, @vitest/coverage-v8, @vitest/coverage-v8, main, name (+12 more)

### Community 126 - "api/package.json"
Cohesion: 0.07
Nodes (27): description, devDependencies, @nestjs/cli, @nestjs/testing, supertest, @types/nodemailer, @types/supertest, @nestjs/cli (+19 more)

### Community 127 - "vitest"
Cohesion: 0.18
Nodes (4): packageName, packageName, config, vitest

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
Cohesion: 0.10
Nodes (7): AdvanceTest, BranchTest, DraftTest, NoteAndCheckTest, ReturnTest, StartTest, StatusTest

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
Cohesion: 0.07
Nodes (17): ExecutionFiguresTest, journal_with_a_return(), journal_worked_in_two_sessions(), LastSliceTest, Slices, sessions and what a slice cost, from the journal and nothing else., Null, not one: a record without a session cannot say it was the same one., A returned ticket proved slices in each attempt, and paid for each. Reading…, Null rather than zero: nothing was cut badly, there was nothing to cut. (+9 more)

### Community 138 - "SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports"
Cohesion: 0.25
Nodes (8): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports, What the first report says

### Community 139 - "SEEN-099: Set the context budget and measure what the tools changed"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-099: Set the context budget and measure what the tools changed

### Community 140 - "DoctorTest"
Cohesion: 0.13
Nodes (5): AppendOnlyScopeTest, DeliverStatusTest, DoctorTest, Records are append-only. The files beside them are not records., The rule CLAUDE.md states and nothing enforced until SEEN-107. The reviewed-…

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

### Community 148 - "rls.test.ts"
Cohesion: 0.05
Nodes (36): Context, Attempt, Attempted, AuthoredIdentifier, authoredIdentifiers(), chainTo(), ClaimFixture, connect() (+28 more)

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
Cohesion: 0.12
Nodes (12): Acceptance criteria, Blocks, Context, Depends on, Description, Known and deliberately left, Outcome, SEEN-097: Set up the local Docker development environment (+4 more)

### Community 153 - "providers/package.json"
Cohesion: 0.11
Nodes (17): dependencies, @supabase/supabase-js, description, devDependencies, @vitest/coverage-v8, @vitest/coverage-v8, main, name (+9 more)

### Community 154 - "pack"
Cohesion: 0.14
Nodes (15): _decisions(), estimate_tokens(), _graph_answers(), _one_line(), pack(), Tokens, rounded up, by the only measure available here., What this slice runs on, which the session is never to decide for itself. The…, What a round that belongs to no single slice runs on, or nothing. `_route_line`… (+7 more)

### Community 155 - "FocusSetTest"
Cohesion: 0.12
Nodes (9): FocusSetTest, transport(), The reviewer's model is a rule, and the depth is what decides it. A full review…, What the reviewer is asked to read, and what shadow mode does to it., A stub asking for a spot review of one file out of the three., Pass three is text: the task the session hands its subagent., Asserted on the diff section, which is the part `no others` governs. The ticket…, ReviewerModelTest (+1 more)

### Community 156 - "providers/src/index.ts"
Cohesion: 0.13
Nodes (32): createSecretsProvider(), environmentVariableFor(), envSecretsProvider(), SECRETS_PROVIDERS, SecretsProvider, SecretsProviderName, Environment, notUntilGoLive() (+24 more)

### Community 157 - "SEEN-098: Add repowise and carry its risk answer into the gate"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-098: Add repowise and carry its risk answer into the gate

### Community 158 - "repository.ts"
Cohesion: 0.08
Nodes (37): READING_SOURCES, SETTLED_SOURCES, candidatePaths(), COMPILED_TO_SOURCE_EXTENSIONS, IMPORTS_THAT_CANNOT_READ, INERT_EXTENSIONS, isRepositoryFile(), listRepositoryDirectory() (+29 more)

### Community 159 - "Seen: development harness"
Cohesion: 0.17
Nodes (11): Commands, Correctness before volume: rules, contracts, proofs, and a bounded review, KPIs, Principles, Repository layout, Security controls, Seen: development harness, The context per session (+3 more)

### Community 160 - "BudgetRulesTest"
Cohesion: 0.22
Nodes (3): BudgetRulesTest, A rule in a prompt is not a rule., A date would count the tickets that installed them, which it must not.

### Community 161 - "journal"
Cohesion: 0.10
Nodes (16): EscapeTest, finding(), journal(), F2: two committed reports must not state different findings for one ticket., F3: the fallback restored the merge the fourth review removed., What counts as an escape, and what the rule refuses to count either way., The triage said so itself and returned the ticket; it missed nothing., F4 of the first review: nothing requires the flag, so a forgotten one would… (+8 more)

### Community 162 - "SEEN-102: Decide on the repowise PR bot for a private repository"
Cohesion: 0.17
Nodes (12): A note on how it got here, Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-102: Decide on the repowise PR bot for a private repository (+4 more)

### Community 164 - "ComparisonTest"
Cohesion: 0.16
Nodes (4): ComparisonTest, What the report says about the figures, and when it refuses to say it., G4: SEEN-098's own rule, applied to the agents this time., Two numbers divided is not evidence when there are two tickets.

### Community 165 - "Outcome"
Cohesion: 0.09
Nodes (27): Known and deliberately left, Outcome, Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-111: Hold a slice to the context it was routed to, and price it before it is worked (+19 more)

### Community 166 - "health.controller.ts"
Cohesion: 0.29
Nodes (6): HealthController, Controller, Get, LEDGER_CURRENCY, packageName, sumCents()

### Community 167 - "outbound.ts"
Cohesion: 0.20
Nodes (8): Environment, mailpit(), MailpitMessage, createMailer(), Environment, Mailer, OutboundMail, nodemailer

### Community 168 - "HarnessError"
Cohesion: 0.07
Nodes (56): ast, Exception, harness, Running and recording a verification command. A check is a real subprocess in…, Tokens spent on a ticket, read from the session logs. Only four numbers are…, HarnessError, The one error type a harness command may fail with, and the check that raises…, A refusal a person can act on: what is wrong and, where possible, what to do. (+48 more)

### Community 169 - "api/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 170 - "worker/nest-cli.json"
Cohesion: 0.25
Nodes (7): collection, compilerOptions, deleteOutDir, tsConfigPath, entryFile, $schema, sourceRoot

### Community 171 - ".plan_with"
Cohesion: 0.10
Nodes (11): AnEntryGitWillNotTakeAsAPathspec, EveryEntryInTheScopeResolves, A slice naming a directory covers what is under it, and nothing beside it., No scope is not an empty scope: an empty one would accept everything., A file entry that matches no path makes the comparison vacuous. F2 of this…, The partial case: the scope is not trustworthy because part of it is not,…, A file that did not exist yet is not code that check covered., F6 of the third review: an entry resolving outside the repository. `git ls-tree… (+3 more)

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
Cohesion: 0.04
Nodes (79): _absent(), assess(), changed_files(), What repowise says about the change in front of the session. A risk decision…, What the working tree changes against HEAD, tracked and untracked., The change-risk answer, or a recorded reason there is none. Scored from the…, _run(), _acceptance_check() (+71 more)

### Community 176 - ".journal"
Cohesion: 0.12
Nodes (9): G3: the window is the reviewer's, and the rework between two is not., Where the scout runs, and from SEEN-108 the implementer subagent., M1 and M2: what a long ticket loses, and what it must not. The first cap kept…, One accepted tdd record per slice, each citing a red and a green., What kpi.json keeps of a triage, derived and never typed., N1: the field went in at attempt 10 with no test, found by mutation. The share…, ReviewWindowsTest, SliceCapTest (+1 more)

### Community 177 - "AgentSyncTest"
Cohesion: 0.06
Nodes (12): AgentSyncTest, ImplementerTest, F10: a file with no source under harness/agents/ has had no review. The name…, The guard the two above lost: drift must not be able to stand in for strays. A…, G7: .claude/agents/ belongs to the person; only the seen- names are ours., What comes back from a context of its own, and how small it has to be. A brief…, The one agent whose model and effort are not its own to choose. All three carry…, The first agent that does, because writing the slice is what it is for. (+4 more)

### Community 179 - "providers/tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, baseUrl, noEmit, extends, include, ../../tsconfig.base.json

### Community 180 - "marketplaces.test.ts"
Cohesion: 0.10
Nodes (21): Capability, CAPABILITY_MODES, CAPABILITY_ROWS, CapabilityKey, CapabilityMode, EXCEPTIONS, MARKETPLACE_COLUMNS, MARKETPLACE_IDS (+13 more)

### Community 181 - "record"
Cohesion: 0.12
Nodes (16): at(), journal_with_a_compaction(), check(), handoff(), journal_with_a_route(), check(), handoff(), A timestamp minutes after ten, so a journal can span an hour or more. (+8 more)

### Community 182 - ".evaluate"
Cohesion: 0.05
Nodes (34): ANullRoundIsHeldToTheStrictestRoute, CiteAcrossAttempts, Corroboration grants the scope as well as withholding it: this is the citation…, The acceptance this rule must not cost: slice three wrote elsewhere, so slice…, What the measurement caught: on SEEN-112 slice 1's green fell back to the whole…, This ticket's own case, and the reason the tolerance exists., A red judged by its green is still the red the journal says it is. F1 of the…, Two rounds in attempt 1, and the tdd record that attributed them. `mentioning`… (+26 more)

### Community 183 - "Seen"
Cohesion: 0.33
Nodes (6): Development harness, Example dialogue, Flagged ambiguities, Language, Product, Seen

### Community 184 - "SEEN-093: Add harness reopen to void a receipt before merge"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-093: Add harness reopen to void a receipt before merge

### Community 185 - "NoSecondReaderTest"
Cohesion: 0.15
Nodes (10): NoSecondReaderTest, Criterion 1 of SEEN-140: one implementation of the comparison in harness/. The…, Every module of the package, which is the only scope that cannot age. F1 of the…, Whether a comparator is a plan's file list, rather than mentions one. Three…, Every membership test in one module, as (line, the source of it)., The blind spot F1 came through, proved on source of its own shape. Without this…, F1 of the second review: the scope must not be an allowlist. The instrument…, F2 of the second review: a subtree, not a string. `entry.get('files') or []` is… (+2 more)

### Community 186 - "hello.ts"
Cohesion: 0.24
Nodes (8): connection, HELLO_QUEUE, HelloPayload, HelloResult, HelloWorker, startHelloWorker(), worker, bullmq

### Community 187 - ".slice_three_writes_its_own_file"
Cohesion: 0.09
Nodes (17): CitedAcrossAttemptsByItsOwnFiles, NoPairSurvivesItsGreensRefusal, A citation the journal cannot place is held to the strict whole-tree rule. Fail…, A check whose tree was never committed as it stood: nothing says which files it…, The scoped comparison identifies a check's tree by its fingerprint, so the two…, The one citation that is scoped to nothing on purpose, and says so. The…, Attempt 1 proved slice one and ran its regression, then advanced., The plan reading a null position gets is the slice citation's and not the… (+9 more)

### Community 188 - "hooks.py"
Cohesion: 0.05
Nodes (62): collections, Outcome, What is not done, and what cannot be, What the returns taught, which is the part worth keeping, _agent_that_stopped(), _block(), command_for(), _command_in() (+54 more)

### Community 189 - ".reach_tdd"
Cohesion: 0.13
Nodes (9): JevTest, What no model is asked about, and why each one is a rule., What the model is asked, and what is done with what comes back., The record itself: where it may be written and what it names., F5: a route that did not clear its own threshold says so., Both planning gates passed, with the stage requests forgotten. The gates ask…, RecordTest, RouteBelowItsBarTest (+1 more)

### Community 194 - "HookSyncTest"
Cohesion: 0.09
Nodes (13): HookSyncTest, sync against a project whose copies already hold somebody else's entries., Every command in a copy, whoever owns it., The permissions are the person's. A sync that rewrote them would make every…, F2: the withholding this replaces rested on a reason known to be false. Slice 1…, Ownership is the command prefix, so a command written any other way is an entry…, A merge that appended rather than replaced would double every entry., The silent pass this check exists for. The edit breaks the invocation prefix,… (+5 more)

### Community 196 - "SidechainTokensTest"
Cohesion: 0.20
Nodes (6): DeliveredFiguresTest, walk_to_review(), One subagent entry inside the window, and one before it that is not., The reviewer's own cost, read from the log rather than declared., F3 of the second review: criterion 5 names kpi.json, and delivery writes it. G2…, SidechainTokensTest

### Community 197 - "Outcome"
Cohesion: 0.14
Nodes (15): Acceptance criteria, Amendments, Blocks, Carried forward, Context, Depends on, Description, Outcome (+7 more)

### Community 198 - "clarify_evidence"
Cohesion: 0.15
Nodes (9): GuardCommandTest, Before `start`, there is no stage to guard by, and the gate that comes next…, SEEN-140's RED for this reader, which answered no to a question two said yes…, A non-code ticket reaches tdd with no slices to plan by at all., The real entry point, for the exit code and stderr text a hook reads., `harness guard <path>`, through the process every hook and every person calls., The RED this slice must demonstrate. Before harness/guard.py and the `guard`…, run_cli() (+1 more)

### Community 200 - "SEEN-094: Verify delivery against CI and verify the merge against the receipt"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-094: Verify delivery against CI and verify the merge against the receipt

### Community 201 - "test_stage_gates.py"
Cohesion: 0.06
Nodes (24): ForecastTest, What a plan of this shape has cost, read from the delivered KPI records. The…, A kpi.json shaped enough for forecast.py: one execution entry per figure.…, `count` tickets, each carrying the same one-slice figure., TheAbsenceTest, ThePredictionTest, TheSplitNamedTest, write_kpi() (+16 more)

### Community 202 - ".journal"
Cohesion: 0.14
Nodes (6): A review re-run lists its findings again; they are still the same findings., Whether a ticket was worked with the scout and the reviewer, from its journal.…, F4: the report row is about the scout and the reviewer, not either one., Nineteen journals were written before either agent existed., RepeatedReviewTest, SubagentAttributionTest

### Community 203 - "SEEN-106: Enforce the harness with hooks in both assistants, generated from one source"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, SEEN-106: Enforce the harness with hooks in both assistants, generated from one source

### Community 204 - "model"
Cohesion: 0.24
Nodes (7): How the harness meets the assistants, model(), The model this session is running on, from its own log, or nothing. Read when a…, DescriptionSaysWhatIsNotAppliedTest, The ticket says the routed effort is applied by nothing, where a reader meets…, The sentence that promised Claude Code's effort and the Codex TOML., check()

### Community 205 - "SEEN-103: Declare non-code mode at the solution stage, not after it"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-103: Declare non-code mode at the solution stage, not after it

### Community 206 - ".plant"
Cohesion: 0.10
Nodes (7): EffectiveShadowTest, GoLiveDecisionTest, Which tickets the window counts, and which it names as excluded and why., The one question a triage asks: which shadow am I in, and what put me there., The switch and the decision it names, which is what going live takes., F3: going live must name the record the decision is in, or it is an edit., WindowTest

### Community 207 - "agents.py"
Cohesion: 0.08
Nodes (36): What the sixth review found, _body(), claude_copy(), codex_copy(), drift(), _folded(), Three agents with a context of their own, and the copies each assistant reads.…, Every agent as this repository defines it, from its source and one table. (+28 more)

### Community 208 - "uniqueness.test.ts"
Cohesion: 0.15
Nodes (8): ERASURE_REGISTRY_TABLE, EXTERNALLY_SOURCED_TABLES, TABLE_RELKINDS, connect(), Fixture, NEEDED, Rail, where()

### Community 209 - "require"
Cohesion: 0.03
Nodes (117): Outcome, Outcome, Outcome, draft(), go_back(), The ticket file as it stands now: the recorded path, or found by its id. A…, ticket_file(), Refuse unless the condition holds. Never repairs, never warns and continues. (+109 more)

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
Cohesion: 0.14
Nodes (14): Agent runtime and the policy gate, Capability routing per marketplace, Infrastructure and security, Modules on the same record, Open verifications before build, Principles, Seen as seller of record (storefront), Seen: MVP architecture (+6 more)

### Community 214 - "CommandTest"
Cohesion: 0.06
Nodes (18): BaselineTest, CitedRedTest, NonCodeCoverageTest, A ticket with no behaviour to prove owes no coverage figure. Its own setUp…, The baseline moves only when a ticket delivers., A red recorded before the rule existed can still be cited, so the gate checks…, A refusal has to say what happened, not what the rule is called., RefusalMessageTest (+10 more)

### Community 215 - "FailedCheckStillAsksTest"
Cohesion: 0.29
Nodes (4): FailedCheckStillAsksTest, low_on_the_second(), J1: only the three rules silence the request; a failed check does not. Pass one…, The figure SEEN-109 divides on, which a skipped request left at zero.

### Community 216 - ".rendered"
Cohesion: 0.13
Nodes (8): ForwardReferenceTest, F5 of SEEN-108's third review: what the printed report tells a reader to run.…, The direction this guards now: a report never sends a reader to nothing., F1 of the fifth review: a row nothing could price must still render. The fourth…, The shape that raised: one unpriced row beside one priced row., F2 of the sixth review: a row a reader can check. Points is every point the…, ReconcilingRowTest, UnpricedRowTest

### Community 217 - ".set_shadow"
Cohesion: 0.14
Nodes (8): ContextOfItsOwnTest, DeclaredModelTest, What a subagent can say about itself, because the log cannot say it. A Claude…, Declares an agent on every call: this class is about `--model`, and SEEN-111's…, The subagent ran on the routed model; the log says the parent's., A slice held to a context of its own, and not only to its route's model.…, The one line in the project's own thresholds, and only that line. Written…, Declares an agent on every call, for the same reason `GateTest.run_check` does:…

### Community 218 - "BookkeepingAfterReceiptTest"
Cohesion: 0.17
Nodes (5): BookkeepingAfterReceiptTest, A commit can carry more than one run of the same check. GitHub shows the latest…, What delivery itself writes may follow the receipt; nothing else may., The week includes the ticket that just delivered, so the report moves., SupersededRunTest

### Community 219 - ".done"
Cohesion: 0.09
Nodes (29): graphify, Ground rules, Index of docs/, Seen: Claude Code entry point, Tickets (140, 422 build points), Working a ticket, Acceptance criteria, Blocks (+21 more)

### Community 220 - "TddGateTest"
Cohesion: 0.19
Nodes (8): check_record(), coverage_record(), A recorded check. A red fails by default, because a red that passed is not one., A measurement of the gated package, which the tdd gate requires for the attempt., Slice 1 proved in attempt 1, slice 2 in attempt 2, slice 3 in attempt 5.…, Every journal written before this rule: nothing says whether it moved., Slice one proved in attempt 1, slice three in attempt 2, which is now. Attempt…, TddGateTest

### Community 221 - "Outcome"
Cohesion: 0.12
Nodes (24): Outcome, The wall the procedure itself hit, and the attempt that was withdrawn, What the fifth review found, What the fourth review found, What the review found, What the second review found, escapes(), finding_key() (+16 more)

### Community 222 - "NonCodeSolutionTest"
Cohesion: 0.21
Nodes (6): NonCodeSolutionTest, The hole SEEN-102 fell into, closed., The guard: this must not become a way round the gate., The template asks, so a record that does not answer is not finished., Nine solution records are already written without it, and stay valid., Absent is not the same as a record that said nothing.

### Community 223 - ".commit"
Cohesion: 0.07
Nodes (21): Record 50: the defect under this whole chain, and it is a step of the…, What the procedure asks for before review is left, on the real file., And what it asks for after the reviewer has read, in the same file., The shape the procedure forces on every round, which the fixture lacked. The…, Without this the acceptance above could be an exact match all along., The mirror that matters at the gate: a scope granted is a scope compared, so…, The guard the tolerance is worth nothing without: one path is tolerated, and a…, Without this the refusal above could be the fixture failing to match for some… (+13 more)

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

### Community 234 - ".reach_tdd"
Cohesion: 0.16
Nodes (6): F1: a return from review says what it found, or says it found nothing., F3 of the first review: the flag the second escape kind is read from., A review that returns a ticket records what it found, or the window cannot read…, ReturningFindingsTest, ReviewReturnDeclarationTest, UnmetCriteriaTest

### Community 235 - "AgentDefinitionTest"
Cohesion: 0.29
Nodes (3): AgentDefinitionTest, What each agent is allowed to do, which is the point of separating them., The scout and the reviewer read and nothing else. SEEN-105 could say this of…

### Community 236 - "GateTest"
Cohesion: 0.17
Nodes (5): GateTest, A check recorded under a model the route did not choose. Refused only with…, The one line in the project's own thresholds, and only that line. Written…, A check, recorded under a model, which is what a session log gives. The tests…, One slice proved red then green, both recorded under one model.

### Community 238 - ".task"
Cohesion: 0.16
Nodes (5): CarriedNotAppliedTest, What the spawn instruction may promise about the effort, which is nothing. F1…, A route is read only for the plan it routed. The record names the solution…, Back to solution, a different plan accepted, and no new route., StalePlanTest

### Community 239 - "calibration.py"
Cohesion: 0.07
Nodes (45): declared_empty(), delivered_at(), effective_shadow(), evidence(), _excluded_reason(), fixes_index(), journals(), latest_route() (+37 more)

### Community 240 - "FifthReviewTest"
Cohesion: 0.11
Nodes (7): FifthReviewTest, The findings of the fifth review, at note 56., A ticket whose blocking finding lands in a file no slice named., F1: nothing says which slice caused it, which is what route_rule already says…, The downgraded slices against the rest, on the charges the rule names., RouteVerdictTest, slice_entry()

### Community 241 - "CostPerPointByModelTest"
Cohesion: 0.21
Nodes (4): CostPerPointByModelTest, What a point cost on each model, beside the tokens per point. The point of the…, In shadow those differ, and only one of them cost anything., F3: dividing a partial cost by every point understates the model. On SEEN-108's…

### Community 242 - "ThirdReviewTest"
Cohesion: 0.13
Nodes (8): F6: a stray file in one journal must not block every other review., Go-live or stay-shadow for the triage, stated by the rule and not by a reading., The ticket's another ten: ten clean tickets after the escape., The findings of the third review, at note 36., F1: counted neither way must mean the verdict waits, not that it passes., F4: a founder auditing the decision must recompute over the same list., ThirdReviewTest, TriageVerdictTest

### Community 243 - "doctor.py"
Cohesion: 0.04
Nodes (67): datetime, agent_problems(), calibration_problems(), gitignore_problems(), hook_file_problems(), hook_problems(), journal_problems(), link_problems() (+59 more)

### Community 244 - "OutcomeReconcilesTest"
Cohesion: 0.36
Nodes (3): OutcomeReconcilesTest, The Outcome's findings against the journal that is supposed to supply them. F4…, Every reviewer note, in the order they were written.

### Community 245 - "test_triage.py"
Cohesion: 0.15
Nodes (16): Tooling, noul(), score(), transport(), transport(), The review triage: three passes, cheapest first, and what each one settles.…, G1: a judgement nobody made must not take a file out of a review., A transport answering every triage question, keyed the way triage asks them.… (+8 more)

### Community 246 - "DecideTest"
Cohesion: 0.22
Nodes (6): DecideTest, `guard.decide` called directly, for every rule and both absence cases. The…, Claude Code's PreToolUse payload carries tool_input.file_path, always absolute.…, Only packages/ and apps/ are refused before tdd; a documentation ticket writes…, Past tdd there is nothing left in this guard to refuse by: review and deliver…, Rule 3 asks only whether the branch names some ticket; whether that ticket has…

### Community 247 - "delivery.py"
Cohesion: 0.09
Nodes (31): Read a stage evidence file, which must live where drafts live. Anywhere else it…, read_evidence(), baseline(), compare(), measured(), Line coverage on the packages the harness holds a floor under. One fixed…, The last delivered figure, or None when nothing has delivered yet., The line percentage vitest's json-summary reporter wrote. (+23 more)

### Community 249 - "CompactionWindowTest"
Cohesion: 0.14
Nodes (10): CompactionWindowTest, journal_with_rework(), The same two-slice ticket, returned once and proved again. The shape F2 of the…, F2 of the third review: what a rework round's tokens are charged to. Nothing,…, This fixture ends its plan at a handoff, so the advance has nothing left. The…, The slices do not carry it; the ticket's own token figure does., F3 of SEEN-106's review: a compaction is not a slice boundary. A pack written…, The declared boundary at record 8, not the compaction at record 10.… (+2 more)

### Community 250 - "named"
Cohesion: 0.22
Nodes (10): The second review, and why the instrument needed fixing twice, clientPrivilegesOnNonTablesIn(), effectivePrivilegesIn(), foreignTablesIn(), holdingLabel(), materialisedViewsIn(), named(), nonTableRelationsIn() (+2 more)

### Community 251 - "RouteTest"
Cohesion: 0.10
Nodes (8): DeclarationIsInstructedTest, ImplementerCopyTest, F4: a route record that predates the fields the skill says it carries. The only…, The agent the slice is worked by, and the keys its copies carry. They were…, The declaration is only worth having if something asks for it. F1 of the third…, A ticket worked to the tdd stage, which is where the route is decided., RouteRecordIsCurrentTest, RouteTest

### Community 252 - ".refusal"
Cohesion: 0.08
Nodes (19): ARoundThatBelongsToNoSingleSlice, A null position is a claim on the plan, so the plan is what it is judged over.…, The journal of a round that declared null for the checks it recorded., The citation record 47 recorded as refused, accepted: this is the whole point…, The mirror that matters most: slice two is a slice this round is not, and the…, Whose files the comparison was made over is what a session reading the refusal…, A null position claims no slice, so there is nothing for another record to…, Null is a claim and not a shrug, so a record declaring it where the accepted… (+11 more)

### Community 253 - ".citing_all"
Cohesion: 0.14
Nodes (9): EvidenceForChangedCode, OrderingAcrossAttempts, SEEN-112's shape: five attempts, the early slices proved in the first two. A…, The two reasons a citation is refused, which one sentence used to answer. A…, The attempt was the proxy; naming it is what hid the real reason., The mirror the loosening is only safe with: code that moved loses its evidence.…, The ordering rule reads sequence numbers, which are monotonic across attempts.…, SeenOneTwelveShape (+1 more)

### Community 254 - "ReportTest"
Cohesion: 0.19
Nodes (6): The evidence per ticket and per slice, with the rule printed beside it., F2 of the first review: the only test for this line exercised the branch that…, The one thing that happens without a person: the return to shadow., Go live the way the founder must: the switch and the decision it names., ReportTest, TriageShadowTest

### Community 255 - "FourthReviewTest"
Cohesion: 0.15
Nodes (8): FourthReviewTest, The findings of the fourth review, at note 46., F1: a reviewer writes a hunk, and the tail is not all digits., Not in would_exclude and not in the diff: placed nowhere, not placed outside., F2: the triage reads the verdict, which is what four documents say., A window that is not full is a reason to conclude nothing, not to override., F3: a declaration is a claim by its author, so the report says who made it., F4: the one-line instruction must not be able to come back quietly.

### Community 256 - "graph.py"
Cohesion: 0.39
Nodes (8): ask(), build_command(), _index_counts(), Asking the knowledge graphs a question and keeping the answer in the journal.…, Nodes and edges, as codegraph status reports them. Weaker than a hash: two…, Run one verb in the project root and return what to record., _run(), tool_for()

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
Nodes (6): The findings of the sixth review, at note 65., A round that returned a ticket on an open finding, and a round that passed., F1: the review gate refuses an advance carrying an unresolved finding, so a…, F2: membership, not the rate, is what says a group is empty., F4: two faults, two messages, so a reader fixes the right one., SixthReviewTest

### Community 266 - "slices_proved"
Cohesion: 0.20
Nodes (10): _is_an_accepted_green(), _plan_length_at(), _positions_the_journal_declares(), How many slices the plan in force at that point in the journal had. Read from…, How far into the plan the work has got, counting slices and not greens. A slice…, A green the journal kept: a tdd check of that phase that really passed., Which slice of the plan each cited green proved, where a tdd record says. The…, The one position the journal settles on for that green, or nothing. Three… (+2 more)

### Community 268 - "TheRoundsOwnCommitSaysWhatItCovered"
Cohesion: 0.08
Nodes (12): The scope may not be taken on the word of the record that wants it. F1 of this…, Without this the refusal above could be a comparison with nothing to accept,…, This ticket's own record 17 declares position 2 for a round whose behaviour…, F1 of the third review: the corroboration was one round deep. A record's…, Without this the refusal above could be the corroboration refusing, which would…, The round committed slice two's file as well, so a later change to it changes…, The shape every real journal is in, and the fixture was not: the harness writes…, The walk back stops at the first commit that moved something, so it cannot… (+4 more)

### Community 269 - "BudgetTest"
Cohesion: 0.29
Nodes (4): BudgetTest, What a session can be told about its own spending, and when it cannot., A session log of the shape the assistant writes, and nothing else., A subagent's own transcript, beside the parent's, the way Claude Code writes it.

### Community 270 - "render"
Cohesion: 0.20
Nodes (9): calibration_line(), _duration(), The context budget and what the figures say about it, or that they cannot. The…, What a point cost on each model, with the date the prices were read. Printed…, A report anyone can read without opening a journal. The last section names what…, One line for the weekly report: which shadow the triage is in, and why., render(), render_context() (+1 more)

### Community 271 - "DeliveryChecksTest"
Cohesion: 0.29
Nodes (4): DeliveryChecksTest, broken(), Check runs in the shape gh reports them., runs()

### Community 273 - "ReceiptAttestsTheReviewedTreeTest"
Cohesion: 0.29
Nodes (3): What a receipt attests, and why attempt 8's exception was withdrawn. Attempt 8…, The order the procedure has to keep: the status goes in before the gate., ReceiptAttestsTheReviewedTreeTest

### Community 274 - "SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Amendments, Blocks, Context, Depends on, Description, SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants

### Community 275 - "execution"
Cohesion: 0.20
Nodes (10): _closes(), cost_cents(), execution(), _latest_route(), Each slice's window: what it cost and which records fall inside it. Keyed by…, Which slice this record's boundary closed, and the figures it carried. A…, What those output tokens cost on that model, or that nobody priced it. A whole…, What each slice was routed to, what it ran on and what it cost. Null rather… (+2 more)

### Community 276 - "SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token

### Community 277 - "The Seen harness"
Cohesion: 0.22
Nodes (8): Asking the graphs, Six rules you cannot infer, The context budget, The five stages, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 279 - "SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-110: Verify the hooks in a Codex session and close what SEEN-106 declined

### Community 280 - "The calibration window"
Cohesion: 0.40
Nodes (4): Not in the window, The calibration window, The routes, The triage

### Community 282 - "The Seen harness"
Cohesion: 0.22
Nodes (8): Asking the graphs, Six rules you cannot infer, The context budget, The five stages, The Seen harness, The three agents, The worked example, What the harness will refuse

### Community 284 - "ReplanCarriesForward"
Cohesion: 0.18
Nodes (7): named_plan(), A plan whose slices name different files, so the guard can tell them apart., SEEN-112 at its record 44: two slices green, a return, the same plan again.…, The one case the attempt boundary got right, and it is kept. A plan whose…, F3 of this ticket's second review, and a regression the carry forward caused.…, ReplanCarriesForward, ReworkAfterAReplanDoesNotAdvanceTheCount

### Community 285 - "APairIsJudgedByItsGreen"
Cohesion: 0.15
Nodes (9): APairIsJudgedByItsGreen, A red's standing rests on its green's tree, because it can have none of its…, The shape of every real red, and of this ticket's own red 34., Without this the acceptance below could be an exact match all along., The citation this ticket has been blocked on for two rounds., So the acceptance above is worth what the green's comparison is worth: a change…, The one thing this harness refuses outright, and the exemption is not a way…, A timeout is a fact about the runner rather than about the behaviour. (+1 more)

### Community 286 - "handoff.py"
Cohesion: 0.25
Nodes (8): hands_over_nothing(), _heading(), The handoff pack: the only thing that crosses a slice boundary. A session that…, What makes a slice the same slice across two acceptances of one plan., Why an automatically written pack would hand nothing over, or nothing. One…, The ticket's title, from the snapshot taken when it started., _slice_key(), _slices_accepted_by()

### Community 287 - "SEEN-113: Let a tdd record cite the evidence a return did not invalidate"
Cohesion: 0.18
Nodes (12): Acceptance criteria, Amendment, Blocks, Context, Depends on, Description, SEEN-113: Let a tdd record cite the evidence a return did not invalidate, Slices (+4 more)

### Community 288 - "PartialAnswerTest"
Cohesion: 0.31
Nodes (4): PartialAnswerTest, drops_clarified(), F1: a reply that left one question out must not cost the rest. A transport…, The other half of must_answer: a stage needs a judgement.

### Community 289 - ".evidence"
Cohesion: 0.20
Nodes (7): PositionIsDeclaredTest, A rework round spanning slices belongs to none of them, and says null., F3 of the ninth review: a rule a plan can miss by not naming a file. The rules…, Checks that declare the routed model, so the rule is what is under test.…, F2 of the fifth review: the route comparison is not skipped by omission. The…, RuleTrippedByTheWorkTest, transport()

### Community 290 - "DirectoryNamedSliceTest"
Cohesion: 0.39
Nodes (3): DirectoryNamedSliceTest, A rule a plan's wording cannot dodge. F6 of the third review: the patterns were…, `packages/core-utils` is a different package, not money arithmetic.

### Community 291 - "GuardIsLastTest"
Cohesion: 0.39
Nodes (4): What the building of it settled, GuardIsLastTest, A module's own run must collect its own tests. F3 of the sixth review: five…, The guard's line, found at column zero so a quotation is not one.

### Community 292 - "Outcome"
Cohesion: 0.33
Nodes (7): Outcome, _evidence(), How this ticket was worked: briefs from the scout, and the review's own kind.…, The evidence of the most recent accepted advance out of a stage., Slices planned at solution against slices proved at tdd. Proved counts every…, slices(), subagents()

### Community 293 - "SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide, Slices

### Community 294 - "PartlyGeneratedCopyTest"
Cohesion: 0.36
Nodes (4): PartlyGeneratedCopyTest, F1: one list answered two questions, and a security control fell through it.…, The part of the copy nobody generates, changed the way a session would., The other half, and the reason the two sets are separated rather than the hook…

### Community 295 - "ModesMustAgreeTest"
Cohesion: 0.43
Nodes (3): ModesMustAgreeTest, A ticket that plans no tests and then records a code TDD changed its mind., With a well-formed slice, so it is the disagreement that refuses.

### Community 296 - "withTheUniquenessReplacedBy"
Cohesion: 0.21
Nodes (8): answered(), checkedBlocksOf(), connect(), dropTheUniqueness(), migrationNamed(), replayedAgainstTheSchema(), where(), withTheUniquenessReplacedBy()

### Community 297 - "SEEN-101: Let a journal survive its ticket being renamed"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, Outcome, SEEN-101: Let a journal survive its ticket being renamed

### Community 298 - ".test_the_delivered_file_carries_a_cost_for_each_routed_slice"
Cohesion: 0.40
Nodes (3): DeliveredCostTest, F2 of SEEN-108's second review: criterion 4 names kpi.json, and delivery writes…, A session log for this walk, because a cost without tokens is null. The name is…

### Community 299 - "SEEN-129: List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-129: List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data, Slices

### Community 300 - "SEEN-130: Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-130: Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back, Slices

### Community 301 - "SEEN-131: Consumer invoices with VAT by destination and the OSS return"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-131: Consumer invoices with VAT by destination and the OSS return, Slices

### Community 302 - "SEEN-132: Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through"
Cohesion: 0.29
Nodes (7): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-132: Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through, Slices

### Community 303 - "tenancyGapsIn"
Cohesion: 0.38
Nodes (7): assertPopulated(), collapsed(), policiesIn(), rlsGapsIn(), tablesIn(), tenancyGapsIn(), tenantIdGapsIn()

### Community 304 - "TheDisclosureNamesWhatARedIsHeldTo"
Cohesion: 0.28
Nodes (4): What a red is held to, said where a reader of the rule will meet it. The second…, F3 of the fifth review. The list says a red is held to the route of the…, Within one attempt no accepted tdd record can mention the checks being cited,…, TheDisclosureNamesWhatARedIsHeldTo

### Community 305 - "record"
Cohesion: 0.25
Nodes (7): at(), A triage as SEEN-107 writes one: what it would have dropped, and its answers., F3: reopen voids the receipt, so the ticket is being worked again., record(), review_advance(), route_record(), triage_record()

### Community 306 - "The Codex review, and the four findings it returned"
Cohesion: 0.33
Nodes (6): The Codex review, and the four findings it returned, commentParagraphs(), defaultPrivilegesForClientRolesIn(), lastMemberClaimedInComments(), setSizesStatedInComments(), migrationColumnReferences()

### Community 307 - "SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack

### Community 308 - "GeneratedCopiesTest"
Cohesion: 0.43
Nodes (3): GeneratedCopiesTest, Files sync writes are named by naming their source. Found by running the triage…, Excluded from the check, not from the diff: it did change.

### Community 309 - "SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds

### Community 310 - "SEEN-115: Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-115: Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them

### Community 311 - "SEEN-116: Property-based and mutation tests on the money core, as a gate"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-116: Property-based and mutation tests on the money core, as a gate

### Community 312 - "SEEN-117: The spec session writes the RED; the implementer cannot touch it"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-117: The spec session writes the RED; the implementer cannot touch it

### Community 313 - "SEEN-118: A finding needs a failing test, taste is not a finding, and the third round is the founder's"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-118: A finding needs a failing test, taste is not a finding, and the third round is the founder's

### Community 314 - "SEEN-119: Independent slices run in parallel worktrees"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-119: Independent slices run in parallel worktrees

### Community 315 - "SEEN-120: Affected-only checks and a local CI that finishes in minutes"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-120: Affected-only checks and a local CI that finishes in minutes

### Community 316 - "F1, and what it says about the test that missed it"
Cohesion: 0.40
Nodes (4): F1, and what it says about the test that missed it, The deadlock this ticket had to break, and how, PartlySettledIsDocumentedTest, K2: the canonical document and the code must name the same checks.

### Community 317 - "SEEN-121: Bake-off: the TypeScript LSP plugin against codegraph, keep one"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-121: Bake-off: the TypeScript LSP plugin against codegraph, keep one

### Community 318 - "SEEN-122: Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-122: Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures

### Community 319 - "SEEN-123: Cap harness work at ten percent of a sprint and make every harness ticket state its payback"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-123: Cap harness work at ten percent of a sprint and make every harness ticket state its payback

### Community 320 - "SEEN-124: Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-124: Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due

### Community 321 - "SEEN-125: Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-125: Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack

### Community 322 - "SEEN-126: Register the storefront entity for EPR, GPSR responsible-person data and product liability cover"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-126: Register the storefront entity for EPR, GPSR responsible-person data and product liability cover

### Community 323 - "SEEN-127: Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-127: Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee

### Community 324 - "SEEN-128: Connection ownership and storefront mode on the trade record"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-128: Connection ownership and storefront mode on the trade record

### Community 325 - "SEEN-133: Returns, withdrawals and guarantee cases handled as the seller of record"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-133: Returns, withdrawals and guarantee cases handled as the seller of record

### Community 326 - "SEEN-134: Storefront pilot: one supplier live on Bol under Seen's account, first statement paid"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-134: Storefront pilot: one supplier live on Bol under Seen's account, first statement paid

### Community 327 - "SEEN-135: Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-135: Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings

### Community 328 - "SEEN-136: No test touches the clock, the network or randomness unfaked, and a flaky test is a defect"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-136: No test touches the clock, the network or randomness unfaked, and a flaky test is a defect

### Community 329 - "SEEN-137: One worked example per acceptance criterion before the solution stage, so the RED is a transcription"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-137: One worked example per acceptance criterion before the solution stage, so the RED is a transcription

### Community 330 - "SEEN-138: The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change"
Cohesion: 0.33
Nodes (6): Acceptance criteria, Blocks, Context, Depends on, Description, SEEN-138: The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change

### Community 331 - "current_slice"
Cohesion: 0.33
Nodes (6): current_slice(), last_declaration(), plan_of(), The count the most recent handoff declared since the plan was accepted. F1 in…, The slice a fresh session picks up, declared or counted from the journal. The…, The slice plan the solution record carries, or nothing.

### Community 332 - "verdict_routes"
Cohesion: 0.40
Nodes (3): What the third review found, Go-live or stay-shadow for the routes: the downgraded slices against the rest.…, verdict_routes()

### Community 333 - "SEEN-139: Hand the immutability guard forward to every migration that adds a table"
Cohesion: 0.40
Nodes (5): Acceptance criteria, Depends on, Description, SEEN-139: Hand the immutability guard forward to every migration that adds a table, Slices

### Community 334 - "claimsStillStanding"
Cohesion: 0.50
Nodes (5): claimsStillStanding(), linesWhere(), proseOf(), withdrawnClaimsStillStanding(), withdrawnShapeClaimsStillStanding()

## Knowledge Gaps
- **1169 isolated node(s):** `graphify-mcp`, `repowise`, `$schema`, `collection`, `sourceRoot` (+1164 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2394 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HarnessError` connect `HarnessError` to `TriageTest`, `.review`, `Repository`, `.start`, `TemplatePositionTest`, `RecordTest`, `cli.py`, `DeliveryWalk`, `.graph`, `DoctorTest`, `.at_tdd`, `DeliveryChecksTest`, `ReceiptAttestsTheReviewedTreeTest`, `MergeTest`, `CoverageTest`, `stub`, `.triage`, `FindingFileTest`, `DeclaredSliceTest`, `ReopenTest`, `StateForTest`, `ReplanCarriesForward`, `PartialAnswerTest`, `.evidence`, `PartlyGeneratedCopyTest`, `ModesMustAgreeTest`, `.advance_review`, `triage.py`, `AgentSyncTest`, `.evaluate`, `hooks.py`, `.reach_tdd`, `HookSyncTest`, `RedRuleTest`, `test_stage_gates.py`, `require`, `route_stub`, `CommandTest`, `FailedCheckStillAsksTest`, `.set_shadow`, `BookkeepingAfterReceiptTest`, `TddGateTest`, `NonCodeSolutionTest`, `.commit`, `.reach_tdd`, `GateTest`, `calibration.py`, `solution_evidence`, `doctor.py`, `test_triage.py`, `delivery.py`, `DiscardTest`, `routing.py`, `.refusal`, `.citing_all`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `require()` connect `require` to `graph.py`, `Repository`, `cli.py`, `HarnessError`, `current_slice`, `agents.py`, `calibration.py`, `triage.py`, `doctor.py`, `delivery.py`, `Outcome`, `routing.py`, `hooks.py`, `handoff.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `Outcome` connect `Outcome` to `require`, `providers/src/index.ts`, `app.module.ts`, `boundary.ts`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 96 inferred relationships involving `HarnessError` (e.g. with `Outcome` and `journals()`) actually correct?**
  _`HarnessError` has 96 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `require()` (e.g. with `Outcome` and `Outcome`) actually correct?**
  _`require()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Repository` (e.g. with `HarnessError` and `AgentSyncTest`) actually correct?**
  _`Repository` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify-mcp`, `repowise`, `$schema` to the rest of the system?**
  _1169 weakly-connected nodes found - possible documentation gaps or missing edges._