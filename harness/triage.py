"""The review triage: three passes, cheapest first.

The review is the most expensive read in the procedure, because a model holds the
whole diff, the journal and the criteria at once. So the model is given last what
the cheaper passes could not settle.

Pass one runs no model at all. It is the checks the harness already has and the
ones the journal makes possible, each answering pass, fail or unavailable. A
failure does not refuse the triage: most of these can be unavailable for a reason
about the machine rather than about the work, so a failure forces full depth and
is carried in the record where the reviewer will read it.

Pass two is one Jev request over the journal and the diff excerpts. Jev cannot run
a test and cannot read the repository, so every answer it gives is only as good as
the state this module puts in front of it, which is why pass one comes first and
why the state is what the journal already holds rather than the tree.

Pass three is not run here. The harness runs no model: the record carries the task
text naming exactly the focus set, and the session hands that to its subagent.

Three things are rules and never Jev's to answer, and they live in gates.py beside
the predicate that already reads two of them: an agent action, billing or the
policy gate, and a migration. Any of them is full depth with no request made.
"""

import re

from . import gates, journal, kpi, risk, secrets
from .errors import HarnessError, require
from .paths import FINGERPRINT_EXCLUDED

# Pass one, in the order a reader wants them: what the tests said, what the tree
# says, what the journal says, and what is outside the repository.
DETERMINISTIC = ('coverage', 'lint', 'gitleaks', 'fingerprint', 'slice_files',
                 'red_before_green', 'tests_added', 'acceptance_entries', 'pull_request')

PASS, FAIL, UNAVAILABLE = 'pass', 'fail', 'unavailable'

# A path that is a test, by the two conventions this repository uses: Python
# tests under harness/tests/ and TypeScript tests beside the code they cover.
TEST_PATH = re.compile(r'(^|/)(tests?|__tests__)/|\.(test|spec)\.[jt]sx?$|(^|/)test_[^/]+\.py$')
# A criterion in a ticket file: a task-list item under ## Acceptance criteria.
CRITERION = re.compile(r'^\s*-\s*\[[ xX]\]\s*(?P<text>.+?)\s*$')
# `diff --git a/<path> b/<path>`, whose second half survives a rename.
DIFF_HEADER = re.compile(r'^diff --git a/(?P<old>.+?) b/(?P<new>.+)$')
GITLEAKS_FOUND = 1


def _entry(name, outcome, detail):
    return dict(name=name, outcome=outcome, detail=detail)


def changed_files(repository):
    """Every file this branch changes, committed or not, minus what is not the work.

    Both halves are needed. A branch several commits in has its work in the
    commits, and a session mid-slice has it in the working tree; a triage that
    read only one of them would hand the reviewer half a diff.
    """
    base = repository.default_branch()
    committed = []
    try:
        committed = repository.git('diff', '--name-only', f'{base}...HEAD').split()
    except HarnessError:
        # A branch with no merge base, which is every fresh test project and any
        # repository whose default branch is not fetched. The working tree still
        # answers, and the pending half below is what it answers with.
        pass
    pending = risk.changed_files(repository.root)
    return sorted({path for path in set(committed) | set(pending)
                   if not path.startswith(FINGERPRINT_EXCLUDED)})


def _numstat(repository, *arguments):
    """Lines added and removed per path, as git counts them."""
    counted = {}
    try:
        output = repository.git('diff', '--numstat', *arguments)
    except HarnessError:
        return counted
    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) != 3:
            continue
        added, removed, path = parts
        # A binary file is reported as two dashes, and counts as neither.
        current = counted.setdefault(path, dict(added=0, removed=0))
        current['added'] += int(added) if added.isdigit() else 0
        current['removed'] += int(removed) if removed.isdigit() else 0
    return counted


def _hunks(repository, *arguments):
    """Hunks per path, counted from one diff rather than one diff per file."""
    counted, path = {}, None
    try:
        output = repository.git('diff', *arguments)
    except HarnessError:
        return counted
    for line in output.splitlines():
        header = DIFF_HEADER.match(line)
        if header:
            path = header.group('new')
            counted.setdefault(path, 0)
        elif path and line.startswith('@@'):
            counted[path] += 1
    return counted


def package_of(path):
    """Which package a path belongs to, by this repository's own layout.

    packages/<name> and apps/<name> are the workspaces; everything else is named
    by its first segment, so harness/triage.py is `harness` and a file at the root
    is `root`. A guess would be worse than a rule: the reviewer_must_read question
    is given this to tell a change in core from a change in the web app.
    """
    parts = path.split('/')
    if len(parts) > 2 and parts[0] in ('packages', 'apps'):
        return f'{parts[0]}/{parts[1]}'
    return parts[0] if len(parts) > 1 else 'root'


def solution_paths(solution):
    """Every path the solution record named, from the slices and from changes.

    A changes entry is "path: what changes in it", so the path is what stands
    before the first colon. A slice names its files outright.
    """
    named = set()
    for entry in solution.get('slices') or []:
        named.update(str(path) for path in (entry.get('files') or []))
    for entry in solution.get('changes') or []:
        named.add(str(entry).partition(':')[0].strip())
    return {path for path in named if path}


def ticket_criteria(text):
    """The acceptance criteria a ticket file lists, in order."""
    found, inside = [], False
    for line in text.splitlines():
        if line.startswith('## '):
            inside = line.strip().lower().startswith('## acceptance criteria')
            continue
        if not inside:
            continue
        match = CRITERION.match(line)
        if match:
            found.append(match.group('text'))
    return found


def _latest_check(records, attempt, phases):
    for record in reversed(records):
        if (record['kind'] == 'check' and record['stage'] == 'tdd'
                and record['attempt'] == attempt
                and record['data'].get('phase') in phases):
            return record
    return None


def _coverage_check(records, attempt):
    record = _latest_check(records, attempt, ('coverage',))
    if record is None:
        return _entry('coverage', UNAVAILABLE,
                      'No coverage measurement in this attempt, which is every non-code ticket')
    delta = record['data'].get('delta')
    if delta is None:
        return _entry('coverage', PASS,
                      f'{record["data"].get("package")} at {record["data"].get("lines")}%, '
                      'the first measurement, so there is no baseline it could have fallen from')
    if delta < 0:
        return _entry('coverage', FAIL,
                      f'{record["data"].get("package")} fell by {delta} to '
                      f'{record["data"].get("lines")}%')
    return _entry('coverage', PASS,
                  f'{record["data"].get("package")} at {record["data"].get("lines")}%, '
                  f'{delta:+} against the baseline')


def _lint_check(root):
    found = secrets.marketplace_hosts(root)
    if found:
        return _entry('lint', FAIL,
                      'Live marketplace hosts in test code: '
                      + ', '.join(f'{entry["path"]}:{entry["line"]}' for entry in found[:5]))
    return _entry('lint', PASS, 'No live marketplace host in test code')


def _gitleaks_check(repository):
    """The same scan the pre-commit hook runs, over this branch's commits.

    An exit of 1 is gitleaks saying it found something. Any other non-zero is
    gitleaks failing to run, which says nothing about the work and is recorded as
    an absence rather than as a leak.
    """
    base = repository.default_branch()
    import subprocess
    try:
        completed = subprocess.run(
            ['gitleaks', 'detect', '--redact', '--no-banner', f'--log-opts={base}..HEAD'],
            cwd=repository.root, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return _entry('gitleaks', UNAVAILABLE,
                      'gitleaks is not on PATH; brew install gitleaks, or review from a '
                      'machine that has it. CI runs it again on the checkout')
    except subprocess.TimeoutExpired:
        return _entry('gitleaks', UNAVAILABLE, 'gitleaks did not finish within 300s')
    if completed.returncode == 0:
        return _entry('gitleaks', PASS, f'No leak in {base}..HEAD')
    if completed.returncode == GITLEAKS_FOUND:
        return _entry('gitleaks', FAIL,
                      'gitleaks found something in this branch; its own output names it, and '
                      'it is redacted here on purpose')
    return _entry('gitleaks', UNAVAILABLE,
                  f'gitleaks exited {completed.returncode}: '
                  f'{(completed.stderr or completed.stdout).strip().splitlines()[-1:] or ["no reason given"]}'
                  .strip("[]'"))


def _fingerprint_check(repository, records, attempt, now):
    """Whether the tree is still the one the tests last ran against.

    The coverage measurement is excluded: it is written straight into the journal
    by some fixtures and its fingerprints are not a claim about the tree.
    """
    record = _latest_check(records, attempt, ('red', 'green', 'regression'))
    if record is None:
        return _entry('fingerprint', UNAVAILABLE,
                      'No test run in this attempt to compare the tree against')
    after = record['data'].get('after')
    if after == now:
        return _entry('fingerprint', PASS,
                      f'The tree is the one check {record["sequence"]} ran against')
    return _entry('fingerprint', FAIL,
                  f'The tree changed after check {record["sequence"]}: it ran against '
                  f'{str(after)[:12]} and this triage reads {now[:12]}. The tests that passed '
                  'are not the tests for this tree')


def _slice_files_check(files, named):
    outside = sorted(path for path in files if path not in named)
    if not outside:
        return _entry('slice_files', PASS,
                      f'All {len(files)} changed files are named by the accepted slice plan')
    return _entry('slice_files', FAIL,
                  'Changed but named by no slice and no changes entry: '
                  + ', '.join(outside))


def _red_check(records):
    answer = kpi.red_before_green(records)
    if answer is None:
        return _entry('red_before_green', UNAVAILABLE,
                      'No accepted tdd record carries slices, which is every non-code ticket')
    if answer:
        return _entry('red_before_green', PASS,
                      'Every slice cites a RED that failed rather than a command that passed')
    return _entry('red_before_green', FAIL,
                  'A slice cites a RED that did not fail, so nothing proves the test could tell '
                  'the behaviour was absent')


def _tests_check(files):
    tests = sorted(path for path in files if TEST_PATH.search(path))
    if tests:
        return _entry('tests_added', PASS, 'Tests changed: ' + ', '.join(tests[:5]))
    return _entry('tests_added', FAIL,
                  'No test file is in this change, so nothing new is guarded by a test')


def _acceptance_check(records, criteria):
    clarified = gates.latest_evidence(records, 'clarify') or {}
    restated = clarified.get('acceptance') or []
    if not criteria:
        return _entry('acceptance_entries', UNAVAILABLE,
                      'The ticket file lists no acceptance criteria to count against')
    if len(restated) >= len(criteria):
        return _entry('acceptance_entries', PASS,
                      f'The clarify record restates {len(restated)} checks against '
                      f'{len(criteria)} criteria in the ticket')
    return _entry('acceptance_entries', FAIL,
                  f'The clarify record restates {len(restated)} checks against '
                  f'{len(criteria)} criteria in the ticket, so at least one criterion was '
                  'never turned into a check')


def _pull_request_check(repository, ticket):
    """Whether a pull request exists yet and names the ticket.

    Asked only when the repository has a remote, so a checkout with none never
    shells out to gh. The pull request is usually opened at deliver, so no pull
    request at review is an absence rather than a failure.
    """
    from . import github
    try:
        if not repository.git('remote').split():
            return _entry('pull_request', UNAVAILABLE,
                          'This checkout has no remote, so there is no pull request to read')
        request = github.pull_request(repository)
    except (HarnessError, OSError):
        return _entry('pull_request', UNAVAILABLE,
                      'gh could not answer, so the pull request body was not read. It is '
                      'checked again at merge, where the receipt hash has to be in it')
    body = request.get('body') or ''
    if ticket in body:
        return _entry('pull_request', PASS,
                      f'Pull request {request.get("number")} names {ticket} in its body')
    return _entry('pull_request', FAIL,
                  f'Pull request {request.get("number")} does not name {ticket} in its body, '
                  'so nobody reading it can tell which ticket it delivers')


def deterministic(repository, records, current, files, named, criteria, ticket, fingerprint):
    """Pass one, in the order DETERMINISTIC lists it."""
    attempt = current['attempt']
    return [_coverage_check(records, attempt),
            _lint_check(repository.root),
            _gitleaks_check(repository),
            _fingerprint_check(repository, records, attempt, fingerprint),
            _slice_files_check(files, named),
            _red_check(records),
            _tests_check(files),
            _acceptance_check(records, criteria),
            _pull_request_check(repository, ticket)]


def failed(results):
    return [check for check in results if check['outcome'] == FAIL]


def file_facts(repository, files, named, records, attempt):
    """One entry per changed file: what the reviewer_must_read question is given.

    The change-risk percentile and the coverage delta are figures about the change
    as a whole rather than about one file, and they are carried on every entry
    rather than put somewhere else in the state, because the question is asked per
    file and a question should carry what it is answered from.
    """
    base = repository.default_branch()
    counts = _numstat(repository, f'{base}...HEAD')
    for path, entry in _numstat(repository, 'HEAD').items():
        current = counts.setdefault(path, dict(added=0, removed=0))
        current['added'] += entry['added']
        current['removed'] += entry['removed']
    hunks = _hunks(repository, f'{base}...HEAD')
    for path, count in _hunks(repository, 'HEAD').items():
        hunks[path] = hunks.get(path, 0) + count

    scored = risk.assess(repository.root)
    coverage = _latest_check(records, attempt, ('coverage',))
    delta = coverage['data'].get('delta') if coverage else None

    facts = []
    for path in files:
        counted = counts.get(path)
        if counted is None:
            # Untracked: git counts nothing for a file it has never seen, and the
            # whole file is what the reviewer would read.
            full = repository.root / path
            lines = len(full.read_text(errors='replace').splitlines()) if full.is_file() else 0
            counted, hunk_count = dict(added=lines, removed=0), 1
        else:
            hunk_count = hunks.get(path, 1)
        facts.append(dict(path=path,
                          hunks=hunk_count,
                          added=counted['added'],
                          removed=counted['removed'],
                          package=package_of(path),
                          risk_percentile=scored.get('percentile'),
                          coverage_delta=delta,
                          named_in_solution=path in named))
    return facts


def run(repository, records, current, rules, ticket):
    """The whole triage, as the data a `triage` record carries.

    Pass two is added by the next slice. Until then every triage is full depth,
    which is the safe half of the trade: the reviewer reads what it reads today.
    """
    require(current['stage'] == 'review',
            f'A triage is run at the review stage; this ticket is at {current["stage"]}. '
            'The triage decides what the reviewer reads, so it comes after the tdd gate '
            'and before the reviewer is spawned')
    solution = gates.latest_evidence(records, 'solution') or {}
    fingerprint = repository.fingerprint()
    files = changed_files(repository)
    named = solution_paths(solution)
    criteria = ticket_criteria(_ticket_text(repository, records))
    results = deterministic(repository, records, current, files, named, criteria, ticket,
                            fingerprint)
    tripped = gates.full_depth_rules(records, repository.root, solution)
    reasons = [gates.FULL_DEPTH_RULES[name] for name in tripped]
    reasons += [f'{check["name"]} did not pass, so the reviewer reads everything: '
                f'{check["detail"]}' for check in failed(results)]
    return dict(fingerprint=fingerprint,
                files=file_facts(repository, files, named, records, current['attempt']),
                criteria=criteria,
                deterministic=results,
                rules=reasons,
                jev=dict(asked=False,
                         reason='Full depth is already settled, so nothing is put to the model'
                                if reasons else 'Pass two is not built yet',
                         answers=[]),
                review_depth='full',
                focus=list(files),
                shadow=bool(rules['review']['triage_shadow']),
                would_exclude=[],
                excluded_share=0.0)


def _ticket_text(repository, records):
    """The ticket as it stands, by the same rule every other reader uses."""
    from .cli import _ticket_text as read
    text, _ = read(records[0]['data'], records[0]['data'].get('ticket_id', records[0]['ticket']),
                   repository.root)
    return text


def append(repository, folder, records, current, args, rules):
    """Run the triage and keep it, as a record of its own at the review stage."""
    data = run(repository, records, current, rules, args.ticket)
    return journal.append(folder, records, kind='triage', stage='review',
                          attempt=current['attempt'], actor=args.actor,
                          head=repository.head(), ticket=args.ticket, data=data)
