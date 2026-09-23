"""Line coverage on the packages the harness holds a floor under.

One fixed measurement, compared with the last delivered figure. A delta needs
two numbers from the same command, so the command is not something a session
hands in: it is this one, and the baseline moves only when a ticket delivers.
"""

import json

from .errors import require

# Only packages/core is gated. The other packages carry placeholder tests, and a
# floor under those would measure nothing while looking like a control.
GATED_PACKAGE = '@seen/core'
SUMMARY = 'packages/core/coverage/coverage-summary.json'
from .paths import COVERAGE_BASELINE

BASELINE = str(COVERAGE_BASELINE)
DEFAULT_COMMAND = ('pnpm', '--filter', '@seen/core', 'test', '--',
                   '--coverage.enabled', '--coverage.reporter=json-summary')


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


def measured(root):
    """The line percentage vitest's json-summary reporter wrote."""
    path = root / SUMMARY
    require(path.is_file(),
            f'No coverage summary at {SUMMARY}; the measurement command must write one')
    try:
        summary = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        require(False, f'{SUMMARY} is not readable JSON: {error}')
    lines = summary.get('total', {}).get('lines', {}).get('pct')
    require(isinstance(lines, (int, float)), f'{SUMMARY} carries no total line percentage')
    return float(lines)


def compare(root, evidence):
    """Attach the baseline and the delta to a finished measurement run."""
    lines = measured(root)
    previous = baseline(root)
    # A first measurement is not a regression: there is nothing to have fallen from.
    delta = None if previous is None else round(lines - float(previous), 4)
    return dict(evidence, package=GATED_PACKAGE, lines=lines, baseline=previous, delta=delta)


def record_baseline(root, lines, package=GATED_PACKAGE):
    """Move the baseline. Called at delivery and nowhere else."""
    path = root / BASELINE
    stored = json.loads(path.read_text()) if path.is_file() else {}
    stored.setdefault('packages', {})[package] = {'lines': lines}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stored, indent=2) + '\n')
    return stored
