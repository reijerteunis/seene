"""A throwaway project to run harness commands against.

Tests never touch the repository they live in: a test that can append to the
live journal is a test that can forge evidence.
"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HARNESS = Path(__file__).resolve().parents[1]
PROJECT = HARNESS.parent

TICKET = """---
id: SEEN-001
estimate: 2
executor: claude-code
changes_agent_action: false
status: doing
---
# SEEN-001: A ticket to work

## Acceptance criteria

- [ ] Something observable happens
"""


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def make_project(ticket_id='SEEN-001', branch=None):
    """A git repository shaped like Seen: a ticket, the harness files, one commit."""
    root = Path(tempfile.mkdtemp())
    git(root, 'init', '--initial-branch=main')
    git(root, 'config', 'user.email', 'harness@example.test')
    git(root, 'config', 'user.name', 'Harness Test')
    git(root, 'config', 'commit.gpgsign', 'false')
    (root / 'harness').mkdir()
    shutil.copytree(HARNESS / 'templates', root / 'harness' / 'templates')
    shutil.copyfile(HARNESS / 'thresholds.toml', root / 'harness' / 'thresholds.toml')
    (root / '.gitignore').write_text('.harness-drafts/\n.harness.lock\n')
    # The project under test carries the same controls the real one does, so
    # doctor's checks are exercised rather than skipped.
    hooks = root / '.githooks'
    hooks.mkdir()
    hook = hooks / 'pre-commit'
    # A no-op stand-in: doctor checks that the hook exists, is executable and is
    # wired up, and none of that needs gitleaks installed. The real hook is
    # exercised by hand and by CI, not by every unit test.
    hook.write_text('#!/bin/sh\n# stand-in for the real pre-commit hook\nexit 0\n')
    hook.chmod(0o755)
    git(root, 'config', 'core.hooksPath', '.githooks')
    # The skill the drift check compares against, generated the same way sync
    # generates it, so doctor's check is exercised rather than skipped.
    from harness import skills
    source = root / skills.SOURCE
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('# The Seen harness\n\nWork the five stages.\n')
    for relative in skills.COMMITTED:
        copy = root / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(skills.render(source.read_text()))

    tickets = root / 'docs' / 'tickets'
    tickets.mkdir(parents=True)
    ticket_file = tickets / f'{ticket_id}-a-ticket-to-work.md'
    ticket_file.write_text(TICKET.replace('SEEN-001', ticket_id))
    git(root, 'add', '-A')
    git(root, 'commit', '-m', 'chore: project')
    git(root, 'checkout', '-q', '-b', branch or f'claude/{ticket_id}-a-ticket-to-work')
    return root, str(ticket_file.relative_to(root))


class ProjectTest(unittest.TestCase):
    """Base class giving each test its own project and ticket."""

    ticket_id = 'SEEN-001'

    def setUp(self):
        self.root, self.ticket_file = make_project(self.ticket_id)
        self._isolate_from_jev()

    def _isolate_from_jev(self):
        """No test calls the decision API, and none inherits a shell credential.

        A test that could reach Jev would be a test that spends money and gives
        different answers on different days.
        """
        from harness import jev
        for name in jev.CREDENTIAL_NAMES:
            if name in os.environ:
                value = os.environ.pop(name)
                self.addCleanup(os.environ.__setitem__, name, value)
        jev.TRANSPORT = None
        self.addCleanup(setattr, jev, 'TRANSPORT', None)

    def git(self, *args):
        return git(self.root, *args)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path


def add_remote(root):
    """A bare repository to push to, so delivery can be verified without a network."""
    remote = Path(tempfile.mkdtemp()) / 'origin.git'
    subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
    git(root, 'remote', 'add', 'origin', str(remote))
    return remote
