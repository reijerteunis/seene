---
id: SEEN-093
title: "Add harness reopen to void a receipt before merge"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086]
status: done
---
# SEEN-093: Add harness reopen to void a receipt before merge

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

Add `harness reopen <ticket> --reason "..." --actor <actor>`: it voids the receipt of a delivered
ticket, records the voiding with its reason, and returns the ticket to `tdd` on a new attempt. It
refuses once the delivered commit is merged into the default branch, because a merged receipt is
history and history is not edited. The decision that matters: a receipt is final when the work is
merged, not when it is written, so the guarantee worth protecting is that the receipt attests exactly
what merged.

SEEN-086 made `delivered` terminal on the assumption that a receipt marks the end of the work. Two
tickets showed otherwise: SEEN-087 shipped a broken CI assertion and SEEN-088 a transport that could
never reach its API, and both were found after their receipts. Each was patched on the branch, which
left the receipt attesting a commit that is not the one that merges. Voiding is the honest path:
the journal reads receipt, void, rework, second receipt, and rework is counted where it happened.

## Acceptance criteria

- [x] reopen on a delivered ticket appends a reopen record carrying the voided receipt hash, the reason and the actor, and status then shows the ticket at tdd on the next attempt
- [x] reopen is refused on a ticket that is not delivered, and the refusal names the stage it is in
- [x] reopen is refused when the delivered commit is an ancestor of the default branch, naming the merge commit
- [x] verify-delivery after a reopen writes a second receipt, and doctor still verifies the whole chain
- [x] A voided receipt is never deleted or rewritten: the reopen record follows it, and a test proves the chain still verifies

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- The receipt's meaning: [docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md](../adr/0002-the-receipt-attests-the-tree-minus-the-journal.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
