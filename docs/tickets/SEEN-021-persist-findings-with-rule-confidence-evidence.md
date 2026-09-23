---
id: SEEN-021
title: "Persist findings with rule, confidence, evidence refs and deadline"
epic: E2
epic_name: "Reconciliation, findings and audit"
sprint: 1
sprint_dates: "12 - 23 Oct 2026"
gate: G1
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-019, SEEN-020]
status: todo
---
# SEEN-021: Persist findings with rule, confidence, evidence refs and deadline

| | |
|---|---|
| Epic | E2 Reconciliation, findings and audit |
| Sprint | 1 (12 - 23 Oct 2026), gate G1 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Wire the detectors into a reconcile worker in apps/worker that writes findings rows (type, rule, amount, confidence, evidence refs, deadline, status open, claimed, credited, refused or expired) with a deterministic finding key so re-runs update rather than duplicate, and expose GET /tenants/:id/findings in apps/api with filters by marketplace, rule and status. Status transitions are the only writes the claims rail is allowed to make later.

## Acceptance criteria

- [ ] Re-running reconciliation on unchanged data produces zero new findings rows
- [ ] GET /tenants/:id/findings returns amount, rule, confidence, evidence refs, deadline and status under RLS
- [ ] A finding whose deadline passes without a claim moves to expired by a daily job
- [ ] Sum of open findings per marketplace comes from one SQL view that the audit PDF also uses

## Depends on

- [SEEN-019](SEEN-019-implement-fee-detectors-as-pure-tested-functions.md): Implement fee detectors as pure tested functions
- [SEEN-020](SEEN-020-implement-shipment-return-and-inventory.md): Implement shipment, return and inventory detectors

## Blocks

- [SEEN-022](SEEN-022-generate-the-audit-pdf-with-scorecard-and-line.md): Generate the audit PDF with scorecard and line annex
- [SEEN-023](SEEN-023-measure-the-recoverable-pool-per-marketplace.md): Measure the recoverable pool per marketplace
- [SEEN-024](SEEN-024-ship-ops-console-v1-for-tenants-connections-and.md): Ship ops console v1 for tenants, connections and sync status
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-042](SEEN-042-ship-the-reconcile-module-with-margin-and-fee.md): Ship the Reconcile module with margin and fee-change alerts
- [SEEN-066](SEEN-066-track-claim-and-dispute-deadlines-with-alerts.md): Track claim and dispute deadlines with alerts

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Match every settlement line to an order line, detect fee errors, lost shipments and return shortfalls with tested code, and deliver the audit PDF with a measured recoverable pool.
