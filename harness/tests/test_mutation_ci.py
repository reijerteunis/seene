"""The file selection of CI's incremental mutation job, as a tested module.

SEEN-116. The job used to carry its selection as inline shell no test ran. The
rules are pure and are asserted here over lists of changed paths; `main` is
asserted over a temporary GITHUB_OUTPUT file and a patched stdin. No test runs
git, Stryker or the network.
"""

import io
import os
import tempfile
import unittest
from unittest import mock

from harness import mutation_ci

ALL_OF_SRC = 'src/**/*.ts,!src/**/*.test.ts'


def everything_exists(path):
    return True


def nothing_exists(path):
    return False


class SelectTest(unittest.TestCase):
    def test_a_product_file_is_selected_without_the_package_prefix(self):
        self.assertEqual(mutation_ci.select(['packages/core/src/fee.ts'], everything_exists), 'src/fee.ts')

    def test_several_files_are_joined_with_commas_in_input_order(self):
        paths = ['packages/core/src/vat.ts', 'packages/core/src/money/fee.ts']
        self.assertEqual(mutation_ci.select(paths, everything_exists), 'src/vat.ts,src/money/fee.ts')

    def test_a_changed_tsconfig_selects_all_of_src(self):
        self.assertEqual(mutation_ci.select(['packages/core/tsconfig.json'], everything_exists),
                         ALL_OF_SRC)

    def test_a_changed_root_tsconfig_selects_all_of_src(self):
        """packages/core/tsconfig.json extends it, and the TypeScript checker reads both."""
        self.assertEqual(mutation_ci.select(['tsconfig.base.json'], everything_exists), ALL_OF_SRC)

    def test_a_test_file_selects_its_source_once(self):
        paths = ['packages/core/src/fee.test.ts', 'packages/core/src/fee.ts']
        self.assertEqual(mutation_ci.select(paths, everything_exists), 'src/fee.ts')

    def test_input_order_is_kept(self):
        paths = ['packages/core/src/vat.ts', 'packages/core/src/fees/detect.test.ts',
                 'packages/core/src/fee.ts']
        self.assertEqual(mutation_ci.select(paths, everything_exists),
                         'src/vat.ts,src/fees/detect.ts,src/fee.ts')

    def test_a_changed_test_selects_the_source_it_tests(self):
        self.assertEqual(mutation_ci.select(['packages/core/src/fees/detect.test.ts'],
                                            everything_exists), 'src/fees/detect.ts')

    def test_a_changed_test_with_no_sibling_selects_the_globs_of_its_directory(self):
        self.assertEqual(mutation_ci.select(['packages/core/src/fees/detect.test.ts'],
                                            nothing_exists),
                         'src/fees/**/*.ts,!src/fees/**/*.test.ts')

    def test_the_sibling_is_looked_for_by_repository_path(self):
        asked = []

        def exists(path):
            asked.append(path)
            return False

        mutation_ci.select(['packages/core/src/fee.test.ts'], exists)
        self.assertEqual(asked, ['packages/core/src/fee.ts'])

    def test_a_config_change_selects_all_of_src(self):
        for config in ('stryker.config.mjs', 'vitest.config.ts', 'package.json'):
            with self.subTest(config=config):
                paths = ['packages/core/src/fee.ts', f'packages/core/{config}']
                self.assertEqual(mutation_ci.select(paths, everything_exists), ALL_OF_SRC)

    def test_a_config_change_alone_selects_all_of_src(self):
        self.assertEqual(mutation_ci.select(['packages/core/package.json'], everything_exists), ALL_OF_SRC)

    def test_another_package_json_is_not_a_config_change(self):
        self.assertIsNone(mutation_ci.select(['package.json', 'apps/api/package.json'], everything_exists))

    def test_nothing_changed_selects_nothing(self):
        self.assertIsNone(mutation_ci.select([], everything_exists))

    def test_blank_lines_are_ignored(self):
        paths = ['', '  ', 'packages/core/src/fee.ts', '']
        self.assertEqual(mutation_ci.select(paths, everything_exists), 'src/fee.ts')

    def test_paths_outside_core_src_and_non_ts_files_are_ignored(self):
        paths = [
            'packages/core/fixtures/fee.ts',
            'packages/core/src/x.js',
            'packages/connectors/src/fee.ts',
            'apps/api/src/fee.ts',
            'docs/prd/prd.md',
        ]
        self.assertIsNone(mutation_ci.select(paths, everything_exists))


class MainTest(unittest.TestCase):
    def run_main(self, stdin, sibling_exists=True):
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, 'github_output')
            with mock.patch.dict(os.environ, {'GITHUB_OUTPUT': output}), \
                    mock.patch('os.path.isfile', return_value=sibling_exists), \
                    mock.patch('sys.stdin', io.StringIO(stdin)), \
                    mock.patch('sys.stdout', new_callable=io.StringIO) as stdout:
                status = mutation_ci.main()
            with open(output, encoding='utf-8') as handle:
                return status, handle.read(), stdout.getvalue()

    def test_main_writes_any_true_and_the_files(self):
        status, written, printed = self.run_main(
            'packages/core/src/fee.ts\npackages/core/src/fee.test.ts\ndocs/x.md\n')
        self.assertEqual(status, 0)
        self.assertEqual(written, 'any=true\nfiles=src/fee.ts\n')
        self.assertIn('src/fee.ts', printed)

    def test_main_writes_any_false_and_no_files_when_nothing_qualifies(self):
        status, written, printed = self.run_main('docs/x.md\n\n')
        self.assertEqual(status, 0)
        self.assertEqual(written, 'any=false\n')
        self.assertIn('No product file', printed)

    def test_main_selects_the_source_of_a_changed_test_by_asking_the_file_system(self):
        _, written, _ = self.run_main('packages/core/src/fee.test.ts\n')
        self.assertEqual(written, 'any=true\nfiles=src/fee.ts\n')
        _, written, _ = self.run_main('packages/core/src/fee.test.ts\n', sibling_exists=False)
        self.assertEqual(written, 'any=true\nfiles=src/**/*.ts,!src/**/*.test.ts\n')

    def test_main_on_empty_input_writes_any_false(self):
        _, written, _ = self.run_main('')
        self.assertEqual(written, 'any=false\n')

    def test_main_appends_to_the_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, 'github_output')
            with open(output, 'w', encoding='utf-8') as handle:
                handle.write('earlier=1\n')
            with mock.patch.dict(os.environ, {'GITHUB_OUTPUT': output}), \
                    mock.patch('sys.stdin', io.StringIO('packages/core/src/a.ts\n')), \
                    mock.patch('sys.stdout', new_callable=io.StringIO):
                mutation_ci.main()
            with open(output, encoding='utf-8') as handle:
                self.assertEqual(handle.read(), 'earlier=1\nany=true\nfiles=src/a.ts\n')


if __name__ == '__main__':
    unittest.main()
