"""The change-risk answer the risk decision is judged on.

A gate decision should read evidence rather than impressions, and repowise
computes its answer with no model: percentile against the repository's own
commit distribution, and a test gap from the graph. When it cannot answer, the
absence is recorded as an absence, because a gate that cannot tell a low score
from a missing one is worse than no gate.
"""

import json
import os
import stat
import unittest

from harness import risk
from harness.tests.helpers import ProjectTest

BAND = {'risk_percentile': 59.4, 'review_priority': 'moderate', 'classification': 'Typical',
        'score': 8.9, 'baseline_sample_size': 122, 'ref': 'working tree', 'working_tree': True}

BLAST = {'directive': {'may_break_tests': ['packages/core/src/index.test.ts'],
                       'missing_cochanges': ['packages/core/src/index.test.ts'],
                       'missing_tests': []},
         'pr_blast_radius': {'test_gaps': ['apps/api/src/main.ts', 'tsconfig.base.json'],
                             'test_gaps_total': 2,
                             'structural_impact_band': 'localized'}}

STUB = """#!/bin/sh
for arg in "$@"; do
  if [ "$arg" = "--target" ]; then
    cat <<'JSON'
%s
JSON
    exit 0
  fi
done
cat <<'JSON'
%s
JSON
exit 0
"""


class RiskTest(ProjectTest):

    def stub_repowise(self, body=None):
        binaries = self.root / '.harness-drafts' / 'bin'
        binaries.mkdir(parents=True, exist_ok=True)
        stub = binaries / 'repowise'
        stub.write_text(body if body is not None
                        else STUB % (json.dumps(BLAST), json.dumps(BAND)))
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        (self.root / '.repowise').mkdir(exist_ok=True)
        os.environ['PATH'] = f'{binaries}{os.pathsep}{os.environ["PATH"]}'
        self.addCleanup(lambda: os.environ.__setitem__(
            'PATH', os.environ['PATH'].replace(f'{binaries}{os.pathsep}', '')))

    def test_the_answer_carries_the_percentile_and_the_priority(self):
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertEqual(answer['percentile'], 59.4)
        self.assertEqual(answer['review_priority'], 'moderate')
        self.assertEqual(answer['classification'], 'Typical')

    def test_the_answer_carries_the_test_gap(self):
        """The half of the ticket that is about tests rather than about size."""
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertEqual(answer['test_gaps'], ['apps/api/src/main.ts', 'tsconfig.base.json'])
        self.assertEqual(answer['tests_that_may_break'], ['packages/core/src/index.test.ts'])

    def test_it_names_the_files_it_scored(self):
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIn('packages/core/src/index.ts', answer['changed_files'])

    def test_no_repowise_on_path_is_an_absence_with_a_reason(self):
        """The harness must work on a machine that has never heard of repowise."""
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIsNone(answer['percentile'])
        self.assertIn('repowise', answer['unavailable'])

    def test_no_index_is_an_absence_naming_repowise_init(self):
        self.stub_repowise()
        (self.root / '.repowise').rmdir()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIsNone(answer['percentile'])
        self.assertIn('repowise init', answer['unavailable'])

    def test_nothing_changed_is_an_absence_rather_than_a_score_of_zero(self):
        self.stub_repowise()

        answer = risk.assess(self.root)

        self.assertIsNone(answer['percentile'])
        self.assertIn('no change', answer['unavailable'].lower())

    def test_a_broken_repowise_is_an_absence_rather_than_a_crash(self):
        self.stub_repowise('#!/bin/sh\necho "not json at all"\nexit 0\n')
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIsNone(answer['percentile'])
        self.assertIn('unavailable', answer)


if __name__ == '__main__':
    unittest.main()


class ElidedBlastRadiusTest(RiskTest):
    """repowise elides a large payload and leaves a marker in its place.

    Observed at 23 changed files on 24 September: pr_blast_radius vanished and
    omission_marker appeared. Reporting that as an empty test gap would be the
    silent absence this module exists to refuse, one field down.
    """

    ELIDED = STUB % (json.dumps({'directive': {'may_break_tests': ['a_test.py'],
                                               'missing_cochanges': []},
                                 'omission_marker': '[repowise#abc123]'}),
                     json.dumps(BAND))

    def test_an_elided_blast_radius_is_named_rather_than_read_as_no_gaps(self):
        self.stub_repowise(self.ELIDED)
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIsNone(answer['test_gaps'])
        self.assertIn('[repowise#abc123]', answer['blast_radius_unavailable'])

    def test_the_reason_counts_files_rather_than_command_line_flags(self):
        """One file is four arguments: --target X --changed-file X."""
        self.stub_repowise(self.ELIDED)
        self.write('packages/core/src/index.ts', 'export const x = 1\n')
        self.write('packages/core/src/other.ts', 'export const y = 2\n')

        answer = risk.assess(self.root)

        self.assertIn('2 files', answer['blast_radius_unavailable'])

    def test_the_reason_does_not_repeat_the_expand_command_the_marker_carries(self):
        """repowise's own marker already says how to restore it."""
        self.stub_repowise(self.ELIDED)
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertEqual(answer['blast_radius_unavailable'].count('expand'), 0)

    def test_what_survives_the_elision_is_still_carried(self):
        self.stub_repowise(self.ELIDED)
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertEqual(answer['tests_that_may_break'], ['a_test.py'])
        self.assertEqual(answer['percentile'], 59.4)

    def test_a_full_answer_says_the_blast_radius_was_available(self):
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        answer = risk.assess(self.root)

        self.assertIsNone(answer['blast_radius_unavailable'])


class RiskInTheDecisionTest(RiskTest):
    """What the model sees when it is asked how risky this change is."""

    def state(self):
        from harness import cli
        from harness.repository import Repository
        repository = Repository(self.root)
        records = [dict(sequence=1, ticket='SEEN-001', kind='start', stage='clarify', attempt=1,
                        data=dict(ticket_file=self.ticket_file, ticket_id='SEEN-001',
                                  ticket_snapshot='# snapshot\n'))]
        return cli.state_for(records, dict(stage='clarify', attempt=1),
                             root=repository.root, question='risk')

    def test_the_risk_question_is_given_the_change_risk(self):
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        state = self.state()

        self.assertEqual(state['change_risk']['percentile'], 59.4)
        self.assertEqual(state['change_risk']['test_gaps'],
                         ['apps/api/src/main.ts', 'tsconfig.base.json'])

    def test_an_absent_answer_reaches_the_state_as_an_absence(self):
        """Not as a low score, and not as silence."""
        self.write('packages/core/src/index.ts', 'export const x = 1\n')

        state = self.state()

        self.assertIsNone(state['change_risk']['percentile'])
        self.assertIn('repowise', state['change_risk']['unavailable'])

    def test_no_other_question_is_given_it(self):
        """One extra payload string per question is not free: SEEN-101."""
        from harness import cli
        from harness.repository import Repository
        self.stub_repowise()
        self.write('packages/core/src/index.ts', 'export const x = 1\n')
        records = [dict(sequence=1, ticket='SEEN-001', kind='start', stage='clarify', attempt=1,
                        data=dict(ticket_file=self.ticket_file, ticket_id='SEEN-001',
                                  ticket_snapshot='# snapshot\n'))]

        state = cli.state_for(records, dict(stage='clarify', attempt=1),
                             root=Repository(self.root).root, question='clarified')

        self.assertNotIn('change_risk', state)
