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
status: review
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
| Status | review |

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

- [x] What the per-PR page shows is established by looking at one and recorded; what a **private** repository's page shows is recorded as unresolved, because establishing that requires installing the bot on a private repository, which is the decision itself
- [x] A decision is recorded under `## Outcome`: declined, with two conditions that reopen it
- [ ] Not applicable: nothing was installed, so there is no bot comment to record
- [x] SEEN-098's fourth criterion is marked as decided and declined, pointing here

## Depends on

- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Split out of SEEN-098 on 24 September 2026, recorded in that ticket's journal at record 4.
- The repository was deliberately kept private and branch protection deliberately not bought, both recorded in earlier tickets. This decision belongs to the same set.

## Outcome

**Declined, 24 September 2026.** Ruud's call, in his words:

> Why:
>   - Contents: Read on the whole private tree
>   - repowise servers clone the repo to index it
>   - Per-PR page public-vs-private: UNRESOLVED (/privacy and /security both 404)
>   - 15 USD/month before it says a word
>   - Nothing in the harness depends on it
>
> Revisit when: seene goes public, or repowise states the page is access-controlled for private repos.

### What was established

The GitHub App asks for **Contents: Read, Pull requests: Write, Metadata: Read, Issues: Write**. The
first is read access to the whole tree, not to a pull request's diff.

The bot page says "No clone, no LLM, no token cost" and "Read-only. No code execution." The pricing
page says the repository is cloned onto "an ephemeral indexing container," parsed into a graph, and
"the cloned working tree is wiped at the end of every run," with derived artefacts kept. Both can be
true at once, the bot reading an index an indexer cloned to build, and the material fact is the second:
repowise's servers would clone this private repository. They state they never use code to train a
model.

Public repositories are free and uncapped. **Private repositories index for free but their PR comments
require the Pro plan at 15 USD per month**, and the bot stays silent on private-repo pull requests
until the owner upgrades. `reijerteunis/seene` is private, so installing it buys nothing until a
subscription starts.

The live example page, read without signing in, carries the pull request title and author, the commit
hash, a change-risk score and percentile, repository health, changed contracts with file paths and line
numbers, outside callers in untouched files, introduced findings by severity, primary authors by file
with commit percentages, the tests that import the changed modules, and an AI-versus-human attribution.
No source snippets and no email addresses.

### What could not be established

**Whether a private repository's per-PR page is also public is not stated anywhere in the public
material.** The README lists "Public analysis page per PR, no sign-in" as a feature with no carve-out
for private repositories, and `/privacy` and `/security` both return 404. The absence of a carve-out is
not a statement that there is none, so it is recorded as unresolved.

The first criterion asked for this to be established by looking at a private repository's page. That
cannot be done without first installing the bot on a private repository, which is the decision being
made. What would settle it is repowise saying so, or an installation on a throwaway private repository.
Neither was done, because a decline needs neither.

### What this is not

Not a judgement on the bot, which does something this project believes in: a review comment with no
model behind it, deterministic, the same twice for the same diff. It is a judgement on the trade. A
private repository whose file names are a product roadmap, read in full by a third party, for a page
whose visibility nobody could establish, at a monthly cost, for a surface answering questions the local
index already answers through `harness graph` and the risk decision.

### Two conditions reopen this

`reijerteunis/seene` becoming public, where the bot is free and there is nothing left to expose, or
repowise stating that a private repository's per-PR page is access-controlled. Either one reopens this
ticket rather than starting the argument again.

### A note on how it got here

This was the first non-code ticket the harness has seen, and it parked at the solution gate, which
required `tests_first` of every ticket while non-code mode was declared a stage later. SEEN-103 moved
the declaration, and this ticket's solution record at record 6 is the first to use it.
