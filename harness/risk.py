"""What repowise says about the change in front of the session.

A risk decision should read evidence rather than impressions. repowise scores a
change against the repository's own commit distribution and reads the test gap
from its graph, both with no model and no key, so the answer costs nothing and
says the same thing twice running.

When it cannot answer, the absence is returned as an absence with the reason.
A gate that cannot tell a low score from a missing one is worse than no gate,
and the harness has to keep working on a machine that has never heard of
repowise.
"""

import json
import subprocess

from .paths import REPOWISE_DIRECTORY

TIMEOUT = 120
# Enough files to characterise a change without turning one decision into a
# survey; repowise itself truncates and says how many it left out.
MAX_TARGETS = 25


def _run(command, root):
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True,
                                   text=True, timeout=TIMEOUT)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


def changed_files(root):
    """What the working tree changes against HEAD, tracked and untracked."""
    tracked = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=root,
                             capture_output=True, text=True)
    untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'],
                               cwd=root, capture_output=True, text=True)
    names = tracked.stdout.split() + untracked.stdout.split()
    return sorted(set(names))


def _absent(reason, files=None):
    return dict(percentile=None, review_priority=None, classification=None,
                score=None, test_gaps=None, tests_that_may_break=None,
                blast_radius_unavailable=None,
                changed_files=files or [], unavailable=reason)


def assess(root):
    """The change-risk answer, or a recorded reason there is none.

    Scored from the working tree rather than from the index, because the index
    is only as fresh as the last `repowise update` and the decision is about the
    change in front of the session.
    """
    files = changed_files(root)
    if not files:
        return _absent('There is no change in the working tree to score', files)
    if not (root / REPOWISE_DIRECTORY).is_dir():
        return _absent(f'No repowise index at {REPOWISE_DIRECTORY}; run repowise init', files)

    band = _run(['repowise', 'risk', '--format', 'json'], root)
    if band is None:
        return _absent('repowise did not answer; it may not be installed, or not on PATH '
                       '(uv tool install --python 3.12 repowise)', files)

    targets = []
    for name in files[:MAX_TARGETS]:
        targets += ['--target', name, '--changed-file', name]
    blast = _run(['repowise', 'risk', *targets, '--format', 'json'], root) or {}
    radius = blast.get('pr_blast_radius') or {}
    directive = blast.get('directive') or {}
    # Past some payload size repowise elides a section and leaves a marker where
    # it was. Twenty-three changed files did it on 24 September. An elided test
    # gap read as an empty one is exactly the silent absence this module exists
    # to refuse, so the marker is carried and the fields stay None.
    elided = None
    if not radius:
        marker = blast.get('omission_marker')
        # One file is four arguments, and the marker carries its own restore
        # instruction, so neither is repeated here.
        elided = (f'repowise elided the blast radius for {len(targets) // 4} files: {marker}'
                  if marker else 'repowise returned no blast radius for this change')

    return dict(percentile=band.get('risk_percentile'),
                review_priority=band.get('review_priority'),
                classification=band.get('classification'),
                score=band.get('score'),
                baseline_sample_size=band.get('baseline_sample_size'),
                structural_impact_band=radius.get('structural_impact_band'),
                test_gaps=radius.get('test_gaps'),
                test_gaps_total=radius.get('test_gaps_total'),
                tests_that_may_break=directive.get('may_break_tests'),
                missing_cochanges=directive.get('missing_cochanges'),
                blast_radius_unavailable=elided,
                changed_files=files,
                source='repowise',
                unavailable=None)
