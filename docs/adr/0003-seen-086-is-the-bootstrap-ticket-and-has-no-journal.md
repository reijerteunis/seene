# SEEN-086 is the bootstrap ticket and has no journal

The harness does not exist while it is being built, so the only ways to give SEEN-086 a journal are to hand-write records with correct hashes or to backdate them once the code runs. Both are falsifications, and the first journal in the repository is the one every later ticket imitates. So SEEN-086 has no journal at all: its evidence is its test suite, its pull request and an `## Outcome` section in the ticket file. Every ticket from SEEN-087 onwards has a journal written by the harness itself.

Rejected: a partial journal starting once `start` works, which produces a record `0001` that is an `advance` with no `start` before it and needs explaining to every future reader. A clean absence is easier to trust than a partial presence.

## Consequences

`doctor` treats a missing journal as normal, since most tickets have not started. The exemption is named in `CLAUDE.md` and in the ticket rather than taken silently, and the reference example of a complete journal is the dry run SEEN-092 commits.
