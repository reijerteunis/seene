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
depends_on: [SEEN-089]
status: doing
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
| Status | doing |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

A test that passes proves the code does what the test says; it does not prove the test says anything. The money core (detectors, matching, fee expectations, the policy gate) is pure functions, which is exactly where property-based tests and mutation testing earn their keep. This ticket builds the machinery and the gate, not the properties themselves: those belong to the tickets that write each function (SEEN-016 to SEEN-020 and SEEN-033), and each of them carries a criterion for its own named invariant. Here fast-check becomes a dev dependency of packages/core with a documented convention for naming the invariant a property states, and StrykerJS with the vitest runner and the TypeScript checker mutates packages/core and reports the mutation score; the threshold lives in thresholds.toml (start at 70, raised with the measurement) and the tdd gate accepts a killed mutant as RED evidence. CI runs incremental mutation on the files a pull request changed. The mechanism is proven on a fixture detector of its own under the test fixtures, never on product code, so this ticket depends on no platform ticket and lands before the first one that moves money. The decision that matters: on the code that moves money, the standard is not coverage but killed mutants and stated invariants, because that is the code a review cannot fully read.

## Acceptance criteria

- [ ] fast-check is a dev dependency of packages/core, and the convention for naming the invariant a property states is written in docs/harness/workflow.md
- [ ] StrykerJS runs on packages/core with the vitest runner and the TypeScript checker, and the mutation score is reported in kpi.json and the sprint report
- [ ] thresholds.toml carries the mutation score floor, the tdd gate refuses to advance packages/core changes below it, and a killed mutant is accepted as RED evidence
- [ ] CI runs incremental mutation on the changed files of a pull request in under ten minutes
- [ ] A seeded bug in a fixture detector (wrong tolerance sign) is caught by a property and by a mutant, proven with a fixture that is not product code

## Depends on

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce the TDD gates in the harness

## Blocks

- [SEEN-016](SEEN-016-encode-fee-schedules-per-marketplace-and.md): Encode fee schedules per marketplace and category in core
- [SEEN-017](SEEN-017-compute-fee-expectations-per-order-line-from.md): Compute fee_expectations per order line from schedules and APIs
- [SEEN-018](SEEN-018-match-settlement-lines-to-order-lines.md): Match settlement_lines to order_lines deterministically
- [SEEN-019](SEEN-019-implement-fee-detectors-as-pure-tested-functions.md): Implement fee detectors as pure tested functions
- [SEEN-020](SEEN-020-implement-shipment-return-and-inventory.md): Implement shipment, return and inventory detectors
- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

packages/core now has the machinery for property-based and mutation tests, and
the tdd gate holds product code to a mutation floor. The properties themselves
belong to the tickets that write each money function, as the description says.

- fast-check 4 and `@fast-check/vitest` are dev dependencies of packages/core.
  docs/harness/workflow.md states the convention: a property is written with
  `test.prop`, so a failure prints its counterexample and replay seed, and its
  title is `invariant: ` followed by the invariant as one sentence.
- StrykerJS 10 runs on packages/core through `stryker.config.mjs`, with the
  vitest runner and the TypeScript checker, over `src/` only and against the
  database-free `unit` vitest project (clarify decision, record 6). A
  `--phase mutation` check reads Stryker's JSON report. kpi.json carries the
  score, or the reason there is none, and the sprint report has a Mutation
  column.
- thresholds.toml carries `[mutation] floor = 70`, registered in
  `thresholds.EXPECTED`. The tdd gate refuses an attempt whose slices name a
  file under packages/core/src unless a mutation measurement over those files
  is at or above the floor. A measurement with no mutants in them is recorded
  as not applicable, with its count. A RED whose Stryker report names a Killed
  mutant in a slice file counts as a demonstrated failure. Slice 2, RED 28,
  GREEN 29.
- CI's `mutation` job runs on pull requests only. It diffs packages/core/src
  against the PR base, widens to all of src when a Stryker or vitest config
  changes, skips when nothing in src changed, and runs Stryker with
  `--incremental --mutate`. Slice 3, RED 32, GREEN 34. Check 48 measured it on
  pull request 44:
  - Run 37068194534 on 7682adc, cold: 32 seconds for the job.
  - Run 37070105397 on ca030d9, warm from the incremental cache: 29 seconds.
  - Run 37077429429 on dfbc3b9, the selection in `harness/mutation_ci.py`
    (attempt 5): 25 seconds. It widened to all of src, because package.json
    is in the diff.

  Both are far under ten minutes. src holds one mutable file today, so this
  shows the step is fast on today's src, not on a much larger one.
- A fixture detector under `packages/core/fixtures/tolerance/`, outside src,
  the exports and the coverage figure, carries the seeded wrong-sign tolerance
  bug in `seeded.ts`. The `invariant:` property finds it there and none in
  `detector.ts`. The fixture Stryker run kills all 5 mutants of `detector.ts`,
  among them the comparison-flipping and sign-flipping ones. Slice 1, RED 40,
  GREEN 41.

This ticket's own figure: its slices name nothing under packages/core/src, so
the floor does not apply to it. It recorded no mutation check, so its kpi.json
mutation is null and the sprint report shows a dash.

Attempt 5 fixed four medium findings of the attempt 4 review (return 53,
scope in note 55):
- F1: a slice entry naming a directory under packages/core/src is mutated as
  `<dir>/**/*.ts,!<dir>/**/*.test.ts`. A measurement whose report lists none of
  a named file, or no file under a named directory, has no score and is
  refused, rather than recorded as not applicable. Slice 1, RED 59 and 61,
  GREEN 60 and 62.
- F2 and F3: the tdd gate reads a mutation measurement only when its `after`
  fingerprint is the tree being advanced and its command is
  `mutation.command(files)`. A stale score or one written by another command
  is refused. Slice 2, RED 65, GREEN 66.
- F4: CI's file selection is `harness/mutation_ci.py`, with a test per rule in
  `harness/tests/test_mutation_ci.py`, which CI's harness job runs. The
  `changed` step pipes the PR diff into it. Slice 3, RED 68, GREEN 69.
  Regression 70.
- F5: the README status row now mirrors the ticket status, and attempt 5's
  plan names it.
- F6: slice 1's RED 40 shows killed mutants, not the db/ exclusion. The RED
  for that exclusion is check 16 of attempt 2: `test:unit` ran
  `db/authorities.test.ts` before the unit project left db/ out.

The work took five attempts:
- Two returns from tdd to solution: the slice 1 regression at record 13, and
  the slice 2 regression at record 24.
- One return from the review triage at record 47, for criterion 4. The CI
  measurement only existed after the pull request ran. It is recorded in
  attempt 4 as check 48, cited in slice 3's entry.
- One return from review to solution at record 53, for F1 to F4 above.
