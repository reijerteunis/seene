"""The self-check a session runs before it starts working.

It reports problems rather than repairing them, because a silent repair hides
the drift a reviewer needs to see, and it reports all of them at once, because
fixing five problems one command at a time is five round trips. Local and
offline: nothing here waits on a network, so nobody has a reason to skip it.
"""

import json
import os
import re
import sys

from . import agents, journal, secrets, skills
from .errors import HarnessError
from .paths import (DRAFTS, HISTORY, LOCK, NON_CODE_TEMPLATE, TEMPLATES, TEMPLATE_FOR_STAGE,
                    THRESHOLDS)

PYTHON_FLOOR = (3, 12)

# The one ticket that is done with no journal, exempt by design and recorded in
# CLAUDE.md: the harness did not exist while it was being built.
BOOTSTRAP = 'SEEN-086'

# Statuses that may sit against a journal still in a working stage.
WORKING_STATUSES = ('doing', 'review', 'parked')
# Markdown links, excluding image embeds.
LINK = re.compile(r'(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
FENCE = re.compile(r'^\s*(```|~~~)')
EXTERNAL = ('http://', 'https://', 'mailto:', 'tel:', '//')


def python_problems(version):
    if tuple(version[:2]) < PYTHON_FLOOR:
        floor = '.'.join(str(part) for part in PYTHON_FLOOR)
        return [f'The harness needs Python {floor} or later, not '
                f'{".".join(str(part) for part in version[:3])}']
    return []


def template_problems(repository):
    problems = []
    for name in list(TEMPLATE_FOR_STAGE.values()) + [NON_CODE_TEMPLATE]:
        path = repository.root / TEMPLATES / name
        if not path.is_file():
            problems.append(f'Missing template: {TEMPLATES / name}')
            continue
        try:
            content = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            problems.append(f'{TEMPLATES / name} is not readable JSON: {error}')
            continue
        if not isinstance(content, dict) or not content:
            problems.append(f'{TEMPLATES / name} must be a JSON object with at least one field')
    return problems


def journal_problems(repository):
    """Journals whose chain, numbering or contents no longer verify."""
    problems = []
    history = repository.root / HISTORY
    if not history.is_dir():
        return problems
    for folder in sorted(path for path in history.iterdir() if path.is_dir()):
        try:
            journal.read(folder)
        except HarnessError as error:
            problems.append(f'{HISTORY / folder.name}: {error}')
    return problems


def rewritten_record_problems(repository):
    """Records git has seen change after the commit that created them.

    The chain makes a rewrite expensive; this makes it provable, because
    recomputing every later hash still leaves the modification in history.
    """
    return [f'{name} was committed as a modification or a deletion; a journal is append-only'
            for name in repository.rewritten_history_records()]


def status_problems(repository):
    """A ticket's frontmatter against the journal beside it.

    Four facts and no judgement: the status, the journal's last record, whether
    the receipt's commit is merged, and the bootstrap exemption. SEEN-006 and
    SEEN-089 sat at doing for hours after delivering and merging, because their
    mark-done commits were lost in a rebase and nothing compared the two.

    It reports and repairs nothing. A status corrected silently is a status
    nobody learns to keep right.
    """
    from . import report as reporting
    problems = []
    for path in sorted((repository.root / 'docs' / 'tickets').glob('*.md')):
        header = reporting.frontmatter(path)
        identifier = reporting._field(header, 'id')
        status = reporting._field(header, 'status')
        if not identifier or not status:
            continue
        folder = repository.root / HISTORY / identifier
        try:
            records = journal.read(folder) if folder.is_dir() else []
        except HarnessError:
            continue                      # the journal check already reports this
        if not records:
            if status == 'done' and identifier != BOOTSTRAP:
                problems.append(f'{identifier} says done but has no journal; only {BOOTSTRAP} is '
                                'exempt, as the bootstrap')
            continue
        state = journal.state(records)
        if state['stage'] != 'delivered':
            # The deliver stage is past the review gate, and the reviewed-tree
            # fingerprint covers the ticket file, so `review` has to be in the
            # tree before that advance exactly as the `## Outcome` section does.
            # Any working status passed here until SEEN-107, and the mismatch was
            # reported only once the receipt had moved the ticket to delivered, by
            # which point verify_merge will not let the ticket file change either:
            # a ticket could deliver and then be unable to merge, which is what
            # happened to SEEN-107 itself.
            wanted = ('review', 'done') if state['stage'] == 'deliver' else WORKING_STATUSES
            if status not in wanted:
                problems.append(f'{identifier} says {status} but its journal is at '
                                f'{state["stage"]}'
                                + ('; it has passed review, so the ticket file has to say '
                                   'review, and it has to say it before the review advance: what '
                                   'a receipt attests is the tree the review read, so writing it '
                                   'afterwards moves that tree and delivery refuses'
                                   if state['stage'] == 'deliver' else ''))
            continue
        receipt = records[-1]
        commit = receipt['data'].get('commit', '')
        if commit and repository.is_in_default_branch(commit):
            if status != 'done':
                problems.append(f'{identifier} says {status}, but its receipt attests '
                                f'{commit[:8]} which is merged; it is done')
        elif status not in ('review', 'done'):
            problems.append(f'{identifier} says {status} but it has delivered and is waiting to '
                            'merge; it is review')
    return problems


def skill_problems(repository):
    """The skill copies both assistants read, against the one file that makes them."""
    return skills.drift(repository.root)


def agent_problems(repository):
    """The agent copies both assistants read, against the sources that make them."""
    return agents.drift(repository.root)


def hook_problems(repository):
    """The pre-commit hook is the first place a credential is caught.

    It lives in .githooks, committed, because a control only one machine has is
    not a control. git has to be told to use it, and that setting is per clone.
    """
    hook = repository.root / '.githooks' / 'pre-commit'
    if not hook.is_file():
        return ['Missing .githooks/pre-commit, so nothing scans a commit for credentials']
    problems = []
    if not os.access(hook, os.X_OK):
        problems.append('.githooks/pre-commit is not executable, so git will skip it')
    try:
        configured = repository.git('config', '--get', 'core.hooksPath')
    except HarnessError:
        configured = ''
    if configured != '.githooks':
        problems.append('core.hooksPath is not .githooks, so the pre-commit hook does not run. '
                        'Run: git config core.hooksPath .githooks')
    return problems


def gitignore_problems(repository):
    path = repository.root / '.gitignore'
    if not path.is_file():
        return ['Missing .gitignore; drafts and the lock file would be committed']
    ignored = {line.strip().rstrip('/') for line in path.read_text().splitlines()}
    return [f'.gitignore does not ignore {name}'
            for name in (str(DRAFTS), str(LOCK)) if name.rstrip('/') not in ignored]


def link_problems(repository):
    """Relative markdown links that do not resolve.

    The docs are what this project mostly consists of, and a renamed ticket file
    silently breaks the entry point every session reads first.
    """
    problems = []
    for name in repository.tracked_and_untracked():
        if not name.endswith('.md'):
            continue
        path = repository.root / name
        if not path.is_file():
            continue
        fenced = False
        for number, line in enumerate(path.read_text(errors='replace').splitlines(), start=1):
            if FENCE.match(line):
                fenced = not fenced
                continue
            if fenced:
                continue
            for target in LINK.findall(line):
                if target.startswith('#') or target.startswith(EXTERNAL):
                    continue
                if not (path.parent / target.split('#')[0]).exists():
                    problems.append(f'{name}:{number} link does not resolve: {target}')
    return problems


def calibration_problems(repository, rules):
    """Whether the go-live on record names a decision a reader can open."""
    from . import calibration
    if (rules.get('review') or {}).get('triage_shadow', True):
        return []
    if not rules.get('calibration'):
        return []
    problem = calibration.went_live_problem(repository.root, rules)
    return [problem] if problem else []


def report(repository, rules):
    """Run every check and collect what is wrong."""
    sections = {
        'python': python_problems(sys.version_info),
        'thresholds': [] if (repository.root / THRESHOLDS).is_file() else [f'{THRESHOLDS} missing'],
        'templates': template_problems(repository),
        'journals': journal_problems(repository),
        'append_only': rewritten_record_problems(repository),
        'gitignore': gitignore_problems(repository),
        'hooks': hook_problems(repository),
        'skill': skill_problems(repository),
        'agents': agent_problems(repository),
        'ticket_status': status_problems(repository),
        'marketplace_hosts': [f'{entry["path"]}:{entry["line"]} names {entry["host"]}'
                              for entry in secrets.marketplace_hosts(repository.root)],
        'links': link_problems(repository),
        # A switch flipped with no decision named is an edit, not a decision.
        # Here rather than in front of every triage, because the harness's own
        # tests flip the threshold to exercise spot depth and a refusal there
        # would make the narrowing untestable: doctor is where the repository
        # is held to being in order. F3 of SEEN-109's second review.
        'calibration': calibration_problems(repository, rules),
    }
    problems = [problem for found in sections.values() for problem in found]
    return dict(ok=not problems, checked=list(sections), problems=problems)
