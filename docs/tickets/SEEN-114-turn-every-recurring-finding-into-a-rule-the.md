---
id: SEEN-114
title: "Turn every recurring finding into a rule the pre-commit hook runs in seconds"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-090, SEEN-107]
status: review
priority: P0
---
# SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | review |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Sprint 0 delivered 63 review findings on 20 tickets (2 blocking, 18 high, 27 medium, 16 low) and 0.79 returns per ticket. A finding a static rule could have caught is a finding paid for three times: the reviewer's reading, the return, the second review. Put the rules in front of the model. TypeScript strict with noUncheckedIndexedAccess, exactOptionalPropertyTypes and noImplicitOverride; Biome for format and lint with the typed rules on; ast-grep rules that encode the ground rules (cents as integers, no euro sign, no em dash, no cloud SDK import outside the provider packages, no live marketplace host in a test, no any, no floating promise); dependency-cruiser for the layering (packages/core imports nothing from apps or connectors and no IO library at all, no node:fs, fetch, pg or bullmq; connectors never import agent and reach the network only through the generated clients; a marketplace write is reachable only through the policy gate module; database access goes through the repository layer; no app imports another app); knip for dead exports, with an exports map per package so nothing reaches into another package's internals. Each rule cites the finding that created it or the architecture section that states it, so a rule nobody can trace is a rule to delete. Every review finding at medium or above carries rule_candidate (a rule id, or the reason none can catch it); harness report --week lists the findings a rule could have caught and the rules added since, and a rule candidate that recurs twice without a rule is a doctor warning. The pre-commit hook runs the rule set on staged files in under ten seconds; CI runs it on the tree. The decision that matters: a rule is written the week its finding appears, by the ticket that got the finding, so the review reads less every sprint.

## Acceptance criteria

- [x] tsconfig.base.json carries strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes and noImplicitOverride, and every TypeScript project in the tree typechecks. **Amended on 1 October 2026:** "the tree" is read as the seven projects `pnpm turbo run typecheck` compiles, because `packages/core/tsconfig.json` includes only `src/**/*` and so the eleven modules of `packages/core/db/`, which are SEEN-008's trade-record schema and its tests, are in no project at all and were already outside the typecheck before this ticket. Compiling them needs a second project with an ESM module setting, because `db/repository.ts` reads `import.meta.url` and the base configuration is commonjs, and two of them carry genuine errors under the new flags. That is a ticket of its own, named in the Outcome.
- [x] Biome, ast-grep and dependency-cruiser run on staged files in the pre-commit hook in under ten seconds, and in CI on the tree, with the ground rules above each proven by a fixture that fails (among them: node:fs imported inside packages/core, a marketplace write outside the policy gate, a query outside the repository layer)
- [x] Every review finding at medium or above carries rule_candidate, and the review gate refuses a record without it
- [x] harness report --week lists findings a rule could have caught, the rules added, and any candidate that recurred without a rule
- [x] knip reports zero unused exports on packages/core and the connectors, every package declares an exports map, and each rule in the set cites a finding id or an architecture section, enforced in CI

## Depends on

- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff

## Blocks

- [SEEN-135](SEEN-135-branded-money-and-ids-one-schema-per-boundary.md): Branded money and ids, one schema per boundary: the compiler catches the wrong-unit and wrong-id findings

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

Delivered on 1 October 2026 in four slices: the compiler and the formatter with the registry, the
ground rules with their fixtures and the hook, `rule_candidate` on the review gate, and the loop back
through the weekly report and `doctor`. Twenty-two rules, each with a citation a reader can open and a
fixture the rule itself refuses. 1,521 harness tests pass, coverage on `packages/core` is 100.0 with a
delta of 0.0, `doctor` reports no problems and no warnings.

### What runs, and how fast

| Where | What runs | Measured |
|---|---|---|
| pre-commit, on the staged paths | gitleaks, then Biome, ast-grep and dependency-cruiser | 0.66s over 51 staged paths, against a ten-second budget |
| CI, harness job | `harness rules --check` | reads files, needs no workspace |
| CI, monorepo job | `harness rules --fixtures`, then `turbo run lint`, then `scripts/rules.sh tree` | 1.45s for the whole set over the tree |

`scripts/rules.sh` is the one definition of what running the set means, called by the hook and by CI,
because SEEN-097 recorded what happens when the same environment has two definitions. knip is in CI
and not in the hook: a dead export is a property of the whole import graph and cannot be judged from a
staged file.

### The twenty-two rules

Four compiler flags, four Biome rules, five ast-grep rules, eight dependency-cruiser layering rules
and knip. `rules/registry.toml` is the one place each says what it stands on, and `harness rules
--check` reads it against the tools' own configurations **in both directions**: a rule a configuration
enables that the registry does not carry fails the build, and so does a registry entry for a rule
nothing runs, because a registry that only had to be a superset could be padded. A citation is the
finding a rule came from, as `SEEN-097 F1`, or a document in the tree; a bare ticket id is refused,
because every rule was added by some ticket.

Two rules have a real finding behind them rather than a ground rule.
`ast-grep/no-credential-literal-in-tests` cites SEEN-097 F2, where `stack.test.ts` carried the local
Supabase service-role JWT as a literal fallback and gitleaks did not catch it.
`dependency-cruiser/no-cloud-sdk-outside-providers` cites SEEN-097 F1 and replaces
`packages/providers/src/boundary.ts`, a source-text search that reported the wrong line, reported line
0 for an import broken over several lines, and had to be taught `require` and dynamic `import()` one
grammar at a time. A resolver reads every grammar; both that module and its test are deleted.

Three decisions worth a reader's attention. Biome replaces ESLint rather than running beside it, because
two linters are two authorities on style and SEEN-118 makes Biome the authority. One rule, one owner:
`harness lint` keeps "no live marketplace host in a test" because it reads every tracked file in any
language, where an ast-grep rule would read only TypeScript. And `dependency-cruiser/core-no-io` is
scoped to `packages/core/src/**` and says in its own registry entry that the complete instrument for
that package is the allow-list in `packages/core/db/repository.ts`, which admits four specifiers and
reads the compiler's own pre-processor; this rule is the ten-second half of it, which matters because
`packages/core`'s suite needs the Supabase stack and a laptop without it never sees the allow-list
before CI.

### An absence is never a pass

`harness rules --fixtures` reports four things as what they are rather than as a proof: a tool that is
not installed, a fixture directory with nothing in it, a fixture its own rule accepts, and a tool whose
configuration is missing. The last was measured while this was being written, and it is the one that
would have been invisible: `biome/recommended` read as firing with no `biome.json` in the tree, because
Biome's defaults include the recommended set, so the fixture was proving the tool's defaults and not
this repository's rules. A compiler flag is proven by compiling its fixture twice, once with the flag
the base configuration sets and once with that one flag off, because tsc names the option in its
message for one of the four and not the others.

### What the rule set found on its own first run

`biome check --write --unsafe` broke a controller. Without
`javascript.parser.unsafeParameterDecoratorsEnabled`, Biome cannot parse a NestJS parameter decorator,
so it read the injected `ThreadStore` as an unused parameter and the unsafe fix renamed it to
`_threads` while `this.threads` still read the old name. That is a TypeError on every inbound mail,
applied by a tool, in a file nobody was looking at. The configuration now carries the option, the
rename is reverted, and two rules came out of it that no tool can hold: the unsafe fixes are read one
at a time by hand and never written across a tree, and a linter's first run on a framework's code is a
measurement of the linter's configuration before it is a measurement of the code.

### The loop back

`rule_candidate` is required on every finding at medium severity or above, in one of three shapes: a
rule id in the registry, a rule id not in it yet, or `none: <reason>`. The check sits outside the
`resolved` branch, so a return's findings owe it too: a defect serious enough to return a ticket on is
serious enough to ask what would have caught it. The rule-id shape is built from
`rules.CONFIG_FOR_TOOL` rather than restating the tool list.

`harness report --week` carries four figures, not the three the criterion asks for. The fourth is the
count of findings in the window that predate the field, because a finding recorded before this ticket
carries none and a report that counted those as "no rule could have caught it" would read as though
every old finding had been triaged against the rule set. Today a reader sees: 0 findings a rule could
have caught, all 22 rules added this week, no candidate recurring without a rule, and 11 findings that
predate the field. A candidate that recurred twice with no rule written is a `doctor` **warning** and
not a problem, leaving `ok` true, because `doctor` runs in CI and at the end of every turn through the
Stop hook and a problem there would block every unrelated ticket until somebody wrote a rule.

### Carried for other tickets

**`packages/core/db` is in no tsconfig project.** Eleven modules, SEEN-008's schema and its tests, are
never compiled by `pnpm turbo run typecheck`. Criterion 1 is amended above with the reason. Compiling
them needs a second project with an ESM module setting, because `db/repository.ts` reads
`import.meta.url` while the base configuration is commonjs, and `db/marketplaces.ts` carries two
genuine `exactOptionalPropertyTypes` and `noUncheckedIndexedAccess` errors. Its own ticket.

**`harness/guard.py` compares a path to the slice's file list exactly**, where `harness/gates.py`
answers the same question with `_covers`, which reads a directory entry. So a slice naming
`rules/fixtures` is refused a file inside it. That inconsistency is why one slice of this ticket wrote
two paths through a shell and another stopped and reported: the difference was the guard, not the
agents. Journal record 36.

**A tdd record cannot cite evidence from before a return when the plan's slices name overlapping
directories.** SEEN-113's repair scopes the tree comparison to the cited slice's files, granted only
when an already accepted tdd record says which slice a check proved; a ticket that returns before ever
advancing out of tdd has none, so the comparison falls back to the whole tree, which has moved by
definition. And here even the scoped comparison would have failed, because the first amendment widened
slices 1, 2 and 4 to name `apps`, `packages`, `rules/fixtures` and `harness/rules.py`, so no slice's
files were stable once a later slice ran. The plan caused it and the gate was right. Journal records 52
and 63 carry the diagnosis and the replay; the two questions it raises, where the first corroboration
comes from and whether the solution gate should refuse a plan whose slices overlap, belong to a harness
ticket of their own.

**The paragraphs SEEN-139 reverted are no longer this ticket's to restore, and were.** SEEN-139's docs
regeneration was built from a branch point before SEEN-106, SEEN-107, SEEN-109 and SEEN-111 landed and
reverted ten paragraphs of `docs/harness/workflow.md`, which the guard SEEN-107 wrote caught, and CI
had been red on main since. This ticket carried the repair as commit `c43bc57` on Ruud's decision,
because it already edited that document. SEEN-140 then needed the same repair to make its own
regression exit zero, cherry-picked `c43bc57` with `-x`, and merged first; the rebase onto main
dropped the commit from this branch as already upstream, which is what a cherry-pick is for. So the
restore is in main and is not in this diff, and this paragraph says so rather than leaving a claim
about a commit a reader would not find.

### What it cost

Four slices against a three-point estimate, planned at seven points and delivered in four sessions, one
orchestrating and three implementers. Two returns to solution against a target of 0.5 per ticket, and
both were the same mistake in a different place: a solution record that named the files a change is
written in and not the files the change makes fail. First the formatter rewriting twenty-six files,
then a required field invalidating nine fixtures. The cheap version of that question is "what does this
make red", asked once at solution, and neither return would have been needed.
