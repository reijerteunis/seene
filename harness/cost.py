"""Tokens spent on a ticket, read from the session logs.

Only four numbers are read. A session log holds prompts and file contents, none
of which belongs in a journal, and the tokens are the only part that answers the
question the KPI asks.
"""

import json
from pathlib import Path

LOGS = Path.home() / '.claude' / 'projects'
FIELDS = ('input_tokens', 'output_tokens', 'cache_read_input_tokens',
          'cache_creation_input_tokens')


def log_directory(root):
    """Where Claude Code keeps this project's session logs, by its own naming."""
    return LOGS / str(root.resolve()).replace('/', '-')


def tokens_between(root, opened, closed):
    """Token counts from entries falling inside a ticket's window.

    Null rather than zero when there are no logs: zero is a claim that nothing
    was spent, and the honest answer on a machine without logs is that nobody
    knows.
    """
    directory = log_directory(root)
    if not directory.is_dir():
        return None
    totals = dict.fromkeys(FIELDS, 0)
    seen = False
    for path in sorted(directory.glob('*.jsonl')):
        for line in path.read_text(errors='replace').splitlines():
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            stamp = entry.get('timestamp')
            usage = (entry.get('message') or {}).get('usage')
            if not stamp or not usage:
                continue
            stamp = stamp.replace('Z', '+00:00')
            if opened <= stamp <= closed:
                seen = True
                for field in FIELDS:
                    totals[field] += usage.get(field, 0) or 0
    return totals if seen else None
