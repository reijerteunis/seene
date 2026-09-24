"""Asking the knowledge graphs a question and keeping the answer in the journal.

Two tools, because they know different things. codegraph indexes symbols, so it
answers what calls this and what breaks if I change it. graphify knows files,
commits and pull requests, so it answers how these two ends connect and what the
open pull requests touch.

The harness does not traverse either. It runs one verb, records the command, the
exit code and the answer, and stamps which index produced it, so a note can be
read later against the graph it came from rather than against whatever the graph
has become.

codegraph has no standing daemon: its watcher lives in the MCP server an
assistant starts, so a shell command finds whatever the index was when one last
had it open. Every codegraph query therefore syncs first, which took 55
milliseconds on this repository, and records that it did. Observed on
24 September 2026 and written up in SEEN-096's journal at record 13.
"""

import hashlib
import re
import subprocess
import time

from .errors import require
from .paths import CODEGRAPH_DIRECTORY, GRAPH_FILE

# The four questions a ticket asks, the tool that answers each, and its verb.
MODES = {
    'impact': ('codegraph', 'impact'),
    'explain': ('codegraph', 'explore'),
    'path': ('graphify', 'path'),
    'prs': ('graphify', 'prs'),
}
NEEDS_SUBJECT = ('impact', 'explain')
NEEDS_ENDS = ('path',)
OUTPUT_LIMIT = 65536
COUNT = re.compile(r'^\s*(Nodes|Edges):\s*([\d,]+)', re.MULTILINE)


def tool_for(mode):
    require(mode in MODES,
            f'Unknown graph mode: {mode!r}; the harness asks for {", ".join(sorted(MODES))}')
    return MODES[mode][0]


def build_command(mode, about, source, target):
    tool_for(mode)
    tool, verb = MODES[mode]
    if mode in NEEDS_SUBJECT:
        require(about, f'A {mode} query needs --about "<node or question>"')
        return [tool, verb, about]
    if mode in NEEDS_ENDS:
        require(source and target, 'A path query needs --from and --to')
        return [tool, verb, source, target]
    return [tool, verb]


def _run(command, root, timeout):
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True,
                                   text=True, timeout=timeout)
        return completed.returncode, completed.stdout + completed.stderr
    except FileNotFoundError:
        tool = command[0]
        hint = ('npm i -g @colbymchenry/codegraph, then codegraph init'
                if tool == 'codegraph' else 'uv tool install graphifyy')
        require(False, f'{tool} is not on PATH; install it with {hint}')
    except subprocess.TimeoutExpired:
        return 124, f'The harness stopped {command[0]} after {timeout}s.\n'


def _index_counts(root, timeout):
    """Nodes and edges, as codegraph status reports them.

    Weaker than a hash: two different indexes can share their counts. It is
    enough to tell a stale answer from a fresh one, which is what a fingerprint
    on a note is for, and the database itself is megabytes that change on every
    sync.
    """
    _, output = _run(['codegraph', 'status'], root, timeout)
    found = {name.lower(): int(value.replace(',', '')) for name, value in COUNT.findall(output)}
    return dict(nodes=found.get('nodes'), edges=found.get('edges'))


def ask(repository, mode, about=None, source=None, target=None, timeout=300):
    """Run one verb in the project root and return what to record."""
    tool = tool_for(mode)
    command = build_command(mode, about, source, target)
    root = repository.root
    record = dict(source=tool, mode=mode, command=command)
    if tool == 'codegraph':
        require((root / CODEGRAPH_DIRECTORY).is_dir(),
                f'No codegraph index at {CODEGRAPH_DIRECTORY}; run codegraph init in this '
                'repository before asking it questions')
        sync_code, _ = _run(['codegraph', 'sync'], root, timeout)
        record['synced'] = sync_code == 0
    else:
        graph = root / GRAPH_FILE
        require(graph.is_file(),
                f'No graph at {GRAPH_FILE}; run graphify on this repository before asking it '
                'questions')
        record['graph_sha256'] = hashlib.sha256(graph.read_bytes()).hexdigest()
    started = time.monotonic()
    exit_code, answer = _run(command, root, timeout)
    if tool == 'codegraph':
        record['index'] = _index_counts(root, timeout)
    return dict(record,
                exit_code=exit_code,
                duration_ms=int((time.monotonic() - started) * 1000),
                answer=answer[:OUTPUT_LIMIT],
                answer_truncated=len(answer) > OUTPUT_LIMIT)
