---
id: SEEN-144
title: "Tell a path the branch deleted from a typo in the plan"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-113]
status: todo
priority: P1
---
# SEEN-144: Tell a path the branch deleted from a typo in the plan

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (it turns every return on a ticket that deletes a file into a full replay) |

## Description

SEEN-113 exists so that a tdd record can cite evidence a return did not invalidate: the test is the code rather than the attempt, scoped to the files the cited slice names, so a ticket returned twice does not have to re-prove slices whose tests never moved. One deleted file in a slice plan defeats it, and then every citation on that ticket is compared over the whole tree for the rest of its life.

The mechanism, in two steps. `_unresolved_in` asks `git ls-tree -r --name-only <commit> -- <path>` for each path the plan names, against the commit holding the tree the cited check ran on, and an entry that matches nothing costs the whole scope: the comparison falls back to `after == tree`, over everything. That rule is right and it was earned. F2 of SEEN-113's second review found that a plan naming a typo for the file its work is in, or naming a gitignored path, accepted a citation however much the code had moved, and F6 of the third found that a path git will not take as a pathspec at all does the same. An entry nothing resolves is an untrustworthy scope rather than an empty one.

A file the branch deleted resolves nowhere either, and that test cannot tell it from a typo. SEEN-114's slice 1 named `eslint.config.mjs` because part of its work was deleting it: Biome replaced ESLint. The plan named it correctly, the slice did what it said, and from then on every citation on that ticket was unscoped.

What makes that expensive rather than merely untidy is the second step. The tree the comparison falls back to is `repository.fingerprint()` with no exclusions, so the ticket file is in it, and the procedure rewrites the ticket file between the regression and the advance on every ticket by design: the status, the ticks and the Outcome go in before the gate that decides whether the review passes. So an unscoped citation is not unlikely to fail, it is certain to.

Measured on SEEN-114. At attempt 14 the only thing that had moved since the cited checks was the ticket file, two citations repointed at a regression that had not been recorded yet, and all seven pairs were refused with `compared over the whole tree because the plan names eslint.config.mjs, which git cannot see in the tree it ran against`. The repair was to record seven pairs and a regression again, about twenty-five minutes, for evidence that was already true. The same sentence appears at attempt 9's refusal, where a test file had genuinely moved as well, so that one would have been refused by the scoped comparison too and is not a second instance of this defect: one decisive case, named as one.

The distinction the fix turns on is available and cheap. A typo resolves nowhere, ever, at any commit. A file the branch deleted resolves at the branch point, which is what makes it a correctly named entry whose work was its own deletion. So ask `git ls-tree` of the merge base as well as of the check's commit: an entry that resolves at neither is still a typo and still costs the whole scope, which keeps F2's and F6's protection whole; an entry that resolved at the merge base and not in the check's tree is a path this branch deleted, and it costs nothing. Whether the deleted path then joins the compared set is its own small question, and the honest answer is that it should: a file that is absent from both trees cannot have moved between them, so comparing it is free and says so.

There is a second, independent fix and the solution stage should weigh it on its own merits rather than as an alternative. The whole-tree fall-back could leave out the ticket file, the way SEEN-107's review gate already leaves it out of the comparison it makes for exactly this reason, because the procedure writes it between the triage and the advance every time. That change alone would have saved SEEN-114's replay even with the scope lost, and it is the difference between a fall-back that is strict and one that is unconditional. Both fixes are small, they are not substitutes, and the ticket can carry both.

One thing to be careful of. The scope is not only the cited slice's own files: a round that declares no position is judged over every file the plan names, which is wider and so stricter, and that is where `eslint.config.mjs` reached SEEN-114's rework rounds. A fix that looked only at the citing slice's own entries would leave the null-position rounds, which is what every review round records, exactly as broken.

## Acceptance criteria

- [ ] An entry a slice plan names that this branch deleted does not cost the scope, and the citation is compared over the files that do resolve
- [ ] An entry that resolves at neither the merge base nor the check's commit still costs the whole scope, with F2's typo case and F6's unusable pathspec both still refused and both still named in the message
- [ ] A round that declares no position gets the same treatment, since its scope is every file the plan names and that is where the defect was met
- [ ] The whole-tree fall-back leaves out the ticket file, or the ticket records why it should not, with the reason weighed against SEEN-107's precedent for the review gate
- [ ] A RED per criterion, replaying SEEN-114's own case: a plan naming a deleted file, a citation whose slice files have not moved, and a ticket file that has, refused before the change and accepted after
- [ ] The whole harness suite is green, and no citation that is refused today for a reason other than this one becomes accepted

## Depends on

- SEEN-113: Let a tdd record cite the evidence a return did not invalidate. It built the exemption, the scoping and the two refusals this ticket narrows without removing.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The code: `_unresolved_in`, `_the_files_the_round_moved` and `cited_check` in `harness/gates.py`, and the `tree = repository.fingerprint()` the tdd gate passes them
- The evidence: SEEN-114's attempt 14, where seven pairs were refused and replayed because a ticket file had moved and a deleted file had cost the scope. Its journal records the replay; the refusal is the sentence quoted above.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
