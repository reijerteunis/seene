"""The edit guard: whether a path may be written now, and why.

Two entry points call `guard.decide` and this file exercises both. `DecideTest`
calls it directly, in process, for every rule and both absence cases; it is the
fast, precise half. `GuardCommandTest` goes through the real entry point with
subprocess, because what a hook reads is the process exit code and stderr text,
and a refusal raised in process proves neither. That subprocess half carries
this slice's RED: before `harness guard` exists, an unknown command already
exits 2 on a usage error, so every assertion here is on the reason text and
never on the exit code alone.

The path shape a payload carries matters to a hook, though this slice builds no
hook. Claude Code's PreToolUse payload carries the path at `tool_input.file_path`,
always absolute; `DecideTest` proves `decide` reads that shape the same way it
reads a person's project-relative one. Codex's own PreToolUse field name is not
established anywhere in this repository: `codex doctor` says nothing about it
and no fixture of it exists yet. Rather than guess a field name silently, this
file uses only the Claude Code shape and leaves the note here for slice 3, which
builds the `hook` dispatcher that will have to settle the Codex shape against a
real Codex session.
"""

import json
import subprocess
import sys
import unittest

from harness import journal, thresholds
from harness.cli import BRANCH
from harness.tests.helpers import HARNESS
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

RUN = HARNESS / 'run.py'

MONEY_SLICE = dict(name='Fee expectations', points=1,
                   files=['packages/core/src/detectors.ts'],
                   red='No fee expectation is computed for an order line')

# A slice that names a directory, which is what a change over every file in a
# workspace honestly describes: SEEN-114's formatter adoption named `apps` and
# `packages` because adopting a formatter rewrites the twenty-six files under
# them. The route verdict has read such an entry as covering what is under it
# since SEEN-104; SEEN-140 is this guard catching up.
PACKAGES_SLICE = dict(name='A formatter over the packages', points=1,
                      files=['packages', 'harness/rules.py'],
                      red='No package is formatted')

# Distinguishes "let decide() work out the branch" from "judge this branch",
# including the detached-HEAD case, which is itself None.
_DEFAULT = object()


def run_cli(root, path):
    """The real entry point, for the exit code and stderr text a hook reads."""
    return subprocess.run([sys.executable, str(RUN), '--root', str(root), 'guard', path],
                         capture_output=True, text=True)


class GuardCommandTest(CommandTest):
    """`harness guard <path>`, through the process every hook and every person calls."""

    def test_a_refusal_at_the_solution_stage_exits_2_and_names_the_stage(self):
        """The RED this slice must demonstrate.

        Before harness/guard.py and the `guard` command exist, this is not a
        command argparse recognises, so it already exits 2, on a usage error
        rather than on this rule. A test asserting only the exit code would
        pass against that harness exactly as it would against this one, which
        is why the assertion that must fail first is on the reason text.
        """
        self.start()
        self.submit('clarify', clarify_evidence())

        result = run_cli(self.root, 'packages/core/src/detectors.ts')

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '', 'a refusal must not print a result object')
        self.assertIn('solution', result.stderr)
        self.assertIn('packages/core/src/detectors.ts', result.stderr)

    def test_a_refusal_at_clarify_names_the_stage_too(self):
        self.start()

        result = run_cli(self.root, 'apps/web/src/status.tsx')

        self.assertEqual(result.returncode, 2)
        self.assertIn('clarify', result.stderr)

    def test_the_ticket_file_is_allowed_at_every_stage(self):
        self.start()
        self.submit('clarify', clarify_evidence())

        result = run_cli(self.root, self.ticket_file)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['rule'], 'always-allowed')

    def test_the_drafts_directory_is_allowed_at_every_stage(self):
        self.start()

        result = run_cli(self.root, '.harness-drafts/notes.md')

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_branch_that_is_not_a_ticket_branch_refuses_code_and_harness(self):
        self.start()
        self.git('checkout', '-q', 'main')

        for path in ('packages/core/src/detectors.ts', 'apps/web/src/status.tsx',
                    'harness/guard.py'):
            with self.subTest(path=path):
                result = run_cli(self.root, path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('not a ticket branch', result.stderr)

    def test_a_branch_that_is_not_a_ticket_branch_allows_paths_the_guard_has_no_rule_for(self):
        self.start()
        self.git('checkout', '-q', 'main')

        result = run_cli(self.root, 'docs/architecture.md')

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_journal_yet_allows_the_edit(self):
        """Before `start`, there is no stage to guard by, and the gate that
        comes next already refuses this absence."""
        result = run_cli(self.root, 'packages/core/src/detectors.ts')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No journal', json.loads(result.stdout)['reason'])

    def test_outside_the_accepted_slice_is_refused_at_tdd(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=[MONEY_SLICE]))

        result = run_cli(self.root, 'apps/web/src/status.tsx')

        self.assertEqual(result.returncode, 2)
        self.assertIn('apps/web/src/status.tsx', result.stderr)

    def test_a_file_the_accepted_slice_names_is_allowed_at_tdd(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=[MONEY_SLICE]))

        result = run_cli(self.root, 'packages/core/src/detectors.ts')

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_file_inside_a_directory_the_slice_names_is_allowed_at_tdd(self):
        """SEEN-140's RED for this reader, which answered no to a question two said yes to.

        `calibration` has read a directory entry as covering what is under it
        since SEEN-104, and the route verdict charges a finding to a slice by
        that reading, so a plan naming `packages` covered
        `packages/core/db/tables.ts` there while this guard refused it. The
        second half of the test is what must hold while the first flips: a path
        under no entry at all is still refused, with the plan's own entries
        named, because a name a session can read is a name it can go and look up
        in the solution record.
        """
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(slices=[PACKAGES_SLICE]))

        inside = run_cli(self.root, 'packages/core/db/tables.ts')
        outside = run_cli(self.root, 'apps/web/src/status.tsx')

        self.assertEqual(inside.returncode, 0, inside.stderr)
        self.assertEqual(outside.returncode, 2)
        self.assertIn('apps/web/src/status.tsx', outside.stderr)
        self.assertIn('packages', outside.stderr)
        self.assertIn('harness/rules.py', outside.stderr)

    def test_no_accepted_slice_plan_allows_the_edit_at_tdd(self):
        """A non-code ticket reaches tdd with no slices to plan by at all."""
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(mode='non-code', slices=[]))

        result = run_cli(self.root, 'packages/core/src/detectors.ts')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No accepted slice plan', json.loads(result.stdout)['reason'])


class DecideTest(CommandTest):
    """`guard.decide` called directly, for every rule and both absence cases.

    The helper resolves the journal the same way `harness guard` does: from
    the branch, never from `self.ticket_id`, so a test naming another ticket's
    branch is judged on that ticket's own, usually absent, journal.
    """

    def decide(self, path, branch=_DEFAULT):
        from harness import guard
        rules = thresholds.load(self.root)
        actual_branch = self.git('branch', '--show-current') if branch is _DEFAULT else branch
        match = BRANCH.match(actual_branch or '')
        folder = (self.root / 'docs' / 'harness' / 'history'
                 / (match.group('ticket') if match else 'no-such-ticket'))
        records = journal.read(folder)
        return guard.decide(self.root, records, actual_branch, path, rules)

    def test_an_absolute_path_is_judged_the_same_as_a_project_relative_one(self):
        """Claude Code's PreToolUse payload carries tool_input.file_path, always
        absolute. A path a person types is project-relative. Both must land on
        the same rule."""
        self.start()
        self.submit('clarify', clarify_evidence())

        relative = self.decide('packages/core/src/detectors.ts')
        absolute = self.decide(str(self.root / 'packages/core/src/detectors.ts'))

        self.assertEqual(relative, absolute)
        self.assertFalse(relative['allowed'])
        self.assertIn('solution', relative['reason'])

    def test_apps_is_refused_at_clarify_the_same_way_packages_is(self):
        self.start()

        decision = self.decide('apps/web/src/status.tsx')

        self.assertFalse(decision['allowed'])
        self.assertIn('clarify', decision['reason'])

    def test_docs_are_not_touched_by_the_stage_rule(self):
        """Only packages/ and apps/ are refused before tdd; a documentation
        ticket writes Markdown at clarify and solution too."""
        self.start()

        decision = self.decide('docs/architecture.md')

        self.assertTrue(decision['allowed'])

    def test_a_stage_the_guard_has_no_rule_for_allows_and_says_so(self):
        """Past tdd there is nothing left in this guard to refuse by: review
        and deliver read the diff and the receipt, not the edit guard."""
        self.start()
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        records = journal.read(folder)
        journal.append(folder, records, kind='advance', stage='tdd', attempt=1,
                       actor='claude:implementer', head=self.git('rev-parse', 'HEAD'),
                       ticket=self.ticket_id,
                       data=dict(from_stage='tdd', to_stage='review', evidence={}, decisions=[]))

        decision = self.decide('packages/core/src/detectors.ts')

        self.assertTrue(decision['allowed'])
        self.assertEqual(decision['rule'], 'no-rule')

    def test_a_branch_naming_a_ticket_with_no_journal_yet_allows(self):
        """Rule 3 asks only whether the branch names some ticket; whether that
        ticket has started is the absence the next rule reads."""
        self.git('checkout', '-q', '-b', 'claude/SEEN-002-something-else')

        decision = self.decide('packages/core/src/detectors.ts',
                               branch='claude/SEEN-002-something-else')

        self.assertTrue(decision['allowed'])
        self.assertEqual(decision['rule'], 'no-journal')

    def test_a_detached_head_refuses_harness_too(self):
        decision = self.decide('harness/guard.py', branch=None)

        self.assertFalse(decision['allowed'])
        self.assertIn('not a ticket branch', decision['reason'])

    def test_a_detached_head_allows_a_path_the_guard_has_no_rule_for(self):
        decision = self.decide('docs/architecture.md', branch=None)

        self.assertTrue(decision['allowed'])


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
