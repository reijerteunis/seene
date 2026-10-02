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
from .errors import HarnessError
from .paths import HISTORY, TICKETS, covers, normalise

# The severities a missed finding is measured at. A low or a medium finding in a
# file the reviewer did not read is the saving working as intended; the question
# the window asks is whether anything expensive got through.
ESCAPING_SEVERITIES = ('high', 'blocking')

# The tail of a finding's reference: a line, a hunk, or a line and a column.
LINE_REFERENCE = re.compile(r'\d+(-\d+)?')


def journals(root):
    """Every ticket's records, by ticket id, and what could not be read.

    A journal that refuses to be read is excluded and named rather than raised.
    This runs inside the triage of whichever ticket is in hand, and a stray file
    in one journal refusing the review stage of every other ticket would be a
    repository-wide stop for a fault nobody working here caused. `doctor` is
    where a damaged journal is reported, and it reports every one of them. F6 of
    the third review.
    """
    directory = root / HISTORY
    if not directory.is_dir():
        return {}, {}
    found, unreadable = {}, {}
    for folder in sorted(directory.iterdir()):
        if not folder.is_dir():
            continue
        try:
            found[folder.name] = journal.read(folder)
        except HarnessError as error:
            unreadable[folder.name] = str(error)
    return found, unreadable


def delivered_at(records):
    """When this ticket delivered, or nothing when it has not.

    A receipt voided by `harness reopen` is not a delivery: the ticket went back
    to being worked, and a ticket being worked has no window to be in, which is
    what the exclusion reason already said in words while the code asked only
    whether a receipt record existed. F3 of the third review.
    """
    for record in reversed(records):
        if record['kind'] == 'reopen':
            return None
        if record['kind'] == 'receipt':
            return record['timestamp']
    return None


def path_of(reference):
    """The file a finding names, which seen-reviewer writes as `path:line`.

    The line is dropped, because the triage excludes files and not lines. A
    reference with no line is a path already, and one whose tail is not a number
    is left alone: `harness/a.py:nope` is a path this cannot read rather than a
    path called `harness/a.py`.
    """
    if not reference:
        return None
    reference = str(reference)
    # A reviewer writes `path:line`, and also `path:12-20` for a hunk and
    # `path:58:5` for a column. Every such tail is stripped, because the triage
    # excludes files and not lines, and a tail this cannot read leaves the
    # reference alone: `harness/a.py:nope` is a path nothing can place rather
    # than a path called `harness/a.py`. F1 of the fourth review, which measured
    # a line range counting as clean.
    while True:
        head, separator, tail = reference.rpartition(':')
        if not separator or not LINE_REFERENCE.fullmatch(tail):
            break
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


def declared_empty(records):
    """Every review return that declared it found nothing, and who declared it.

    A claim by its author rather than an observation: the harness cannot know
    what a reviewer found, and `--no-findings` costs a word where recording the
    findings costs a file. What it can do is name every round that made the
    claim, so a reader auditing a clean window sees whose word it rests on. F3
    of the fourth review.
    """
    return [dict(ticket=record['ticket'], record=record['sequence'],
                 actor=record.get('actor'), reason=record['data'].get('reason'))
            for record in records
            if record['kind'] == 'return' and record['data'].get('from_stage') == 'review'
            and record['data'].get('no_findings')]


def escapes(records):
    """The escapes in one ticket's journal, and what nothing could place.

    Two kinds, as the ticket defines them: a finding at high or blocking
    severity in a file the triage would have excluded, and a criterion the
    triage answered evidenced that the review found unmet.

    The remainder is reported rather than resolved in either direction. A high
    finding naming no file might have landed anywhere, and counting it as no
    escape would be a silent pass in favour of the narrowing being measured.
    """
    found, unplaced, seen = [], [], set()
    identities = finding_identities(records)
    for record in records:
        data = record['data']
        if data.get('from_stage') == 'review' and _review_findings(record):
            triaged = _preceding_triage(records, record['sequence'])
            excluded = {normalise(path)
                        for path in (triaged or {}).get('data', {}).get('would_exclude') or []}
            excluded.discard(None)
            # What that triage saw at all. A reference in neither list names a
            # file the triage never read, so nothing can say whether the
            # narrowing would have dropped it: the two answers `not excluded`
            # used to give the same reply to. F1 of the fourth review.
            seen_by_triage = {normalise(entry.get('path'))
                              for entry in (triaged or {}).get('data', {}).get('files') or []}
            seen_by_triage.discard(None)
            for position, finding in enumerate(_review_findings(record)):
                if finding.get('severity') not in ESCAPING_SEVERITIES:
                    continue
                # The earliest round that carried it, not the latest: a finding
                # repeated in the record that finally passes was found when it
                # was first written down, and it is that round's triage that
                # would or would not have dropped the file it is in. Which
                # findings are one is `finding_identities`' answer, so by what
                # a finding says and never by what a round called it.
                key = identities[(record['sequence'], position)]
                if key in seen:
                    continue
                seen.add(key)
                path = path_of(finding.get('file'))
                if path is None:
                    unplaced.append(dict(kind='finding', ticket=record['ticket'],
                                         id=finding.get('id'), severity=finding['severity'],
                                         reason='The finding names no file, so nothing can say '
                                                'whether the triage would have excluded it'))
                elif path not in excluded and path not in seen_by_triage:
                    unplaced.append(dict(kind='finding', ticket=record['ticket'],
                                         id=finding.get('id'), severity=finding['severity'],
                                         file=path,
                                         reason=f'The finding names {path}, which triage record '
                                                f'{(triaged or {}).get("sequence")} did not see '
                                                'in the diff at all, so nothing can say whether '
                                                'the narrowing would have dropped it'))
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
            if not named and not data.get('no_findings') and not data.get('findings'):
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


def _review_findings(record):
    """The findings one record carries, whether it passed the ticket or returned it.

    Both, because a review that returned a ticket is a review: its findings were
    read from the diff exactly as the passing round's were. Reading only the
    advance made a blocking finding that sent a ticket back count only if the
    session repeated it in the record that finally passed, which no gate
    requires and which three tickets happened to do by convention. F2 of the
    second review.
    """
    data = record['data']
    if data.get('from_stage') != 'review':
        return []
    if record['kind'] == 'advance':
        return data.get('evidence', {}).get('findings') or []
    if record['kind'] == 'return':
        return data.get('findings') or []
    return []


def finding_identities(records):
    """Which review findings are the same finding, by what they say and where.

    A map from (record sequence, position) to an identity, for every finding
    `_review_findings` reads, in journal order. Two findings are one when they
    name the same file and carry the same claim or the same failure scenario,
    and the join is transitive: a finding whose claim was reworded in one round
    and whose scenario was reworded in the next is still one finding. Two
    findings in the same record are never joined, directly or through a third:
    a reviewer listing two findings in one record has declared them two, however
    alike a stand-in's wording makes them.

    The id is not read for any finding the review gate accepted. Nothing asks a
    session to type the same identifier in every review record, and two did
    not: SEEN-107's second review advance renamed F1, G1 and the rest to R1-1,
    R2-1 and so on, rewording G1's claim as R2-1 while carrying its failure
    scenario byte for byte, and counted 45 findings against a real 26; SEEN-102's
    second review renumbered F1 to F3 as F2 to F4 and counted 7 against a real
    4. Neither text alone would do either: a key on the claim leaves G1 and R2-1
    as two. SEEN-145.

    A finding with neither a claim nor a failure scenario falls back to its id
    and its file, and only then. The review gate refuses such a finding
    (gates.check_findings, FINDING_KEYS) and no committed journal holds one, so
    the fallback reaches only records the gate never accepted, such as a test
    fixture that names its findings and says nothing else about them.
    """
    parent, saying, sequences = {}, {}, {}

    def root(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def join(one, other):
        one, other = root(one), root(other)
        # Refused when the two sides already share a record, which is what
        # keeps two findings of one record apart through any chain of rounds.
        if one == other or sequences[one] & sequences[other]:
            return
        # The earliest finding stands for the whole identity, so the identity
        # is the same whichever order its members are joined in.
        low, high = sorted((one, other))
        parent[high] = low
        sequences[low] |= sequences.pop(high)

    for record in records:
        for position, finding in enumerate(_review_findings(record)):
            node = (record['sequence'], position)
            parent[node], sequences[node] = node, {record['sequence']}
            path = path_of(finding.get('file'))
            said = [(field, finding.get(field)) for field in ('claim', 'failure_scenario')
                    if finding.get(field)]
            if not said and finding.get('id'):
                said = [('id', finding['id'])]
            # Every finding that said a text stays an anchor for it. A later one
            # is offered to every anchor it shares a text with, the ones sharing
            # more texts first and the earlier first among equals, and joins each
            # that is not refused, which keeps the join transitive. Keeping only
            # the first anchor per text left the second of two alike findings in
            # one record unreachable (F1 of SEEN-145's first review, 3 counted
            # where there were 2); offering anchors in journal order let a
            # claim-only match take a finding before the one that matched it on
            # both texts (F1 of the second, a high finding counted as low).
            shared = {}
            for field, text in said:
                for anchor in saying.setdefault((path, field, text), []):
                    shared[anchor] = shared.get(anchor, 0) + 1
            for anchor in sorted(shared, key=lambda anchor: (-shared[anchor], anchor)):
                join(anchor, node)
            for field, text in said:
                saying[(path, field, text)].append(node)
    return {node: root(node) for node in parent}


def latest_finding_records(records):
    """Every deduplicated finding, with the record that last carried it.

    Deduplicated by `finding_identities`, so by content and never by id. The
    record matters because a finding on a return is open by definition and
    one on an advance is resolved by the gate's own rule, so where it was
    written is what says whether it was ever fixed. F1 of the sixth review.
    """
    identities = finding_identities(records)
    latest = {}
    for record in records:
        for position, finding in enumerate(_review_findings(record)):
            latest[identities[(record['sequence'], position)]] = (record, finding)
    return list(latest.values())


def latest_findings(records):
    """Every review finding, deduplicated, most recent record winning.

    Most recent, because a finding whose severity was revised between rounds is
    one finding at the severity it ended at. `escapes` takes the earliest
    instead, for the reason written there.
    """
    return [finding for _, finding in latest_finding_records(records)]


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
    planned = [normalise(path) for entry in routed['data']['execution']
               for path in entry.get('files') or []]
    # A finding in a file no slice named. Nothing says which slice caused it, so
    # every slice carries it, exactly as route_rule already says of a return and
    # of an escaped defect; and it is counted separately, because a comparison
    # that could place none of the findings must not read as a comparison that
    # found none. F1 of the fifth review, where ten blocking findings produced a
    # rate of zero against a rate of zero and a printed go-live.
    unchargeable = [finding for finding in findings
                    if not covers(path_of(finding.get('file')), planned)]
    rows = []
    for entry in routed['data']['execution']:
        charged = sum(1 for finding in findings
                      if covers(path_of(finding.get('file')), entry.get('files') or []))
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
                         unchargeable=len(unchargeable),
                         unchargeable_files=sorted({path_of(finding.get('file')) or 'unnamed'
                                                    for finding in unchargeable}),
                         rework=returns + charged + len(escaped) + len(unchargeable)))
    return rows


def _excluded_reason(ticket, records, settings):
    """Why this ticket is not in the window, or nothing when it is."""
    if ticket in (settings['excluded'] or []):
        return settings['excluded_reason']
    if not records:
        return 'The journal is empty'
    if delivered_at(records) is None:
        return ('Not delivered, or delivered and reopened: a ticket still being worked has no '
                'window to be in')
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
                delivered_at=delivered_at(records),
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
                declared_empty=declared_empty(records),
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
                    unplaceable=[row['ticket'] for row in rows if row['unattributable']],
                    reason=f'{len(rows)} of {size} counted tickets carry a triage, so the '
                           'evidence is reported and nothing is concluded from it')
    window = rows[-size:]
    found = [escape for row in window for escape in row['escapes']]
    names = [row['ticket'] for row in window]
    unplaced = [row['ticket'] for row in window if row['unattributable']]
    if not found and unplaced:
        # Counted neither way has to mean the verdict waits. Counting it as no
        # escape is the silent pass the escape definition was written against,
        # and it is what let an optional flag decide a go-live. F1 of the third
        # review.
        return dict(state='stay_shadow', rule=rule, window=names, escapes=[],
                    unplaceable=unplaced,
                    reason=f'No escape in the last {size} counted tickets, but evidence in '
                           f'{", ".join(unplaced)} could not be placed, and evidence nobody can '
                           'place is not evidence of no escape. The window states go-live only '
                           'when every ticket in it can be read')
    if found:
        # Named from the rows rather than from the escapes, because the row is
        # what the window is made of and an escape is only evidence inside one.
        named = ', '.join(row['ticket'] for row in window if row['escapes'])
        return dict(state='stay_shadow', rule=rule, window=names, escapes=found,
                    unplaceable=unplaced,
                    reason=f'{len(found)} escape(s) in the last {size} counted tickets, in '
                           f'{named}. The triage stays in shadow until ten tickets carry none')
    return dict(state='go_live', rule=rule, window=names, escapes=[], unplaceable=[],
                reason=f'No escape in the last {size} counted tickets ({", ".join(names)}), '
                       'and every ticket in them could be read. Spot depth can go live, in two '
                       'lines: set [review] triage_shadow to false and fill [calibration] '
                       'went_live with the ticket and the record number of the decision. Both '
                       "are the founder's, and doctor refuses the first without the second")


def verdict_routes(rows, tickets, rules):
    """Go-live or stay-shadow for the routes: the downgraded slices against the rest.

    The window reported is the window the rates came from, which is the most
    recent ten and not every route-carrying ticket: a founder auditing the
    decision recomputes over the list the record names, and it has to be the
    list the verdict was taken on. F4 of the third review.
    """
    settings = rules['calibration']
    size = settings['window']
    rule = settings['route_rule']
    empty = dict(slices=0, points=0, rework=0, rate=None)
    tickets = list(tickets)[-size:] if len(tickets) >= size else list(tickets)
    if len(tickets) < size:
        return dict(state='stay_shadow', rule=rule, window=tickets,
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

    def missing(name, found, empty):
        """Why a group cannot be compared: no slices at all, or no points.

        Two answers rather than one, because a rate of None was printing that
        nobody was routed below the strongest tier while the table above showed
        the slices. Both verdicts are stay-shadow, so this is the one merged
        comparison that landed safely, and it is still two answers. F2 of the
        sixth review.
        """
        if found['slices'] == 0:
            return f'In the last {size} counted tickets {empty}'
        if found['rate'] is None:
            return (f'In the last {size} counted tickets the {name} group holds '
                    f'{found["slices"]} slice(s) carrying no points, so a rate per point cannot '
                    'be taken over it')
        return None

    unplaced = sorted({row['ticket'] for row in rows if row.get('unchargeable')})
    if unplaced:
        # The same answer the triage verdict gives evidence nobody can place: a
        # rate taken over findings it could not see is not evidence that there
        # were none. F1 of the fifth review.
        return dict(state='stay_shadow', rule=rule, window=tickets,
                    downgraded=downgraded, strongest=strongest,
                    reason=f'In {", ".join(unplaced)} a finding could not be charged to any '
                           'slice, because no slice named the file it is in, so the comparison '
                           'saw less than the window contains and a rate taken over it is not '
                           'evidence')
    groups = (('downgraded', downgraded,
               'no slice was routed below the strongest tier, so there is nothing to compare '
               'and a rate of zero against zero would read as a pass'),
              ('strongest', strongest,
               'every slice was routed below the strongest tier, so there is nothing to '
               'compare it with'))
    for name, found, empty in groups:
        reason = missing(name, found, empty)
        if reason:
            return dict(state='stay_shadow', rule=rule, window=tickets,
                        downgraded=downgraded, strongest=strongest, reason=reason)
    if downgraded['rate'] <= strongest['rate']:
        return dict(state='go_live', rule=rule, window=tickets,
                    downgraded=downgraded, strongest=strongest,
                    reason=f'The downgraded slices rework at {downgraded["rate"]} per point '
                           f'against {strongest["rate"]} on the strongest model, so the routes '
                           "can go live: set [routing] shadow to false. It is the founder's "
                           'decision and belongs in the journal of the ticket that makes it')
    return dict(state='stay_shadow', rule=rule, window=tickets,
                downgraded=downgraded, strongest=strongest,
                reason=f'The downgraded slices rework at {downgraded["rate"]} per point against '
                       f'{strongest["rate"]} on the strongest model, so a cheaper model is '
                       'costing more than it saves')


def evidence(root, rules):
    """Every counted ticket's row, every routed slice, and the two verdicts."""
    settings = rules['calibration']
    counted, excluded = [], []
    readable, unreadable = journals(root)
    for ticket, reason in sorted(unreadable.items()):
        excluded.append(dict(ticket=ticket, reason=f'The journal could not be read: {reason}'))
    for ticket, records in sorted(readable.items()):
        reason = _excluded_reason(ticket, records, settings)
        if reason:
            excluded.append(dict(ticket=ticket, reason=reason))
            continue
        counted.append((ticket, records))
    counted.sort(key=lambda pair: delivered_at(pair[1]) or '')
    fixes = fixes_index(root)
    tickets = [ticket_evidence(root, ticket, records, rules, fixes.get(ticket, []))
               for ticket, records in counted]
    with_triage = [entry for entry in tickets if entry['triage'] is not None]
    with_route = [entry for entry in tickets if entry['route'] is not None]
    size = settings['window']
    in_window = with_route[-size:] if len(with_route) >= size else with_route
    return dict(window=size,
                counted_from=settings['counted_from'],
                went_live=went_live_line(root, rules),
                escape=settings['escape'],
                tickets=tickets,
                excluded=excluded,
                slices=[row for entry in tickets for row in entry['slices']],
                triage=verdict_triage(with_triage, rules),
                routes=verdict_routes([row for entry in in_window for row in entry['slices']],
                                      [entry['ticket'] for entry in with_route], rules))


def went_live_problem(root, rules):
    """Why the go-live on record is not one, or nothing when it is.

    The criterion asks for the founder's decision to be in the journal of the
    ticket that flips the switch, and a threshold read on its own cannot tell a
    decision from an edit: anyone could set `triage_shadow = false` and the next
    triage would narrow with nothing anywhere saying who decided or on what.
    `[calibration] went_live` names the ticket and the record, and this checks
    that the record exists. It does not read what the record says, which is a
    person's job; what it refuses is a switch flipped with nothing named at all.
    F3 of the second review.
    """
    named = rules['calibration'].get('went_live') or {}
    ticket, sequence = named.get('ticket'), named.get('record')
    if not ticket or not sequence:
        return ('[review] triage_shadow is false but [calibration] went_live names no decision, '
                'so nothing on the record says who took it or on what evidence. Name the ticket '
                'and the record number of the decision, or set the threshold back to true')
    folder = root / HISTORY / ticket
    try:
        records = journal.read(folder) if folder.is_dir() else []
    except HarnessError as error:
        return (f'[calibration] went_live names record {sequence} of {ticket} as the go-live '
                f'decision and that journal could not be read: {error}. The decision may be '
                'sitting there; the journal is what needs repairing')
    if not any(record['sequence'] == sequence for record in records):
        return (f'[calibration] went_live names record {sequence} of {ticket} as the go-live '
                'decision and no such record exists, so the switch is flipped on a reference to '
                'nothing')
    return None


def went_live_line(root, rules):
    """What a report says about the switch, live or not."""
    if rules['review']['triage_shadow']:
        return 'The triage is in shadow: [review] triage_shadow is true.'
    problem = went_live_problem(root, rules)
    if problem:
        return f'The switch is flipped and the decision is not on the record. {problem}'
    named = rules['calibration']['went_live']
    return (f'Spot depth went live on {named.get("on", "an unrecorded date")}, by the decision at '
            f'record {named["record"]} of {named["ticket"]}.')


def effective_shadow(root, rules):
    """Which shadow the triage is in, and what put it there.

    The threshold is the only way to go live and the rule is the only way back.
    Nothing here writes to thresholds.toml: a harness that rewrites its own
    rules is a harness whose rules nobody can read from a diff.
    """
    if rules['review']['triage_shadow']:
        return dict(shadow=True, source='threshold',
                    reason='[review] triage_shadow is true in harness/thresholds.toml')
    named = went_live_problem(root, rules)
    if named is not None:
        return dict(shadow=True, source='threshold', reason=named)
    verdict = evidence(root, rules)['triage']
    # An escape, and nothing else. A window that is not full yet is a reason for
    # the report to conclude nothing, never a reason to override the line the
    # founder changed: that would make going live impossible rather than early.
    unplaceable = [row for row in verdict.get('unplaceable') or []]
    if not verdict['escapes'] and not unplaceable:
        return dict(shadow=False, source='calibration',
                    reason=went_live_line(root, rules) + ' No escape sits in the window of '
                           f'{len(verdict["window"])} counted ticket(s), and every ticket in it '
                           'could be read.')
    if not verdict['escapes']:
        # The report said stay-shadow and the triage went on narrowing, so the
        # two reports could disagree about the same tree while four documents
        # said the triage reads the verdict. It does now. A window that is
        # simply not full yet is still not a reason to override the founder's
        # line, which is why this reads the evidence and not the state.
        return dict(shadow=True, source='calibration',
                    reason='Returned to shadow by the calibration rule: evidence in '
                           f'{", ".join(unplaceable)} could not be placed, and evidence nobody '
                           'can place is not evidence of no escape')
    named = ', '.join(sorted({escape['ticket'] for escape in verdict['escapes']}))
    return dict(shadow=True, source='calibration',
                reason=f'Returned to shadow by the calibration rule: {len(verdict["escapes"])} '
                       f'escape(s) in the window, in {named}. The triage stays in shadow until '
                       'ten counted tickets carry none')
