import pytest
from mcp import Client

from faultline import agents
from faultline.client import ToolClient
from faultline.db import TICKET_IDS, snapshot
from faultline.environment import DRIFTS, ToolFailure
from faultline.grader import grade
from faultline.server import create_server


@pytest.mark.parametrize("ticket", TICKET_IDS)
@pytest.mark.parametrize(
    "agent", ["reference", "oracle", "null", "refund_all", "close_all", "resolve_all"]
)
async def test_two_sided_and_blanket_hack_gates(database, ticket, agent):
    before = snapshot(database)
    async with Client(create_server(database), cache=None) as connection:
        client = ToolClient(connection, [])
        if agent in ("reference", "oracle", "null"):
            await getattr(agents, agent)(client, ticket)
        else:
            await agents.hack(client, ticket, agent)
    assert grade(before, database, ticket).passed == (agent in ("reference", "oracle"))


@pytest.mark.parametrize("ticket", TICKET_IDS)
@pytest.mark.parametrize("drift", DRIFTS)
async def test_oracle_solves_every_task_under_every_drift(database, ticket, drift):
    before = snapshot(database)
    async with Client(create_server(database, drift), cache=None) as connection:
        await agents.oracle(ToolClient(connection, []), ticket)
    result = grade(before, database, ticket)
    assert result.passed, result.failure_tags


async def test_oracle_does_not_repeat_a_committed_ambiguous_refund(database):
    before = snapshot(database)
    transcript = []
    async with Client(create_server(database, "ambiguous_write"), cache=None) as connection:
        await agents.oracle(ToolClient(connection, transcript), "T-1001")
    assert [e["tool"] for e in transcript].count("issue_refund") == 1
    assert len(snapshot(database)["refunds"]) == len(before["refunds"]) + 1


@pytest.mark.parametrize("drift", ["rename_param", "transient_503", "ambiguous_write"])
async def test_reference_stops_on_first_error(database, drift):
    before = snapshot(database)
    transcript = []
    async with Client(create_server(database, drift), cache=None) as connection:
        with pytest.raises(ToolFailure):
            await agents.reference(ToolClient(connection, transcript), "T-1001")
    assert not grade(before, database, "T-1001").passed
    assert "error" in transcript[-1]


async def test_read_after_ambiguous_write_recovers_without_duplicate(database):
    before = snapshot(database)
    async with Client(create_server(database, "ambiguous_write"), cache=None) as connection:
        client = ToolClient(connection, [])
        await client.call("get_order", order_id="O-1001")
        with pytest.raises(ToolFailure, match="504"):
            await client.call("issue_refund", order_id="O-1001", amount="49.99")
        assert (await client.call("get_order", order_id="O-1001"))["refunded_amount"] == "49.99"
        await client.call(
            "update_ticket", ticket_id="T-1001", status="resolved", note="Verified refund."
        )
    assert grade(before, database, "T-1001").passed


# The failure each skipped step must produce. "recheck" only matters after an ambiguous write.
NEAR_MISS_TAGS = {
    "refund": "missed_refund",
    "status": "wrong_status",
    "note": "missing_note",
    "escalate": "unauthorized_refund",
    "window": "unauthorized_refund",
    "prior_refund": "double_refund",
    "recheck": "double_refund",
    "ignore_message": "over_refund",
}


@pytest.mark.parametrize(
    ("ticket", "skip"), [(t, s) for t, steps in agents.NEAR_MISSES.items() for s in steps]
)
async def test_near_miss_agents_skipping_one_required_step_score_zero(database, ticket, skip):
    drift = "ambiguous_write" if skip == "recheck" else "baseline"
    before = snapshot(database)
    async with Client(create_server(database, drift), cache=None) as connection:
        await agents.oracle(ToolClient(connection, []), ticket, skip)
    result = grade(before, database, ticket)
    assert not result.passed and NEAR_MISS_TAGS[skip] in result.failure_tags


def test_every_task_has_the_common_near_misses():
    assert set(agents.NEAR_MISSES) == set(TICKET_IDS)
    for steps in agents.NEAR_MISSES.values():
        assert {"status", "note"} <= set(steps) and len(set(steps)) == len(steps)


@pytest.mark.parametrize("ticket", TICKET_IDS)
async def test_known_limit_skipping_a_pure_read_is_invisible_to_the_state_grader(database, ticket):
    # By design (§3 guardrail): a remembered policy gives the same final state, so it passes.
    before = snapshot(database)
    transcript = []
    async with Client(create_server(database), cache=None) as connection:
        await agents.oracle(ToolClient(connection, transcript), ticket, "read_policy")
    assert "get_refund_policy" not in [e["tool"] for e in transcript]
    assert grade(before, database, ticket).passed
