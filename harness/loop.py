"""What the run does next, read from the journal, the ticket and the thresholds.

The opening of the Principles section of docs/harness/workflow.md says: "The
harness is a procedure, not an orchestrator: it runs inside the current assistant
session, launches no other model, bypasses no tool permission, and never claims
an independent review when the implementing session reviewed its own work." So
this module answers one question and starts nothing. Given a journal, a ticket
file and the thresholds: what is the next action, exactly. The assistant executes
it and asks again.

An action carries the stage it belongs to, its kind, the argv to run, the agent
to spawn and that agent's task text where there is one, why this action rather
than another, and the named stops that end a run. Nothing here composes a task
of its own: the implementer's is routing.implementer_task() and the reviewer's is
triage.reviewer_task(), both read from the record that decided them, so the model
a slice is spawned on and the model it was routed to are the same word.

The stops are the ticket's own five plus the ordinary end of a run, and they live
in `[run] stops` in thresholds.toml, so adding one is a diff a person reviews.
Each is decided by evidence in the journal and never by a counter this module
keeps, which is what lets a fresh session read the same run from the same
records.
"""

import json
import re

from . import gates, handoff, journal, routing
from .errors import HarnessError, require
from .paths import DRAFTS, STAGES

# The entry point every action's argv starts with, because a run is a sequence of
# commands a person can read and repeat by hand.
ENTRY = ('python3', 'harness/run.py')

# What an action can be. `command` is a harness command, `spawn` hands a slice or
# a review to an agent with a context of its own, `ask` puts every open question
# to a person in one batch, `stop` ends the run at a named halt and `merge` is
# the one action nobody takes without authorisation.
ACTIONS = ('command', 'spawn', 'ask', 'stop', 'merge')

IMPLEMENTER = 'seen-implementer'
REVIEWER = 'seen-reviewer'
# The tool half of an actor when nothing says otherwise. Every writing command
# takes --actor, so this is only the fallback for a direct call.
DEFAULT_TOOL = 'claude'

# The placeholder the spawn argv ends in, on the precedent of
# routing.implementer_task(), which already hands an agent this exact line: the
# harness knows the phase, the actor, the model and the agent, and the command
# that proves the slice is the agent's to write.
COMMAND = '<command>'
# The same, for the one thing only a person can fill in: who allowed the merge.
WHO = '<who>'

# The merge, which is the one action whose argv is not a harness command. Nothing
# in the harness merges a pull request and nothing ever will: the run says what to
# run and who authorised it, and the person who authorised it runs it. Squash,
# because that is how every ticket in this repository has landed.
MERGE = ('gh', 'pr', 'merge', '--squash')

# Phases whose non-zero exit is a failure rather than the point. A red that fails
# is the red doing its job, which is why the phase decides and not the exit code
# alone.
MUST_PASS = ('green', 'regression', 'qa', 'coverage')

# The two suites this repository has. A plan that touches only harness/ is proved
# by the Python one; anything else goes through turborepo, which runs both. A
# default command in code rather than in thresholds, on the precedent of
# coverage.DEFAULT_COMMAND: it is what the project runs, not a rule to tune.
PYTHON_SUITE = ('python3', '-m', 'pytest', 'harness/tests', '-q')
PNPM_SUITE = ('pnpm', 'test')

# What only a person at a keyboard can produce: a session somebody ran, a figure
# read off a live account, a key somebody obtained. Observations rather than
# nouns, which is why 'printed verbatim' is here and 'prints' is not: one is a
# person reporting what they saw and the other is a program's own output.
INTERACTIVE = ('session', 'verbatim', 'verification', 'register', 'obtain', 'observe',
               'by hand', 'live account', 'signed off', 'sign off')

# A criterion and its box. triage.CRITERION is the same line without the box,
# which is what every other reader wants; the summary is the one place the box is
# the answer, so it is matched here and the texts still come from that reader.
CHECKBOX = re.compile(r'^\s*-\s*\[(?P<box>[ xX])\]\s*(?P<text>.+?)\s*$')

# Why each named stop ends a run. The vocabulary is thresholds' and the wording
# is here: a reason added to `[run] stops` without a line here still builds a
# stop, because the list is what the ticket names and this is only how it reads.
WHY = {
    'gate_refused': 'The stage gate refused the evidence it was given, and its message says '
                    'what it refused. A run that advanced again with the same record would be '
                    'retrying a decision, so this stop is where the run ends.',
    'question_open': 'The record carries a question only a person can settle. A run that '
                     'answered it itself would be inventing the answer and writing a journal '
                     'that reads as though the work were done.',
    'check_failed': 'A check that had to pass did not. What to fix is the code, not the record '
                    'of it, and the run does not re-run a check over an unchanged tree.',
    'ci_red': 'CI is red on the commit the receipt would attest, and a receipt over a red tree '
              'says nothing about what was delivered.',
    'second_return': 'This plan has been returned twice. A second return is thrashing rather '
                     'than a correction, and what to do with it is a person\'s call.',
    'awaiting_authorisation': 'The run has done everything short of the merge. The merge is '
                              'outward-facing and irreversible in the way nothing else in the '
                              'procedure is, so it waits on a person.',
}
GENERIC_WHY = ('A named stop from [run] stops in harness/thresholds.toml. It ends the run and is '
               'not retried.')


def stops(rules):
    """The named stops, in the order thresholds.toml lists them."""
    return tuple(rules['run']['stops'])


def _argv(*rest):
    return [*ENTRY, *rest]


def _role(actor, role):
    """The same tool in another role: a Codex run spawns Codex, not Claude."""
    tool, _, _ = str(actor or '').partition(':')
    return f'{tool or DEFAULT_TOOL}:{role}'


def draft_of(ticket, stage):
    """Where the stage evidence is drafted, which is what an advance reads."""
    return f'{DRAFTS}/{ticket}-{stage}.json'


def open_questions(repository, ticket, stage='clarify'):
    """What the stage draft says is still open, read from the draft itself.

    The clarify record is the only one with a question of its own to carry, which
    is why the stage has a default and not a branch: `open_questions` is a field of
    that template, and the gate that reads it refuses a record still carrying one.
    A draft that is not yet readable JSON has no questions here: the advance is the
    action that follows, and what is wrong with the file is the gate's to say.
    """
    path = repository.root / draft_of(ticket, stage)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    return [str(question) for question in (data.get('open_questions') or [])]


def question_stops(records):
    """Every stop that asked a batch, in order. What a second batch is counted from."""
    return [record for record in records
            if record['kind'] == 'stop' and record['data'].get('reason') == 'question_open']


def asked_already(records):
    """Every question a batch of this run has already carried."""
    return [question for record in question_stops(records)
            for question in record['data'].get('questions') or []]


def unanswered(records, questions):
    """The batch still to ask: every open question, minus the ones already asked.

    What makes the run continue is the answer being on record, not the loop liking
    it: a note after the stop that asked is the answer, and whether it is a
    sufficient one is the clarify gate's `clarified` and not a second definition
    here. So a question is asked once. One that no batch carried is a second batch,
    which is what the summary names as a defect of the run: a first batch that was
    incomplete cost a person two interruptions where one would have done.
    """
    if not questions:
        return []
    asked = question_stops(records)
    if not asked:
        return list(questions)
    answered = any(record['kind'] == 'note' and record['sequence'] > asked[-1]['sequence']
                   for record in records)
    if not answered:
        # The same batch, still open. Reported again and never a second stop,
        # because the stop is idempotent on the record it points at.
        return list(questions)
    carried = asked_already(records)
    return [question for question in questions if question not in carried]


def _action(stage, kind, argv, why, rules, **extra):
    """One answer, with every key present whether or not it is filled in.

    A shape that changes per kind is a shape every reader has to branch on, and
    the two that arrive with the second slice would change it again.
    """
    answer = dict(stage=stage, kind=kind, argv=list(argv), agent=None, task=None,
                  why=why, stops=list(stops(rules)))
    answer.update(extra)
    return answer


def ticket_path(repository, ticket, records):
    """The ticket file as it stands, by the rule every other reader uses."""
    from .cli import ticket_file
    first = records[0]['data'] if records else {}
    relative, _ = ticket_file(first, ticket, repository.root)
    return repository.root / relative if relative else None


def criteria(text):
    """Every acceptance criterion with its box, in the order the ticket lists them.

    The texts are triage.ticket_criteria's, which is the reader the triage and the
    review gate already use, so a criterion listed here is the one they answered;
    the box is read beside it, because that reader drops it deliberately and the
    summary is the one place it is the answer.
    """
    from . import triage
    boxes = [(match.group('box').lower() == 'x', match.group('text'))
             for match in (CHECKBOX.match(line) for line in text.splitlines()) if match]
    found = []
    for criterion in triage.ticket_criteria(text):
        entry = next((box for box in boxes if box[1] == criterion), None)
        if entry is not None:
            boxes.remove(entry)
        found.append((entry[0] if entry is not None else False, criterion))
    return found


def waiting_criteria(text):
    """The criteria that wait on an observation nobody can make from a file."""
    from . import triage
    return [criterion for criterion in triage.ticket_criteria(text)
            if any(word in criterion.lower() for word in INTERACTIVE)]


def refuse_human_executor(path):
    """Refuse a ticket whose executor is a person, before any record exists.

    SEEN-110 is the worked example the ticket names: three of its five criteria
    wait on an observation in an interactive Codex session, and a run that
    started it would arrive at a verification whose only way forward is to invent
    the fact the criterion exists to establish. The refusal names those criteria
    and not all five, because what a run must never do is settle an observation
    nobody made; the rest of such a ticket is ordinary work.

    The executor decides and the wording never does. A code ticket whose criteria
    mention a person is worked, or this would be a keyword search standing in for
    a decision.
    """
    from . import report as reporting
    if path is None or not path.is_file():
        return None
    text = path.read_text()
    header = reporting.frontmatter(path)
    executor = reporting._field(header, 'executor') or ''
    if 'human' not in re.split(r'[,\s]+', executor.strip().lower()):
        return None
    ticket = reporting._field(header, 'id') or path.stem
    criteria = waiting_criteria(text)
    if not criteria:
        from . import triage
        criteria = triage.ticket_criteria(text)
    require(False,
            f'{ticket} has executor: human, so the run refuses it rather than starting it. '
            f'{len(criteria)} of its criteria wait on an observation only a person can make:\n  - '
            + '\n  - '.join(criteria)
            + '\nWork them with Ruud and record the outcome under ## Outcome in the ticket file. '
              'A run that started here would reach a verification whose only way forward is to '
              'invent the fact the criterion exists to establish.')


def points_at(records):
    """The record a stop points at: the last one that is not a stop itself.

    A stop pointing at the latest record would point at itself the moment it was
    written, and the idempotence rule reads (reason, record): a run asked twice
    would then write two stops about one halt.
    """
    for record in reversed(records):
        if record['kind'] != 'stop':
            return record['sequence']
    return len(records)


def _failed_check(records, current):
    """The latest check of this attempt, when it is one that had to pass.

    Only the latest, so a failure a later run of the same phase fixed is not a
    stop that still stands.
    """
    latest = None
    for record in records:
        if record['kind'] == 'check' and record['attempt'] == current['attempt']:
            latest = record
    if latest is None:
        return None
    code = latest['data'].get('exit_code')
    if latest['data'].get('phase') in MUST_PASS and isinstance(code, int) and code != 0:
        return latest['sequence']
    return None


def _second_return(records):
    """The second return since the plan in hand was accepted, or nothing.

    Counted from the solution advance rather than from the attempt, for the
    reason handoff.plan_accepted_at gives: returns are what a plan collects, and
    a replan that passes the solution gate again starts its own count. Two of
    them under one plan is where a correction has become thrashing.
    """
    returns = [record for record in records
               if record['kind'] == 'return'
               and record['sequence'] > handoff.plan_accepted_at(records)]
    return returns[1]['sequence'] if len(returns) > 1 else None


def _evident_stop(records, current):
    """A stop the journal itself shows, as its reason and the record it points at.

    A second return first: a failing check inside a plan that has already been
    returned twice is the smaller of the two things a person has to decide.
    """
    thrashing = _second_return(records)
    if thrashing is not None:
        return 'second_return', thrashing
    failed = _failed_check(records, current)
    if failed is not None:
        return 'check_failed', failed
    return None


def resume(reason, ticket, stage, actor):
    """The one command a person runs to take the run forward from a stop.

    One command, because a stop that offered three is a stop that has not said
    what it is waiting for. Where the fix is outside the harness, in the code or
    in CI, the command is the run itself: it reads the journal again and says
    what is next from there.
    """
    if reason == 'gate_refused':
        return _argv('advance', ticket, '--file', draft_of(ticket, stage), '--actor', actor)
    if reason == 'question_open':
        return _argv('note', ticket, '--file', f'{DRAFTS}/{ticket}-answers.md', '--actor', actor)
    if reason == 'ci_red':
        return _argv('verify-delivery', ticket, '--file', draft_of(ticket, 'deliver'),
                     '--actor', actor)
    if reason == 'second_return':
        return _argv('draft', ticket, '--stage', 'solution')
    if reason == 'awaiting_authorisation':
        return _argv('authorise', ticket, '--merge', '--by', WHO, '--actor', actor)
    return _argv('run', ticket, '--actor', actor)


def stop(reason, stage, record, resume_argv, why=None, questions=()):
    """One named stop: where it stopped, what it points at, how to resume.

    This is what the `stop` record carries. The action a caller gets back is the
    same thing in the shape every other action has, which _stop_action builds.
    `questions` is what the batch carried and is empty for every other reason,
    present rather than omitted for the reason _action gives: what a second batch
    is is read from these lists, so they are part of every stop's shape.
    """
    return dict(kind='stop', stage=stage, reason=reason, record=record,
                resume=list(resume_argv), why=why or WHY.get(reason, GENERIC_WHY),
                questions=list(questions))


def _stop_action(reason, stage, record, ticket, actor, rules, questions=()):
    """A stop as an action: its argv is the one command that resumes the run."""
    built = stop(reason, stage, record, resume(reason, ticket, stage, actor),
                 questions=questions)
    return _action(stage, 'stop', built['resume'], built['why'], rules,
                   reason=reason, record=record, resume=built['resume'],
                   questions=built['questions'])


def standing(records, reason, record):
    """The stop record for this reason and this record, when one already stands."""
    for entry in records:
        if (entry['kind'] == 'stop' and entry['data']['reason'] == reason
                and entry['data']['record'] == record):
            return entry
    return None


def halt(repository, folder, records, ticket, actor, reason, rules):
    """Record a stop, once. Asked again while it stands, it reports the same one.

    At most one stop record per reason and record number, which is what "none is
    retried" means in an append-only journal: a run asked ten times about one
    refused gate leaves one record saying so, and a reader can see that nobody
    tried the gate ten times.
    """
    require(reason in stops(rules),
            f'{reason!r} is not one of the named stops: {", ".join(stops(rules))}. A run ends at '
            'one of those or it does not end; add a reason to [run] stops in '
            'harness/thresholds.toml if a new one is real')
    require(records,
            f'A stop points at the record it stopped on, and {ticket} has no journal yet')
    refuse_human_executor(ticket_path(repository, ticket, records))
    current = journal.state(records)
    stage = current['stage']
    evident = _evident_stop(records, current)
    record = evident[1] if evident and evident[0] == reason else points_at(records)
    questions = open_questions(repository, ticket) if reason == 'question_open' else ()
    answer = _stop_action(reason, stage, record, ticket, actor, rules, questions=questions)
    already = standing(records, reason, record)
    if already is not None:
        return dict(answer, sequence=already['sequence'], recorded=False)
    if records[-1]['kind'] == 'receipt':
        # The one halt that is reported and not written. The receipt has to be the
        # last record for `verify-merge` to read it at all, which is that command's
        # own first rule and what
        # docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md settles,
        # so the ordinary end of a run leaves the journal as the receipt left it.
        # What a person allows is written, by `authorise`, and that is the record
        # the merge rests on.
        return dict(answer, sequence=None, recorded=False)
    written = journal.append(folder, records, kind='stop', stage=stage,
                             attempt=current['attempt'], actor=actor, head=repository.head(),
                             ticket=ticket,
                             data=stop(reason, stage, record,
                                       resume(reason, ticket, stage, actor),
                                       questions=questions))
    return dict(answer, sequence=written['sequence'], recorded=True)


def action(repository, ticket, records, rules, actor=None, folder=None):
    """The next action, exactly. Reads the journal and writes nothing.

    `folder` is where the journal lives, which the delivered stage needs because
    the check it reads digests the receipt file. Derived when a caller has not got
    it, so a direct call stays a one-liner.
    """
    actor = actor or f'{DEFAULT_TOOL}:implementer'
    refuse_human_executor(ticket_path(repository, ticket, records))
    if not records:
        return _start(repository, ticket, records, actor, rules)
    if folder is None:
        from .cli import journal_folder
        folder = journal_folder(repository, ticket)
    current = journal.state(records)
    evident = _evident_stop(records, current)
    if evident is not None:
        reason, record = evident
        return _stop_action(reason, current['stage'], record, ticket, actor, rules)
    return _stage_action(repository, folder, ticket, records, current, rules, actor)


def _start(repository, ticket, records, actor, rules):
    path = ticket_path(repository, ticket, records)
    require(path is not None,
            f'No ticket file for {ticket} under docs/tickets, so there is nothing to start')
    relative = str(path.relative_to(repository.root))
    return _action('clarify', 'command',
                   _argv('start', ticket, '--ticket', relative, '--actor', actor),
                   f'{ticket} has no journal yet. The first record snapshots the ticket as it '
                   'stands, which is what every later stage is judged against.', rules)


def _stage_action(repository, folder, ticket, records, current, rules, actor):
    stage = current['stage']
    if stage in ('clarify', 'solution'):
        return _gate(repository, ticket, stage, actor, rules, records=records)
    if stage == 'tdd':
        return _tdd(repository, ticket, records, current, rules, actor)
    if stage == 'review':
        return _review(repository, ticket, records, current, rules, actor)
    if stage == 'deliver':
        return _deliver(repository, ticket, actor, rules)
    return _after_the_receipt(repository, folder, ticket, records, actor, rules)


def _ask(ticket, stage, questions, actor, rules):
    """Every open question in one batch, and where the answer goes.

    One action for the whole batch, because a person answering a run's questions
    should be interrupted once. What only the work can settle is not here: the
    record's own `decisions` is where a named unknown belongs, with the observation
    that will settle it, and SEEN-100 measured that such a record is clearer rather
    than less clear. The two lists in the draft make that distinction, so nothing
    here has to guess which a question is.
    """
    return _action(stage, 'ask',
                   _argv('note', ticket, '--file', f'{DRAFTS}/{ticket}-answers.md',
                         '--actor', actor),
                   f'The {stage} draft leaves {len(questions)} question(s) that only a person can '
                   'settle, and they are asked together rather than one at a time. Put the answers '
                   f'in {DRAFTS}/{ticket}-answers.md, record them with the command above, then '
                   f'fold them into the draft: the gate refuses a {stage} record that still '
                   'carries an open question. Anything only the work can settle is not asked at '
                   "all, and belongs in the record's decisions with what will settle it.",
                   rules, questions=list(questions), reason='question_open')


def _gate(repository, ticket, stage, actor, rules, because='', records=()):
    """Draft the stage evidence, then pass the gate with it.

    The prose stays in cli.NEXT_COMMAND, which is where the handoff pack reads
    it; what this adds is the argv beside it.
    """
    from .cli import NEXT_COMMAND
    relative = draft_of(ticket, stage)
    if not (repository.root / relative).is_file():
        return _action(stage, 'command', _argv('draft', ticket),
                       f'{because}The {stage} evidence starts from the template and the gate '
                       f'reads what is filled in. {NEXT_COMMAND[stage]}', rules)
    batch = unanswered(records, open_questions(repository, ticket, stage))
    if batch:
        return _ask(ticket, stage, batch, actor, rules)
    return _action(stage, 'command',
                   _argv('advance', ticket, '--file', relative, '--actor', actor),
                   f'{because}The {stage} draft is written, so the gate decides. If it refuses, '
                   'that is the gate_refused stop and the same advance is not tried again.',
                   rules)


def _tdd(repository, ticket, records, current, rules, actor):
    solution = gates.latest_evidence(records, 'solution') or {}
    if gates.mode_of(solution) == 'non-code':
        return _gate(repository, ticket, 'tdd', actor, rules,
                     because='This ticket declared non-code mode at solution, so it has no slice '
                             'to prove and no check to record. ')
    slice_ = handoff.current_slice(records, current)
    if slice_ is not None and slice_['entry'] is not None:
        return _slice(ticket, records, slice_, rules, actor)
    return _before_the_tdd_gate(repository, ticket, records, current, rules, actor)


def _slice(ticket, records, slice_, rules, actor):
    """The next slice: routed first, then handed to an implementer of its own."""
    position, total = slice_['position'], slice_['total']
    entry = routing.for_slice(records, position)
    if entry is None:
        return _action('tdd', 'command', _argv('route', ticket, '--actor', actor),
                       f'Slice {position} of {total} is next and nothing has routed this plan. '
                       'The model and the effort a slice runs on are decided here, with the plan '
                       'and the risk answers on record, and never inside the session that would '
                       'benefit from a stronger model.', rules)
    return _action('tdd', 'spawn',
                   _argv('check', ticket, '--phase', 'red', '--actor', _role(actor, 'implementer'),
                         '--model', entry['model'], '--agent', IMPLEMENTER, '--', COMMAND),
                   f'Slice {position} of {total}, {entry["points"]} point(s), routed to '
                   f'{entry["model"]} at {entry["effort"]} effort. It is worked in a context of '
                   'its own, and its first record is the RED its route names.', rules,
                   agent=IMPLEMENTER,
                   task=entry.get('implementer_task') or routing.implementer_task(ticket, entry))


def _before_the_tdd_gate(repository, ticket, records, current, rules, actor):
    """Every slice is proved, so what is left is the measurement and the suite."""
    if _coverage(records, current) is None:
        return _action('tdd', 'command', _argv('coverage', ticket, '--actor', actor),
                       'Every slice of the plan is green, and the gated package is measured '
                       'once per attempt before the tdd gate reads the delta.', rules)
    if _regression(records, current) is None:
        return _action('tdd', 'command',
                       _argv('check', ticket, '--phase', 'regression', '--actor', actor,
                             '--', *regression_command(records)),
                       'The slices are green and measured, so the whole suite runs last: the '
                       'tdd gate requires the regression to come after every green it cites.',
                       rules)
    return _gate(repository, ticket, 'tdd', actor, rules)


def _coverage(records, current):
    for record in reversed(records):
        if (record['kind'] == 'check' and record['attempt'] == current['attempt']
                and record['data'].get('phase') == 'coverage'):
            return record
    return None


def _regression(records, current):
    """A passing regression recorded after the last green of the plan in hand."""
    greens = handoff.accepted_greens(records, handoff.plan_accepted_at(records))
    last = greens[-1]['sequence'] if greens else 0
    for record in reversed(records):
        if (record['kind'] == 'check' and record['attempt'] == current['attempt']
                and record['data'].get('phase') == 'regression'
                and record['data'].get('exit_code') == 0
                and record['sequence'] > last):
            return record
    return None


def regression_command(records):
    """The suite a regression runs, chosen from what the plan says it touches."""
    files = [name for entry in handoff.plan_of(records) for name in (entry.get('files') or [])]
    if files and all(str(name).startswith('harness/') for name in files):
        return PYTHON_SUITE
    return PNPM_SUITE


def _review(repository, ticket, records, current, rules, actor):
    """The cheapest pass first: the triage, then a reviewer with its own context."""
    reviewer = _role(actor, 'reviewer')
    triaged = gates.latest_triage(records, current)
    if triaged is None:
        return _action('review', 'command', _argv('review', 'triage', ticket, '--actor', reviewer),
                       'The review runs its deterministic pass first, which settles what no '
                       'model needs to read and says what the reviewer must.', rules)
    if _qa(records, current) is None:
        return _action('review', 'spawn',
                       _argv('check', ticket, '--phase', 'qa', '--actor', reviewer,
                             '--agent', REVIEWER, '--', COMMAND),
                       f'Triage record {triaged["sequence"]} says what this review reads. The '
                       'reviewer reads it in a context of its own, because a session that wrote '
                       'the code cannot claim an independent review of it.', rules,
                       agent=REVIEWER, task=triaged['data'].get('reviewer_task'))
    return _gate(repository, ticket, 'review', reviewer, rules)


def _qa(records, current):
    for record in reversed(records):
        if (record['kind'] == 'check' and record['attempt'] == current['attempt']
                and record['data'].get('phase') == 'qa'):
            return record
    return None


def _deliver(repository, ticket, actor, rules):
    relative = draft_of(ticket, 'deliver')
    if not (repository.root / relative).is_file():
        return _action('deliver', 'command', _argv('draft', ticket),
                       'The review passed. The deliver evidence names the remote and the pull '
                       'request, and the ticket\'s status, its ## Outcome and its ticked criteria '
                       'go in before the gate reads the tree.', rules)
    return _action('deliver', 'command',
                   _argv('verify-delivery', ticket, '--file', relative, '--actor', actor),
                   'Commit, push and open the pull request, then this writes the receipt. Red CI '
                   'on the commit it would attest is the ci_red stop.', rules)


def authorisation(records):
    """The authorisation for the delivery in hand, or nothing.

    After the receipt, so one written before a reopen never authorises the delivery
    that followed it: what a person allowed was a tree, and a reopened ticket
    delivers another.
    """
    receipt = next((record['sequence'] for record in reversed(records)
                    if record['kind'] == 'receipt'), None)
    if receipt is None:
        return None
    for record in reversed(records):
        if record['kind'] == 'authorisation' and record['sequence'] > receipt:
            return record
    return None


def merge_ready(repository, folder, records):
    """Whether verify-merge is green, read by running it: it records nothing.

    Its refusal is not a stop. What it says is what is still in the way, and the
    action it produces is the same check run by hand, so the person reads the whole
    of it rather than a summary of it.
    """
    from . import delivery
    try:
        return delivery.verify_merge(repository, folder, records), None
    except (HarnessError, OSError) as error:
        return None, str(error)


def _after_the_receipt(repository, folder, ticket, records, actor, rules):
    """The receipt is written, so what is left is a person's.

    Three answers, in the order the evidence decides them: the merge once somebody
    has allowed it, the check while it is not yet green, and the stop in between.
    The run never takes the merge in any of them.
    """
    allowed = authorisation(records)
    if allowed is not None:
        tip = allowed['data'].get('tip')
        head = repository.head()
        if tip and tip != head:
            return _action('delivered', 'command',
                           _argv('reopen', ticket, '--reason',
                                 f'The branch moved to {head[:8]} after the merge of {tip[:8]} '
                                 'was authorised', '--actor', actor),
                           f'Record {allowed["sequence"]} authorised {tip[:8]} and the branch is '
                           f'now at {head[:8]}, so what would merge is not what was allowed. '
                           'Reopen voids the receipt and returns the ticket to tdd, which is the '
                           'only honest way back: nobody has seen this tree.', rules)
        return _action('delivered', 'merge', list(MERGE),
                       f'{allowed["data"].get("by")} authorised this merge at record '
                       f'{allowed["sequence"]}, over the receipt and the tip verify-merge read '
                       'there. The harness has no merge of its own and never will: run the '
                       'command above yourself, or leave it to whoever authorised it.', rules,
                       authorisation=allowed['sequence'],
                       by=allowed['data'].get('by'),
                       authorised_at=allowed['timestamp'],
                       receipt=allowed['data'].get('receipt_sha256'),
                       tip=tip)
    ready, refusal = merge_ready(repository, folder, records)
    if ready is None:
        return _action('delivered', 'command', _argv('verify-merge', ticket),
                       'The receipt is written, so what is left is the check that it still '
                       'describes what is about to merge, and the receipt hash in the pull '
                       f'request body. It does not pass yet: {refusal}', rules)
    return _stop_action('awaiting_authorisation', 'delivered', points_at(records), ticket, actor,
                        rules)


def latest_stop(records):
    """The most recent halt, or nothing. What an unmet criterion is waiting on."""
    for record in reversed(records):
        if record['kind'] == 'stop':
            return record
    return None


def defects(records):
    """What went wrong in the run itself, counted from the records rather than told.

    One so far: a second question batch. A run asks every question it has at once,
    so a second batch is a first batch that was incomplete, and it cost a person
    two interruptions where one would have done. Counted from the stop records,
    because prose about a run is the run's own account of itself.
    """
    batches = question_stops(records)
    if len(batches) < 2:
        return []
    return [dict(defect='second_question_batch',
                 records=[record['sequence'] for record in batches],
                 detail=f'{len(batches)} question batches, at records '
                        + ', '.join(str(record['sequence']) for record in batches)
                        + '. A run puts every question it has to a person at once, so a later '
                          'batch is an earlier one that was incomplete.')]


def _waiting_on(records, current, clarify_at, check):
    """What an unticked criterion is waiting on, from the journal and nowhere else."""
    parts = []
    stopped = latest_stop(records)
    if stopped is not None and stopped['sequence'] > (clarify_at or 0):
        parts.append(f'The run stopped at {stopped["data"]["reason"]}, recorded at '
                     f'{stopped["sequence"]} over record {stopped["data"]["record"]}.')
    parts.append(f'The ticket is at {current["stage"]}, attempt {current["attempt"]}.')
    if check is None:
        parts.append('No clarify record restates a check at this position, so nothing on record '
                     'says what would satisfy it.')
    else:
        parts.append(f'Record {clarify_at} restates it as: {check}')
    return ' '.join(parts)


def summary(repository, ticket, records, rules):
    """Every criterion, its box, and what each unmet one waits on.

    The one thing a run produces to be read rather than executed, and it asserts
    nothing of its own: the box is the ticket file's, the check is the clarify
    record's, and a defect is counted from the records. Read-only and actorless,
    for the reason `status` and `budget` are: a command a person runs to see where a
    ticket stands must not make its journal longer.
    """
    path = ticket_path(repository, ticket, records)
    require(path is not None and path.is_file(),
            f'No ticket file for {ticket} under docs/tickets, so there are no criteria to list')
    text = path.read_text()
    current = journal.state(records) if records else dict(stage=STAGES[0], attempt=1)
    clarified = gates.latest_evidence(records, 'clarify') or {}
    restated = clarified.get('acceptance') or []
    clarify_at = next((record['sequence'] for record in reversed(records)
                       if record['kind'] == 'advance'
                       and record['data'].get('from_stage') == 'clarify'), None)
    entries = []
    for position, (met, criterion) in enumerate(criteria(text), start=1):
        check = restated[position - 1] if position <= len(restated) else None
        entries.append(dict(position=position,
                            criterion=criterion,
                            box='x' if met else ' ',
                            met=met,
                            check=check,
                            check_record=None if check is None else clarify_at,
                            waiting_on=None if met
                            else _waiting_on(records, current, clarify_at, check)))
    return dict(ticket=ticket,
                stage=current['stage'],
                attempt=current['attempt'],
                ticket_file=str(path.relative_to(repository.root)),
                criteria=entries,
                met=sum(1 for entry in entries if entry['met']),
                unmet=sum(1 for entry in entries if not entry['met']),
                question_batches=[record['sequence'] for record in question_stops(records)],
                authorisation=(authorisation(records) or {}).get('sequence'),
                defects=defects(records),
                stops=list(stops(rules)))
