---
id: SEEN-094
title: "Verify delivery against CI and verify the merge against the receipt"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-093]
status: done
---
# SEEN-094: Verify delivery against CI and verify the merge against the receipt

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

Close the gap two tickets have already fallen through. `verify-delivery` reads the checks GitHub
reports for the commit the receipt attests and refuses unless every one has concluded green, refusing
outright when `gh` cannot answer rather than passing silently. A new command, `harness verify-merge
<ticket>`, runs before the merge button: the last record must be a receipt, its commit must be an
ancestor of the branch tip, every commit between the two must touch only what delivery itself writes,
the pull request body must carry the receipt hash, and the tip's checks must be green.

The decision that matters: the receipt attests HEAD before the receipt record is committed, so the
tip is always one commit ahead by construction. Comparing them at delivery would refuse every
delivery, which is why this is a merge-time check with its own command.

Green means every check run on the commit has concluded with `success` or `skipped`. A run still in
progress refuses the delivery, and a commit with no checks at all refuses too, because a commit
nobody built is not a commit that passed.

Scope, settled on 23 September 2026: this ticket is delivery and merge verification and nothing else.
gitleaks, `pnpm audit --audit-level high` and the seeded-secret proof belong to
[SEEN-090](SEEN-090-add-harness-security-controls-secrets.md), whose subject is secrets and supply
chain. The repository gains a pull request template here, but the template itself is only applied by
GitHub when a pull request is opened in the browser, and every pull request in this project is opened
by `gh pr create --body-file`, which bypasses it. So the template is for a human opening one by hand,
and `verify-merge` enforces the substance that matters, the receipt hash, whatever created the pull
request.

## Acceptance criteria

- [x] verify-delivery refuses when any check on the delivered commit is not green, when one has not concluded, and when there are none at all
- [x] verify-delivery refuses when gh is missing or unauthenticated, naming what to install or authenticate, rather than passing
- [x] verify-merge refuses when a commit after the receipt touches anything but the journal, the coverage baseline and the graph, naming the file
- [x] verify-merge refuses a pull request body without the receipt hash, and passes when the receipt is the last record and the tip is green
- [x] The pull request template exists and carries the acceptance criteria, the red and green evidence, the review findings and the receipt hash

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-093](SEEN-093-add-harness-reopen-to-void-a-receipt-before.md): Add harness reopen to void a receipt before merge

## Blocks

- [SEEN-095](SEEN-095-check-ticket-status-against-its-own-journal.md): Check a ticket's status against its own journal
- [SEEN-008](SEEN-008-create-trade-record-schema-v1-with-tenant-id.md): Create trade-record schema v1 with tenant_id and RLS on every table

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Why the receipt cannot be the tip at delivery: [docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md](../adr/0002-the-receipt-attests-the-tree-minus-the-journal.md)
- Split out of SEEN-089 on 23 September 2026, because one solution record covering seven enforcements could not be judged complete: the same question scored 0.49 on all seven and 0.67 on one.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
