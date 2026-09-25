"""Whether three knowledge tools paid for the context they occupy.

codegraph, graphify and repowise each put a set of tool schemas into every
session before a ticket is read. SEEN-099 recorded a baseline of ten tickets
delivered before any of them existed, and the rule for reading the comparison,
so that the figure is judged by a rule rather than the rule by the figure.

Nothing here divides two numbers and calls it evidence: below a minimum number
of qualifying tickets it says how many there are and concludes nothing.
"""


def _per_point(tickets, field):
    points = sum(ticket['points'] or 0 for ticket in tickets)
    if not points:
        return None
    return round(sum(ticket[field] for ticket in tickets) / points, 1)


def _per_slice(tickets, field='output_tokens'):
    """The same division by slices proved, for the tickets that have any.

    Null rather than zero where no ticket carries a slice count: every ticket
    delivered before SEEN-104 was planned in no slices at all, and dividing by
    the tickets that were would compare two different things.
    """
    counted = sum((ticket.get('slices') or {}).get('proven') or 0 for ticket in tickets)
    if not counted:
        return None
    return round(sum(ticket[field] for ticket in tickets) / counted, 1)


UNKNOWN = 'unknown'


def cost_by_model(tickets):
    """What a point cost on each model, from the slices that actually ran on it.

    Grouped by the model the work ran on and never by the one it was routed to.
    In shadow every slice still runs on whatever model its session is, so a
    table keyed by the route would price a slice's real tokens at a model that
    never touched it and print a saving that had not happened, in the very table
    SEEN-109 decides from. F5 of this ticket's first review. The routed price is
    carried per slice as `routed_cost_cents` and named a counterfactual there;
    comparing the two is `report --calibration`, which is SEEN-109's.

    Divided by the points the slices themselves carried rather than by the
    tickets', because one ticket's slices can run on three models and a division
    by the ticket would charge all of them to whichever came first.

    A slice with no cost still counts its points and leaves the division null:
    the honest answer on a machine with no session logs is that nobody knows
    what it cost, and a mean over the ones that happened to have figures would
    be a number about the machines rather than about the models. A slice nobody
    can say ran anywhere gets its own row rather than being dropped.
    """
    by_model = {}
    for ticket in tickets:
        for entry in ticket.get('execution') or []:
            found = by_model.setdefault(entry.get('ran_on_tier') or UNKNOWN,
                                        dict(slices=0, points=0, priced_points=0,
                                             cost_cents=0, output_tokens=0, priced=0))
            found['slices'] += 1
            found['points'] += entry.get('points') or 0
            if entry.get('cost_cents') is not None:
                found['cost_cents'] += entry['cost_cents']
                found['priced'] += 1
                found['priced_points'] += entry.get('points') or 0
            if entry.get('output_tokens') is not None:
                found['output_tokens'] += entry['output_tokens']
    for found in by_model.values():
        priced, priced_points = found.pop('priced'), found['priced_points']
        # Divided by the points it could price and never by all of them: a
        # numerator covering two slices over a denominator covering three
        # understates the model, which is what this function's own docstring
        # says it must not do. On SEEN-108's figures opus read 103.8 cents per
        # point where its priced slices gave 173.0. F3 of the fourth review.
        #
        # A whole number of cents, as the amounts it sums are, and nothing at
        # all where nothing was priced: zero is a claim that a slice was free.
        found['cost_cents'] = round(found['cost_cents']) if priced else None
        found['cost_per_point'] = (round(found['cost_cents'] / priced_points, 2)
                                   if priced and priced_points else None)
    return by_model


def worked_with_agents(tickets, since=''):
    """Tickets whose journal says both agents were used, after they existed.

    The fifth criterion of SEEN-105 compares the main session's cost on those
    against the baseline, so they are divided on their own rather than mixed into a
    figure that cannot say which tickets paid for what.

    The date is the rule SEEN-098 wrote for its own tool: a ticket that installed
    one was not worked with it. G4 of SEEN-105's second review found the ticket that
    built the agents counting itself, which would have made the row the mean of the
    first ticket worked with them and the one that could not have been.
    """
    return [ticket for ticket in tickets
            if (ticket.get('subagents') or {}).get('both')
            and (ticket.get('started') or '') >= since]


def qualifying(tickets, since):
    """Tickets started after both tools existed, with figures to compare.

    A ticket that installed a tool was not worked with it, and a ticket whose
    session logs are gone has nothing to contribute, so neither counts.
    """
    return [ticket for ticket in tickets
            if (ticket.get('started') or '') >= since
            and ticket.get('output_tokens') is not None
            and ticket.get('tool_calls') is not None
            and ticket.get('points')]


def compare(tickets, baseline, minimum, since='', agents_from=''):
    """The two rows, the baseline beside them, and what the rule points to."""
    counted = qualifying(tickets, since)
    with_agents = worked_with_agents(counted, agents_from)
    totals = baseline['totals']
    section = dict(tickets=len(counted),
                   tickets_with_agents=len(with_agents),
                   tickets_named_with_agents=[ticket['ticket'] for ticket in with_agents],
                   output_tokens_per_point_with_agents=_per_point(with_agents, 'output_tokens'),
                   minimum=minimum,
                   output_tokens_per_point=_per_point(counted, 'output_tokens'),
                   output_tokens_per_slice=_per_slice(counted),
                   tool_calls_per_point=_per_point(counted, 'tool_calls'),
                   baseline_output_tokens_per_point=totals['output_tokens_per_point'],
                   baseline_tool_calls_per_point=totals['tool_calls_per_point'],
                   baseline_points=totals['points'],
                   conclusion=None,
                   not_measurable=None)
    if len(counted) < minimum:
        section['not_measurable'] = (
            f'The context budget comparison: {len(counted)} of {minimum} qualifying tickets '
            'have delivered, so the figures are reported and nothing is concluded from them')
        return section
    if section['output_tokens_per_point'] <= totals['output_tokens_per_point']:
        section['conclusion'] = (
            f'Keep all three: {section["output_tokens_per_point"]} output tokens per point '
            f'against a baseline of {totals["output_tokens_per_point"]}, so the tools paid for '
            'the context they occupy.')
    else:
        section['conclusion'] = (
            f'Remove one, graphify first: {section["output_tokens_per_point"]} output tokens '
            f'per point against a baseline of {totals["output_tokens_per_point"]}. codegraph '
            'and repowise can partly answer its questions. The call is the founder\'s.')
    return section


def _subject(record):
    """What a graph record asked about, as the command carries it."""
    command = record['data'].get('command') or []
    return command[-1] if len(command) > 2 else None


def overlaps(records):
    """Subjects asked of more than one tool on one ticket.

    The test of the design: a question with two right addressees means one tool
    is carrying schemas for answers another already gives. Read from what was
    actually asked rather than from a table of what might overlap, because a
    table written in advance is an opinion.
    """
    asked = {}
    for record in records:
        subject = _subject(record)
        source = record['data'].get('source')
        if not subject or not source:
            continue
        asked.setdefault((record['ticket'], subject), set()).add(source)
    return [dict(ticket=ticket, subject=subject, tools=sorted(tools))
            for (ticket, subject), tools in sorted(asked.items()) if len(tools) > 1]
