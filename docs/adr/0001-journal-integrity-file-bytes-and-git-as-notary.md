# Journal records are hashed as file bytes, and git is the notary

Every harness record links to the previous one by `prev_hash`, the sha256 of the previous record file exactly as it sits on disk. A record carries no hash of itself, so the chain is verifiable by anyone with `shasum -a 256` and no harness at all, and any reformat, re-indent or whitespace change is a tamper by definition. The obvious alternative, an in-file `hash` field computed over the record minus that field, was rejected because only the harness can then verify it, which makes the evidence depend on the tool it is evidence about.

The chain alone cannot stop tampering: whoever edits record 3 can recompute records 4 to N. So `doctor` also asks git, failing when any file under `docs/harness/history/` has ever been committed as a modification or a deletion rather than an addition. That is the half the chain cannot prove. Together they mean an accidental rewrite is caught immediately, and a deliberate one requires a large, obvious diff in a commit a human is about to review.

## Consequences

Record writes must be byte-deterministic (fixed indent, sorted keys, `ensure_ascii=False`, one trailing newline) and atomic (temporary file, fsync, `os.link` to the final name, unlink), because a truncated write breaks the chain permanently. A journal directory holds only `NNNN.json` records plus an allowlist of `kpi.json` and `attachments/`; a stray `0007.json.bak` from a bad merge is a `doctor` failure, since that is how a damaged journal actually appears in practice.
