"""Weekly and sprint reports, aggregated from the tickets' own figures.

A report is written, committed and read later, so nothing enters one that could
not be shown to anyone: the same rule the journal uses applies here.
"""

from datetime import date, datetime
import json
import os
import re

from . import context, secrets
from .errors import require
from .paths import REPORTS

FRONTMATTER = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def _field(text, name):
    match = re.search(rf'^{name}:\s*(.+)$', text, re.MULTILINE)
    return match.group(1).strip() if match else None


def frontmatter(path):
    """The ticket's own metadata, which is where points and status live."""
    match = FRONTMATTER.match(path.read_text(errors='replace'))
    return match.group(1) if match else ''


def within_week(tickets, when):
    """Tickets whose receipt falls in the ISO week of a date, in UTC."""
    target = date.fromisoformat(when).isocalendar()[:2]
    covered = []
    for ticket in tickets:
        delivered = ticket.get('delivered_at')
        if not delivered:
            continue
        moment = datetime.fromisoformat(delivered.replace('Z', '+00:00'))
        if moment.date().isocalendar()[:2] == target:
            covered.append(ticket)
    return covered


def _median(values):
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def totals(tickets):
    """The figures a report leads with, derived from the tickets it covers."""
    cycles = [ticket['cycle_time_seconds'] for ticket in tickets
              if ticket.get('cycle_time_seconds') is not None]
    reworks = [ticket['rework'] for ticket in tickets if ticket.get('rework') is not None]
    known = [ticket['first_pass_ci'] for ticket in tickets
             if ticket.get('first_pass_ci') is not None]
    by_severity = {}
    for ticket in tickets:
        for severity, count in (ticket.get('findings') or {}).get('by_severity', {}).items():
            by_severity[severity] = by_severity.get(severity, 0) + count
    return dict(tickets=len(tickets),
                points_delivered=sum(ticket.get('points') or 0 for ticket in tickets),
                median_cycle_time_seconds=_median(cycles),
                rework_per_ticket=round(sum(reworks) / len(reworks), 2) if reworks else None,
                first_pass_ci_rate=(sum(1 for value in known if value) / len(known))
                if known else None,
                first_pass_ci_unknown=len(tickets) - len(known),
                findings_by_severity=by_severity)


def escaped_defects(root, ticket):
    """Tickets whose frontmatter says they fix this one."""
    found = []
    for path in sorted((root / 'docs' / 'tickets').glob('*.md')):
        header = frontmatter(path)
        fixes = _field(header, 'fixes')
        if fixes and ticket in fixes:
            identifier = _field(header, 'id')
            if identifier:
                found.append(identifier)
    return found


def write(root, name, markdown, payload):
    """Write a report and its JSON, refusing anything that carries a credential."""
    carried = secrets.leaked(markdown + json.dumps(payload, ensure_ascii=False), os.environ)
    require(not carried,
            f'This report carries the value of {", ".join(carried)} from the environment. '
            'A report is committed and read by people; credentials do not go in one')
    directory = root / REPORTS
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f'{name}.md').write_text(markdown)
    (directory / f'{name}.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    return dict(report=str(REPORTS / f'{name}.md'), data=str(REPORTS / f'{name}.json'))


def _duration(seconds):
    if seconds is None:
        return 'not measured'
    hours, rest = divmod(int(seconds), 3600)
    return f'{hours}h {rest // 60}m' if hours else f'{rest // 60}m'


def render_context(section, rules):
    """The context budget and what the figures say about it, or that they cannot.

    The rule is printed beside the numbers every time, so a reader never has to
    take on trust that it was chosen before them.
    """
    lines = ['', '## The context budget', '']
    lines += [f'- {rule}' for rule in rules['rules']]
    per_point = section['output_tokens_per_point']
    calls = section['tool_calls_per_point']
    per_slice = section.get('output_tokens_per_slice')
    lines += ['', '| Measure | This report | Baseline |', '|---|---|---|',
              f'| Output tokens per point | {per_point if per_point is not None else "not measured"} '
              f'| {section["baseline_output_tokens_per_point"]} |',
              f'| Output tokens per slice | {per_slice if per_slice is not None else "not measured"} '
              '| none: the baseline predates slices |',
              f'| Tool calls per point | {calls if calls is not None else "not measured"} '
              f'| {section["baseline_tool_calls_per_point"]} |',
              f'| Qualifying tickets | {section["tickets"]} | {section["baseline_points"]} points '
              'over 10 tickets |']
    with_agents = section.get('output_tokens_per_point_with_agents')
    counted = section.get('tickets_with_agents') or 0
    lines += [f'| Output tokens per point, worked with the scout and the reviewer '
              f'| {with_agents if with_agents is not None else "not measured"} '
              f'| {section["baseline_output_tokens_per_point"]} |',
              f'| Tickets worked with both agents | {counted} | none: the baseline predates them |']
    # G4 of SEEN-105's second review: a mean nobody can attribute is a mean nobody
    # can check, so the row says which tickets are in it.
    named = section.get('tickets_named_with_agents') or []
    if named:
        lines += ['', f'Worked with the scout and the reviewer: {", ".join(named)}.']
    lines += render_cost(section.get('cost_by_model') or {}, section.get('prices'))
    lines += ['', f'**The rule, recorded before the numbers.** {rules["decision_rule"]}', '']
    if section['conclusion']:
        lines += [f'**What it points to.** {section["conclusion"]}', '',
                  "**The founder's call.** Not made here; it belongs in this report, written by "
                  'Ruud beside the line above.']
    else:
        lines += ['**What it points to.** Nothing yet. '
                  f'{section["not_measurable"]}']
    if section.get('overlaps'):
        lines += ['', '### One tool too many', '']
        for overlap in section['overlaps']:
            lines.append(f'- {overlap["ticket"]} asked about `{overlap["subject"]}` of both '
                         f'{" and ".join(overlap["tools"])}: one question, two right addressees.')
    return lines


def render_cost(by_model, prices):
    """What a point cost on each model, with the date the prices were read.

    Printed beside the figure every time rather than in a footnote: a price per
    token is stale the day it is written, and the answer to that is to say how
    old it is, not to report no figure at all. That is the amendment SEEN-108
    made to the line that said euros could not be reported.
    """
    if not by_model:
        return []
    currency = (prices or {}).get('currency', 'EUR')
    priced_on = (prices or {}).get('priced_on', 'an unrecorded date')
    lines = ['', '### Cost per point by the model the work ran on', '',
             f'| Model | Slices | Points | Points priced | Output tokens '
             f'| Cost ({currency} cents) | Cost per point |',
             '|---|---|---|---|---|---|---|']
    # Dearest first among the rows that could be priced, and the rest after
    # them. cost_cents is None for a row nothing could price, because zero is a
    # claim that a slice was free, and sorting on it raised TypeError and wrote
    # no report at all: the fourth review's F3 made the value right and the
    # fifth review's F1 found this sort still reading it as a number.
    def order(name):
        cost = by_model[name]['cost_cents']
        return (cost is not None, cost or 0)

    for model in sorted(by_model, key=order, reverse=True):
        found = by_model[model]
        per_point = found['cost_per_point']
        cost = found['cost_cents']
        lines.append(f'| {model} | {found["slices"]} | {found["points"]} '
                     f'| {found["priced_points"]} | {found["output_tokens"]} '
                     f'| {cost if cost is not None else "not measured"} '
                     f'| {per_point if per_point is not None else "not measured"} |')
    lines += ['',
              f'Prices read on {priced_on}, in {currency} cents per million tokens, from '
              '`[routing.prices]`. Output tokens only: a handoff record carries the session\'s '
              'output tokens and tool calls and nothing about input, so the figure says what it '
              'covers rather than guessing at the rest. Cost per point is the cost divided by '
              'the points it could price, which is the fourth column and not the third: a slice '
              'whose boundary carried no token figure counts its points and not its cost, so a '
              'row where the two differ does not divide the way it reads. Rows are the model '
              'each slice actually '
              'ran on, which while `[routing] shadow` is true is the session\'s model and not '
              'the routed one; what the route would have cost is carried per slice in kpi.json '
              'as `routed_cost_cents`; comparing the two is what `report --calibration` will do when '
              'SEEN-109 adds it, and no command does it today. A row named '
              f'`{context.UNKNOWN}` is slices whose session left no log to read a model from.']
    return lines


def render(title, tickets, figures, unmeasurable, context_section=None, context_rules=None):
    """A report anyone can read without opening a journal.

    The last section names what could not be measured and why, because a report
    that omits what it cannot measure reads as though everything were measured.
    """
    lines = [f'# {title}', '']
    lines += ['## What delivered', '',
              '| Ticket | Points | Cycle time | Attempts | Rework | Findings | Coverage |',
              '|---|---|---|---|---|---|---|']
    for ticket in tickets:
        findings = ticket.get('findings') or {}
        total = sum((findings.get('by_severity') or {}).values())
        coverage = ticket.get('coverage') or {}
        delta = coverage.get('delta')
        lines.append(
            f'| {ticket["ticket"]} | {ticket.get("points") or "-"} '
            f'| {_duration(ticket.get("cycle_time_seconds"))} '
            f'| {ticket.get("attempts") or "-"} | {ticket.get("rework") if ticket.get("rework") is not None else "-"} '
            f'| {total} ({findings.get("fixed", 0)} fixed, {findings.get("waived", 0)} waived) '
            f'| {"+" if isinstance(delta, (int, float)) and delta > 0 else ""}{delta if delta is not None else "-"} |')
    rate = figures['first_pass_ci_rate']
    first_pass = 'not measurable yet' if rate is None else f'{round(rate * 100)}%'
    rework = figures['rework_per_ticket']
    lines += ['', '## Against the targets', '',
              '| Measure | This report | Target |', '|---|---|---|',
              f'| Median cycle time | {_duration(figures["median_cycle_time_seconds"])} '
              '| under 2 days per ticket |',
              f'| Rework per ticket | {rework if rework is not None else "not measured"} '
              '| under 0.5 over a sprint |',
              f'| First-pass CI | {first_pass} | 80% |',
              f'| Points delivered | {figures["points_delivered"]} | against plan |']
    lines += ['', '## Findings', '']
    if figures['findings_by_severity']:
        for severity, count in sorted(figures['findings_by_severity'].items()):
            lines.append(f'- {severity}: {count}')
    else:
        lines.append('- none recorded')
    if context_section is not None:
        lines += render_context(context_section, context_rules)
    lines += ['', '## Not measurable yet', '']
    reasons = list(unmeasurable)
    if context_section is not None and context_section.get('not_measurable'):
        reasons.append(context_section['not_measurable'])
    lines += [f'- {reason}' for reason in reasons] or ['- nothing']
    return '\n'.join(lines) + '\n'
