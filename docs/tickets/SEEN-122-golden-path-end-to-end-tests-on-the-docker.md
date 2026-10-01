---
id: SEEN-122
title: "Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-097, SEEN-115, SEEN-035]
status: todo
priority: P1
---
# SEEN-122: Golden-path end-to-end tests on the docker stack with recorded marketplace fixtures

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Unit tests and the review see one package at a time; the defects that reach a pilot brand live between packages: a queue that never fires, an approval that resumes the wrong run, a settlement line that lands in the wrong tenant. Write the golden paths once as end-to-end tests: connect a tenant, ingest ninety days from the Prism mocks and the recorded fixtures, run the audit, file a claim from the inbox, match a credit; Playwright for the inbox, HTTP for the API, the compose stack from SEEN-097 underneath. They run in CI on every pull request that touches apps/ and are the last check before verify-delivery on those tickets. The decision that matters: the review reads code; the golden path runs it.

## Acceptance criteria

- [ ] Five golden-path tests exist (connect, ingest, audit, claim, credit) and run green on the compose stack in CI
- [ ] The inbox path runs in Playwright against the local web app with RLS enforced, proven by a cross-tenant assertion
- [ ] A pull request touching apps/ cannot deliver without the golden paths green, enforced by verify-delivery
- [ ] The suite runs in under ten minutes on CI, recorded in the sprint report
- [ ] A seeded defect (a claim resumed into the wrong run) is caught by the claim path, proven with a fixture

## Depends on

- [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md): Set up the local Docker development environment
- [SEEN-115](SEEN-115-generate-the-marketplace-clients-from-the.md): Generate the marketplace clients from the official OpenAPI specs and validate every fixture against them
- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
