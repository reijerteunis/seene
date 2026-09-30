---
id: SEEN-022
title: "Generate the audit PDF with scorecard and line annex"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-021]
status: todo
---
# SEEN-022: Generate the audit PDF with scorecard and line annex

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Build the audit report in apps/api with a headless renderer: a cover with the 90-day window, a scorecard per marketplace (settled amount, fees charged, fees expected, findings by rule, recoverable amount, deadlines at risk) and a line-by-line annex listing every finding with its evidence refs. Report data comes from the findings view and settlement totals so the PDF never computes money itself.

Where the PDF may be uploaded is settled by SEEN-008. The trade record schema constrains `evidence.storage_path` to begin with the row's own `tenant_id`, and that check binds the text a row holds and not the object an upload wrote: a check constraint cannot read `storage.objects`. A deletion on request finds a tenant's objects by sweeping the bucket for that same prefix, so an object uploaded outside it survives the erasure with nothing able to say whose it was, which SEEN-008 measured as F63. The reason is in `supabase/migrations/20260930000001_trade_record_v1_evidence_and_billing.sql` and on the comment of `public.evidence`, and `packages/core/db/schema.test.ts` goes red if the criterion below leaves this ticket.

## Acceptance criteria

- [ ] POST /tenants/:id/audits generates a PDF for a 90-day window in under 60 seconds for 10,000 settlement lines
- [ ] Scorecard totals equal the SQL view totals to the cent in a test fixture
- [ ] Annex lists every open finding with rule, amount, external ids and deadline
- [ ] PDF stored in the evidence bucket under the tenant's own prefix, so the object name begins with the tenant_id and a slash, with its sha256 recorded on the audit row

## Slices

The starting slice plan, one session each; the solution stage adopts or amends it (SEEN-104). A slice is at most 2 points and a ticket has at most four.

1. Report data: the findings view and settlement totals as the only sources (2 pt). RED: the scorecard totals equal the SQL view totals to the cent
2. Cover, scorecard per marketplace and the line annex rendered headless (2 pt). RED: a fixture with 10,000 lines renders in under 60 seconds
3. Storage in the evidence bucket with sha256 on the audit row (1 pt). RED: the stored object's name begins with the tenant_id and its hash equals the hash recorded on the audit row

## Depends on

- [SEEN-021](SEEN-021-persist-findings-with-rule-confidence-evidence.md): Persist findings with rule, confidence, evidence refs and deadline

## Blocks

- [SEEN-025](SEEN-025-run-three-real-90-day-audits-and-deliver-the.md): Run three real 90-day audits and deliver the PDFs

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
