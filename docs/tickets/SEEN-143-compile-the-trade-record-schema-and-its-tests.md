---
id: SEEN-143
title: "Compile the trade-record schema and its tests, which no compiler reads today"
epic: E0
epic_name: "Foundations and registrations"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-008, SEEN-114]
status: todo
priority: P1
---
# SEEN-143: Compile the trade-record schema and its tests, which no compiler reads today

| | |
|---|---|
| Epic | E0 Foundations and registrations |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (14,865 lines in the package that holds the money core, run by vitest and read by no compiler) |

## Description

`packages/core/tsconfig.json` includes `src/**/*` and nothing else, so the nine files of `packages/core/db/` are in no TypeScript project at all. They are not unchecked by accident of configuration drift: no project lists them, so `pnpm turbo run typecheck` compiles seven projects and none of them is these files. Vitest runs them, 196 tests across seven files on every `pnpm --filter @seen/core test`, because vitest transpiles rather than typechecks. So the trade-record schema, its RLS proofs, its tenancy and uniqueness and authority suites and the repository guard are executed constantly and compiled never.

The sizes say why that matters more than a configuration tidy. `db/tables.ts` is 1,725 lines, `db/repository.ts` 737 and `db/marketplaces.ts` 284, which is 2,746 lines of source; the six test files are 12,119, `db/schema.test.ts` alone 8,206. Fourteen thousand lines in the package whose other half is the money core.

SEEN-114 is why this is a ticket now rather than a sentence in a backlog. It turned on `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` and `noImplicitOverride`, and amended its own criterion 1 to read "the tree" as the seven projects `turbo run typecheck` compiles, because these nine files were outside the typecheck before it and widening the criterion would have meant doing this work inside that ticket. Its Outcome says what a ticket would have to carry and states plainly that no such ticket exists. This is that ticket, and the figures below are its measurements rather than new guesses.

Two things are needed and the second is the work. A second project, because `db/repository.ts` reads `import.meta.url` and the base configuration is `commonjs`, so these files need a project with an ESM module setting rather than an extra `include` line in the existing one. And then the diagnostics, measured at `main` with the four flags and an ESM module setting:

| compiled | diagnostics | where |
|---|---|---|
| the three source modules | 5 | all five in `db/marketplaces.ts`: two `TS2322`, two `TS2345`, one `TS2532`. `db/repository.ts` and `db/tables.ts` are clean |
| all nine files | 122 | 108 `TS2532`, 7 `TS18048`, 3 `TS2322`, 2 `TS2345`, 1 `TS2538`, 1 `TS2488` |

The 117 that arrive with the test files are almost all one shape: `noUncheckedIndexedAccess` on an array or record index, because a test that asserts on `rows[0].id` is indexing something the compiler cannot know is there. That shape is the reason the ticket is three points and not one, and it is also the reason it needs a stated rule before it starts, because there are two ways to make each one compile and only one of them is worth doing. A non-null assertion silences the compiler and leaves the test asserting on a value it has not established exists, which in a suite whose whole purpose is proving what the database refuses is the worst possible place to do it: a row that is unexpectedly absent would turn a real failure into a different error at a different line. The honest fix is the assertion the test already means, that the row is there, written so the compiler and the reader agree. The ticket should say which sites genuinely want `!` and why, rather than reaching for it 108 times.

What this ticket is not is a reopening of SEEN-008. That ticket is merged and its frontmatter still says `review`, because it was merged without a delivery receipt on Ruud's explicit decision, recorded in its journal at record 314 before the merge rather than after: `REVIEWED_TWICE` makes a Codex review mandatory for a ticket that touches billing and a migration, three Codex rounds died on usage limits, and the gate refused correctly. `done` is what a receipt earns and it has not earned one. So these files have an owner whose ticket has not closed, and two consequences follow. If SEEN-008 ever gets the Codex review it is owed, these files move under this ticket's feet, and the session working this one should check that before it starts. And nothing here should be read as evidence for SEEN-008's criteria: a file that compiles is not a schema that is correct, and SEEN-008's five criteria were measured by execution against the live database.

One judgement for the solution stage. Whether the six test files join the same project as the three source modules or a second one of their own. Separate projects would let the source modules reach the typecheck now and the tests follow, which is the smaller first slice and the more honest one if the 117 take longer than they look; one project is simpler and is what `apps/api` does for its own sources while excluding its tests, which is the configuration that let SEEN-114's three edited api test files go uncompiled. That precedent argues for including them.

## Slices

1. **The source modules compile.** A second project with an ESM module setting, the three source modules in it, the project in what `turbo run typecheck` builds, and the five diagnostics in `db/marketplaces.ts` fixed. The RED is the project compiling with five errors named.
2. **The tests compile.** The six test files in a project, and the 117 diagnostics fixed with the narrowing each test already means rather than with an assertion that silences it. The RED is the 117, and the slice's own risk is that the lazy fix passes it.

## Acceptance criteria

- [ ] Every file under `packages/core/db/` is in a TypeScript project, and `pnpm turbo run typecheck` compiles it with the four flags SEEN-114 turned on
- [ ] `tsc` reports no diagnostic for `packages/core/db/`, with the five in `db/marketplaces.ts` fixed as defects rather than suppressed
- [ ] No new non-null assertion is added to make a test compile unless the ticket says why that site is the exception, and the count of them before and after is recorded
- [ ] The 196 tests of `packages/core` still pass, and the suite still refuses what it refused before: the fix changes what the compiler sees and not what the database is asked
- [ ] A RED per slice: the project compiling with its diagnostics named, before each is fixed
- [ ] SEEN-114's criterion 1 amendment is answered in this ticket's Outcome, so a reader of either knows the deferred work is done and where

## Depends on

- SEEN-008: Create trade-record schema v1 with tenant_id and RLS on every table. It wrote all nine files. It is merged and still at `review` with no receipt, by the decision in its record 314, so it owns these files and has not closed.
- SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds. It turned on the four flags, measured this gap, and deferred it here.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The measurements: SEEN-114's checks 253 (the nine files), 254 (the three source modules, five diagnostics) and 277 (all nine, 122), and its criterion 1 amendment
- The decision this ticket must not disturb: SEEN-008's journal record 314
- Epic goal: Stand up the monorepo, the EU infrastructure and the trade-record schema, and file every day-0 registration so nothing waits on a marketplace later.
