"""The coverage gate: the command that measures and the figure it is allowed to read.

Defect 3 of record 42, found by running the harness on SEEN-008 rather than by
reading it. `DEFAULT_COMMAND` parked the coverage flags behind a bare `--`, which
pnpm forwards verbatim, so vitest never enabled coverage and never rewrote
`packages/core/coverage/coverage-summary.json`. The gate then read the file that
was already there, dated 23 September 2026, and reported it as this run's
measurement against the baseline. Both halves are tested here, and the second
matters more: a gate reading a figure no run produced reports a control that does
not exist, which is worse than having no gate at all.
"""

import os
import time
import unittest

from harness import coverage
from harness.errors import HarnessError
from harness.tests.test_lifecycle import CommandTest, clarify_evidence, solution_evidence

# Old enough that no reading of "the run that was supposed to write it" reaches
# back this far, and the age SEEN-008 actually met: four days.
DAYS = 4 * 24 * 3600


class DefaultCommand(unittest.TestCase):
    """What the harness runs when a session does not hand in a command.

    Whether the command writes a summary was verified by hand at the repository
    root on 27 September 2026, both ways round: the old command printed no
    coverage line and left the summary's mtime at 23 September, and
    `pnpm --filter @seen/core exec vitest run --coverage.enabled
    --coverage.reporter=json-summary` printed "Coverage enabled with v8" and
    rewrote the file. A unit test cannot install pnpm, so what it holds is the
    shape that made the difference.
    """

    def test_the_coverage_flags_are_not_parked_behind_a_bare_separator(self):
        self.assertNotIn(
            '--', coverage.DEFAULT_COMMAND,
            'pnpm forwards a literal -- to the script, and vitest parks every flag after it '
            'without reading any of them, so coverage is never enabled')

    def test_the_command_asks_for_coverage_and_the_summary_the_gate_reads(self):
        self.assertIn('--coverage.enabled', coverage.DEFAULT_COMMAND)
        self.assertIn('--coverage.reporter=json-summary', coverage.DEFAULT_COMMAND)

    def test_the_command_still_runs_in_the_package_the_gate_holds_a_floor_under(self):
        """The summary is read from packages/core/coverage/, so the run has to
        happen there: the filter is what puts it there."""
        self.assertIn('--filter', coverage.DEFAULT_COMMAND)
        self.assertIn(coverage.GATED_PACKAGE, coverage.DEFAULT_COMMAND)


class StaleCoverageSummary(CommandTest):
    """A figure the run did not produce is refused rather than reported."""

    def setUp(self):
        super().setUp()
        self.start()
        self.submit('clarify', clarify_evidence())
        self.submit('solution', solution_evidence())

    def summary(self, percentage, age_seconds=0):
        """The shape vitest's json-summary reporter writes, at a chosen age."""
        path = self.write('packages/core/coverage/coverage-summary.json',
                          f'{{"total": {{"lines": {{"total": 100, "covered": '
                          f'{int(percentage)}, "skipped": 0, "pct": {percentage}}}}}}}')
        if age_seconds:
            written = time.time() - age_seconds
            os.utime(path, (written, written))
        return path

    def baseline(self, percentage):
        return self.write('docs/harness/coverage.json',
                          f'{{"packages": {{"@seen/core": {{"lines": {percentage}}}}}}}')

    def measure(self):
        """The gate, run with a command that does not write coverage, which is
        exactly what the broken default did."""
        return self.run_harness('coverage', self.ticket_id, '--actor', 'claude:implementer',
                                '--', 'true')

    def test_a_summary_older_than_the_run_is_refused(self):
        self.baseline(80.0)
        self.summary(100.0, age_seconds=DAYS)

        with self.assertRaisesRegex(HarnessError, 'stale'):
            self.measure()

    def test_the_stale_figure_is_not_recorded_as_a_measurement(self):
        """The tdd gate counts coverage records, so a refused reading that left
        one behind would still pass the gate it was refused by."""
        self.summary(100.0, age_seconds=DAYS)
        before = len(self.records())

        with self.assertRaises(HarnessError):
            self.measure()

        self.assertEqual(len(self.records()), before,
                         'a figure no run produced is not a measurement')

    def test_a_summary_the_run_wrote_is_measured_and_compared(self):
        self.baseline(70.0)
        self.summary(74.0)

        record = self.measure()

        self.assertEqual(record['data']['lines'], 74.0)
        self.assertEqual(record['data']['delta'], 4.0)

    def test_the_slack_a_coarse_filesystem_clock_needs_is_allowed(self):
        """A summary written a moment before the reading is this run's output;
        a second of mtime granularity must not be read as staleness."""
        self.summary(74.0, age_seconds=1)

        self.assertEqual(self.measure()['data']['lines'], 74.0)

    def test_the_record_says_when_the_figure_it_read_was_written(self):
        """So a later reader never has to take the freshness on trust."""
        self.summary(74.0)

        self.assertIn('summary_written', self.measure()['data'])


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
