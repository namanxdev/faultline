"""transient_503: the first call to each read tool fails with a retry hint."""

from faultline.drifts.base import Drift, ToolFailure


class Transient503(Drift):
    name = "transient_503"
    rationale = "Services blip; a correct agent retries reads that say they are retryable."

    def gate(self, service, name, args):
        if service.spec(name).kind == "read" and service.calls[name] == 1:
            raise ToolFailure("503 Service unavailable. Retry this read once.")


DRIFT = Transient503()
