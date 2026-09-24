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

from . import gates, jev, journal, kpi, risk, secrets
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
# How much of a check's output goes into the state. The RED's own failure is the
# evidence criterion_evidenced is answered from, and its tail is where a runner
# puts it; the whole log would be the repository-wide read this ticket exists to
# avoid, paid for at the API instead of in the session.
EXCERPT_CHARACTERS = 800


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


def generated_paths():
    """Every file `sync` writes from a source, which a record names by its source.

    A generated copy has no review surface of its own: `doctor` refuses one that
    does not match what its source would generate, so naming the source is naming
    the copy. Counting them as unplanned is the mistake the ticket file already
    taught, one layer out, and it was found by running this triage on SEEN-107's
    own branch: the four copies were flagged while both their sources were named,
    which would have forced full depth on every harness ticket that runs sync.

    The Codex home copy is not here, because it lives outside the repository and
    can never be in a diff.
    """
    from . import agents, skills
    paths = {str(relative) for relative in skills.COMMITTED}
    for agent in agents.AGENTS:
        paths.add(str(agents.claude_copy(agent)))
        paths.add(str(agents.codex_copy(agent)))
    return paths


def procedure_paths(records):
    """Paths a solution record cannot plan and a comparison must not fire on.

    The ticket file, which the procedure writes: `status: doing` with the first
    commit, the `## Outcome` before review is left, the boxes ticked after the
    reviewer has read. And the copies `sync` generates, for the reason
    `generated_paths` gives. Neither is left out of the diff, only out of the
    slice check and out of the code fingerprint the review gate compares: they
    changed, and a reviewer can still be sent to them.
    """
    ticket = {records[0]['data'].get('ticket_file')} - {None} if records else set()
    return ticket | generated_paths()


def _slice_files_check(files, named, procedure):
    """Every changed file is one the solution record planned, bar what it cannot plan.

    The ticket file is excluded because the procedure writes it and no solution
    record plans it: `status: doing` goes in with the first commit and the
    `## Outcome` section before review is left. A check that failed on the harness's
    own writing would fail on every ticket and mean nothing. Generated copies are
    excluded for the reason `generated_paths` gives. Neither is excluded from the
    diff, only from this check: they changed, and the reviewer can still be sent
    to them.
    """
    procedure = set(procedure)
    outside = sorted(path for path in files if path not in named and path not in procedure)
    if not outside:
        return _entry('slice_files', PASS,
                      f'All {len(files)} changed files are named by the accepted slice plan, '
                      'or are the ticket file the procedure itself writes')
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
            _slice_files_check(files, named, procedure_paths(records)),
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


def criterion_key(position):
    return f'criterion_evidenced#{position}'


def file_key(path):
    return f'reviewer_must_read#{path}'


def _tail(text):
    text = text or ''
    return text if len(text) <= EXCERPT_CHARACTERS else '[...] ' + text[-EXCERPT_CHARACTERS:]


def _record_at(records, sequence):
    for record in records:
        if record['sequence'] == sequence:
            return record
    return None


def _check_excerpt(record):
    if record is None:
        return None
    return dict(record=record['sequence'],
                command=record['data'].get('command'),
                exit_code=record['data'].get('exit_code'),
                output=_tail(record['data'].get('output')))


def journal_excerpts(records):
    """What the journal already holds, bounded, as pass two's evidence.

    Excerpts rather than the tree, because Jev can neither run a test nor read a
    file: every answer it gives is only as good as the state put in front of it,
    and a summary of a tree it cannot see would be an impression rather than
    evidence. What is here is what was recorded: the criteria as checks, the
    decisions taken, and each slice's behaviour beside the RED that failed for it
    and the GREEN that followed.
    """
    clarified = gates.latest_evidence(records, 'clarify') or {}
    proved = gates.latest_evidence(records, 'tdd') or {}
    return dict(acceptance=clarified.get('acceptance') or [],
                decisions=clarified.get('decisions') or [],
                slices=[dict(behaviour=entry.get('behaviour'),
                             failure_reason=entry.get('failure_reason'),
                             red=_check_excerpt(_record_at(records, entry.get('red'))),
                             green=_check_excerpt(_record_at(records, entry.get('green'))))
                        for entry in proved.get('slices') or []])


def file_subject(entry):
    """What the reviewer_must_read question about one file is answered from."""
    return (f'File: {entry["path"]}\n'
            f'Package: {entry["package"]}\n'
            f'{entry["hunks"]} hunk(s), {entry["added"]} lines added and '
            f'{entry["removed"]} removed\n'
            f'Named by the solution record: {"yes" if entry["named_in_solution"] else "no"}\n'
            f'repowise change-risk percentile for this change: {entry["risk_percentile"]}\n'
            f'Coverage delta on the gated package: {entry["coverage_delta"]}')


def questions(criteria, facts):
    """Every question one triage request carries, keyed so none collides."""
    asked = [(criterion_key(position), 'criterion_evidenced', f'Criterion: {text}')
             for position, text in enumerate(criteria, start=1)]
    asked.append(('diff_matches_solution', 'diff_matches_solution', None))
    asked += [(file_key(entry['path']), 'reviewer_must_read', file_subject(entry))
              for entry in facts]
    asked.append(('review_depth', 'review_depth', None))
    return asked


def depth_from(answer):
    """The depth an answer settles, with every doubt resolved towards reading more.

    Spot only when the model is surer of spot than of full and clears the bar. An
    answer nobody could give, and a tie, are both full: narrowing a review is the
    thing this ticket has to earn, and neither of those is evidence for it.
    """
    if answer is None or answer['outcome'] is None:
        return 'full'
    spot = answer['probabilities'].get('spot', 0.0)
    full = answer['probabilities'].get('full', 0.0)
    return 'spot' if spot >= (answer['threshold'] or 0.0) and spot > full else 'full'


def focus_set(facts, by_key, depth, rules):
    """The files the reviewer is asked to read.

    At full depth, every one. At spot depth, the files the model is at least
    half sure carry something the tests would not have caught, and never none:
    a review that reads nothing is not a review, so the file it was least unsure
    about stays. A failed deterministic check needs no clause of its own here,
    because a failure has already forced full depth by the time this is reached.
    """
    paths = [entry['path'] for entry in facts]
    if depth == 'full':
        return list(paths)
    bar = rules['review']['focus_probability']
    scored = {path: (by_key.get(file_key(path)) or {}).get('probabilities', {}).get('yes', 0.0)
              for path in paths}
    kept = [path for path in paths if scored[path] >= bar]
    if not kept and paths:
        kept = [max(paths, key=lambda path: scored[path])]
    return kept


def excluded_share(facts, narrowed):
    """The share of the diff's lines the focus set leaves out, by line count."""
    inside = set(narrowed)
    total = sum(entry['added'] + entry['removed'] for entry in facts)
    if not total:
        return 0.0
    dropped = sum(entry['added'] + entry['removed'] for entry in facts
                  if entry['path'] not in inside)
    return round(dropped / total, 4)


def reviewer_task(ticket, sequence, depth, focus, results, shadow):
    """The task the session hands its reviewer subagent.

    Text rather than a call, because the harness runs no model: what it buys is
    that the focus set the reviewer is given and the focus set the gate will
    check are the same list, read from the same record. What pass one already
    settled is named so the reviewer does not spend a read confirming it.
    """
    passed = [check['name'] for check in results if check['outcome'] == PASS]
    # Names for what passed, and the detail only for what did not. A passing
    # check's detail names paths, and at spot depth some of those are outside the
    # focus set: naming one is inviting the read this ticket exists to save. The
    # detail is safe on the rest, because a failed check has already forced full
    # depth, where the focus set is the whole diff, and no unavailable check's
    # detail names a path at all.
    outstanding = [f'- {check["name"]} ({check["outcome"]}): {check["detail"]}'
                   for check in results if check['outcome'] != PASS]
    lines = [f'Review {ticket} against its acceptance criteria and its journal.',
             '',
             f'Depth: {depth}, settled by triage record {sequence}'
             + (', in shadow mode, so the focus set is the whole diff and what the narrowing '
                'would have dropped is recorded rather than acted on' if shadow else ''),
             '',
             f'Read these {len(focus)} file(s) and no others:']
    lines += [f'- {path}' for path in focus]
    if passed:
        lines += ['',
                  'Already settled with no model, so do not spend a read confirming any of '
                  'them: ' + ', '.join(passed) + '.']
    if outstanding:
        lines += ['', 'Not settled, so they are yours:']
        lines += outstanding
    lines += ['',
              "Return the review record's shape. Its `read` list must name every file you "
              'read and must cover the focus set above, which the review gate checks.']
    return '\n'.join(lines)


def run(repository, records, current, rules, ticket, sequence):
    """The whole triage, as the data a `triage` record carries."""
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
    facts = file_facts(repository, files, named, records, current['attempt'])

    reasons = [gates.FULL_DEPTH_RULES[name]
               for name in gates.full_depth_rules(records, repository.root, solution)]
    reasons += [f'{check["name"]} did not pass, so the reviewer reads everything: '
                f'{check["detail"]}' for check in failed(results)]

    if reasons:
        # Nothing is put to the model, because nothing it could answer would
        # change the answer. That is the whole point of a rule.
        asked, answers = [], []
        requested = dict(asked=False, model=None,
                         reason='Full depth is settled by rule, so no request was made: '
                                + reasons[0],
                         answers=[])
    else:
        asked = questions(criteria, facts)
        state = dict(ticket=ticket,
                     stage='review',
                     attempt=current['attempt'],
                     criteria=criteria,
                     solution=dict(mode=gates.mode_of(solution),
                                   approach=solution.get('approach'),
                                   changes=solution.get('changes') or [],
                                   migrations=solution.get('migrations') or [],
                                   slices=solution.get('slices') or []),
                     deterministic=results,
                     files=facts,
                     journal=journal_excerpts(records))
        answers = jev.ask_batch(repository.root, rules, asked, state, must_answer=False)
        answered = next((answer for answer in answers if answer['source'] == 'jev'), None)
        requested = dict(asked=True,
                         model=(answered or {}).get('model'),
                         reason=None if answered else
                                'The request was made and nothing came back that could be read',
                         answers=answers)

    by_key = {answer['key']: answer for answer in answers}
    criteria_answers = [dict(by_key[criterion_key(position)], criterion=text)
                        for position, text in enumerate(criteria, start=1)
                        if criterion_key(position) in by_key]
    depth = 'full' if reasons else depth_from(by_key.get('review_depth'))
    narrowed = focus_set(facts, by_key, depth, rules)
    shadow = bool(rules['review']['triage_shadow'])
    focus = [entry['path'] for entry in facts] if shadow else list(narrowed)
    return dict(fingerprint=fingerprint,
                # What the review gate compares, and why it is a second number:
                # the procedure writes the ticket file between this record and
                # that advance, every time, so a comparison over the whole tree
                # would fire on the harness's own writing. F4 and F5 of this
                # ticket's review.
                code_fingerprint=repository.fingerprint(excluding=procedure_paths(records)),
                files=facts,
                criteria=criteria,
                deterministic=results,
                rules=reasons,
                jev=requested,
                criteria_answers=criteria_answers,
                review_depth=depth,
                # In shadow the reviewer still reads everything, and what the
                # narrowing would have dropped is stored rather than acted on.
                # That is the figure SEEN-109 decides on, measured before
                # anything is decided by it.
                focus=focus,
                shadow=shadow,
                would_exclude=sorted({entry['path'] for entry in facts} - set(narrowed)),
                excluded_share=excluded_share(facts, narrowed),
                reviewer_task=reviewer_task(ticket, sequence, depth, focus, results, shadow))


def _ticket_text(repository, records):
    """The ticket as it stands, by the same rule every other reader uses."""
    from .cli import _ticket_text as read
    text, _ = read(records[0]['data'], records[0]['data'].get('ticket_id', records[0]['ticket']),
                   repository.root)
    return text


def unevidenced(data):
    """The criteria the model could see no evidence for.

    `passed` is False only for an answer that was actually given and did not clear
    its bar. An unavailable answer leaves it None and sends nothing back: a
    judgement nobody made is not a judgement, which is the rule the stage gates
    already apply.
    """
    return [answer['criterion'] for answer in data['criteria_answers']
            if answer['passed'] is False]


def append(repository, folder, records, current, args, rules):
    """Run the triage, keep it, and send the ticket back if a criterion has no evidence.

    The triage is recorded either way, because it happened; what is refused is
    going on to a reviewer. That ordering is the one `check` already uses for a
    RED that did not fail, and it is what puts the return before any model reads
    the diff.
    """
    # The reviewer task names the record it came from, and a record does not know
    # its own number until it is written. This is the number journal.append will
    # give it, computed the same way and under the same lock.
    data = run(repository, records, current, rules, args.ticket, len(records) + 1)
    record = journal.append(folder, records, kind='triage', stage='review',
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket, data=data)
    missing = unevidenced(data)
    if not missing:
        return record
    reason = ('The triage could see no evidence for: ' + '; '.join(missing)
              + '. A criterion with nothing behind it is answered at the tdd stage, by writing '
                'the test or the check that proves it, rather than by a reviewer reading a diff '
                'that does not contain it')
    journal.append(folder, records + [record], kind='return', stage='review',
                   attempt=current['attempt'], actor=args.actor, head=repository.head(),
                   ticket=args.ticket,
                   data=dict(from_stage='review', to_stage='tdd',
                             to_attempt=current['attempt'] + 1, reason=reason))
    raise HarnessError(
        f'{reason}. Recorded as triage {record["sequence"]} and returned to tdd; no reviewer '
        'was spawned, so nothing has read the diff yet')
