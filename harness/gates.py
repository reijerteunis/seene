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
# past the longest ticket on record and keeps the search bounded. It bounds the
# tolerant half of that search too, and squarely: the blobs tried for the path
# the procedure rewrites are the ones it held inside the same window, so the work
# is at most this many hashes of this many listings and no extra git call.
# Measured on this branch at the current limit: the window walk costs 0.32
# seconds in fifty ls-tree calls, and the worst case of the tolerant half, 2,500
# substituted hashes of a 299-path listing, costs 0.07 on top of it, which is
# 0.39 seconds in all. The figures here used to be 0.36 and 0.08, which add to
# 0.44 against a claim of under 0.4: the fifth review caught the arithmetic and
# re-measurement settled every figure above. The longest branch on record is
# nine commits.
TREE_SEARCH_LIMIT = 50
# Why a citation is compared over the whole tree when nothing scopes it. The
# regression is the deliberate case: it covers the suite and not a slice, so it
# has no files to be judged over and never had. The second is the reason of last
# resort, for a caller that named no scope and no reason of its own.
WHOLE_SUITE = ('the regression covers the suite rather than a slice, so there are no files to '
               'scope the comparison to')
UNSCOPED = 'nothing scopes this citation to the code it covered'
# Whose files the comparison was made over, for the refusal to say. A citation
# that names a slice is judged over that slice's files; one that belongs to no
# single slice is judged over every file the plan names, and a session reading
# the refusal needs to know which of the two it met.
BY_THE_SLICE = 'its slice'
BY_THE_PLAN = 'the plan'


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


def _tree_listing(repository, commit):
    """The `path: blob` of a commit's tree over the paths the fingerprint counts."""
    entries = {}
    for line in repository.git('ls-tree', '-r', commit).splitlines():
        details, _, path = line.partition('\t')
        if path and not path.startswith(FINGERPRINT_EXCLUDED):
            entries[path] = details.split()[2]
    return entries


def _fingerprint_of(entries):
    """The hash of such a listing, composed exactly as the repository composes it.

    Separate from the reading of it because the commit search asks the question
    of a listing it has altered by one entry, and the only honest way to compare
    an altered listing with a recorded fingerprint is to hash it the same way. A
    second hashing rule here would be a second answer waiting to disagree.
    """
    listing = '\n'.join(f'{path}:{blob}' for path, blob in sorted(entries.items()))
    return hashlib.sha256(listing.encode()).hexdigest()


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
    return _fingerprint_of(_tree_listing(repository, commit))


def _the_path_the_procedure_rewrites(records, ticket, repository):
    """The one path the harness's own procedure rewrites after a round's checks.

    The ticket file, and nothing else, because nothing else is written by the
    procedure between a check and the commit that carries the work that check
    proved. The workflow requires the `## Outcome`, the frontmatter `status` and
    the criteria ticks before review is left, so the ticket file is guaranteed to
    differ by then; the journal, the drafts, the graph, the coverage baseline and
    the reports are already outside the fingerprint for the neighbouring reason,
    that writing a record about a tree must not change that tree.

    Deliberately narrower than `triage.procedure_paths`, which adds the copies
    `sync` generates whole. Those change when a session runs `sync`, which is part
    of the work and lands in the same commit as the source it is generated from:
    the procedure does not force them to move after the last check of a round, so
    tolerating them would widen the search for nothing. A path is tolerated here
    because the procedure rewrites it at that moment, never because it is
    documentation.

    Resolved the way the review triage resolves it, and by the same function: a
    ticket file carries its title and so changes name when the title does, and
    reading record 1 directly was a defect once already, J3 of SEEN-107's fifth
    review, which excluded a path that was no longer there. None where nothing
    resolves, and None is a licence for nothing: the search stays exactly as
    strict as it was.
    """
    if repository is None or not records:
        return None
    from .cli import ticket_file
    path, _ = ticket_file(records[0].get('data') or {}, ticket, repository.root)
    return path


def _the_commit_holding(repository, tree, rewritten=None):
    """The commit whose content is that tree, if this branch still has one.

    A check records the fingerprint of a tree and not the tree, so which files it
    held is a question only the tree itself answers. What answers it afterwards
    is the commit that carried the work the check proved: one commit later the
    same content is in the history, and its fingerprint says so. Nothing is
    trusted about which commit that is; every candidate is hashed and the one
    that matches is the tree.

    Apart from `rewritten`, the one path the procedure itself rewrites between a
    check and that commit. Without this the search could not succeed at all, and
    that is measured rather than argued: the workflow requires the `## Outcome`,
    the `status` and the criteria ticks in the ticket file before review is left,
    the fingerprint counts the ticket file, so the tree a check ran against is
    never any commit's content. On this ticket's own branch, neither green 35's
    tree nor red 34's is the content of any of the last sixty commits, and green
    35's is `36b3c57`'s content with the ticket file read as it stood at the
    check. Every refusal in this chain traced to a step the harness mandates.

    What is not tolerated is anything else, and that is the whole of the guard:
    the candidate's listing is altered at that one path and nowhere else, so a
    commit differing in the ticket file and in a source file matches nothing. The
    fingerprint is untouched by any of this and still covers the whole ticket
    file, which is what gives the receipt its meaning and what SEEN-109 withdrew
    an attempt to weaken; what has become tolerant is this search and only this
    search.

    A commit holding the tree exactly is preferred to one holding it by
    substitution, which is why the whole window is walked for an exact match
    before any blob is tried. An exact match is the tree, and a reader can check
    it by hand with `git ls-tree`; a substituted match is a reconstruction resting
    on the claim that the only difference is the path the procedure rewrites.
    Where both exist they carry the same code, so preferring the one that needs no
    inference costs nothing and keeps the weaker answer as the fallback it is.

    The candidate blobs are the ones that path held inside the same window, so
    nothing outside the window can be read in and no further git call is made:
    the listings the exact pass already read are what the substitutions are built
    from. That bounds the added work at `TREE_SEARCH_LIMIT` squared hashes and no
    subprocess at all, which is 2,500 hashes of a 299-path listing at the current
    limit, measured at 0.07 seconds against the 0.32 the window walk itself
    costs.

    None when no commit carries it, which is a check whose tree was never
    committed as it stood, and every RED is in that shape: its tree holds the
    test without the code that answers it, and what gets committed is the green.
    That is an absence rather than a difference, and it falls back to the whole
    tree rather than being scoped to a guess.
    """
    listings = {}
    for commit in repository.git('log', '--format=%H', '-n', str(TREE_SEARCH_LIMIT),
                                 'HEAD').split():
        listings[commit] = _tree_listing(repository, commit)
        if _fingerprint_of(listings[commit]) == tree:
            return commit
    if rewritten is None:
        return None
    # Every distinct content that path held in the window, and only those: the
    # listings are already in hand, so the tolerance reads nothing new.
    blobs = list(dict.fromkeys(entries[rewritten] for entries in listings.values()
                               if rewritten in entries))
    # Newest first again, because a dict keeps the order it was filled in: the
    # commit chosen is the one the exact pass would have chosen had the procedure
    # left the ticket file alone.
    for commit, entries in listings.items():
        held = entries.get(rewritten)
        # A path the candidate does not carry at all cannot be substituted into
        # it. Adding or removing a path changes which files exist, which is not
        # the procedure rewriting one of them, so it is not tolerated.
        if held is None:
            continue
        for blob in blobs:
            if blob != held and _fingerprint_of({**entries, rewritten: blob}) == tree:
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
    names it. Nothing for a position no plan names or an entry that names no
    file: each is an absence of scope, and an absence of scope is not an empty
    one. An empty comparison would accept every citation, so it falls back to the
    whole tree instead. Nothing for no position at all, because a round that
    belongs to no single slice is judged over the plan and not over one slice of
    it; `_the_files_the_plan_covers` is that reading, and this function is the
    part of it that reads one position.
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


def _the_files_the_plan_covers(records):
    """Every file the accepted plan's slices cover, or nothing.

    The scope of a round that belongs to no single slice, because such a round
    belongs to the plan rather than to nothing. Record 47 of SEEN-113's own
    journal is the measurement: attempt 4's accepted tdd record declared null for
    the checks it recorded, which is what the template asks a round that touches
    more than one slice's work to declare, and attempt 5 citing that pair was
    compared over the whole tree and refused. Every round after a return that
    corrects work across slices is in that shape, so the rule carried the
    evidence of a tidy single-slice round forward and refused the evidence of
    exactly the rounds a return produces. Treating "several slices" as
    "unknowable" is the same mistake as treating "every slice done" as "no plan
    accepted", which is the defect this ticket started from.

    Each position is read through `_files_the_slice_covers`, so a slice the route
    re-scoped is read from its route here too and the union is exactly what the
    positions would have bought one at a time. Wider than one slice's files and
    narrower than the tree, and wider is stricter: a file any slice names is in
    the comparison, so the round is held to the whole plan and not to the part of
    it somebody says it worked.

    Nothing where no plan is accepted and nothing where no slice of it names a
    file: both are absences of scope rather than empty ones, and an empty
    comparison would accept every citation, so they fall back to the whole tree.
    """
    planned = (latest_evidence(records, 'solution') or {}).get('slices') or []
    covered = set()
    for position in range(1, len(planned) + 1):
        covered.update(_files_the_slice_covers(records, position) or ())
    return sorted(covered) or None


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

    An entry git refuses as a pathspec at all counts here too. `../elsewhere.py`
    and an absolute path outside the working tree make git exit non-zero, and the
    session met `fatal: ... is outside repository` naming a temporary directory
    rather than the sentence every other unresolvable entry gets. An entry git
    will not even take the question about is the strongest form of unresolvable,
    so it costs the scope the same way and is named the same way. F6 of the third
    review.
    """
    unresolved = []
    for path in files:
        try:
            seen = repository.git('ls-tree', '-r', '--name-only', commit, '--', path).strip()
        except HarnessError:
            seen = ''
        if not seen:
            unresolved.append(path)
    return unresolved


def _the_files_the_round_moved(repository, commit, rewritten=None):
    """Which files the commit carrying a check's tree moved, against its parent.

    What the round the check belongs to actually did, read from the history
    rather than from anybody's account of it. A check records the fingerprint of
    the tree it ran against; the commit that carries that content is the commit
    that carried the work, and its diff against its parent is the change that
    work was. No record is consulted and none can bend it: a journal declaring
    the wrong slice does not make git say a different set of files.

    The paths the fingerprint leaves out are left out here too, because the
    comparison is the fingerprint's comparison: counting the journal the commit
    carries would refuse every citation the moment the next record was written.
    And `rewritten` with them, for that same reason one step on. The procedure
    rewrites the ticket file after a round's checks and again after the review,
    so a comparison counting it refuses every citation whatever the code did, and
    the commit this question is asked of is often the commit that rewrote it and
    nothing else: on this ticket's branch green 35's tree is held by a docs commit
    whose own change is the ticket file. A commit that moved only that path did
    not carry the work either, so the question goes to its parent, exactly as it
    does for a commit that moved nothing counted at all. Left out of what the
    round moved, not out of what a plan may name: a slice naming the ticket file
    is still held to it, because that is the plan's own choice and a stricter one.

    A commit that moved no counted file is not the commit that carried the work:
    its parent holds the same content, so the question is asked of the parent,
    and on down while the content stands still. That is the shape every journal
    this harness has written is in, because the records go into the same branch:
    the commit after the work carries the same code and the same fingerprint, and
    being the newer one it is the one found. Measured on SEEN-112, slice 1's green
    ran against a tree carried by `docs(SEEN-112): slice 1 note and the handoff
    pack`, whose own change is one journal record, so without the walk back the
    scoped comparison this ticket exists for was unreachable in every real
    journal. The walk stops at the first commit that moved something, so it never
    collects a later slice's work.

    None where the history cannot answer: the earliest commit holding that content
    is a root commit, whose change has nothing to be a change against. That is an
    absence, and an absence falls closed to the whole tree.
    """
    for _ in range(TREE_SEARCH_LIMIT):
        parents = repository.git('log', '-1', '--format=%P', commit).split()
        if not parents:
            return None
        moved = [path for path
                 in repository.git('diff', '--name-only', parents[0], commit).splitlines()
                 if path.strip() and not path.startswith(FINGERPRINT_EXCLUDED)
                 and path != rewritten]
        if moved:
            return moved
        # No counted path differs, so the parent's content is this commit's
        # content and the check's tree is carried by it too. Nothing is assumed
        # about why: that equality is the same one the fingerprint is made of.
        commit = parents[0]
    return None


def _positions_declared_for(records, number):
    """Which slice of the plan the accepted tdd records say this check proved.

    Every answer found rather than the last one read, so that two records
    disagreeing stays a disagreement: the scope is granted on one answer and on
    nothing else. None stands for a round that declared no position, which is a
    claim that the round belongs to no single slice, and it is read twice. It
    lends no mapping to one slice, so a citation naming a number gets no scope
    from it; and it is the answer a citation declaring null agrees with, so a
    number in this set is what withholds the plan's files from one.
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


def _the_journal_puts_it_elsewhere(records, number, position):
    """The sentence saying an accepted tdd record puts this check at another slice.

    Nothing where no accepted record disagrees, which is either agreement or
    silence, and the two are told apart by the caller and not here: silence is an
    absence and falls closed to the strictest thing the caller has, while a
    disagreement is settled the other way and no comparison can answer it.

    Split out of the scope question because a red needs this answer without the
    files. For a green the two are one: a contradicted position wins no scope, the
    comparison falls back to the whole tree, and the refusal carries the
    disagreement. A red judged by its green has no comparison left to fall back
    to, so the contradiction had nowhere to be spent and passed in silence: a
    slice entry could join one round's red to another round's green and the gate
    took its word for it, although the accepted tdd record of the round that
    recorded the red named a different slice for it. F1 of this ticket's fifth
    review.

    Both directions, because a declaration is a claim whichever value it takes: a
    number the chain contradicts, and a null where the chain named a slice.
    """
    declared = _positions_declared_for(records, number)
    if position is None:
        numbered = sorted(value for value in declared if value is not None)
        if not numbered:
            return None
        named = ', '.join(f'slice {value}' for value in numbered)
        return (f'this record says check {number} belongs to no single slice and the tdd record '
                f'of the round that recorded it named {named}')
    if not declared or declared == {position}:
        return None
    named = ', '.join('no slice at all' if value is None else f'slice {value}'
                      for value in sorted(declared, key=lambda value: (value is None, value)))
    return (f'this record names slice {position} for check {number} and the tdd record of the '
            f'round that recorded it named {named}')


def _the_scope_a_citation_is_judged_in(records, number, position):
    """The files a cited check's evidence is about, whose they are, and why none.

    Three answers and not one: the reason there is no scope is what the refusal
    has to say, and whose files they are is what it has to call them. The position
    is named by the record making the citation, which is exactly why it cannot
    settle the scope by itself: naming another slice's position was all it took to
    be compared against files that had not moved, and the same citation declared
    honestly was refused. F1 of SEEN-113's second review, reproduced end to end.

    So a named position is corroborated from a record that is not the one asking:
    the tdd record of the round that recorded the check, which passed this gate
    when the check was fresh and is in the hash chain since. A check no accepted
    tdd record cites is corroborated by nothing, and a record whose position that
    round contradicts has settled nothing. Both are absences, and an absence fails
    closed to the whole-tree comparison.

    A citation that declares null is a different question and not a missing
    answer. It claims the round belonged to no single slice, which the template
    asks for in as many words, and a round that belongs to no single slice belongs
    to the plan: its files are every file the plan's slices name, read by
    `_the_files_the_plan_covers`. There is nothing to corroborate, because that
    scope rests on no claim the citing record makes: the plan is read from the
    accepted solution record and the rest from git, so no position named here can
    widen it or narrow it, and a round no accepted tdd record mentions reaches it
    too. What is still refused is a null declared where an accepted tdd record
    named a slice for the same check, because that is the same disagreement the
    numbered direction falls closed on, read the other way round: null is a claim,
    a claim the chain contradicts settles nothing, and neither reading wins.

    Both disagreements are answered by `_the_journal_puts_it_elsewhere`, which is
    where the numbered and the null readings of the same contradiction live
    together, and which a red is held to on its own now that its comparison is
    carried by its green.

    This is the plan's half of the answer and not the whole of it. Corroboration
    is a record vouching for a record, and the earlier record's position was
    never itself checked against any code, so the comparison is widened by what
    the round's own commit moved before any citation is accepted; see
    `_require_the_check_is_about_this_code`. What is decided here can only add
    files to that comparison, never take one away.
    """
    declared = _positions_declared_for(records, number)
    # The attribution first, in whichever direction it disagrees: it is the one
    # answer that settles the question rather than leaving it open, and it is the
    # half a red is held to on its own.
    elsewhere = _the_journal_puts_it_elsewhere(records, number, position)
    if elsewhere:
        return None, f'{elsewhere}, so which files it covered is not settled', None
    if position is None:
        files = _the_files_the_plan_covers(records)
        if not files:
            return None, (f'check {number} belongs to no single slice, and nothing in the plan or '
                          'the routes names a file for any slice of it, so there is nothing to '
                          'scope the comparison to'), None
        return files, None, BY_THE_PLAN
    if not declared:
        return None, (f'no accepted tdd record says which slice of the plan check {number} '
                      'proved, so the position this record names for it is corroborated by '
                      'nothing but itself'), None
    files = _files_the_slice_covers(records, position)
    if not files:
        return None, (f'nothing in the plan or the route says which files slice {position} '
                      'covers, so there is nothing to scope the comparison to'), None
    return files, None, BY_THE_SLICE


def _require_the_check_is_about_this_code(record, number, tree, current, repository, scope,
                                          rewritten=None):
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

    `scope` is the files, the reason there are none when there are none, and
    whose files they are when there are: a scope is granted where the journal
    corroborates the slice a citation names, and where a citation names no slice
    it is every file the plan's slices cover. Everything else is an absence that
    falls back to the whole tree. Which of the two granted it is what the refusal
    calls the files, because a round told it was judged against the plan knows to
    look at the plan.

    What the comparison is finally made over is wider than `scope` and is not
    read from any record: the files the round itself moved, from the commit
    carrying the check's tree against its parent, together with the ones its
    slice names. The corroboration held within a round and not across them, where
    the same author's earlier unchecked claim was the authority: a first attempt
    declaring position 2 for the round that proved slice 1 was corroborated by
    itself ever after, the scope became slice 2's untouched files, and a rewrite
    of slice 1 kept its stale evidence, while the same citation declared honestly
    was refused. F1 of the third review, reproduced end to end. The plan's files
    stay in the comparison rather than being replaced by the round's, because a
    slice may name a file its round did not happen to move, and dropping it would
    be a citation newly accepted.

    `rewritten` is the one path the procedure rewrites between a check and the
    commit carrying its work, which both of those readings are told to tolerate
    and nothing else is. It is what makes the scoped comparison reachable at all,
    because until it was tolerated no commit carried any check's tree:
    `_the_path_the_procedure_rewrites` argues for the narrowness of the set and
    `_the_commit_holding` for the guard around the search.
    """
    files, because, named_by = scope
    # Never an empty reason. The whole-tree refusal is the one a reader meets
    # with nothing else to go on, and "because None" is what a caller that
    # passed files and no reason used to leave them with.
    because = because or UNSCOPED
    # And never an unnamed scope, for the same reason: a caller that passed files
    # and did not say whose they are still has a sentence to write about them.
    named_by = named_by or BY_THE_SLICE
    after = record['data'].get('after')
    require(after is not None,
            f'Check {number} was recorded in attempt {record["attempt"]} and this record is '
            f'written in attempt {current["attempt"]}, and the check does not say which tree it '
            'ran against, so nothing here can tell whether its evidence is still about this '
            'code; run it again in this attempt')
    if after == tree:
        return
    commit = _the_commit_holding(repository, after, rewritten) if files and repository else None
    if commit is not None:
        unresolved = _unresolved_in(repository, commit, files)
        moved_by_the_round = _the_files_the_round_moved(repository, commit, rewritten)
        if unresolved:
            because = (f'{named_by} names {", ".join(unresolved)}, which git cannot see in the '
                       'tree it ran against, so a comparison over those names is a comparison '
                       'of nothing')
        elif moved_by_the_round is None:
            because = ('the earliest commit carrying the tree it ran against has no parent for '
                       'its work to be a change against, so which files that round moved cannot '
                       'be read from the history')
        else:
            covered = sorted(set(files) | set(moved_by_the_round))
            moved = _moved_since(repository, commit, covered)
            require(not moved,
                    f'The code check {number} covers has changed since it ran: '
                    f'{", ".join(moved)}. The round that recorded it moved '
                    f'{", ".join(moved_by_the_round)} and {named_by} names {", ".join(files)}, '
                    'and its evidence is about those files as they were, not as they are; run '
                    'it again in this attempt')
            return
    elif files:
        # Which of the two searches came back empty, because a session reading
        # this needs to know whether the tolerance was even in play. A RED's tree
        # is the ordinary case: it holds the test without the code that answers
        # it, and what gets committed is the green.
        because = ('no commit on this branch carries the tree it ran against'
                   + (f', even reading {rewritten} as the procedure rewrote it' if rewritten
                      else '')
                   + ', so which files moved cannot be told')
    require(False,
            f'The tree moved under check {number}: it ran against {after[:12]} and this record '
            f'is written against {tree[:12]}, compared over the whole tree because {because}. '
            'Its evidence is about code this ticket has changed since, so it does not support a '
            'citation here; run it again in this attempt')


def _require_the_pair_is_one_round(position, red, green):
    """A slice's red and its green were recorded in the same attempt.

    The one thing a gate can check of the claim the exemption below rests on.
    Judging a pair by its green lends the green's standing to the red, which is
    honest only where the two halves are the same work, and Ruud's decision at
    record 54 says why they are: a red and the green that follows it in one slice
    entry are one round, so the round the green's commit carries is the red's
    round too. A pair split across a return is not that. Every return increments
    the attempt, and a return is what ends a round, so a red from attempt 2 beside
    a green from attempt 5 is two halves of different work and the red would be
    borrowing a tree it has no claim on.

    Measured before it was required, on every journal under
    `docs/harness/history`: 100 slice entries in accepted tdd records, and all 100
    have their red and their green in the same attempt. So this refuses nothing
    any journal has recorded, and it does not narrow the citation this ticket
    exists for: what has to be old is the pair, not either half of it separately.

    **What ties the halves together, in full.** This rule; the ordering rule,
    which puts the red after the previous entry's green and before its own; the
    route, which holds both halves to the model and the context the position was
    routed to; and the journal's own attribution, which refuses a red an accepted
    tdd record puts at another slice, in `_the_journal_puts_it_elsewhere`. That
    fourth one was being checked all along for every red a tdd record had
    attributed, because the scope the comparison read carried it, and the first
    version of the exemption dropped it while this paragraph went on saying three
    rules were all of them. F1 of the fifth review, whose second half was the
    disclosure and was weighed the same.

    **Where the attribution stops, which is what is not tied.** An accepted tdd
    record can only attribute a check recorded before it, so within one attempt
    there is nothing to attribute the checks a record cites: the record writing
    that attribution is the record being judged. So inside an attempt a session
    may record two rounds and the pairing rests on the record's word, and slice
    B's green cited beside slice A's red there is taken at its word. The nearest
    red before the green is not the missing rule either, and that was measured
    rather than assumed: SEEN-098's green 8 belongs to red 6 with another red
    recorded at 7, so a nearest-red rule would refuse a real pair. Nor is the
    failure reason a check of it: `failure_reason` is prose a reviewer reads
    against the runner's output at the triage, and `triage` says so in as many
    words.
    """
    require(red['attempt'] == green['attempt'],
            f'Slice {position} cites red {red["sequence"]} from attempt {red["attempt"]} beside '
            f'green {green["sequence"]} from attempt {green["attempt"]}. A red and its green are '
            'one round, and a return is what ends a round, so a pair split across one is two '
            'halves of different work: the red is judged by its green here, and a green from '
            'another attempt is not its green. Cite the green of the round that recorded the '
            'red, or the red of the round that recorded the green')


def cited_check(records, number, phase, current, tree=None, repository=None,
                scope=(None, None, None), judged_with=None, declared_position=None):
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
    question is asked over, with the reason there are none and whose files they
    are: the cited check's own slice where the citation names one, and every slice
    of the plan where the round belonged to none.
    Given no tree, only this attempt's own checks count, because a comparison
    with nothing is not one.

    Two refusals and not one, because a gate answering "another attempt" where it
    means "different code" is what made this take five returns to find: there is
    no such check, or the tree moved under the check there is.

    `judged_with` is the pair's green, for a red, and is what makes a pair judged
    once at the half that can be judged. **Ruud's decision, at record 54 of
    SEEN-113's journal, and the measurement that forced it:** a red runs on a tree
    holding the test without the code that answers it, and what gets committed is
    the green, so no commit ever carries a red's tree. None of SEEN-112's five reds
    nor this ticket's red 34 is any commit's content, modulo any single path. So
    the tree test could never pass for a red, and since a slice entry requires both
    halves, every cross-attempt pair fell closed on its red however untouched its
    code was. A red's standing never rested on its tree in the first place: it
    rests on the ordering rule, which reads sequence numbers, and on its own
    recorded failure, which is read from the record two requires below.

    What the red loses is that comparison and nothing else, and the difference is
    the whole of F1 of the fifth review: the first version of this exemption
    skipped the cross-attempt branch entire, and the attribution the scope carried
    went with it, so a slice entry could join one round's red to another round's
    green and be taken at its word. `declared_position` is what puts it back. It
    is the position the citing record declares, read on this path and nowhere
    else, and its default is the null reading, which is the fail-closed one: a
    caller that exempts a red without saying where its record puts it meets the
    refusal a null declaration meets against a journal naming a slice, rather than
    silence.

    **What a red is held to, in full.** A non-zero exit that
    `checks.demonstrates_failure` holds of; its phase and its stage; its place in
    the order; the route of the position its entry declares; the attempt of its
    green, through `_require_the_pair_is_one_round`; and the journal's own
    attribution, through `_the_journal_puts_it_elsewhere`, wherever an accepted
    tdd record has made one. **What is not checked**, said as plainly: the tree it
    ran against, which is the exemption; and the fingerprint it recorded, which is
    not read here at all, because a red that recorded none was recorded beside a
    green that recorded none and the green is refused for both. Where the journal
    has attributed nothing the attribution refuses nothing either, and that is an
    absence the pair has already paid for at the half that can pay: the green
    resolves to no scope for the same silence and is compared over the whole tree.

    The mirror is structural rather than a matter of statement order: the only
    value `judged_with` takes is the green this same function has already returned,
    so a red's citation cannot be written without the green's comparison having run
    and raised. A pair whose green is refused fails as a pair, and a red is never
    citable where its green is not. `_require_the_pair_is_one_round` is what ties
    the two halves to the same work, and is honest about how far that goes.
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
    if judged_with is not None:
        # Never anything but a green, so no caller can exempt a check by handing
        # this the check itself or the regression. The pair's green is confirmed
        # by the time it can be passed here, which is the whole of the mechanism.
        require(phase == 'red' and judged_with['data'].get('phase') == 'green',
                f'Check {number} is cited as a {phase} and judged with check '
                f'{judged_with["sequence"]}, a {judged_with["data"].get("phase")}. Only a red is '
                'judged with its green')
        # Reached by every exempted red and by no other path, because the
        # exemption is this block: what the green stands in for is the tree, and
        # where the journal says the red belongs is not a question about a tree.
        elsewhere = _the_journal_puts_it_elsewhere(records, number, declared_position)
        if elsewhere:
            require(False,
                    f'The journal puts check {number} at another slice: {elsewhere}. A red is '
                    "judged by its green here, which lends it the green's tree and nothing else: "
                    'which slice it proved is still read from the accepted tdd record of the '
                    'round that recorded it, so a red that record puts elsewhere is not this '
                    "round's red. Cite the red of the round that recorded the green, or declare "
                    'the position the journal names for the pair')
    if record['attempt'] != current['attempt'] and judged_with is None:
        # The ticket is read from the record being judged rather than from the
        # start record, because every record carries the ticket it belongs to and
        # the start record of a journal written before a field existed may not.
        _require_the_check_is_about_this_code(
            record, number, tree, current, repository, scope,
            _the_path_the_procedure_rewrites(records, record.get('ticket'), repository))
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
    # not. A round that belonged to no single slice is judged over every file the
    # plan names instead, which is wider and so stricter. The regression is scoped
    # to nothing, because it covers the suite and not a slice: it is held to the
    # whole tree.
    tree = repository.fingerprint()
    regression = cited_check(records, data['regression'], 'regression', current, tree,
                             repository, (None, WHOLE_SUITE, None))
    previous_green = 0
    pairs = []
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
        # The green first, and the red with it in hand: a slice's pair is judged
        # by its green, because a red's tree is unfindable by construction and
        # the pair is one round. `cited_check` argues it and record 54 decided it.
        # Passing the confirmed green is what makes the red's exemption reachable
        # only through the green's comparison, so a pair whose green is refused
        # cannot half survive. The red gets no scope, because with the comparison
        # carried by the green nothing reads one for it, and computing a scope
        # nothing reads is how a reader is left thinking something checks it.
        green = cited_check(records, slice_.get('green'), 'green', current, tree, repository,
                            _the_scope_a_citation_is_judged_in(records, slice_.get('green'),
                                                               declared))
        red = cited_check(records, slice_.get('red'), 'red', current, tree, repository,
                          judged_with=green, declared_position=declared)
        require(previous_green < red['sequence'] < green['sequence'] <= regression['sequence'],
                f'Slice {position} is out of order; each red must precede its green, slices '
                'must not overlap, and the regression must be the last check')
        _require_the_routed_slice(records, slice_, position, (red, green), thresholds)
        previous_green = green['sequence']
        pairs.append((position, red, green))
    # After the ordering pass and not inside it. The ordering rule reads across
    # entries, so it is a property of the whole record: a record whose entries
    # overlap gets the sentence about overlapping, which is the one a session can
    # act on, rather than a sentence about a pair that rule was going to refuse
    # anyway.
    for position, red, green in pairs:
        _require_the_pair_is_one_round(position, red, green)
    return {}


def _require_the_routed_slice(records, slice_, order, checks_cited, thresholds):
    """Which slice of the plan this proved slice is, and then its route.

    The plan position, not the order in this record. They agree only in an
    attempt that re-proves the whole plan in order: a rework attempt proves the
    one slice it reworked, so reading the index would have held it to plan slice
    1's route and, with shadow off, refused work that ran exactly as routed.
    F1 of this ticket's fourth review.

    A slice may declare no position, as null, for a rework round that belongs to
    no single slice. It was held to no route at all, on the reasoning that a
    mapping the record says it does not have cannot be inferred, and that made
    null the cheapest thing a record could declare: it bought the plan's whole
    file union for its scope and paid nothing for the route. It is held to the
    strictest route in the plan instead, argued in
    `_require_the_strictest_route_in_the_plan`. The declaration is required and
    only its value may be empty: left optional, omitting it was a way past the
    refusal that no reader could tell from a record written before the field
    existed. F2 of the fifth review, twice over.
    """
    position = slice_.get('position')
    if position is None:
        _require_the_strictest_route_in_the_plan(records, checks_cited, thresholds)
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


def strictest_route(records, thresholds):
    """The route a round that belongs to no single slice is held to, or nothing.

    The strongest tier any slice of the plan in hand was routed to, and the entry
    carrying it, because a refusal and a handoff pack both have to say whose route
    it is. A tie goes to the earliest slice, which decides only which position is
    named: the tier is the same either way.

    Nothing where no plan is accepted, where no slice of it was routed, and where
    every route names a tier this thresholds file does not: each is an absence, and
    a comparison with nothing is not a comparison. Read by the tdd gate, which
    refuses under it, and by `handoff._rework_line`, which is how it reaches the
    session working the round: a session refused by a rule the pack never told it
    is the thing the pack exists to prevent.
    """
    from . import routing
    order = routing.tiers(thresholds)
    planned = len((latest_evidence(records, 'solution') or {}).get('slices') or [])
    strictest = None
    for position in range(1, planned + 1):
        entry = routing.for_slice(records, position)
        if entry is None or entry.get('model') not in order:
            continue
        if strictest is None or order.index(entry['model']) > order.index(strictest['model']):
            strictest = entry
    return strictest


def _require_the_strictest_route_in_the_plan(records, checks_cited, thresholds):
    """A round that belongs to no single slice answers to every route it may carry.

    F2 of the fifth review. A null position had become the cheapest declaration a
    record could make: it buys the plan's whole file union for its scope, which is
    wider than one slice's files and so stricter, and it returned from here before
    any route comparison was made, so a slice routed to opus and worked on sonnet
    was refused when it declared its position and accepted when it declared null.
    Before the union, a null declaration cost the citation its evidence and fell
    back to the whole tree, which was the counter-pressure; once the scope was
    granted for nothing, the truth was the more expensive thing to say.

    So it is held to the strictest route in the plan, on the same reasoning that
    makes its scope the union rather than nothing: a round that belongs to no
    single slice touches several, and what it must satisfy is what all of them ask.

    A floor and not an equality, which is the one place this departs from
    `_require_the_routed_model`. Under an equality a plan routed to sonnet and to
    opus could be met by neither model, so the rule would be one nobody could
    satisfy and the way out of it would be to name a position the round does not
    have, which is the lie this whole gate is built to make unnecessary. What a
    route guards against is work done under a weaker model than the plan judged
    necessary; a stronger one is a cost, and a round that belongs to no single
    slice has no routed cost of its own to be held to.

    The context of its own with it, because a slice routed at all is routed to one:
    a round that may have touched any of them is not excused by belonging to none.
    Nothing is refused in shadow and nothing without a route to compare against,
    exactly as the numbered rule reads both absences.
    """
    from . import routing
    if routing.shadow(thresholds):
        return
    strictest = strictest_route(records, thresholds)
    if strictest is None:
        return
    order = routing.tiers(thresholds)
    floor = order.index(strictest['model'])
    held_to = (f'Such a round is held to the strictest route in the plan, which is slice '
               f'{strictest["position"]}\'s {strictest["model"]}, or stronger: it may have '
               'touched any slice of the plan, so it answers to the strongest model any of them '
               'was routed to. Declare the position the round really proved, or work it on the '
               "model the plan's strictest slice was routed to")
    for record in checks_cited:
        data = record['data']
        # The declaration first, for the reason the numbered rule reads it first:
        # a Claude Code subagent inherits its parent's session id, so the log of
        # its check carries the parent's model and only the declaration knows.
        declared = data.get('model_declared')
        if declared:
            require(declared in order and order.index(declared) >= floor,
                    f'This record says its round belongs to no single slice, and check '
                    f'{record["sequence"]}, its {data["phase"]}, declared {declared}. {held_to}')
            continue
        ran_on = data.get('model')
        tier = routing.tier_of(thresholds, ran_on) if ran_on else None
        # An id no tier names is an absence and not a weaker model: nothing can
        # place it against the floor, and a comparison with nothing is not one.
        if tier is None or order.index(tier) >= floor:
            continue
        require(False,
                f'This record says its round belongs to no single slice, and check '
                f'{record["sequence"]}, its {data["phase"]}, was recorded under {ran_on}, which '
                f'is {tier}, and declared nothing. {held_to}')
    if any(record['data'].get('agent_declared') for record in checks_cited):
        return
    check_names = ' nor '.join(f'check {record["sequence"]} ({record["data"]["phase"]})'
                               for record in checks_cited)
    require(False,
            f'This record says its round belongs to no single slice, and neither {check_names} '
            'declares an agent. Every slice this plan routed was routed to a context of its own, '
            'and a round that may have touched any of them is not excused by belonging to none: '
            'run the implementer as a subagent and pass its check command --agent <name>, or if a '
            'subagent worked it, declare which check is theirs')


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
