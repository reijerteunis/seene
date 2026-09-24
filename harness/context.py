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


def worked_with_agents(tickets):
    """Tickets whose journal says both agents were used.

    The fifth criterion of SEEN-105 compares the main session's cost on those
    against the baseline, so they are divided on their own rather than mixed into
    a figure that cannot say which tickets paid for what.
    """
    return [ticket for ticket in tickets if (ticket.get('subagents') or {}).get('both')]


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


def compare(tickets, baseline, minimum, since=''):
    """The two rows, the baseline beside them, and what the rule points to."""
    counted = qualifying(tickets, since)
    with_agents = worked_with_agents(counted)
    totals = baseline['totals']
    section = dict(tickets=len(counted),
                   tickets_with_agents=len(with_agents),
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
