"""What a plan of this shape has cost, read from the delivered KPI records.

A ticket's own points say nothing about tokens: SEEN-109's own kpi.json
records a one-point slice at 121,398 output tokens and another at 42,520, both
against a 60,000 [session] output_token_budget, and SEEN-110 planned two
points and spent 140,000. The unit a session runs out of is the token, so this
reads every delivered `docs/harness/history/*/kpi.json`'s `execution` entries
and predicts a plan of this shape from their distribution rather than from
what the plan's points claim.

Nothing here refuses. `require` belongs to a gate deciding whether a ticket
may advance, and the ticket that motivated this module closes on the point
that only the person at the keyboard can end a session; a refusal mid-slice
leaves work done and unrecorded. So every path here is a report: a missing or
malformed kpi.json is skipped exactly as `cost.py` skips a malformed log line,
and a missing figure reads null rather than zero, for the reason `cost.py`
already gives for every figure it reads: zero is a claim that nothing was
spent, and null says nobody knows.

A prediction over budget is named rather than acted on for the same reason:
the session that planned SEEN-111 itself had spent 61,432 output tokens
before a line of code existed, which a per-slice split cannot rescue, and this
module does not pretend it can. It names the split; it does not promise the
split will fit.
"""

import json
import math
import statistics

from .paths import HISTORY


def _delivered_slice_figures(root):
    """Every delivered ticket's per-slice output tokens, keyed by ticket id.

    Only tickets contributing at least one priced slice are counted: a
    kpi.json with no `execution`, or one whose every entry is null, has
    nothing to predict from, and counting it as delivered would make an
    absence read as a low figure rather than as an absence, which is the one
    thing this module must not do.
    """
    directory = root / HISTORY
    if not directory.is_dir():
        return {}
    found = {}
    for folder in sorted(directory.iterdir()):
        if not folder.is_dir():
            continue
        path = folder / 'kpi.json'
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, ValueError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        execution = data.get('execution')
        if not isinstance(execution, list):
            continue
        figures = [entry.get('output_tokens') for entry in execution
                   if isinstance(entry, dict) and entry.get('output_tokens') is not None]
        if figures:
            found[folder.name] = figures
    return found


def predict(slices, root, thresholds):
    """The price of a plan shaped like `slices`, from what delivered slices cost.

    `slices` is the plan in hand, read only for how many slices it names: its
    points play no part in the figure, which is the whole reason this module
    exists rather than a division of the plan's own estimate.

    Below `[calibration] window` delivered tickets, the distribution is too
    thin to read anything from, so the answer is an absence: `available` is
    false, with the count observed and the count the window needs, and no
    figure at all. At or above it, the per-slice figure is the median of every
    delivered slice's output tokens, reported beside the highest one seen and
    the counts they came from; when it is over `[session] output_token_budget`
    the plan is told so and given the number of sessions that figure would
    take, named as a split and not as a fix.
    """
    window = thresholds['calibration']['window']
    budget = thresholds['session']['output_token_budget']
    by_ticket = _delivered_slice_figures(root)
    observed_tickets = len(by_ticket)
    if observed_tickets < window:
        return dict(available=False, observed_tickets=observed_tickets, required=window)
    figures = sorted(value for values in by_ticket.values() for value in values)
    median = round(statistics.median(figures))
    highest = figures[-1]
    exceeds = median > budget
    return dict(available=True,
                observed_tickets=observed_tickets,
                observed_slices=len(figures),
                median_output_tokens_per_slice=median,
                highest_output_tokens_per_slice=highest,
                output_tokens_per_slice=median,
                planned_slices=len(slices),
                output_token_budget=budget,
                exceeds_budget=exceeds,
                split=math.ceil(median / budget) if exceeds else None)
