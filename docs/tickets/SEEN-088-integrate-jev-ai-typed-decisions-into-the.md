---
id: SEEN-088
title: "Integrate Jev AI typed decisions into the harness gates"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086]
status: done
---
# SEEN-088: Integrate Jev AI typed decisions into the harness gates

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

Add harness/jev.py calling POST https://api.typesafe.ai/v1/systemone with model jev-latest, the stage record as the state, and a map of typed questions in one request: clarified (noul), risk (score low, medium, high), solution_complete (noul), touches_billing_or_policy_gate (noul), finding severity (score low, medium, high, blocking), must_fix (noul), is_destructive (noul). A noul answer comes back as a single probability, a score as a weighted value with a legend, per-level probabilities and a confidence. Wire harness decide <ticket> --question <name> and call the questions automatically on advance for the stage they belong to; thresholds live in harness/thresholds.toml. Every call writes the question, the probabilities, the threshold and the outcome to the journal. When JEV_API_KEY is missing or the API fails, the harness asks the human, records the fallback, and continues. The endpoint and model above were established from https://docs.typesafe.ai/api.md on 23 September 2026 and verified with a live call; the thejevai.com host this ticket originally named is the playground, which rejects API credentials. The decision that matters: Jev is a decision layer for the procedure only; it never edits code, never touches a marketplace and never decides a product action.

## Acceptance criteria

- [x] harness decide SEEN-088 --question risk returns a score with per-option probabilities and appends a decision record with model, question, probabilities, threshold and outcome
- [x] advance from clarify is refused when clarified is below the policy threshold (0.8 by default) and the refusal names the open question from the record
- [x] advance from solution adds the security checklist and a second-reviewer requirement to the review template when touches_billing_or_policy_gate is yes
- [x] With JEV_API_KEY unset, every decision point prompts the human and records fallback: human in the journal instead of failing
- [x] The key is read from .env.local only; a unit test asserts that no decision record contains the key or any environment value

## Outcome

Delivered on 23 September 2026 after one reopen. 35 journal records, three attempts, one return and
one voided receipt.

**The first delivery was against a service that does not exist.** The ticket named
`thejevai.com/v1/systemone` with model `typesafe/jev-1.13`. That host is TypeSafe's playground: it
rejects API credentials, which is why two valid-looking keys came back as `Invalid API key` and why
the endpoint was blamed last rather than first. The real contract, from
https://docs.typesafe.ai/api.md, is `POST https://api.typesafe.ai/v1/systemone` with model
`jev-latest`, a map of questions in one request, a noul answered as a single probability, and a score
answered by level index with a legend, a weighted value and a confidence. The ticket text and
`docs/harness/workflow.md` are corrected at the source, so no later session inherits the wrong facts.

**It is verified live.** Record 29 is the first real judgement this harness has taken: Jev rated this
ticket's own risk `medium` at 0.65, score 1.31, confidence 0.48. Record 34 carries the review gate's
own decisions, `severity: blocking` at 0.78 and `must_fix: no` at 0.42, both from `jev-1.13.0`.

**The receipt for the wrong implementation was voided, not patched.** SEEN-093 was built for exactly
this: record 26 voids receipt `10215e20...` with its reason, the receipt file is untouched, and the
journal reads receipt, void, rework, second receipt. Two earlier tickets were patched after their
receipts instead, and that is the habit this replaced.

**Three defects found in review, all resolved**: the wrong service (blocking), invented answer shapes
(high), and questions carrying no criteria, so the model was given a bare question and no rubric
(medium).

**Earlier in this journal**: the gate was inverted on `must_fix`, every test would have called the
live API, requiring a judgement before every advance would have made the harness unusable without a
key, and the transport could never have reached the API at all because Cloudflare rejects Python's
default user agent. Record 8 is a meaningless check, disowned in the note at record 9.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
