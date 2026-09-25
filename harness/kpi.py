"""One ticket's figures, derived from its journal.

Nothing here is typed in, and nothing is stored that can be derived: a number
kept beside the thing it came from is a number that can disagree with it.
"""

from datetime import datetime

TRANSITIONS = ('advance', 'return', 'reopen', 'receipt')


def _moment(record):
    return datetime.fromisoformat(record['timestamp'])


def _stage_of(record):
    """The stage a record was written in, which is the one it may be leaving."""
    return record['stage']


def stage_seconds(records):
    """Seconds spent in each stage, counting every visit.

    A stage revisited after a return is counted twice, because rework is time
    spent and a figure that hides it flatters the ticket.
    """
    spent, entered, stage = {}, _moment(records[0]), records[0]['stage']
    for record in records[1:]:
        if record['kind'] not in TRANSITIONS:
            continue
        moment = _moment(record)
        spent[stage] = spent.get(stage, 0.0) + (moment - entered).total_seconds()
        entered, stage = moment, record['data'].get('to_stage', stage)
    return {name: int(seconds) for name, seconds in spent.items()}


def _receipt(records):
    for record in reversed(records):
        if record['kind'] == 'receipt':
            return record
    return None


def _check(records, sequence):
    for record in records:
        if record['sequence'] == sequence and record['kind'] == 'check':
            return record
    return None


def red_before_green(records):
    """True when every slice of every accepted tdd record cites a red that failed."""
    slices = [entry
              for record in records
              if record['kind'] == 'advance' and record['data'].get('from_stage') == 'tdd'
              for entry in record['data'].get('evidence', {}).get('slices', [])]
    if not slices:
        return None
    for entry in slices:
        red = _check(records, entry.get('red'))
        if red is None or not 0 < red['data'].get('exit_code', 0) < 124:
            return False
    return True


def _evidence(records, stage):
    """The evidence of the most recent accepted advance out of a stage."""
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == stage:
            return record['data'].get('evidence', {})
    return {}


def slices(records):
    """Slices planned at solution against slices proved at tdd.

    Proved counts every accepted tdd record and not just the latest, because a
    ticket that was returned proved slices in each attempt and paid tokens for
    each of them; `red_before_green` reads them the same way. A re-proved slice
    counts again for the same reason, so proven above planned is rework showing
    up rather than an error. Reading only the latest record said SEEN-104 proved
    one slice of the three it planned, and made its cost per slice three times
    too large.

    Null rather than zero for a ticket that plans none and proves none, which is
    every non-code ticket: zero slices would read as a ticket that was cut badly
    rather than one with no behaviour to cut.
    """
    planned = _evidence(records, 'solution').get('slices') or []
    proven = sum(len(record['data'].get('evidence', {}).get('slices') or [])
                 for record in records
                 if record['kind'] == 'advance' and record['data'].get('from_stage') == 'tdd')
    if not planned and not proven:
        return None
    return dict(planned=len(planned), proven=proven)


def _latest_route(records):
    """The route in force, which is the most recent one written.

    The most recent, because a plan changed by a return to solution is routed
    again and the later record describes the plan the work was done against.
    """
    for record in reversed(records):
        if record['kind'] == 'route':
            return record
    return None


def slice_windows(records):
    """Each slice's window: what it cost and which records fall inside it.

    Keyed by the slice the boundary closed, which is `done` and never
    `position`: a handoff names the slice in front of you, so keying by position
    charges every slice the window before it and charges the planning window,
    which belongs to no slice, to slice 1. On this ticket's own journal that put
    the 81,880 tokens of clarify and solution on slice 1 and left slice 4, the
    most expensive of the four, charged to nobody.

    A handoff carries the session's own spending at the moment it stopped, so a
    slice worked in a session that had already worked another costs the
    difference between the two boundaries. A boundary in a fresh session costs
    what that session had spent, because its figure starts from nothing.

    Null rather than zero wherever the figure is missing: a machine with no
    session logs records null, and subtracting one from a number would turn an
    absence into a total.
    """
    planned = len(_evidence(records, 'solution').get('slices') or [])
    windows, opened, previous, last = {}, 0, None, 0
    for record in records:
        closes = _closes(record, last, planned)
        if closes is None:
            continue
        done, figures = closes
        output, session = figures.get('output_tokens'), figures.get('session')
        if done:
            spent = None
            if output is not None:
                spent = (output - previous['output_tokens']
                         if previous and previous['session'] == session else output)
            windows[done] = dict(spent=spent, opened=opened, closed=record['sequence'])
            last = done
        opened = record['sequence']
        if output is not None:
            previous = dict(session=session, output_tokens=output)
    return windows


def _closes(record, last, planned):
    """Which slice this record's boundary closed, and the figures it carried.

    A handoff says so itself. The accepted tdd advance closes whatever slice the
    last boundary left open, because the plan ends there and no handoff follows
    the final slice: without it the last slice of every ticket carried nothing,
    which is the fault keying by `done` was supposed to have cured and had not.
    F3 of the second review.

    Bounded by the plan, and a boundary whether or not it carries figures. The
    first version did neither, so a reworked ticket's second advance keyed a
    window past the end of the plan and its tokens were dropped, which made a
    reworked route look cheaper than it was; and on this ticket's own journal,
    where only the last advance carried figures, slice 4's window ran from the
    last handoff to the end and swallowed all four review rounds: 253,085 output
    tokens against a two-point slice, 62 per cent of the ticket. F2 of the third
    review. Rework belongs to no slice of the plan and is charged to none; the
    ticket's own token figure still counts it, because that is read from the
    logs over the whole window rather than from these boundaries.

    An advance carrying no figures still closes its slice, with nothing spent:
    the boundary is where the work stopped, and a missing figure is an absence
    rather than a reason to let the window run on.
    """
    data = record['data']
    if record['kind'] == 'handoff':
        return (data.get('slice') or {}).get('done'), data.get('figures') or {}
    if record['kind'] == 'advance' and data.get('from_stage') == 'tdd':
        following = last + 1
        return (following if following <= planned else 0), data.get('figures') or {}
    return None


def ran_on(records, window):
    """The model the greens inside a slice's window were actually recorded under.

    From the same windows the tokens come from, because they answer the same
    question: what happened between this slice's boundary and the one before.
    The first version read the accepted tdd record's citations instead, took
    `model` off the record envelope rather than `record['data']`, and indexed
    that record's slice list by route position, which a return makes mean
    something else; it was null for every slice of this ticket. F2 of the first
    review.

    The last green in the window, because that is the one that proved the slice.
    """
    if window is None:
        return None
    found = None
    for record in records:
        if not window['opened'] < record['sequence'] < window['closed']:
            continue
        data = record['data']
        if (record['kind'] == 'check' and data.get('phase') == 'green'
                and data.get('exit_code') == 0 and data.get('model')):
            found = data['model']
    return found


def cost_cents(model, tokens, prices):
    """What those output tokens cost on that model, or that nobody priced it.

    A whole number of cents, because amounts are cents as integers with a
    currency code and the table these come from says so of itself. A fraction of
    a cent is below the resolution the ground rule gives an amount, and a sum of
    rounded floats drifts from the sum of the rows a reader can see. F7 of this
    ticket's first review.

    Output only, because a handoff record carries output tokens and tool calls
    and nothing about input: a figure that silently included a guess at the
    input side would be worse than one that says what it covers.
    """
    if not prices or tokens is None:
        return None
    price = prices.get(model)
    if not price:
        return None
    return round(tokens * price['output'] / 1_000_000)


COST_BASIS = ('output tokens only, at the price of the model the slice ran on: a handoff record '
              'carries the session\'s output tokens and tool calls and nothing about input. '
              'routed_cost_cents prices the same tokens at the model the route chose, which in '
              'shadow is a counterfactual and not a cost')


def execution(records, rules=None):
    """What each slice was routed to, what it ran on and what it cost.

    Null rather than an empty list for a ticket nobody routed, which is every
    ticket delivered before SEEN-108: no route is not a route to nothing.
    """
    routed = _latest_route(records)
    if routed is None:
        return None
    from . import routing
    prices = ((rules or {}).get('routing') or {}).get('prices')
    windows = slice_windows(records)
    found = []
    for entry in routed['data']['execution']:
        window = windows.get(entry['position'])
        tokens = (window or {}).get('spent')
        actual = ran_on(records, window)
        tier = routing.tier_of(rules, actual) if rules and actual else None
        found.append(dict(position=entry['position'],
                          name=entry.get('name'),
                          points=entry.get('points'),
                          model=entry['model'],
                          effort=entry['effort'],
                          source=entry['source'],
                          rule=entry.get('rule'),
                          # What the route chose, beside what the work actually
                          # ran on. In shadow they differ, and that is the
                          # comparison SEEN-109 is for.
                          ran_on=actual,
                          ran_on_tier=tier,
                          output_tokens=tokens,
                          # What it cost, at the price of the model that ran it.
                          cost_cents=cost_cents(tier, tokens, prices),
                          # What the route would have cost. A counterfactual,
                          # named as one: in shadow nothing ran on it.
                          routed_cost_cents=cost_cents(entry['model'], tokens, prices),
                          cost_basis=COST_BASIS))
    return found


def sessions(records):
    """How many sessions wrote this journal, or that nobody can tell.

    Null rather than 1 for the nineteen journals written before the envelope
    carried a session: a record that cannot say which session wrote it cannot
    say it was the same one. A journal that gained the field halfway, as
    SEEN-104's own did, counts the sessions that can be seen, which is a lower
    bound and is recorded as one.
    """
    seen = {record.get('session') for record in records if record.get('session')}
    return len(seen) or None


def output_tokens_per_slice(tokens, counted):
    """What one slice cost, by the only division the journal supports.

    Two slices worked in one session cannot be told apart by division; the
    handoff records carry each session's own figures so a later ticket can
    refine this without re-deriving the data.
    """
    if not tokens or not counted:
        return None
    output = tokens.get('output_tokens')
    return None if output is None else round(output / counted, 1)


def subagents(records):
    """How this ticket was worked: briefs from the scout, and the review's own kind.

    Null rather than false when the journal holds neither a brief nor an accepted
    review. Nineteen journals were written before either agent existed, and a
    record that cannot say whether an agent was used cannot say one was not; the
    same rule `sessions` already applies to the session field.

    `both` is the figure the sprint report divides on: a brief recorded from an
    agent and a review disclosed as coming from a subagent. One without the other
    is a ticket that used one of the two, which is not what the fifth criterion of
    SEEN-105 asks the report to compare.
    """
    briefs = [record for record in records
              if record['kind'] == 'note' and record['data'].get('agent')]
    review = _evidence(records, 'review').get('independence')
    if not briefs and review is None:
        return None
    from . import agents as roster
    named = sorted({record['data']['agent'] for record in briefs})
    # F4 in SEEN-105's first review: any note carrying any agent name counted as a
    # brief, so a note from the reviewer made `both` true and the report
    # attributed a saving to a ticket the scout never ran on.
    return dict(briefs=len(briefs),
                agents=named,
                review=review,
                both=roster.SCOUT['name'] in named and review == 'subagent')


def _latest_triage(records):
    for record in reversed(records):
        if record['kind'] == 'triage':
            return record
    return None


def review_windows(records):
    """Every span a reviewer ran in: a triage, and the record that closed it.

    One span per review round, because a ticket reviewed twice ran a reviewer
    twice and paid for both, and a second triage inside one round closes the
    first for the same reason. What must not be inside a span is the rework
    between two of them: that is where the scout runs and, from SEEN-108, the
    implementer subagent, and they write the same sidechain entries.

    G3 of SEEN-107's third review, which found one window opening at the first
    triage of the ticket and closing at the last review advance, spanning two
    returns and two whole tdd attempts on this ticket alone. A round still open
    runs to the last record, which is a lower bound and reads as one.
    """
    spans, opened = [], None
    for record in records:
        leaves_review = (record['kind'] in ('advance', 'return')
                         and record['data'].get('from_stage') == 'review')
        if opened is not None and (record['kind'] == 'triage' or leaves_review):
            spans.append((opened, record['timestamp']))
            opened = None
        if record['kind'] == 'triage':
            opened = record['timestamp']
    if opened is not None:
        spans.append((opened, records[-1]['timestamp']))
    return spans


def reviewer_tokens(root, records):
    """The reviewer's own cost on this ticket, read from the log over its windows.

    The one place the log and the journal meet, so there is one thing for a test
    to hold: G2 of the third review found the only guard on this asserting that
    two words appeared in delivery's source, which passed with the behaviour gone.
    """
    from . import cost
    windows = review_windows(records)
    return cost.tokens_over(root, windows, sidechain=True) if windows else None


def review_triage(records, reviewer_tokens=None):
    """What the review triage settled on this ticket, and what the reviewer cost.

    Null rather than a hollow section on a journal with no triage record. Every
    ticket delivered before SEEN-107 had none, and a ticket that could not have
    been triaged must not read as one that was triaged badly: the same rule
    `sessions` and `subagents` already apply.

    The excluded share is the figure SEEN-109 decides on. In shadow mode it is
    what the narrowing would have dropped while the reviewer still read
    everything, which is the only way to measure a saving before taking it.
    """
    latest = _latest_triage(records)
    if latest is None:
        return None
    data = latest['data']
    return dict(record=latest['sequence'],
                depth=data.get('review_depth'),
                # The share below is measured at the depth the model chose, not
                # at the one the rules enforced, so the row carries both: a
                # calibration that averages the share without knowing which is
                # which counts a saving on tickets where nothing could have been
                # saved. M3 of the seventh review, guarded from the eighth.
                model_depth=data.get('model_depth'),
                shadow=data.get('shadow'),
                asked=(data.get('jev') or {}).get('asked'),
                rules=list(data.get('rules') or []),
                files=len(data.get('files') or []),
                focus=len(data.get('focus') or []),
                excluded=len(data.get('would_exclude') or []),
                excluded_share=data.get('excluded_share'),
                # Read from the log by `reviewer_tokens` above, which both
                # delivery and the report call. Null on a machine with no logs
                # and on a ticket whose reviewer never ran as a subagent, which
                # on this repository is still every ticket. G5 of the third
                # review: this used to say delivery could not supply it, which
                # both callers contradict.
                reviewer_output_tokens=(reviewer_tokens or {}).get('output_tokens'),
                reviewer_tokens=reviewer_tokens)


def coverage(records):
    for record in reversed(records):
        if record['kind'] == 'check' and record['data'].get('phase') == 'coverage':
            return dict(package=record['data'].get('package'),
                        lines=record['data'].get('lines'),
                        delta=record['data'].get('delta'))
    return None


def findings(records):
    """Review findings by severity, and how many were fixed rather than waived.

    A returned ticket is reviewed again and lists its findings again, so the
    same finding appears in several records. They are counted by id, most recent
    record wins, because a finding resolved on the second pass is one finding.
    """
    latest = {}
    for record in records:
        if record['kind'] != 'advance' or record['data'].get('from_stage') != 'review':
            continue
        for position, finding in enumerate(record['data'].get('evidence', {}).get('findings', [])):
            latest[finding.get('id') or f'{record["sequence"]}-{position}'] = finding
    by_severity, fixed, waived = {}, 0, 0
    for finding in latest.values():
        severity = finding.get('severity', 'unknown')
        by_severity[severity] = by_severity.get(severity, 0) + 1
        if finding.get('status') == 'resolved':
            fixed += 1
        else:
            waived += 1
    return dict(by_severity=by_severity, fixed=fixed, waived=waived)


def first_pass_ci(records):
    """One run per check on the delivered commit, all green, or None if unrecorded.

    The receipt started carrying the checks it verified with SEEN-091; tickets
    delivered before that have nothing to read, and null says so.
    """
    receipt = _receipt(records)
    checks = (receipt or {}).get('data', {}).get('checks')
    if not checks:
        return None
    return all(check.get('runs', 1) == 1 and check.get('conclusion') in ('success', 'skipped')
               for check in checks)


def measure(records, ticket, points=None, delivered_at=None, tokens=None, cost=None,
            reviewer_tokens=None, rules=None):
    """Everything a KPI record carries for one ticket."""
    if not records:
        return dict(ticket=ticket, delivered_at=delivered_at, points=points,
                    cycle_time_seconds=None, stage_seconds={}, attempts=None, rework=None,
                    red_before_green=None, coverage=None,
                    findings=dict(by_severity={}, fixed=0, waived=0),
                    first_pass_ci=None, tokens=tokens, cost=cost, escaped_defects=[],
                    slices=None, sessions=None, output_tokens_per_slice=None,
                    subagents=None, review_triage=None, execution=None, harness_version=None,
                    note='Measured from the ticket file: this ticket has no journal')
    receipt = _receipt(records)
    rework = sum(1 for record in records if record['kind'] in ('return', 'reopen'))
    cut = slices(records)
    return dict(ticket=ticket,
                delivered_at=receipt['timestamp'] if receipt else delivered_at,
                points=points,
                cycle_time_seconds=(int((_moment(receipt) - _moment(records[0])).total_seconds())
                                    if receipt else None),
                stage_seconds=stage_seconds(records),
                attempts=records[-1]['attempt'],
                rework=rework,
                red_before_green=red_before_green(records),
                coverage=coverage(records),
                findings=findings(records),
                first_pass_ci=first_pass_ci(records),
                tokens=tokens,
                cost=cost,
                escaped_defects=[],
                slices=cut,
                sessions=sessions(records),
                subagents=subagents(records),
                review_triage=review_triage(records, reviewer_tokens),
                execution=execution(records, rules),
                output_tokens_per_slice=output_tokens_per_slice(
                    tokens, (cut or {}).get('proven') or (cut or {}).get('planned')),
                harness_version=records[-1].get('harness_version'),
                note=None)
