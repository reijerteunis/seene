# Seen

Seen runs a brand's trading relationship with online marketplaces through official APIs, and is itself built through a fixed development procedure called the harness. Both use the word "gate", so this glossary exists first to keep them apart. Product terms are defined in the PRD glossary (`docs/prd/prd.md`, section 17); this file records the terms whose meaning was settled in conversation and the ones that were ambiguous.

## Language

### Development harness

**Harness**:
The fixed procedure every ticket goes through, run by one command per stage inside the assistant session that is doing the work.
_Avoid_: pipeline, orchestrator, workflow engine

**Stage**:
One named step of the harness that a ticket occupies at a point in time. A ticket is always in exactly one stage.
_Avoid_: phase (reserved for the red, green, regression and qa phases of a recorded check)

**Stage gate**:
The condition a ticket must satisfy to leave the stage it is in. Made of three layers: the stage template declares which fields must be present, harness code declares the relations between records, and `harness/thresholds.toml` declares the numbers and checklists.
_Avoid_: gate (bare), quality gate

**Journal**:
The append-only, hash-chained record of everything that happened to one ticket, held as numbered JSON files under `docs/harness/history/<ticket>/`. The source of truth for resuming work, so a session started in one assistant continues in another.
_Avoid_: history, log, audit trail (reserved for the product's `audit_events`)

**Record**:
One entry in a journal. Never edited and never deleted; a superseded decision is followed by another record, not replaced.
_Avoid_: entry, event (reserved for the product's audit events)

**Template**:
The JSON file per stage in `harness/templates/` that a session copies, fills in and submits to `advance`. Every key it carries is required; a key whose template value is an empty list may stay empty.
_Avoid_: schema, form

**Draft**:
A working copy of a template under `.harness-drafts/`, never committed. Evidence only counts once it is in the journal.

**Receipt**:
The record that closes a ticket, appended by `verify-delivery`. It attests the code commit CI went green on and the reviewed-tree fingerprint, and its own sha256 is what the pull request body carries.
_Avoid_: sign-off, proof

**Reviewed-tree fingerprint**:
The hash of the working tree as it stood when review passed, computed over everything except the journal and the drafts directory, so that recording evidence about a tree cannot change that tree.

**Chain**:
The link from each record to the sha256 of the previous record file, verified by `doctor` together with git history. It makes an accidental rewrite detectable and a deliberate one expensive and visible; it does not make one impossible.
_Avoid_: blockchain, ledger

**Actor**:
The self-reported tool and role that wrote a record, for example `claude:implementer`. Self-reported means unverifiable: the harness records the claim, it does not authenticate it.

**Non-code mode**:
The declaration at the TDD stage that a ticket has no executable behaviour to prove, with a change type of documentation, research, verification or policy and a recorded reason. It keeps registration and verification tickets inside the harness rather than outside it.

**Source**:
For a verification ticket, where a claim came from: a URL, a saved response file in the ticket's journal directory, or a named person and date. A fact without a source is not a verified fact.

**Attachment**:
A file saved beside a journal, under `attachments/`, that a record cites by path and sha256. The evidence a verification ticket rests on, such as a saved API response, rather than a claim about it.

**Thresholds**:
The numbers and checklists the stage gates apply, held in `harness/thresholds.toml` so that changing one is a visible decision rather than an edit to a prompt.
_Avoid_: policy, config

### Product

**Policy gate**:
The product component that decides autonomous, approval or refuse for every proposed agent action. Nothing to do with the harness.
_Avoid_: gate (bare), action gate

**Sprint gate**:
One of the checkpoints G0 to G7 that must be proven before the next sprint starts. Written `gate: G0` in ticket frontmatter for historical reasons, said as "sprint gate G0".
_Avoid_: milestone, gate (bare)

**Policy-gate action ticket**:
A ticket that changes an action subject to the policy gate, flagged `changes_agent_action: true` in its frontmatter. It carries extra obligations: declared reversibility, action type, a euro impact estimator, and a second reviewer.
_Avoid_: gate-action ticket

## Flagged ambiguities

**"Gate", resolved 23 September 2026.** The word had three meanings across the docs (the product's policy gate, the sprint gates G0 to G7, and the harness's stage gates) plus a fourth in "gate-action ticket". Resolution: each meaning always carries its qualifier, and bare "gate" is retired from harness code, harness prose and error messages. `harness/policy.toml` was renamed `harness/thresholds.toml` in the same pass so that "policy" belongs to the product alone.

## Example dialogue

**Dev**: SEEN-033 is a policy-gate action ticket, so when it reaches the harness's review stage the stage gate wants a second reviewer.

**Jev**: Where does "wants a second reviewer" come from, the template or the code?

**Dev**: The threshold file says a policy-gate action ticket needs two reviewers. The review template has a field for each reviewer, so the stage gate refuses the advance when the second one is missing, and names the field.

**Jev**: And if I change the threshold to one reviewer to get the ticket out of the door?

**Dev**: That is an edit to `harness/thresholds.toml`, which is a commit anyone can see, and the journal keeps the record of the advance that happened under the old number. The harness cannot stop you, it can only make it visible.
