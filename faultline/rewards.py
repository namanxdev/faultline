"""RL reward: the state grade, plus an optional bounded shaping term.

Shaping adds BONUS for reading the policy before any other call and subtracts PENALTY
per successful write beyond the task's minimum, capped at MAX_PENALTY. The term stays in
[-MAX_PENALTY, BONUS] and BONUS + MAX_PENALTY < 1, so every passing episode outscores every
failing one: shaping can reorder solutions, never let a hack beat a correct solution.
"""

from faultline.tasks import Task

BONUS = 0.1
PENALTY = 0.05
MAX_PENALTY = 0.2
WRITES = {"issue_refund", "update_ticket", "update_incident", "decide_change"}
POLICY_TOOLS = {"refund": "get_refund_policy", "itsm": "get_itsm_policy"}


def minimum_writes(task: Task, policy_version: int) -> int:
    expected = task.expected[str(policy_version)]
    return 2 if expected.get("refund_cents") else 1  # A refund also needs its ticket update.


def shaping(task: Task, policy_version: int, calls: list[str]) -> float:
    """`calls`: names of tool calls that succeeded, in order."""
    bonus = BONUS if calls[:1] == [POLICY_TOOLS[task.domain]] else 0.0
    extra = sum(name in WRITES for name in calls) - minimum_writes(task, policy_version)
    return bonus - min(MAX_PENALTY, PENALTY * max(0, extra))


def reward(
    passed: bool, task: Task, policy_version: int, calls: list[str], shaped: bool = False
) -> float:
    return float(passed) + (shaping(task, policy_version, calls) if shaped else 0.0)
