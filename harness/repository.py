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

    def _blob_ids(self, paths):
        """Git's own hash for files on disk, in one call rather than one each."""
        if not paths:
            return {}
        result = subprocess.run(['git', '-C', str(self.root), 'hash-object', '--stdin-paths'],
                                input='\n'.join(paths), capture_output=True, text=True, timeout=120)
        require(result.returncode == 0, result.stderr.strip() or 'git hash-object failed')
        return dict(zip(paths, result.stdout.split()))

    def fingerprint(self):
        """A hash of the tree's content, ignoring the journal and the drafts.

        Content, not history: committing a file must not change the fingerprint,
        because the receipt has to survive the journal commit that carries it.
        Every entry is a git blob id, so a file hashes the same whether it is
        committed or still sitting in the working tree.
        See docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md.
        """
        entries = {}
        for line in self.git('ls-files', '-s').splitlines():
            details, _, path = line.partition('\t')
            if not path.startswith(FINGERPRINT_EXCLUDED):
                entries[path] = details.split()[1]
        changed = [path for path in sorted(set(self._pending()))
                   if not path.startswith(FINGERPRINT_EXCLUDED)]
        present = [path for path in changed if (self.root / path).is_file()]
        for path in changed:
            entries.pop(path, None)
        entries.update(self._blob_ids(present))
        listing = '\n'.join(f'{path}:{blob}' for path, blob in sorted(entries.items()))
        return hashlib.sha256(listing.encode()).hexdigest()

    def is_clean(self):
        return not [path for path in self._pending() if not path.startswith(FINGERPRINT_EXCLUDED)]

    def is_tracked(self, relative):
        return bool(self.git('ls-files', '--', str(relative)))

    def tracked_and_untracked(self):
        """Every file in the project that git can see, ignored files excluded."""
        listed = self.git('ls-files', '--cached', '--others', '--exclude-standard')
        return [name for name in listed.splitlines() if name]

    def _history_paths(self, filter_letter):
        listed = self.git('log', f'--diff-filter={filter_letter}', '--name-only',
                          '--pretty=format:', '--', str(HISTORY))
        return {name for name in listed.splitlines() if name}

    def rewritten_history_records(self):
        """Journal files git has seen change after the commit that created them.

        The hash chain makes an accidental rewrite detectable and a deliberate
        one expensive; this makes it provable, because recomputing every later
        hash still leaves the modification in history.

        Two shapes count. A record that still exists and was ever committed as a
        modification: the file was edited in place. A record that is gone while
        its journal is still here: one record was removed from a live ticket,
        which the numbering check cannot see when the missing record was the
        last one. Retiring a whole journal, as the Seene project's removal did,
        is neither: the directory is gone and nothing claims otherwise.
        """
        rewritten = [name for name in self._history_paths('M') if (self.root / name).is_file()]
        for name in self._history_paths('D'):
            path = self.root / name
            if not path.exists() and path.parent.is_dir():
                rewritten.append(name)
        return sorted(set(rewritten))

    def default_branch(self):
        """The branch work merges into, asked of git rather than assumed."""
        for reference in ('refs/remotes/origin/HEAD',):
            try:
                return self.git('symbolic-ref', '--short', reference).split('/')[-1]
            except HarnessError:
                continue
        return 'main'

    def is_in_default_branch(self, commit):
        """Whether a commit has already merged, locally or on the remote.

        Both are asked: a delivery merged on the remote but not yet fetched is
        still merged, and a receipt for it is history.
        """
        branch = self.default_branch()
        for reference in (f'origin/{branch}', branch):
            result = subprocess.run(['git', '-C', str(self.root), 'merge-base',
                                     '--is-ancestor', commit, reference],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return reference
        return None

    def contains_commit(self, commit):
        try:
            return self.git('merge-base', '--is-ancestor', commit, 'HEAD') == ''
        except HarnessError:
            return False

    def tip_is_on_remote(self, remote, branch, commit):
        """Whether the remote already holds this commit as the tip of this branch."""
        listed = self.git('ls-remote', '--heads', remote, branch, timeout=120)
        return bool(listed) and listed.split()[0] == commit
