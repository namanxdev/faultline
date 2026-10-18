import pytest
from mcp import Client

from drift_gym import agents
from drift_gym.client import ToolClient
from drift_gym.db import TICKET_IDS, snapshot
from drift_gym.environment import ToolFailure
from drift_gym.grader import grade
from drift_gym.server import create_server


@pytest.mark.parametrize("ticket", TICKET_IDS)
@pytest.mark.parametrize("agent", ["reference", "null", "refund_all", "close_all", "resolve_all"])
async def test_two_sided_and_blanket_hack_gates(database, ticket, agent):
    before = snapshot(database)
    async with Client(create_server(database), cache=None) as connection:
        client = ToolClient(connection, [])
        if agent in ("reference", "null"):
            await getattr(agents, agent)(client, ticket)
        else:
            await agents.hack(client, ticket, agent)
    assert grade(before, database, ticket).passed == (agent == "reference")


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
