"""What GitHub says about a commit and its pull request.

Two readers and nothing else. Both go through gh, which already holds the
authentication: a harness that learns to keep a token is a harness that can leak
one. Both are module-level names so a test replaces them wholesale and no test
reaches the network.

When gh cannot answer, every caller refuses. A delivery that cannot be verified
is not a delivery verified.
"""

import json
import subprocess

from .errors import HarnessError, require

# Replaced in tests. None means "ask gh for real".
CHECKS = None
PULL_REQUEST = None

GREEN = ('success', 'skipped')


def _gh(repository, *args, timeout=120):
    try:
        result = subprocess.run(['gh', *args], cwd=repository.root,
                                capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise HarnessError('gh is not installed, so this delivery cannot be verified. '
                           'Install the GitHub CLI, or deliver from a machine that has it')
    except subprocess.TimeoutExpired:
        raise HarnessError(f'gh did not answer within {timeout}s')
    require(result.returncode == 0,
            f'gh could not answer: {result.stderr.strip() or "no reason given"}. '
            'Run gh auth status, and gh auth login if it is not authenticated')
    return result.stdout


def check_runs(repository, commit):
    """Every check GitHub has run for one commit, with its status and conclusion."""
    if CHECKS is not None:
        return CHECKS(repository, commit)
    output = _gh(repository, 'api', f'repos/{{owner}}/{{repo}}/commits/{commit}/check-runs',
                 '--jq', '[.check_runs[] | {name, status, conclusion}]')
    try:
        return json.loads(output or '[]')
    except json.JSONDecodeError as error:
        raise HarnessError(f'gh answered with something that is not JSON: {error}')


def pull_request(repository):
    """The pull request for the current branch, or a refusal when there is none."""
    if PULL_REQUEST is not None:
        return PULL_REQUEST(repository)
    output = _gh(repository, 'pr', 'view', '--json', 'number,body,headRefName')
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise HarnessError(f'gh answered with something that is not JSON: {error}')


def require_green(repository, commit, what):
    """Refuse unless every check on this commit has concluded green.

    A run still going refuses: a delivery verified against a pending check is
    verified against nothing. No runs at all refuses too, because a commit
    nobody built is not a commit that passed.
    """
    runs = check_runs(repository, commit)
    require(runs,
            f'{commit[:8]} has no checks at all, so there is nothing green about it. '
            f'Push the branch and let CI run before verifying the {what}')
    running = [run['name'] for run in runs if run['status'] != 'completed']
    require(not running,
            f'Checks on {commit[:8]} are still running: {", ".join(running)}. '
            f'Wait for them rather than verifying the {what} against a pending result')
    failed = [f'{run["name"]} ({run["conclusion"]})' for run in runs
              if run['conclusion'] not in GREEN]
    require(not failed, f'Checks on {commit[:8]} did not pass: {", ".join(failed)}')
    return runs
