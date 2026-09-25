"""What the triage and the routes actually cost, read from the journals.

SEEN-107's triage narrows what a reviewer reads and SEEN-108's routes send a
slice to a cheaper model. Both can cost more than they save, so both run in
shadow while the evidence accumulates and a rule written before the first
measurement decides. Everything here derives that evidence from records that
already exist: the triage record's `would_exclude` and `criteria_answers`, the
review advance's findings, the route record's `execution`, and the returns.

Nothing here writes. The rule lives in `[calibration]` in thresholds.toml, the
switch lives in `[review] triage_shadow` and `[routing] shadow`, and both are
lines a person changes in a diff a person reviews. The one thing that happens
without a person is the return to shadow: `effective_shadow` widens the
threshold's true with a stay-shadow verdict, so an escape puts the next triage
back in shadow with nothing edited and no race between a report and a rule.
"""

import re

from . import journal, report
from .paths import HISTORY, TICKETS

# The severities a missed finding is measured at. A low or a medium finding in a
# file the reviewer did not read is the saving working as intended; the question
# the window asks is whether anything expensive got through.
ESCAPING_SEVERITIES = ('high', 'blocking')


def journals(root):
    """Every ticket's records, by ticket id."""
    directory = root / HISTORY
    if not directory.is_dir():
        return {}
    return {folder.name: journal.read(folder)
            for folder in sorted(directory.iterdir()) if folder.is_dir()}


def _receipt(records):
    for record in reversed(records):
        if record['kind'] == 'receipt':
            return record
    return None


def normalise(path):
    """One spelling of a repository-relative path, or nothing for one that is not.

    Both sides of the comparison come through here, because a finding and a
    triage's `would_exclude` are written by different hands. The `./` prefix is
    removed as a prefix and not as a set of characters: `str.lstrip('./')`
    strips every leading `.` and `/`, which turned `.claude/agents/x.md` into
    `claude/agents/x.md` and made a finding in any dot directory match nothing
    while looking like a path that had been read. F1 of this ticket's first
    review, on a list where four of the thirteen excluded files were dot
    directories.

    An absolute path returns nothing. It cannot be compared with anything a
    triage records, so it is placed nowhere rather than silently placed outside.
    """
    if not path:
        return None
    path = str(path).strip()
    while path.startswith('./'):
        path = path[2:]
    if not path or path.startswith('/'):
        return None
    return path.rstrip('/') or None


def path_of(reference):
    """The file a finding names, which seen-reviewer writes as `path:line`.

    The line is dropped, because the triage excludes files and not lines. A
    reference with no line is a path already, and one whose tail is not a number
    is left alone: `harness/a.py:nope` is a path this cannot read rather than a
    path called `harness/a.py`.
    """
    if not reference:
        return None
    head, separator, tail = str(reference).rpartition(':')
    if separator and tail.isdigit():
        reference = head
    return normalise(reference)


def _preceding_triage(records, sequence):
    """The triage that chose what the reviewer read before this record was written.

    Per record rather than per ticket: a ticket reviewed twice was triaged
    twice, and a file excluded in the first round and read in the second was
    read. Pairing every finding with the last triage of the ticket would charge
    the second round's findings to the first round's exclusions.
    """
    found = None
    for record in records:
        if record['sequence'] >= sequence:
            break
        if record['kind'] == 'triage':
            found = record
    return found


def escapes(records):
    """The escapes in one ticket's journal, and what nothing could place.

    Two kinds, as the ticket defines them: a finding at high or blocking
    severity in a file the triage would have excluded, and a criterion the
    triage answered evidenced that the review found unmet.

    The remainder is reported rather than resolved in either direction. A high
    finding naming no file might have landed anywhere, and counting it as no
    escape would be a silent pass in favour of the narrowing being measured.
    """
    found, unplaced = [], []
    for record in records:
        data = record['data']
        if record['kind'] == 'advance' and data.get('from_stage') == 'review':
            triaged = _preceding_triage(records, record['sequence'])
            excluded = {normalise(path)
                        for path in (triaged or {}).get('data', {}).get('would_exclude') or []}
            excluded.discard(None)
            for finding in data.get('evidence', {}).get('findings') or []:
                if finding.get('severity') not in ESCAPING_SEVERITIES:
                    continue
                path = path_of(finding.get('file'))
                if path is None:
                    unplaced.append(dict(kind='finding', ticket=record['ticket'],
                                         id=finding.get('id'), severity=finding['severity'],
                                         reason='The finding names no file, so nothing can say '
                                                'whether the triage would have excluded it'))
                elif path in excluded:
                    found.append(dict(kind='finding_in_excluded_file', ticket=record['ticket'],
                                      id=finding.get('id'), severity=finding['severity'],
                                      file=path, claim=finding.get('claim'),
                                      triage=(triaged or {}).get('sequence'),
                                      record=record['sequence']))
        if record['kind'] == 'return' and data.get('from_stage') == 'review':
            triaged = _preceding_triage(records, record['sequence'])
            answers = {answer.get('key'): answer
                       for answer in (triaged or {}).get('data', {}).get('criteria_answers') or []}
            named = data.get('unmet_criteria')
            if not named:
                # F4 of this ticket's first review. Nothing requires the flag,
                # so a review that returned a ticket for an unmet criterion and
                # did not name it would read exactly like one that returned it
                # for a finding. Placed nowhere rather than counted clean, which
                # is the rule this whole module is written to.
                unplaced.append(dict(kind='return', ticket=record['ticket'],
                                     record=record['sequence'],
                                     reason='This return from review names no criterion, so '
                                            'nothing can say whether a criterion the triage '
                                            'called evidenced was found unmet. Name it with '
                                            'harness return --unmet <n>'))
            for position in named or []:
                answer = answers.get(f'criterion_evidenced#{position}')
                if answer is None or answer.get('passed') is None:
                    unplaced.append(dict(kind='criterion', ticket=record['ticket'],
                                         position=position,
                                         reason='The triage recorded no answer about this '
                                                'criterion, so nothing can say it was missed'))
                elif answer['passed']:
                    found.append(dict(kind='unmet_criterion', ticket=record['ticket'],
                                      position=position, criterion=answer.get('criterion'),
                                      triage=(triaged or {}).get('sequence'),
                                      record=record['sequence']))
                # passed is False: the triage said so itself and returned the
                # ticket before a reviewer read anything. It missed nothing.
    return dict(escapes=found, unattributable=unplaced)


def latest_triage(records):
    for record in reversed(records):
        if record['kind'] == 'triage':
            return record
    return None


def latest_route(records):
    """The route that routed the plan the work was done against.

    The same rule kpi applies, kept here rather than imported because this reads
    the route entries' `files`, which the KPI drops: a finding is charged to a
    slice by the files that slice planned to change.
    """
    accepted = None
    for record in reversed(records):
        if (accepted is None and record['kind'] == 'advance'
                and record['data'].get('from_stage') == 'solution'):
            accepted = record['sequence']
    if accepted is None:
        return None
    for record in reversed(records):
        if record['kind'] == 'route':
            return record if record['data'].get('solution') == accepted else None
    return None


def latest_findings(records):
    """Every review finding, deduplicated by id, most recent record winning.

    The rule kpi.findings already applies to the counts, applied here to the
    findings themselves: a ticket reviewed twice lists the same finding twice
    and it is one finding.
    """
    latest = {}
    for record in records:
        if record['kind'] != 'advance' or record['data'].get('from_stage') != 'review':
            continue
        for position, finding in enumerate(record['data'].get('evidence', {}).get('findings') or []):
            latest[finding.get('id') or f'{record["sequence"]}-{position}'] = finding
    return list(latest.values())


def _covers(path, files):
    """Whether a slice's planned files contain this path, directories included."""
    if path is None:
        return False
    for named in files:
        named = str(named).strip().lstrip('./').rstrip('/')
        if path == named or path.startswith(named + '/'):
            return True
    return False


def slice_rows(ticket, records, escaped, rules):
    """Each routed slice, its group, and the rework charged to it.

    The charges are coarser than they read, and the rule in thresholds.toml says
    so: a return sends the whole ticket back and no record says which slice
    caused it, so every slice of the plan carries it, and an escaped defect is
    charged the same way. Findings are the one per-slice measure, attributed by
    the files the slice planned to change.
    """
    routed = latest_route(records)
    if routed is None:
        return []
    strongest = rules['routing']['tiers'][-1]
    returns = sum(1 for record in records if record['kind'] in ('return', 'reopen'))
    findings = [finding for finding in latest_findings(records)
                if finding.get('severity') in ESCAPING_SEVERITIES]
    rows = []
    for entry in routed['data']['execution']:
        charged = sum(1 for finding in findings
                      if _covers(path_of(finding.get('file')), entry.get('files') or []))
        # A rule gives the strongest tier, so a rule-routed slice is evidence
        # about the strongest model and belongs in that group. Only a slice Jev
        # sent below it is the thing under calibration.
        downgraded = entry['source'] == 'jev' and entry['model'] != strongest
        rows.append(dict(ticket=ticket, position=entry['position'], name=entry.get('name'),
                         points=entry.get('points') or 0,
                         model=entry['model'], effort=entry.get('effort'),
                         source=entry['source'], rule=entry.get('rule'),
                         group='downgraded' if downgraded else 'strongest',
                         returns=returns, findings=charged, escaped_defects=len(escaped),
                         rework=returns + charged + len(escaped)))
    return rows


def _excluded_reason(ticket, records, settings):
    """Why this ticket is not in the window, or nothing when it is."""
    if ticket in (settings['excluded'] or []):
        return settings['excluded_reason']
    if not records:
        return 'The journal is empty'
    if _receipt(records) is None:
        return 'Not delivered: a ticket still being worked has no window to be in'
    started = records[0]['timestamp']
    if started < settings['counted_from']:
        return (f'Started {started}, before the calibration rule existed at '
                f'{settings["counted_from"]}')
    return None


def fixes_index(root):
    """Every ticket that names an earlier one as the ticket it fixes, by that ticket.

    Built once rather than per ticket: report.escaped_defects reads every ticket
    file to answer for one, and this is asked for every ticket in the window,
    inside a triage that a session is waiting on.
    """
    found = {}
    for path in sorted((root / TICKETS).glob('*.md')):
        header = report.frontmatter(path)
        fixes = report._field(header, 'fixes')
        identifier = report._field(header, 'id')
        if not fixes or not identifier:
            continue
        for fixed in re.split(r'[\s,\[\]]+', fixes):
            if fixed:
                found.setdefault(fixed, []).append(identifier)
    return found


def ticket_evidence(root, ticket, records, rules, escaped=None):
    """One counted ticket's row: what the triage would have dropped, and what got through."""
    triaged = latest_triage(records)
    routed = latest_route(records)
    escaped = report.escaped_defects(root, ticket) if escaped is None else escaped
    placed = escapes(records)
    by_severity = {}
    for finding in latest_findings(records):
        severity = finding.get('severity', 'unknown')
        by_severity[severity] = by_severity.get(severity, 0) + 1
    return dict(ticket=ticket,
                delivered_at=(_receipt(records) or {}).get('timestamp'),
                findings_by_severity=by_severity,
                triage=None if triaged is None else dict(
                    record=triaged['sequence'],
                    depth=triaged['data'].get('review_depth'),
                    model_depth=triaged['data'].get('model_depth'),
                    shadow=triaged['data'].get('shadow'),
                    would_exclude=list(triaged['data'].get('would_exclude') or []),
                    excluded_share=triaged['data'].get('excluded_share')),
                route=None if routed is None else routed['sequence'],
                escaped_defects=escaped,
                escapes=placed['escapes'],
                unattributable=placed['unattributable'],
                slices=slice_rows(ticket, records, escaped, rules))


def verdict_triage(rows, rules):
    """Go-live or stay-shadow for the triage, by the rule and by nothing else.

    The window is the most recent ten counted tickets rather than a counter
    somebody keeps, which is what makes the return to shadow need no state: an
    escape holds the verdict at stay-shadow until ten further tickets have
    pushed it out of the window, which is the ticket's another ten.
    """
    settings = rules['calibration']
    size = settings['window']
    rule = settings['triage_rule']
    if len(rows) < size:
        return dict(state='stay_shadow', rule=rule, window=[row['ticket'] for row in rows],
                    escapes=[escape for row in rows for escape in row['escapes']],
                    reason=f'{len(rows)} of {size} counted tickets carry a triage, so the '
                           'evidence is reported and nothing is concluded from it')
    window = rows[-size:]
    found = [escape for row in window for escape in row['escapes']]
    names = [row['ticket'] for row in window]
    if found:
        # Named from the rows rather than from the escapes, because the row is
        # what the window is made of and an escape is only evidence inside one.
        named = ', '.join(row['ticket'] for row in window if row['escapes'])
        return dict(state='stay_shadow', rule=rule, window=names, escapes=found,
                    reason=f'{len(found)} escape(s) in the last {size} counted tickets, in '
                           f'{named}. The triage stays in shadow until ten tickets carry none')
    return dict(state='go_live', rule=rule, window=names, escapes=[],
                reason=f'No escape in the last {size} counted tickets ({", ".join(names)}). '
                       'Spot depth can go live: set [review] triage_shadow to false, which is '
                       "the founder's decision and belongs in the journal of the ticket that "
                       'makes it')


def verdict_routes(rows, tickets, rules):
    """Go-live or stay-shadow for the routes: the downgraded slices against the rest."""
    settings = rules['calibration']
    size = settings['window']
    rule = settings['route_rule']
    empty = dict(slices=0, points=0, rework=0, rate=None)
    if len(tickets) < size:
        return dict(state='stay_shadow', rule=rule, window=list(tickets),
                    downgraded=empty, strongest=empty,
                    reason=f'{len(tickets)} of {size} counted tickets carry a route, so the '
                           'evidence is reported and nothing is concluded from it')

    def group(name):
        found = [row for row in rows if row['group'] == name]
        points = sum(row['points'] for row in found)
        rework = sum(row['rework'] for row in found)
        return dict(slices=len(found), points=points, rework=rework,
                    rate=round(rework / points, 4) if points else None)

    downgraded, strongest = group('downgraded'), group('strongest')
    if downgraded['rate'] is None:
        return dict(state='stay_shadow', rule=rule, window=list(tickets),
                    downgraded=downgraded, strongest=strongest,
                    reason=f'In the last {size} counted tickets no slice was routed below the '
                           'strongest tier, so there is nothing to compare and a rate of zero '
                           'against zero would read as a pass')
    if strongest['rate'] is None:
        return dict(state='stay_shadow', rule=rule, window=list(tickets),
                    downgraded=downgraded, strongest=strongest,
                    reason=f'In the last {size} counted tickets every slice was routed below the '
                           'strongest tier, so there is nothing to compare it with')
    if downgraded['rate'] <= strongest['rate']:
        return dict(state='go_live', rule=rule, window=list(tickets),
                    downgraded=downgraded, strongest=strongest,
                    reason=f'The downgraded slices rework at {downgraded["rate"]} per point '
                           f'against {strongest["rate"]} on the strongest model, so the routes '
                           'can go live: set [routing] shadow to false, which is the founder\'s '
                           'decision and belongs in the journal of the ticket that makes it')
    return dict(state='stay_shadow', rule=rule, window=list(tickets),
                downgraded=downgraded, strongest=strongest,
                reason=f'The downgraded slices rework at {downgraded["rate"]} per point against '
                       f'{strongest["rate"]} on the strongest model, so a cheaper model is '
                       'costing more than it saves')


def evidence(root, rules):
    """Every counted ticket's row, every routed slice, and the two verdicts."""
    settings = rules['calibration']
    counted, excluded = [], []
    for ticket, records in sorted(journals(root).items()):
        reason = _excluded_reason(ticket, records, settings)
        if reason:
            excluded.append(dict(ticket=ticket, reason=reason))
            continue
        counted.append((ticket, records))
    counted.sort(key=lambda pair: (_receipt(pair[1]) or {}).get('timestamp') or '')
    fixes = fixes_index(root)
    tickets = [ticket_evidence(root, ticket, records, rules, fixes.get(ticket, []))
               for ticket, records in counted]
    with_triage = [entry for entry in tickets if entry['triage'] is not None]
    with_route = [entry for entry in tickets if entry['route'] is not None]
    size = settings['window']
    in_window = with_route[-size:] if len(with_route) >= size else with_route
    return dict(window=size,
                counted_from=settings['counted_from'],
                escape=settings['escape'],
                tickets=tickets,
                excluded=excluded,
                slices=[row for entry in tickets for row in entry['slices']],
                triage=verdict_triage(with_triage, rules),
                routes=verdict_routes([row for entry in in_window for row in entry['slices']],
                                      [entry['ticket'] for entry in with_route], rules))


def effective_shadow(root, rules):
    """Which shadow the triage is in, and what put it there.

    The threshold is the only way to go live and the rule is the only way back.
    Nothing here writes to thresholds.toml: a harness that rewrites its own
    rules is a harness whose rules nobody can read from a diff.
    """
    if rules['review']['triage_shadow']:
        return dict(shadow=True, source='threshold',
                    reason='[review] triage_shadow is true in harness/thresholds.toml')
    verdict = evidence(root, rules)['triage']
    # An escape, and nothing else. A window that is not full yet is a reason for
    # the report to conclude nothing, never a reason to override the line the
    # founder changed: that would make going live impossible rather than early.
    if not verdict['escapes']:
        return dict(shadow=False, source='calibration',
                    reason='[review] triage_shadow is false and no escape sits in the window of '
                           f'{len(verdict["window"])} counted ticket(s)')
    named = ', '.join(sorted({escape['ticket'] for escape in verdict['escapes']}))
    return dict(shadow=True, source='calibration',
                reason=f'Returned to shadow by the calibration rule: {len(verdict["escapes"])} '
                       f'escape(s) in the window, in {named}. The triage stays in shadow until '
                       'ten counted tickets carry none')
