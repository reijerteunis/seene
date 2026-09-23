"""Delivery: the deliver stage's own gate, and the receipt it writes.

There is no advance out of deliver. This command checks what can be checked
without trusting the session that asks, appends the receipt and moves the ticket
to delivered. In SEEN-086 it is offline apart from git ls-remote and never needs
gh; SEEN-089 adds the CI check and SEEN-091 the KPI check, and each refuses
rather than passes when it cannot be run.
"""

import subprocess

from . import coverage, gates, journal
from .errors import require
from .paths import HISTORY, WORKING_STAGES


def verify(repository, folder, records, args, current):
    require(current['stage'] == 'deliver',
            f'This ticket is at {current["stage"]}; reach the deliver stage first')
    data = _evidence(repository, args)
    reviewed = gates.latest_evidence(records, 'review')
    require(reviewed is not None, 'Complete the review stage before delivery')
    for stage in WORKING_STAGES[:-1]:
        require(gates.latest_evidence(records, stage) is not None,
                f'The journal has no accepted {stage} record')

    tree = repository.fingerprint()
    require(reviewed['tree'] == tree,
            'The project changed after review; return the ticket to the stage that owns it')
    _require_committed(repository, folder)
    branch, commit = repository.branch(), repository.head()
    require(repository.tip_is_on_remote(data['remote'], branch, commit),
            f'{commit[:8]} is not the tip of {branch} on the {data["remote"]} remote; '
            'push the branch before verifying delivery')

    _refresh_graph(repository)

    # The baseline moves here and nowhere else, so a delta always compares this
    # ticket's measurement with the last one that actually delivered.
    measurement = _latest_coverage(records)
    if measurement is not None:
        coverage.record_baseline(repository.root, measurement['lines'], measurement['package'])

    record = journal.append(folder, records, kind='receipt', stage='deliver',
                            attempt=current['attempt'], actor=args.actor,
                            head=commit, ticket=args.ticket,
                            data=dict(from_stage='deliver', to_stage='delivered',
                                      commit=commit, branch=branch, remote=data['remote'],
                                      tree=tree, pull_request=data['pull_request'],
                                      limits=data['limits'], evidence=data,
                                      coverage=measurement and dict(
                                          package=measurement['package'],
                                          lines=measurement['lines'],
                                          delta=measurement['delta'])))
    path = folder / f'{record["sequence"]:04d}.json'
    return dict(record=record,
                receipt_sha256=journal.digest(path),
                receipt_file=str(path.relative_to(repository.root)),
                next_step='Commit and push this record, then put the receipt hash in the '
                          'pull request body.')


def _refresh_graph(repository):
    """Bring the committed graph up to date with the code being delivered.

    graphify's own hooks did this after every commit and left the tree dirty
    behind each one, which broke four git operations in a single session. Here it
    happens once, on the same cadence as the receipt and the coverage baseline,
    and a failure is not fatal: the graph is context, not evidence.
    """
    try:
        subprocess.run(['graphify', 'update', '.'], cwd=repository.root,
                       capture_output=True, timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return


def _latest_coverage(records):
    for record in reversed(records):
        if record['kind'] == 'check' and record['data'].get('phase') == 'coverage':
            return record['data']
    return None


def _evidence(repository, args):
    from .cli import read_evidence
    data = read_evidence(repository, args.file)
    template = gates.load_template(repository.root, 'deliver')
    gates.require_template_fields(template, data)
    gates.reject_placeholders(template, data)
    return data


def _require_committed(repository, folder):
    """Every record must already be in the history that was pushed.

    The receipt is the one record written afterwards, which is why it attests a
    tree that excludes the journal.
    """
    uncommitted = [path.name for path in sorted(folder.glob('[0-9]*.json'))
                   if not repository.is_tracked(path.relative_to(repository.root))]
    require(not uncommitted,
            f'Commit and push the journal before verifying delivery: {", ".join(uncommitted)}')
