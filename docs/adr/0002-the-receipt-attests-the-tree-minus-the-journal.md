# The delivery receipt attests the tree minus the journal

Delivery is circular: the receipt is a journal record, the journal is committed, so writing the receipt dirties the tree after the commit that CI verified, and no commit can contain a receipt for itself. We resolved it by scoping what the receipt attests. The reviewed-tree fingerprint is computed over everything except `docs/harness/history/` and `.harness-drafts/`, so the journal-only commit that carries the receipt cannot invalidate the receipt, and the receipt's own sha256 goes into the pull request body, which is edited through the API and costs no commit.

Rejected: keeping the receipt only in the pull request body (the journal stops being the source of truth for resume, and nothing survives in the tree after merge), and writing journals to `main` only at merge (a resumed session on the branch would not see its own history).

## Consequences

Every delivered ticket leaves one trailing commit whose only content is a journal record, 92 of them over the MVP. `verify-delivery` is the deliver stage's own stage gate rather than an `advance`: it appends the receipt and moves the ticket to `delivered`. Merge to `main` requires the receipt hash in the pull request body, checked at merge time rather than before the push.
