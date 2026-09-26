---
id: SEEN-106
title: "Enforce the harness with hooks in both assistants, generated from one source"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-092]
status: doing
---
# SEEN-106: Enforce the harness with hooks in both assistants, generated from one source

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

The skill tells a session what to do; a hook makes the assistant unable to do otherwise, and both assistants run the same lifecycle events with the same JSON shape (Claude Code in .claude/settings.json, Codex in .codex/hooks.json). harness/hooks.json is the single source; harness sync generates both copies, keeping the graphify hook-guard entries and the permissions, and doctor reports drift. The hooks, each a harness command reading the hook's JSON on stdin: SessionStart runs harness status --brief for the ticket of the current branch and injects it as additionalContext, so a session starts from the handoff pack rather than from the PRD; UserPromptSubmit runs harness budget and injects a warning once the session is over budget; PreToolUse on Edit, Write and MultiEdit runs harness guard <path>, which blocks with a reason (exit 2) an edit to code while the ticket is at clarify or solution, an edit on a branch that is not the ticket's, and an edit outside the files the accepted slice names, and allows the ticket file and .harness-drafts/ at every stage; PreCompact runs harness handoff --auto so the pack exists before the context is summarised; SubagentStop for seen-reviewer validates the findings JSON and drafts the review record; Stop runs harness doctor --quick for the ticket. The decision that matters: enforcement lives in harness commands with tests and fixtures, and the hook files are generated, never edited by hand.

## Acceptance criteria

- [ ] harness sync generates the hooks section of .claude/settings.json and .codex/hooks.json from harness/hooks.json, preserving the graphify hooks and the permissions, and doctor reports a hand edit of either copy
- [ ] harness guard blocks an edit to packages/ or apps/ while the ticket is at clarify or solution, an edit on a non-ticket branch and an edit outside the accepted slice's files, each with a reason, and allows the ticket file and .harness-drafts/ at every stage, proven with hook-input fixtures for both assistants
- [ ] SessionStart injects the handoff pack and UserPromptSubmit injects a budget warning once the session is over budget, proven with fixtures
- [ ] PreCompact writes the handoff pack before compaction, and a test proves it is written when the trigger is auto
- [ ] The hooks run in a Codex session: /hooks lists them and a blocked edit is refused there too, recorded as a verification in the journal

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
