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


class GuardRefusal(HarnessError):
    """A refusal from the edit guard, which blocks in both assistants.

    A distinct exception rather than the plain HarnessError every other
    command raises, because argparse itself exits 2 on an unknown command:
    if a guard refusal also mapped to exit 1, main could not tell the two
    apart, and a hook watching for exit 2 would treat every other harness
    refusal as a block too. HarnessError still covers it for `require` and
    for any caller that only wants to know something failed.
    """


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TICKET_COMMANDS = ('start', 'status', 'history', 'draft', 'note', 'check', 'advance',
                   'return', 'graph', 'decide', 'coverage', 'handoff', 'budget', 'reopen',
                   'discard', 'verify-delivery', 'verify-merge', 'review')
# handoff writes a record, so it is bound to the ticket's own branch like every
# other writing command. status --brief is not here and neither is budget: a
# command a session runs to see where it stands must not make the journal longer
# every time it is run.
WRITING_COMMANDS = ('start', 'note', 'check', 'advance', 'return', 'graph', 'decide', 'coverage',
                    'handoff', 'reopen', 'review', 'route',
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
    check.add_argument('--model', dest='declared',
                       help='The tier this runner was spawned on, when it is a subagent and '
                            'knows: a disclosure, recorded beside the model read from the log')
    check.add_argument('--agent', dest='agent_declared',
                       help='The agent this runner was spawned as, when it is a subagent and '
                            'knows: a disclosure, checked against [agents] names and not a '
                            'proof, because a Claude Code subagent inherits its parent\'s '
                            'session id and the log cannot say it either')
    check.add_argument('--timeout', type=int, help='Seconds before the command is stopped')
    check.add_argument('--quiet', action='store_true',
                       help='Return the exit code, the size counts and a tail of the output '
                            'instead of the whole transcript. The journal record is unchanged: '
                            'this only shapes what comes back to the caller, not what is written')

    advance = ticket_command('advance', 'Pass the current stage gate with completed evidence')
    advance.add_argument('--file', required=True, help='Completed stage evidence JSON')
    advance.add_argument('--actor', required=True)

    back = ticket_command('return', 'Send the ticket back to an earlier stage')
    back.add_argument('--to', required=True)
    back.add_argument('--reason', required=True)
    back.add_argument('--actor', required=True)
    back.add_argument('--findings', metavar='FILE',
                      help='JSON array of the findings this review returns the ticket on. A '
                           'review that returned a ticket is a review, and its findings are what '
                           'the calibration window reads: without them an escape counts only if '
                           'the round that finally passes repeats it')
    back.add_argument('--no-findings', action='store_true',
                      help='This return from review is not about a defect, so there is nothing '
                           'for the calibration window to read. One of --findings, --unmet or '
                           'this is required at the review stage, because an absence nobody '
                           'declared cannot be told from a flag somebody forgot')
    back.add_argument('--unmet', type=int, action='append', metavar='N',
                      help='The number of an acceptance criterion this return found unmet, '
                           'repeatable. A criterion the triage answered evidenced and a review '
                           'found unmet is an escape, and its number is the only thing that '
                           'tells such a return from an ordinary one')

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
    pack.add_argument('--auto', action='store_true',
                      help='The PreCompact path: write the pack and refuse nothing. A hook that '
                           'failed compaction would lose the context it was protecting, so what '
                           'would raise becomes a reason in the answer')

    ticket_command('budget', "This session's tokens and tool calls against the session budget")

    route = ticket_command('route', 'Decide which model and which effort implement each slice')
    route.add_argument('--actor', required=True)

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

    # Two words because the triage is one pass of the review rather than a stage of
    # its own, and because a later pass should be another action here rather than
    # another top-level verb.
    review = commands.add_parser('review', help='The review stage, cheapest pass first')
    actions = review.add_subparsers(dest='action', required=True)
    triage_action = actions.add_parser(
        'triage', help='Run the deterministic pass and one Jev request, and record what the '
                       'reviewer must read')
    triage_action.add_argument('ticket', help='Ticket identifier, for example SEEN-086')
    triage_action.add_argument('--actor', required=True)

    report = commands.add_parser('report', help='Aggregate delivered tickets into a report')
    report.add_argument('--week', action='store_true', help='The ISO week of --date, or today')
    report.add_argument('--sprint', type=int, help='Planned against delivered for one sprint')
    report.add_argument('--date', help='The date whose week to report, YYYY-MM-DD')
    report.add_argument('--calibration', action='store_true',
                        help='The evidence the review triage and the routes will be decided on, '
                             'per ticket and per slice, with the rule printed beside it')

    guard = commands.add_parser(
        'guard', help='Refuse an edit the stage or the accepted slice does not allow')
    guard.add_argument('path', help='The path about to be written, project-relative or absolute')

    from . import hooks as hook_module
    hook = commands.add_parser(
        'hook', help="Answer one lifecycle hook: its JSON on stdin, the client's envelope on "
                     'stdout')
    hook.add_argument('event', choices=sorted(hook_module.HANDLERS),
                      help='The event, as harness/hooks.json names it')
    hook.add_argument('--client', required=True, choices=sorted(hook_module.COPIES),
                      help='Which assistant sent the payload, because the envelope is its own')

    commands.add_parser('sync', help='Generate the skill copies from docs/harness/skill.md')
    commands.add_parser('lint', help='Refuse live marketplace hosts in test code')
    rule_set = commands.add_parser('rules',
                                   help='The rule set in front of the model: its registry, its '
                                        'citations and the fixture each rule is proven by')
    rule_set.add_argument('--check', action='store_true',
                          help='Cross-check rules/registry.toml against the tools\' own '
                               'configurations, in both directions, and refuse a rule with no '
                               'citation. The default when no flag is given')
    rule_set.add_argument('--fixtures', action='store_true',
                          help='Run each rule against the fixture it stands on and refuse one '
                               'that does not fire. Needs the workspace installed')
    check_self = commands.add_parser('doctor',
                                     help='Check the harness files, the journals and the links')
    check_self.add_argument('--quick', action='store_true',
                            help='The Stop path: the sections that read the journal and the '
                                 'generated copies, and none that reads every tracked file')
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
    secret = (f'This pack carries the value of {", ".join(carried)} from the environment. A pack '
              'is read by the next session and by people; credentials do not go in one'
              if carried else None)
    oversize = (f'This pack is about {built["estimated_tokens"]} tokens against a limit of '
                f'{built["token_limit"]}. The pack is built from bounded sections, so a pack over '
                'the limit is a bug in harness/handoff.py rather than a journal to shorten'
                if built['estimated_tokens'] > built['token_limit'] else None)
    # --auto refuses nothing, because it is the compaction path: a hook that
    # failed compaction would lose the context it exists to protect. Every
    # refusal below becomes the reason in the answer instead, which a person
    # reads as a systemMessage rather than as a compaction that did not happen.
    if getattr(args, 'auto', False):
        declined = handoff_module.hands_over_nothing(built) or secret or oversize
        if declined:
            return dict(ticket=args.ticket, written=False, reason=declined)
    require(not carried, secret)
    require(not oversize, oversize)
    path = pack_path(repository, args.ticket)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit, because the bytes on disk are compared against the hash this
    # record carries, and a ticket title is not guaranteed to be ASCII.
    path.write_text(text, encoding='utf-8')
    record = journal.append(folder, records, kind='handoff', stage=current['stage'],
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket,
                            data=dict(pack=str(path.relative_to(repository.root)),
                                      sha256=handoff_module.digest(text),
                                      estimated_tokens=built['estimated_tokens'],
                                      token_limit=built['token_limit'],
                                      slice=built['slice'],
                                      # Which hand wrote it: a pack written by a
                                      # compaction is not a session declaring a
                                      # boundary, and a later reader has to be
                                      # able to tell one from the other.
                                      auto=getattr(args, 'auto', False),
                                      figures=sessions.figures(repository.root)))
    if getattr(args, 'auto', False):
        return dict(ticket=args.ticket, written=True,
                    pack=str(path.relative_to(repository.root)), record=record['sequence'])
    return record


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
    subagents = sessions.subagent_figures(repository.root)
    return dict(ticket=ticket,
               **sessions.against_budget(spent, limits['output_token_budget'],
                                         subagents=subagents))


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
    content.update(extra_review_fields(records, stage, repository.root))
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


def ticket_file(first, ticket_id, root):
    """The ticket file as it stands now: the recorded path, or found by its id.

    A filename carries a title, so renaming a ticket is ordinary. SEEN-096 was
    split three ways and its file was renamed mid-ticket, which is why SEEN-101
    exists. The path in record 1 is the one the ticket was started with; the id is
    what stays true. Public because the review triage needs the same answer, and a
    second copy of this resolution is a second answer waiting to disagree: J3 of
    SEEN-107's fifth review found it reading record 1 directly and excluding a path
    that was no longer there.

    Returns the project-relative path and how it was found, or None when nothing
    on disk matches.
    """
    recorded = first.get('ticket_file')
    if root is None:
        return recorded, 'recorded path'
    if recorded and (root / recorded).is_file():
        return recorded, 'recorded path'
    matches = sorted((root / TICKETS).glob(f'{ticket_id}-*.md'))
    require(len(matches) < 2,
            f'{ticket_id} matches more than one ticket file, so the harness cannot tell which '
            'one it is judging against: '
            + ', '.join(str(match.relative_to(root)) for match in matches))
    if matches:
        return str(matches[0].relative_to(root)), 'found by id'
    return recorded, None


def _ticket_text(first, ticket_id, root):
    """The ticket and where it came from: the path, the id, or the snapshot.

    Which source was used is returned rather than hidden, because a judgement
    against a snapshot of a deleted ticket is weaker evidence than one against the
    ticket, and a journal should say which it was.
    """
    snapshot = first['ticket_snapshot']
    if root is None:
        return snapshot, 'snapshot in record 1'
    path, found = ticket_file(first, ticket_id, root)
    if found is None:
        return snapshot, 'snapshot in record 1'
    return (root / path).read_text(), found


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


def extra_review_fields(records, stage, root=None):
    """What a review must answer beyond the template, asked of the gate itself.

    A change that touches billing or changes an agent action is reviewed twice and
    against the security checklist, so the draft asks for both rather than leaving
    a reviewer to remember. H3 of SEEN-105's third review: this used to carry its
    own copy of the gate's reasoning and the two had already drifted apart, so the
    harness wrote a draft the gate it ships with would refuse.
    """
    if stage != 'review' or not gates.needs_two_reviewers(records, root):
        return {}
    return {'second_reviewer': 'The second reviewer, tool:role, from the other assistant. '
                               'Required because this change touches billing or an agent action.',
            'security_checklist': [
                'No secret in the diff',
                'No new dependency without a lockfile entry and an audit',
                'No live marketplace call in a test',
                'No PII field without its expiry job',
                'No tool without a policy-gate declaration']}


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
    declared = getattr(args, 'declared', None)
    if declared is not None:
        tiers = rules['routing']['tiers']
        require(declared in tiers,
                f'{declared!r} is not one of {", ".join(tiers)}. A declared model is a tier from '
                '[routing] tiers, which is what a route carries and what the gate compares')
    agent_declared = getattr(args, 'agent_declared', None)
    if agent_declared is not None:
        roster = rules['agents']['names']
        require(agent_declared in roster,
                f'{agent_declared!r} is not one of the agents this repository generates: '
                f'{", ".join(roster)}. A declared agent is a name from [agents] names, which '
                'is what a check can honestly claim and nothing more')
    evidence = checks.run(repository, args.argv, phase, timeout, limits['output_limit_bytes'],
                          declared=declared, agent=agent_declared)
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
    if getattr(args, 'quiet', False):
        return _quiet_payload(record, limits['quiet_tail_lines'])
    return record


def _quiet_payload(record, tail_lines):
    """What `--quiet` hands back to the caller, in place of the whole transcript.

    The journal file is already written by the time this runs, over the record
    exactly as `journal.append` returned it, so the evidence on disk is byte for
    byte what it would have been without the flag. This builds a fresh dict for
    the caller instead: `record['data']` is never mutated in place, because a
    later reader of that same dict must still see what was recorded, and the
    caller only gets the exit code, the size counts and a tail of the output,
    for a regression whose passing transcript nobody needs back.
    """
    output = record['data']['output']
    lines = output.splitlines()
    data = {key: value for key, value in record['data'].items() if key != 'output'}
    data.update(output_omitted=True,
                output_lines=len(lines),
                output_bytes=len(output.encode()),
                output_tail='\n'.join(lines[-tail_lines:]))
    return {**record, 'data': data}


def route_slices(repository, folder, records, args, current, rules):
    """Decide which model and which effort implement each slice, and keep it.

    Named for what it does rather than for the command, because `route` is taken
    here by the parser's own variable and a handler that shadows it is a handler
    somebody will one day call by mistake.
    """
    from . import routing
    return routing.append(repository, folder, records, current, args, rules)


def review(repository, folder, records, args, current, rules):
    """One pass of the review stage. Today there is one: the triage."""
    from . import triage
    actions = dict(triage=triage.append)
    require(args.action in actions,
            f'Unknown review action: {args.action!r}; the harness runs '
            f'{", ".join(sorted(actions))}')
    return actions[args.action](repository, folder, records, current, args, rules)


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
    body = dict(from_stage=stage, to_stage=next_stage, evidence=data, decisions=answers)
    if stage == 'tdd':
        # The last slice has no handoff after it, because a handoff is written
        # at a boundary and the plan ends here. Without a figure at this record
        # the final slice of every ticket carried no tokens, no cost and no
        # model, which is the window SEEN-109 compares routes on. F3 of this
        # ticket's second review.
        body['figures'] = sessions.figures(repository.root)
    record = journal.append(folder, records, kind='advance', stage=stage,
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket,
                            data=body)
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
    findings = []
    named = getattr(args, 'findings', None)
    if named:
        path = repository.root / named
        require(path.is_file(), f'No such findings file: {named}')
        try:
            findings = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            require(False, f'{named} is not readable JSON: {error}')
        require(isinstance(findings, list), f'{named} must hold a JSON array of findings')
        # The same shape the review gate demands, minus the resolution: a finding
        # that returned a ticket is open by definition, and it must still name
        # the file it is in when it is serious enough to be an escape.
        gates.check_findings(findings, rules['review']['severities'], resolved=False)
    unmet = sorted(set(getattr(args, 'unmet', None) or []))
    require(all(position >= 1 for position in unmet),
            'An unmet criterion is named by its number in the ticket, counting from 1')
    declared = bool(getattr(args, 'no_findings', False))
    require(stage != 'review' or findings or unmet or declared,
            'A return from review says what it found: --findings <file> for the findings it '
            'returns the ticket on, --unmet <n> for a criterion it found unmet, or --no-findings '
            'when it is neither. The calibration window reads a returning round like any other, '
            'and an absence nobody declared cannot be told from a flag somebody forgot')
    return journal.append(folder, records, kind='return', stage=stage,
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket,
                          data=dict(from_stage=stage, to_stage=args.to,
                                    to_attempt=current['attempt'] + 1, reason=args.reason,
                                    findings=findings,
                                    # Declared rather than inferred, for the
                                    # reason the requirement above gives.
                                    no_findings=declared,
                                    # Which criteria this return says are unmet, by their
                                    # number in the ticket. SEEN-109's second escape kind
                                    # is a criterion the triage answered evidenced and a
                                    # review found unmet, and prose cannot be read for it.
                                    unmet_criteria=unmet))


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


def ticket_figures(repository, rules=None):
    """Every delivered ticket's figures, derived from its journal.

    A ticket delivered before kpi.json existed is covered identically, because
    the journal is the source and the file is only a cache. A ticket with no
    journal at all, which SEEN-086 is by design, is listed from its ticket file
    rather than dropped.
    """
    from . import report as reporting
    rules = thresholds.load(repository.root) if rules is None else rules
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
                               delivered_at=delivered_at,
                               # The price table and the tier names, so the cost
                               # per slice is read from a diff a person reviews
                               # rather than from a constant in code.
                               rules=rules,
                               # The same call delivery makes, so the report and
                               # the delivered file cannot disagree about it.
                               reviewer_tokens=kpi.reviewer_tokens(repository.root, records))
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
    'Cost in euros beyond output tokens: a handoff record carries the session\'s output tokens '
    'and tool calls and nothing about input, so the cost per slice in [routing.prices] covers '
    'the output side and says so, with the date the prices were read printed beside it',
]


def write_report(repository, args):
    from . import calibration as calibrating, report as reporting
    require(args.week or args.sprint is not None or args.calibration,
            'Ask for --week, --sprint <n> or --calibration')
    rules = thresholds.load(repository.root)
    if args.calibration:
        section = calibrating.evidence(repository.root, rules)
        markdown = reporting.render_calibration(section, rules)
        written = reporting.write(repository.root, 'calibration', markdown, section)
        return dict(written, tickets=len(section['tickets']),
                    triage=section['triage']['state'], routes=section['routes']['state'])
    figures = ticket_figures(repository, rules)
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
                                  budget['minimum_tickets'], budget['tools_available_from'],
                                  agents_from=budget['agents_available_from'])
        section['overlaps'] = context.overlaps(_graph_records(repository.root, covered))
        # What a point cost on each model, from the routes the slices were given.
        # Beside the tokens per point rather than instead of it: the tokens are
        # the measure that does not go stale.
        section['cost_by_model'] = context.cost_by_model(covered)
        section['prices'] = rules['routing']['prices']
    # Which shadow the review triage is in, and what put it there. In a weekly
    # report rather than only in the calibration one, because an escape returns
    # the triage to shadow with nobody editing a file, and a change nobody made
    # is the one a reader most needs told.
    shadow = calibrating.effective_shadow(repository.root, rules)
    payload = dict(name=name, generated_for=name, tickets=covered, totals=totals,
                   unmeasurable=UNMEASURABLE, context=section, review_triage_shadow=shadow)
    markdown = reporting.render(title, covered, totals, UNMEASURABLE, section, budget, shadow)
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


def guard_command(repository, args, rules):
    """Whether `args.path` may be written now, from the current branch's own ticket.

    Neither writes a record nor takes an actor: it answers a question a hook
    asks before every edit, and a journal entry for every keystroke a session
    considers making would make the journal the thing that grows fastest.
    """
    from . import guard as guard_module
    branch = repository.branch_or_none()
    match = BRANCH.match(branch or '')
    records = journal.read(journal_folder(repository, match.group('ticket'))) if match else []
    decision = guard_module.decide(repository.root, records, branch, args.path, rules)
    if not decision['allowed']:
        raise GuardRefusal(decision['reason'])
    return decision


def hook_command(repository, args, rules):
    """One lifecycle hook answered: its payload on stdin, its envelope on stdout.

    Neither writes a record nor takes an actor, for the reason `guard` does not:
    it answers a question an assistant asks about a keystroke, and the one event
    that does write a record writes it through `handoff --auto`, which is bound
    to the branch like every other writing command.

    An empty or unreadable stdin is an empty payload rather than a failure. A
    person runs this by hand to see what a hook would say, and on PreToolUse a
    non-zero exit is how both assistants spell deny.
    """
    from . import hooks as hook_module
    raw = sys.stdin.read() if not sys.stdin.isatty() else ''
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as error:
        raise HarnessError(f'The {args.event} payload on stdin is not valid JSON: '
                           f'{error}') from error
    return hook_module.respond(repository, rules, args.event, payload, args.client)


def execute(args):
    repository = Repository(args.root)
    repository.require_is_root()
    rules = thresholds.load(repository.root)
    if args.command == 'doctor':
        result = doctor.report(repository, rules, quick=getattr(args, 'quick', False))
        require(result['ok'],
                'The harness self-check found problems:\n  ' + '\n  '.join(result['problems']))
        return result
    if args.command == 'sync':
        from . import agents, hooks, skills
        written = skills.sync(repository.root)
        # One command for every generated copy: a session that has to remember a
        # second one is a session that will read a stale agent, or run without
        # the hooks that enforce the procedure.
        return dict(written, written=(written['written'] + agents.sync(repository.root)
                                      + hooks.sync(repository.root)))
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
    if args.command == 'rules':
        from . import rules as rule_set
        # No flag means --check, because the question a session asks about the
        # rule set without saying which is whether it is traceable, and the
        # fixtures need the workspace installed where the check needs nothing.
        answer = rule_set.report(repository.root, fixtures=args.fixtures)
        # One refusal carrying both halves rather than two in sequence. A
        # registry problem would otherwise hide every unproven rule behind it,
        # and the two are fixed in the same sitting: the rule and its citation
        # are written together or neither is.
        trouble = []
        if answer['problems']:
            trouble.append('The rule set is not traceable:\n  '
                           + '\n  '.join(answer['problems']))
        if answer.get('unproven'):
            trouble.append('These rules did not refuse their own fixture, so nothing proves they '
                           'run:\n  '
                           + '\n  '.join(f'{result["id"]}: {result["detail"]}'
                                         for result in answer.get('fixtures', [])
                                         if not result['fired']))
        require(not trouble, '\n'.join(trouble))
        return answer
    if args.command == 'list':
        return list_tickets(repository)
    if args.command == 'guard':
        return guard_command(repository, args, rules)
    if args.command == 'hook':
        return hook_command(repository, args, rules)

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
                        coverage=coverage, handoff=handoff, review=review, route=route_slices)
        handlers['return'] = go_back
        return handlers[args.command](repository, folder, records, args, current, rules)
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def main(argv=None):
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
        result = execute(args)
    except GuardRefusal as error:
        # Its own path to exit 2, checked before the general HarnessError
        # below: argparse already exits 2 on a command it does not recognise,
        # which is the reason every guard test asserts the reason text and
        # not the code alone.
        print(f'Harness: {error}', file=sys.stderr)
        return 2
    except (HarnessError, OSError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as error:
        print(f'Harness: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == 'check' and result['data']['exit_code'] != 0:
        return 1
    return 0
