"""The mutation measurement: Stryker's report read into a score, and a kill read as a RED.

SEEN-116. Stryker exits 0 whether it killed every mutant or none, so neither the
score nor the RED can come from its exit code. Both are read from the JSON
report, and every figure here is asserted over a report written by the test: no
test runs Stryker.
"""

import json
import os
import time
import unittest

from harness import checks, mutation
from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

SRC = 'packages/core/src/fee.ts'
OTHER = 'packages/core/src/vat.ts'


def mutant(identifier, status):
    return dict(id=str(identifier), mutatorName='EqualityOperator', replacement='x',
                status=status, location=dict(start=dict(line=1, column=1),
                                             end=dict(line=1, column=2)))


def report(**files):
    """A mutation-testing-report-schema document: file key to the statuses it holds.

    Keys are relative to packages/core, which is where Stryker runs, so a test
    names `src/fee.ts` here and `packages/core/src/fee.ts` everywhere else.
    """
    return dict(schemaVersion='1.0', thresholds=dict(high=80, low=60),
                files={name.replace('__', '/').replace('_ts', '.ts'): dict(
                    language='typescript', source='',
                    mutants=[mutant(index, status) for index, status in enumerate(statuses)])
                    for name, statuses in files.items()})


class ScoreTest(unittest.TestCase):

    def counts(self, **statuses):
        return mutation.counts(report(src__fee_ts=[
            status for status, number in statuses.items() for _ in range(number)]), [SRC])

    def test_a_kill_and_a_timeout_count_for_the_tests(self):
        self.assertEqual(mutation.score(self.counts(Killed=3, Timeout=1, Survived=1,
                                                    NoCoverage=1)), 66.67)

    def test_a_survivor_and_an_uncovered_mutant_count_against_them(self):
        self.assertEqual(mutation.score(self.counts(Killed=1, Survived=1)), 50.0)
        self.assertEqual(mutation.score(self.counts(Killed=1, NoCoverage=1)), 50.0)

    def test_a_mutant_that_never_compiled_is_neither_for_nor_against(self):
        counts = self.counts(Killed=2, CompileError=5, RuntimeError=1, Ignored=1)
        self.assertEqual(mutation.score(counts), 100.0)
        self.assertEqual(counts['killed'], 2)

    def test_no_mutants_is_not_applicable_and_never_a_hundred(self):
        self.assertIsNone(mutation.score(self.counts(CompileError=4)))
        self.assertIsNone(mutation.score(self.counts()))

    def test_only_the_files_asked_about_are_counted(self):
        document = report(src__fee_ts=['Killed', 'Killed'], src__vat_ts=['Survived'] * 8)
        self.assertEqual(mutation.counts(document, [SRC])['survived'], 0)
        self.assertEqual(mutation.counts(document, [SRC, OTHER])['survived'], 8)

    def test_a_directory_names_the_files_under_it(self):
        document = report(src__fee_ts=['Killed'], src__vat_ts=['Survived'])
        counts = mutation.counts(document, ['packages/core/src'])
        self.assertEqual((counts['killed'], counts['survived']), (1, 1))

    def test_a_file_the_report_does_not_hold_has_no_mutants(self):
        self.assertIsNone(mutation.score(mutation.counts(report(), [SRC])))


class SourceFilesTest(unittest.TestCase):

    def test_only_product_source_under_core_src_is_held_to_the_floor(self):
        named = ['harness/gates.py', SRC, 'packages/core/src/fee.test.ts',
                 'packages/core/fixtures/tolerance/detector.ts', 'packages/core/db/repository.ts',
                 'packages/connectors/src/bol.ts', 'packages/core/src/money/cents.ts']
        self.assertEqual(mutation.source_files(named), [SRC, 'packages/core/src/money/cents.ts'])

    def test_a_directory_under_src_is_product_source_too(self):
        self.assertEqual(mutation.source_files(['packages/core/src']), ['packages/core/src'])

    def test_a_plan_naming_no_core_source_names_nothing(self):
        self.assertEqual(mutation.source_files(['harness/gates.py', 'docs/x.md']), [])


class AKillIsARedTest(unittest.TestCase):

    def evidence(self, exit_code=0, **extra):
        return dict(phase='red', exit_code=exit_code, command=['pnpm'], **extra)

    def test_a_passing_command_that_killed_a_mutant_demonstrates_failure(self):
        self.assertTrue(checks.demonstrates_failure(self.evidence(mutants_killed={SRC: ['3']})))

    def test_a_passing_command_that_killed_nothing_still_does_not(self):
        self.assertFalse(checks.demonstrates_failure(self.evidence()))
        self.assertFalse(checks.demonstrates_failure(self.evidence(mutants_killed={})))
        self.assertFalse(checks.demonstrates_failure(self.evidence(mutants_killed={SRC: []})))

    def test_a_timeout_or_a_failure_to_start_is_not_made_a_red_by_a_report(self):
        for code in (checks.TIMEOUT_EXIT, checks.LAUNCH_FAILURE_EXIT):
            self.assertFalse(checks.demonstrates_failure(
                self.evidence(exit_code=code, mutants_killed={SRC: ['3']})))

    def test_a_real_non_zero_exit_is_still_a_red_with_or_without_a_report(self):
        self.assertTrue(checks.demonstrates_failure(self.evidence(exit_code=1)))


class ReadingTheReportTest(CommandTest):

    def write_report(self, **files):
        return self.write(mutation.PRODUCT_REPORT, json.dumps(report(**files)))

    def test_the_killed_mutants_are_named_by_file_and_id(self):
        self.write_report(src__fee_ts=['Survived', 'Killed', 'Killed'], src__vat_ts=['Survived'])
        self.assertEqual(mutation.killed_since(self.root, 0), {SRC: ['1', '2']})

    def test_a_report_of_survivors_names_no_kill(self):
        self.write_report(src__fee_ts=['Survived', 'NoCoverage'])
        self.assertEqual(mutation.killed_since(self.root, 0), {})

    def test_a_report_older_than_the_run_is_not_this_runs_evidence(self):
        path = self.write_report(src__fee_ts=['Killed'])
        os.utime(path, (time.time() - 100, time.time() - 100))
        self.assertEqual(mutation.killed_since(self.root, time.time() - 10), {})

    def test_the_fixture_report_is_read_beside_the_product_one(self):
        self.write(mutation.FIXTURE_REPORT, json.dumps(
            report(fixtures__tolerance__detector_ts=['Killed'])))
        self.assertEqual(mutation.killed_since(self.root, 0),
                         {'packages/core/fixtures/tolerance/detector.ts': ['0']})

    def test_a_report_that_is_not_json_is_refused_by_name(self):
        self.write(mutation.PRODUCT_REPORT, '{not json')
        with self.assertRaisesRegex(HarnessError, 'not readable JSON'):
            mutation.killed_since(self.root, 0)

    def test_the_command_mutates_only_the_files_it_is_given_relative_to_core(self):
        command = mutation.command([SRC, 'packages/core/src/money/cents.ts'])
        self.assertEqual(command[-2:], ('--mutate', 'src/fee.ts,src/money/cents.ts'))
        self.assertEqual(command[:4], ('pnpm', '--filter', '@seen/core', 'mutation'))

    def test_a_directory_is_expanded_into_the_globs_of_the_files_under_it(self):
        self.assertEqual(mutation.command(['packages/core/src/money']),
                         ('pnpm', '--filter', '@seen/core', 'mutation', '--mutate',
                          'src/money/**/*.ts,!src/money/**/*.test.ts'))
        self.assertEqual(mutation.command(['packages/core/src/'])[-1],
                         'src/**/*.ts,!src/**/*.test.ts')

    def test_a_file_and_a_directory_are_joined_into_one_mutate_value(self):
        self.assertEqual(mutation.command([SRC, 'packages/core/src/money'])[-1],
                         'src/fee.ts,src/money/**/*.ts,!src/money/**/*.test.ts')


class MeasureTest(CommandTest):

    def measure(self, statuses, files=(SRC,), since=0, **evidence):
        self.write(mutation.PRODUCT_REPORT,
                   json.dumps(report(src__fee_ts=statuses)))
        return mutation.measure(self.root, dict(dict(phase='mutation', exit_code=0), **evidence),
                                list(files), 70, since)

    def test_the_record_carries_the_score_the_counts_the_files_and_the_floor(self):
        data = self.measure(['Killed'] * 7 + ['Survived'] * 3)
        self.assertEqual((data['score'], data['floor'], data['files']), (70.0, 70, [SRC]))
        self.assertEqual((data['killed'], data['survived'], data['mutants']), (7, 3, 10))
        self.assertIsNone(data['reason'])
        self.assertFalse(data['not_applicable'])

    def test_no_mutants_in_the_files_is_recorded_as_such_and_never_as_a_score(self):
        data = self.measure(['CompileError'])
        self.assertIsNone(data['score'])
        self.assertEqual(data['mutants'], 0)
        self.assertIn('no mutants', data['reason'])
        self.assertTrue(data['not_applicable'])

    def test_a_run_that_failed_measures_nothing_whatever_report_is_lying_about(self):
        data = self.measure(['Killed'] * 5, exit_code=1)
        self.assertIsNone(data['score'])
        self.assertIn('failed', data['reason'])
        self.assertFalse(data['not_applicable'])

    def test_a_report_from_before_the_run_measures_nothing(self):
        data = self.measure(['Killed'] * 5, since=time.time() + 100)
        self.assertIsNone(data['score'])
        self.assertIn('report', data['reason'])
        self.assertFalse(data['not_applicable'])

    def measure_over(self, files, **named):
        self.write(mutation.PRODUCT_REPORT, json.dumps(report(**named)))
        return mutation.measure(self.root, dict(phase='mutation', exit_code=0),
                                list(files), 70, 0)

    def test_a_named_file_the_report_lacks_is_a_miss_and_never_not_applicable(self):
        data = self.measure_over(['packages/core/src/typo.ts'], src__fee_ts=['Killed'])
        self.assertIsNone(data['score'])
        self.assertFalse(data['not_applicable'])
        self.assertIn('src/typo.ts', data['reason'])
        self.assertEqual(data['missing'], ['packages/core/src/typo.ts'])

    def test_a_directory_with_no_report_file_under_it_is_a_miss_too(self):
        data = self.measure_over(['packages/core/src/money'], src__fee_ts=['Killed'])
        self.assertIsNone(data['score'])
        self.assertFalse(data['not_applicable'])
        self.assertIn('src/money', data['reason'])

    def test_every_named_file_in_the_report_with_no_mutants_is_still_not_applicable(self):
        data = self.measure_over([SRC, 'packages/core/src/money'], src__fee_ts=[],
                                 src__money__cents_ts=['CompileError'])
        self.assertTrue(data['not_applicable'])
        self.assertIsNone(data['score'])
        self.assertEqual(data['missing'], [])


class TheCommandTest(CommandTest):
    """`harness mutation` and `harness check` over a stub that writes a report."""

    WRITE = ('import json,pathlib,sys\n'
             'p=pathlib.Path("packages/core/reports/mutation/mutation.json")\n'
             'p.parent.mkdir(parents=True,exist_ok=True)\n'
             'p.write_text(sys.argv[1])\n')

    def stub(self, document):
        return ['python3', '-c', self.WRITE, json.dumps(document)]

    def to_tdd(self, files=(SRC,)):
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence(
            slices=[dict(name='Fees', points=1, files=list(files), red='r')]))

    def test_a_red_whose_report_names_a_kill_is_recorded_with_the_kill(self):
        self.to_tdd()
        record = self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                                  'claude:implementer', '--',
                                  *self.stub(report(src__fee_ts=['Killed', 'Survived'])))
        self.assertEqual(record['data']['exit_code'], 0)
        self.assertEqual(record['data']['mutants_killed'], {SRC: ['0']})

    def test_a_red_whose_report_holds_only_survivors_is_refused_as_before(self):
        self.to_tdd()
        with self.assertRaisesRegex(HarnessError, 'did not fail'):
            self.run_harness('check', self.ticket_id, '--phase', 'red', '--actor',
                             'claude:implementer', '--',
                             *self.stub(report(src__fee_ts=['Survived'])))

    def test_the_mutation_command_scores_the_files_the_plan_names_under_core_src(self):
        self.to_tdd(files=(SRC, 'harness/gates.py'))
        record = self.run_harness('mutation', self.ticket_id, '--actor', 'claude:implementer',
                                  '--', *self.stub(report(src__fee_ts=['Killed', 'Killed',
                                                                       'Survived'])))
        data = record['data']
        self.assertEqual((record['kind'], data['phase'], record['stage']),
                         ('check', 'mutation', 'tdd'))
        self.assertEqual((data['score'], data['files'], data['floor']), (66.67, [SRC], 70))

    def test_a_plan_naming_no_core_source_has_nothing_to_measure(self):
        self.to_tdd(files=('harness/gates.py',))
        with self.assertRaisesRegex(HarnessError, 'packages/core/src'):
            self.run_harness('mutation', self.ticket_id, '--actor', 'claude:implementer',
                             '--', 'true')


if __name__ == '__main__':
    unittest.main()
