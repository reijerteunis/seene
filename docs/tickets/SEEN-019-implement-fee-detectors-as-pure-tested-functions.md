---
id: SEEN-019
title: "Implement fee detectors as pure tested functions"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-017, SEEN-018, SEEN-116]
status: todo
---
# SEEN-019: Implement fee detectors as pure tested functions

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Add packages/core/detectors with four pure functions over matched settlement lines and fee_expectations: commission overcharge, fixed-fee error, duplicate charge and ad charge above expectation. Each returns a candidate finding with rule id, amount, confidence, evidence refs (settlement line, order line, fee expectation) and the marketplace's claim deadline. Tolerances are per-marketplace constants (rounding to EUR 0.01, VAT handling) so the detectors raise nothing on rounding.

## Acceptance criteria

- [ ] Each detector has unit tests with at least 5 true positives and 5 true negatives built from anonymised real lines
- [ ] Commission overcharge raises only when the charged rate exceeds the expected rate by more than 0.1 percentage points and EUR 0.05
- [ ] Duplicate charge detects two settlement lines with the same type, order line and amount within 90 days
- [ ] Detectors are deterministic: the same input yields identical findings on 100 repeated runs
- [ ] A fast-check property, named after its invariant, shows that each fee detector never raises inside its tolerance and always raises outside it

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Finding shape, tolerances per marketplace and the commission overcharge detector (2 pt). RED: a charged rate above the expected rate by more than the tolerance raises, a rounding difference does not
2. Fixed-fee error and duplicate charge detectors (2 pt). RED: two lines with the same type, order line and amount inside the window raise a duplicate
3. Ad charge above expectation and the determinism run (1 pt). RED: 100 runs over the same input yield identical findings

## Depends on

- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs
- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically
- [SEEN-116](SEEN-116-property-based-and-mutation-tests-on-the-money.md): Property-based and mutation tests on the money core, as a gate

## Blocks

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
