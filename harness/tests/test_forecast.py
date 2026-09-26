"""What a plan of this shape has cost, read from the delivered KPI records.

The forecast is evidence on a solution advance and never a reason to refuse
one: SEEN-111's own clarify record found the session that planned it had
already spent 61,432 output tokens before a line of code existed, which a
per-slice prediction cannot rescue and must not pretend to. These tests cover
the three things the criterion asks for: the prediction read from delivered
figures rather than from points, the split named when that prediction is over
budget, and the absence read as an absence rather than as a low number.
"""

import json
import statistics
import unittest

from harness.tests.test_stage_gates import GateTest


def write_kpi(root, ticket, output_tokens):
    """A kpi.json shaped enough for forecast.py: one execution entry per figure.

    `output_tokens` is a list of values, one per delivered slice; `None` stands
    for a slice a session log could not price, which forecast.py must skip
    rather than read as a free slice.
    """
    folder = root / 'docs' / 'harness' / 'history' / ticket
    folder.mkdir(parents=True, exist_ok=True)
    execution = [dict(position=position, name=f'slice {position}', points=1,
                      model='sonnet', effort='medium', source='rule', ran_on='sonnet',
                      output_tokens=value)
                 for position, value in enumerate(output_tokens, start=1)]
    (folder / 'kpi.json').write_text(json.dumps(dict(ticket=ticket, execution=execution)))


class ForecastTest(GateTest):

    def setUp(self):
        super().setUp()
        self.window = self.thresholds['calibration']['window']
        self.budget = self.thresholds['session']['output_token_budget']

    def deliver(self, count, output_tokens):
        """`count` tickets, each carrying the same one-slice figure."""
        for index in range(count):
            write_kpi(self.root, f'SEEN-{900 + index}', [output_tokens])


class ThePredictionTest(ForecastTest):

    def test_the_per_slice_figure_is_the_median_of_delivered_slices_not_the_plan_points(self):
        values = [10_000, 12_000, 14_000, 16_000, 18_000, 20_000, 22_000, 24_000, 26_000, 28_000]
        for index, value in enumerate(values):
            write_kpi(self.root, f'SEEN-{900 + index}', [value])
        # A plan whose own points bear no relation to the delivered figures, so a
        # forecast that echoed the points back would be caught rather than
        # coincide with the right answer.
        data = self.filled_solution(slices=[dict(position=1, name='The detector', points=1,
                                                  files=['packages/core/src/fees.ts'],
                                                  red='No detector exists')])
        result = self.evaluate('solution', data)
        forecast = result['forecast']
        self.assertTrue(forecast['available'])
        self.assertEqual(forecast['output_tokens_per_slice'], statistics.median(values))
        self.assertNotEqual(forecast['output_tokens_per_slice'], data['slices'][0]['points'])

    def filled_solution(self, **changes):
        # SolutionGateTest's own builder, reused rather than copied: two builders
        # of the same fixture would drift the moment one of them changed.
        from harness.tests.test_stage_gates import SolutionGateTest
        return SolutionGateTest.filled_solution(self, **changes)


class TheSplitNamedTest(ForecastTest):

    def test_a_prediction_over_budget_says_so_and_names_the_split_and_still_advances(self):
        # SEEN-109's own recorded figures: a one-point slice at 121,398 output
        # tokens and one at 42,520, against a 60,000 budget. The median of ten
        # such slices is still well over budget.
        values = [121_398, 118_000, 130_000, 125_000, 122_000,
                  128_000, 119_000, 131_000, 126_000, 124_000]
        for index, value in enumerate(values):
            write_kpi(self.root, f'SEEN-{900 + index}', [value])
        from harness.tests.test_stage_gates import SolutionGateTest
        data = SolutionGateTest.filled_solution(self)
        result = self.evaluate('solution', data)
        forecast = result['forecast']
        self.assertTrue(forecast['available'])
        median = statistics.median(values)
        self.assertGreater(median, self.budget)
        self.assertTrue(forecast['exceeds_budget'])
        self.assertIsNotNone(forecast['split'])
        self.assertGreaterEqual(forecast['split'], 2)


class TheAbsenceTest(ForecastTest):

    def test_fewer_delivered_tickets_than_the_window_reports_an_absence_not_a_figure(self):
        observed = self.window - 1
        self.deliver(observed, 30_000)
        from harness.tests.test_stage_gates import SolutionGateTest
        data = SolutionGateTest.filled_solution(self)
        result = self.evaluate('solution', data)
        forecast = result['forecast']
        self.assertFalse(forecast['available'])
        self.assertEqual(forecast['observed_tickets'], observed)
        self.assertEqual(forecast['required'], self.window)
        self.assertNotIn('output_tokens_per_slice', forecast)


if __name__ == '__main__':  # pragma: no cover - a module must run on its own
    unittest.main()
