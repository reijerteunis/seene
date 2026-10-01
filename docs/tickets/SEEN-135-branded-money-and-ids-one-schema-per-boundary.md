---
id: SEEN-135
title: "Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-114, SEEN-006]
status: todo
priority: P0
---
# SEEN-135: Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

A share of the sprint-0 findings were type errors in disguise: a euro amount added to a cent amount, a Bol order id passed where an internal order id was expected, an optional field read as present, a switch over marketplaces that forgot Kaufland. SEEN-114 turns the compiler's strict flags on; this ticket gives the domain its own types so the compiler has something to check. Money is an integer in minor units carrying a currency brand, and arithmetic on it goes only through packages/core/money, with an ast-grep rule in SEEN-114's set refusing a plus sign between two Money values. Tenant, connection, order, order line, settlement line, claim and marketplace identifiers are branded types, so an id of one kind cannot be passed as another and a marketplace's own id never masquerades as ours. Every boundary has one zod schema (marketplace payloads in, database rows out, queue jobs, HTTP bodies, the policy gate's input) and the TypeScript type is inferred from the schema, never declared a second time by hand. Switches over marketplaces, statuses and finding types are exhaustive by the compiler. Existing violations are fixed in this ticket, not suppressed: a biome-ignore needs a reason that cites a ticket, and kpi.json counts them. The decision that matters: a type error costs nothing to find and nothing to review, while the same mistake found in review costs a return, so every finding of the kind wrong unit, wrong id, missing case becomes a type first and a rule second.

## Acceptance criteria

- [ ] Money is a branded integer type in minor units with a currency, arithmetic goes only through packages/core/money, and a fixture that adds two Money values with a plus sign fails the rule set
- [ ] Tenant, connection, order, order line, settlement line, claim and marketplace ids are branded types, and passing a Bol order id where an internal order id is expected is a compile error, proven with a type test
- [ ] Every marketplace payload, database row, queue job, HTTP body and policy gate input has one zod schema with its type inferred from it, and a second hand-written type for the same shape is refused by a rule in SEEN-114's set
- [ ] Switches over marketplaces, statuses and finding types are exhaustive, proven by a fixture that adds a marketplace and fails to compile
- [ ] kpi.json counts biome-ignore comments, each carries a reason citing a ticket, and the count is in the weekly report

## Depends on

- [SEEN-114](SEEN-114-turn-every-recurring-finding-into-a-rule-the.md): Turn every recurring finding into a rule the pre-commit hook runs in seconds
- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
