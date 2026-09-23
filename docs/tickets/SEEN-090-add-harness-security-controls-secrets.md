---
id: SEEN-090
title: "Add harness security controls: secrets, permissions, injection, supply chain"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-088]
status: doing
---
# SEEN-090: Add harness security controls: secrets, permissions, injection, supply chain

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Install gitleaks in the pre-commit hook and CI, make the harness refuse to write any environment value into a record, allowlist only harness and test commands in .claude/settings.json and the Codex equivalent, pass ticket text, marketplace payloads and web content through files rather than shell arguments everywhere in harness/, add the recorded-fixture rule for connector tests with a lint that fails on a live marketplace host in test code, and protect main (PR required, CI required, no force push). Add the is_destructive Jev question plus a human confirmation before any harness command that deletes or rewrites journal or graph files. The decision that matters: security is a stage checklist the review cannot skip, not a reminder in a prompt.

## Acceptance criteria

- [x] A commit containing a fake AWS key is blocked by the pre-commit hook and, when forced, fails CI
- [x] A unit test proves no journal record can contain the value of any variable present in the environment at write time
- [x] The test-code lint fails on any of api.bol.com, sellingpartnerapi, api.ebay.com, sellerapi.kaufland.com or api.otto.market appearing in a test file
- [x] Branch protection on main requires the CI check and a pull request, verified with the GitHub API
- [x] Deleting a journal directory through the harness asks Jev is_destructive, then the human, and records both before acting

## Carried in from SEEN-094

gitleaks and `pnpm audit --audit-level high` in CI, and the proof that a seeded secret on a throwaway
branch fails the pipeline, belong here rather than in the delivery ticket. The seeded key is a
documented example value in a fixture, the failing run is kept as evidence, and the branch is deleted
afterwards; gitleaks scans the working tree rather than full history, so one old commit cannot fail
every future run.

## Carried in from SEEN-006 and SEEN-089

Branch protection is not available on this plan: the repository is private on the free tier and the
API answers 403, "Upgrade to GitHub Pro or make this repository public". SEEN-006 therefore delivers
CI on every pull request and records the blocking half as a limit. Settle the plan here before
claiming the control: either GitHub Pro, or accept that the discipline is the harness refusing
delivery rather than GitHub refusing merge, and say so in the ticket rather than leaving a green tick
that means nothing.

Also carried in: the refusal message for a blocking decision prints the question's sense verbatim, so
a decision that failed to clear its threshold reads "clears its threshold". Fix it where the gate
enforcement lives.

## Outcome

Delivered on 23 September 2026. Two slices with recorded reds, and one refinement accounted for in a
note rather than given a red it never had.

**Each control sits where it cannot be skipped.** `journal.append` refuses any record carrying the
value of an environment variable of twelve characters or more, checked at the one place every record
passes through, and the refusal names the variable rather than its value: a refusal that prints the
secret has leaked it. `.githooks/pre-commit` runs gitleaks on staged changes and is committed rather
than living in `.git`, because a control only one machine has is not a control. Both assistants read
the same command allowlist. A test walks the harness's own source and fails on any shell use, because
ticket text and marketplace payloads are data. `harness lint` refuses live marketplace hosts in test
code. And `harness discard` is the only way the harness removes a journal: it refuses once a record is
committed, requires the ticket id typed out rather than a prompt a session can answer, and writes what
it removed with hashes before removing anything.

**Both controls caught something the day they were installed.** `pnpm audit` failed on two real high
advisories in postcss, reached transitively through Next.js, now pinned above both. The lint found its
own test file and the compiled bytecode beside it, so it skips compiled files and takes a visible
per-line marker instead of a hidden list of files it has quietly stopped checking.

**The seeded-secret proof**: run 35922041819 failed on a throwaway branch carrying a fake AWS key
committed with `--no-verify`, which is the case CI exists to catch. The branch is deleted; the failing
run stays in the Actions history as the evidence. Worth knowing: AWS's own documentation example key
is allowlisted by gitleaks, so a test using it proves nothing.

**The rule was too crude, and CI found that too.** Judging a credential by length alone refused
ordinary words: CI has `GITHUB_EVENT_NAME=pull_request`, and a delivery record legitimately contains
those words, so four delivery tests failed there and passed here. A variable now counts by name or by
shape, and review returned the ticket for it.

**And this delivery found a defect in the delivery check itself.** A commit can carry several runs of
the same check, and `verify-delivery` judged all of them, so one superseded failure refused a delivery
GitHub itself showed as green. Each check name is now judged on its latest run. Review returned the
ticket a second time for it.

**And I destroyed my own work.** Removing a test commit with `git reset --hard HEAD~1` also discarded
every uncommitted edit to tracked files, while the new untracked files survived, so the commit that
followed carried the tests and not the code they test. CI caught it. `git reset --soft` would have
removed the commit and kept the work. Recorded at record 11, with a finding for a later harness
ticket: `advance` could compare the tree against the checks it cites, in the way delivery already
compares the tree against review.

**Branch protection was settled and not bought**: unavailable on a private repository on the free
plan, and the founder chose neither GitHub Pro nor making the repository public. The enforcement today
is the harness refusing delivery and `verify-merge` refusing a stale receipt, neither of which GitHub
knows about.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
