"""Stage names, project-relative locations and the shapes files must have.

Everything here is structure rather than judgement, which is why it lives in
code: changing it changes what the harness is, not how strict it is. Numbers and
vocabularies that a person may legitimately tune live in thresholds.toml.
"""

from pathlib import Path
import re

# The five working stages and the terminal one. Order defines advance and return.
# `deliver` has no advance out of it: verify-delivery is its stage gate.
STAGES = ('clarify', 'solution', 'tdd', 'review', 'deliver', 'delivered')
WORKING_STAGES = STAGES[:-1]
FINAL_WORKING_STAGE = 'deliver'

# Bumped when record semantics change. Held at 1 until the harness was complete
# at SEEN-092, so the first six journals were not stamped six ways; 2 from
# SEEN-104, where the envelope gained the session that wrote the record. A
# version that stands still while the envelope changes tells a reader nothing,
# which is the one thing it exists to do.
HARNESS_VERSION = '2'

# handoff is its own kind rather than a note, because the KPI and status must
# find a slice boundary without parsing prose. It is not in journal.TRANSITIONS:
# writing a pack says where the work stands and never moves it.
# triage is its own kind for the reason handoff is: the review gate has to find
# the focus set and the KPI the excluded share, and a reader that parses prose is
# a reader that will one day read it wrong. Like handoff it is not in
# journal.TRANSITIONS: a triage says what the reviewer must read and never moves
# the ticket. The envelope is unchanged, so HARNESS_VERSION stays at 2.
# route is its own kind for the reason handoff and triage are, and for one more:
# the journal is append-only, so the route a slice runs under cannot be written
# into the solution record that planned it. The record names that record instead.
# Like both of them it is not in journal.TRANSITIONS: a route says what a slice
# should run on and never moves the ticket. The envelope is unchanged, so
# HARNESS_VERSION stays at 2.
KINDS = ('start', 'note', 'check', 'advance', 'return', 'receipt', 'reopen', 'decision',
         'handoff', 'triage', 'route')

# Committed run history: docs/harness/history/<TICKET>/0001.json and onwards.
HISTORY = Path('docs/harness/history')
# Where a ticket lives. Its filename carries its title and so changes when the
# title does; the id at the front is what a journal can rely on.
TICKETS = Path('docs/tickets')
# Stage evidence templates a session copies, fills in and passes to advance.
TEMPLATES = Path('harness/templates')
# Thresholds and vocabularies. Fatal when missing: never silently defaulted.
THRESHOLDS = Path('harness/thresholds.toml')
# The lifecycle hooks: the one source, and the file each assistant reads them
# from. Both copies hold entries the harness did not write, which is why
# harness/hooks.py replaces the entries it owns rather than the file.
HOOK_SOURCE = Path('harness/hooks.json')
CLAUDE_SETTINGS = Path('.claude/settings.json')
CODEX_HOOKS = Path('.codex/hooks.json')
# Where the last delivered coverage figure is kept, so a delta has something to
# compare against. Written by delivery, so it sits outside the fingerprint for
# the same reason the journal does.
COVERAGE_BASELINE = Path('docs/harness/coverage.json')

# Reports, written by a command anyone can run, and the per-ticket KPI cache
# delivery writes. Both sit outside the fingerprint for the same reason the
# journal does: writing a record about a tree must not change that tree.
REPORTS = Path('docs/harness/reports')
KPI_FILE = 'kpi.json'

# The committed knowledge graph: context before a session reads any file.
GRAPH_DIRECTORY = Path('graphify-out')
# codegraph's symbol index. Local to each machine and ignored by a .gitignore
# the tool ships inside it, so this repository's own .gitignore says nothing.
CODEGRAPH_DIRECTORY = Path('.codegraph')
# repowise's index and structural wiki. Gitignored for the same reason: derived
# from the tree, rebuilt by repowise update, and not evidence about the work.
REPOWISE_DIRECTORY = Path('.repowise')
GRAPH_FILE = GRAPH_DIRECTORY / 'graph.json'

# Working copies of templates. Gitignored; only the journal is evidence.
DRAFTS = Path('.harness-drafts')
# The handoff pack, beside the drafts, for the same reason: it is written about
# the tree and must not change it. The journal holds its hash, which is what
# makes the file replaceable.
HANDOFF_PACK = '{ticket}-handoff.md'
# Advisory lock so two sessions never interleave writes to one journal.
LOCK = Path('.harness.lock')

# A journal directory holds records and nothing else, bar this allowlist. A
# damaged journal shows up in practice as 0007.json.bak or 0008 (copy).json
# from a bad merge, so anything unrecognised is refused rather than ignored.
RECORD_NAME = re.compile(r'^\d{4}\.json$')
ALLOWED_BESIDE_RECORDS = ('kpi.json', 'attachments')

# Paths whose contents must not affect the reviewed-tree fingerprint: the
# journal grows while a ticket proceeds, drafts are scratch space, and the
# graph is derived from the tree rather than evidence about it. graphify's
# post-commit hook rewrites the graph in the background after every commit,
# so counting it would make delivery refuse a ticket for a change no person
# made. See docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md.
FINGERPRINT_EXCLUDED = (str(HISTORY) + '/', str(DRAFTS) + '/', str(GRAPH_DIRECTORY) + '/',
                        str(COVERAGE_BASELINE), str(REPORTS) + '/', str(LOCK))

TEMPLATE_FOR_STAGE = {
    'clarify': 'clarify.json',
    'solution': 'solution.json',
    'tdd': 'tdd.json',
    'review': 'review.json',
    'deliver': 'deliver.json',
}
NON_CODE_TEMPLATE = 'tdd-non-code.json'

# Template values that are legitimate answers rather than example prose, so
# submitting them unchanged is not evidence of an unedited template.
ENUMERATED_KEYS = frozenset({'mode', 'change_type', 'verdict', 'independence', 'severity',
                             'status', 'id', 'phase', 'remote', 'reviewer'})


def normalise(path):
    """One spelling of a repository-relative path, or nothing for one that is not.

    Both sides of every comparison come through here, because a finding, a
    triage's `would_exclude` and a slice's file list are written by different
    hands. The `./` prefix is removed as a prefix and not as a set of characters:
    `str.lstrip('./')` strips every leading `.` and `/`, which turned
    `.claude/agents/x.md` into `claude/agents/x.md` and made a finding in any dot
    directory match nothing while looking like a path that had been read. F1 of
    SEEN-109's first review, on a list where four of the thirteen excluded files
    were dot directories.

    An absolute path returns nothing. It cannot be compared with anything a
    triage records, so it is placed nowhere rather than silently placed outside.
    """
    if not path:
        return None
    path = str(path).strip()
    while path.startswith('./'):
        path = path[2:]
    if not path or path.startswith('/'):
        return None
    return path.rstrip('/') or None


def covers(path, files):
    """Whether a plan's named files contain this path, directories included.

    The one reader of that question, and the reason it lives here: three places
    asked it and two disagreed with the third. The route verdict read a directory
    entry, so a slice naming `packages` was charged with a finding in
    `packages/core/db/tables.ts`; the edit guard and the triage's `slice_files`
    each compared exactly, so the same plan covered nothing inside it. SEEN-114
    met all three in one ticket: refused the right to write files its plan named,
    then returned three times over about forty files reported as belonging to no
    slice. SEEN-140 brought the two exact comparisons up to this answer and moved
    nothing down to theirs.

    Through `normalise`, like every other path comparison. The first version
    repeated the `lstrip('./')` that module's docstring was written to explain,
    one function below it and on the other side of the same comparison, where it
    decides the route verdict rather than the triage one: a finding in a dot
    directory was charged to no slice, so a downgraded slice that produced it
    read as having produced nothing, and findings are the only per-slice measure
    the route rule has. F1 of SEEN-109's second review, on a repository where
    SEEN-104 and SEEN-105 planned slices over `.claude/`, `.codex/` and
    `.agents/`.

    Whether a plan should be allowed to name a directory at all is a separate
    question, open since SEEN-140 raised it and the founder's to settle.
    """
    if path is None:
        return False
    for named in files:
        named = normalise(named)
        if named is not None and (path == named or path.startswith(named + '/')):
            return True
    return False
