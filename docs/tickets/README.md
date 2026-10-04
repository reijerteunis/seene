# Tickets

140 tickets for the Seen MVP, one file per ticket, grouped by sprint. Each file carries YAML frontmatter (id, epic, sprint, gate, estimate, executor, changes_agent_action, marketplaces, depends_on, status) so the backlog can be filtered with grep or loaded by a script. Status values: todo, doing, review, done, parked. Update the status line in the frontmatter and the table when a ticket moves; `harness doctor` reports a status that disagrees with the ticket's journal. A started ticket's file is owned by this repository: the generator behind the council artifact rewrites only tickets still at todo.

Conventions: branch `claude/<id>-<slug>` (or `codex/`), commit messages `feat(<id>): ...`, `fix(<id>): ...`, `docs(<id>): ...`; a ticket is done only when every acceptance criterion is checked and the tests named in it run in CI.

## Sprint 0: Harness first, then foundations, three read connectors, ingest, day-0 registrations

24 Sep - 9 Oct 2026, gate G0, 56 tickets, 134 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-001](SEEN-001-register-amazon-sp-api-developer-and-file-ads.md) | Register Amazon SP-API developer and file Ads API application | E0 | 2 | human | todo |  |
| [SEEN-002](SEEN-002-obtain-ebay-production-keys-and-file.md) | Obtain eBay production keys and file Application Growth Check | E0 | 1 | human | todo |  |
| [SEEN-003](SEEN-003-obtain-bol-credentials-and-verify-oauth-grant.md) | Obtain Bol credentials and verify OAuth grant and rate limits | E0 | 1 | human | todo |  |
| [SEEN-004](SEEN-004-set-up-postmark-inbound-domain-and-stripe.md) | Set up Postmark inbound domain and Stripe account | E0 | 1 | human | todo |  |
| [SEEN-005](SEEN-005-review-partao-contract-and-draft-dpa-and-amazon.md) | Review Partao contract and draft DPA and Amazon data statement | E0 | 2 | human | todo |  |
| [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md) | Build the Seen harness CLI with staged journal and receipts | E10 | 8 | Claude Code | done |  |
| [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md) | Scaffold the pnpm turborepo monorepo with all six packages | E0 | 3 | Claude Code | done |  |
| [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md) | Set up the local Docker development environment | E0 | 3 | Claude Code | done | SEEN-006 |
| [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md) | Install graphify, build the repo graph and wire it into both assistants | E10 | 3 | Claude Code | done | SEEN-086 |
| [SEEN-096](SEEN-096-add-codegraph-and-route-the-graph-command.md) | Add codegraph and route the graph command to it | E10 | 1 | Claude Code | done | SEEN-086, SEEN-087 |
| [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md) | Add repowise and carry its risk answer into the gate | E10 | 2 | Claude Code | done | SEEN-086, SEEN-088 |
| [SEEN-099](SEEN-099-set-the-context-budget-and-measure-the-tools.md) | Set the context budget and measure what the tools changed | E10 | 1 | Claude Code | done | SEEN-096, SEEN-098, SEEN-091 |
| [SEEN-100](SEEN-100-let-a-gate-tell-an-open-question-from-an.md) | Let a gate tell an open question from an unknowable one | E10 | 1 | Claude Code | done | SEEN-088 |
| [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md) | Integrate Jev AI typed decisions into the harness gates | E10 | 3 | Claude Code | done | SEEN-086 |
| [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md) | Enforce the TDD gates in the harness | E10 | 3 | Claude Code | done | SEEN-006, SEEN-086 |
| [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md) | Verify delivery against CI and verify the merge against the receipt | E10 | 2 | Claude Code | done | SEEN-086, SEEN-093 |
| [SEEN-095](SEEN-095-check-ticket-status-against-its-own-journal.md) | Check a ticket's status against its own journal | E10 | 1 | Claude Code | done | SEEN-086, SEEN-094 |
| [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md) | Add harness security controls: secrets, permissions, injection, supply chain | E10 | 3 | Claude Code | done | SEEN-086, SEEN-088 |
| [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md) | Collect harness KPIs per ticket and produce weekly and sprint reports | E10 | 3 | Claude Code | done | SEEN-086, SEEN-089 |
| [SEEN-093](SEEN-093-add-harness-reopen-to-void-a-receipt-before.md) | Add harness reopen to void a receipt before merge | E10 | 2 | Claude Code | done | SEEN-086 |
| [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md) | Sync the harness skill to Claude Code and Codex and retire the Seene leftovers | E10 | 2 | Claude Code | done | SEEN-086, SEEN-087, SEEN-088, SEEN-089, SEEN-090, SEEN-091 |
| [SEEN-101](SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md) | Let a journal survive its ticket being renamed | E10 | 1 | Claude Code | done | SEEN-088 |
| [SEEN-102](SEEN-102-decide-on-the-repowise-pr-bot.md) | Decide on the repowise PR bot for a private repository | E10 | 0 | human | done | SEEN-098 |
| [SEEN-103](SEEN-103-declare-non-code-mode-at-the-solution-stage.md) | Declare non-code mode at the solution stage, not after it | E10 | 1 | Claude Code | done | SEEN-086 |
| [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md) | Cap a session at one slice: the slice plan, the budget and the handoff pack | E10 | 3 | Claude Code | done | SEEN-099, SEEN-103, SEEN-091 |
| [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md) | Give the scout and the reviewer their own context as subagents in both assistants | E10 | 3 | Claude Code | done | SEEN-104, SEEN-092, SEEN-098 |
| [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md) | Enforce the harness with hooks in both assistants, generated from one source | E10 | 3 | Claude Code | done | SEEN-104, SEEN-092 |
| [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md) | Let Jev settle what the review can settle before a model reads the diff | E10 | 3 | Claude Code | done | SEEN-105, SEEN-098, SEEN-104 |
| [SEEN-108](SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md) | Route each slice to a model and an effort at solution, by rule first and by Jev second | E10 | 2 | Claude Code | done | SEEN-104, SEEN-105, SEEN-098 |
| [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md) | Calibrate the review triage and the routes on ten tickets before either saves a token | E10 | 2 | Claude Code | done | SEEN-107, SEEN-108 |
| [SEEN-110](SEEN-110-verify-the-hooks-in-a-codex-session-and-close.md) | Verify the hooks in a Codex session and close what SEEN-106 declined | E10 | 2 | human | doing | SEEN-106 |
| [SEEN-111](SEEN-111-hold-a-slice-to-the-context-it-was-routed-to.md) | Hold a slice to the context it was routed to, and price it before it is worked | E10 | 3 | Claude Code | done | SEEN-104, SEEN-105, SEEN-108 |
| [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md) | Run a ticket from clarify to merge in one go, asking only what it cannot decide | E10 | 3 | Claude Code | doing | SEEN-104, SEEN-105, SEEN-107, SEEN-111 |
| [SEEN-113](SEEN-113-let-a-tdd-record-cite-the-evidence-a-return.md) | Let a tdd record cite the evidence a return did not invalidate | E10 | 2 | Claude Code | review | SEEN-104, SEEN-112 |
| [SEEN-114](SEEN-114-turn-every-recurring-finding-into-a-rule-the.md) | Turn every recurring finding into a rule the pre-commit hook runs in seconds | E10 | 3 | Claude Code | todo | SEEN-090, SEEN-107 |
| [SEEN-115](SEEN-115-generate-the-marketplace-clients-from-the.md) | Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them | E10 | 3 | Claude Code | todo | SEEN-009 |
| [SEEN-116](SEEN-116-property-based-and-mutation-tests-on-the-money.md) | Property-based and mutation tests on the money core, as a gate | E10 | 3 | Claude Code | done | SEEN-089 |
| [SEEN-117](SEEN-117-the-spec-session-writes-the-red-the-implementer.md) | The spec session writes the RED; the implementer cannot touch it | E10 | 2 | Claude Code | todo | SEEN-105, SEEN-106, SEEN-111 |
| [SEEN-118](SEEN-118-a-finding-needs-a-failing-test-taste-is-not-a.md) | A finding needs a failing test, taste is not a finding, and the third round is the founder's | E10 | 2 | Claude Code | todo | SEEN-107, SEEN-113 |
| [SEEN-119](SEEN-119-independent-slices-run-in-parallel-worktrees.md) | Independent slices run in parallel worktrees | E10 | 3 | Claude Code | todo | SEEN-111, SEEN-112 |
| [SEEN-120](SEEN-120-affected-only-checks-and-a-local-ci-that.md) | Affected-only checks and a local CI that finishes in minutes | E10 | 2 | Claude Code | todo | SEEN-097, SEEN-094 |
| [SEEN-121](SEEN-121-bake-off-the-typescript-lsp-plugin-against.md) | Bake-off: the TypeScript LSP plugin against codegraph, keep one | E10 | 2 | Claude Code | todo | SEEN-099, SEEN-096 |
| [SEEN-122](SEEN-122-golden-path-end-to-end-tests-on-the-docker.md) | Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures | E10 | 3 | Claude Code | todo | SEEN-097, SEEN-115, SEEN-035 |
| [SEEN-123](SEEN-123-cap-harness-work-at-ten-percent-of-a-sprint-and.md) | Cap harness work at ten percent of a sprint and make every harness ticket state its payback | E10 | 1 | Claude Code | todo | SEEN-091 |
| [SEEN-135](SEEN-135-branded-money-and-ids-one-schema-per-boundary.md) | Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings | E10 | 2 | Claude Code | todo | SEEN-114, SEEN-006 |
| [SEEN-136](SEEN-136-no-test-touches-the-clock-the-network-or.md) | No test touches the clock, the network or randomness unfaked, and a flaky test is a defect | E10 | 2 | Claude Code | todo | SEEN-089, SEEN-097 |
| [SEEN-137](SEEN-137-one-worked-example-per-acceptance-criterion.md) | One worked example per acceptance criterion before the solution stage, so the RED is a transcription | E10 | 1 | Claude Code | todo | SEEN-088, SEEN-117 |
| [SEEN-138](SEEN-138-the-harness-has-its-own-regression-suite-five.md) | The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change | E10 | 3 | Claude Code | todo | SEEN-091, SEEN-104, SEEN-105 |
| [SEEN-140](SEEN-140-one-answer-to-whether-a-slices-plan-covers-a.md) | One answer to whether a slice's plan covers a path | E10 | 1 | Claude Code | done | none |
| [SEEN-141](SEEN-141-hold-a-figure-in-a-tdd-record-to-the.md) | Hold a figure in a tdd record to the check it cites | E10 | 2 | Claude Code | todo | SEEN-114 |
| [SEEN-142](SEEN-142-keep-the-triage-s-request-inside-what-the-api.md) | Keep the triage's request inside what the API accepts, and say so when it cannot | E10 | 2 | Claude Code | todo | SEEN-107, SEEN-109 |
| [SEEN-144](SEEN-144-tell-a-path-the-branch-deleted-from-a-typo-in.md) | Tell a path the branch deleted from a typo in the plan | E10 | 2 | Claude Code | todo | SEEN-113 |
| [SEEN-145](SEEN-145-count-a-review-finding-once-however-the.md) | Count a review finding once, however the record that carries it names it | E10 | 1 | Claude Code | done | SEEN-091, SEEN-107, SEEN-109 |
| [SEEN-146](SEEN-146-assign-a-later-review-s-findings-by-maximum.md) | Match a later review's findings as a whole, so the order they are listed in never changes a count | E10 | 2 | Claude Code | done | SEEN-145 |
| [SEEN-147](SEEN-147-a-drafter-writes-the-clarify-and-solution.md) | A drafter writes the clarify and solution records, so the orchestrator holds only the gate answers | E10 | 3 | Claude Code | todo | SEEN-105, SEEN-112 |
| [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md) | Create trade-record schema v1 with tenant_id and RLS on every table | E0 | 5 | Claude Code | done | SEEN-006, SEEN-092, SEEN-094 |
| [SEEN-139](SEEN-139-hand-the-immutability-guard-forward-to-every.md) | Hand the immutability guard forward to every migration that adds a table | E0 | 2 | Claude Code | todo | SEEN-008 |
| [SEEN-143](SEEN-143-compile-the-trade-record-schema-and-its-tests.md) | Compile the trade-record schema and its tests, which no compiler reads today | E0 | 3 | Claude Code | todo | SEEN-008, SEEN-114 |
| [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md) | Define connector interface, capability matrix and credential access | E1 | 5 | Claude Code | todo | SEEN-006, SEEN-008 |
| [SEEN-010](SEEN-010-add-per-marketplace-rate-limiting-with-header.md) | Add per-marketplace rate limiting with header-driven backoff | E1 | 3 | Claude Code | todo | SEEN-009 |
| [SEEN-011](SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md) | Build Bol Retailer API v10 connector for orders to commissions | E1 | 5 | Claude Code | todo | SEEN-003, SEEN-009, SEEN-010, SEEN-115 |
| [SEEN-012](SEEN-012-build-ebay-connector-for-orders-returns.md) | Build eBay connector for orders, returns, transactions and payouts | E1 | 5 | Claude Code | todo | SEEN-002, SEEN-009, SEEN-010, SEEN-115 |
| [SEEN-013](SEEN-013-build-amazon-sp-api-connector-for-orders.md) | Build Amazon SP-API connector for orders, reports and Finances | E1 | 5 | Claude Code | todo | SEEN-001, SEEN-009, SEEN-010, SEEN-115 |
| [SEEN-014](SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md) | Run ingest workers with idempotent upserts, raw archive and cadences | E1 | 5 | Claude Code | todo | SEEN-008, SEEN-011, SEEN-012, SEEN-013 |

## Sprint 1: Reconciliation engine, fee expectations, findings, audit PDF

12 - 23 Oct 2026, gate G1, 11 tickets, 37 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-015](SEEN-015-verify-amazon-report-names-and-finances.md) | Verify Amazon report names and Finances transactions version | E1 | 1 | human | todo | SEEN-013 |
| [SEEN-016](SEEN-016-encode-fee-schedules-per-marketplace-and.md) | Encode fee schedules per marketplace and category in core | E2 | 3 | Claude Code | todo | SEEN-008, SEEN-116 |
| [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md) | Compute fee_expectations per order line from schedules and APIs | E2 | 5 | Claude Code | todo | SEEN-011, SEEN-014, SEEN-016, SEEN-116 |
| [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md) | Match settlement_lines to order_lines deterministically | E2 | 5 | Claude Code | todo | SEEN-014, SEEN-116 |
| [SEEN-019](SEEN-019-implement-fee-detectors-as-pure-tested-functions.md) | Implement fee detectors as pure tested functions | E2 | 5 | Claude Code | todo | SEEN-017, SEEN-018, SEEN-116 |
| [SEEN-020](SEEN-020-implement-shipment-return-and-inventory.md) | Implement shipment, return and inventory detectors | E2 | 5 | Claude Code | todo | SEEN-015, SEEN-018, SEEN-116 |
| [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md) | Persist findings with rule, confidence, evidence refs and deadline | E2 | 3 | Claude Code | todo | SEEN-019, SEEN-020 |
| [SEEN-022](SEEN-022-generate-the-audit-pdf-with-scorecard-and-line.md) | Generate the audit PDF with scorecard and line annex | E2 | 5 | Claude Code | todo | SEEN-021 |
| [SEEN-023](SEEN-023-measure-the-recoverable-pool-per-marketplace.md) | Measure the recoverable pool per marketplace | E2 | 3 | Claude Code | todo | SEEN-021 |
| [SEEN-024](SEEN-024-ship-ops-console-v1-for-tenants-connections-and.md) | Ship ops console v1 for tenants, connections and sync status | E5 | 3 | Claude Code | todo | SEEN-014, SEEN-021 |
| [SEEN-025](SEEN-025-run-three-real-90-day-audits-and-deliver-the.md) | Run three real 90-day audits and deliver the PDFs | E2 | 2 | human | todo | SEEN-022, SEEN-023 |

## Sprint 2: Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching

26 Oct - 6 Nov 2026, gate G2, 14 tickets, 44 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-026](SEEN-026-verify-bol-compensation-request-form-structure.md) | Verify Bol compensation request form structure | E3 | 1 | human | todo | SEEN-003 |
| [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md) | Build the claims rail with api, assisted and track modes | E3 | 5 | Claude Code | todo | SEEN-021, SEEN-026 |
| [SEEN-028](SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md) | Contest eBay payment disputes and cases by API | E3 | 5 | Claude Code | todo | SEEN-012, SEEN-027 |
| [SEEN-029](SEEN-029-build-the-bol-assisted-case-pack-with-tracking.md) | Build the Bol assisted case pack with tracking | E3 | 3 | Claude Code | todo | SEEN-026, SEEN-027 |
| [SEEN-030](SEEN-030-build-the-amazon-assisted-case-pack-with-report.md) | Build the Amazon assisted case pack with report tracking | E3 | 3 | Claude Code | todo | SEEN-027 |
| [SEEN-031](SEEN-031-match-credits-to-claims-as-the-only-billable.md) | Match credits to claims as the only billable event | E3 | 3 | Claude Code | todo | SEEN-027 |
| [SEEN-032](SEEN-032-write-append-only-audit-events-before-every.md) | Write append-only audit_events before every side effect | E4 | 2 | Claude Code | todo | SEEN-008 |
| [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md) | Implement policy gate v1 with caps and reversibility | E4 | 5 | Claude Code | todo | SEEN-032, SEEN-116 |
| [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md) | Build agent runtime v1 with the fixed tool set and cost accounting | E4 | 5 | Claude Code | todo | SEEN-027, SEEN-032, SEEN-033 |
| [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md) | Build the approval inbox with approve, edit and reject | E4 | 5 | Claude Code | todo | SEEN-033, SEEN-034 |
| [SEEN-036](SEEN-036-create-the-eval-set-of-30-real-findings-with.md) | Create the eval set of 30 real findings with expected drafts | E4 | 3 | Claude Code | todo | SEEN-034 |
| [SEEN-037](SEEN-037-file-the-first-ten-claims-across-two.md) | File the first ten claims across two marketplaces from the inbox | E3 | 2 | human | todo | SEEN-028, SEEN-029, SEEN-030, SEEN-035 |
| [SEEN-007](SEEN-007-go-live-on-google-cloud-after-the-go-no-go.md) | Go live on Google Cloud after the go/no-go decision | E0 | 5 | Claude Code | todo | SEEN-097, SEEN-014 |
| [SEEN-124](SEEN-124-decide-the-storefront-legal-model-with-the-tax.md) | Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due | E11 | 2 | human | todo | SEEN-005 |

## Sprint 3: Reconcile module, Stripe billing, statements, Shopify

9 - 20 Nov 2026, gate G3, 11 tickets, 36 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-038](SEEN-038-verify-shopify-payments-payout-scopes-and.md) | Verify Shopify Payments payout scopes and create the custom app | E1 | 1 | human | todo | SEEN-009 |
| [SEEN-039](SEEN-039-create-stripe-customers-with-sepa-and-card-and.md) | Create Stripe customers with SEPA and card and handle webhooks | E6 | 5 | Claude Code | todo | SEEN-004, SEEN-008 |
| [SEEN-040](SEEN-040-issue-invoices-with-recovery-share-lines-from.md) | Issue invoices with recovery-share lines from credited claims only | E6 | 5 | Claude Code | todo | SEEN-031, SEEN-039 |
| [SEEN-041](SEEN-041-generate-and-send-the-monthly-statement-pdf.md) | Generate and send the monthly statement PDF | E6 | 5 | Claude Code | todo | SEEN-004, SEEN-040 |
| [SEEN-042](SEEN-042-ship-the-reconcile-module-with-margin-and-fee.md) | Ship the Reconcile module with margin and fee-change alerts | E7 | 5 | Claude Code | todo | SEEN-018, SEEN-021 |
| [SEEN-043](SEEN-043-export-finance-csv-of-settlements-and-matched.md) | Export finance CSV of settlements and matched lines | E7 | 3 | Claude Code | todo | SEEN-018 |
| [SEEN-044](SEEN-044-build-the-shopify-admin-graphql-connector-as.md) | Build the Shopify Admin GraphQL connector as product and stock truth | E1 | 5 | Claude Code | todo | SEEN-009, SEEN-014, SEEN-038 |
| [SEEN-045](SEEN-045-add-module-switches-per-tenant-with-scheduling.md) | Add module switches per tenant with scheduling and billing hooks | E7 | 3 | Claude Code | todo | SEEN-033, SEEN-040 |
| [SEEN-046](SEEN-046-build-customer-facing-findings-and-claims-views.md) | Build customer-facing findings and claims views | E5 | 5 | Claude Code | todo | SEEN-027, SEEN-031, SEEN-035 |
| [SEEN-047](SEEN-047-issue-the-first-invoice-and-send-the-signed.md) | Issue the first invoice and send the signed statement | E6 | 1 | human | todo | SEEN-040, SEEN-041, SEEN-042, SEEN-045 |
| [SEEN-125](SEEN-125-open-seen-s-own-seller-accounts-on-bol-and.md) | Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack | E11 | 2 | human | todo | SEEN-124 |

## Sprint 4: Comply v1, Kaufland connector, listing fixes by API

23 Nov - 4 Dec 2026, gate G4, 12 tickets, 36 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-048](SEEN-048-verify-kaufland-settlement-and-ticket-endpoints.md) | Verify Kaufland settlement and ticket endpoints and obtain keys | E1 | 1 | human | todo | SEEN-009 |
| [SEEN-049](SEEN-049-encode-listing-spec-rules-per-marketplace-in.md) | Encode listing spec rules per marketplace in core | E7 | 5 | Claude Code | todo | SEEN-008 |
| [SEEN-050](SEEN-050-ingest-listings-with-content-hash-and-drift.md) | Ingest listings with content hash and drift detection | E7 | 5 | Claude Code | todo | SEEN-044, SEEN-049 |
| [SEEN-051](SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md) | Add propose_listing_fix and apply_listing_fix tools with diff | E7 | 5 | Claude Code | todo | SEEN-033, SEEN-034, SEEN-045, SEEN-050 |
| [SEEN-052](SEEN-052-write-listing-content-through-bol-and-ebay-apis.md) | Write listing content through Bol and eBay APIs | E1 | 5 | Claude Code | todo | SEEN-051 |
| [SEEN-053](SEEN-053-write-listing-content-through-amazon-listings.md) | Write listing content through Amazon Listings Items and Feeds | E1 | 5 | Claude Code | todo | SEEN-051 |
| [SEEN-054](SEEN-054-build-the-kaufland-connector-with-tickets-as.md) | Build the Kaufland connector with tickets as the claims rail | E1 | 5 | Claude Code | todo | SEEN-009, SEEN-014, SEEN-027, SEEN-048, SEEN-115 |
| [SEEN-055](SEEN-055-monitor-unauthorised-sellers-from-competing.md) | Monitor unauthorised sellers from competing offers | E7 | 3 | Claude Code | todo | SEEN-010, SEEN-050 |
| [SEEN-056](SEEN-056-show-comply-defects-and-fix-diffs-in-the-inbox.md) | Show Comply defects and fix diffs in the inbox | E5 | 3 | Claude Code | todo | SEEN-035, SEEN-051 |
| [SEEN-057](SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md) | Verify listing fixes on three marketplaces and file Kaufland tickets | E7 | 2 | human | todo | SEEN-052, SEEN-053, SEEN-054, SEEN-056 |
| [SEEN-126](SEEN-126-register-the-storefront-entity-for-epr-gpsr.md) | Register the storefront entity for EPR, GPSR responsible-person data and product liability cover | E11 | 2 | human | todo | SEEN-124 |
| [SEEN-127](SEEN-127-write-the-storefront-agreement-supply-terms-the.md) | Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee | E11 | 1 | human | todo | SEEN-124, SEEN-126 |

## Sprint 5: Serve v1, forwarded mailbox, trust ramp, Otto connector

7 - 18 Dec 2026, gate G5, 10 tickets, 36 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-058](SEEN-058-verify-ebay-messaging-deprecation-and-choose.md) | Verify eBay messaging deprecation and choose the message path | E1 | 1 | human | todo | SEEN-012 |
| [SEEN-059](SEEN-059-verify-otto-rate-limits-and-obtain-otto-api-keys.md) | Verify Otto rate limits and obtain Otto API keys | E1 | 1 | human | todo | SEEN-009 |
| [SEEN-060](SEEN-060-build-the-otto-connector-for-orders-returns.md) | Build the Otto connector for orders, returns, receipts and messages | E1 | 5 | Claude Code | todo | SEEN-009, SEEN-014, SEEN-027, SEEN-059, SEEN-115 |
| [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md) | Ingest message_threads from Amazon, eBay, Kaufland and Otto | E7 | 5 | Claude Code | todo | SEEN-054, SEEN-058, SEEN-060 |
| [SEEN-062](SEEN-062-parse-the-forwarded-mailbox-via-postmark.md) | Parse the forwarded mailbox via Postmark inbound into threads | E7 | 5 | Claude Code | todo | SEEN-004, SEEN-027, SEEN-061 |
| [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md) | Add reply_message tool bound to tenant service policies | E7 | 5 | Claude Code | todo | SEEN-033, SEEN-034, SEEN-061, SEEN-062 |
| [SEEN-064](SEEN-064-apply-return-and-cancellation-decisions-through.md) | Apply return and cancellation decisions through returns APIs | E7 | 5 | Claude Code | todo | SEEN-011, SEEN-012, SEEN-013, SEEN-033, SEEN-034 |
| [SEEN-065](SEEN-065-implement-the-trust-ramp-with-autonomy-per.md) | Implement the trust ramp with autonomy per action type | E4 | 5 | Claude Code | todo | SEEN-033, SEEN-035 |
| [SEEN-066](SEEN-066-track-claim-and-dispute-deadlines-with-alerts.md) | Track claim and dispute deadlines with alerts | E3 | 3 | Claude Code | todo | SEEN-021, SEEN-028 |
| [SEEN-067](SEEN-067-show-serve-threads-and-drafts-in-the-inbox.md) | Show Serve threads and drafts in the inbox | E5 | 3 | Claude Code | todo | SEEN-035, SEEN-063, SEEN-065 |

## Sprint 6: Price module v1: competitor snapshots, net-margin model, governor, headroom meter

4 - 15 Jan 2027, gate G6, 9 tickets, 36 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-068](SEEN-068-verify-the-kaufland-virtual-buy-box-endpoint.md) | Verify the Kaufland virtual buy box endpoint | E8 | 1 | human | todo | SEEN-054 |
| [SEEN-069](SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md) | Snapshot competing offers from Bol by EAN and eBay by GTIN | E8 | 5 | Claude Code | todo | SEEN-010, SEEN-011, SEEN-012, SEEN-055 |
| [SEEN-070](SEEN-070-snapshot-amazon-pricing-on-a-tiered-clock.md) | Snapshot Amazon pricing on a tiered clock | E8 | 5 | Claude Code | todo | SEEN-010, SEEN-013, SEEN-015 |
| [SEEN-071](SEEN-071-model-net-margin-per-marketplace-from-cost.md) | Model net margin per marketplace from cost layers | E8 | 5 | Claude Code | todo | SEEN-017, SEEN-044 |
| [SEEN-072](SEEN-072-implement-the-price-governor-with-bands.md) | Implement the price governor with bands, ceilings and cooldowns | E8 | 5 | Claude Code | todo | SEEN-033, SEEN-071 |
| [SEEN-073](SEEN-073-write-prices-through-bol-offers-and-ebay.md) | Write prices through Bol Offers and eBay Inventory offers | E1 | 3 | Claude Code | todo | SEEN-011, SEEN-012 |
| [SEEN-074](SEEN-074-add-propose-price-and-apply-price-tools-with.md) | Add propose_price and apply_price tools with buy-box tracking | E8 | 5 | Claude Code | todo | SEEN-034, SEEN-045, SEEN-069, SEEN-072, SEEN-073 |
| [SEEN-075](SEEN-075-meter-headroom-entries-and-show-the-price-view.md) | Meter headroom_entries and show the Price view | E8 | 5 | Claude Code | todo | SEEN-069, SEEN-074 |
| [SEEN-076](SEEN-076-run-the-daily-bol-buy-box-feedback-loop.md) | Run the daily Bol buy-box feedback loop | E8 | 3 | Claude Code | todo | SEEN-069, SEEN-074 |

## Sprint 7: Grow v1, retailer read-only view, hardening, day-120 metrics

18 - 29 Jan 2027, gate G7, 10 tickets, 39 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-077](SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md) | Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted | E9 | 5 | Claude Code | todo | SEEN-001, SEEN-002, SEEN-009, SEEN-014 |
| [SEEN-078](SEEN-078-attribute-ad-cost-into-margin-and-publish-the.md) | Attribute ad cost into margin and publish the weekly Grow report | E9 | 5 | Claude Code | todo | SEEN-045, SEEN-071, SEEN-077 |
| [SEEN-079](SEEN-079-propose-campaign-budgets-through-the-gate-no.md) | Propose campaign budgets through the gate, no autonomous creation | E9 | 3 | Claude Code | todo | SEEN-033, SEEN-034, SEEN-077 |
| [SEEN-080](SEEN-080-build-the-retailer-read-only-view-via-a-scoped.md) | Build the retailer read-only view via a scoped link | E9 | 5 | Claude Code | todo | SEEN-046 |
| [SEEN-081](SEEN-081-load-test-ingest-on-50-tenants-and-run-rate.md) | Load test ingest on 50 tenants and run rate-limit chaos | E9 | 5 | Claude Code | todo | SEEN-010, SEEN-014 |
| [SEEN-082](SEEN-082-run-rls-penetration-tests-and-the-restore-drill.md) | Run RLS penetration tests and the restore drill | E9 | 5 | Claude Code | todo | SEEN-008, SEEN-032 |
| [SEEN-083](SEEN-083-expire-amazon-pii-after-30-days-and-delete.md) | Expire Amazon PII after 30 days and delete tenants on request | E9 | 3 | Claude Code | todo | SEEN-013, SEEN-027 |
| [SEEN-084](SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md) | Build the day-120 metrics dashboard and CSV export | E9 | 5 | Claude Code | todo | SEEN-034, SEEN-040, SEEN-045, SEEN-065 |
| [SEEN-085](SEEN-085-run-restore-drill-close-pen-test-findings-sign.md) | Run restore drill, close pen-test findings, sign metrics pack | E9 | 2 | human | todo | SEEN-081, SEEN-082, SEEN-084 |
| [SEEN-128](SEEN-128-connection-ownership-and-storefront-mode-on-the.md) | Connection ownership and storefront mode on the trade record | E11 | 3 | Claude Code | todo | SEEN-009, SEEN-124, SEEN-125 |

## Sprint 8: Storefront: Seen as seller of record, one supplier live on Bol

1 - 12 Feb 2027, gate G8, 6 tickets, 23 build points.

| Ticket | Title | Epic | Pts | Executor | Status | Depends on |
|---|---|---|---|---|---|---|
| [SEEN-129](SEEN-129-list-a-supplier-s-catalogue-under-seen-s.md) | List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data | E11 | 5 | Claude Code | todo | SEEN-128, SEEN-126, SEEN-044, SEEN-052 |
| [SEEN-130](SEEN-130-dropship-flow-a-purchase-order-to-the-supplier.md) | Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back | E11 | 5 | Claude Code | todo | SEEN-128, SEEN-014, SEEN-044 |
| [SEEN-131](SEEN-131-consumer-invoices-with-vat-by-destination-and.md) | Consumer invoices with VAT by destination and the OSS return | E11 | 5 | Claude Code | todo | SEEN-128, SEEN-124, SEEN-039 |
| [SEEN-132](SEEN-132-supplier-statements-and-payouts-net-proceeds.md) | Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through | E11 | 5 | Claude Code | todo | SEEN-128, SEEN-131, SEEN-040, SEEN-127 |
| [SEEN-133](SEEN-133-returns-withdrawals-and-guarantee-cases-handled.md) | Returns, withdrawals and guarantee cases handled as the seller of record | E11 | 3 | Claude Code | todo | SEEN-128, SEEN-063, SEEN-064, SEEN-131 |
| [SEEN-134](SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md) | Storefront pilot: one supplier live on Bol under Seen's account, first statement paid | E11 | 2 | human | todo | SEEN-129, SEEN-130, SEEN-131, SEEN-132, SEEN-133 |

## Epics

| Epic | Name | Goal | Tickets |
|---|---|---|---|
| E0 | Foundations and registrations | Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later. | SEEN-001, SEEN-002, SEEN-003, SEEN-004, SEEN-005, SEEN-006, SEEN-097, SEEN-008, SEEN-139, SEEN-143, SEEN-007 |
| E1 | Connectors and ingest | Ingest orders, shipments, returns, settlements and listings from Bol, Amazon, eBay, Kaufland, Otto and Shopify into one idempotent, tenant-isolated trade record. | SEEN-009, SEEN-010, SEEN-011, SEEN-012, SEEN-013, SEEN-014, SEEN-015, SEEN-038, SEEN-044, SEEN-048, SEEN-052, SEEN-053, SEEN-054, SEEN-058, SEEN-059, SEEN-060, SEEN-073 |
| E2 | Reconciliation, findings and audit | Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool. | SEEN-016, SEEN-017, SEEN-018, SEEN-019, SEEN-020, SEEN-021, SEEN-022, SEEN-023, SEEN-025 |
| E3 | Claims rail and evidence | File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence. | SEEN-026, SEEN-027, SEEN-028, SEEN-029, SEEN-030, SEEN-031, SEEN-037, SEEN-066 |
| E4 | Agent runtime, policy gate, approvals and audit log | Run every agent action through one policy gate with caps, reversibility and a trust ramp, approved from the inbox and written to an append-only audit log before the side effect. | SEEN-032, SEEN-033, SEEN-034, SEEN-035, SEEN-036, SEEN-065 |
| E5 | Customer inbox and ops console | Give tenants one inbox for approvals, findings, claims and statements and give ops one console for tenants, connections, runs and costs. | SEEN-024, SEEN-046, SEEN-056, SEEN-067 |
| E6 | Billing, statements and metering | Bill the recovery share only on credits matched to claims, issue Stripe invoices and a signed monthly statement from the same tables that hold the ledger. | SEEN-039, SEEN-040, SEEN-041, SEEN-047 |
| E7 | Modules: Reconcile, Comply, Serve | Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record. | SEEN-042, SEEN-043, SEEN-045, SEEN-049, SEEN-050, SEEN-051, SEEN-055, SEEN-057, SEEN-061, SEEN-062, SEEN-063, SEEN-064 |
| E8 | Price module | Snapshot competing offers, model net margin per marketplace and move prices inside bands through a governor, counting headroom captured from ingested orders. | SEEN-068, SEEN-069, SEEN-070, SEEN-071, SEEN-072, SEEN-074, SEEN-075, SEEN-076 |
| E9 | Grow, retailer view, hardening and day-120 metrics | Read ad reports into margin, give retailers a scoped read-only view, pass load, security and restore drills, and produce the day-120 metrics pack. | SEEN-077, SEEN-078, SEEN-079, SEEN-080, SEEN-081, SEEN-082, SEEN-083, SEEN-084, SEEN-085 |
| E10 | Development harness | Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket. | SEEN-086, SEEN-087, SEEN-096, SEEN-098, SEEN-099, SEEN-100, SEEN-088, SEEN-089, SEEN-094, SEEN-095, SEEN-090, SEEN-091, SEEN-093, SEEN-092, SEEN-101, SEEN-102, SEEN-103, SEEN-104, SEEN-105, SEEN-106, SEEN-107, SEEN-108, SEEN-109, SEEN-110, SEEN-111, SEEN-112, SEEN-113, SEEN-114, SEEN-115, SEEN-116, SEEN-117, SEEN-118, SEEN-119, SEEN-120, SEEN-121, SEEN-122, SEEN-123, SEEN-135, SEEN-136, SEEN-137, SEEN-138, SEEN-140, SEEN-141, SEEN-142, SEEN-144, SEEN-145, SEEN-146, SEEN-147 |
| E11 | Seller of record | Let a brand sell through Seen's own marketplace accounts when it cannot be the seller itself: Seen carries the seller obligations, the brand supplies and ships, and the trade record, the modules and the recovery loop run unchanged. | SEEN-124, SEEN-125, SEEN-126, SEEN-127, SEEN-128, SEEN-129, SEEN-130, SEEN-131, SEEN-132, SEEN-133, SEEN-134 |
