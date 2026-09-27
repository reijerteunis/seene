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

from . import gates, routing

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


def _is_an_accepted_green(record):
    """A green the journal kept: a tdd check of that phase that really passed."""
    return (record['kind'] == 'check' and record['stage'] == 'tdd'
            and record['data'].get('phase') == 'green'
            and record['data'].get('exit_code') == 0)


def _positions_the_journal_declares(records, after=0):
    """Which slice of the plan each cited green proved, where a tdd record says.

    The journal's own answer to a question counting cannot ask. A green is a
    check that passed; which slice it proved is a claim, and the tdd records are
    where that claim is made, one position per round beside the red and the green
    that proved it.
    """
    declared = {}
    for record in records:
        if (record['sequence'] <= after or record['kind'] != 'advance'
                or record['data'].get('from_stage') != 'tdd'):
            continue
        for entry in (record['data'].get('evidence') or {}).get('slices') or []:
            if not isinstance(entry, dict):
                continue
            position, green = entry.get('position'), entry.get('green')
            if (isinstance(position, int) and not isinstance(position, bool)
                    and isinstance(green, int) and not isinstance(green, bool)):
                declared[green] = max(declared.get(green, 0), position)
    return declared


def slices_proved(records, after=0, done=0):
    """How far into the plan the work has got, counting slices and not greens.

    A slice proved green does not become unproved because a review sent the
    ticket back: the code is in the branch either way, and the rework is work on
    top of it. That is H4 of SEEN-105's third review, and counting the greens
    since the plan was accepted was how it was answered. With the count starting
    at the first acceptance of a plan that still stands, counting greens became
    worse than what it replaced: one slice proved, a return to solution that
    re-accepted the same plan, the same slice reworked and proved again, and two
    greens read as two slices, so the pack handed over slice 3 with slice 2
    unworked and the guard refused slice 2's files. F3 of SEEN-113's second
    review.

    A green is not a slice. What a run at tdd reached is how far into the plan it
    got: a green nothing attributes is the next slice of that run, and a green a
    tdd record attributes is the slice that record names, which never carries the
    count past the position it names. A run begins where the plan was accepted
    again, because a plan somebody went back to is worked to fix something rather
    than to carry on, and a green recorded after it may be rework of a slice
    already counted. So each run starts its own reckoning from the count that
    stood, and the answer is the furthest any of them reached.

    Under-counting is the direction this errs in: a run that really did carry the
    plan on after a return, and whose tdd record has not been written yet,
    reaches a lower number than it earned, and the session that worked it says so
    with --slice-done. Over-counting is the harm, because it points the next
    session past a slice nobody worked.
    """
    declared = _positions_the_journal_declares(records, after)
    reached = furthest = done
    for record in records:
        if record['sequence'] <= after:
            continue
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'solution':
            reached = done
        elif _is_an_accepted_green(record):
            reached = (max(reached, declared[record['sequence']])
                       if record['sequence'] in declared else reached + 1)
            furthest = max(furthest, reached)
    return furthest


def _slice_key(entry):
    """What makes a slice the same slice across two acceptances of one plan."""
    return (entry.get('name'), entry.get('points'),
            tuple(entry.get('files') or []), entry.get('red'))


def _slices_accepted_by(record):
    return [_slice_key(entry)
            for entry in (record['data'].get('evidence') or {}).get('slices') or []]


def _is_the_same_plan(earlier, current):
    """Whether an earlier acceptance accepted the plan that stands now.

    The slices the two have in common, rather than the whole list, because a
    replan that appends a slice or drops the last one leaves the slices already
    proved exactly where they were. An acceptance that planned no slices at all
    can never be the start of this plan's count: there was no slice then for a
    green to have proved.
    """
    if not earlier:
        return False
    shared = min(len(earlier), len(current))
    return earlier[:shared] == current[:shared]


def plan_accepted_at(records):
    """Where the plan the pack counts against was first accepted.

    Slices belong to a plan, and a plan is set by the solution record. Counting
    from there rather than from the attempt is what H4 in SEEN-105's third review
    asked for: a return starts a new attempt without undoing a slice that shipped,
    and scoping the count to the attempt threw the declaration away and pointed the
    next session at work already delivered. A plan changed by a return to solution
    starts its own count, which is the one case an attempt boundary got right.

    SEEN-113: reading only the last acceptance made every replan a changed plan,
    so a return that re-accepted the same slices discarded the greens that proved
    them. The count starts at the earliest acceptance whose slices still agree
    with the current plan's on every slice the two have in common; the first one
    that disagrees is where the plan really changed, and the count starts after
    it. On SEEN-112 at its record 44 the pack read "slice 1 of 3, 0 of 3 done"
    with slices 1 and 2 green and committed, and handed a session slice 1's file
    list for work that belonged to slice 3.
    """
    acceptances = [record for record in records
                   if record['kind'] == 'advance'
                   and record['data'].get('from_stage') == 'solution']
    if not acceptances:
        return 0
    current = _slices_accepted_by(acceptances[-1])
    first = acceptances[-1]
    for record in reversed(acceptances[:-1]):
        if not _is_the_same_plan(_slices_accepted_by(record), current):
            break
        first = record
    return first['sequence']


def last_declaration(records, after=0):
    """The count the most recent handoff declared since the plan was accepted.

    F1 in SEEN-105's first review: --slice-done wrote the right number into the
    record and `status --brief` rebuilt the pack without it, so the session that
    resumed read the inference anyway and was sent past a slice nobody worked.
    """
    for record in reversed(records):
        if (record['sequence'] > after and record['kind'] == 'handoff'
                and (record['data'].get('slice') or {}).get('declared')):
            return record['data']['slice']['done'], record['sequence']
    return 0, after


def current_slice(records, state, declared=None):
    """The slice a fresh session picks up, declared or counted from the journal.

    The plan is ordered and the tdd stage gate refuses slices out of order, so
    how far a run at tdd reached is usually how many slices are behind us.
    Usually: a slice that records a second green inside one run, which is what a
    correction inside a slice looks like, counts twice and sends the next session
    past a slice nobody worked. It happened on SEEN-105's own slice 1, and
    `slices_proved` closes it only where the journal says which slice a green
    proved.

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
    # The last declaration stands, and greens recorded after it still count: a
    # session that declared at its boundary and then worked on is where both
    # numbers are needed.
    planned_at = plan_accepted_at(records)
    at_boundary, since = last_declaration(records, planned_at)
    inferred = min(slices_proved(records, since, at_boundary), len(slices))
    if declared is None:
        done = inferred
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
                # Recorded beside the declaration so a count the journal does not
                # support is visible later. It is not refused: only the session
                # that worked the slice knows, and a gate that guessed would be
                # the miscount this flag exists to answer.
                inferred=inferred,
                entry=entry)


def _route_line(records, position):
    """What this slice runs on, which the session is never to decide for itself.

    The pack is the only thing that crosses a slice boundary, so this is the one
    place the route reaches the session that works it.
    """
    entry = routing.for_slice(records, position)
    if entry is None:
        return ('No route for this slice yet: run harness route <ticket> before working it, so '
                'the model and the effort are decided from the plan rather than inside the '
                'session that benefits from the answer.')
    source = entry['source']
    how = (f'by rule ({entry["rule"]})' if source == 'rule'
           else f'by Jev at {entry["model_probability"]}' if source == 'jev'
           else 'by neither: routed to the strongest because nobody answered')
    return f'Runs on: {entry["model"]} at {entry["effort"]} effort, {how}.'


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


def hands_over_nothing(built):
    """Why an automatically written pack would hand nothing over, or nothing.

    One case, and it is an absence rather than a fault: before the solution
    record has advanced there is no accepted slice plan, so there is no slice for
    a pack to hand over. PreCompact reads this and writes neither the file nor a
    record, because a pack that says no plan exists is not context worth keeping
    across a compaction, and a ticket compacting at clarify is not a ticket
    anything went wrong in.
    """
    if built['slice'] is None:
        return ('No accepted slice plan yet, so there is no slice for a pack to hand over; the '
                'plan is written at the solution stage')
    return None


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
                  'Files: ' + ', '.join(str(name) for name in entry.get('files') or []), '',
                  _route_line(records, slice_now['position'])]
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
