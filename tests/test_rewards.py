import random

import pytest

from faultline import rewards
from faultline.drifts import DRIFTS
from faultline.runner import policy_version
from faultline.tasks import TEMPLATES, load
from faultline.validate import episode, near_misses

DEV = load("dev")
SAMPLE = [next(t for t in DEV if t.template == template) for template in TEMPLATES]


def succeeded(transcript: list[dict]) -> list[str]:
    return [e["tool"] for e in transcript if "tool" in e and "result" in e]


def test_shaping_bounds_keep_every_pass_above_every_failure():
    assert rewards.BONUS + rewards.MAX_PENALTY < 1
    rng = random.Random(0)
    names = [*rewards.WRITES, "get_ticket", "get_refund_policy", "get_itsm_policy", "wait"]
    for task in SAMPLE:
        for _ in range(200):
            calls = [rng.choice(names) for _ in range(rng.randint(0, 20))]
            term = rewards.shaping(task, 3, calls)
            assert -rewards.MAX_PENALTY <= term <= rewards.BONUS
            assert rewards.reward(False, task, 3, calls, True) < 1 - rewards.MAX_PENALTY


def test_shaping_rewards_reading_policy_first_and_penalizes_extra_writes():
    task = next(t for t in DEV if t.template == "eligible")  # Needs a refund and an update.
    base = ["get_ticket", "get_order", "issue_refund", "update_ticket"]
    assert rewards.shaping(task, 3, base) == 0
    assert rewards.shaping(task, 3, ["get_refund_policy", *base]) == rewards.BONUS
    assert rewards.shaping(task, 3, [*base, "update_ticket"]) == -rewards.PENALTY
    assert rewards.shaping(task, 3, [*base] + ["issue_refund"] * 10) == -rewards.MAX_PENALTY
    assert rewards.reward(True, task, 3, base) == 1.0  # Unshaped by default.


@pytest.mark.parametrize("task", SAMPLE, ids=lambda t: t.template)
async def test_shaped_hacks_and_near_misses_never_beat_the_oracle(task):
    worst_pass = min(
        [await _shaped(task, d, "oracle") for d in DRIFTS]
        + [await _shaped(task, d, "oracle_idem") for d in ("baseline", "ambiguous_write")]
    )
    gates = [(a, None, "baseline") for a in ("null", "refund_all", "close_all", "resolve_all")]
    gates += [
        ("oracle", s, "ambiguous_write" if s == "recheck" else "baseline")
        for s in near_misses(task)
    ]
    best_fail = max([await _shaped(task, d, a, s) for a, s, d in gates])
    assert worst_pass >= 1 - rewards.MAX_PENALTY > rewards.BONUS >= best_fail


async def _shaped(task, drift, agent, skip=None) -> float:
    transcript = []
    result, _ = await episode(task, drift, agent, skip, transcript)
    return rewards.reward(result.passed, task, policy_version(drift), succeeded(transcript), True)
