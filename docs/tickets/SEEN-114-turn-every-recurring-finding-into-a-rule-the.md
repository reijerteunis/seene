---
id: SEEN-114
title: "Turn every recurring finding into a rule the pre-commit hook runs in seconds"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-090, SEEN-107]
status: todo
priority: P0
---
# SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Sprint 0 delivered 63 review findings on 20 tickets (2 blocking, 18 high, 27 medium, 16 low) and 0.79 returns per ticket. A finding a static rule could have caught is a finding paid for three times: the reviewer's reading, the return, the second review. Put the rules in front of the model. TypeScript strict with noUncheckedIndexedAccess, exactOptionalPropertyTypes and noImplicitOverride; Biome for format and lint with the typed rules on; ast-grep rules that encode the ground rules (cents as integers, no euro sign, no em dash, no cloud SDK import outside the provider packages, no live marketplace host in a test, no any, no floating promise); dependency-cruiser for the layering (packages/core imports nothing from apps or connectors and no IO library at all, no node:fs, fetch, pg or bullmq; connectors never import agent and reach the network only through the generated clients; a marketplace write is reachable only through the policy gate module; database access goes through the repository layer; no app imports another app); knip for dead exports, with an exports map per package so nothing reaches into another package's internals. Each rule cites the finding that created it or the architecture section that states it, so a rule nobody can trace is a rule to delete. Every review finding at medium or above carries rule_candidate (a rule id, or the reason none can catch it); harness report --week lists the findings a rule could have caught and the rules added since, and a rule candidate that recurs twice without a rule is a doctor warning. The pre-commit hook runs the rule set on staged files in under ten seconds; CI runs it on the tree. The decision that matters: a rule is written the week its finding appears, by the ticket that got the finding, so the review reads less every sprint.

## Acceptance criteria

- [ ] tsconfig.base.json carries strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes and noImplicitOverride, and the tree typechecks
- [ ] Biome, ast-grep and dependency-cruiser run on staged files in the pre-commit hook in under ten seconds, and in CI on the tree, with the ground rules above each proven by a fixture that fails (among them: node:fs imported inside packages/core, a marketplace write outside the policy gate, a query outside the repository layer)
- [ ] Every review finding at medium or above carries rule_candidate, and the review gate refuses a record without it
- [ ] harness report --week lists findings a rule could have caught, the rules added, and any candidate that recurred without a rule
- [ ] knip reports zero unused exports on packages/core and the connectors, every package declares an exports map, and each rule in the set cites a finding id or an architecture section, enforced in CI

## Depends on

- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff

## Blocks

- [SEEN-135](SEEN-135-branded-money-and-ids-one-schema-per-boundary.md): Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
