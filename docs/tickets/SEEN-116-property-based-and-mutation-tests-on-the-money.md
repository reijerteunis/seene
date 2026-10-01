---
id: SEEN-116
title: "Property-based and mutation tests on the money core, as a gate"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-089, SEEN-016]
status: todo
priority: P0
---
# SEEN-116: Property-based and mutation tests on the money core, as a gate

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

A test that passes proves the code does what the test says; it does not prove the test says anything. The money core (detectors, matching, fee expectations, the policy gate) is pure functions, which is exactly where property-based tests and mutation testing earn their keep. fast-check properties state the invariants a reviewer otherwise checks by reading: settlement sums are conserved through matching, matching is idempotent and deterministic, a detector never raises inside the tolerance and always raises outside it, a fee expectation never exceeds the gross line, the policy gate refuses anything on the never list whatever the policies row says. StrykerJS with the vitest runner and the TypeScript checker mutates packages/core and reports the mutation score; the threshold lives in thresholds.toml (start at 70, raised with the measurement) and the tdd gate accepts a killed mutant as RED evidence. CI runs incremental mutation on the files a pull request changed. The decision that matters: on the code that moves money, the standard is not coverage but killed mutants and stated invariants, because that is the code a review cannot fully read.

## Acceptance criteria

- [ ] fast-check properties exist for matching, the fee detectors, the shipment and return detectors, fee expectations and the policy gate, with the invariant named in each property
- [ ] StrykerJS runs on packages/core with the vitest runner and the TypeScript checker, and the mutation score is reported in kpi.json and the sprint report
- [ ] thresholds.toml carries the mutation score floor, the tdd gate refuses to advance packages/core changes below it, and a killed mutant is accepted as RED evidence
- [ ] CI runs incremental mutation on the changed files of a pull request in under ten minutes
- [ ] A seeded bug in a detector (wrong tolerance sign) is caught by a property or a mutant, proven with a fixture

## Depends on

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce the TDD gates in the harness
- [SEEN-016](SEEN-016-encode-fee-schedules-per-marketplace-and.md): Encode fee schedules per marketplace and category in core

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
