"""Tests must never touch the journal of the repository they live in.

A test suite that can append to the live journal is a test suite that can forge
evidence, so this is checked rather than assumed.
"""

import tempfile
import unittest

from harness.tests import helpers


class IsolationTest(unittest.TestCase):

    def test_a_project_under_test_is_always_a_temporary_directory(self):
        root, _ = helpers.make_project()
        self.assertTrue(str(root).startswith(tempfile.gettempdir()))
        self.assertNotEqual(root, helpers.PROJECT)

    def test_no_test_writes_a_journal_into_this_repository(self):
        history = helpers.PROJECT / 'docs' / 'harness' / 'history'
        written = [path.name for path in history.glob('SEEN-0*')] if history.is_dir() else []
        self.assertEqual([name for name in written if name in ('SEEN-001', 'SEEN-002')], [],
                         'a test wrote into the live journal')

    def test_the_harness_under_test_is_the_one_in_this_checkout(self):
        self.assertEqual(helpers.HARNESS.name, 'harness')
        self.assertTrue((helpers.HARNESS / 'thresholds.toml').is_file())


class EntryPointTest(unittest.TestCase):
    """run.py must work as a script, which is how every session calls it."""

    def test_the_script_runs_from_the_project_root(self):
        import json
        import subprocess
        import sys
        root, _ = helpers.make_project()
        result = subprocess.run([sys.executable, str(helpers.HARNESS / 'run.py'),
                                 '--root', str(root), 'list'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(tickets=[]))

    def test_a_refusal_goes_to_stderr_with_a_non_zero_exit(self):
        import subprocess
        import sys
        root, _ = helpers.make_project()
        result = subprocess.run([sys.executable, str(helpers.HARNESS / 'run.py'),
                                 '--root', str(root), 'status', 'SEEN-999'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '', 'a refusal must not print a result object')
        self.assertIn('Harness:', result.stderr)

if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
