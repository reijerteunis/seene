"""The commands a session runs, and the order they may be run in.

Two families: ticket commands that read and extend one journal, and repository
commands that look after the harness itself. Ticket text and check output are
data the harness passes through files; nothing here interpolates them into a
shell.
"""

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from . import (checks, cost as cost_module, coverage as coverage_module, doctor, gates,
               context, graph as graph_module, handoff as handoff_module, jev, journal, kpi,
               report as report_module, risk, sessions, thresholds)
from .errors import HarnessError, require
from .paths import (DRAFTS, HANDOFF_PACK, HISTORY, KINDS, LOCK, NON_CODE_TEMPLATE, STAGES,
                    TEMPLATES, TEMPLATE_FOR_STAGE, TICKETS, WORKING_STAGES)
from .repository import Repository

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TICKET_COMMANDS = ('start', 'status', 'history', 'draft', 'note', 'check', 'advance',
                   'return', 'graph', 'decide', 'coverage', 'handoff', 'budget', 'reopen',
                   'discard', 'verify-delivery', 'verify-merge')
# handoff writes a record, so it is bound to the ticket's own branch like every
# other writing command. status --brief is not here and neither is budget: a
# command a session runs to see where it stands must not make the journal longer
# every time it is run.
WRITING_COMMANDS = ('start', 'note', 'check', 'advance', 'return', 'graph', 'decide', 'coverage',
                    'handoff', 'reopen',
                    'verify-delivery')
BRANCH = re.compile(r'^(claude|codex)/(?P<ticket>[A-Z]+-\d+)-')

# The questions that can refuse an advance, and which way round each one reads.
# clarified and solution_complete must clear their bar; must_fix is the
# opposite, because a confident yes means something is still broken. A score
# question routes rather than blocks, so none appears here.
BLOCKING = {'clarify': {'clarified': 'clears'},
            'solution': {'solution_complete': 'clears'},
            'tdd': {},
            'review': {'must_fix': 'does not clear'},
            'deliver': {}}

NEXT_COMMAND = {
    'clarify': 'harness draft <ticket>, fill in the scope and the acceptance checks, '
               'then harness advance',
    'solution': 'harness draft <ticket>, name the files, the tests to write first and the '
                'rollback, then harness advance',
    'tdd': 'harness check --phase red, then green per slice, then regression, then harness advance',
    'review': 'read the diff and the journal, harness check --phase qa, then harness advance '
              'or harness return',
    'deliver': 'commit, push, open the pull request, then harness verify-delivery',
    'delivered': 'nothing; open a follow-up ticket for further work',
}


def build_parser():
    parser = argparse.ArgumentParser(prog='harness/run.py', description='The Seen harness.')
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT,
                        help='Project root (defaults to this checkout)')
    commands = parser.add_subparsers(dest='command', required=True)

    def ticket_command(name, help_text):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument('ticket', help='Ticket identifier, for example SEEN-086')
        return sub

    start = ticket_command('start', 'Begin a ticket and snapshot it')
    start.add_argument('--ticket', dest='ticket_file', required=True,
                       help='Project-relative path to the ticket file')
    start.add_argument('--actor', required=True, help='tool:role, for example claude:implementer')

    status = ticket_command('status', 'Report the stage, the branch and the next command')
    status.add_argument('--brief', action='store_true',
                        help='Print the handoff pack a fresh session starts from')
    history = ticket_command('history', 'Print the verified journal')
    history.add_argument('--kind', choices=KINDS, help='Show only records of one kind')

    draft = ticket_command('draft', 'Copy the current stage template into .harness-drafts')
    draft.add_argument('--stage', choices=list(TEMPLATE_FOR_STAGE), help='Override the stage')
    draft.add_argument('--non-code', action='store_true',
                       help='Take the non-code path at the TDD stage')

    note = ticket_command('note', 'Record a decision, a question or a brief')
    note.add_argument('--file', required=True, help='Markdown file holding the note')
    note.add_argument('--actor', required=True)
    note.add_argument('--from', dest='from_agent',
                      help='The agent this came back from, for example seen-scout. A note from '
                           'an agent is a brief and is held to the word cap')

    check = ticket_command('check', 'Run and record a verification command')
    check.add_argument('--phase', required=True)
    check.add_argument('--actor', required=True)
    check.add_argument('--timeout', type=int, help='Seconds before the command is stopped')

    advance = ticket_command('advance', 'Pass the current stage gate with completed evidence')
    advance.add_argument('--file', required=True, help='Completed stage evidence JSON')
    advance.add_argument('--actor', required=True)

    back = ticket_command('return', 'Send the ticket back to an earlier stage')
    back.add_argument('--to', required=True)
    back.add_argument('--reason', required=True)
    back.add_argument('--actor', required=True)

    measure = ticket_command('coverage', 'Measure coverage on the gated package and record the delta')
    measure.add_argument('--actor', required=True)
    measure.add_argument('--timeout', type=int, help='Seconds before the command is stopped')

    decide = ticket_command('decide', 'Ask Jev a typed question on the record and keep the answer')
    decide.add_argument('--question', required=True, help=', '.join(sorted(jev.QUESTIONS)))
    decide.add_argument('--answer', help='The human answer, when there is no credential')
    decide.add_argument('--confidence', type=float, default=1.0,
                        help='How sure the human is, 0 to 1 (default 1.0)')
    decide.add_argument('--actor', required=True)

    graph = ticket_command('graph', 'Ask the knowledge graph and record the answer')
    graph.add_argument('mode', help='impact, path, explain or prs')
    graph.add_argument('--about', help='The node or question, for impact and explain')
    graph.add_argument('--from', dest='source', help='Start node, for path')
    graph.add_argument('--to', dest='target', help='End node, for path')
    graph.add_argument('--actor', required=True)

    pack = ticket_command('handoff', 'Write the pack a fresh session starts from at a slice boundary')
    pack.add_argument('--actor', required=True)
    pack.add_argument('--slice-done', dest='slice_done', type=int,
                      help='How many slices are done, when the greens do not say it: a slice '
                           'that recorded two greens counts twice without this')

    ticket_command('budget', "This session's tokens and tool calls against the session budget")

    reopen = ticket_command('reopen', 'Void a receipt and return the ticket to tdd, before merge')
    reopen.add_argument('--reason', required=True)
    reopen.add_argument('--actor', required=True)

    discard = ticket_command('discard', 'Remove an uncommitted journal, recording what was removed')
    discard.add_argument('--reason', required=True)
    discard.add_argument('--confirm', help='The ticket id, typed out, to confirm the removal')
    discard.add_argument('--actor', required=True)

    ticket_command('verify-merge', 'Check the receipt still describes what is about to merge')

    deliver = ticket_command('verify-delivery', 'Confirm the delivery and write the receipt')
    deliver.add_argument('--file', required=True, help='Completed deliver evidence JSON')
    deliver.add_argument('--actor', required=True)

    report = commands.add_parser('report', help='Aggregate delivered tickets into a report')
    report.add_argument('--week', action='store_true', help='The ISO week of --date, or today')
    report.add_argument('--sprint', type=int, help='Planned against delivered for one sprint')
    report.add_argument('--date', help='The date whose week to report, YYYY-MM-DD')

    commands.add_parser('sync', help='Generate the skill copies from docs/harness/skill.md')
    commands.add_parser('lint', help='Refuse live marketplace hosts in test code')
    commands.add_parser('doctor', help='Check the harness files, the journals and the links')
    commands.add_parser('list', help='List every ticket with a journal and where it stands')
    return parser


def parse(argv):
    parser = build_parser()
    known, extra = parser.parse_known_args(argv)
    if known.command in ('check', 'coverage'):
        require(extra and extra[0] == '--' or known.command == 'coverage',
                'Put the check command after --')
        known.argv = extra[1:] if extra else []
    else:
        require(not extra, f'Unrecognised arguments: {" ".join(extra)}')
    return known


def require_ticket_id(ticket, rules):
    prefix = rules['tickets']['prefix']
    require(re.fullmatch(rf'{prefix}-\d{{3,}}', ticket),
            f'A ticket id is {prefix} followed by at least three digits, not {ticket!r}')


def require_actor(actor, rules):
    tools, roles = rules['actors']['tools'], rules['actors']['roles']
    tool, _, role = str(actor).partition(':')
    require(tool in tools and role in roles,
            f'An actor is tool:role, one of {", ".join(tools)} and one of {", ".join(roles)}, '
            f'not {actor!r}. It is a self-reported claim, so report it honestly')


def require_branch(repository, ticket):
    """One ticket, one branch, checked on every command that writes.

    The expensive mistake is not starting on the wrong branch, it is drifting
    onto another branch halfway through and recording evidence about a tree that
    belongs to different work.
    """
    branch = repository.branch_or_none()
    match = BRANCH.match(branch or '')
    require(match and match.group('ticket') == ticket,
            f'This ticket belongs on branch claude/{ticket}-<slug> or codex/{ticket}-<slug>, '
            f'not on {branch or "a detached HEAD"}')


def lock(root):
    """An advisory lock, never broken automatically.

    Two sessions may share a checkout. Breaking a lock because its process looks
    dead is how two commands interleave writes to one record.
    """
    path = root / LOCK
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise HarnessError(f'Another harness command holds {LOCK}: {path.read_text().strip()}. '
                           'Check that process before removing the file by hand')
    with os.fdopen(descriptor, 'w') as handle:
        handle.write(f'pid {os.getpid()} running {" ".join(sys.argv[1:])}\n')
    return path


def journal_folder(repository, ticket):
    folder = (repository.root / HISTORY / ticket).resolve()
    require(folder.is_relative_to(repository.root), 'A journal must stay inside the project')
    return folder


def start(repository, folder, records, args, rules):
    require(not records, f'{args.ticket} already has a journal; use status and resume it')
    ticket_file = repository.file_inside(args.ticket_file)
    return journal.append(folder, records, kind='start', stage=STAGES[0], attempt=1,
                          actor=args.actor, head=repository.head(), ticket=args.ticket,
                          data=dict(ticket_file=str(ticket_file.relative_to(repository.root)),
                                    ticket_snapshot=ticket_file.read_text(),
                                    base_commit=repository.head()))


def describe(repository, ticket, records, folder):
    """Everything a resuming session needs before it touches the project.

    Deliberately cheap: one git call beyond HEAD, no fingerprint and no network,
    because a status command that is slow is a status command nobody runs.
    """
    current = journal.state(records)
    return dict(ticket=ticket,
                stage=current['stage'],
                attempt=current['attempt'],
                records=current['records'],
                ticket_file=records[0]['data']['ticket_file'],
                started=records[0]['timestamp'],
                updated=records[-1]['timestamp'],
                last_actor=records[-1]['actor'],
                branch=repository.branch_or_none(),
                head=repository.head(),
                chain_head=journal.digest(folder / f'{len(records):04d}.json'),
                next_command=NEXT_COMMAND[current['stage']])


def build_pack(repository, records, current, rules, slice_done=None):
    """The pack, rendered from the journal and nothing else."""
    return handoff_module.pack(records, current, rules,
                               branch=repository.branch_or_none(),
                               next_command=NEXT_COMMAND[current['stage']],
                               slice_done=slice_done)


def pack_path(repository, ticket):
    return repository.root / DRAFTS / HANDOFF_PACK.format(ticket=ticket)


def handoff(repository, folder, records, args, current, rules):
    """Write the pack at a slice boundary and record what was handed over.

    The pack is derived, so the file is replaceable and the journal holds its
    hash. The figures are the session's own spending at the moment it stopped,
    which is the one place a session's cost is written down.
    """
    built = build_pack(repository, records, current, rules,
                       slice_done=getattr(args, 'slice_done', None))
    text = built['markdown']
    carried = secrets_module().leaked(text, os.environ)
    require(not carried,
            f'This pack carries the value of {", ".join(carried)} from the environment. A pack '
            'is read by the next session and by people; credentials do not go in one')
    require(built['estimated_tokens'] <= built['token_limit'],
            f'This pack is about {built["estimated_tokens"]} tokens against a limit of '
            f'{built["token_limit"]}. The pack is built from bounded sections, so a pack over '
            'the limit is a bug in harness/handoff.py rather than a journal to shorten')
    path = pack_path(repository, args.ticket)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit, because the bytes on disk are compared against the hash this
    # record carries, and a ticket title is not guaranteed to be ASCII.
    path.write_text(text, encoding='utf-8')
    return journal.append(folder, records, kind='handoff', stage=current['stage'],
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket,
                          data=dict(pack=str(path.relative_to(repository.root)),
                                    sha256=handoff_module.digest(text),
                                    estimated_tokens=built['estimated_tokens'],
                                    token_limit=built['token_limit'],
                                    slice=built['slice'],
                                    figures=sessions.figures(repository.root)))


def secrets_module():
    from . import secrets
    return secrets


def brief(repository, ticket, records, current, rules):
    """What a fresh session reads before it does anything else.

    Built from the journal rather than printed from the file, because the drafts
    directory is gitignored: a session in another checkout has the records and
    not the pack, and a --brief that is empty exactly when it is needed is worse
    than one that rebuilds it. The last recorded hash is compared against the
    file so drift is visible rather than silent.
    """
    built = build_pack(repository, records, current, rules)
    recorded = next((record for record in reversed(records) if record['kind'] == 'handoff'), None)
    path = pack_path(repository, ticket)
    matches = None
    if recorded is not None and path.is_file():
        matches = (handoff_module.digest(path.read_text(encoding='utf-8'))
                   == recorded['data']['sha256'])
    return dict(ticket=ticket,
                stage=current['stage'],
                attempt=current['attempt'],
                records=len(records),
                pack=built['markdown'],
                estimated_tokens=built['estimated_tokens'],
                pack_file=str(path.relative_to(repository.root)),
                recorded_at=recorded['sequence'] if recorded else None,
                pack_matches_record=matches,
                next_command=NEXT_COMMAND[current['stage']])


def budget(repository, ticket, rules):
    """Where this session stands against the budget for one slice.

    It reads the session's own log and the journal not at all, so it can be run
    at any moment and as often as a session likes without making the journal
    longer. What is recorded instead is the figure at a boundary, which the
    handoff record carries.
    """
    limits = rules['session']
    spent = sessions.figures(repository.root)
    return dict(ticket=ticket, **sessions.against_budget(spent, limits['output_token_budget']))


def draft(repository, records, args):
    stage = args.stage or journal.state(records)['stage']
    mode = 'non-code' if getattr(args, 'non_code', False) else None
    name = gates.template_name(stage, mode)
    source = repository.root / TEMPLATES / name
    require(source.is_file(), f'Missing template: {source}')
    target = repository.root / DRAFTS / f'{args.ticket}-{stage}.json'
    require(not target.exists(),
            f'A draft already exists; edit or delete it: {target.relative_to(repository.root)}')
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.loads(source.read_text())
    content.update(extra_review_fields(records, stage))
    target.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n')
    current = journal.state(records)
    available = [dict(record=record['sequence'], phase=record['data']['phase'],
                      exit_code=record['data']['exit_code'], command=record['data']['command'])
                 for record in records
                 if record['kind'] == 'check' and record['stage'] == current['stage']
                 and record['attempt'] == current['attempt']]
    return dict(stage=stage,
                draft=str(target.relative_to(repository.root)),
                template=str(TEMPLATES / name),
                checks_in_this_attempt=available,
                reminder='Replace every example value with real evidence, then pass this file '
                         'to advance. Unchanged template text counts as a missing answer.')


def coverage(repository, folder, records, args, current, rules):
    """Measure the gated package and record what it is against what it was."""
    require(current['stage'] == 'tdd', 'Coverage is measured at the tdd stage')
    limits = rules['checks']
    command = list(getattr(args, 'argv', None) or coverage_module.DEFAULT_COMMAND)
    evidence = checks.run(repository, command, 'coverage',
                          args.timeout or limits['default_timeout_seconds'],
                          limits['output_limit_bytes'])
    return journal.append(folder, records, kind='check', stage='tdd', attempt=current['attempt'],
                          actor=args.actor, head=repository.head(), ticket=args.ticket,
                          data=coverage_module.compare(repository.root, evidence))


def decide(repository, folder, records, args, current, rules):
    """Ask one typed question about this ticket and keep the answer."""
    answer = jev.ask(repository.root, rules, args.question,
                     state_for(records, current, None, repository.root,
                               question=args.question),
                     args.answer, args.confidence)
    return journal.append(folder, records, kind='decision', stage=current['stage'],
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket, data=answer)


def state_for(records, current, evidence=None, root=None, question=None):
    """What Jev is given to judge: the ticket, the stage and the record at hand.

    The ticket text is read from the file as it stands now, not from the snapshot
    in record 1. Tickets are amended during clarify, routinely and deliberately,
    and judging a record against the document it was written before is how a
    resolved question keeps reading as an open one. The snapshot stays in the
    journal, where it is evidence of what the work was asked to do.

    Internal working text only. No credential is in it, and nothing is read from
    the environment to build it.
    """
    ticket_id = records[0]['data'].get('ticket_id', records[0]['ticket'])
    ticket_text, source = _ticket_text(records[0]['data'], ticket_id, root)
    state = dict(ticket=ticket_id,
                 stage=current['stage'],
                 attempt=current['attempt'],
                 ticket_text=ticket_text,
                 ticket_source=source,
                 record=evidence if evidence is not None else _latest_evidence(records))
    if question == 'risk' and root is not None:
        # Evidence rather than impressions, and only for the question it is
        # evidence about: one more string in every payload is not free, which
        # SEEN-101 had to say out loud after adding ticket_source.
        state['change_risk'] = risk.assess(root)
    return state


def _ticket_text(first, ticket_id, root):
    """The ticket and where it came from: the path, the id, or the snapshot.

    A filename carries a title, so renaming a ticket is ordinary. SEEN-096 was
    split three ways, its file was renamed, and every judgement after that read
    a snapshot of the ticket before the split. The id is stable; the filename is
    not. Which source was used is returned rather than hidden, because a
    judgement against a snapshot of a deleted ticket is weaker evidence than one
    against the ticket, and a journal should say which it was.
    """
    snapshot = first['ticket_snapshot']
    if root is None:
        return snapshot, 'snapshot in record 1'
    path = root / first['ticket_file']
    if path.is_file():
        return path.read_text(), 'recorded path'
    matches = sorted((root / TICKETS).glob(f'{ticket_id}-*.md'))
    require(len(matches) < 2,
            f'{ticket_id} matches more than one ticket file, so the harness cannot tell which '
            'one it is judging against: '
            + ', '.join(str(match.relative_to(root)) for match in matches))
    if matches:
        return matches[0].read_text(), 'found by id'
    return snapshot, 'snapshot in record 1' 


def _latest_evidence(records):
    for record in reversed(records):
        if record['kind'] == 'advance':
            return record['data']['evidence']
    return {}


def graph(repository, folder, records, args, current, rules):
    """Ask the graph and keep the answer, as a note at the current stage.

    Recorded rather than printed, so the context a decision was taken on is in
    the journal beside the decision.
    """
    evidence = graph_module.ask(repository, args.mode, args.about, args.source, args.target)
    return journal.append(folder, records, kind='note', stage=current['stage'],
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket, data=evidence)


def extra_review_fields(records, stage):
    """What a review must answer beyond the template, given the solution's decisions.

    A change that touches billing or the policy gate is reviewed twice and
    against the security checklist, so the draft asks for both rather than
    leaving a reviewer to remember.
    """
    if stage != 'review':
        return {}
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'solution':
            for decision in record['data'].get('decisions', []):
                if (decision['question'] == 'touches_billing_or_policy_gate'
                        and decision['outcome'] == 'yes'):
                    return {'second_reviewer': 'The second reviewer, tool:role. Required because '
                                               'this change touches billing or the policy gate.',
                            'security_checklist': [
                                'No secret in the diff',
                                'No new dependency without a lockfile entry and an audit',
                                'No live marketplace call in a test',
                                'No PII field without its expiry job',
                                'No tool without a policy-gate declaration']}
    return {}


def note(repository, folder, records, args, current, rules):
    """A note, or a brief from one of the agents.

    A brief is the only thing that crosses back from a context of its own, so it
    is held to a word cap here rather than in the agent's instructions: what an
    agent is told is a request, and what the harness records is a control. It
    stays a note rather than a new kind, because the kinds are the one vocabulary
    every reader of a journal has to know.
    """
    text = repository.file_inside(args.file).read_text()
    require(text.strip(), 'A note must not be empty')
    data = dict(text=text)
    agent = getattr(args, 'from_agent', None)
    if agent:
        roster = rules['agents']['names']
        require(agent in roster,
                f'{agent!r} is not one of the agents this repository generates: '
                f'{", ".join(roster)}. An agent with no source has no instructions either')
        limit = rules['agents']['brief_word_limit']
        words = len(text.split())
        require(words <= limit,
                f'This brief is {words} words against a cap of {limit}. Cut it to the answer, '
                'the paths it rests on and the questions it could not answer; a brief that has '
                'to be skimmed buys the session nothing')
        data.update(agent=agent, words=words)
    return journal.append(folder, records, kind='note', stage=current['stage'],
                          attempt=current['attempt'], actor=args.actor, head=repository.head(),
                          ticket=args.ticket, data=data)


def check(repository, folder, records, args, current, rules):
    stage, phase = current['stage'], args.phase
    allowed = checks.phases_for(stage)
    require(phase in allowed,
            f'A {phase} check is not part of the {stage} stage'
            + (f'; this stage records {", ".join(allowed)}' if allowed
               else ', which records no checks'))
    limits = rules['checks']
    timeout = args.timeout or limits['default_timeout_seconds']
    require(0 < timeout <= limits['maximum_timeout_seconds'],
            f'A check timeout must be between 1 and {limits["maximum_timeout_seconds"]} seconds')
    evidence = checks.run(repository, args.argv, phase, timeout, limits['output_limit_bytes'])
    record = journal.append(folder, records, kind='check', stage=stage, attempt=current['attempt'],
                            actor=args.actor, head=repository.head(), ticket=args.ticket,
                            data=evidence)
    # The run is recorded either way, because it happened. What is refused is the
    # claim that it was a RED, which an exit code of zero contradicts and which a
    # timeout or a failure to start cannot support.
    require(phase != 'red' or checks.demonstrates_failure(evidence),
            f'Recorded as check {record["sequence"]}, but this RED did not fail: the command exited '
            f'{evidence["exit_code"]}. A RED is a test failing for the reason the solution record '
            'predicted, not a command that passed, timed out or could not start')
    return record


def read_evidence(repository, relative):
    """Read a stage evidence file, which must live where drafts live.

    Anywhere else it is an untracked file in the tree, so submitting it would
    change the fingerprint that review attested and delivery would later refuse
    the ticket for a change the harness itself caused.
    """
    require(Path(relative).parts[:1] == (str(DRAFTS),),
            f'Stage evidence must live in {DRAFTS}/, where harness draft puts it, so that '
            f'submitting it cannot change the tree under review: {relative}')
    try:
        return json.loads(repository.file_inside(relative).read_text())
    except json.JSONDecodeError as error:
        raise HarnessError(f'Stage evidence is not valid JSON: {error}')


def recorded_decisions(records, stage, attempt):
    """Decisions already taken for this stage and this attempt, latest per question."""
    taken = {}
    for record in records:
        if (record['kind'] == 'decision' and record['stage'] == stage
                and record['attempt'] == attempt):
            taken[record['data']['question']] = record['data']
    return taken


def stage_decisions(repository, records, args, current, rules, evidence):
    """Every question this stage owns, answered once.

    An answer already recorded for this stage and attempt is reused rather than
    asked again. Without a credential the harness refuses and names the command
    that records a human answer, because a judgement nobody made is not one.
    """
    stage = current['stage']
    taken = recorded_decisions(records, stage, current['attempt'])
    outstanding = [name for name in jev.questions_for(stage) if name not in taken]
    fresh = {}
    if outstanding:
        if jev.credential(repository.root):
            # One request for the whole stage, which is what the API is shaped for.
            # The whole stage in one request, which is what the API is shaped
            # for, so the change risk goes in whenever risk is among the
            # questions being asked rather than once per question.
            asked = 'risk' if 'risk' in outstanding else None
            fresh = {answer['question']: answer
                     for answer in jev.ask_many(repository.root, rules, outstanding,
                                                state_for(records, current, evidence,
                                                          repository.root, question=asked))}
        else:
            fresh = {name: jev.unavailable(
                name, jev.QUESTIONS[name],
                f'No Jev credential. Record a human answer with: harness decide {args.ticket} '
                f'--question {name} --answer <option> --confidence <0 to 1> '
                f'--actor {args.actor}') for name in outstanding}
    return [taken.get(name) or fresh[name] for name in jev.questions_for(stage)]


def require_decisions_pass(stage, answers):
    """Refuse an advance the stage's blocking questions did not allow.

    Each blocking question says which way it reads. A decision that could not be
    taken at all blocks nothing: it is recorded as unavailable and counted later,
    rather than standing in for a judgement.
    """
    rules = BLOCKING.get(stage, {})
    for answer in answers:
        sense = rules.get(answer['question'])
        if sense is None or answer['passed'] is None:
            continue
        refused = (answer['passed'] is False) if sense == 'clears' else answer['passed']
        if not refused:
            continue
        probability = answer['probabilities'].get(
            'yes', answer['probabilities'].get(answer['outcome'], 0.0))
        # The message says what happened. Printing the rule's own word made a
        # decision that failed read as one that cleared, which is the opposite
        # of what a refusal is for.
        happened = 'did not clear' if sense == 'clears' else 'cleared'
        raise HarnessError(
            f'The {answer["question"]} question {happened} its threshold: {probability} against '
            f'{answer["threshold"]}, answered {answer["outcome"]!r} by {answer["source"]}. '
            f'Resolve what is still open, record a note saying how, then advance again')


def advance(repository, folder, records, args, current, rules):
    stage = current['stage']
    data = read_evidence(repository, args.file)
    data.update(gates.evaluate(stage, data, records, current, repository, rules))
    answers = stage_decisions(repository, records, args, current, rules, data)
    require_decisions_pass(stage, answers)
    next_stage = STAGES[STAGES.index(stage) + 1]
    record = journal.append(folder, records, kind='advance', stage=stage,
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket,
                            data=dict(from_stage=stage, to_stage=next_stage, evidence=data,
                                      decisions=answers))
    discard_draft(repository, args.ticket, stage)
    return record


def discard_draft(repository, ticket, stage):
    """Remove the draft the evidence came from; the journal now holds it."""
    (repository.root / DRAFTS / f'{ticket}-{stage}.json').unlink(missing_ok=True)


def go_back(repository, folder, records, args, current, rules):
    stage = current['stage']
    targets = rules['stages']['return_targets']
    require(args.to in targets, f'A return targets one of {", ".join(targets)}, not {args.to!r}')
    require(STAGES.index(args.to) < STAGES.index(stage),
            f'A return must target a stage before {stage}')
    require(args.reason.strip(), 'A return needs a recorded reason')
    return journal.append(folder, records, kind='return', stage=stage,
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket,
                          data=dict(from_stage=stage, to_stage=args.to,
                                    to_attempt=current['attempt'] + 1, reason=args.reason))


DISCARDED = Path('docs/harness/discarded.jsonl')


def discard_journal(repository, folder, records, args, rules):
    """Remove a journal that should never have been started.

    The only way the harness deletes evidence, and it refuses the cases where
    deleting would be wrong: a record that is committed is history, and history
    is not deleted. The confirmation is the ticket id typed out rather than a
    prompt, because a prompt a session can answer is not a control on a session.
    What was removed is written down first, hashes included, so a deletion is
    itself evidence.
    """
    require(records, f'{args.ticket} has no journal to discard')
    require(args.confirm == args.ticket,
            'Discarding a journal removes evidence. Repeat the ticket id to confirm: '
            f'--confirm {args.ticket}')
    require(args.reason.strip(), 'A discard needs a recorded reason')
    committed = [path.name for path in sorted(folder.glob('[0-9]*.json'))
                 if repository.is_tracked(path.relative_to(repository.root))]
    require(not committed,
            f'{", ".join(committed)} are committed, so they are history and history is not '
            'deleted. Use harness reopen if the work must change')

    decision = jev.ask(repository.root, rules, 'is_destructive',
                       dict(ticket=args.ticket, operation='discard the journal',
                            reason=args.reason, records=len(records)),
                       answer='yes', confidence=1.0)
    removed = [dict(name=path.name, sha256=journal.digest(path))
               for path in sorted(folder.glob('[0-9]*.json'))]
    line = dict(ticket=args.ticket, timestamp=records[-1]['timestamp'], actor=args.actor,
                reason=args.reason, decision=decision, records=removed, head=repository.head())
    log = repository.root / DISCARDED
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a') as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + '\n')

    for path in sorted(folder.iterdir()):
        if path.is_file():
            path.unlink()
    folder.rmdir()
    return dict(ticket=args.ticket, removed=len(removed), recorded_in=str(DISCARDED))


def reopen(repository, folder, records, args, current):
    """Void a receipt while the work can still change.

    A receipt is final when the work is merged, not when it is written. Until
    then a defect found after delivery is rework, and the journal should say so
    rather than have the receipt quietly attest a commit that is not the one
    that merges. The receipt is never edited: this record follows it.
    """
    require(current['stage'] == 'delivered',
            f'Only a delivered ticket can be reopened; this one is at {current["stage"]}')
    require(args.reason.strip(), 'A reopen needs a recorded reason')
    receipt = next((record for record in reversed(records) if record['kind'] == 'receipt'), None)
    require(receipt, 'This ticket has no receipt to void')
    commit = receipt['data']['commit']
    merged = repository.is_in_default_branch(commit)
    require(not merged,
            f'{commit[:8]} is already merged into {merged}, so its receipt is history. '
            'Open a follow-up ticket instead')
    path = folder / f'{receipt["sequence"]:04d}.json'
    return journal.append(folder, records, kind='reopen', stage='delivered',
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket,
                          data=dict(from_stage='delivered', to_stage='tdd',
                                    to_attempt=current['attempt'] + 1,
                                    voided_receipt=journal.digest(path),
                                    voided_commit=commit,
                                    reason=args.reason))


def ticket_figures(repository):
    """Every delivered ticket's figures, derived from its journal.

    A ticket delivered before kpi.json existed is covered identically, because
    the journal is the source and the file is only a cache. A ticket with no
    journal at all, which SEEN-086 is by design, is listed from its ticket file
    rather than dropped.
    """
    from . import report as reporting
    figures = []
    for path in sorted((repository.root / 'docs' / 'tickets').glob('*.md')):
        header = reporting.frontmatter(path)
        identifier = reporting._field(header, 'id')
        if not identifier:
            continue
        status = reporting._field(header, 'status')
        points = reporting._field(header, 'estimate')
        folder = repository.root / HISTORY / identifier
        records = journal.read(folder) if folder.is_dir() else []
        has_receipt = any(record['kind'] == 'receipt' for record in records)
        if not has_receipt and status != 'done':
            continue
        delivered_at = None
        if not records:
            delivered_at = repository.git('log', '-1', '--format=%cI', '--', str(path)) or None
        measured = kpi.measure(records, identifier,
                               points=int(points) if points and points.isdigit() else None,
                               delivered_at=delivered_at)
        if records and measured['delivered_at']:
            measured['tokens'] = cost_module.tokens_between(
                repository.root, records[0]['timestamp'], measured['delivered_at'])
        if records and measured['delivered_at']:
            measured['tool_calls'] = cost_module.tool_calls_between(
                repository.root, records[0]['timestamp'], measured['delivered_at'])
            measured['started'] = records[0]['timestamp']
        measured['output_tokens'] = (measured.get('tokens') or {}).get('output_tokens')
        measured['escaped_defects'] = reporting.escaped_defects(repository.root, identifier)
        figures.append(measured)
    return figures


UNMEASURABLE = [
    'Eval pass rate for policy-gate action tickets: the eval set is SEEN-036 and no such ticket '
    'has been worked, so a figure here would be invented',
    'Escaped defects: counted from tickets whose frontmatter names an earlier one, and none has '
    'been written yet',
    'Cost in euros: the session logs carry tokens, and a price per token is stale the day it is '
    'written, so only tokens are reported',
]


def write_report(repository, args):
    from . import report as reporting
    require(args.week or args.sprint is not None, 'Ask for --week or --sprint <n>')
    rules = thresholds.load(repository.root)
    figures = ticket_figures(repository)
    if args.sprint is not None:
        planned = 0
        for path in sorted((repository.root / 'docs' / 'tickets').glob('*.md')):
            header = reporting.frontmatter(path)
            if reporting._field(header, 'sprint') == str(args.sprint):
                points = reporting._field(header, 'estimate')
                planned += int(points) if points and points.isdigit() else 0
        covered = [entry for entry in figures
                   if reporting._field(reporting.frontmatter(
                       next(iter(sorted((repository.root / 'docs' / 'tickets')
                                        .glob(f'{entry["ticket"]}-*.md')), ), ), ), 'sprint')
                   == str(args.sprint)]
        totals = reporting.totals(covered)
        totals['points_planned'] = planned
        name = f'sprint-{args.sprint}'
        title = f'Sprint {args.sprint}: {totals["points_delivered"]} of {planned} points delivered'
    else:
        when = args.date or repository.git('log', '-1', '--format=%cs')
        covered = reporting.within_week(figures, when)
        totals = reporting.totals(covered)
        year, week, _ = date.fromisoformat(when).isocalendar()
        name = f'{year}-W{week:02d}'
        title = f'Week {week} of {year}'
    budget = rules['context']
    baseline_path = repository.root / budget['baseline']
    section = None
    if baseline_path.is_file():
        section = context.compare(covered, json.loads(baseline_path.read_text()),
                                  budget['minimum_tickets'], budget['tools_available_from'])
        section['overlaps'] = context.overlaps(_graph_records(repository.root, covered))
    payload = dict(name=name, generated_for=name, tickets=covered, totals=totals,
                   unmeasurable=UNMEASURABLE, context=section)
    markdown = reporting.render(title, covered, totals, UNMEASURABLE, section, budget)
    written = reporting.write(repository.root, name, markdown, payload)
    return dict(written, tickets=len(covered), totals=totals)


def _graph_records(root, tickets):
    """Every graph note on the tickets a report covers."""
    found = []
    for entry in tickets:
        folder = root / HISTORY / entry['ticket']
        if not folder.is_dir():
            continue
        for record in journal.read(folder):
            if record['kind'] == 'note' and 'source' in record['data']:
                found.append(record)
    return found


def list_tickets(repository):
    history = repository.root / HISTORY
    tickets = []
    if history.is_dir():
        for folder in sorted(path for path in history.iterdir() if path.is_dir()):
            try:
                records = journal.read(folder)
            except HarnessError as error:
                # One damaged journal must not hide every other ticket.
                tickets.append(dict(ticket=folder.name, stage='unreadable', problem=str(error)))
                continue
            if records:
                current = journal.state(records)
                tickets.append(dict(ticket=folder.name, stage=current['stage'],
                                    attempt=current['attempt'], records=current['records'],
                                    updated=records[-1]['timestamp']))
    return dict(tickets=tickets)


def execute(args):
    repository = Repository(args.root)
    repository.require_is_root()
    rules = thresholds.load(repository.root)
    if args.command == 'doctor':
        result = doctor.report(repository, rules)
        require(result['ok'],
                'The harness self-check found problems:\n  ' + '\n  '.join(result['problems']))
        return result
    if args.command == 'sync':
        from . import agents, skills
        written = skills.sync(repository.root)
        # One command for every generated copy: a session that has to remember a
        # second one is a session that will read a stale agent.
        return dict(written, written=written['written'] + agents.sync(repository.root))
    if args.command == 'report':
        return write_report(repository, args)
    if args.command == 'lint':
        from . import secrets
        found = secrets.marketplace_hosts(repository.root)
        require(not found,
                'Live marketplace hosts in test code:\n  '
                + '\n  '.join(f'{entry["path"]}:{entry["line"]} {entry["host"]}'
                               for entry in found)
                + '\nConnector tests run against recorded fixtures. If a line names a host on '
                  'purpose, mark it with ' + secrets.ALLOW_MARKER)
        return dict(ok=True, checked='test code', hosts=list(secrets.MARKETPLACE_HOSTS))
    if args.command == 'list':
        return list_tickets(repository)

    require_ticket_id(args.ticket, rules)
    if args.command in WRITING_COMMANDS:
        require_actor(args.actor, rules)
        require_branch(repository, args.ticket)

    folder = journal_folder(repository, args.ticket)
    path = lock(repository.root) if args.command in WRITING_COMMANDS else None
    try:
        records = journal.read(folder)
        if args.command == 'start':
            return start(repository, folder, records, args, rules)
        if args.command == 'history':
            return [record for record in records if not args.kind or record['kind'] == args.kind]
        if args.command == 'budget':
            return budget(repository, args.ticket, rules)
        if args.command == 'status':
            if getattr(args, 'brief', False):
                return brief(repository, args.ticket, records, journal.state(records), rules)
            return describe(repository, args.ticket, records, folder)
        if args.command == 'draft':
            return draft(repository, records, args)

        if args.command == 'discard':
            return discard_journal(repository, folder, records, args, rules)
        if args.command == 'verify-merge':
            from . import delivery
            return delivery.verify_merge(repository, folder, records)

        current = journal.state(records)
        if args.command == 'reopen':
            return reopen(repository, folder, records, args, current)
        if args.command == 'verify-delivery':
            from . import delivery
            return delivery.verify(repository, folder, records, args, current)
        require(current['stage'] in WORKING_STAGES,
                f'{args.ticket} is {current["stage"]}; open a follow-up ticket for further work')
        handlers = dict(note=note, check=check, advance=advance, graph=graph, decide=decide,
                        coverage=coverage, handoff=handoff)
        handlers['return'] = go_back
        return handlers[args.command](repository, folder, records, args, current, rules)
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def main(argv=None):
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
        result = execute(args)
    except (HarnessError, OSError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as error:
        print(f'Harness: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == 'check' and result['data']['exit_code'] != 0:
        return 1
    return 0
