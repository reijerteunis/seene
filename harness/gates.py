"""What each stage gate proves before a ticket may leave its stage.

Three layers, one job each. The stage template declares which fields must be
present; this module declares the relations between records, which no template
can express; thresholds.toml declares the numbers and vocabularies. A gate
checks that recorded evidence exists, is current and is ordered. It cannot check
that a conclusion is correct, and it does not pretend to.
"""

import json

from . import checks
from .errors import HarnessError, require
from .paths import ENUMERATED_KEYS, NON_CODE_TEMPLATE, TEMPLATE_FOR_STAGE, TEMPLATES

MODES = ('code', 'non-code')
# How a review discloses whose context it came from. A subagent is a context
# boundary and not independence by itself, so it is its own word rather than a
# second meaning of independent: the escaped-defect figures are read per kind
# later, and a word covering both could not answer which kind caught what.
INDEPENDENCE = ('independent', 'subagent', 'self-review')
SLICE_KEYS = ('name', 'points', 'files', 'red')
POLICY_GATE_ACTION_KEYS = ('reversibility', 'action_type', 'euro_impact_estimator')
FINDING_KEYS = ('id', 'severity', 'claim', 'failure_scenario', 'status', 'resolution')


def template_name(stage, mode=None):
    if stage == 'tdd' and mode == 'non-code':
        return NON_CODE_TEMPLATE
    require(stage in TEMPLATE_FOR_STAGE, f'Stage {stage} has no evidence template')
    return TEMPLATE_FOR_STAGE[stage]


def load_template(root, stage, mode=None):
    path = root / TEMPLATES / template_name(stage, mode)
    require(path.is_file(), f'Missing template: {path}')
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise HarnessError(f'Template {path.name} is not readable JSON: {error}')


def mode_of(data):
    """A record's mode, with silence meaning code.

    Nine solution records were written before the field existed, and a gate that
    invalidates history to gain a field is the worse trade.
    """
    return data.get('mode', 'code')


def for_mode(template, stage, mode, data=None):
    """The fields a stage requires of this kind of ticket.

    A non-code ticket has no tests to write first, and until SEEN-103 it had to
    write some anyway to reach the stage where it said so. The tdd stage solves
    the same problem with a whole second template; one field out of eleven does
    not justify a second one here.
    """
    if stage == 'solution' and mode == 'non-code':
        return {key: value for key, value in template.items()
                if key not in ('tests_first', 'slices')}
    # A review names the reviewer's session only when it discloses a subagent,
    # which is the one disclosure the gate checks the value against. A review by
    # the other assistant has a context of its own by construction, and on a
    # self-review the value would only restate the implementer's own session.
    if stage == 'review' and (data or {}).get('independence') != 'subagent':
        return {key: value for key, value in template.items() if key != 'reviewer_session'}
    return template


def _filled(value):
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def require_template_fields(template, data):
    """Every key the template carries must be answered.

    A key the template ships as an empty list may stay empty; anything else must
    hold a real value, because an empty answer to a question the template asks
    is the same as not answering it.
    """
    for key, example in template.items():
        require(key in data, f'Missing required field: {key}')
        value = data[key]
        if isinstance(example, bool):
            require(isinstance(value, bool), f'Field {key} must be true or false')
        elif isinstance(example, int) and not isinstance(example, bool):
            require(isinstance(value, int) and not isinstance(value, bool),
                    f'Field {key} must be a recorded record number')
        elif isinstance(example, str):
            require(isinstance(value, str) and value.strip(), f'Field {key} must not be empty')
        elif isinstance(example, list):
            require(isinstance(value, list), f'Field {key} must be a list')
            require(example == [] or value, f'Field {key} must not be empty')
            for entry in value:
                require(_filled(entry), f'Field {key} holds an empty entry')
        elif isinstance(example, dict):
            require(isinstance(value, dict), f'Field {key} must be an object')


def _strings(value, key=None):
    """Every free-text string in a document, skipping enumerated answers."""
    if isinstance(value, dict):
        for name, item in value.items():
            if name not in ENUMERATED_KEYS:
                yield from _strings(item, name)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, key)
    elif isinstance(value, str):
        yield value


def reject_placeholders(template, data):
    """Refuse evidence still carrying the template's example prose.

    Copying a template and advancing without editing it would record a claim
    nobody made, so unchanged example text counts as a missing answer.
    """
    examples = set(_strings(template))
    for value in _strings(data):
        require(value not in examples,
                f'Replace the template text before advancing: "{value}"')


def record_at(records, number):
    require(isinstance(number, int) and not isinstance(number, bool),
            f'Not a record number: {number!r}')
    for record in records:
        if record['sequence'] == number:
            return record
    raise HarnessError(f'Record {number} is not in this journal')


def cited_check(records, number, phase, current):
    """A check a stage record points at, confirmed to be usable evidence here.

    A check counts only for the stage and attempt that produced it, so evidence
    from before a return cannot be quietly reused after one.
    """
    record = record_at(records, number)
    require(record['kind'] == 'check', f'Record {number} is not a check')
    require(record['stage'] == current['stage'] and record['attempt'] == current['attempt'],
            f'Check {number} belongs to another stage or attempt; run it again')
    require(record['data']['phase'] == phase,
            f'Expected a {phase} check at record {number}, found {record["data"]["phase"]}')
    if phase == 'red':
        require(checks.demonstrates_failure(record['data']),
                f'Check {number} is cited as a RED but did not fail: it exited '
                f'{record["data"]["exit_code"]}')
    else:
        require(record['data']['exit_code'] == 0,
                f'Check {number} is cited as a {phase} but exited {record["data"]["exit_code"]}')
    return record


def latest_evidence(records, stage):
    """The evidence of the most recent accepted advance out of a stage."""
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == stage:
            return record['data'].get('evidence', {})
    return None


def _clarify(data, records, current, repository, thresholds):
    require(data['open_questions'] == [],
            'Answer every open question, or record the decision to defer it, before advancing: '
            + '; '.join(str(question) for question in data['open_questions']))
    return {}


def _slice_plan(data, thresholds):
    """The slices a code-mode ticket plans, and the two caps they may not break.

    The caps are about what one context can hold, which is why they are counted
    per slice and per plan and not against the ticket's estimate. A plan whose
    points disagree with the forecast is reported and allowed: a gate that made
    the two equal would turn every re-estimate into a returned record.
    """
    limits = thresholds['session']
    slices = data['slices']
    require(len(slices) <= limits['max_slices_per_ticket'],
            f'This plan has {len(slices)} slices and a ticket may plan at most '
            f'{limits["max_slices_per_ticket"]}. A plan that needs more is a ticket that is too '
            'big, and it is split the way SEEN-089 and SEEN-096 were')
    total = 0
    for position, entry in enumerate(slices, start=1):
        require(isinstance(entry, dict), f'Slice {position} must be an object')
        for key in SLICE_KEYS:
            require(_filled(entry.get(key)), f'Slice {position} is missing {key}')
        points = entry['points']
        require(isinstance(points, int) and not isinstance(points, bool) and points > 0,
                f'Slice {position} must carry its points as a whole number above zero, '
                f'not {points!r}')
        require(points <= limits['max_points_per_slice'],
                f'{entry["name"]} carries {points} points, over the '
                f'{limits["max_points_per_slice"]} points one slice may carry. A slice is what '
                'one session can hold start to finish; split it, or split the ticket')
        total += points
    return total


def _solution(data, records, current, repository, thresholds):
    clarified = latest_evidence(records, 'clarify') or {}
    if clarified.get('changes_agent_action'):
        declaration = data.get('policy_gate_action')
        require(isinstance(declaration, dict) and declaration,
                'This ticket changes an agent action, so policy_gate_action must declare '
                'reversibility, action_type and euro_impact_estimator')
        for key in POLICY_GATE_ACTION_KEYS:
            require(_filled(declaration.get(key)), f'policy_gate_action is missing {key}')
    if mode_of(data) == 'non-code':
        return {}
    return dict(slice_points=_slice_plan(data, thresholds))


def _tdd(data, records, current, repository, thresholds):
    mode = mode_of(data)
    require(mode in MODES, f'Unknown mode: {mode!r}; use {" or ".join(MODES)}')
    solution = latest_evidence(records, 'solution')
    # No solution record is not a record saying code: there is nothing to
    # disagree with, and the stage order is what requires one.
    if solution is not None:
        planned = mode_of(solution)
        require(mode == planned,
                f'The solution record planned {planned} and this tdd record says {mode}. A '
                'ticket that changes its mind about having behaviour to prove says so in a note '
                'and returns to solution, rather than changing it between stages')
    if mode == 'non-code':
        return _non_code(data, thresholds)
    slices = data['slices']
    require(slices, 'Code changes need at least one slice in slices')
    _require_coverage(records, current)
    regression = cited_check(records, data['regression'], 'regression', current)
    previous_green = 0
    for position, slice_ in enumerate(slices, start=1):
        require(isinstance(slice_, dict), f'Slice {position} must be an object')
        for key in ('behaviour', 'failure_reason'):
            require(_filled(slice_.get(key)), f'Slice {position} is missing {key}')
        red = cited_check(records, slice_.get('red'), 'red', current)
        green = cited_check(records, slice_.get('green'), 'green', current)
        require(previous_green < red['sequence'] < green['sequence'] <= regression['sequence'],
                f'Slice {position} is out of order; each red must precede its green, slices '
                'must not overlap, and the regression must be the last check')
        previous_green = green['sequence']
    return {}


def _require_coverage(records, current):
    """A code change measures the gated package, and may not let it fall.

    A first measurement has no baseline and is not a regression; anything after
    that has a number to be compared with.
    """
    measurements = [record for record in records
                    if record['kind'] == 'check' and record['stage'] == 'tdd'
                    and record['attempt'] == current['attempt']
                    and record['data'].get('phase') == 'coverage']
    require(measurements,
            'No coverage measurement for this attempt: run harness coverage <ticket> '
            '--actor <actor> before advancing')
    latest = measurements[-1]['data']
    delta = latest.get('delta')
    require(delta is None or delta >= 0,
            f'Coverage on {latest.get("package")} fell by {delta}: '
            f'{latest.get("baseline")} to {latest.get("lines")}. Cover what the change added, '
            'or say in a note why the fall is right and raise the baseline deliberately')


def _non_code(data, thresholds):
    change_types = thresholds['non_code']['change_types']
    require(data.get('change_type') in change_types,
            f'Unknown change_type: {data.get("change_type")!r}; use one of {", ".join(change_types)}')
    require(_filled(data.get('reason')), 'A non-code change needs a reason')
    if data['change_type'] == 'verification':
        require(data.get('sources'),
                'A verification must name its sources; a fact without a source is not verified')
    return {}


def _review(data, records, current, repository, thresholds):
    require(latest_evidence(records, 'tdd') is not None, 'Complete the TDD stage before review')
    require(data['verdict'] == 'pass',
            f'A verdict of {data["verdict"]!r} is a return, not an advance; use harness return')
    severities = thresholds['review']['severities']
    for finding in data['findings']:
        require(isinstance(finding, dict), 'Every finding must be an object')
        for key in FINDING_KEYS[:-1]:
            require(_filled(finding.get(key)), f'A finding is missing {key}')
        require(finding['severity'] in severities,
                f'Unknown severity: {finding["severity"]!r}; use one of {", ".join(severities)}')
        require(finding['status'] == 'resolved',
                f'Finding {finding["id"]} is {finding["status"]}; resolve every finding or '
                'return the ticket, and do not relabel it')
        require(_filled(finding.get('resolution')), f'Finding {finding["id"]} is missing resolution')
    if _needs_two_reviewers(records):
        require(_filled(data.get('second_reviewer')),
                'This change touches billing or the policy gate, so the review needs a '
                'second_reviewer and a security checklist')
        require(data.get('security_checklist'), 'The security checklist must be answered')
    require(data['independence'] in INDEPENDENCE,
            f'Disclose independence as {", ".join(INDEPENDENCE)}')
    worked_by = _tools_of(records)
    if data['independence'] == 'independent':
        tools = set(worked_by)
        tools.add(str(data['reviewer']).split(':')[0])
        require(len(tools) > 1,
                'A review is not independent when one tool wrote every record on this ticket')
    if data['independence'] == 'subagent':
        _require_another_context(data, records)
    if _needs_two_reviewers(records):
        known = set(thresholds['actors']['tools'])
        # F6: a prefix that is not a tool this repository knows is a typo, not the
        # other assistant, and it satisfied the one control that stands where a
        # declared session cannot be verified.
        named = {str(data.get(key) or '').partition(':')[0]
                 for key in ('reviewer', 'second_reviewer')} & known
        require(named - _implementer_tools(records),
                'This change touches billing or the policy gate, so the review comes from the '
                f'other assistant: {", ".join(sorted(_implementer_tools(records)))} wrote this '
                f'ticket and {", ".join(sorted(named)) or "no tool this repository knows"} '
                'reviewed it. A subagent is a context boundary, not independence by itself, and a '
                'declared session cannot stand in for it where a missed defect costs money. Name '
                f'the reviewer as one of {", ".join(sorted(known))} and a role')
    return dict(tree=repository.fingerprint())


def _tools_of(records):
    """The tools that wrote this ticket's records, read from the actor on each."""
    return {record['actor'].split(':')[0] for record in records if record.get('actor')}


def _implementer_tools(records):
    """The tools that wrote the work, which is not the tools that wrote a record.

    F2 in SEEN-105's first review: the other assistant records a `return` when it
    sends work back, which is the documented path, and reading that as authorship
    made the gate refuse the very review it demands. A reviewer's own records are
    therefore not authorship.
    """
    tools = set()
    for record in records:
        tool, _, role = (record.get('actor') or '').partition(':')
        if tool and role != 'reviewer':
            tools.add(tool)
    return tools


def _sessions_of(records):
    """Every session that wrote a record on this ticket.

    F5 in SEEN-105's first review: this was scoped to the current attempt, so the
    session that worked attempt 1 passed as the reviewer's context in attempt 2.
    Criterion 3 says the implementer's session, and a session that wrote any
    record on this ticket is one.
    """
    return {record.get('session') for record in records if record.get('session')}


def _require_another_context(data, records):
    """A subagent review names a session, and not one the implementer worked in.

    A Claude Code subagent inherits its parent's session id, observed and recorded
    in SEEN-105's journal at record 7, so the harness cannot derive this and the
    record declares it. The gate refuses what it can see: a value that is one of
    the sessions which wrote this attempt's records, or the session running the
    advance. A value typed to pass is not detectable and the gate does not pretend
    to detect it; what stands where that matters is the cross-tool review.
    """
    from . import sessions
    declared = str(data.get('reviewer_session') or '').strip()
    require(declared,
            'A subagent review must name the reviewer_session it came from. The harness cannot '
            'read it, because a subagent inherits its parent session id, so the session that '
            'spawned the reviewer records the identifier it gave it')
    own = _sessions_of(records)
    running = sessions.current()
    if running:
        own.add(running)
    require(declared not in own,
            f'{declared} is a session that worked this ticket, so a review from it is a '
            'self-review however it is disclosed. Disclose it as self-review, or have the review '
            'done in a context that did not write the code')


GATES = {'clarify': _clarify, 'solution': _solution, 'tdd': _tdd, 'review': _review}


def _needs_two_reviewers(records):
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'solution':
            return any(decision['question'] == 'touches_billing_or_policy_gate'
                       and decision['outcome'] == 'yes'
                       for decision in record['data'].get('decisions', []))
    return False


def evaluate(stage, data, records, current, repository, thresholds):
    """Run one stage gate and return the facts the harness adds to the record."""
    require(isinstance(data, dict), 'Stage evidence must be a JSON object')
    gate = GATES.get(stage)
    require(gate is not None,
            f'Stage {stage} has no advance out of it'
            + ('; verify-delivery is its stage gate' if stage == 'deliver' else ''))
    if stage in ('solution', 'tdd'):
        require(mode_of(data) in MODES,
                f'Unknown mode: {data.get("mode")!r}; use {" or ".join(MODES)}')
    template = load_template(repository.root, stage, data.get('mode'))
    # Both checks read the same shape. A field this kind of record does not carry
    # is not required and its example is not placeholder text either: a non-code
    # solution record that left the tests_first example in place would otherwise
    # be refused for prose the gate had just decided not to ask for.
    shaped = for_mode(template, stage, mode_of(data), data)
    require_template_fields(shaped, data)
    # F8 in SEEN-105's first review: the examples come from the whole template, so
    # prose from a field this record does not carry is still placeholder text
    # wherever it was pasted. Only the dropped field's own value is left out.
    reject_placeholders(template, {key: value for key, value in data.items() if key in shaped})
    return gate(data, records, current, repository, thresholds)
