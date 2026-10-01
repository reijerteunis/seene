# Seen: Claude Code entry point

Seen (tryseen.com) is an AI agent that runs a brand's trading relationship with online marketplaces end to end: it connects to Bol, Amazon, eBay, Kaufland and Otto through their official APIs, keeps one reconciled trade record of orders, shipments, returns and settlements, recovers the money the marketplaces kept in error, and then takes over reconciliation, listing compliance, correspondence, pricing and advertising as modules on the same record. Working name during the council rounds: Channel Trade Ledger. This repository previously held the Seene project; that code was removed on 23 September 2026 and everything under `docs/` describes Seen.

Read the three documents in this order before writing code: the PRD for what and why, the architecture for how, the development plan for when. Then read the harness workflow, because every ticket is worked through it. Then open the ticket you are working on. Everything else in `docs/` is indexed below.

## Ground rules

- API-native only. Every marketplace action goes through an official API or is handed to a human as a prepared one-click case pack. Never build or suggest browser automation.
- Every agent action passes the policy gate (autonomous, approval, refuse) and writes its audit event before the side effect. Refunds, purchase orders, account settings and delistings are never agent actions.
- Deterministic code reconciles, the model reasons: matching, fee expectation and euro arithmetic are pure functions with tests in `packages/core`; classification, drafting and correspondence are the model behind the fixed tool set in `packages/agent`.
- Every table carries `tenant_id` with row-level security. Credentials live in Secret Manager per connection, never in the database or in code.
- A credit is billable only as an ingested settlement line linked to a claim. Never let a person or the agent create a billable event directly.
- Stack: pnpm and turborepo monorepo, `apps/api` (NestJS), `apps/worker` (NestJS + BullMQ on Redis), `apps/web` (Next.js, Supabase Auth), `packages/core`, `packages/connectors`, `packages/agent`; Supabase Postgres. Node version in `.nvmrc`.
- Local first, cloud by decision. Development and the first pilots run on the local Docker environment (`pnpm dev:up`: Supabase CLI stack, Redis, Mailpit, telemetry collector); CI runs the same services. Nothing is deployed to Google Cloud until Ruud records a go decision in the SEEN-007 journal. Code never imports a cloud SDK outside the provider packages: secrets, storage and telemetry are abstractions selected by configuration (.env.local, local Supabase Storage and the console now; Secret Manager, the Supabase EU project and Cloud Logging after go-live). Sync cadences are BullMQ repeatable jobs, not Cloud Scheduler.
- Amounts are in cents as integers with a currency code; use `EUR` in text, never the euro sign in code comments or docs. British spelling. No em dashes or en dashes anywhere, in code, docs or customer-facing copy; use a plain hyphen or rewrite the sentence.
- Buyer PII (names, addresses) is persisted only as far as a claim needs it, encrypted at rest, and expires after 30 days.
- Two ways to sell: direct (the brand's accounts) and storefront (Seen as seller of record on Seen's own accounts, epic E11). Ownership is a column, never a second product: `connections.owner` is `brand` or `seen`, `tenants.selling_mode` per marketplace is `direct` or `storefront`, every row still carries the supplier's `tenant_id`, and in storefront mode Seen is the actor of every agent action. Consumer invoices, credit notes and supplier statements derive from ingested settlements and invoices only, the same rule as billing.
- Rules before reading. The pre-commit hook runs the static rules (strict TypeScript, Biome, ast-grep ground rules, dependency-cruiser layering, knip) in seconds; a review finding a rule could have caught names the rule; the money core carries fast-check properties and a mutation-score floor. Marketplace clients are generated from the vendored OpenAPI contracts under `packages/connectors/specs`, never hand-typed from documentation; money and ids are branded types and every boundary has one zod schema its type is inferred from (SEEN-114 to SEEN-116, SEEN-135).

## Working a ticket

Every ticket runs through the Seen harness (`docs/harness/workflow.md`): five stages, clarify, solution, tdd, review, deliver, one command each, with the evidence written to `docs/harness/history/<ticket>/` as it happens. The harness delivered on 23 and 24 September 2026 (SEEN-086 to SEEN-103); SEEN-104 to SEEN-106 add the session cap, the subagents and the hooks. SEEN-086 is the bootstrap ticket and is exempt: the harness did not exist while it was being built, so it has no journal at all, and its evidence is its test suite, its pull request body and an `## Outcome` section in the ticket file. Every ticket from SEEN-087 onwards has a journal written by the harness itself; a hand-written journal record is a falsification, not a stand-in. Context comes from the graph tools before reading files, one tool call per question: `codegraph_explore` (symbols, callers, callees, blast radius, verbatim source) while writing code; repowise `risk`, `why` and `health` through `harness graph` at clarify, solution and review; graphify `path` and `prs` for the map across code and documents (see the graphify section below). Judgement calls at the gates go to Jev through `harness decide` and are recorded with their probabilities.

1. Read `docs/prd/prd.md`, `docs/architecture.md`, `docs/harness/workflow.md` and the ticket file. The ticket's acceptance criteria are the definition of done; do not widen the scope.
2. Branch from `main` as `claude/<ticket-id>-<slug>` (Codex sessions use `codex/`). One ticket per branch.
3. Set `status: doing` in the ticket's frontmatter in the first commit; `done` after merge. Write the ticket's `## Outcome` section, set `status: review` and tick every acceptance criterion **before** advancing out of the review stage: the reviewed-tree fingerprint covers the whole ticket file, so any of the four added afterwards makes `verify-delivery` refuse. Writing `status: review` before the gate that decides whether the review passes reads oddly and is what the receipt's meaning requires; a review that returns the ticket sets it back. SEEN-109 tried to make delivery accept the status and the ticks afterwards and withdrew it at record 84, because one review found two ways through the exception. The receipt hash is the one thing that cannot be written earlier at all, and it belongs in the pull request body.
4. Tests first for anything in `packages/core` (detectors, matching, fee expectations, the policy gate). Integration tests mock the connectors; never call a live marketplace from a test.
5. Commits: `feat(<id>): ...`, `fix(<id>): ...`, `docs(<id>): ...`, `test(<id>): ...`. Keep the ticket id in every commit.
6. Human tickets (executor `human`) are registrations, verifications against a live account and real-data runs. Do them with Ruud, record the outcome in the ticket file under a `## Outcome` heading, and never invent API facts a verification ticket was meant to establish.
7. One slice per session. A session reads the PRD and the architecture once, at clarify; every later session starts from the handoff pack (`harness status --brief`), works one slice of at most 2 points, writes the next pack with `harness handoff` and ends. Research goes to the scout subagent and review to the reviewer subagent, each in a context of its own (`harness handoff` and `status --brief` are SEEN-104's and exist; the subagents and the hooks arrive with SEEN-105 and SEEN-106, and until then `/clear` at every slice boundary after writing the pack). The model and effort a slice runs on are read from the handoff pack once SEEN-108 lands and are never chosen inside the session; the review reads only what SEEN-107's triage leaves for it.
8. Ticket files are owned by this repository once a ticket has started: the plan generator behind the council artifact rewrites only tickets still at `status: todo` and never touches a started ticket's criteria, `## Outcome` or amendments. Renumbering is never done on a started ticket, because receipts, journals and pull request bodies quote its id. No new ticket is above 3 points; a five-point ticket carries a `## Slices` section that the solution stage adopts or amends.
9. Harness work (epic E10) takes at most ten percent of a sprint's build points from Sprint 1 and states the KPI it will move in its clarify record (SEEN-123).
10. When a ticket changes an agent action (`changes_agent_action: true`), the tool must declare reversibility, action type and a euro impact estimator, and the gate decision must be written to `agent_actions` and `audit_events` before execution.

After cloning, wire up the git hooks once: `git config core.hooksPath .githooks`. The pre-commit hook
runs gitleaks on staged changes, and `doctor` refuses until it is set.

Harness commands: `python3 harness/run.py doctor | start | status | history | draft | note | check |
coverage | advance | graph | decide | return | reopen | verify-delivery | verify-merge | report |
guard | hook | lint | sync | discard | list`. Every writing command refuses unless the branch is
`claude/<ticket-id>-…` or `codex/<ticket-id>-…`. The skill both assistants read is generated from
`docs/harness/skill.md` by `sync`, and `doctor` refuses when a copy has been edited by hand.
`guard <path>` answers whether an edit is allowed before it is made, which is worth asking rather
than finding out at the review: it exits 2 with the reason on stderr for code edits at clarify or
solution, edits from a branch that is not the ticket's, and edits outside the files the accepted
slice names. `hook <event> --client <claude|codex>` is the dispatcher the generated hook entries
call; it is not a command to run by hand.

## Index of docs/

| File | What it is |
|---|---|
| [docs/prd/prd.md](docs/prd/prd.md) | Product requirements for the MVP: summary, problem, goals and non-goals, users, principles, scope by module, journeys, functional requirements FR-1 to FR-46, capability routing, pricing and metering, data and security, gates and metrics, release plan, risks, open questions, glossary |
| [docs/architecture.md](docs/architecture.md) | MVP architecture: principles, capability routing per marketplace, system context, services, trade record data model, agent runtime and policy gate, modules, infrastructure and security, open verifications |
| [docs/development-plan.md](docs/development-plan.md) | Sprint calendar (harness days from 24 Sep, Sprint 0 to 7 to 29 Jan 2027), gates G0 to G7, team and capacity, day-0 checklist, not in the MVP, risks |
| [docs/harness/workflow.md](docs/harness/workflow.md) | The development harness as built: why, principles, the five stages and their stage gates, graphify, CodeGraph and Repowise with one role each, the context per session (slices, handoff packs, subagents, hooks), how the harness meets Claude Code and Codex, Jev before the model (review triage, routes, calibration), the correctness programme (rules from findings, generated marketplace clients, property and mutation tests, the spec session, the bounded review, prioritised P0 to P2), Jev AI, CI, the eleven KPIs, security controls, commands, repository layout, what the building settled, the harness tickets |
| [docs/tickets/README.md](docs/tickets/README.md) | Ticket index by sprint with points, executors, status and dependencies, plus the epic table |
| [CONTEXT.md](CONTEXT.md) | Glossary: the harness terms, the product terms they collide with, and the resolution of the three meanings of gate |
| [docs/adr/](docs/adr/) | Architecture decision records: journal integrity, the delivery receipt, the SEEN-086 bootstrap exemption, why an Outcome cannot count its own review rounds |

### Tickets (140, 422 build points)

| Ticket | Title | Epic | Size |
|---|---|---|---|
| Sprint 0 | 24 Sep - 9 Oct 2026 | Harness first, then foundations, three read connectors, ingest, day-0 registrations | gate G0 |
| [SEEN-001](docs/tickets/SEEN-001-register-amazon-sp-api-developer-and-file-ads.md) | Register Amazon SP-API developer and file Ads API application | E0 | human |
| [SEEN-002](docs/tickets/SEEN-002-obtain-ebay-production-keys-and-file.md) | Obtain eBay production keys and file Application Growth Check | E0 | human |
| [SEEN-003](docs/tickets/SEEN-003-obtain-bol-credentials-and-verify-oauth-grant.md) | Obtain Bol credentials and verify OAuth grant and rate limits | E0 | human |
| [SEEN-004](docs/tickets/SEEN-004-set-up-postmark-inbound-domain-and-stripe.md) | Set up Postmark inbound domain and Stripe account | E0 | human |
| [SEEN-005](docs/tickets/SEEN-005-review-partao-contract-and-draft-dpa-and-amazon.md) | Review Partao contract and draft DPA and Amazon data statement | E0 | human |
| [SEEN-086](docs/tickets/SEEN-086-build-the-seen-harness-cli-with-staged-journal.md) | Build the Seen harness CLI with staged journal and receipts | E10 | 8 pt |
| [SEEN-006](docs/tickets/SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md) | Scaffold the pnpm turborepo monorepo with all six packages | E0 | 3 pt |
| [SEEN-097](docs/tickets/SEEN-097-set-up-the-local-docker-development-environment.md) | Set up the local Docker development environment | E0 | 3 pt |
| [SEEN-087](docs/tickets/SEEN-087-install-graphify-build-the-repo-graph-and-wire.md) | Install graphify, build the repo graph and wire it into both assistants | E10 | 3 pt |
| [SEEN-096](docs/tickets/SEEN-096-add-codegraph-and-route-the-graph-command.md) | Add codegraph and route the graph command to it | E10 | 1 pt |
| [SEEN-098](docs/tickets/SEEN-098-add-repowise-and-carry-risk-into-the-gate.md) | Add repowise and carry its risk answer into the gate | E10 | 2 pt |
| [SEEN-099](docs/tickets/SEEN-099-set-the-context-budget-and-measure-the-tools.md) | Set the context budget and measure what the tools changed | E10 | 1 pt |
| [SEEN-100](docs/tickets/SEEN-100-let-a-gate-tell-an-open-question-from-an.md) | Let a gate tell an open question from an unknowable one | E10 | 1 pt |
| [SEEN-088](docs/tickets/SEEN-088-integrate-jev-ai-typed-decisions-into-the.md) | Integrate Jev AI typed decisions into the harness gates | E10 | 3 pt |
| [SEEN-089](docs/tickets/SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md) | Enforce the TDD gates in the harness | E10 | 3 pt |
| [SEEN-094](docs/tickets/SEEN-094-verify-delivery-against-ci-and-the-merge.md) | Verify delivery against CI and verify the merge against the receipt | E10 | 2 pt |
| [SEEN-095](docs/tickets/SEEN-095-check-ticket-status-against-its-own-journal.md) | Check a ticket's status against its own journal | E10 | 1 pt |
| [SEEN-090](docs/tickets/SEEN-090-add-harness-security-controls-secrets.md) | Add harness security controls: secrets, permissions, injection, supply chain | E10 | 3 pt |
| [SEEN-091](docs/tickets/SEEN-091-collect-harness-kpis-per-ticket-and-produce.md) | Collect harness KPIs per ticket and produce weekly and sprint reports | E10 | 3 pt |
| [SEEN-093](docs/tickets/SEEN-093-add-harness-reopen-to-void-a-receipt-before.md) | Add harness reopen to void a receipt before merge | E10 | 2 pt |
| [SEEN-092](docs/tickets/SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md) | Sync the harness skill to Claude Code and Codex and retire the Seene leftovers | E10 | 2 pt |
| [SEEN-101](docs/tickets/SEEN-101-let-a-journal-survive-its-ticket-being-renamed.md) | Let a journal survive its ticket being renamed | E10 | 1 pt |
| [SEEN-102](docs/tickets/SEEN-102-decide-on-the-repowise-pr-bot.md) | Decide on the repowise PR bot for a private repository | E10 | human |
| [SEEN-103](docs/tickets/SEEN-103-declare-non-code-mode-at-the-solution-stage.md) | Declare non-code mode at the solution stage, not after it | E10 | 1 pt |
| [SEEN-104](docs/tickets/SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md) | Cap a session at one slice: the slice plan, the budget and the handoff pack | E10 | 3 pt |
| [SEEN-105](docs/tickets/SEEN-105-give-the-scout-and-the-reviewer-their-own.md) | Give the scout and the reviewer their own context as subagents in both assistants | E10 | 3 pt |
| [SEEN-106](docs/tickets/SEEN-106-enforce-the-harness-with-hooks-in-both.md) | Enforce the harness with hooks in both assistants, generated from one source | E10 | 3 pt |
| [SEEN-107](docs/tickets/SEEN-107-let-jev-settle-what-the-review-can-settle.md) | Let Jev settle what the review can settle before a model reads the diff | E10 | 3 pt |
| [SEEN-108](docs/tickets/SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md) | Route each slice to a model and an effort at solution, by rule first and by Jev second | E10 | 2 pt |
| [SEEN-109](docs/tickets/SEEN-109-calibrate-the-review-triage-and-the-routes-on.md) | Calibrate the review triage and the routes on ten tickets before either saves a token | E10 | 2 pt |
| [SEEN-110](docs/tickets/SEEN-110-verify-the-hooks-in-a-codex-session-and-close.md) | Verify the hooks in a Codex session and close what SEEN-106 declined | E10 | human |
| [SEEN-111](docs/tickets/SEEN-111-hold-a-slice-to-the-context-it-was-routed-to.md) | Hold a slice to the context it was routed to, and price it before it is worked | E10 | 3 pt |
| [SEEN-112](docs/tickets/SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md) | Run a ticket from clarify to merge in one go, asking only what it cannot decide | E10 | 3 pt |
| [SEEN-113](docs/tickets/SEEN-113-let-a-tdd-record-cite-the-evidence-a-return.md) | Let a tdd record cite the evidence a return did not invalidate | E10 | 2 pt |
| [SEEN-114](docs/tickets/SEEN-114-turn-every-recurring-finding-into-a-rule-the.md) | Turn every recurring finding into a rule the pre-commit hook runs in seconds | E10 | 3 pt |
| [SEEN-115](docs/tickets/SEEN-115-generate-the-marketplace-clients-from-the.md) | Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them | E10 | 3 pt |
| [SEEN-116](docs/tickets/SEEN-116-property-based-and-mutation-tests-on-the-money.md) | Property-based and mutation tests on the money core, as a gate | E10 | 3 pt |
| [SEEN-117](docs/tickets/SEEN-117-the-spec-session-writes-the-red-the-implementer.md) | The spec session writes the RED; the implementer cannot touch it | E10 | 2 pt |
| [SEEN-118](docs/tickets/SEEN-118-a-finding-needs-a-failing-test-taste-is-not-a.md) | A finding needs a failing test, taste is not a finding, and the third round is the founder's | E10 | 2 pt |
| [SEEN-119](docs/tickets/SEEN-119-independent-slices-run-in-parallel-worktrees.md) | Independent slices run in parallel worktrees | E10 | 3 pt |
| [SEEN-120](docs/tickets/SEEN-120-affected-only-checks-and-a-local-ci-that.md) | Affected-only checks and a local CI that finishes in minutes | E10 | 2 pt |
| [SEEN-121](docs/tickets/SEEN-121-bake-off-the-typescript-lsp-plugin-against.md) | Bake-off: the TypeScript LSP plugin against codegraph, keep one | E10 | 2 pt |
| [SEEN-122](docs/tickets/SEEN-122-golden-path-end-to-end-tests-on-the-docker.md) | Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures | E10 | 3 pt |
| [SEEN-123](docs/tickets/SEEN-123-cap-harness-work-at-ten-percent-of-a-sprint-and.md) | Cap harness work at ten percent of a sprint and make every harness ticket state its payback | E10 | 1 pt |
| [SEEN-135](docs/tickets/SEEN-135-branded-money-and-ids-one-schema-per-boundary.md) | Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings | E10 | 2 pt |
| [SEEN-136](docs/tickets/SEEN-136-no-test-touches-the-clock-the-network-or.md) | No test touches the clock, the network or randomness unfaked, and a flaky test is a defect | E10 | 2 pt |
| [SEEN-137](docs/tickets/SEEN-137-one-worked-example-per-acceptance-criterion.md) | One worked example per acceptance criterion before the solution stage, so the RED is a transcription | E10 | 1 pt |
| [SEEN-138](docs/tickets/SEEN-138-the-harness-has-its-own-regression-suite-five.md) | The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change | E10 | 3 pt |
| [SEEN-140](docs/tickets/SEEN-140-one-answer-to-whether-a-slices-plan-covers-a.md) | One answer to whether a slice's plan covers a path | E10 | 1 pt |
| [SEEN-008](docs/tickets/SEEN-008-create-trade-record-schema-v1-with-tenant-id.md) | Create trade-record schema v1 with tenant_id and RLS on every table | E0 | 5 pt |
| [SEEN-139](docs/tickets/SEEN-139-hand-the-immutability-guard-forward-to-every.md) | Hand the immutability guard forward to every migration that adds a table | E0 | 2 pt |
| [SEEN-009](docs/tickets/SEEN-009-define-connector-interface-capability-matrix.md) | Define connector interface, capability matrix and credential access | E1 | 5 pt |
| [SEEN-010](docs/tickets/SEEN-010-add-per-marketplace-rate-limiting-with-header.md) | Add per-marketplace rate limiting with header-driven backoff | E1 | 3 pt |
| [SEEN-011](docs/tickets/SEEN-011-build-bol-retailer-api-v10-connector-for-orders.md) | Build Bol Retailer API v10 connector for orders to commissions | E1 | 5 pt |
| [SEEN-012](docs/tickets/SEEN-012-build-ebay-connector-for-orders-returns.md) | Build eBay connector for orders, returns, transactions and payouts | E1 | 5 pt |
| [SEEN-013](docs/tickets/SEEN-013-build-amazon-sp-api-connector-for-orders.md) | Build Amazon SP-API connector for orders, reports and Finances | E1 | 5 pt |
| [SEEN-014](docs/tickets/SEEN-014-run-ingest-workers-with-idempotent-upserts-raw.md) | Run ingest workers with idempotent upserts, raw archive and cadences | E1 | 5 pt |
| Sprint 1 | 12 - 23 Oct 2026 | Reconciliation engine, fee expectations, findings, audit PDF | gate G1 |
| [SEEN-015](docs/tickets/SEEN-015-verify-amazon-report-names-and-finances.md) | Verify Amazon report names and Finances transactions version | E1 | human |
| [SEEN-016](docs/tickets/SEEN-016-encode-fee-schedules-per-marketplace-and.md) | Encode fee schedules per marketplace and category in core | E2 | 3 pt |
| [SEEN-017](docs/tickets/SEEN-017-compute-fee-expectations-per-order-line-from.md) | Compute fee_expectations per order line from schedules and APIs | E2 | 5 pt |
| [SEEN-018](docs/tickets/SEEN-018-match-settlement-lines-to-order-lines.md) | Match settlement_lines to order_lines deterministically | E2 | 5 pt |
| [SEEN-019](docs/tickets/SEEN-019-implement-fee-detectors-as-pure-tested-functions.md) | Implement fee detectors as pure tested functions | E2 | 5 pt |
| [SEEN-020](docs/tickets/SEEN-020-implement-shipment-return-and-inventory.md) | Implement shipment, return and inventory detectors | E2 | 5 pt |
| [SEEN-021](docs/tickets/SEEN-021-persist-findings-with-rule-confidence-evidence.md) | Persist findings with rule, confidence, evidence refs and deadline | E2 | 3 pt |
| [SEEN-022](docs/tickets/SEEN-022-generate-the-audit-pdf-with-scorecard-and-line.md) | Generate the audit PDF with scorecard and line annex | E2 | 5 pt |
| [SEEN-023](docs/tickets/SEEN-023-measure-the-recoverable-pool-per-marketplace.md) | Measure the recoverable pool per marketplace | E2 | 3 pt |
| [SEEN-024](docs/tickets/SEEN-024-ship-ops-console-v1-for-tenants-connections-and.md) | Ship ops console v1 for tenants, connections and sync status | E5 | 3 pt |
| [SEEN-025](docs/tickets/SEEN-025-run-three-real-90-day-audits-and-deliver-the.md) | Run three real 90-day audits and deliver the PDFs | E2 | human |
| Sprint 2 | 26 Oct - 6 Nov 2026 | Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching | gate G2 |
| [SEEN-026](docs/tickets/SEEN-026-verify-bol-compensation-request-form-structure.md) | Verify Bol compensation request form structure | E3 | human |
| [SEEN-027](docs/tickets/SEEN-027-build-the-claims-rail-with-api-assisted-and.md) | Build the claims rail with api, assisted and track modes | E3 | 5 pt |
| [SEEN-028](docs/tickets/SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md) | Contest eBay payment disputes and cases by API | E3 | 5 pt |
| [SEEN-029](docs/tickets/SEEN-029-build-the-bol-assisted-case-pack-with-tracking.md) | Build the Bol assisted case pack with tracking | E3 | 3 pt |
| [SEEN-030](docs/tickets/SEEN-030-build-the-amazon-assisted-case-pack-with-report.md) | Build the Amazon assisted case pack with report tracking | E3 | 3 pt |
| [SEEN-031](docs/tickets/SEEN-031-match-credits-to-claims-as-the-only-billable.md) | Match credits to claims as the only billable event | E3 | 3 pt |
| [SEEN-032](docs/tickets/SEEN-032-write-append-only-audit-events-before-every.md) | Write append-only audit_events before every side effect | E4 | 2 pt |
| [SEEN-033](docs/tickets/SEEN-033-implement-policy-gate-v1-with-caps-and.md) | Implement policy gate v1 with caps and reversibility | E4 | 5 pt, gate action |
| [SEEN-034](docs/tickets/SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md) | Build agent runtime v1 with the fixed tool set and cost accounting | E4 | 5 pt, gate action |
| [SEEN-035](docs/tickets/SEEN-035-build-the-approval-inbox-with-approve-edit-and.md) | Build the approval inbox with approve, edit and reject | E4 | 5 pt |
| [SEEN-036](docs/tickets/SEEN-036-create-the-eval-set-of-30-real-findings-with.md) | Create the eval set of 30 real findings with expected drafts | E4 | 3 pt |
| [SEEN-037](docs/tickets/SEEN-037-file-the-first-ten-claims-across-two.md) | File the first ten claims across two marketplaces from the inbox | E3 | human |
| [SEEN-007](docs/tickets/SEEN-007-go-live-on-google-cloud-after-the-go-no-go.md) | Go live on Google Cloud after the go/no-go decision | E0 | 5 pt |
| [SEEN-124](docs/tickets/SEEN-124-decide-the-storefront-legal-model-with-the-tax.md) | Decide the storefront legal model with the tax adviser: commissionaire or buy-resell, and where VAT is due | E11 | human |
| Sprint 3 | 9 - 20 Nov 2026 | Reconcile module, Stripe billing, statements, Shopify | gate G3 |
| [SEEN-038](docs/tickets/SEEN-038-verify-shopify-payments-payout-scopes-and.md) | Verify Shopify Payments payout scopes and create the custom app | E1 | human |
| [SEEN-039](docs/tickets/SEEN-039-create-stripe-customers-with-sepa-and-card-and.md) | Create Stripe customers with SEPA and card and handle webhooks | E6 | 5 pt |
| [SEEN-040](docs/tickets/SEEN-040-issue-invoices-with-recovery-share-lines-from.md) | Issue invoices with recovery-share lines from credited claims only | E6 | 5 pt |
| [SEEN-041](docs/tickets/SEEN-041-generate-and-send-the-monthly-statement-pdf.md) | Generate and send the monthly statement PDF | E6 | 5 pt |
| [SEEN-042](docs/tickets/SEEN-042-ship-the-reconcile-module-with-margin-and-fee.md) | Ship the Reconcile module with margin and fee-change alerts | E7 | 5 pt |
| [SEEN-043](docs/tickets/SEEN-043-export-finance-csv-of-settlements-and-matched.md) | Export finance CSV of settlements and matched lines | E7 | 3 pt |
| [SEEN-044](docs/tickets/SEEN-044-build-the-shopify-admin-graphql-connector-as.md) | Build the Shopify Admin GraphQL connector as product and stock truth | E1 | 5 pt |
| [SEEN-045](docs/tickets/SEEN-045-add-module-switches-per-tenant-with-scheduling.md) | Add module switches per tenant with scheduling and billing hooks | E7 | 3 pt |
| [SEEN-046](docs/tickets/SEEN-046-build-customer-facing-findings-and-claims-views.md) | Build customer-facing findings and claims views | E5 | 5 pt |
| [SEEN-047](docs/tickets/SEEN-047-issue-the-first-invoice-and-send-the-signed.md) | Issue the first invoice and send the signed statement | E6 | human |
| [SEEN-125](docs/tickets/SEEN-125-open-seen-s-own-seller-accounts-on-bol-and.md) | Open Seen's own seller accounts on Bol and Amazon EU and obtain the brand authorisation pack | E11 | human |
| Sprint 4 | 23 Nov - 4 Dec 2026 | Comply v1, Kaufland connector, listing fixes by API | gate G4 |
| [SEEN-048](docs/tickets/SEEN-048-verify-kaufland-settlement-and-ticket-endpoints.md) | Verify Kaufland settlement and ticket endpoints and obtain keys | E1 | human |
| [SEEN-049](docs/tickets/SEEN-049-encode-listing-spec-rules-per-marketplace-in.md) | Encode listing spec rules per marketplace in core | E7 | 5 pt |
| [SEEN-050](docs/tickets/SEEN-050-ingest-listings-with-content-hash-and-drift.md) | Ingest listings with content hash and drift detection | E7 | 5 pt |
| [SEEN-051](docs/tickets/SEEN-051-add-propose-listing-fix-and-apply-listing-fix.md) | Add propose_listing_fix and apply_listing_fix tools with diff | E7 | 5 pt, gate action |
| [SEEN-052](docs/tickets/SEEN-052-write-listing-content-through-bol-and-ebay-apis.md) | Write listing content through Bol and eBay APIs | E1 | 5 pt |
| [SEEN-053](docs/tickets/SEEN-053-write-listing-content-through-amazon-listings.md) | Write listing content through Amazon Listings Items and Feeds | E1 | 5 pt |
| [SEEN-054](docs/tickets/SEEN-054-build-the-kaufland-connector-with-tickets-as.md) | Build the Kaufland connector with tickets as the claims rail | E1 | 5 pt |
| [SEEN-055](docs/tickets/SEEN-055-monitor-unauthorised-sellers-from-competing.md) | Monitor unauthorised sellers from competing offers | E7 | 3 pt |
| [SEEN-056](docs/tickets/SEEN-056-show-comply-defects-and-fix-diffs-in-the-inbox.md) | Show Comply defects and fix diffs in the inbox | E5 | 3 pt |
| [SEEN-057](docs/tickets/SEEN-057-verify-listing-fixes-on-three-marketplaces-and.md) | Verify listing fixes on three marketplaces and file Kaufland tickets | E7 | human |
| [SEEN-126](docs/tickets/SEEN-126-register-the-storefront-entity-for-epr-gpsr.md) | Register the storefront entity for EPR, GPSR responsible-person data and product liability cover | E11 | human |
| [SEEN-127](docs/tickets/SEEN-127-write-the-storefront-agreement-supply-terms-the.md) | Write the storefront agreement: supply terms, the statement, the payout schedule, returns and the fee | E11 | human |
| Sprint 5 | 7 - 18 Dec 2026 | Serve v1, forwarded mailbox, trust ramp, Otto connector | gate G5 |
| [SEEN-058](docs/tickets/SEEN-058-verify-ebay-messaging-deprecation-and-choose.md) | Verify eBay messaging deprecation and choose the message path | E1 | human |
| [SEEN-059](docs/tickets/SEEN-059-verify-otto-rate-limits-and-obtain-otto-api-keys.md) | Verify Otto rate limits and obtain Otto API keys | E1 | human |
| [SEEN-060](docs/tickets/SEEN-060-build-the-otto-connector-for-orders-returns.md) | Build the Otto connector for orders, returns, receipts and messages | E1 | 5 pt |
| [SEEN-061](docs/tickets/SEEN-061-ingest-message-threads-from-amazon-ebay.md) | Ingest message_threads from Amazon, eBay, Kaufland and Otto | E7 | 5 pt |
| [SEEN-062](docs/tickets/SEEN-062-parse-the-forwarded-mailbox-via-postmark.md) | Parse the forwarded mailbox via Postmark inbound into threads | E7 | 5 pt |
| [SEEN-063](docs/tickets/SEEN-063-add-reply-message-tool-bound-to-tenant-service.md) | Add reply_message tool bound to tenant service policies | E7 | 5 pt, gate action |
| [SEEN-064](docs/tickets/SEEN-064-apply-return-and-cancellation-decisions-through.md) | Apply return and cancellation decisions through returns APIs | E7 | 5 pt, gate action |
| [SEEN-065](docs/tickets/SEEN-065-implement-the-trust-ramp-with-autonomy-per.md) | Implement the trust ramp with autonomy per action type | E4 | 5 pt, gate action |
| [SEEN-066](docs/tickets/SEEN-066-track-claim-and-dispute-deadlines-with-alerts.md) | Track claim and dispute deadlines with alerts | E3 | 3 pt |
| [SEEN-067](docs/tickets/SEEN-067-show-serve-threads-and-drafts-in-the-inbox.md) | Show Serve threads and drafts in the inbox | E5 | 3 pt |
| Sprint 6 | 4 - 15 Jan 2027 | Price module v1: competitor snapshots, net-margin model, governor, headroom meter | gate G6 |
| [SEEN-068](docs/tickets/SEEN-068-verify-the-kaufland-virtual-buy-box-endpoint.md) | Verify the Kaufland virtual buy box endpoint | E8 | human |
| [SEEN-069](docs/tickets/SEEN-069-snapshot-competing-offers-from-bol-by-ean-and.md) | Snapshot competing offers from Bol by EAN and eBay by GTIN | E8 | 5 pt |
| [SEEN-070](docs/tickets/SEEN-070-snapshot-amazon-pricing-on-a-tiered-clock.md) | Snapshot Amazon pricing on a tiered clock | E8 | 5 pt |
| [SEEN-071](docs/tickets/SEEN-071-model-net-margin-per-marketplace-from-cost.md) | Model net margin per marketplace from cost layers | E8 | 5 pt |
| [SEEN-072](docs/tickets/SEEN-072-implement-the-price-governor-with-bands.md) | Implement the price governor with bands, ceilings and cooldowns | E8 | 5 pt, gate action |
| [SEEN-073](docs/tickets/SEEN-073-write-prices-through-bol-offers-and-ebay.md) | Write prices through Bol Offers and eBay Inventory offers | E1 | 3 pt |
| [SEEN-074](docs/tickets/SEEN-074-add-propose-price-and-apply-price-tools-with.md) | Add propose_price and apply_price tools with buy-box tracking | E8 | 5 pt, gate action |
| [SEEN-075](docs/tickets/SEEN-075-meter-headroom-entries-and-show-the-price-view.md) | Meter headroom_entries and show the Price view | E8 | 5 pt |
| [SEEN-076](docs/tickets/SEEN-076-run-the-daily-bol-buy-box-feedback-loop.md) | Run the daily Bol buy-box feedback loop | E8 | 3 pt |
| Sprint 7 | 18 - 29 Jan 2027 | Grow v1, retailer read-only view, hardening, day-120 metrics | gate G7 |
| [SEEN-077](docs/tickets/SEEN-077-read-ad-reports-from-amazon-ads-bol-advertising.md) | Read ad reports from Amazon Ads, Bol Advertising and eBay Promoted | E9 | 5 pt |
| [SEEN-078](docs/tickets/SEEN-078-attribute-ad-cost-into-margin-and-publish-the.md) | Attribute ad cost into margin and publish the weekly Grow report | E9 | 5 pt |
| [SEEN-079](docs/tickets/SEEN-079-propose-campaign-budgets-through-the-gate-no.md) | Propose campaign budgets through the gate, no autonomous creation | E9 | 3 pt, gate action |
| [SEEN-080](docs/tickets/SEEN-080-build-the-retailer-read-only-view-via-a-scoped.md) | Build the retailer read-only view via a scoped link | E9 | 5 pt |
| [SEEN-081](docs/tickets/SEEN-081-load-test-ingest-on-50-tenants-and-run-rate.md) | Load test ingest on 50 tenants and run rate-limit chaos | E9 | 5 pt |
| [SEEN-082](docs/tickets/SEEN-082-run-rls-penetration-tests-and-the-restore-drill.md) | Run RLS penetration tests and the restore drill | E9 | 5 pt |
| [SEEN-083](docs/tickets/SEEN-083-expire-amazon-pii-after-30-days-and-delete.md) | Expire Amazon PII after 30 days and delete tenants on request | E9 | 3 pt |
| [SEEN-084](docs/tickets/SEEN-084-build-the-day-120-metrics-dashboard-and-csv.md) | Build the day-120 metrics dashboard and CSV export | E9 | 5 pt |
| [SEEN-085](docs/tickets/SEEN-085-run-restore-drill-close-pen-test-findings-sign.md) | Run restore drill, close pen-test findings, sign metrics pack | E9 | human |
| [SEEN-128](docs/tickets/SEEN-128-connection-ownership-and-storefront-mode-on-the.md) | Connection ownership and storefront mode on the trade record | E11 | 3 pt |
| Sprint 8 | 1 - 12 Feb 2027 | Storefront: Seen as seller of record, one supplier live on Bol | gate G8 |
| [SEEN-129](docs/tickets/SEEN-129-list-a-supplier-s-catalogue-under-seen-s.md) | List a supplier's catalogue under Seen's accounts with brand mapping and GPSR data | E11 | 5 pt |
| [SEEN-130](docs/tickets/SEEN-130-dropship-flow-a-purchase-order-to-the-supplier.md) | Dropship flow: a purchase order to the supplier on every storefront order, shipment and tracking back | E11 | 5 pt |
| [SEEN-131](docs/tickets/SEEN-131-consumer-invoices-with-vat-by-destination-and.md) | Consumer invoices with VAT by destination and the OSS return | E11 | 5 pt |
| [SEEN-132](docs/tickets/SEEN-132-supplier-statements-and-payouts-net-proceeds.md) | Supplier statements and payouts: net proceeds minus marketplace fees and the storefront fee, credits passed through | E11 | 5 pt |
| [SEEN-133](docs/tickets/SEEN-133-returns-withdrawals-and-guarantee-cases-handled.md) | Returns, withdrawals and guarantee cases handled as the seller of record | E11 | 3 pt |
| [SEEN-134](docs/tickets/SEEN-134-storefront-pilot-one-supplier-live-on-bol-under.md) | Storefront pilot: one supplier live on Bol under Seen's account, first statement paid | E11 | human |

## graphify

The repository's knowledge graph lives in `graphify-out/` and is committed, so a fresh clone has
context before its first build. Ask it before reading files.

- `graphify query "<question>"` for a scoped subgraph, `graphify path "<A>" "<B>"` for how two things
  connect, `graphify explain "<concept>"` for one concept, `graphify affected "<symbol>"` for what a
  change touches. The same graph is available as MCP tools (`query_graph`, `get_neighbors`,
  `shortest_path`, `get_pr_impact`) in Claude Code and Codex.
- `graphify-out/GRAPH_REPORT.md` is for broad architecture review, not for answering a specific
  question. Reach for it after query, path and explain have not surfaced enough.
- The post-commit hook runs `graphify update .`, so the graph follows the code without an API call.
  A commit that changes code carries the updated graph with it.
- `harness graph <ticket> <impact|path|explain|prs>` asks the same graph and writes the answer into
  the ticket's journal, with the hash of the graph that answered.
