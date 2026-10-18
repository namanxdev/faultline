"""ambiguous_write: the first unsafe write commits, then reports an ambiguous timeout."""

from faultline.drifts.base import Drift, ToolFailure


class AmbiguousWrite(Drift):
    name = "ambiguous_write"
    rationale = "A timeout after a write hides whether it committed; blind retries duplicate it."

    def after(self, service, name, args, result):
        if name == service.UNSAFE_WRITE and service.calls[name] == 1:
            raise ToolFailure("504 Gateway timeout: write may or may not have completed.")
        return result


DRIFT = AmbiguousWrite()
