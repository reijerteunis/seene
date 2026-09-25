"""The route: which model and which effort implement each slice.

Every slice used to run on whatever model the session happened to be, at
whatever effort, and the session that would have benefited from a stronger model
was the one deciding. So the choice is moved to where the information already
is: after the solution record is accepted, with the slice plan, the risk answers
and the graph answers on record, and before any session opens the slice.

Rules first, and a rule is never Jev's to answer. Three of them are ticket-wide
and are the ones gates.full_depth_rules already reads for the review triage: an
agent action, billing or the policy gate, and a plan carrying a migration. The
rest are patterns over a slice's own files in thresholds.toml, because money
arithmetic, a migration and a credential are things a path can say. Anything a
rule settles goes to the strongest tier at high effort with no request made.

What no rule settles is one Jev request carrying both questions once per slice.
An answer that did not come back is recorded as an absence and routed to the
strongest tier, never to the cheapest: a judgement nobody made must not become a
downgrade nobody decided.

Nothing here changes what a slice runs on while `[routing] shadow` is true, which
is the default. SEEN-109's window is what decides whether it ever should.
"""

import fnmatch

from . import gates, jev, journal
from .errors import require

# The three that are ticket-wide, named here with what they mean for a route.
# The predicate is gates.full_depth_rules, which the review triage already reads:
# one list of rules, two readers, so a rule added there is a rule here.
TICKET_RULES = {
    'agent_action': 'This ticket changes an agent action, so every slice of it is routed by rule',
    'billing': 'This change touches billing or the policy gate, so every slice of it is routed '
               'by rule',
    'migration': 'This plan carries a migration, so every slice of it is routed by rule',
}
# What each pattern set in [routing.rules] is about. The patterns are a
# legitimate thing to tune and live in thresholds.toml; what they mean is what
# the harness is and lives here.
PATH_RULES = {
    'money': 'money arithmetic in packages/core, which the ground rules say is deterministic '
             'and tested',
    'migration': 'a migration or an RLS policy',
    'credentials': 'credentials',
}
# How much of a graph answer goes into the state. A route is decided from what
# the journal already holds, and the whole of a repowise risk answer is a table
# nobody needs to see twice.
EXCERPT_CHARACTERS = 600
MAX_GRAPH_ANSWERS = 6


def tiers(rules):
    return list(rules['routing']['tiers'])


def strongest(rules):
    """The last tier, which is what every rule and every absence routes to."""
    return tiers(rules)[-1]


def rule_effort(rules):
    return rules['routing']['rule_effort']


def shadow(rules):
    return bool(rules['routing']['shadow'])


def model_id(rules, tier):
    """The model id a session log carries for a tier, or nothing.

    Nothing rather than a guess: the tdd gate compares a recorded check against
    this, and a comparison with a tier whose id nobody wrote down would refuse a
    check for a name it invented.
    """
    return rules['routing']['models'].get(tier)


def reviewer_model(depth, rules):
    """Which model reviews, which is a rule and never Jev's to answer.

    A full review holds the whole diff, the journal and the criteria at once,
    which is the most expensive read in the procedure and the one where a missed
    defect costs most, so it gets the strongest tier. A spot review reads a
    narrowed focus set and goes one tier down. The depth it reads is the one the
    triage enforced, not the one the model would have chosen: what the reviewer
    is actually asked to read is what decides what it needs to be.
    """
    order = tiers(rules)
    return order[-1] if depth == 'full' else order[max(len(order) - 2, 0)]


def path_rule(files, patterns):
    """The first rule a slice's own files trip, and the file that tripped it."""
    for name, globs in patterns.items():
        for path in files:
            if any(fnmatch.fnmatch(path, pattern) for pattern in globs):
                return name, path
    return None, None


def rule_for(entry, ticket_rules, patterns):
    """Why this slice is not Jev's to route, or nothing.

    The ticket-wide rules come first because they are about the whole ticket: a
    ticket that changes an agent action has no slice that does not.
    """
    if ticket_rules:
        name = ticket_rules[0]
        return name, TICKET_RULES[name]
    name, path = path_rule(entry['files'], patterns)
    if name is None:
        return None, None
    return name, f'{path} is {PATH_RULES.get(name, name)}, so this slice is routed by rule'


def planned(solution):
    """The slices to route, in the order the plan put them."""
    return [dict(position=position, name=entry.get('name'), points=entry.get('points'),
                 files=list(entry.get('files') or []), red=entry.get('red'))
            for position, entry in enumerate(solution.get('slices') or [], start=1)]


def key(question, position):
    """One question about one slice. The position is what makes it answerable."""
    return f'{question}#{position}'


def subject(entry):
    """What `implementation_model#2` is a question about."""
    return ('The slice:\n'
            f'- name: {entry["name"]}\n'
            f'- points: {entry["points"]}\n'
            f'- files: {", ".join(entry["files"]) or "none named"}\n'
            f'- the RED it must demonstrate: {entry["red"]}')


def questions(unruled):
    """Both questions, once per slice no rule settled."""
    asked = []
    for entry in unruled:
        for name in ('implementation_model', 'implementation_effort'):
            asked.append((key(name, entry['position']), name, subject(entry)))
    return asked


def _excerpt(text):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= EXCERPT_CHARACTERS else text[:EXCERPT_CHARACTERS] + ' [...]'


def _decision(records, stage, question):
    """A gate decision already taken, from the advance that carried it."""
    for record in reversed(records):
        if record['kind'] != 'advance' or record['data'].get('from_stage') != stage:
            continue
        for answer in record['data'].get('decisions') or []:
            if answer['question'] == question:
                return answer
    return None


def graph_answers(records):
    """What the graphs have already said, so the route reads it rather than asking again.

    The answer itself and not a pointer to the record holding it: a model cannot
    follow a record number, and whether the pattern already exists in this
    repository is exactly what these answers settle.
    """
    found = []
    for record in records:
        data = record['data']
        if record['kind'] != 'note' or 'source' not in data:
            continue
        command = data.get('command') or []
        found.append(dict(source=data['source'], mode=data.get('mode'),
                          about=command[-1] if len(command) > 2 else None,
                          answer=_excerpt(data.get('answer'))))
    return found[-MAX_GRAPH_ANSWERS:]


def marketplaces(repository, records):
    """The marketplaces the ticket names, from its own frontmatter."""
    from .cli import _ticket_text
    from .report import _field
    first = records[0]['data']
    text, _ = _ticket_text(first, first.get('ticket_id', records[0]['ticket']), repository.root)
    named = _field(text.split('---')[1] if text.startswith('---') else '', 'marketplaces')
    return named or 'none'


def state(repository, records, current, ticket, solution, entries):
    """What the route is decided from: the plan, the risk answers and the history."""
    risk = _decision(records, 'clarify', 'risk') or {}
    change_risk = next((record for record in reversed(records)
                        if record['kind'] == 'note' and record['data'].get('source') == 'repowise'
                        and record['data'].get('mode') == 'risk'), None)
    return dict(ticket=ticket,
                stage=current['stage'],
                attempt=current['attempt'],
                slices=entries,
                solution=dict(mode=gates.mode_of(solution),
                              approach=solution.get('approach'),
                              changes=solution.get('changes') or [],
                              migrations=solution.get('migrations') or [],
                              new_dependencies=solution.get('new_dependencies') or []),
                risk=risk.get('outcome'),
                risk_probabilities=risk.get('probabilities') or {},
                change_risk=_excerpt(change_risk['data']['answer']) if change_risk else None,
                graph_answers=graph_answers(records),
                marketplaces=marketplaces(repository, records),
                # How often this ticket has already been sent back. A plan that
                # has been reworked twice is evidence about the plan, which is
                # the kind of thing the route should see.
                returns=sum(1 for record in records if record['kind'] == 'return'))


def _from_answers(entry, by_key, rules):
    """One unruled slice's route, from the two answers about it, or from neither."""
    model = by_key.get(key('implementation_model', entry['position']))
    effort = by_key.get(key('implementation_effort', entry['position']))
    missing = [name for name, answer in (('implementation_model', model),
                                         ('implementation_effort', effort))
               if answer is None or answer['outcome'] is None]
    if missing:
        reasons = sorted({answer['fallback_reason'] for answer in (model, effort)
                          if answer and answer['fallback_reason']})
        return dict(entry,
                    model=strongest(rules), effort=rule_effort(rules),
                    source='unavailable', rule=None,
                    # The slice is routed to the strongest rather than the
                    # cheapest, because a judgement nobody made must not become
                    # a downgrade nobody decided.
                    reason='Routed to the strongest model because '
                           + ', '.join(key(name, entry['position']) for name in missing)
                           + ' was not answered'
                           + (f': {"; ".join(reasons)}' if reasons else ''),
                    model_probability=None, effort_probability=None)
    return dict(entry,
                model=model['outcome'], effort=effort['outcome'],
                source='jev', rule=None,
                reason=None,
                model_probability=model['probabilities'].get(model['outcome']),
                effort_probability=effort['probabilities'].get(effort['outcome']))


def run(repository, records, current, rules, ticket):
    """The whole route, as the data a `route` record carries."""
    require(current['stage'] == 'tdd',
            f'A route is decided at the tdd stage; this ticket is at {current["stage"]}. '
            'The slice plan is what a route routes, so it comes after the solution gate and '
            'before the first slice is opened')
    solution = gates.latest_evidence(records, 'solution') or {}
    entries = planned(solution)
    require(entries,
            'This plan has no slices to route. A ticket with no behaviour to prove declares '
            'non-code mode at solution and has no slice for a model to implement')
    tripped = gates.full_depth_rules(records, repository.root, solution)
    patterns = rules['routing']['rules']

    routed, unruled = [], []
    for entry in entries:
        name, reason = rule_for(entry, tripped, patterns)
        if name is None:
            unruled.append(entry)
            routed.append(None)
            continue
        routed.append(dict(entry, model=strongest(rules), effort=rule_effort(rules),
                           source='rule', rule=name, reason=reason,
                           model_probability=None, effort_probability=None))

    answers, requested = [], dict(asked=False, model=None, answers=[],
                                  reason='Every slice was settled by rule, so no request was made')
    if unruled:
        asked = questions(unruled)
        answers = jev.ask_batch(repository.root, rules, asked,
                                state(repository, records, current, ticket, solution, entries),
                                must_answer=False)
        answered = next((answer for answer in answers if answer['source'] == 'jev'), None)
        requested = dict(asked=answered is not None,
                         model=(answered or {}).get('model'),
                         reason=jev.why_not(answered, jev.credential(repository.root), answers),
                         answers=answers)
    by_key = {answer['key']: answer for answer in answers}
    execution = [entry if entry is not None else _from_answers(unruled.pop(0), by_key, rules)
                 for entry in routed]
    return dict(solution=(solution_record(records) or {}).get('sequence'),
                # What the record was written under, so a reader never has to
                # ask whether the route took effect: in shadow it did not.
                shadow=shadow(rules),
                strongest=strongest(rules),
                tiers=tiers(rules),
                rules=[TICKET_RULES[name] for name in tripped],
                jev=requested,
                execution=execution)


def solution_record(records):
    """The accepted solution advance this route routes.

    Named rather than written into, because the journal is append-only: a route
    written into the record that planned it would be either a rewrite of
    evidence or a second record claiming to be the first.
    """
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'solution':
            return record
    return None


def for_slice(records, position):
    """The route the most recent record gives one slice, or nothing.

    The most recent, because a plan changed by a return to solution is routed
    again and the later record is the one that describes the plan in hand.
    """
    for record in reversed(records):
        if record['kind'] != 'route':
            continue
        for entry in record['data']['execution']:
            if entry['position'] == position:
                return entry
        return None
    return None


def append(repository, folder, records, current, args, rules):
    """Run the route and keep it. Nothing is refused by what it decides."""
    from . import agents
    data = run(repository, records, current, rules, args.ticket)
    record = journal.append(folder, records, kind='route', stage=current['stage'],
                            attempt=current['attempt'], actor=args.actor,
                            head=repository.head(), ticket=args.ticket, data=data)
    # The implementer's copies carry the route, so a route that changed them and
    # did not rewrite them would leave doctor reporting drift and the next
    # session spawning on the model the last slice was given.
    agents.sync(repository.root)
    return record
