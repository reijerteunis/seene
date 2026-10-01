---
id: SEEN-118
title: "A finding needs a failing test, taste is not a finding, and the third round is the founder's"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-107, SEEN-113]
status: todo
priority: P0
---
# SEEN-118: A finding needs a failing test, taste is not a finding, and the third round is the founder's

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

A ticket was returned five times before SEEN-113 was written, and most returns carried findings a reader could argue with. Bound the review. Findings carry a category from a fixed list (correctness, security, tenant_isolation, money, contract, missing_test, evidence, documentation); a style or naming remark is refused by the review gate, because Biome decides style (SEEN-114). A finding at high or blocking must carry a failing test the reviewer subagent wrote into the test tree (it gets Write on tests only), or a scenario the harness can run; without one it is a note, not a return. The second review round reads only the files of the previous findings and their tests, at the depth the first round chose. A third round on the same attempt does not happen: the harness returns the finding list to the founder, who decides in the journal. Rework per category lands in the weekly report. The decision that matters: a return costs a session, so a return has to prove something, and the number of rounds is a rule rather than a mood.

## Acceptance criteria

- [ ] The review template carries category from the fixed list and the review gate refuses a finding without one or with a style category
- [ ] A high or blocking finding without a failing test or a runnable scenario is downgraded to a note by the gate, and a test the reviewer wrote is recorded with the reviewer's session id
- [ ] The second review round's focus set is the previous findings' files and tests, and the gate refuses a wider read list
- [ ] A third round on one attempt is refused and the finding list is written to the journal for the founder's decision
- [ ] harness report --week shows rework and findings by category

## Depends on

- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff
- [SEEN-113](SEEN-113-let-a-tdd-record-cite-the-evidence-a-return.md): Let a tdd record cite the evidence a return did not invalidate

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
