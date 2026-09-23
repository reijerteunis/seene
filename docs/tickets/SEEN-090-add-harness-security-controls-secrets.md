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
status: todo
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
| Status | todo |

## Description

Install gitleaks in the pre-commit hook and CI, make the harness refuse to write any environment value into a record, allowlist only harness and test commands in .claude/settings.json and the Codex equivalent, pass ticket text, marketplace payloads and web content through files rather than shell arguments everywhere in harness/, add the recorded-fixture rule for connector tests with a lint that fails on a live marketplace host in test code, and protect main (PR required, CI required, no force push). Add the is_destructive Jev question plus a human confirmation before any harness command that deletes or rewrites journal or graph files. The decision that matters: security is a stage checklist the review cannot skip, not a reminder in a prompt.

## Acceptance criteria

- [ ] A commit containing a fake AWS key is blocked by the pre-commit hook and, when forced, fails CI
- [ ] A unit test proves no journal record can contain the value of any variable present in the environment at write time
- [ ] The test-code lint fails on any of api.bol.com, sellingpartnerapi, api.ebay.com, sellerapi.kaufland.com or api.otto.market appearing in a test file
- [ ] Branch protection on main requires the CI check and a pull request, verified with the GitHub API
- [ ] Deleting a journal directory through the harness asks Jev is_destructive, then the human, and records both before acting

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
