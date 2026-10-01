"""rule_candidate on every finding that could have been a rule.

SEEN-114 slice 3. A finding a static rule could have caught is a finding paid
for three times: the reviewer's reading, the return, the second review. The
loop that stops that starts with every finding at medium or above naming the
rule that would have caught it, the rule that should be written, or
`none: <reason>` when no static rule can. Low is left alone, for the same
reason `file` is left alone at low and medium in `check_findings`: not
looking for a low finding is the saving itself.
"""

import json
import unittest

from harness import gates, thresholds
from harness.errors import HarnessError
from harness.repository import Repository
from harness.tests.helpers import ProjectTest


class ReviewGateTest(ProjectTest):

    def setUp(self):
        super().setUp()
        self.repository = Repository(self.root)
        self.thresholds = thresholds.load(self.root)

    def template(self, stage, **changes):
        name = gates.template_name(stage, changes.get('mode'))
        data = json.loads((self.root / 'harness' / 'templates' / name).read_text())
        data.update(changes)
        return data

    def tdd_done(self):
        records = [dict(sequence=1, kind='start', stage='clarify', attempt=1,
                        actor='claude:implementer', data={})]
        records.append(dict(sequence=2, kind='advance', stage='tdd', attempt=1,
                            actor='claude:implementer',
                            data=dict(from_stage='tdd', to_stage='review',
                                      evidence=dict(regression=0), decisions=[])))
        return records

    def review(self, **changes):
        data = self.template('review',
                             read=['harness/gates.py'],
                             acceptance_evidence=['AC1 proven by check 4'],
                             independence='self-review',
                             reviewer='claude:reviewer')
        data.update(changes)
        return data

    def evaluate(self, stage, data, records=None, attempt=1):
        current = dict(stage=stage, attempt=attempt, records=len(records or []))
        return gates.evaluate(stage, data, records or self.tdd_done(), current,
                              self.repository, self.thresholds)

    def finding(self, severity, **changes):
        body = dict(id='R-01', severity=severity, claim='A detector rounds the wrong way',
                   failure_scenario='A EUR 0.005 fee rounds up and the claim overstates',
                   status='resolved', resolution='Fixed the rounding')
        if severity in gates.ESCAPING_SEVERITIES:
            body['file'] = 'packages/core/src/fees.ts:12'
        body.update(changes)
        return body

    def test_a_medium_finding_with_no_rule_candidate_is_refused(self):
        finding = self.finding('medium')
        self.assertNotIn('rule_candidate', finding)
        with self.assertRaisesRegex(HarnessError, 'rule_candidate'):
            self.evaluate('review', self.review(findings=[finding]))

    def test_a_low_finding_needs_no_rule_candidate(self):
        finding = self.finding('low')
        self.assertNotIn('rule_candidate', finding)
        self.evaluate('review', self.review(findings=[finding]))

    def test_a_malformed_rule_candidate_is_refused(self):
        finding = self.finding('medium', rule_candidate='just a vibe')
        with self.assertRaisesRegex(HarnessError, 'rule_candidate'):
            self.evaluate('review', self.review(findings=[finding]))

    def test_a_rule_id_already_in_the_registry_is_accepted(self):
        finding = self.finding('medium', rule_candidate='ast-grep/no-euro-sign')
        self.evaluate('review', self.review(findings=[finding]))

    def test_a_rule_id_not_yet_in_the_registry_is_accepted(self):
        finding = self.finding('high', rule_candidate='ast-grep/no-settlement-mutation')
        self.evaluate('review', self.review(findings=[finding]))

    def test_a_none_shape_with_a_reason_is_accepted(self):
        finding = self.finding('high',
                               rule_candidate='none: this is a judgement call about wording, '
                                              'not a pattern a static rule could match')
        self.evaluate('review', self.review(findings=[finding]))

    def test_a_none_shape_with_no_reason_is_refused(self):
        finding = self.finding('high', rule_candidate='none:')
        with self.assertRaisesRegex(HarnessError, 'rule_candidate'):
            self.evaluate('review', self.review(findings=[finding]))

    def test_an_unknown_tool_in_the_rule_id_is_refused(self):
        finding = self.finding('blocking', rule_candidate='eslint/no-any')
        with self.assertRaisesRegex(HarnessError, 'rule_candidate'):
            self.evaluate('review', self.review(findings=[finding]))


if __name__ == '__main__':
    unittest.main()
