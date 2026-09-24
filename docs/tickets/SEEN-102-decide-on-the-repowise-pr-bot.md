---
id: SEEN-102
title: "Decide on the repowise PR bot for a private repository"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 0
executor: human
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-098]
status: parked
---
# SEEN-102: Decide on the repowise PR bot for a private repository

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | human decision |
| Executor | human (Ruud) |
| Changes an agent action | no |
| Marketplaces | none |
| Status | parked (waiting for SEEN-103) |

## Description

The repowise PR bot puts change risk, blast radius at symbol level, tests that may break and missing
co-changes on every pull request, with no LLM call. It is a GitHub App
(`github.com/apps/repowise-bot`), so installing it is an authorisation on this repository made through
a browser by the account owner.

Two things to decide with, both from SEEN-098's journal at record 4:

**Read access.** The app reads the whole tree. This repository will hold the trade record schema, the
claims logic and the configuration around marketplace credentials, though never the credentials
themselves, which live in Secret Manager. Granting a third party read on a private repository is a
decision about who sees Seen's code.

**A public page per pull request.** The bot's comment links to `repowise.dev/pr/<owner>/<repo>/<number>`,
which repowise documents as public with no sign-in. For a private repository that is a disclosure
rather than a convenience, and it is worth confirming what that page shows before deciding, not after.

Nothing in the harness depends on this. `harness graph why`, `health` and `risk` and the change-risk
answer carried into the risk decision all read the local index and work without it.

## Acceptance criteria

- [ ] What the public per-PR page shows for a private repository is established by looking at one, and recorded
- [ ] A decision is recorded under `## Outcome`: install, decline, or revisit when the repository goes public
- [ ] If installed, one pull request carries a bot comment and the absence of an LLM key is recorded with it
- [ ] If declined, SEEN-098's fourth criterion is marked as decided rather than left open

## Depends on

- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Split out of SEEN-098 on 24 September 2026, recorded in that ticket's journal at record 4.
- The repository was deliberately kept private and branch protection deliberately not bought, both recorded in earlier tickets. This decision belongs to the same set.
