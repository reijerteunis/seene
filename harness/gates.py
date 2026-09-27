"""What each stage gate proves before a ticket may leave its stage.

Three layers, one job each. The stage template declares which fields must be
present; this module declares the relations between records, which no template
can express; thresholds.toml declares the numbers and vocabularies. A gate
checks that recorded evidence exists, is current and is ordered. It cannot check
that a conclusion is correct, and it does not pretend to.
"""

import hashlib
import json

from . import checks
from .errors import HarnessError, require
from .paths import (ENUMERATED_KEYS, FINGERPRINT_EXCLUDED, NON_CODE_TEMPLATE,
                    TEMPLATE_FOR_STAGE, TEMPLATES)

MODES = ('code', 'non-code')
# How a review discloses whose context it came from. A subagent is a context
# boundary and not independence by itself, so it is its own word rather than a
# second meaning of independent: the escaped-defect figures are read per kind
# later, and a word covering both could not answer which kind caught what.
INDEPENDENCE = ('independent', 'subagent', 'self-review')
# Where a ticket is worked. A tool that wrote a record at one of these wrote the
# work; the stages after them are what happens to the work once it exists.
WORK_STAGES = ('clarify', 'solution', 'tdd')
SLICE_KEYS = ('name', 'points', 'files', 'red')
POLICY_GATE_ACTION_KEYS = ('reversibility', 'action_type', 'euro_impact_estimator')
FINDING_KEYS = ('id', 'severity', 'claim', 'failure_scenario', 'status', 'resolution')
# The severities SEEN-109's escape rule is written at, which is why a finding at
# one of them has to name the file it is in.
ESCAPING_SEVERITIES = ('high', 'blocking')
# How far back the tree a check ran against is looked for. A check runs on the
# working tree, and what puts that tree in the history is the commit that
# carried the work it proved, which is the next commit on the branch; fifty is
# past the longest ticket on record and keeps the search bounded.
TREE_SEARCH_LIMIT = 50
# Why a citation is compared over the whole tree when nothing scopes it. The
# regression is the deliberate case: it covers the suite and not a slice, so it
# has no files to be judged over and never had. The second is the reason of last
# resort, for a caller that named no scope and no reason of its own.
WHOLE_SUITE = ('the regression covers the suite rather than a slice, so there are no files to '
               'scope the comparison to')
UNSCOPED = 'nothing scopes this citation to the code it covered'


def template_name(stage, mode=None):
    if stage == 'tdd' and mode == 'non-code':
        return NON_CODE_TEMPLATE
    require(stage in TEMPLATE_FOR_STAGE, f'Stage {stage} has no evidence template')
    return TEMPLATE_FOR_STAGE[stage]


def load_template(root, stage, mode=None):
    path = root / TEMPLATES / template_name(stage, mode)
    require(path.is_file(), f'Missing template: {path}')
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise HarnessError(f'Template {path.name} is not readable JSON: {error}')


def mode_of(data):
    """A record's mode, with silence meaning code.

    Nine solution records were written before the field existed, and a gate that
    invalidates history to gain a field is the worse trade.
    """
    return data.get('mode', 'code')


def for_mode(template, stage, mode, data=None):
    """The fields a stage requires of this kind of ticket.

    A non-code ticket has no tests to write first, and until SEEN-103 it had to
    write some anyway to reach the stage where it said so. The tdd stage solves
    the same problem with a whole second template; one field out of eleven does
    not justify a second one here.
    """
    if stage == 'solution' and mode == 'non-code':
        return {key: value for key, value in template.items()
                if key not in ('tests_first', 'slices')}
    # A review names the reviewer's session only when it discloses a subagent,
    # which is the one disclosure the gate checks the value against. A review by
    # the other assistant has a context of its own by construction, and on a
    # self-review the value would only restate the implementer's own session.
    if stage == 'review' and (data or {}).get('independence') != 'subagent':
        return {key: value for key, value in template.items() if key != 'reviewer_session'}
    return template


def _filled(value):
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def require_template_fields(template, data):
    """Every key the template carries must be answered.

    A key the template ships as an empty list may stay empty; anything else must
    hold a real value, because an empty answer to a question the template asks
    is the same as not answering it.
    """
    for key, example in template.items():
        require(key in data, f'Missing required field: {key}')
        value = data[key]
        if isinstance(example, bool):
            require(isinstance(value, bool), f'Field {key} must be true or false')
        elif isinstance(example, int) and not isinstance(example, bool):
            require(isinstance(value, int) and not isinstance(value, bool),
                    f'Field {key} must be a recorded record number')
        elif isinstance(example, str):
            require(isinstance(value, str) and value.strip(), f'Field {key} must not be empty')
        elif isinstance(example, list):
            require(isinstance(value, list), f'Field {key} must be a list')
            require(example == [] or value, f'Field {key} must not be empty')
            for entry in value:
                require(_filled(entry), f'Field {key} holds an empty entry')
        elif isinstance(example, dict):
            require(isinstance(value, dict), f'Field {key} must be an object')


def _strings(value, key=None):
    """Every free-text string in a document, skipping enumerated answers."""
    if isinstance(value, dict):
        for name, item in value.items():
            if name not in ENUMERATED_KEYS:
                yield from _strings(item, name)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, key)
    elif isinstance(value, str):
        yield value


def reject_placeholders(template, data):
    """Refuse evidence still carrying the template's example prose.

    Copying a template and advancing without editing it would record a claim
    nobody made, so unchanged example text counts as a missing answer.
    """
    examples = set(_strings(template))
    for value in _strings(data):
        require(value not in examples,
                f'Replace the template text before advancing: "{value}"')


def record_at(records, number):
    require(isinstance(number, int) and not isinstance(number, bool),
            f'Not a record number: {number!r}')
    for record in records:
        if record['sequence'] == number:
            return record
    raise HarnessError(f'Record {number} is not in this journal')


def content_fingerprint(repository, commit):
    """The fingerprint of a commit's tree, as `Repository.fingerprint` defines it.

    The same listing of `path:blob` over the paths the fingerprint counts, read
    from a commit rather than from the index and the working tree. It is a second
    reading of one definition, which is worth saying plainly: the repository
    hashes the tree in hand and cannot hash a commit, and the alternative was to
    check out or stash somebody's work to ask a question about it.
    `test_the_fingerprint_this_rule_reads_is_the_one_the_repository_writes` holds
    the two readings to each other, so a change to either is caught here rather
    than by a citation silently scoped off the wrong commit.
    """
    entries = {}
    for line in repository.git('ls-tree', '-r', commit).splitlines():
        details, _, path = line.partition('\t')
        if path and not path.startswith(FINGERPRINT_EXCLUDED):
            entries[path] = details.split()[2]
    listing = '\n'.join(f'{path}:{blob}' for path, blob in sorted(entries.items()))
    return hashlib.sha256(listing.encode()).hexdigest()


def _the_commit_holding(repository, tree):
    """The commit whose content is that tree, if this branch still has one.

    A check records the fingerprint of a tree and not the tree, so which files it
    held is a question only the tree itself answers. What answers it afterwards
    is the commit that carried the work the check proved: one commit later the
    same content is in the history, and its fingerprint says so. Nothing is
    trusted about which commit that is; every candidate is hashed and the one
    that matches is the tree.

    None when no commit carries it, which is a check whose tree was never
    committed as it stood. That is an absence rather than a difference, and it
    falls back to the whole tree rather than being scoped to a guess.
    """
    for commit in repository.git('log', '--format=%H', '-n', str(TREE_SEARCH_LIMIT),
                                 'HEAD').split():
        if content_fingerprint(repository, commit) == tree:
            return commit
    return None


def _moved_since(repository, commit, files):
    """Which of these paths differ between that commit and the tree in hand.

    Git's own pathspec, so a slice entry naming a directory covers everything
    under it and nothing beside it: `supabase/migrations` reaches every migration
    and not `supabase/migrations-old`. That is the same reading the guard settled
    on in SEEN-112, and here it can only cost a citation its evidence, never
    grant it: a wider scope is a stricter rule.

    Untracked files are counted, because a path the slice names that is new is a
    path that was not there when the check ran.
    """
    moved = set(repository.git('diff', '--name-only', commit, '--', *files).split())
    for line in repository.git('status', '--porcelain', '-uall', '--', *files).splitlines():
        if line.startswith('??'):
            moved.add(line[3:].strip())
    return sorted(path for path in moved if path)


def _files_the_slice_covers(records, position):
    """The files the plan says the slice at this position covers, or nothing.

    Read from the route record first, because the route is what the pack hands
    the session that works the slice, and from the accepted plan when no route
    names it. Nothing for a citation that names no slice, a position no plan
    names, or an entry that names no file: each is an absence of scope, and an
    absence of scope is not an empty one. An empty comparison would accept every
    citation, so it falls back to the whole tree instead.
    """
    if position is None:
        return None
    from . import routing
    entry = routing.for_slice(records, position) or {}
    files = entry.get('files')
    if not files:
        planned = (latest_evidence(records, 'solution') or {}).get('slices') or []
        if isinstance(position, int) and 1 <= position <= len(planned):
            files = (planned[position - 1] or {}).get('files')
    named = [path for path in (files or []) if isinstance(path, str) and path.strip()]
    return named or None


def _unresolved_in(repository, commit, files):
    """Which of these entries match nothing git can see in that commit.

    `git diff --name-only <commit> -- harness/typo.py` exits 0 with no output, so
    an entry that matches no path made the comparison vacuous rather than empty:
    a slice naming a typo for the file its work is in, or a gitignored path,
    accepted a citation however much the code had moved, and the realistic case
    is a typo beside a test file that stood still. An entry nothing resolves is
    an untrustworthy scope and not an empty one, so it costs the whole scope. F2
    of SEEN-113's second review, reproduced end to end.

    Asked of the commit the comparison is made against, because that is the tree
    the check ran on: a path that was not in it is not code that check covered.
    """
    return [path for path in files
            if not repository.git('ls-tree', '-r', '--name-only', commit, '--', path).strip()]


def _positions_declared_for(records, number):
    """Which slice of the plan the accepted tdd records say this check proved.

    Every answer found rather than the last one read, so that two records
    disagreeing stays a disagreement: the scope is granted on one answer and on
    nothing else. None stands for a round that declared no position, which is a
    claim that the round belongs to no single slice and so lends no mapping.
    """
    if not isinstance(number, int) or isinstance(number, bool):
        return set()
    declared = set()
    for record in records:
        if record['kind'] != 'advance' or record['data'].get('from_stage') != 'tdd':
            continue
        for entry in (record['data'].get('evidence') or {}).get('slices') or []:
            if not isinstance(entry, dict):
                continue
            if number not in (entry.get('red'), entry.get('green')):
                continue
            position = entry.get('position')
            declared.add(position if isinstance(position, int)
                         and not isinstance(position, bool) else None)
    return declared


def _the_scope_a_citation_is_judged_in(records, number, position):
    """The files a cited check's evidence is about, and why there are none.

    Two answers and not one, because the reason there is no scope is what the
    refusal has to say. The position is named by the record making the citation,
    which is exactly why it cannot settle the scope by itself: naming another
    slice's position was all it took to be compared against files that had not
    moved, and the same citation declared honestly was refused. F1 of SEEN-113's
    second review, reproduced end to end.

    So it is corroborated from a record that is not the one asking: the tdd
    record of the round that recorded the check, which passed this gate when the
    check was fresh and is in the hash chain since. A check no accepted tdd
    record cites is corroborated by nothing, and a round that declared no
    position declares no mapping, which is this ticket's own record 17. Both are
    absences, and an absence fails closed to the whole-tree comparison.
    """
    if position is None:
        return None, ('this citation names no slice, so there is nothing to scope the '
                      'comparison to')
    declared = _positions_declared_for(records, number)
    if not declared:
        return None, (f'no accepted tdd record says which slice of the plan check {number} '
                      'proved, so the position this record names for it is corroborated by '
                      'nothing but itself')
    if declared != {position}:
        named = ', '.join('no slice at all' if value is None else f'slice {value}'
                          for value in sorted(declared, key=lambda value: (value is None, value)))
        return None, (f'this record names slice {position} for check {number} and the tdd record '
                      f'of the round that recorded it named {named}, so which files it covered '
                      'is not settled')
    files = _files_the_slice_covers(records, position)
    if not files:
        return None, (f'nothing in the plan or the route says which files slice {position} '
                      'covers, so there is nothing to scope the comparison to')
    return files, None


def _require_the_check_is_about_this_code(record, number, tree, current, repository, scope):
    """A check from an earlier attempt still describes the code it covered.

    The second of the two refusals, and the one that carries the reason: a check
    records the fingerprint of the tree it ran against, so whether its evidence
    is still about this code is a question the journal answers rather than one
    anybody has to be trusted on.

    Scoped to the files the cited check's slice names, because that is what "this
    code" means. The whole tree cannot answer it: every green records a distinct
    tree, SEEN-107 13 of 13, SEEN-109 13 of 13, SEEN-111 5 of 5, so a whole-tree
    comparison accepts an earlier attempt's green only when nothing at all
    changed since, which is never true of a ticket whose later slices added code.
    A green proving slice 1 is still evidence about slice 1 when slice 3 has since
    written elsewhere, and stops being evidence the moment a file slice 1 names
    has moved. The refusal names those files, because a file is what a session
    can go and look at.

    The whole tree survives as the fallback and only as the fallback: a citation
    no slice can be attributed to, and a check whose tree no commit carries, are
    held to the strict rule. Both are absences, and an absence fails closed.

    A check that recorded no fingerprint at all is refused too, and separately:
    it is not evidence that the tree moved, it is the absence of the evidence
    that it did not, and every journal written before SEEN-086 recorded one is in
    that position.

    `scope` is the files and, when there are none, the reason there are none: a
    scope is granted only where the journal corroborates the slice it belongs to
    and git can resolve every path that slice names, and everything else is an
    absence that falls back to the whole tree.
    """
    files, because = scope
    # Never an empty reason. The whole-tree refusal is the one a reader meets
    # with nothing else to go on, and "because None" is what a caller that
    # passed files and no reason used to leave them with.
    because = because or UNSCOPED
    after = record['data'].get('after')
    require(after is not None,
            f'Check {number} was recorded in attempt {record["attempt"]} and this record is '
            f'written in attempt {current["attempt"]}, and the check does not say which tree it '
            'ran against, so nothing here can tell whether its evidence is still about this '
            'code; run it again in this attempt')
    if after == tree:
        return
    commit = _the_commit_holding(repository, after) if files and repository else None
    if commit is not None:
        unresolved = _unresolved_in(repository, commit, files)
        if not unresolved:
            moved = _moved_since(repository, commit, files)
            require(not moved,
                    f'The code check {number} covers has changed since it ran: '
                    f'{", ".join(moved)}. Its slice names {", ".join(files)}, and its evidence '
                    'is about those files as they were, not as they are; run it again in this '
                    'attempt')
            return
        because = (f'its slice names {", ".join(unresolved)}, which git cannot see in the tree '
                   'it ran against, so a comparison over those names is a comparison of nothing')
    elif files:
        because = ('no commit on this branch carries the tree it ran against, so which files '
                   'moved cannot be told')
    require(False,
            f'The tree moved under check {number}: it ran against {after[:12]} and this record '
            f'is written against {tree[:12]}, compared over the whole tree because {because}. '
            'Its evidence is about code this ticket has changed since, so it does not support a '
            'citation here; run it again in this attempt')


def cited_check(records, number, phase, current, tree=None, repository=None,
                scope=(None, None)):
    """A check a stage record points at, confirmed to be usable evidence here.

    A check counts only for the stage that produced it, and only while it is
    still about this code. The attempt used to stand for the second half, and it
    is a lossy stand-in: a return resets which checks a record may cite, so a
    ticket returned more than once could not accumulate its evidence, although
    the slices proved in its first attempts were still green and their tests
    still in the branch. Re-proving one of them needs a RED for code that already
    passes, which is the one thing this harness refuses outright, so there was no
    honest way out from inside such a ticket. SEEN-112 was returned five times
    and found it.

    So the test is the code rather than the attempt, which keeps the original
    protection whole: what it defended against was evidence reused for code that
    changed, and the fingerprint is the thing that says whether it did. `tree` is
    the tree the citing record is written against and `scope` is the files the
    cited check's own slice covers with the reason there are none, which is the
    scope the question is asked in.
    Given no tree, only this attempt's own checks count, because a comparison
    with nothing is not one.

    Two refusals and not one, because a gate answering "another attempt" where it
    means "different code" is what made this take five returns to find: there is
    no such check, or the tree moved under the check there is.
    """
    require(isinstance(number, int) and not isinstance(number, bool),
            f'Not a record number: {number!r}')
    record = next((entry for entry in records
                   if entry['sequence'] == number and entry['kind'] == 'check'), None)
    require(record is not None,
            f'There is no such check: record {number} is not a check in this journal, so nothing '
            'in it supports this citation')
    require(record['stage'] == current['stage'],
            f'Check {number} was recorded at the {record["stage"]} stage and this record belongs '
            f'to {current["stage"]}; a check counts only for the stage that produced it')
    if record['attempt'] != current['attempt']:
        _require_the_check_is_about_this_code(record, number, tree, current, repository, scope)
    require(record['data']['phase'] == phase,
            f'Expected a {phase} check at record {number}, found {record["data"]["phase"]}')
    if phase == 'red':
        require(checks.demonstrates_failure(record['data']),
                f'Check {number} is cited as a RED but did not fail: it exited '
                f'{record["data"]["exit_code"]}')
    else:
        require(record['data']['exit_code'] == 0,
                f'Check {number} is cited as a {phase} but exited {record["data"]["exit_code"]}')
    return record


def latest_evidence(records, stage):
    """The evidence of the most recent accepted advance out of a stage."""
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == stage:
            return record['data'].get('evidence', {})
    return None


def _clarify(data, records, current, repository, thresholds):
    require(data['open_questions'] == [],
            'Answer every open question, or record the decision to defer it, before advancing: '
            + '; '.join(str(question) for question in data['open_questions']))
    return {}


def _slice_plan(data, thresholds):
    """The slices a code-mode ticket plans, and the two caps they may not break.

    The caps are about what one context can hold, which is why they are counted
    per slice and per plan and not against the ticket's estimate. A plan whose
    points disagree with the forecast is reported and allowed: a gate that made
    the two equal would turn every re-estimate into a returned record.
    """
    limits = thresholds['session']
    slices = data['slices']
    require(len(slices) <= limits['max_slices_per_ticket'],
            f'This plan has {len(slices)} slices and a ticket may plan at most '
            f'{limits["max_slices_per_ticket"]}. A plan that needs more is a ticket that is too '
            'big, and it is split the way SEEN-089 and SEEN-096 were')
    total = 0
    for position, entry in enumerate(slices, start=1):
        require(isinstance(entry, dict), f'Slice {position} must be an object')
        for key in SLICE_KEYS:
            require(_filled(entry.get(key)), f'Slice {position} is missing {key}')
        points = entry['points']
        require(isinstance(points, int) and not isinstance(points, bool) and points > 0,
                f'Slice {position} must carry its points as a whole number above zero, '
                f'not {points!r}')
        require(points <= limits['max_points_per_slice'],
                f'{entry["name"]} carries {points} points, over the '
                f'{limits["max_points_per_slice"]} points one slice may carry. A slice is what '
                'one session can hold start to finish; split it, or split the ticket')
        total += points
    return total


def _solution(data, records, current, repository, thresholds):
    clarified = latest_evidence(records, 'clarify') or {}
    if clarified.get('changes_agent_action'):
        declaration = data.get('policy_gate_action')
        require(isinstance(declaration, dict) and declaration,
                'This ticket changes an agent action, so policy_gate_action must declare '
                'reversibility, action_type and euro_impact_estimator')
        for key in POLICY_GATE_ACTION_KEYS:
            require(_filled(declaration.get(key)), f'policy_gate_action is missing {key}')
    if mode_of(data) == 'non-code':
        return {}
    from . import forecast
    return dict(slice_points=_slice_plan(data, thresholds),
                forecast=forecast.predict(data['slices'], repository.root, thresholds))


def _tdd(data, records, current, repository, thresholds):
    mode = mode_of(data)
    require(mode in MODES, f'Unknown mode: {mode!r}; use {" or ".join(MODES)}')
    solution = latest_evidence(records, 'solution')
    # No solution record is not a record saying code: there is nothing to
    # disagree with, and the stage order is what requires one.
    if solution is not None:
        planned = mode_of(solution)
        require(mode == planned,
                f'The solution record planned {planned} and this tdd record says {mode}. A '
                'ticket that changes its mind about having behaviour to prove says so in a note '
                'and returns to solution, rather than changing it between stages')
    if mode == 'non-code':
        return _non_code(data, thresholds)
    slices = data['slices']
    require(slices, 'Code changes need at least one slice in slices')
    _require_coverage(records, current)
    _require_the_work_trips_no_unrouted_rule(records, repository, thresholds)
    # The tree every citation below is judged against, read once: a check from an
    # earlier attempt counts while the files its slice covers still hold the
    # content it ran against, and is refused by their names the moment they do
    # not. The regression is scoped to nothing, because it covers the suite and
    # not a slice: it is held to the whole tree.
    tree = repository.fingerprint()
    regression = cited_check(records, data['regression'], 'regression', current, tree,
                             repository, (None, WHOLE_SUITE))
    previous_green = 0
    for position, slice_ in enumerate(slices, start=1):
        require(isinstance(slice_, dict), f'Slice {position} must be an object')
        for key in ('behaviour', 'failure_reason'):
            require(_filled(slice_.get(key)), f'Slice {position} is missing {key}')
        require('position' in slice_,
                f'Slice {position} of this record does not say which slice of the plan it '
                'proved. Name its position, or null for a round that belongs to no single '
                'slice, which is a claim on the record rather than a gap in it: left out, it '
                'skips the route comparison and is indistinguishable from a record written '
                'before the field existed')
        # Per cited check and not per slice entry: the scope of a citation is
        # what the journal says that check proved, and the record citing it does
        # not decide that by naming a position.
        declared = slice_.get('position')
        red = cited_check(records, slice_.get('red'), 'red', current, tree, repository,
                          _the_scope_a_citation_is_judged_in(records, slice_.get('red'),
                                                             declared))
        green = cited_check(records, slice_.get('green'), 'green', current, tree, repository,
                            _the_scope_a_citation_is_judged_in(records, slice_.get('green'),
                                                               declared))
        require(previous_green < red['sequence'] < green['sequence'] <= regression['sequence'],
                f'Slice {position} is out of order; each red must precede its green, slices '
                'must not overlap, and the regression must be the last check')
        _require_the_routed_slice(records, slice_, position, (red, green), thresholds)
        previous_green = green['sequence']
    return {}


def _require_the_routed_slice(records, slice_, order, checks_cited, thresholds):
    """Which slice of the plan this proved slice is, and then its route.

    The plan position, not the order in this record. They agree only in an
    attempt that re-proves the whole plan in order: a rework attempt proves the
    one slice it reworked, so reading the index would have held it to plan slice
    1's route and, with shadow off, refused work that ran exactly as routed.
    F1 of this ticket's fourth review.

    A slice may declare no position, as null, for a rework round that belongs to
    no single slice; it is then held to no route, because the mapping it says it
    does not have cannot be inferred. The declaration is required and only its
    value may be empty: left optional, omitting it was a way past the refusal
    that no reader could tell from a record written before the field existed.
    F2 of the fifth review.
    """
    position = slice_.get('position')
    if position is None:
        return
    planned = len((latest_evidence(records, 'solution') or {}).get('slices') or [])
    require(isinstance(position, int) and not isinstance(position, bool) and position >= 1,
            f'Slice {order} of this record names position {position!r}, which is not a slice '
            'number. The position is which slice of the plan was proved, which is what its '
            'route is keyed by; a round that proved no single slice declares null')
    # Only against a plan there is one. A gate evaluated with no accepted
    # solution record has nothing to range a position against, and refusing
    # there would be refusing on the absence rather than on the value.
    require(not planned or position <= planned,
            f'Slice {order} of this record names position {position}, and the plan has '
            f'{planned} slices')
    _require_the_routed_model(records, position, checks_cited, thresholds)
    _require_a_context_of_its_own(records, position, checks_cited, thresholds)


def _require_the_routed_model(records, position, checks_cited, thresholds):
    """A slice is proved on the model it was routed to, or not at all.

    Three ways not to refuse, and each is an absence rather than an agreement:
    a ticket nobody routed, a check from a machine with no session log, and a
    tier whose model id nobody wrote down. A comparison with nothing is not a
    comparison, which is the rule cost.py already applies to tokens.

    Nothing is refused at all while `[routing] shadow` is true, because in
    shadow every slice still runs on whatever model its session happens to be:
    a gate that refused then would be the change the window exists to hold back.
    """
    from . import routing
    if routing.shadow(thresholds):
        return
    entry = routing.for_slice(records, position)
    if entry is None:
        return
    wanted = routing.model_id(thresholds, entry['model'])
    for record in checks_cited:
        data = record['data']
        # The declaration first, because it is the only thing on a subagent's
        # side that knows: a Claude Code subagent inherits its parent's session
        # id, so what the log says of its check is the parent's model. It is a
        # disclosure and not a proof, and the record carries both so that what
        # was observed and what was claimed are told apart. F1 of this ticket's
        # second review.
        declared = data.get('model_declared')
        if declared:
            require(declared == entry['model'],
                    f'Slice {position} was routed to {entry["model"]} and check '
                    f'{record["sequence"]}, its {data["phase"]}, declared {declared}. The route '
                    'is decided at the tdd stage with the plan on record and is read from the '
                    'handoff pack, never chosen inside the session: spawn the implementer on '
                    'the model it was routed to, or return to solution and route again')
            continue
        ran_on = data.get('model')
        if not wanted or not ran_on or ran_on == wanted:
            continue
        require(False,
                f'Slice {position} was routed to {entry["model"]} ({wanted}) and check '
                f'{record["sequence"]}, its {data["phase"]}, was recorded under '
                f'{ran_on} and declared nothing. The route is decided at the tdd stage with the '
                'plan on record and is read from the handoff pack, never chosen inside the '
                'session: work the slice again on the model it was routed to, or return to '
                'solution and route again')


def _require_a_context_of_its_own(records, position, checks_cited, thresholds):
    """A slice was worked in a context of its own, or neither check says so.

    Called immediately after `_require_the_routed_model`, which it mirrors: the
    same three absences excuse it from refusing at all. Nothing is refused
    while `[routing] shadow` is true, for the reason that gate already gives:
    a refusal then would be the change the shadow window exists to hold back.
    Nothing is refused without a route entry to name, because a comparison
    with nothing is not a comparison. And nothing here reads a token figure,
    which `harness budget` reports and refuses nothing about.

    Whether a check ran in a context of its own is nowhere the session log
    says: a Claude Code subagent inherits its parent's session id (settled in
    this ticket's clarify record, from a real log), so the digest a record
    already carries cannot tell a slice handed to an implementer subagent from
    one worked in the orchestrating session's own context. Only `--agent`
    can, and like `--model` on the gate above, it is a disclosure and not a
    proof: it is checked against `[agents] names` and nothing more.

    Refused only when NEITHER cited check declares an agent, which is the
    criterion's own case: the slice was recorded in the orchestrating
    session's own context. One of the two declaring an agent is a delegated
    slice, whose RED came back from a context of its own even if its GREEN was
    recorded by the session that spawned it, or the other way about, and is
    not refused: widening the refusal to both would refuse a case the
    criterion does not describe.
    """
    from . import routing
    if routing.shadow(thresholds):
        return
    entry = routing.for_slice(records, position)
    if entry is None:
        return
    if any(record['data'].get('agent_declared') for record in checks_cited):
        return
    route_record = None
    for record in records:
        if record['kind'] != 'route':
            continue
        for candidate in record['data'].get('execution', []):
            if candidate is entry:
                route_record = record
                break
    check_names = ' nor '.join(f'check {record["sequence"]} ({record["data"]["phase"]})'
                               for record in checks_cited)
    require(False,
            f'Slice {position} was routed by record {route_record["sequence"] if route_record else "?"} '
            f'to a context of its own, and neither {check_names} declares an agent. It was '
            'recorded in the orchestrating session\'s own context rather than handed to one of '
            'its own: run the implementer as a subagent and pass its check command --agent '
            '<name>, or if a subagent worked it, declare which check is theirs')


def _require_the_work_trips_no_unrouted_rule(records, repository, thresholds):
    """Work that trips a routing rule was routed by that rule, or it is refused.

    The rules read a slice's declared files, and a plan cannot foresee every
    file the work will touch: on SEEN-108 the plan understated its own change by
    twenty-two files across eight triages, so a plan naming no path under
    packages/core is the ordinary case rather than the odd one. The route cannot
    know before the work exists. By the tdd gate it does, because the diff is
    there, and the one thing worth refusing is money arithmetic, a migration or
    a credential written under a model Jev chose. F3 of SEEN-108's ninth review.

    Whole-ticket and not per slice, because nothing maps a changed file to the
    slice that changed it; what it asks is only that if the work trips a rule,
    some slice was routed by one. Silent while `[routing] shadow` is true, like
    every other refusal this route adds.
    """
    from . import routing, triage
    if routing.shadow(thresholds):
        return
    routed = None
    for record in reversed(records):
        if record['kind'] == 'route':
            routed = record
            break
    if routed is None:
        return
    if any(entry['source'] == 'rule' for entry in routed['data']['execution']):
        return
    patterns = thresholds['routing']['rules']
    name, path = routing.path_rule(triage.changed_files(repository), patterns)
    require(name is None,
            f'This work changed {path}, which is {routing.PATH_RULES.get(name, name)}, and no '
            f'slice of route {routed["sequence"]} was routed by a rule: every one was Jev\'s '
            'choice. A plan that did not name the file cannot have been routed for it, so the '
            'rule the ground rules care most about was never applied. Return to solution, name '
            'the file in the slice that changes it, and route again')


def _require_coverage(records, current):
    """A code change measures the gated package, and may not let it fall.

    A first measurement has no baseline and is not a regression; anything after
    that has a number to be compared with.
    """
    measurements = [record for record in records
                    if record['kind'] == 'check' and record['stage'] == 'tdd'
                    and record['attempt'] == current['attempt']
                    and record['data'].get('phase') == 'coverage']
    require(measurements,
            'No coverage measurement for this attempt: run harness coverage <ticket> '
            '--actor <actor> before advancing')
    latest = measurements[-1]['data']
    delta = latest.get('delta')
    require(delta is None or delta >= 0,
            f'Coverage on {latest.get("package")} fell by {delta}: '
            f'{latest.get("baseline")} to {latest.get("lines")}. Cover what the change added, '
            'or say in a note why the fall is right and raise the baseline deliberately')


def _non_code(data, thresholds):
    change_types = thresholds['non_code']['change_types']
    require(data.get('change_type') in change_types,
            f'Unknown change_type: {data.get("change_type")!r}; use one of {", ".join(change_types)}')
    require(_filled(data.get('reason')), 'A non-code change needs a reason')
    if data['change_type'] == 'verification':
        require(data.get('sources'),
                'A verification must name its sources; a fact without a source is not verified')
    return {}


def latest_triage(records, current):
    """The most recent triage of this attempt, or nothing.

    Scoped to the attempt for the reason a cited check is: a focus set computed
    before a return describes a diff that has changed since, and a review held to
    it would be held to the wrong list.
    """
    for record in reversed(records):
        if record['kind'] == 'triage' and record['attempt'] == current['attempt']:
            return record
    return None


def _require_a_current_triage(records, current):
    """A ticket triaged once is triaged again after a return.

    G4 of SEEN-107's third review: both checks below are scoped to the attempt and
    pass silently when it has none, so every attempt after a return started with
    the gate disarmed and a review naming any file at all was accepted. A ticket
    that has never been triaged is unaffected, which is every journal written
    before this ticket and every review run without the command.
    """
    ever = any(record['kind'] == 'triage' for record in records)
    require(not ever or latest_triage(records, current) is not None,
            f'This ticket was triaged in an earlier attempt and not in attempt '
            f'{current["attempt"]}. The focus set that stands was chosen for work that has '
            'changed since, so it holds the reviewer to the wrong list; run harness review '
            'triage again')


def _require_focus_was_read(data, records, current):
    """A review reads what the triage said to read, or it reviewed something smaller.

    A ticket with no triage has no focus set and nothing to check, which is every
    journal written before SEEN-107 and every review run without the command.
    Reading more than the focus set is never refused: the focus set is a floor.
    """
    triaged = latest_triage(records, current)
    if triaged is None:
        return
    focus = set(triaged['data'].get('focus') or [])
    read = {str(path) for path in data.get('read') or []}
    missing = sorted(focus - read)
    require(not missing,
            f'The review does not say it read {len(missing)} file(s) that triage record '
            f'{triaged["sequence"]} put in the focus set: {", ".join(missing)}. A review that '
            'skipped what the triage told it to read is a review of something smaller than the '
            'change; read them, or run the triage again if the diff has moved since')


def _require_the_diff_has_not_moved(records, current, repository):
    """The focus set is a floor, and a floor under a diff that has moved is none.

    F4 of SEEN-107's review: nothing re-checked the diff between the triage and
    this advance, so a file added after the triage was read by nobody and refused
    by nothing. Compared over the code fingerprint the triage recorded, which
    leaves out the ticket file and the generated copies, because the procedure
    writes those in between on every ticket.
    """
    triaged = latest_triage(records, current)
    recorded = (triaged or {}).get('data', {}).get('code_fingerprint')
    if recorded is None:
        return
    from . import triage
    now = repository.fingerprint(
        excluding=triage.procedure_paths(records, repository.root))
    require(recorded == now,
            f'The diff has moved since triage record {triaged["sequence"]}: it read '
            f'{recorded[:12]} and this advance reads {now[:12]}. The focus set it chose does not '
            'describe this change any more, so a file could reach merge that nothing read. Run '
            'harness review triage again')


def _review(data, records, current, repository, thresholds):
    require(latest_evidence(records, 'tdd') is not None, 'Complete the TDD stage before review')
    _require_a_current_triage(records, current)
    _require_focus_was_read(data, records, current)
    _require_the_diff_has_not_moved(records, current, repository)
    require(data['verdict'] == 'pass',
            f'A verdict of {data["verdict"]!r} is a return, not an advance; use harness return')
    check_findings(data['findings'], thresholds['review']['severities'])
    two_reviewers = needs_two_reviewers(records, repository.root)
    if two_reviewers:
        require(_filled(data.get('second_reviewer')),
                'This change touches billing or an agent action, so the review needs a '
                'second_reviewer and a security checklist')
        require(data.get('security_checklist'), 'The security checklist must be answered')
    require(data['independence'] in INDEPENDENCE,
            f'Disclose independence as {", ".join(INDEPENDENCE)}')
    worked_by = _implementer_tools(records)
    if data['independence'] == 'independent':
        # G2: len(tools) > 1 asked whether a second tool had recorded anything,
        # which a reviewer's own return satisfies, so the implementer's session
        # could review its own code by choosing a different word for it.
        reviewer_tool = str(data['reviewer']).partition(':')[0]
        require(reviewer_tool and reviewer_tool not in worked_by,
                'A review is not independent when the tool that reviewed it is a tool that wrote '
                f'the work: {", ".join(sorted(worked_by)) or "nobody"} wrote this ticket and '
                f'{reviewer_tool or "nobody"} reviewed it. Disclose a review in a context of its '
                'own as subagent, and a review by the session that wrote the code as self-review')
    if data['independence'] == 'subagent':
        _require_another_context(data, records)
    if two_reviewers:
        # G6: [actors] tools carries human, and a person reviewing alone is not the
        # other assistant. The assistants are their own vocabulary.
        known = set(thresholds['actors']['assistants'])
        # F6: a prefix that is not a tool this repository knows is a typo, not the
        # other assistant, and it satisfied the one control that stands where a
        # declared session cannot be verified.
        named = {str(data.get(key) or '').partition(':')[0]
                 for key in ('reviewer', 'second_reviewer')} & known
        require(named - worked_by,
                'This change touches billing or an agent action, so the review comes from the '
                f'other assistant: {", ".join(sorted(worked_by))} wrote this '
                f'ticket and {", ".join(sorted(named)) or "no tool this repository knows"} '
                'reviewed it. A subagent is a context boundary, not independence by itself, and a '
                'declared session cannot stand in for it where a missed defect costs money. Name '
                f'the reviewer as one of {", ".join(sorted(known))} and a role')
    return dict(tree=repository.fingerprint())


def _tools_of(records):
    """The tools that wrote this ticket's records, read from the actor on each."""
    return {record['actor'].split(':')[0] for record in records if record.get('actor')}


def _implementer_tools(records):
    """The tools that wrote the work, read from the stage each record was written at.

    Three reviews asked this question and the first two answers were both wrong in
    the same way, by naming what does not count. F2: every record counted, so the
    other assistant's `return`, which is the documented way to send work back, made
    it an author and the gate refused the review it demands. G1: the actor's role
    counted instead, so a ticket recorded entirely as `:reviewer` had no author at
    all. H1: everything but the review stage counted, so a return at deliver or a
    reopen at delivered did it again through the two stages nobody had thought of.

    So it is named positively. WORK_STAGES is where a ticket is worked, and a tool
    that wrote a record there wrote the work. Anything else, at review, at deliver,
    after delivery, is what happens to the work once it exists. The test that holds
    this runs over every journal in this repository rather than over another
    fixture, which is what the third review asked for instead of a fourth predicate.
    """
    return {(record.get('actor') or '').partition(':')[0] for record in records
            if record.get('actor') and record.get('stage') in WORK_STAGES}


def _sessions_of(records):
    """Every session that wrote a record on this ticket.

    F5 in SEEN-105's first review: this was scoped to the current attempt, so the
    session that worked attempt 1 passed as the reviewer's context in attempt 2.
    Criterion 3 says the implementer's session, and a session that wrote any
    record on this ticket is one.
    """
    return {record.get('session') for record in records if record.get('session')}


def _require_another_context(data, records):
    """A subagent review names a session, and not one the implementer worked in.

    A Claude Code subagent inherits its parent's session id, observed and recorded
    in SEEN-105's journal at record 7, so the harness cannot derive this and the
    record declares it. The gate refuses what it can see: a value that is one of
    the sessions which wrote this attempt's records, or the session running the
    advance. A value typed to pass is not detectable and the gate does not pretend
    to detect it; what stands where that matters is the cross-tool review.
    """
    from . import sessions
    declared = str(data.get('reviewer_session') or '').strip()
    require(declared,
            'A subagent review must name the reviewer_session it came from. The harness cannot '
            'read it, because a subagent inherits its parent session id, so the session that '
            'spawned the reviewer records the identifier it gave it')
    own = _sessions_of(records)
    running = sessions.current()
    if running:
        own.add(running)
    require(declared not in own,
            f'{declared} is a session that worked this ticket, so a review from it is a '
            'self-review however it is disclosed. Disclose it as self-review, or have the review '
            'done in a context that did not write the code')


GATES = {'clarify': _clarify, 'solution': _solution, 'tdd': _tdd, 'review': _review}


# The three conditions SEEN-107 keeps as rules rather than putting to a model,
# and the prose each is recorded as. Two of them are also what makes a change one
# a second reviewer reads, so both readers ask the one predicate below rather than
# keeping a copy of it: a second copy of this reasoning is a second answer waiting
# to disagree, which is what H3 of SEEN-105's third review found.
FULL_DEPTH_RULES = {
    'agent_action': 'This ticket changes an agent action, so the review is full depth by rule',
    'billing': 'This change touches billing or the policy gate, so the review is full depth '
               'by rule',
    'migration': 'This change carries a migration, so the review is full depth by rule',
}
# The two that also need a second reviewer, the security checklist and the other
# assistant. A migration is expensive to review and cheap to revert, which is not
# the same thing as a missed defect costing money.
REVIEWED_TWICE = ('agent_action', 'billing')


def full_depth_rules(records, root=None, solution=None):
    """Which of the three rules this ticket trips, in the order they are listed.

    `solution` is the record in hand when there is one, because a triage run
    against a draft should read that draft rather than the last accepted advance.
    """
    tripped = []
    if (_frontmatter_declares_agent_action(records, root)
            or (latest_evidence(records, 'clarify') or {}).get('changes_agent_action')):
        tripped.append('agent_action')
    if _billing_decision(records):
        tripped.append('billing')
    planned = solution if solution is not None else (latest_evidence(records, 'solution') or {})
    if planned.get('migrations'):
        tripped.append('migration')
    return tripped


def _billing_decision(records):
    """Whether the solution stage answered touches_billing_or_policy_gate yes."""
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'solution':
            return any(decision['question'] == 'touches_billing_or_policy_gate'
                       and decision['outcome'] == 'yes'
                       for decision in record['data'].get('decisions', []))
    return False


def needs_two_reviewers(records, root=None):
    """Whether this review needs a second reviewer, the checklist and another tool.

    Criterion 4 of SEEN-105 says an agent action or billing. G3 in its second review
    found only the billing half enforced, because the solution question can be
    answered no, as it was on SEEN-105 itself at record 14. H2 in its third found
    the half that was added reading a field the same session writes, whose template
    default is false, while the ticket's own frontmatter, which this repository owns
    and which the plan generator will not touch once a ticket has started, was read
    by no harness code at all. Both are read now, and either one is enough.

    Public, because `harness draft` has to ask the same question and a second copy
    of this reasoning is a second answer waiting to disagree: that was H3.
    """
    return bool(set(full_depth_rules(records, root)) & set(REVIEWED_TWICE))


def _frontmatter_declares_agent_action(records, root):
    """What the ticket file itself says, which no session rewrites by hand."""
    if root is None or not records:
        return False
    name = records[0].get('data', {}).get('ticket_file')
    if not name:
        return False
    path = root / name
    if not path.is_file():
        return False
    from . import report as reporting
    return reporting._field(reporting.frontmatter(path), 'changes_agent_action') == 'true'


def evaluate(stage, data, records, current, repository, thresholds):
    """Run one stage gate and return the facts the harness adds to the record."""
    require(isinstance(data, dict), 'Stage evidence must be a JSON object')
    gate = GATES.get(stage)
    require(gate is not None,
            f'Stage {stage} has no advance out of it'
            + ('; verify-delivery is its stage gate' if stage == 'deliver' else ''))
    if stage in ('solution', 'tdd'):
        require(mode_of(data) in MODES,
                f'Unknown mode: {data.get("mode")!r}; use {" or ".join(MODES)}')
    template = load_template(repository.root, stage, data.get('mode'))
    # Both checks read the same shape. A field this kind of record does not carry
    # is not required and its example is not placeholder text either: a non-code
    # solution record that left the tests_first example in place would otherwise
    # be refused for prose the gate had just decided not to ask for.
    shaped = for_mode(template, stage, mode_of(data), data)
    require_template_fields(shaped, data)
    # F8 in SEEN-105's first review: the examples come from the whole template, so
    # prose from a field this record does not carry is still placeholder text
    # wherever it was pasted. Only the dropped field's own value is left out.
    reject_placeholders(template, {key: value for key, value in data.items() if key in shaped})
    return gate(data, records, current, repository, thresholds)


def check_findings(findings, severities, resolved=True):
    """What a finding must carry, and why a serious one must name its file.

    SEEN-109 measures the review triage by asking whether anything expensive got
    through a file the narrowing would have dropped, and a finding nobody can
    place answers that question in favour of the narrowing. seen-reviewer
    already writes `file` as `path:line`, so the requirement asks for what is
    already there. Low and medium are left alone: neither can ever be an escape,
    because not looking for them is the saving itself.
    """
    for finding in findings:
        require(isinstance(finding, dict), 'Every finding must be an object')
        for key in FINDING_KEYS[:-1]:
            require(_filled(finding.get(key)), f'A finding is missing {key}')
        require(finding['severity'] in severities,
                f'Unknown severity: {finding["severity"]!r}; use one of {", ".join(severities)}')
        if resolved:
            require(finding['status'] == 'resolved',
                    f'Finding {finding["id"]} is {finding["status"]}; resolve every finding or '
                    'return the ticket, and do not relabel it')
            require(_filled(finding.get('resolution')),
                    f'Finding {finding["id"]} is missing resolution')
        if finding['severity'] in ESCAPING_SEVERITIES:
            require(_filled(finding.get('file')),
                    f'Finding {finding["id"]} is {finding["severity"]} and names no file. A '
                    'finding this serious is what the calibration window measures the review '
                    'triage by, and one nobody can place counts in favour of the narrowing. '
                    'Give it file, as path or path:line')
