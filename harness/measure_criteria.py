"""Ask one question about real records under two sets of criteria, side by side.

Written for SEEN-100, where the belief was that `clarified` punished a record for
naming what only the work can settle. A belief is not evidence, so this asks the
model, and the table it prints is what went in the journal. Keep it: when the
model version changes, the calibration has to be redone, and the way to redo it
is to run this again.

    python3 -m harness.measure_criteria SEEN-096 SEEN-088 SEEN-091

It calls the live API, once per record per candidate, so it is a script and never
a test. Nothing in harness/tests may reach the network.
"""

import sys

from harness import cli, journal, jev, thresholds
from harness.paths import HISTORY
from harness.repository import Repository

# What SEEN-100 replaced. Kept verbatim so the comparison stays reproducible:
# running this prints the effect of the change rather than a claim about it.
PREVIOUS = {'true': 'Every open question is answered or explicitly deferred with a decision',
            'false': 'Something material is still unresolved'}

IN_FORCE = jev.QUESTIONS['clarified']['criteria']


def state_of(root, ticket):
    """Exactly what the stage gate sends: the ticket as it stands and the record.

    Built through the same function the gate uses, because a measurement of some
    other payload measures some other question. The evidence is the clarify
    record that was actually submitted, found by reading the journal forward.
    """
    records = journal.read(root / HISTORY / ticket)
    evidence = next(record['data']['evidence'] for record in records
                    if record['kind'] == 'advance' and record['stage'] == 'clarify')
    current = dict(stage='clarify', attempt=records[0]['attempt'])
    return cli.state_for(records, current, evidence=evidence, root=root)


def ask(rules, credential_value, state, criteria):
    """One question, one set of criteria, one probability back."""
    payload = dict(state=state, model=rules['jev']['model'],
                   questions={'clarified': dict(type='noul',
                                                instructions=jev.QUESTIONS['clarified']['ask'],
                                                criteria=criteria)})
    body = jev.post(rules['jev']['endpoint'], payload, credential_value,
                    rules['jev']['timeout_seconds'])
    return float(body['answers']['clarified']['noul']), body.get('model')


def main(argv):
    root = Repository('.').root
    rules = thresholds.load(root)
    credential_value = jev.credential(root)
    if not credential_value:
        print('No credential, so no measurement. This script only tells the truth online.')
        return 1

    print(f"{'ticket':<14}{'previous':>10}{'in force':>10}")
    model_used = None
    for ticket in argv:
        state = state_of(root, ticket)
        previous, model_used = ask(rules, credential_value, state, PREVIOUS)
        in_force, _ = ask(rules, credential_value, state, IN_FORCE)
        print(f'{ticket:<14}{previous:>10.2f}{in_force:>10.2f}')
    if model_used:
        print(f'\nmodel: {model_used}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
