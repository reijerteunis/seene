---
id: SEEN-094
title: "Verify delivery against CI and verify the merge against the receipt"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-093]
status: todo
---
# SEEN-094: Verify delivery against CI and verify the merge against the receipt

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Close the gap two tickets have already fallen through. `verify-delivery` reads the checks GitHub
reports for the commit the receipt attests and refuses unless every one has concluded green, refusing
outright when `gh` cannot answer rather than passing silently. A new command, `harness verify-merge
<ticket>`, runs before the merge button: the last record must be a receipt, its commit must be an
ancestor of the branch tip, every commit between the two must touch only the journal, the pull
request body must carry the receipt hash, and the tip's checks must be green. CI gains gitleaks and
`pnpm audit --audit-level high`, and the repository gains a pull request template that carries the
acceptance criteria, the red and green evidence, the review findings and the receipt hash.

The decision that matters: the receipt attests HEAD before the receipt record is committed, so the
tip is always one commit ahead by construction. Comparing them at delivery would refuse every
delivery, which is why this is a merge-time check with its own command.

## Acceptance criteria

- [ ] verify-delivery refuses when any check on the delivered commit is not green, and when a check has not concluded
- [ ] verify-delivery refuses when gh is missing or unauthenticated, naming what to install or authenticate, rather than passing
- [ ] verify-merge refuses when a commit after the receipt touches anything but the journal, naming the file
- [ ] verify-merge refuses a pull request body without the receipt hash, and passes when the receipt is the last record and the tip is green
- [ ] ci.yml runs gitleaks and pnpm audit at high, and a seeded secret on a throwaway branch fails the pipeline
- [ ] The pull request template is applied automatically to a new pull request

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-093](SEEN-093-add-harness-reopen-to-void-a-receipt-before.md): Add harness reopen to void a receipt before merge

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Why the receipt cannot be the tip at delivery: [docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md](../adr/0002-the-receipt-attests-the-tree-minus-the-journal.md)
- Split out of SEEN-089 on 23 September 2026, because one solution record covering seven enforcements could not be judged complete: the same question scored 0.49 on all seven and 0.67 on one.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
