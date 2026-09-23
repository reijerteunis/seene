"""Asking graphify a question and keeping the answer in the journal.

The harness does not traverse the graph. It runs one graphify verb, records the
command, the exit code and the answer, and stamps the hash of the graph that
produced it, so a note can be read later against the graph it came from rather
than against whatever the graph has become.
"""

import hashlib
import subprocess
import time

from .errors import require
from .paths import GRAPH_FILE

# The four questions a ticket asks, and the graphify verb that answers each.
MODES = {
    'impact': 'affected',
    'path': 'path',
    'explain': 'explain',
    'prs': 'prs',
}
NEEDS_SUBJECT = ('impact', 'explain')
NEEDS_ENDS = ('path',)
OUTPUT_LIMIT = 65536


def build_command(mode, about, source, target):
    require(mode in MODES,
            f'Unknown graph mode: {mode!r}; the harness asks for {", ".join(sorted(MODES))}')
    verb = MODES[mode]
    if mode in NEEDS_SUBJECT:
        require(about, f'A {mode} query needs --about "<node or question>"')
        return ['graphify', verb, about]
    if mode in NEEDS_ENDS:
        require(source and target, 'A path query needs --from and --to')
        return ['graphify', verb, source, target]
    return ['graphify', verb]


def ask(repository, mode, about=None, source=None, target=None, timeout=300):
    """Run one graphify verb in the project root and return what to record."""
    graph = repository.root / GRAPH_FILE
    require(graph.is_file(),
            f'No graph at {GRAPH_FILE}; run graphify on this repository before asking it questions')
    command = build_command(mode, about, source, target)
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=repository.root, capture_output=True,
                                   text=True, timeout=timeout)
        exit_code, answer = completed.returncode, completed.stdout + completed.stderr
    except FileNotFoundError:
        require(False, 'graphify is not on PATH; install it with uv tool install graphifyy')
    except subprocess.TimeoutExpired:
        exit_code, answer = 124, f'The harness stopped graphify after {timeout}s.\n'
    return dict(source='graphify',
                mode=mode,
                command=command,
                exit_code=exit_code,
                duration_ms=int((time.monotonic() - started) * 1000),
                answer=answer[:OUTPUT_LIMIT],
                answer_truncated=len(answer) > OUTPUT_LIMIT,
                graph_sha256=hashlib.sha256(graph.read_bytes()).hexdigest())
