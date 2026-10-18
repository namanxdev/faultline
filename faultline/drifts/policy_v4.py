"""policy_v4: the policy document changes; the expected outcome follows the new text."""

from faultline.drifts.base import Drift


class PolicyV4(Drift):
    name = "policy_v4"
    rationale = "Policies change; a correct agent reads the current one instead of remembering."

    def policy_version(self):
        return 4


DRIFT = PolicyV4()
