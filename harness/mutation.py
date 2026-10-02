"""The mutation score on the files a slice names, and a killed mutant read as a RED.

SEEN-116. StrykerJS exits 0 whether it killed every mutant or none, so nothing
here reads an exit code for a verdict. Both the score and the RED come from the
JSON report Stryker writes (the mutation-testing-report-schema), which is the
only place the per-file statuses are kept. A report is evidence of a run only
if it was written after that run began, because a stale one on disk would
otherwise stand in for a run that never produced one.

The score follows Stryker's own definition of the detected share: killed and
timed-out mutants over those plus the survivors and the uncovered. A mutant that
did not compile, or was ignored, says nothing about the tests and is left out.
No mutants at all is not applicable and never a score: it is recorded with its
count and `not_applicable`, and the gate lets it pass (Ruud's decision), but it
is never read as a hundred. It is not applicable only when the report lists every
file named, and a directory by at least one file under it: a name the report does
not hold (a typo, a file the branch deleted) measured nothing, and is refused with
no score, whatever the other files scored, rather than recorded as nothing to
measure.

The measurement mirrors `coverage.py` and is as fixed as it: the command is not
something a session hands in beyond the stub a test substitutes.
"""

import json

from .errors import require

PACKAGE_DIRECTORY = 'packages/core/'
SOURCE_DIRECTORY = 'packages/core/src'
PRODUCT_REPORT = 'packages/core/reports/mutation/mutation.json'
FIXTURE_REPORT = 'packages/core/reports/mutation/fixture.json'
REPORTS = (PRODUCT_REPORT, FIXTURE_REPORT)
BASE_COMMAND = ('pnpm', '--filter', '@seen/core', 'mutation')

DETECTED = ('Killed', 'Timeout')
UNDETECTED = ('Survived', 'NoCoverage')


def command(files):
    """The fixed Stryker command, mutating only these files.

    Stryker runs inside packages/core, so the paths it is given are relative to
    it; a path outside that package is not Stryker's to mutate and is refused.
    An entry that is not a .ts file is a directory, and Stryker takes globs, not
    directories, so it becomes the globs of the files under it, tests left out.
    """
    relative = [_relative(path) for path in files]
    require(relative, f'Nothing to mutate: name a file under {SOURCE_DIRECTORY}')
    patterns = []
    for entry in relative:
        if entry.endswith('.ts'):
            patterns.append(entry)
        else:
            directory = entry.rstrip('/')
            patterns += [f'{directory}/**/*.ts', f'!{directory}/**/*.test.ts']
    return BASE_COMMAND + ('--mutate', ','.join(patterns))


def _relative(path):
    require(path.startswith(PACKAGE_DIRECTORY),
            f'{path} is not under {PACKAGE_DIRECTORY}, which is where Stryker runs')
    return path[len(PACKAGE_DIRECTORY):]


def _is_test(path):
    return path.endswith(('.test.ts', '.spec.ts'))


def source_files(paths):
    """The entries that name product source under packages/core/src.

    Those are the files the floor is held over. A fixture, the database tests
    and the harness have no mutation score to hold, and a test file is what does
    the killing rather than what is killed.
    """
    return sorted({path for path in paths
                   if isinstance(path, str)
                   and (path == SOURCE_DIRECTORY or path.startswith(SOURCE_DIRECTORY + '/'))
                   and not _is_test(path)})


def covers(entries, path):
    """Whether a path is one of these entries or sits under a directory among them."""
    return any(path == entry or path.startswith(entry.rstrip('/') + '/') for entry in entries)


def missing(report, files):
    """The entries the report lists no file for: a file not in it, a directory with none under it."""
    listed = _files_of(report)
    return [entry for entry in files
            if not any(covers([entry], path) for path in listed)]


def read(root, relative):
    """One report, or None when it is not there."""
    path = root / relative
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        require(False, f'{relative} is not readable JSON: {error}')


def _files_of(report):
    return {PACKAGE_DIRECTORY + name: entry.get('mutants') or []
            for name, entry in (report.get('files') or {}).items()}


def counts(report, files):
    """How the mutants in these files ended, by the statuses the score uses."""
    found = dict(killed=0, timeout=0, survived=0, no_coverage=0)
    names = dict(Killed='killed', Timeout='timeout', Survived='survived',
                 NoCoverage='no_coverage')
    for path, mutants in _files_of(report).items():
        if not covers(files, path):
            continue
        for mutant in mutants:
            if mutant.get('status') in names:
                found[names[mutant['status']]] += 1
    return found


def score(found):
    """The percentage of the mutants that mattered which the tests caught, or None."""
    detected = found['killed'] + found['timeout']
    total = detected + found['survived'] + found['no_coverage']
    if total == 0:
        return None
    return round(100 * detected / total, 2)


def killed(report):
    """The mutants a report records as Killed, by repository path, as ids."""
    found = {}
    for path, mutants in _files_of(report).items():
        ids = [str(mutant.get('id')) for mutant in mutants if mutant.get('status') == 'Killed']
        if ids:
            found[path] = ids
    return found


def _written_since(root, relative, since):
    path = root / relative
    return path.is_file() and path.stat().st_mtime >= since


def killed_since(root, since):
    """The mutants any report written since `since` records as Killed.

    Empty rather than refused for a run that wrote none, because that is the
    ordinary case for every check that is not a Stryker run: it is the absence
    of this evidence, and the gate is what decides an absence is not a RED.
    """
    found = {}
    for relative in REPORTS:
        if not _written_since(root, relative, since):
            continue
        for path, ids in killed(read(root, relative)).items():
            found.setdefault(path, []).extend(ids)
    return found


def measure(root, evidence, files, floor, since):
    """Attach the score, the counts, the files and the floor to a finished run.

    A run that failed, or that left no fresh product report, measured nothing,
    and says which in `reason` rather than carrying a figure from a report
    nobody can tie to it.
    """
    data = dict(evidence, files=list(files), floor=floor, score=None, mutants=0, reason=None,
                not_applicable=False, missing=[],
                **dict(killed=0, timeout=0, survived=0, no_coverage=0))
    if evidence['exit_code'] != 0:
        return dict(data, reason=f'the Stryker run failed (exit {evidence["exit_code"]}), so '
                                 'no report from it can be trusted')
    if not _written_since(root, PRODUCT_REPORT, since):
        return dict(data, reason=f'the run wrote no report at {PRODUCT_REPORT}')
    document = read(root, PRODUCT_REPORT)
    found = counts(document, files)
    mutants = sum(found.values())
    absent = missing(document, files)
    data = dict(data, **found, mutants=mutants, score=score(found), missing=absent)
    if absent:
        # Refused whatever the other files scored: a score over the files the report
        # does hold would let a typo or a deleted file through on their figure. The
        # counts stay on the record for reading.
        return dict(data, score=None,
                    reason='the report lists no file for ' + ', '.join(absent)
                           + ', so it measured nothing there: a typo or a file the '
                             'branch deleted')
    if mutants:
        return data
    # Ruud's decision on SEEN-116: a run that completed and found no mutants in
    # files the report does list is recorded as not applicable, with the count
    # and no score, and the gate lets it pass. Only this case: a run that failed
    # or wrote no report, or a name the report lacks, has no score either and is
    # not this.
    return dict(data, not_applicable=True,
                reason='no mutants in the files named, so the score is not applicable')
