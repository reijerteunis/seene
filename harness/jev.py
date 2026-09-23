"""The harness's decision layer: typed questions with recorded probabilities.

Jev answers questions about the procedure, never about the product. It never
edits code, never touches a marketplace and never decides an agent action. Every
answer is recorded with the probabilities it came with and the threshold applied,
so a gate decision can be re-read later rather than taken on trust.

When no credential exists or the API cannot answer, the human answers and the
record says so. That path is not a stopgap: it is what the harness uses whenever
the service is unavailable, and it is the reason a missing key never blocks work.
"""

import json
import os
import urllib.error
import urllib.request

from .errors import HarnessError, require

ENV_FILE = '.env.local'
CREDENTIAL_NAMES = ('JEV_API_KEY', 'JEV_AI_API_KEY')

# The questions the procedure needs answered, and where each belongs. Structure
# lives here because it is what the harness is; the numbers live in
# thresholds.toml because they are what a person may reasonably tune.
NOUL = ('yes', 'no')
QUESTIONS = {
    'clarified': dict(type='noul', options=NOUL, stage='clarify',
                      ask='Are all material questions in this clarify record resolved?'),
    'risk': dict(type='score', options=('low', 'medium', 'high'), stage='clarify',
                 ask='How risky is the change this ticket describes?'),
    'solution_complete': dict(type='noul', options=NOUL, stage='solution',
                              ask='Does this solution record name everything the change needs?'),
    'touches_billing_or_policy_gate': dict(type='noul', options=NOUL, stage='solution',
                                           ask='Does this change touch billing or the policy gate?'),
    'severity': dict(type='score', options=('low', 'medium', 'high', 'blocking'), stage='review',
                     ask='How severe is this review finding?'),
    'must_fix': dict(type='noul', options=NOUL, stage='review',
                     ask='Must this finding be fixed before delivery?'),
    'is_destructive': dict(type='noul', options=NOUL, stage=None,
                           ask='Would this harness operation destroy or rewrite recorded evidence?'),
}

# The transport, replaced wholesale in tests. One function, one job: post JSON
# and hand back the parsed body. Nothing else in this module touches the network.
TRANSPORT = None


def questions_for(stage):
    return [name for name, question in QUESTIONS.items() if question['stage'] == stage]


def credential(root):
    """The Jev credential, from .env.local first and the environment second.

    The file wins so that a machine-wide variable cannot quietly override what
    this project is configured with.
    """
    path = root / ENV_FILE
    if path.is_file():
        for line in path.read_text().splitlines():
            name, _, value = line.partition('=')
            if name.strip() in CREDENTIAL_NAMES and value.strip():
                return value.strip().strip('"\'')
    for name in CREDENTIAL_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return None


def post(endpoint, payload, credential_value, timeout):
    """The live call. Unverified: no valid credential has yet reached this API."""
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {credential_value}'},
        method='POST')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def _transport():
    return TRANSPORT if TRANSPORT is not None else post


def _threshold(rules, question):
    return rules['jev']['thresholds'].get(question)


def _answer_from_jev(root, rules, question, name, state, credential_value):
    """Ask the API, and return None when it cannot answer.

    A failure here is never fatal: the human answers instead, and the record
    says which of the two did.
    """
    payload = dict(model=rules['jev']['model'],
                   question=QUESTIONS[name]['ask'],
                   name=name,
                   type=question['type'],
                   options=list(question['options']),
                   state=state)
    body = _transport()(rules['jev']['endpoint'], payload, credential_value,
                        rules['jev']['timeout_seconds'])
    probabilities = {option: float(body.get('probabilities', {}).get(option, 0.0))
                     for option in question['options']}
    outcome = body.get('answer')
    require(outcome in question['options'],
            f'Jev answered {outcome!r}, which is not one of {", ".join(question["options"])}')
    return dict(source='jev', model=body.get('model'), outcome=outcome,
                probabilities=probabilities, fallback_reason=None)


def unavailable(name, question, reason):
    """The record of a judgement that was not made.

    Honest rather than convenient: no probability, no outcome, and passed is
    neither true nor false. A stage may proceed past it, and SEEN-091 can count
    how often one did.
    """
    return dict(question=name, type=question['type'], options=list(question['options']),
                source='unavailable', model=None, outcome=None, probabilities={},
                threshold=None, passed=None, fallback_reason=reason)


def _answer_from_human(question, name, answer, confidence, reason):
    require(answer, f'This decision needs a human: pass --answer '
                    f'({" or ".join(question["options"])}) and --confidence to record one')
    require(answer in question['options'],
            f'{answer!r} is not one of {", ".join(question["options"])}')
    probabilities = {option: (float(confidence) if option == answer else 0.0)
                     for option in question['options']}
    return dict(source='human', model=None, outcome=answer,
                probabilities=probabilities, fallback_reason=reason)


def ask(root, rules, name, state, answer=None, confidence=1.0):
    """Answer one typed question, by API or by human, and return what to record.

    The returned record is built field by field. The response body is never
    stored wholesale, so an API that echoed the request back, credentials
    included, could not put them in the journal.
    """
    require(name in QUESTIONS,
            f'Unknown question: {name!r}; the harness asks {", ".join(sorted(QUESTIONS))}')
    question = QUESTIONS[name]
    credential_value = credential(root)
    result, reason = None, None
    if credential_value:
        try:
            result = _answer_from_jev(root, rules, question, name, state, credential_value)
        except HarnessError:
            raise
        except Exception as error:                      # noqa: BLE001 - any transport failure
            reason = f'{type(error).__name__}: {error}'
    if result is None:
        result = _answer_from_human(question, name, answer, confidence, reason)
    threshold = _threshold(rules, name)
    passed = _passed(question, result, threshold)
    return dict(question=name,
                type=question['type'],
                options=list(question['options']),
                source=result['source'],
                model=result['model'],
                outcome=result['outcome'],
                probabilities=result['probabilities'],
                threshold=threshold,
                passed=passed,
                fallback_reason=result['fallback_reason'])


def _passed(question, result, threshold):
    """Whether an answer clears its threshold.

    A noul passes when its yes probability clears the bar. A score has no bar of
    its own: it routes, and the gate that reads it decides what to do.
    """
    if threshold is None:
        return None
    if question['type'] == 'noul':
        return result['probabilities'].get('yes', 0.0) >= threshold
    return result['probabilities'].get(result['outcome'], 0.0) >= threshold
