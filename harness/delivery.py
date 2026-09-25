"""Delivery: the deliver stage's own gate, and the receipt it writes.

There is no advance out of deliver. This command checks what can be checked
without trusting the session that asks, appends the receipt and moves the ticket
to delivered. In SEEN-086 it is offline apart from git ls-remote and never needs
gh; SEEN-089 adds the CI check and SEEN-091 the KPI check, and each refuses
rather than passes when it cannot be run.
"""

import json
import re
import subprocess

from . import coverage, gates, github, journal, kpi
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
    marked = False
    if reviewed['tree'] != tree:
        # The one change the procedure itself makes after a review: the ticket's
        # status, its status row and its criteria boxes. A session cannot know
        # the review passed until it has passed, and doctor requires the ticket
        # to say review by the time the journal is at deliver, so every ticket
        # either writes those three things after the advance or writes them
        # before it on the assumption the review will pass. This accepts the
        # first, against the ticket as the reviewed commit had it, and records
        # that it did. Everything else in the ticket, the Outcome above all,
        # stays inside the fingerprint, which is what the skill requires.
        marked = _ticket_marked_after_review(repository, records, reviewed)
        require(marked,
                'The project changed after review; return the ticket to the stage that owns it')
    data['ticket_marked_after_review'] = marked
    _require_committed(repository, folder)
    branch, commit = repository.branch(), repository.head()
    require(repository.tip_is_on_remote(data['remote'], branch, commit),
            f'{commit[:8]} is not the tip of {branch} on the {data["remote"]} remote; '
            'push the branch before verifying delivery')
    # CI is the definition of done, and this is where the harness stops asserting
    # it and starts verifying it. SEEN-087 and SEEN-088 both wrote receipts over
    # red checks for want of these four lines.
    verified = github.require_green(repository, commit, 'delivery')
    runs = {}
    for run in verified:
        runs[run['name']] = runs.get(run['name'], 0) + 1
    checks = [dict(name=run['name'], conclusion=run['conclusion'], runs=runs[run['name']])
              for run in verified]

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
                                      limits=data['limits'], evidence=data, checks=checks,
                                      coverage=measurement and dict(
                                          package=measurement['package'],
                                          lines=measurement['lines'],
                                          delta=measurement['delta'])))
    # What this journal alone can say, cached beside the receipt so a reader
    # need not recompute it. Points and the ticket's own tokens stay null here on
    # purpose: points live in the ticket frontmatter and tokens in the session
    # logs, and harness report fills both. The report is the authority.
    written = journal.read(folder)
    # The one figure read from a machine here, because criterion 5 of SEEN-107
    # names kpi.json and this is its only writer. Null where there are no logs,
    # so the file still reads the same everywhere; it simply carries more where
    # it can. F3 of that ticket's review.
    from . import thresholds
    figures = kpi.measure(written, record['ticket'],
                          reviewer_tokens=kpi.reviewer_tokens(repository.root, written),
                          # The price table, so the delivered file carries what
                          # each slice cost on the model it was routed to.
                          rules=thresholds.load(repository.root))
    (folder / 'kpi.json').write_text(json.dumps(figures, indent=2, ensure_ascii=False) + '\n')

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


STATUS_LINE = re.compile(r'^status:.*$', re.MULTILINE)
STATUS_ROW = re.compile(r'^\| Status \|.*$', re.MULTILINE)


def _procedural(text):
    """The ticket with the three things the procedure writes about a review removed.

    Substance only: the frontmatter status, the status row of the header table and
    whether a criterion's box is ticked. Two tickets that differ in nothing else
    are the same ticket as far as a review is concerned, because a reviewer reads
    the criteria and never the boxes: an unticked criterion the review found met
    is what the advance itself records.
    """
    text = STATUS_LINE.sub('status:', text)
    text = STATUS_ROW.sub('| Status |', text)
    # Trailing newlines go too, because one side of the comparison comes through
    # `git show`, whose output this repository's helper strips, and a file that
    # ends with a newline is not a file whose prose changed.
    return text.replace('- [x]', '- [ ]').rstrip('\n')


def _ticket_marked_after_review(repository, records, reviewed):
    """Whether the only change since the review is the ticket being marked reviewed.

    Read from the commit the review advance was written at, which is git as the
    notary the journal already treats it as, rather than from a copy of the file
    in a record. A tree that differs anywhere else, or a ticket that differs in
    any word of its prose, is not this case.
    """
    for record in reversed(records):
        if record['kind'] == 'advance' and record['data'].get('from_stage') == 'review':
            head = record.get('head')
            break
    else:
        return False
    path = _ticket_path(repository, records)
    if head is None or path is None:
        return False
    if repository.fingerprint(excluding=(str(path),)) != _reviewed_without_ticket(reviewed, path):
        return False
    was = repository.git('show', f'{head}:{path}')
    now = (repository.root / path).read_text()
    return bool(was) and _procedural(was) == _procedural(now)


def _reviewed_without_ticket(reviewed, path):
    """The reviewed tree recomputed without the ticket file.

    The review record holds one number over the whole tree, so the comparison
    that excludes the ticket has to be made against the reviewed commit rather
    than against that number. Stored by the review gate from SEEN-109 as
    `tree_without_ticket`; absent on every review written before it, and an
    absence refuses rather than passes.
    """
    return reviewed.get('tree_without_ticket')


def _ticket_path(repository, records):
    """The ticket file, as the start record named it."""
    named = records[0]['data'].get('ticket_file') if records else None
    if named and (repository.root / named).is_file():
        return named
    return None


def _require_committed(repository, folder):
    """Every record must already be in the history that was pushed.

    The receipt is the one record written afterwards, which is why it attests a
    tree that excludes the journal.
    """
    uncommitted = [path.name for path in sorted(folder.glob('[0-9]*.json'))
                   if not repository.is_tracked(path.relative_to(repository.root))]
    require(not uncommitted,
            f'Commit and push the journal before verifying delivery: {", ".join(uncommitted)}')


# What delivery itself writes after the receipt is taken, and therefore the only
# paths a commit between the receipt and the tip may touch. Reports are here
# because the week a ticket delivers in includes that ticket, so regenerating
# them at delivery is the normal thing to do rather than an unreviewed change.
DELIVERY_WRITES = ('docs/harness/history/', 'docs/harness/coverage.json',
                   'docs/harness/reports/', 'graphify-out/')


def verify_merge(repository, folder, records):
    """Whether the receipt still describes what is about to merge.

    Read-only, and it appends nothing: its own first rule is that the receipt is
    the last record, which a record of this check would break. See
    docs/adr/0002-the-receipt-attests-the-tree-minus-the-journal.md for why the
    receipt can never be the tip at delivery time.
    """
    require(records and records[-1]['kind'] == 'receipt',
            'The last record is not a receipt, so there is no delivery to merge. '
            'Run verify-delivery first, or harness reopen if the work changed')
    receipt = records[-1]
    commit = receipt['data']['commit']
    require(repository.contains_commit(commit),
            f'The receipt attests {commit[:8]}, which is not in this branch')

    changed = repository.git('diff', '--name-only', f'{commit}..HEAD').splitlines()
    unreviewed = [path for path in changed if not path.startswith(DELIVERY_WRITES)]
    require(not unreviewed,
            f'Changed after the receipt was written: {", ".join(unreviewed)}. '
            'The receipt attests a tree that is not the one merging. Run harness reopen, '
            'fix it under review, and deliver again')

    hash_of_receipt = journal.digest(folder / f'{receipt["sequence"]:04d}.json')
    request = github.pull_request(repository)
    require(hash_of_receipt in (request.get('body') or ''),
            f'The pull request body does not carry the receipt hash {hash_of_receipt[:12]}..., '
            'so nobody reading it can tell which delivery it is merging')
    github.require_green(repository, repository.head(), 'merge')
    return dict(ready=True,
                ticket=receipt['ticket'],
                receipt_sha256=hash_of_receipt,
                receipt_commit=commit,
                tip=repository.head(),
                pull_request=request.get('number'),
                journal_only_commits=len(changed))
