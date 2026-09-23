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

from .errors import require

PHASES_FOR_STAGE = {'tdd': ('red', 'green', 'regression'), 'review': ('qa',)}
TIMEOUT_EXIT = 124         # The timeout(1) convention.
LAUNCH_FAILURE_EXIT = 127  # The command could not be started at all.


def phases_for(stage):
    return PHASES_FOR_STAGE.get(stage, ())


def run(repository, command, phase, timeout, limit):
    """Run one check and return the evidence to record."""
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
                duration_ms=duration_ms,
                output=captured[:limit].decode(errors='replace'),
                output_sha256=hashlib.sha256(captured).hexdigest(),
                output_truncated=len(captured) > limit,
                before=before,
                after=repository.fingerprint())
