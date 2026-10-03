"""The edit guard: whether a path may be written, and why.

Early enforcement of rules the stage gates already hold, so a wrong edit is
refused before it is made rather than found afterwards in a review. `decide` is
a pure function of the path, the branch, the journal's stage and the accepted
slice's files; nothing about a hook reaches it, which is what lets a person run
`harness guard <path>` and a lifecycle hook call the same answer.

Four rules and no fifth, in the order they are read: the ticket file and
.harness-drafts/ are allowed at every stage; packages/ and apps/ are refused at
clarify and solution; a branch that is not a ticket branch refuses an edit to
packages/, apps/ or harness/; at tdd, a path outside the accepted slice's files
is refused, and once every slice is done, a path outside the whole plan's files.
A slice entry that names a directory covers the files inside it, through
paths.covers, the one reader of that question since SEEN-140. Absence
allows and says why: no journal for the branch's ticket, or no slice plan
accepted at all. A guard that refused on absence would refuse the first edit of
every ticket, this one included, and the gate that comes next already refuses
that absence. Absence is only ever those two, never a plan already worked
through: SEEN-112's record 42 found the two read as one, which stopped the guard
guarding in the phase it matters most.
"""

from pathlib import Path

from . import handoff, journal
from .paths import DRAFTS, covers

# packages/ and apps/ are the code the clarify and solution stages must not
# touch yet; harness/ joins them for the branch rule, because a harness file
# written from the wrong branch is evidence recorded about the wrong ticket.
CODE_PREFIXES = ('packages/', 'apps/')
GUARDED_PREFIXES = CODE_PREFIXES + ('harness/',)
STAGES_BEFORE_CODE = ('clarify', 'solution')


def _relative(root, path):
    """The path as the rules read it: project-relative, forward slashes.

    A hook payload carries an absolute path (Claude Code's tool_input.file_path
    does); a person typing `harness guard` types a project-relative one. Both
    arrive here and both are judged the same way.

    Literally first and then with both sides resolved, because a symlinked parent
    makes two strings of one file: /var is a link to /private/var on macOS, and a
    payload carrying the form the root does not have would be read as a path
    outside the project, match no slice file and refuse every edit that session
    made. Genuinely outside the project it is judged on its own text, since there
    is nothing to make it relative to.
    """
    candidate = Path(path)
    if candidate.is_absolute():
        for inside, outside in ((candidate, Path(root)),
                                (candidate.resolve(), Path(root).resolve())):
            try:
                return inside.relative_to(outside).as_posix()
            except ValueError:
                continue
        return candidate.as_posix()
    return candidate.as_posix()


def _allow(rule, reason):
    return dict(allowed=True, rule=rule, reason=reason)


def _refuse(rule, reason):
    return dict(allowed=False, rule=rule, reason=reason)


def _under_any(relative, prefixes):
    return any(relative.startswith(prefix) for prefix in prefixes)


def _is_ticket_file(records, relative):
    return bool(records) and records[0]['data'].get('ticket_file') == relative


def decide(root, records, branch, path, rules):
    """Whether `path` may be written now, and why.

    `records` is the branch's own ticket's journal, already read by the caller;
    an empty list means either the branch names no ticket or that ticket has
    not started. `rules` is unused today and is here for the questions a later
    rule might ask of thresholds.toml, the way every other rule in this harness
    does.
    """
    del rules
    relative = _relative(root, path)

    # Rule 1: the ticket file and the drafts directory, at every stage.
    if relative.startswith(f'{DRAFTS}/') or _is_ticket_file(records, relative):
        return _allow('always-allowed',
                       f'{relative} is the ticket file or a draft, allowed at every stage')

    from .cli import BRANCH
    match = BRANCH.match(branch or '')

    # Rule 3, the half of it that needs no journal: a branch that names no
    # ticket at all refuses code and harness edits outright.
    if match is None:
        if _under_any(relative, GUARDED_PREFIXES):
            return _refuse('non-ticket-branch',
                            f'{branch or "a detached HEAD"} is not a ticket branch, so an edit to '
                            f'{relative} is refused; branch onto claude/<ticket>-<slug> or '
                            'codex/<ticket>-<slug> first')
        return _allow('non-ticket-branch',
                       f'{branch or "a detached HEAD"} is not a ticket branch, but {relative} is '
                       'outside packages/, apps/ and harness/, so this guard has no rule against it')

    # Absence: the ticket the branch names has no journal yet.
    if not records:
        return _allow('no-journal',
                       f'No journal yet for {match.group("ticket")}; nothing to guard {relative} '
                       'against until it starts')

    current = journal.state(records)
    stage = current['stage']

    # Rule 2: packages/ and apps/ are not written before tdd.
    if stage in STAGES_BEFORE_CODE and _under_any(relative, CODE_PREFIXES):
        return _refuse('stage',
                        f'{relative} is under packages/ or apps/, which is refused while '
                        f'{match.group("ticket")} is at the {stage} stage')

    if stage == 'tdd':
        slice_ = handoff.current_slice(records, current)
        # Genuine absence, and the only one: no plan has been accepted at all,
        # which is where a non-code ticket reaches tdd. There is nothing to
        # compare a path against, so the permissive answer stands.
        if slice_ is None:
            return _allow('no-slice-plan',
                           f'No accepted slice plan yet for {match.group("ticket")}; nothing to '
                           f'guard {relative} against')
        entry = slice_['entry']
        # Rule 4: outside the slice this session was handed. `covers` is the one
        # reader of that question, so a plan naming a directory covers what is
        # under it here exactly as it does for the route verdict and the triage;
        # before SEEN-140 this comparison was its own, and exact.
        if entry is not None:
            if not covers(relative, entry['files']):
                files = ', '.join(entry['files']) or 'none named'
                return _refuse('outside-slice',
                                f'{relative} is not one of the files slice {slice_["position"]} '
                                f'of {slice_["total"]} names: {files}')
        else:
            # Every slice in the plan is done, which is a different situation
            # from having no plan and was read as the same one until SEEN-112:
            # on SEEN-008, three slices of three done, this answered allowed for
            # a path no slice named. It is also the state a ticket is in after a
            # review returns it, when rework happens and a session is most
            # likely to touch a file the plan never mentioned.
            #
            # The fallback is the union of every slice's files rather than the
            # last slice's, because a review returns a ticket on a finding in
            # whichever slice carried it, usually not the last, so rework is
            # work on any file the plan named. A fallback to the last slice
            # alone would refuse the edit the return asked for, and a rule a
            # session cannot satisfy is the rule that teaches people to write
            # through a shell instead, which is defect 2 of the same record.
            named = [name for other in handoff.plan_of(records) for name in other['files']]
            if not covers(relative, named):
                files = ', '.join(dict.fromkeys(named)) or 'none named'
                return _refuse('outside-plan',
                                f'All {slice_["total"]} slices of {match.group("ticket")} are '
                                f'done, and {relative} is not one of the files the plan names: '
                                f'{files}. Rework stays inside the plan; a file outside it needs '
                                'a return to solution and a slice that names it')

    return _allow('no-rule', f'No rule in this guard refuses {relative} at the {stage} stage')
