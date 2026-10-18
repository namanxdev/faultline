"""rate_limit_429: the first call to each write is rejected with Retry-After on a simulated clock.

The clock advances only through the `wait` tool, which this drift adds. Retrying without
waiting never succeeds, and the result does not depend on model latency.
"""

from faultline.drifts.base import Drift, ToolFailure
from faultline.toolspec import Param, ToolSpec

RETRY_AFTER = 2
WAIT = ToolSpec(
    "wait",
    "Pause for the given number of seconds, for example before retrying a rate-limited call.",
    (Param("seconds", float),),
    "read",
)


class RateLimit429(Drift):
    name = "rate_limit_429"
    rationale = "Rate limits ask clients to back off; a correct agent waits as long as told."

    def specs(self, service, specs):
        return [*specs, WAIT]

    def gate(self, service, name, args):
        if service.spec(name).kind != "write":
            return
        deadline = service.deadlines.setdefault(name, service.clock + RETRY_AFTER)
        if service.clock < deadline:
            # Rejected before running: unlike a 504, nothing was written.
            raise ToolFailure(
                f"429 Too Many Requests: request not processed. Retry-After: {RETRY_AFTER}"
            )


DRIFT = RateLimit429()
