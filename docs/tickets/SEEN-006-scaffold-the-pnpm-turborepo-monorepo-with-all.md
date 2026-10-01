---
id: SEEN-006
title: "Scaffold the pnpm turborepo monorepo with all six packages"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: []
status: done
---
# SEEN-006: Scaffold the pnpm turborepo monorepo with all six packages

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

Create the monorepo with pnpm workspaces and turborepo: apps/api (NestJS), apps/worker (NestJS with BullMQ), apps/web (Next.js App Router), packages/core, packages/connectors and packages/agent, with shared TypeScript config, ESLint, Vitest and a GitHub Actions pipeline that lints, tests and builds every package. Design decision: packages are plain TypeScript compiled by the consuming app with no publish step, so one change to the trade-record schema propagates in one commit.

## Acceptance criteria

- [x] pnpm install and pnpm turbo build succeed from a clean clone in under 5 minutes, timed and recorded
- [x] pnpm turbo test runs a passing placeholder test in each of the six packages
- [x] apps/api answers GET /health with HTTP 200 and apps/worker processes a hello job from a local Redis
- [x] GitHub Actions runs lint, typecheck, test and build on every pull request, and its result is required before merge as far as the plan allows (amended at clarify on 23 September 2026: branch protection is unavailable on a private repository on the free plan, so the blocking half is SEEN-090's, which settles the plan)

## Carried in from SEEN-087

SEEN-087 graphed this repository before the monorepo existed, so two of its acceptance criteria were
re-pointed at `harness/` and the stage gate. Re-verify both here once the packages exist: a commit
changing `packages/core` must update `graphify-out/graph.json` in the same commit, and a graph query
for a symbol in `packages/core` must return its callers.

## Outcome

Delivered on 23 September 2026. Six packages, 21 turbo tasks green, and a clean clone that installs
and builds in **9 seconds** against a five-minute criterion.

**What is real rather than placeholder.** `apps/api` answers `GET /health` with 200 through a Nest
testing module and supertest. `apps/worker` enqueues a hello job and waits for a BullMQ worker to
finish it against a live Redis, reading host and port from the environment so the same test runs in
CI against a service container. The three library packages assert their own name, which proves they
resolve, compile and run under Vitest and claims nothing more; their behaviour belongs to the tickets
that own it. `packages/core` also gains integer cents and the ledger currency, because every later
ticket needs them before it can count money.

**The mechanism the ticket's design decision implies.** Library packages declare `src/index.ts` as
main and types and have no build script. `apps/api` and `apps/worker` compile them into their own
`dist` through a tsconfig rooted at the repository; `apps/web` sets `transpilePackages`. So one change
to the trade record lands in one commit, and nothing is published.

**AC4 was amended at clarify rather than met with an asterisk.** Branch protection cannot be
configured on a private repository on the free plan, so the criterion now says what CI can actually
do, and SEEN-090 settles the plan and owns the blocking half.

**SEEN-087's carried-in verification passed.** A commit changing `packages/core` rebuilt the graph,
and `harness graph SEEN-006 impact --about "sumCents()"` returned its importer, recorded at record 19.

**CI caught a flaky test the machine could not.** The worker test timed out on one run and passed on
another at the same commit: `waitUntilFinished` waits for a completion event, and the events
connection was subscribing after the worker had started, so on a fast runner the job could finish
before anything was listening. The worker now owns its events connection and exposes `ready()`.
Review returned the ticket for it, and ten consecutive local runs follow the fix.

**Two harness defects surfaced while working this ticket and were fixed here**, each recorded as a
note rather than folded quietly into a later ticket. The `solution_complete` question asked whether a
record "names everything the change needs", which no thirty-file scaffold clears; it now asks whether
an implementer could build it without stopping to ask. And the documented human override did not
exist: with a credential present, `harness decide --answer` still asked the model and recorded
`source: jev`. Record 6 is that bug, record 8 is the override working.

## Depends on

- none

## Blocks

- [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md): Set up the local Docker development environment
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce the TDD gates in the harness
- [SEEN-135](SEEN-135-branded-money-and-ids-one-schema-per-boundary.md): Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
