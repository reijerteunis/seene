---
id: SEEN-095
title: "Check a ticket's status against its own journal"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-094]
status: done
---
# SEEN-095: Check a ticket's status against its own journal

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

`doctor` verifies the journals, the chain, the hooks, the links and the skill copies, but nothing
compares a ticket's frontmatter against its own journal. Two tickets, SEEN-006 and SEEN-089, sat at
`status: done` for hours after they had delivered and merged, because both mark-done commits were
lost in a rebase conflict and nothing noticed. A ticket's status is what the backlog, the sprint
report and every session reads first, so a status that disagrees with the journal beside it misleads
everyone who looks.

`doctor` gains one check. For every ticket with a journal: a journal ending in a receipt whose commit
is merged into the default branch must say `done`; a journal in a working stage must not say `done` or
`todo`; and a ticket saying `done` with no receipt and no journal is only acceptable for the bootstrap,
SEEN-086, which is exempt by design and says so in `CLAUDE.md`.

The decision that matters: `doctor` reports the disagreement and repairs nothing, as it does
everywhere else. A status corrected silently is a status nobody learns to keep right.

## Acceptance criteria

- [x] doctor reports a ticket whose journal ends in a merged receipt but whose status is not done, naming the ticket and both values
- [x] doctor reports a ticket at a working stage whose status says done or todo
- [x] doctor accepts SEEN-086, which is done with no journal, because the bootstrap exemption is recorded
- [x] doctor accepts a delivered ticket whose receipt is not yet merged and whose status is review
- [x] doctor repairs nothing, proven by a test that leaves a wrong status in place

## Outcome

Delivered on 24 September 2026, opened the same day after two tickets were found sitting at `doing`
hours after they had delivered and merged.

**One check, four facts, no judgement**: the frontmatter status, the journal's last record, whether the
receipt's commit is an ancestor of the default branch, and the bootstrap exemption. Merged is the same
test `reopen` uses, so the two cannot disagree about what merged means. A delivered ticket waiting to
merge may say `review`, which is the normal state between a receipt and the button. An unstarted ticket
is not reported: eighty are `todo` with no journal, and saying so every run is noise. It reports and
repairs nothing.

**It has caught ten stale statuses in an afternoon.** The two that prompted it, SEEN-006 and SEEN-089,
whose mark-done commits were lost in a rebase conflict. Then eight more: a plan revision arrived in the
working tree written against an earlier snapshot, and had reset every delivered harness ticket to
`todo`. The check named each one with the receipt commit that proves it merged, which is the difference
between a report someone acts on and a report someone argues with.

**Attempt 2 is the reconciliation of that revision**, which is documentation and numbering rather than
code: the revision's two new tickets renumbered to SEEN-096 and SEEN-097, because SEEN-093 and SEEN-094
are merged and quoted by receipts that cannot be renumbered; three sentences restored to `CLAUDE.md`
that the code enforces and the revision could not have known about; and the eight statuses put back.
The review stage saw the tree that actually ships, which is why the ticket was returned rather than
delivered over a fingerprint that no longer matched.

**Record 12 is junk**, a contrived command run out of habit, disowned in the note at record 14 and cited
by nothing. It is the second in eleven tickets, after record 8 of SEEN-088.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md): Verify delivery against CI and verify the merge against the receipt

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Opened on 24 September 2026 after SEEN-006 and SEEN-089 were found sitting at doing, delivered and merged, hours after the fact.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
