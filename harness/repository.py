"""Git access, and the fingerprint that decides whether evidence is still current.

Every fact the harness records about git comes from a real git command here.
Nothing infers repository state from harness files.
"""

import hashlib
from pathlib import Path
import subprocess

from .errors import HarnessError, require
from .paths import FINGERPRINT_EXCLUDED, HISTORY


class Repository:
    """The working copy a harness command operates on."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        require(self.root.is_dir(), f'Project directory does not exist: {self.root}')

    def git(self, *args, timeout=60):
        result = subprocess.run(['git', '-C', str(self.root), *args],
                                capture_output=True, text=True, timeout=timeout)
        require(result.returncode == 0, result.stderr.strip() or f'git {args[0]} failed')
        return result.stdout.rstrip('\n')

    def require_is_root(self):
        """Refuse to operate from a subdirectory or from another repository."""
        toplevel = Path(self.git('rev-parse', '--show-toplevel')).resolve()
        require(toplevel == self.root, f'Run the harness from the git root: {toplevel}')

    def head(self):
        return self.git('rev-parse', 'HEAD')

    def branch(self):
        return self.git('symbolic-ref', '--quiet', '--short', 'HEAD')

    def branch_or_none(self):
        """The branch, or None on a detached HEAD.

        Reporting commands use this, so inspecting an odd state never fails on
        the oddness the operator is inspecting.
        """
        try:
            return self.branch()
        except HarnessError:
            return None

    def file_inside(self, relative):
        """Resolve a project-relative path that must exist inside the project."""
        path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root), f'Path must stay inside the project: {relative}')
        require(path.is_file(), f'File does not exist: {relative}')
        return path

    def _pending(self):
        """Every path git reports as changed, with renames resolved to both sides."""
        output = self.git('status', '--porcelain=v1', '-z', '-uall')
        tokens = [token for token in output.split('\0') if token]
        paths, index = [], 0
        while index < len(tokens):
            entry = tokens[index]
            status, path = entry[:2], entry[3:]
            index += 1
            if status[0] in 'RC' and index < len(tokens):
                paths.append(tokens[index])
                index += 1
            paths.append(path)
        return paths

    def fingerprint(self):
        """A hash of the tree, ignoring the journal and the drafts.

        Recording evidence about a tree must not change that tree, which is why
        docs/harness/history and .harness-drafts are excluded. See
        docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md.
        """
        parts = [self.head()]
        for path in sorted(set(self._pending())):
            if path.startswith(FINGERPRINT_EXCLUDED):
                continue
            full = self.root / path
            content = hashlib.sha256(full.read_bytes()).hexdigest() if full.is_file() else 'absent'
            parts.append(f'{path}:{content}')
        return hashlib.sha256('\n'.join(parts).encode()).hexdigest()

    def is_clean(self):
        return not [path for path in self._pending() if not path.startswith(FINGERPRINT_EXCLUDED)]

    def is_tracked(self, relative):
        return bool(self.git('ls-files', '--', str(relative)))

    def tracked_and_untracked(self):
        """Every file in the project that git can see, ignored files excluded."""
        listed = self.git('ls-files', '--cached', '--others', '--exclude-standard')
        return [name for name in listed.splitlines() if name]

    def rewritten_history_records(self):
        """Journal files that were ever committed as a modification or a deletion.

        The hash chain makes an accidental rewrite detectable and a deliberate
        one expensive; this makes it provable, because recomputing every later
        hash still leaves the modification visible in history.
        """
        changed = self.git('log', '--diff-filter=MD', '--name-only', '--pretty=format:',
                           '--', str(HISTORY))
        return sorted({name for name in changed.splitlines() if name})

    def contains_commit(self, commit):
        try:
            return self.git('merge-base', '--is-ancestor', commit, 'HEAD') == ''
        except HarnessError:
            return False

    def tip_is_on_remote(self, remote, branch, commit):
        """Whether the remote already holds this commit as the tip of this branch."""
        listed = self.git('ls-remote', '--heads', remote, branch, timeout=120)
        return bool(listed) and listed.split()[0] == commit
