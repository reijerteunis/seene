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
status: todo
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
| Status | todo |

## Description

Create the monorepo with pnpm workspaces and turborepo: apps/api (NestJS), apps/worker (NestJS with BullMQ), apps/web (Next.js App Router), packages/core, packages/connectors and packages/agent, with shared TypeScript config, ESLint, Vitest and a GitHub Actions pipeline that lints, tests and builds every package. Design decision: packages are plain TypeScript compiled by the consuming app with no publish step, so one change to the trade-record schema propagates in one commit.

## Acceptance criteria

- [ ] pnpm install and pnpm turbo build succeed from a clean clone in under 5 minutes
- [ ] pnpm turbo test runs a passing placeholder test in each of the six packages
- [ ] apps/api answers GET /health with HTTP 200 and apps/worker processes a hello job from a local Redis
- [ ] GitHub Actions runs lint, test and build on every pull request and blocks merge on failure

## Depends on

- none

## Blocks

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness
- [SEEN-007](SEEN-007-provision-gcp-europe-west4-and-supabase-eu-with.md): Provision GCP europe-west4 and Supabase EU with telemetry
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table
- [SEEN-009](SEEN-009-define-connector-interface-capability-matrix.md): Define connector interface, capability matrix and credential access

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
