"""Line coverage on the packages the harness holds a floor under.

One fixed measurement, compared with the last delivered figure. A delta needs
two numbers from the same command, so the command is not something a session
hands in: it is this one, and the baseline moves only when a ticket delivers.

The figure has to come from the run that was supposed to produce it. Until
SEEN-112 it did not: the command put the coverage flags after a bare `--`, pnpm
forwarded the separator verbatim, vitest parked every flag behind it and enabled
no coverage, and this module then read the summary file that happened to be on
disk from days before and reported it as the measurement. A gate reading a stale
figure is worse than an absent one, because it reports a control that does not
exist, so a summary older than the run is refused here rather than compared.
"""

import datetime
import json
import time

from .errors import require

# Only packages/core is gated. The other packages carry placeholder tests, and a
# floor under those would measure nothing while looking like a control.
GATED_PACKAGE = '@seen/core'
SUMMARY = 'packages/core/coverage/coverage-summary.json'
from .paths import COVERAGE_BASELINE

BASELINE = str(COVERAGE_BASELINE)
# `exec` and not `test`, and no bare `--`: `pnpm --filter <pkg> test -- <flags>`
# forwards the separator to the package script, so vitest saw `vitest run --
# --coverage.enabled ...` and read none of it. `exec` hands the flags to vitest
# directly. The filter stays, because the summary is read from
# packages/core/coverage/ and the filter is what makes the run happen there.
# Verified both ways at the repository root on 27 September 2026: the old form
# printed no coverage line and left the summary's mtime four days old, this one
# printed "Coverage enabled with v8" and rewrote the file.
DEFAULT_COMMAND = ('pnpm', '--filter', GATED_PACKAGE, 'exec', 'vitest', 'run',
                   '--coverage.enabled', '--coverage.reporter=json-summary')

# How far before the run's start a summary may have been timestamped and still
# count as its output. It is not zero for two reasons that have nothing to do
# with staleness: a filesystem may keep mtime to whole seconds, so a file written
# during the run can carry a timestamp from before it, and the start is derived
# from the run's duration with a git fingerprint taken in between, which moves the
# derived start later than the real one. Seconds of slack, against a stale figure
# that was four days old.
TOLERANCE_SECONDS = 5.0


def baseline(root, package=GATED_PACKAGE):
    """The last delivered figure, or None when nothing has delivered yet."""
    path = root / BASELINE
    if not path.is_file():
        return None
    try:
        stored = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        require(False, f'{BASELINE} is not readable JSON: {error}')
    return stored.get('packages', {}).get(package, {}).get('lines')


def measured(root, not_before=None):
    """The line percentage vitest's json-summary reporter wrote.

    `not_before` is when the run that was supposed to write this file started.
    Given one, a file timestamped before it is refused rather than read: it is
    some earlier run's figure, and reporting it as this one's is the defect
    SEEN-112 found. Left out, the file is read as it stands, which is what a
    caller asking only "what does the summary say" wants.
    """
    path = root / SUMMARY
    require(path.is_file(),
            f'No coverage summary at {SUMMARY}; the measurement command must write one')
    if not_before is not None:
        written = path.stat().st_mtime
        require(written >= not_before - TOLERANCE_SECONDS,
                f'{SUMMARY} is stale: it was last written {_moment(written)}, '
                f'{round(not_before - written)}s before this measurement started, so it is not '
                'what this run produced. The command ran without enabling coverage, or wrote its '
                'summary somewhere else. A stale figure compared against the baseline reports a '
                'control that does not exist, so it is refused rather than recorded')
    try:
        summary = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        require(False, f'{SUMMARY} is not readable JSON: {error}')
    lines = summary.get('total', {}).get('lines', {}).get('pct')
    require(isinstance(lines, (int, float)), f'{SUMMARY} carries no total line percentage')
    return float(lines)


def _moment(epoch):
    """A timestamp a person reading a refusal can compare with a journal record."""
    return (datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
            .isoformat(timespec='seconds'))


def _started(evidence):
    """When the run whose evidence this is began, in wall-clock seconds.

    A check records how long it took and not when it started, and it records
    every phase the same way, so the wall clock is derived here instead: this is
    called on the evidence the moment the command returns, so now minus the
    duration is the start of the run, within the milliseconds between the two.
    An explicit start, if a caller ever has one, is better and is preferred.
    """
    return time.time() - evidence.get('duration_ms', 0) / 1000


def compare(root, evidence, started_at=None):
    """Attach the baseline and the delta to a finished measurement run.

    Refuses before it attaches anything when the summary predates the run, so a
    figure no run produced is never recorded as a measurement: the tdd gate
    counts coverage records, and a refused reading that left one behind would
    still satisfy the gate it was refused by.
    """
    started = _started(evidence) if started_at is None else started_at
    lines = measured(root, not_before=started)
    previous = baseline(root)
    # A first measurement is not a regression: there is nothing to have fallen from.
    delta = None if previous is None else round(lines - float(previous), 4)
    return dict(evidence, package=GATED_PACKAGE, lines=lines, baseline=previous, delta=delta,
                # When the file this figure came from was written, so a later
                # reader never has to take its freshness on trust.
                summary_written=_moment((root / SUMMARY).stat().st_mtime))


def record_baseline(root, lines, package=GATED_PACKAGE):
    """Move the baseline. Called at delivery and nowhere else."""
    path = root / BASELINE
    stored = json.loads(path.read_text()) if path.is_file() else {}
    stored.setdefault('packages', {})[package] = {'lines': lines}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stored, indent=2) + '\n')
    return stored
