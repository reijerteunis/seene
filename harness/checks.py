"""Running and recording a verification command.

A check is a real subprocess in the project root. The record holds the command,
its exit code, how long it took, its output and a hash of that output, and the
tree fingerprint before and after, so a later stage gate can tell whether the
result is still current and whether the command changed the project while it ran.

SEEN-086 records; SEEN-089 judges. A red that passed is recorded here and
refused there.
"""

import hashlib
import subprocess
import tempfile
import time

from . import sessions
from .errors import require

PHASES_FOR_STAGE = {'tdd': ('red', 'green', 'regression', 'coverage'), 'review': ('qa',)}
TIMEOUT_EXIT = 124         # The timeout(1) convention.
LAUNCH_FAILURE_EXIT = 127  # The command could not be started at all.


def phases_for(stage):
    return PHASES_FOR_STAGE.get(stage, ())


def demonstrates_failure(evidence):
    """Whether a run is evidence that a test failed.

    Exit zero is a passing command, so it claims the opposite. A timeout and a
    command that could not start say nothing about the behaviour under test:
    they are facts about the runner. Only a real non-zero exit from a command
    that ran is a RED.
    """
    return 0 < evidence['exit_code'] < TIMEOUT_EXIT


def run(repository, command, phase, timeout, limit, declared=None):
    """Run one check and return the evidence to record.

    `declared` is the tier the runner says it was spawned on. It is a
    disclosure and not a proof, which is why it is recorded beside the model
    read from the log rather than instead of it: a Claude Code subagent
    inherits its parent's session id, so a check an implementer subagent runs
    resolves to the parent's transcript and observes the parent's model. F1 of
    SEEN-108's second review, and the same position SEEN-105 took for the
    reviewer's session id.
    """
    require(bool(command), 'Supply the check command after --')
    before = repository.fingerprint()
    started = time.monotonic()
    with tempfile.TemporaryFile() as sink:
        try:
            completed = subprocess.run(command, cwd=repository.root, stdout=sink,
                                       stderr=subprocess.STDOUT, timeout=timeout)
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            exit_code = TIMEOUT_EXIT
            sink.write(f'\nThe harness stopped this command after {timeout}s.\n'.encode())
        except OSError as error:
            exit_code = LAUNCH_FAILURE_EXIT
            sink.write(f'The command could not be started: {error}\n'.encode())
        duration_ms = int((time.monotonic() - started) * 1000)
        sink.seek(0)
        captured = sink.read()
    return dict(command=list(command),
                phase=phase,
                exit_code=exit_code,
                # Which model ran it, so the tdd gate can hold a slice to the
                # route it was given. Read here because it can only be read
                # here: the record carries the digest of its session and not
                # the id, so nobody later can find this session's log.
                model=sessions.model(repository.root),
                # What the runner says it was spawned on, when it says anything.
                # The gate compares this first, because it is the only thing on
                # a subagent's side that knows.
                model_declared=declared,
                duration_ms=duration_ms,
                output=captured[:limit].decode(errors='replace'),
                output_sha256=hashlib.sha256(captured).hexdigest(),
                output_truncated=len(captured) > limit,
                before=before,
                after=repository.fingerprint())
