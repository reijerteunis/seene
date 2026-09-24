"""One ticket from start to delivered, through the commands a session runs."""

import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

from harness import cli
from harness.errors import HarnessError
from harness.tests.helpers import ProjectTest, make_project

PROJECT = Path(__file__).resolve().parents[2]


class CommandTest(ProjectTest):
    """Runs commands in process, which is how the tests stay fast and readable."""

    def run_harness(self, *args):
        return cli.execute(cli.parse(['--root', str(self.root), *args]))

    def start(self, actor='claude:implementer'):
        return self.run_harness('start', self.ticket_id, '--ticket', self.ticket_file,
                                '--actor', actor)

    def records(self):
        folder = self.root / 'docs' / 'harness' / 'history' / self.ticket_id
        return [json.loads(path.read_text()) for path in sorted(folder.glob('[0-9]*.json'))]

    def submit(self, stage, data, actor='claude:implementer', **changes):
        relative = f'.harness-drafts/{self.ticket_id}-{stage}.json'
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(data, **changes)))
        return self.run_harness('advance', self.ticket_id, '--file', relative, '--actor', actor)


class StartTest(CommandTest):

    def test_start_writes_the_first_record_at_clarify(self):
        record = self.start()
        self.assertEqual(record['sequence'], 1)
        self.assertEqual(record['stage'], 'clarify')
        self.assertEqual(record['kind'], 'start')
        self.assertIsNone(record['prev_hash'])
        self.assertEqual(record['data']['ticket_file'], self.ticket_file)

    def test_start_snapshots_the_whole_ticket(self):
        record = self.start()
        self.assertIn('## Acceptance criteria', record['data']['ticket_snapshot'])

    def test_a_ticket_may_not_be_started_twice(self):
        self.start()
        with self.assertRaisesRegex(HarnessError, 'already'):
            self.start()

    def test_an_unknown_ticket_file_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'does not exist'):
            self.run_harness('start', self.ticket_id, '--ticket', 'docs/tickets/nope.md',
                             '--actor', 'claude:implementer')

    def test_an_unknown_actor_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'actor'):
            self.start(actor='gemini:implementer')

    def test_an_actor_without_a_role_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'actor'):
            self.start(actor='claude')

    def test_a_ticket_id_of_the_wrong_project_is_refused(self):
        with self.assertRaisesRegex(HarnessError, 'SEEN'):
            self.run_harness('start', 'SEENE-001', '--ticket', self.ticket_file,
                             '--actor', 'claude:implementer')


class BranchTest(CommandTest):

    def test_a_writing_command_is_refused_on_another_ticket_s_branch(self):
        self.git('checkout', '-q', '-b', 'claude/SEEN-002-something-else')
        with self.assertRaisesRegex(HarnessError, 'branch'):
            self.start()

    def test_a_writing_command_is_refused_on_main(self):
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(HarnessError, 'branch'):
            self.start()

    def test_a_codex_branch_is_accepted(self):
        self.git('checkout', '-q', '-b', f'codex/{self.ticket_id}-a-ticket-to-work')
        self.assertEqual(self.start()['sequence'], 1)

    def test_status_still_works_on_the_wrong_branch(self):
        self.start()
        self.git('checkout', '-q', 'main')
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'clarify')


class StatusTest(CommandTest):

    def test_status_reports_where_the_ticket_stands(self):
        self.start()
        status = self.run_harness('status', self.ticket_id)
        self.assertEqual(status['stage'], 'clarify')
        self.assertEqual(status['attempt'], 1)
        self.assertEqual(status['last_actor'], 'claude:implementer')
        self.assertEqual(status['branch'], f'claude/{self.ticket_id}-a-ticket-to-work')
        self.assertIn('draft', status['next_command'])
        self.assertEqual(len(status['chain_head']), 64)

    def test_status_never_fingerprints_the_tree(self):
        self.start()
        calls = []
        repository_git = cli.Repository.git

        def counting_git(repository, *args, **named):
            calls.append(args[0])
            return repository_git(repository, *args, **named)

        cli.Repository.git = counting_git
        try:
            self.run_harness('status', self.ticket_id)
        finally:
            cli.Repository.git = repository_git
        self.assertNotIn('status', calls, 'status must not fingerprint the tree')
        self.assertLessEqual(len([call for call in calls if call != 'rev-parse']), 2)

    def test_status_stays_well_inside_its_budget(self):
        self.start()
        for _ in range(20):
            self.write('.harness-drafts/note.md', 'A thought.')
            self.run_harness('note', self.ticket_id, '--file', '.harness-drafts/note.md',
                             '--actor', 'claude:implementer')
        started = time.monotonic()
        self.run_harness('status', self.ticket_id)
        elapsed = time.monotonic() - started
        # The design budget is 200 ms. The assertion is loose on purpose: a tight
        # wall-clock check in CI is flaky by construction, and the properties that
        # keep status fast are asserted in the test above.
        self.assertLess(elapsed, 1.0, f'status took {elapsed * 1000:.0f} ms')

    def test_status_of_an_unstarted_ticket_says_so(self):
        with self.assertRaisesRegex(HarnessError, 'start it first'):
            self.run_harness('status', self.ticket_id)


class DraftTest(CommandTest):

    def test_draft_copies_the_template_into_the_drafts_directory(self):
        self.start()
        result = self.run_harness('draft', self.ticket_id)
        draft = self.root / result['draft']
        self.assertTrue(draft.is_file())
        self.assertIn('scope', json.loads(draft.read_text()))

    def test_draft_refuses_to_overwrite_work_in_progress(self):
        self.start()
        self.run_harness('draft', self.ticket_id)
        with self.assertRaisesRegex(HarnessError, 'already'):
            self.run_harness('draft', self.ticket_id)

    def test_draft_offers_the_non_code_template_on_request(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        result = self.run_harness('draft', self.ticket_id, '--non-code')
        self.assertEqual(json.loads((self.root / result['draft']).read_text())['mode'], 'non-code')

    def test_a_successful_advance_removes_the_draft(self):
        self.start()
        result = self.run_harness('draft', self.ticket_id)
        draft = self.root / result['draft']
        draft.write_text(json.dumps(clarify_evidence()))
        self.run_harness('advance', self.ticket_id, '--file', result['draft'],
                         '--actor', 'claude:implementer')
        self.assertFalse(draft.exists(), 'a leftover draft can be edited and resubmitted')


class NoteAndCheckTest(CommandTest):

    def test_a_note_is_recorded_at_the_current_stage(self):
        self.start()
        self.write('note.md', 'Bol answers commissions on cancellations within 24 hours.')
        record = self.run_harness('note', self.ticket_id, '--file', 'note.md',
                                  '--actor', 'human:implementer')
        self.assertEqual(record['kind'], 'note')
        self.assertEqual(record['stage'], 'clarify')
        self.assertIn('Bol answers', record['data']['text'])

    def test_an_empty_note_is_refused(self):
        self.start()
        self.write('note.md', '   \n')
        with self.assertRaisesRegex(HarnessError, 'empty'):
            self.run_harness('note', self.ticket_id, '--file', 'note.md',
                             '--actor', 'claude:implementer')

    def test_a_check_records_the_command_its_exit_code_and_its_output(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        record = self.run_harness('check', self.ticket_id, '--phase', 'red',
                                  '--actor', 'claude:implementer',
                                  '--', 'sh', '-c', 'echo expected 250, received 0; exit 1')
        self.assertEqual(record['data']['exit_code'], 1)
        self.assertEqual(record['data']['phase'], 'red')
        self.assertIn('expected 250', record['data']['output'])
        self.assertEqual(len(record['data']['output_sha256']), 64)
        self.assertGreaterEqual(record['data']['duration_ms'], 0)

    def test_a_failing_check_is_still_recorded(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.run_harness('check', self.ticket_id, '--phase', 'green',
                         '--actor', 'claude:implementer', '--', 'false')
        self.assertEqual(self.records()[-1]['data']['exit_code'], 1,
                         'a failed check is a fact about the work, not a typo')

    def test_a_check_phase_that_does_not_belong_to_the_stage_is_refused(self):
        self.start()
        with self.assertRaisesRegex(HarnessError, 'clarify'):
            self.run_harness('check', self.ticket_id, '--phase', 'red',
                             '--actor', 'claude:implementer', '--', 'true')


class AdvanceTest(CommandTest):

    def test_advance_records_the_evidence_and_moves_the_stage(self):
        self.start()
        record = self.submit('clarify', clarify_evidence())
        self.assertEqual(record['kind'], 'advance')
        self.assertEqual(record['stage'], 'clarify')
        self.assertEqual(record['data']['to_stage'], 'solution')
        self.assertEqual([d['question'] for d in record['data']['decisions']],
                         ['clarified', 'risk'])
        self.assertEqual({d['source'] for d in record['data']['decisions']}, {'unavailable'},
                         'with no credential the judgement is recorded as not made')
        self.assertEqual(self.run_harness('status', self.ticket_id)['stage'], 'solution')

    def test_a_refused_advance_leaves_no_record(self):
        self.start()
        with self.assertRaises(HarnessError):
            self.submit('clarify', clarify_evidence(), open_questions=['Still unsure'])
        self.assertEqual(len(self.records()), 1, 'a rejected evidence file is a typo, not a fact')

    def test_evidence_that_is_not_json_is_refused(self):
        self.start()
        self.write('.harness-drafts/broken.json', '{oops')
        with self.assertRaisesRegex(HarnessError, 'JSON'):
            self.run_harness('advance', self.ticket_id, '--file', '.harness-drafts/broken.json',
                             '--actor', 'claude:implementer')

    def test_evidence_written_outside_the_drafts_directory_is_refused(self):
        self.start()
        self.write('clarify.json', json.dumps(clarify_evidence()))
        with self.assertRaisesRegex(HarnessError, 'harness-drafts'):
            self.run_harness('advance', self.ticket_id, '--file', 'clarify.json',
                             '--actor', 'claude:implementer')

    def test_the_chain_holds_across_every_record(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        self.assertEqual([record['sequence'] for record in self.records()], [1, 2, 3])
        self.assertEqual(self.run_harness('history', self.ticket_id)[-1]['stage'], 'solution')


class ReturnTest(CommandTest):

    def test_a_return_raises_the_attempt_and_moves_the_stage_back(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        record = self.run_harness('return', self.ticket_id, '--to', 'clarify',
                                  '--reason', 'The scope covers two marketplaces, not one',
                                  '--actor', 'codex:reviewer')
        self.assertEqual(record['stage'], 'tdd', 'a record is stamped with the stage it left')
        self.assertEqual(record['data']['to_stage'], 'clarify')
        status = self.run_harness('status', self.ticket_id)
        self.assertEqual((status['stage'], status['attempt']), ('clarify', 2))

    def test_a_return_may_not_go_forwards(self):
        self.start()
        with self.assertRaisesRegex(HarnessError, 'before'):
            self.run_harness('return', self.ticket_id, '--to', 'solution',
                             '--reason', 'Skipping ahead', '--actor', 'codex:reviewer')

    def test_a_return_to_a_stage_that_takes_no_returns_is_refused(self):
        self.start()
        with self.assertRaisesRegex(HarnessError, 'targets one of'):
            self.run_harness('return', self.ticket_id, '--to', 'review',
                             '--reason', 'x', '--actor', 'codex:reviewer')


def clarify_evidence(**changes):
    data = dict(scope='Prove the harness records a ticket end to end.',
                acceptance=['The journal holds one record per stage'],
                decisions=['Recorded by the harness itself, per SEEN-086'],
                open_questions=[],
                changes_agent_action=False,
                graph_impact=[])
    data.update(changes)
    return data


def solution_evidence(**changes):
    data = dict(mode='code',
                approach='Write the records, then read them back.',
                changes=['harness/journal.py: append and read'],
                migrations=[],
                tests_first=['test_journal.py: a chain that does not verify is refused'],
                alternatives=['A single JSONL file, rejected because a gap is invisible'],
                risks=['A crash mid-write; mitigated by writing aside and linking'],
                rollback='Revert the commit; the journal is additive.',
                new_dependencies=[],
                tenant_tables=['none'],
                buyer_pii='none',
                policy_gate_action=None)
    data.update(changes)
    return data


if __name__ == '__main__':
    unittest.main()
