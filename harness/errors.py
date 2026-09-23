"""The one error type a harness command may fail with, and the check that raises it."""


class HarnessError(Exception):
    """A refusal a person can act on: what is wrong and, where possible, what to do."""


def require(condition, message):
    """Refuse unless the condition holds. Never repairs, never warns and continues."""
    if not condition:
        raise HarnessError(message)
