---
id: SEEN-067
title: "Show Serve threads and drafts in the inbox"
epic: E5
epic_name: "Customer inbox and ops console"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-035, SEEN-063, SEEN-065]
status: todo
---
# SEEN-067: Show Serve threads and drafts in the inbox

| | |
|---|---|
| Epic | E5 Customer inbox and ops console |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Add the Serve pages in apps/web: open threads by marketplace with age and response window remaining, the drafted reply with the policy it applied, approve, edit and send, the mail threads from the forwarded mailbox, and the trust ramp panel from SEEN-065. Design decision: the send action reuses the approval inbox queue, so every reply follows the same approve, edit or reject path as a claim.

## Acceptance criteria

- [ ] Threads page lists open threads by marketplace with response window remaining
- [ ] A drafted reply can be approved, edited or rejected and the sent message shows in the thread
- [ ] Mail threads show the original forwarded mail and its attachments
- [ ] Trust ramp panel shows score, count and mode per action type

## Depends on

- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject
- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies
- [SEEN-065](SEEN-065-implement-the-trust-ramp-with-autonomy-per.md): Implement the trust ramp with autonomy per action type

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give tenants one inbox for approvals, findings, claims and statements and give ops one console for tenants, connections, runs and costs.
