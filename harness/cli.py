"""The commands a session runs, and the order they may be run in.

Two families: ticket commands that read and extend one journal, and repository
commands that look after the harness itself. Ticket text and check output are
data the harness passes through files; nothing here interpolates them into a
shell.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from . import checks, doctor, gates, journal, thresholds
from .errors import HarnessError, require
from .paths import (DRAFTS, HISTORY, KINDS, LOCK, NON_CODE_TEMPLATE, STAGES, TEMPLATES,
                    TEMPLATE_FOR_STAGE, WORKING_STAGES)
from .repository import Repository

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TICKET_COMMANDS = ('start', 'status', 'history', 'draft', 'note', 'check', 'advance',
                   'return', 'verify-delivery')
WRITING_COMMANDS = ('start', 'note', 'check', 'advance', 'return', 'verify-delivery')
BRANCH = re.compile(r'^(claude|codex)/(?P<ticket>[A-Z]+-\d+)-')

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

    ticket_command('status', 'Report the stage, the branch and the next command')
    history = ticket_command('history', 'Print the verified journal')
    history.add_argument('--kind', choices=KINDS, help='Show only records of one kind')

    draft = ticket_command('draft', 'Copy the current stage template into .harness-drafts')
    draft.add_argument('--stage', choices=list(TEMPLATE_FOR_STAGE), help='Override the stage')
    draft.add_argument('--non-code', action='store_true',
                       help='Take the non-code path at the TDD stage')

    note = ticket_command('note', 'Record a decision, a question or a handoff')
    note.add_argument('--file', required=True, help='Markdown file holding the note')
    note.add_argument('--actor', required=True)

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

    deliver = ticket_command('verify-delivery', 'Confirm the delivery and write the receipt')
    deliver.add_argument('--file', required=True, help='Completed deliver evidence JSON')
    deliver.add_argument('--actor', required=True)

    commands.add_parser('doctor', help='Check the harness files, the journals and the links')
    commands.add_parser('list', help='List every ticket with a journal and where it stands')
    return parser


def parse(argv):
    parser = build_parser()
    known, extra = parser.parse_known_args(argv)
    if known.command == 'check':
        require(extra and extra[0] == '--', 'Put the check command after --')
        known.argv = extra[1:]
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
    shutil.copyfile(source, target)
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


def note(repository, folder, records, args, current):
    text = repository.file_inside(args.file).read_text()
    require(text.strip(), 'A note must not be empty')
    return journal.append(folder, records, kind='note', stage=current['stage'],
                          attempt=current['attempt'], actor=args.actor, head=repository.head(),
                          ticket=args.ticket, data=dict(text=text))


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
    return journal.append(folder, records, kind='check', stage=stage, attempt=current['attempt'],
                          actor=args.actor, head=repository.head(), ticket=args.ticket,
                          data=evidence)


def read_evidence(repository, relative):
    try:
        return json.loads(repository.file_inside(relative).read_text())
    except json.JSONDecodeError as error:
        raise HarnessError(f'Stage evidence is not valid JSON: {error}')


def advance(repository, folder, records, args, current, rules):
    stage = current['stage']
    data = read_evidence(repository, args.file)
    data.update(gates.evaluate(stage, data, records, current, repository, rules))
    next_stage = STAGES[STAGES.index(stage) + 1]
    record = journal.append(folder, records, kind='advance', stage=stage,
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket,
                            data=dict(from_stage=stage, to_stage=next_stage, evidence=data,
                                      decisions=[]))
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
        if args.command == 'status':
            return describe(repository, args.ticket, records, folder)
        if args.command == 'draft':
            return draft(repository, records, args)

        current = journal.state(records)
        if args.command == 'verify-delivery':
            from . import delivery
            return delivery.verify(repository, folder, records, args, current)
        require(current['stage'] in WORKING_STAGES,
                f'{args.ticket} is {current["stage"]}; open a follow-up ticket for further work')
        handlers = dict(note=note, check=check, advance=advance)
        handlers['return'] = go_back
        handler = handlers[args.command]
        if handler is note:
            return note(repository, folder, records, args, current)
        return handler(repository, folder, records, args, current, rules)
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
