---
id: SEEN-087
title: "Install graphify, build the repo graph and wire it into both assistants"
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
# SEEN-087: Install graphify, build the repo graph and wire it into both assistants

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

Install graphify (uv tool install graphifyy), register it for Claude Code and Codex, build the graph of the repository, docs and SQL schema into graphify-out/, install the git hook so the graph rebuilds on commit and branch switch, run python -m graphify.serve graphify-out/graph.json as an MCP server in both assistants, and add graphify extract to CI so GRAPH_REPORT.md is produced on every run. Add harness graph <ticket> <impact|path|explain|prs> in harness/run.py as a thin wrapper that writes the answer into the journal. The decision that matters: graphify-out/graph.json is committed so a fresh clone has context before its first build; code extraction is local and deterministic, and only the docs pass uses a model.

## Acceptance criteria

- [x] graphify claude install and graphify install --platform codex both succeed and /graphify query works in a Claude Code session on this repository
- [x] The graph is refreshed by CI on every push and by verify-delivery locally, so a commit changing harness/ or packages/core is reflected in graphify-out/graph.json without anyone remembering (amended on 23 September 2026: the post-commit hook was uninstalled after it broke four git operations in one session by leaving the tree dirty behind every commit, including a 20,000-line conflict in graph.json on three rebases; the graph now refreshes on the same cadence as the receipt and the coverage baseline)
- [x] The MCP server exposes query_graph, get_neighbors, shortest_path and get_pr_impact to Claude Code and Codex and a query for the stage gate returns its callers (re-pointed from the policy gate, which arrives with SEEN-033)
- [x] CI runs graphify extract --code-only and fails when the graph does not parse; GRAPH_REPORT.md is an artefact of the run
- [x] harness graph SEEN-087 impact writes the impact set into the journal as a note

## Clarified

Recorded in the journal on 23 September 2026, record 3. SEEN-087 runs before SEEN-006 rather than
after it, so two acceptance criteria are re-pointed at code that exists: `harness/` in place of
`packages/core`, and the stage gate in place of the policy gate. SEEN-006 re-verifies both. CI runs
the deterministic code-only extraction, with no API key and no per-build token spend. The MCP server
is the `graphify-mcp` executable rather than `python -m graphify.serve`, because a uv tool install
isolates the package from the system python.

## Amended after delivery

The post-commit and post-checkout hooks were uninstalled on 23 September 2026, during SEEN-089. They
rebuilt the graph in the background after every commit, which left `graphify-out` dirty and broke four
git operations in one session: two branch switches, two pulls, and three rebases that had to resolve a
20,000-line conflict in `graph.json`. The graph is still committed, as this ticket decided, and still
refreshed: CI rebuilds it on every push, and `verify-delivery` refreshes it locally, which is the same
cadence as the receipt and the coverage baseline. The merge driver stays configured.

## Outcome

Delivered on 23 September 2026, receipt
`ad970cff216b935b8587072533a986399de4bc372ce4489094f103db7eb19e2d`, pull request #2.

The first ticket worked entirely through the harness: 19 journal records, one return, two attempts.
`harness doctor` verifies the chain, and `shasum -a 256 docs/harness/history/SEEN-087/0019.json`
reproduces the receipt without the harness.

**The graph**: 371 nodes, 926 edges, 12 communities over the 36 code files, deterministic AST pass,
no API key, committed with `GRAPH_REPORT.md`. CI rebuilds it on every push and keeps the report as
an artefact.

**Five review findings, all resolved.** Four were things graphify's own installers got wrong for
this repository: the fingerprint counting the graph directory (which would have refused every future
delivery), an absolute machine path in the PreToolUse hooks, an MCP server that could not start for
want of its `mcp` module, and `core.hooksPath` still pointing at the deleted project so no hook would
have run at all. The fifth is a deliberate limit: the 103 documents are not in the graph, because the
semantic pass uses a model.

**One defect escaped the receipt.** The CI step asserting the graph parses read `edges`, while
graphify writes node-link JSON with `links`, so the graph job was red on the delivered commit. The
receipt was still written, because SEEN-086's `verify-delivery` is offline by design and does not
look at CI. The fix is commit-after-receipt, so the receipt attests commit `0fe02dc`, one commit
behind the branch tip. That gap is now SEEN-089's, which carries both halves: refuse a delivery whose
checks are not green, and compare the receipt's commit to the tip at merge.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
