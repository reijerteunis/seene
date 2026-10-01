"""The self-check a session runs before it starts working."""

import unittest
import json

from harness import doctor, journal as journal_module, thresholds
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.test_lifecycle import CommandTest, clarify_evidence


class DoctorTest(CommandTest):

    def report(self):
        repository = Repository(self.root)
        return doctor.report(repository, thresholds.load(self.root))

    def commit(self, message='docs: record'):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def test_a_healthy_project_passes(self):
        self.start()
        report = self.report()
        self.assertTrue(report['ok'], report['problems'])

    def test_it_names_the_ticket_whose_chain_is_broken(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        record.write_text(record.read_text().replace('claude:implementer', 'codex:reviewer'))
        report = self.report()
        self.assertFalse(report['ok'])
        self.assertTrue(any(self.ticket_id in problem and 'chain' in problem
                            for problem in report['problems']), report['problems'])

    def test_it_fails_when_a_record_was_committed_as_a_modification(self):
        self.start()
        self.commit()
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        content = json.loads(record.read_text())
        content['actor'] = 'codex:reviewer'
        record.write_text(json.dumps(content, indent=2) + '\n')
        self.commit('docs: quietly rewrite the record')
        problems = self.report()['problems']
        self.assertTrue(any('0001.json' in problem and 'history' in problem
                            for problem in problems), problems)

    def test_it_fails_when_a_record_was_removed_from_a_live_journal(self):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.commit()
        (self.root / 'docs/harness/history' / self.ticket_id / '0002.json').unlink()
        self.commit('docs: drop the last record')
        problems = self.report()['problems']
        self.assertTrue(any('0002.json' in problem for problem in problems), problems)

    def test_retiring_a_whole_journal_is_not_a_rewrite(self):
        self.start()
        self.commit()
        import shutil
        shutil.rmtree(self.root / 'docs/harness/history' / self.ticket_id)
        self.commit('chore: retire the previous project')
        self.assertTrue(self.report()['ok'], self.report()['problems'])

    def test_it_fails_on_a_stray_file_beside_the_records(self):
        self.start()
        (self.root / 'docs/harness/history' / self.ticket_id / '0001.json.bak').write_text('{}')
        self.assertTrue(any('0001.json.bak' in problem for problem in self.report()['problems']))

    def test_it_fails_on_a_markdown_link_that_does_not_resolve(self):
        self.write('docs/guide.md', 'See the [ticket](SEEN-999-nothing.md) for detail.\n')
        problems = self.report()['problems']
        self.assertTrue(any('docs/guide.md:1' in problem for problem in problems), problems)

    def test_it_ignores_links_inside_code_fences_and_to_the_web(self):
        self.write('docs/guide.md',
                   'A [live link](https://example.test/x).\n\n```\n[not a link](nope.md)\n```\n')
        self.assertTrue(self.report()['ok'], self.report()['problems'])

    def test_it_fails_when_the_drafts_directory_is_not_ignored(self):
        self.write('.gitignore', '\n')
        problems = self.report()['problems']
        self.assertTrue(any('.harness-drafts' in problem for problem in problems), problems)

    def test_it_fails_on_a_template_that_is_not_readable(self):
        self.write('harness/templates/review.json', '{oops')
        problems = self.report()['problems']
        self.assertTrue(any('review.json' in problem for problem in problems), problems)

    def test_it_reports_every_problem_rather_than_the_first(self):
        self.write('.gitignore', '\n')
        self.write('harness/templates/review.json', '{oops')
        self.write('docs/guide.md', 'A [broken link](nowhere.md).\n')
        self.assertGreaterEqual(len(self.report()['problems']), 3)

    def test_it_refuses_a_python_below_the_floor(self):
        self.assertEqual(doctor.python_problems((3, 14, 0)), [])
        self.assertTrue(doctor.python_problems((3, 11, 9)))

    def test_the_command_exits_non_zero_when_something_is_wrong(self):
        self.write('.gitignore', '\n')
        with self.assertRaisesRegex(HarnessError, 'self-check'):
            self.run_harness('doctor')

    def test_the_command_passes_on_a_healthy_project(self):
        self.assertTrue(self.run_harness('doctor')['ok'])


class AppendOnlyScopeTest(DoctorTest):
    """Records are append-only. The files beside them are not records."""

    def test_a_rewritten_kpi_cache_is_not_a_rewritten_record(self):
        self.start()
        self.write('docs/harness/history/' + self.ticket_id + '/kpi.json', '{"ticket": "a"}')
        self.commit()
        self.write('docs/harness/history/' + self.ticket_id + '/kpi.json', '{"ticket": "b"}')
        self.commit('docs: the ticket delivered again, so its figures changed')

        report = self.report()
        self.assertTrue(report['ok'], report['problems'])

    def test_a_rewritten_record_is_still_caught(self):
        self.start()
        self.commit()
        record = self.root / 'docs/harness/history' / self.ticket_id / '0001.json'
        record.write_text(record.read_text().replace('claude:implementer', 'codex:reviewer'))
        self.commit('docs: quietly rewrite the record')

        problems = self.report()['problems']
        self.assertTrue(any('0001.json' in problem for problem in problems), problems)


class DeliverStatusTest(DoctorTest):
    """The rule CLAUDE.md states and nothing enforced until SEEN-107.

    The reviewed-tree fingerprint covers the ticket file, so `status: review` has
    to be in the tree before the review advance, exactly as the `## Outcome`
    section does. Nothing refused it: any working status passed while the journal
    sat at deliver, and the mismatch was reported only once the receipt had moved
    the ticket to delivered, by which point `verify_merge` will not let the ticket
    file change either. A ticket could deliver and then be unable to merge, which
    is what happened to SEEN-107 itself.
    """

    def reach_deliver(self):
        from harness.tests.test_lifecycle import clarify_evidence, solution_evidence
        self.run_harness('start', self.ticket_id, '--ticket', self.ticket_file,
                         '--actor', 'claude:implementer')
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())
        red = self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                               'claude:implementer', '--', 'sh', '-c', 'exit 1')
        green = self.run_harness('check', self.ticket_id, '--phase', 'green', '--actor',
                                 'claude:implementer', '--', 'true')
        regression = self.run_harness('check', self.ticket_id, '--phase', 'regression',
                                      '--actor', 'claude:implementer', '--', 'true')
        self.write('packages/core/coverage/coverage-summary.json',
                   '{"total": {"lines": {"total": 10, "covered": 9, "skipped": 0, "pct": 90.0}}}')
        self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer', '--', 'true')
        self.submit('tdd', dict(mode='code', regression=regression['sequence'],
                                coverage_delta=None,
                                slices=[dict(position=1, behaviour='The thing', failure_reason='It was absent',
                                             red=red['sequence'], green=green['sequence'])]))
        self.submit('review', dict(reviewer='codex:reviewer', independence='independent',
                                   read=['harness/journal.py'],
                                   acceptance_evidence=['Covered'], findings=[], checks=[],
                                   security_checklist=[], verdict='pass'),
                    actor='codex:reviewer')

    def set_status(self, status):
        path = self.root / self.ticket_file
        path.write_text(path.read_text().replace('status: doing', f'status: {status}'))

    def test_a_ticket_at_deliver_still_saying_doing_is_reported(self):
        self.reach_deliver()
        problems = doctor.report(Repository(self.root), thresholds.load(self.root))['problems']

        self.assertTrue(any('doing' in problem and self.ticket_id in problem
                            for problem in problems),
                        'It has passed review, so the ticket file has to say so before the '
                        'fingerprint locks: ' + '; '.join(problems))

    def test_review_is_what_the_deliver_stage_wants(self):
        self.reach_deliver()
        self.set_status('review')

        self.assertEqual(doctor.report(Repository(self.root),
                                       thresholds.load(self.root))['problems'], [])

    def test_doing_is_still_fine_before_the_review_gate(self):
        from harness.tests.test_lifecycle import clarify_evidence
        self.run_harness('start', self.ticket_id, '--ticket', self.ticket_file,
                         '--actor', 'claude:implementer')
        self.submit('clarify', clarify_evidence())

        self.assertEqual(doctor.report(Repository(self.root),
                                       thresholds.load(self.root))['problems'], [])


def _record(sequence, kind, ticket, when, **data):
    return dict(sequence=sequence, ticket=ticket, timestamp=when, harness_version='2',
                kind=kind, stage='review', attempt=1, actor='claude:implementer',
                session='a' * 12, head='0' * 40, prev_hash=None, data=data)


def _finding(identifier, severity, rule_candidate):
    return dict(id=identifier, severity=severity, claim='It breaks',
                failure_scenario='It breaks like this', status='resolved', resolution='Fixed',
                rule_candidate=rule_candidate)


def _plant(root, ticket, when, finding):
    """One delivered ticket's journal, written to disk and chained like a real one."""
    folder = root / 'docs' / 'harness' / 'history' / ticket
    folder.mkdir(parents=True, exist_ok=True)
    records = [
        _record(1, 'start', ticket, when),
        _record(2, 'advance', ticket, when, from_stage='review', to_stage='deliver',
               decisions=[],
               evidence=dict(reviewer='codex:reviewer', independence='subagent', read=[],
                             findings=[finding], verdict='pass')),
        _record(3, 'receipt', ticket, when, commit='a' * 40),
    ]
    previous = None
    for record in records:
        path = folder / f'{record["sequence"]:04d}.json'
        path.write_bytes(journal_module.serialise(dict(record, prev_hash=previous)))
        previous = journal_module.digest(path)
    return folder


class RuleRecurrenceWarningTest(DoctorTest):
    """SEEN-114 criterion 4's doctor half: a warning and never a problem.

    Two counted tickets, delivered after `[calibration] counted_from`, each
    carrying a finding whose `rule_candidate` names the same id and that id
    is not in `rules/registry.toml` (there is none in this throwaway
    project): the candidate has recurred and no rule has been written for it.
    """

    when = '2026-10-10T09:00:00+00:00'

    def test_a_candidate_recurring_twice_is_a_warning_and_not_a_problem(self):
        _plant(self.root, 'SEEN-801', self.when,
              _finding('F1', 'high', 'ast-grep/no-settlement-mutation'))
        _plant(self.root, 'SEEN-802', self.when,
              _finding('F2', 'medium', 'ast-grep/no-settlement-mutation'))
        report = self.report()
        self.assertTrue(report['ok'], report['problems'])
        self.assertTrue(any('ast-grep/no-settlement-mutation' in warning
                            for warning in report['warnings']), report['warnings'])

    def test_a_candidate_seen_once_is_not_a_warning(self):
        _plant(self.root, 'SEEN-801', self.when,
              _finding('F1', 'high', 'ast-grep/no-settlement-mutation'))
        report = self.report()
        self.assertEqual(report['warnings'], [])

    def test_a_healthy_project_carries_an_empty_warnings_list(self):
        self.start()
        self.assertEqual(self.report()['warnings'], [])


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
