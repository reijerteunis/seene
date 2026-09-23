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

# Bumped when record semantics change, and held at 1 until the harness is
# complete at SEEN-092, so the first six journals are not stamped six ways.
HARNESS_VERSION = '1'

KINDS = ('start', 'note', 'check', 'advance', 'return', 'receipt', 'reopen', 'decision')

# Committed run history: docs/harness/history/<TICKET>/0001.json and onwards.
HISTORY = Path('docs/harness/history')
# Stage evidence templates a session copies, fills in and passes to advance.
TEMPLATES = Path('harness/templates')
# Thresholds and vocabularies. Fatal when missing: never silently defaulted.
THRESHOLDS = Path('harness/thresholds.toml')
# Where the last delivered coverage figure is kept, so a delta has something to
# compare against. Written by delivery, so it sits outside the fingerprint for
# the same reason the journal does.
COVERAGE_BASELINE = Path('docs/harness/coverage.json')

# The committed knowledge graph: context before a session reads any file.
GRAPH_DIRECTORY = Path('graphify-out')
GRAPH_FILE = GRAPH_DIRECTORY / 'graph.json'

# Working copies of templates. Gitignored; only the journal is evidence.
DRAFTS = Path('.harness-drafts')
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
                        str(COVERAGE_BASELINE), str(LOCK))

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
