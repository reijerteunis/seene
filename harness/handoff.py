"""The handoff pack: the only thing that crosses a slice boundary.

A session that starts by reading the PRD, the architecture and the workflow has
spent thirty thousand tokens before the first useful line, and a session that
works a whole ticket compacts its context at least once, which is where evidence
quietly becomes summary. So the pack is small and derived: everything in it comes
from the journal, which is committed, so a session in another checkout can be
handed the same pack without the drafts directory travelling with it.

It is built from bounded sections rather than trimmed after the fact. A command
that refused to write a handoff pack because the journal had grown would refuse
at exactly the moment a session needs to hand off.
"""

import hashlib

from . import gates

# Four characters to a token. The harness is standard library only and has no
# tokeniser; at a two thousand token limit the error in this estimate is smaller
# than the margin the section caps leave, and the estimate is recorded in the
# handoff record so a real count can be compared against it later.
CHARACTERS_PER_TOKEN = 4
ENTRY_CHARACTERS = 240
MAX_CRITERIA = 8
MAX_DECISIONS = 6
MAX_GRAPH = 6


def estimate_tokens(text):
    """Tokens, rounded up, by the only measure available here."""
    return -(-len(text) // CHARACTERS_PER_TOKEN)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _one_line(value, limit=ENTRY_CHARACTERS):
    text = ' '.join(str(value).split())
    return text if len(text) <= limit else text[:limit].rstrip() + ' [...]'


def _heading(records):
    """The ticket's title, from the snapshot taken when it started."""
    for line in records[0]['data'].get('ticket_snapshot', '').splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return records[0]['ticket']


def plan_of(records):
    """The slice plan the solution record carries, or nothing."""
    return (gates.latest_evidence(records, 'solution') or {}).get('slices') or []


def accepted_greens(records, attempt):
    return [record for record in records
            if record['kind'] == 'check' and record['stage'] == 'tdd'
            and record['attempt'] == attempt
            and record['data'].get('phase') == 'green'
            and record['data'].get('exit_code') == 0]


def current_slice(records, state, declared=None):
    """The slice a fresh session picks up, declared or counted from the greens.

    The plan is ordered and the tdd stage gate refuses slices out of order, so
    the number of accepted greens in this attempt is usually how many slices are
    behind us. Usually: a slice that records a second green, which is what a
    correction inside a slice looks like, counts twice and sends the next session
    past a slice nobody worked. It happened on SEEN-105's own slice 1.

    Only the session that worked the slice knows it finished it, so it may say so
    with --slice-done and the record keeps which of the two numbers this was. The
    inference stays the default, because a flag nobody passes must still leave a
    right answer most of the time.

    The pack never invents a slice that is not in the plan: before the solution
    record has advanced there is none, and it says so.
    """
    from .errors import require
    slices = plan_of(records)
    if not slices:
        return None
    if declared is None:
        done = min(len(accepted_greens(records, state['attempt'])), len(slices))
    else:
        require(0 <= declared <= len(slices),
                f'--slice-done {declared} is not a count this plan can carry: it has '
                f'{len(slices)} slices, so the number of slices done is between 0 and '
                f'{len(slices)}')
        done = declared
    entry = slices[done] if done < len(slices) else None
    return dict(position=done + 1 if entry else None,
                total=len(slices),
                done=done,
                declared=declared is not None,
                entry=entry)


def _graph_answers(records):
    """What has already been asked of the graphs, so it is not asked twice."""
    found = []
    for record in records:
        data = record['data']
        if record['kind'] != 'note' or 'source' not in data:
            continue
        command = data.get('command') or []
        subject = command[-1] if len(command) > 2 else ''
        found.append(f'{data["source"]} {data.get("mode", "")} {subject}'.strip()
                     + f' (record {record["sequence"]})')
    return found


def _decisions(records):
    """Decisions taken at clarify and solution, the later stage first."""
    taken = []
    for stage in ('solution', 'clarify'):
        evidence = gates.latest_evidence(records, stage) or {}
        taken += [entry for entry in evidence.get('decisions', []) if isinstance(entry, str)]
    return taken


def _section(lines, title, entries, maximum, remaining):
    """One optional section, as much of it as the character budget allows.

    A section that did not fit charges nothing. Charging for a block that was
    discarded drove the budget negative and dropped every later section, which
    is how the graph answers disappeared from a pack with room for them.
    """
    if not entries:
        return remaining
    block, spent, written = ['', f'## {title}', ''], 0, 0
    for entry in entries[:maximum]:
        line = f'- {_one_line(entry)}'
        if spent + len(line) + 1 > remaining:
            break
        block.append(line)
        spent += len(line) + 1
        written += 1
    if not written:
        return remaining
    left = len(entries) - written
    if left > 0:
        note = f'- and {left} more in the journal, which is where they are read in full'
        block.append(note)
        spent += len(note) + 1
    lines += block
    return remaining - spent


def pack(records, state, thresholds, branch=None, next_command='', slice_done=None):
    """The markdown a fresh session starts from, and what it cost to say it."""
    limit = thresholds['session']['handoff_token_limit']
    slice_now = current_slice(records, state, declared=slice_done)
    lines = [f'# {records[0]["ticket"]} handoff pack', '',
             '| | |', '|---|---|',
             f'| Ticket | {_one_line(_heading(records))} |',
             f'| Stage | {state["stage"]}, attempt {state["attempt"]} |',
             f'| Branch | {branch or "not on a branch"} |',
             f'| Records | {len(records)}, the last at {records[-1]["timestamp"]} |',
             f'| Ticket file | {records[0]["data"].get("ticket_file", "unknown")} |',
             '', '## The slice in front of you', '']
    if slice_now is None:
        lines.append('No plan yet: the solution record has not advanced, so no slice has been '
                     'accepted. The plan is written at the solution stage.')
    elif slice_now['entry'] is None:
        # What follows a complete plan depends on where it is read. The first
        # pack written at the review stage told its reader to go and run the
        # regression, which the journal three records above it already showed.
        finished = (f'The plan is complete: {slice_now["total"]} of {slice_now["total"]} slices '
                    'done, every slice has an accepted GREEN.')
        if state['stage'] == 'tdd':
            finished += (' What is left is the regression, the coverage measurement and the '
                         'advance to review.')
        lines.append(finished)
    else:
        entry = slice_now['entry']
        lines += [f'Slice {slice_now["position"]} of {slice_now["total"]}, '
                  f'{slice_now["done"]} of {slice_now["total"]} done, '
                  f'{entry.get("points")} point(s): {entry.get("name")}', '',
                  f'Its RED must demonstrate: {_one_line(entry.get("red"), 400)}', '',
                  'Files: ' + ', '.join(str(name) for name in entry.get('files') or [])]
    tail = ['', '## The next command', '', next_command or 'harness status <ticket>', '',
            'Everything above came from the journal. Read the ticket file and the records this '
            'pack names; nothing else is needed to work the slice.']
    spent = len('\n'.join(lines + tail)) + 2
    remaining = max(limit * CHARACTERS_PER_TOKEN - spent, 0)
    clarified = gates.latest_evidence(records, 'clarify') or {}
    remaining = _section(lines, 'The criteria, as checks', clarified.get('acceptance', []),
                         MAX_CRITERIA, remaining)
    remaining = _section(lines, 'Decisions already taken', _decisions(records),
                         MAX_DECISIONS, remaining)
    _section(lines, 'Graph answers already in the journal', _graph_answers(records),
             MAX_GRAPH, remaining)
    text = '\n'.join(lines + tail) + '\n'
    return dict(markdown=text,
                estimated_tokens=estimate_tokens(text),
                characters=len(text),
                token_limit=limit,
                slice=slice_now)
