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
    'clarified': dict(
        type='noul', options=NOUL, stage='clarify',
        # A named unknown is clarity, not a hole. Writing down what only the work
        # can settle used to lower the score: SEEN-096 fell from 0.67 to 0.46 for
        # saying that a tool's documented behaviour has to be verified by
        # installing it, and SEEN-100's own record fell from 0.77 to 0.72 for
        # saying that no test may call this API. Measured in SEEN-100's journal.
        ask='Are all material questions in this clarify record resolved?',
        criteria={'true': 'Every open question is answered or explicitly deferred with a decision. '
                          'A question that only doing the work can settle counts as resolved when '
                          'the record names what will settle it.',
                  'false': 'Something material is still unresolved, with no decision and nothing '
                           'said about what would resolve it.'}),
    'risk': dict(
        type='score', options=('low', 'medium', 'high'), stage='clarify',
        ask='How risky is the change this ticket describes?',
        criteria=['Isolated and reversible, touching no money, no credentials and no tenant data',
                  'Real blast radius: several modules, a migration, or a change others depend on',
                  'Touches money, credentials, tenant isolation or an action taken inside a '
                  "seller's marketplace account"]),
    'solution_complete': dict(
        type='noul', options=NOUL, stage='solution',
        # "Names everything" invites perfectionism: on a thirty-file change a
        # reader can always find something unnamed. The bar that can actually be
        # judged is whether someone could build it without stopping to ask.
        ask='Could a competent implementer build this change from this record without stopping to '
            'ask a question the record should have answered?',
        criteria={'true': 'The approach, the files, the tests to write first, the rollback and the '
                          'risks are concrete enough to act on, and implementation detail is left '
                          'to the implementer',
                  'false': 'They would have to stop and ask something material: an unnamed '
                           'mechanism, an undecided interface, or a dependency nobody has chosen'}),
    'touches_billing_or_policy_gate': dict(
        type='noul', options=NOUL, stage='solution',
        ask='Does this change touch billing or the policy gate?',
        criteria={'true': 'It changes billable events, invoicing, or how an agent action is '
                          'allowed, approved or refused',
                  'false': 'It touches neither'}),
    'severity': dict(
        type='score', options=('low', 'medium', 'high', 'blocking'), stage='review',
        ask='How severe is this review finding?',
        criteria=['Cosmetic or a matter of taste',
                  'Worth fixing, but nothing breaks if it ships',
                  'Something will go wrong for a user or an operator',
                  'Money, credentials, tenant isolation or evidence integrity is at stake']),
    'must_fix': dict(
        type='noul', options=NOUL, stage='review',
        ask='Must this finding be fixed before this ticket is delivered?',
        criteria={'true': 'Delivering without fixing it would be wrong',
                  'false': 'It can be recorded and carried'}),
    'is_destructive': dict(
        type='noul', options=NOUL, stage=None,
        ask='Would this harness operation destroy or rewrite recorded evidence?',
        criteria={'true': 'It deletes, rewrites or renumbers a journal, a receipt or the graph',
                  'false': 'It only appends or reads'}),
    # The review triage, from SEEN-107. All four have stage=None, the way
    # is_destructive does, because they are asked by their own command rather
    # than by the review stage's advance: questions_for('review') stays severity
    # and must_fix, which are asked once per finding after a reviewer has read.
    'criterion_evidenced': dict(
        type='noul', options=NOUL, stage=None,
        ask='Does the recorded evidence satisfy this acceptance criterion?',
        criteria={'true': 'A check record, a test name or a diff hunk in the state satisfies '
                          'what the criterion asks for',
                  'false': 'Nothing in the state satisfies it, or what is cited proves something '
                           'adjacent to it rather than it'}),
    'diff_matches_solution': dict(
        type='noul', options=NOUL, stage=None,
        ask='Are the files changed and the mechanism used the ones the solution record named?',
        criteria={'true': 'The change lands in the files the record planned and works the way it '
                          'said; a file it did not name follows from the ones it did',
                  'false': 'It lands somewhere the record never named, or reaches its result by '
                           'a mechanism the record did not describe'}),
    'reviewer_must_read': dict(
        type='noul', options=NOUL, stage=None,
        ask='Must a reviewer read this file to judge whether the change is right?',
        criteria={'true': 'Getting this file wrong is something the tests that ran would not '
                          'catch: it carries logic, money, a credential, tenant isolation or '
                          'evidence integrity, or it is large, risky, or changed without the '
                          'solution record naming it',
                  'false': 'It is mechanical, small and guarded: a generated copy, a rename, a '
                           'fixture, or a test whose own failure would be the signal'}),
    'review_depth': dict(
        # Two levels, so the harness reads it by level index the way it reads
        # every other score. A choice between two is what a two-level score is.
        type='score', options=('spot', 'full'), stage=None,
        ask='How much of this diff does the reviewer need to read?',
        criteria=['The focus set is enough: what is outside it is mechanical and the tests '
                  'that ran guard it',
                  'The whole diff: the change is broad, or risky, or does not match what the '
                  'solution record planned']),
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


# The service sits behind Cloudflare, which rejects Python's default user agent
# with error 1010 before the API sees the request. Naming ourselves is both
# politer and the difference between a decision and a 403.
USER_AGENT = 'seen-harness/1.0 (+https://tryseen.com)'


def build_request(endpoint, payload, credential_value):
    """The request that goes over the wire. Separated so it can be read in a test."""
    return urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'Accept': 'application/json',
                 'User-Agent': USER_AGENT,
                 'Authorization': f'Bearer {credential_value}'},
        method='POST')


def post(endpoint, payload, credential_value, timeout):
    """The live call. Unverified: no valid credential has yet reached this API."""
    with urllib.request.urlopen(build_request(endpoint, payload, credential_value),
                                timeout=timeout) as response:
        return json.loads(response.read().decode())


def _transport():
    return TRANSPORT if TRANSPORT is not None else post


def _threshold(rules, question):
    return rules['jev']['thresholds'].get(question)


def triple(entry):
    """One asked question as (key, question, subject), whichever form it came in.

    A stage asks each of its questions once, so a bare name is the whole answer
    there. The review triage asks one question once per acceptance criterion and
    once per changed file, so it keys them itself and says what each is about.
    """
    if isinstance(entry, str):
        return entry, entry, None
    key, name, subject = (list(entry) + [None])[:3]
    return key, name, subject


def build_questions(asked):
    """The questions map the API expects, one entry per key.

    The key rather than the question name, because one request can carry the same
    question several times and a map keyed by name could not. The subject is
    appended to the instructions rather than left in the state, because a question
    should carry what it is answered from: `criterion_evidenced#2` with the
    criterion in front of it is answerable, and without it is not.
    """
    built = {}
    for key, name, subject in (triple(entry) for entry in asked):
        question = QUESTIONS[name]
        instructions = question['ask'] if not subject else f'{question["ask"]}\n\n{subject}'
        entry = dict(type=question['type'], instructions=instructions)
        if question.get('criteria') is not None:
            entry['criteria'] = question['criteria']
        built[key] = entry
    return built


def _read_answer(name, body_answer):
    """One API answer, in the harness's own vocabulary.

    A noul comes back as a single probability of yes. A score comes back by
    level index with a legend and a confidence, and the levels are this
    question's options in order, so the index is the option.
    """
    question = QUESTIONS[name]
    if question['type'] == 'noul':
        probability = float(body_answer['noul'])
        probabilities = {'yes': probability, 'no': round(1.0 - probability, 6)}
        outcome = 'yes' if probability >= 0.5 else 'no'
        return dict(outcome=outcome, probabilities=probabilities, confidence=None, score=None)
    by_level = body_answer.get('probabilities', {})
    probabilities = {option: float(by_level.get(str(index), 0.0))
                     for index, option in enumerate(question['options'])}
    outcome = max(probabilities, key=probabilities.get)
    return dict(outcome=outcome, probabilities=probabilities,
                confidence=body_answer.get('confidence'), score=body_answer.get('score'))


def _ask_api(rules, asked, state, credential_value):
    """One request carrying every question, and the answers it returns."""
    payload = dict(state=state,
                   model=rules['jev']['model'],
                   questions=build_questions(asked))
    body = _transport()(rules['jev']['endpoint'], payload, credential_value,
                        rules['jev']['timeout_seconds'])
    answers = body.get('answers') or {}
    read = {}
    for key, name, _ in asked:
        require(key in answers, f'The API answered without {key}')
        read[key] = dict(_read_answer(name, answers[key]),
                         source='jev', model=body.get('model'), fallback_reason=None)
    return read


def unavailable(name, question, reason, key=None):
    """The record of a judgement that was not made.

    Honest rather than convenient: no probability, no outcome, and passed is
    neither true nor false. A stage may proceed past it, and SEEN-091 can count
    how often one did.
    """
    return dict(key=key or name, question=name, type=question['type'],
                options=list(question['options']),
                source='unavailable', model=None, outcome=None, probabilities={},
                confidence=None, score=None, threshold=None, passed=None,
                fallback_reason=reason)


def _answer_from_human(question, name, answer, confidence, reason):
    require(answer,
            (f'The model could not answer ({reason}). ' if reason else '')
            + f'This decision needs a human: pass --answer '
              f'({" or ".join(question["options"])}) and --confidence to record one')
    require(answer in question['options'],
            f'{answer!r} is not one of {", ".join(question["options"])}')
    probabilities = {option: (float(confidence) if option == answer else 0.0)
                     for option in question['options']}
    return dict(source='human', model=None, outcome=answer, probabilities=probabilities,
                confidence=float(confidence), score=None, fallback_reason=reason)


def ask_batch(root, rules, asked, state, answers=None, confidence=1.0, must_answer=True):
    """Answer several typed questions in one request, by API or by human.

    `asked` is a sequence of question names, or of (key, question, subject) for a
    request that carries one question several times. Each record is built field by
    field, so an API that echoed the request back, credentials and environment
    included, could not put any of it in the journal.

    `must_answer` is what separates the two callers. A stage gate needs a
    judgement, so a transport that failed refuses and names the command that
    records a human answer. The review triage does not: it records the absence and
    reads it as an absence, because a judgement nobody made must neither send a
    ticket back nor narrow what a reviewer reads.
    """
    asked = [triple(entry) for entry in asked]
    for _, name, _ in asked:
        require(name in QUESTIONS,
                f'Unknown question: {name!r}; the harness asks {", ".join(sorted(QUESTIONS))}')
    # A question a human has already answered is not put to the model: the
    # override the harness documents would not otherwise exist, because a
    # credential being present would send every question to the API.
    given = {key: value for key, value in (answers or {}).items() if value}
    outstanding = [entry for entry in asked if entry[0] not in given]
    credential_value = credential(root)
    read, reason = {}, None
    if credential_value and outstanding:
        try:
            read = _ask_api(rules, outstanding, state, credential_value)
        except HarnessError:
            raise
        except Exception as error:                      # noqa: BLE001 - any transport failure
            reason = f'{type(error).__name__}: {error}'
    elif not credential_value:
        reason = 'No Jev credential'
    recorded = []
    for key, name, _ in asked:
        question = QUESTIONS[name]
        result = read.get(key)
        answered_by_hand = (answers or {}).get(key)
        if result is None and not must_answer and not answered_by_hand:
            recorded.append(unavailable(name, question, reason, key=key))
            continue
        if result is None:
            result = _answer_from_human(question, name, answered_by_hand, confidence, reason)
        threshold = _threshold(rules, name)
        recorded.append(dict(key=key,
                             question=name,
                             type=question['type'],
                             options=list(question['options']),
                             source=result['source'],
                             model=result['model'],
                             outcome=result['outcome'],
                             probabilities=result['probabilities'],
                             confidence=result.get('confidence'),
                             score=result.get('score'),
                             threshold=threshold,
                             passed=_passed(question, result, threshold),
                             fallback_reason=result['fallback_reason']))
    return recorded


def ask_many(root, rules, names, state, answers=None, confidence=1.0):
    """One question each, keyed by its own name, which is what a stage asks."""
    return ask_batch(root, rules, list(names), state, answers, confidence)


def ask(root, rules, name, state, answer=None, confidence=1.0):
    """One question, for harness decide."""
    return ask_many(root, rules, [name], state, {name: answer}, confidence)[0]


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
