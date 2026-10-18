import pytest
from mcp import Client

from faultline.client import ToolClient
from faultline.db import snapshot
from faultline.drifts import COMBINED, DRIFTS, HELD_OUT, SINGLE, TRAIN_DRIFTS, parse
from faultline.environment import POLICIES, RefundTools, ToolFailure
from faultline.server import create_server


@pytest.mark.parametrize("name", list(SINGLE))
def test_every_drift_has_its_own_module_and_rationale(name):
    drift = SINGLE[name]
    assert drift.name == name and len(drift.rationale) > 20
    if name != "baseline":
        assert type(drift).__module__ == f"faultline.drifts.{name}"


def test_combined_drifts_parse_and_held_out_never_train():
    assert all(len(parse(c)) == 2 for c in COMBINED)
    assert set(HELD_OUT) <= set(COMBINED) and not set(HELD_OUT) & set(TRAIN_DRIFTS)
    assert len(DRIFTS) == len(SINGLE) + len(COMBINED)
    with pytest.raises(ValueError):
        parse("baseline+nothing")


def test_rate_limit_rejects_until_the_simulated_clock_passes_retry_after(database):
    tools = RefundTools(database, "rate_limit_429")
    args = {"order_id": "O-1001", "amount": "49.99"}
    for _ in range(3):  # Hammering never gets through, and nothing is written.
        with pytest.raises(ToolFailure, match="429.*not processed.*Retry-After: 2"):
            tools.call("issue_refund", args)
    assert len(snapshot(database)["refunds"]) == 1
    tools.call("wait", {"seconds": 1})
    with pytest.raises(ToolFailure, match="429"):
        tools.call("issue_refund", args)
    tools.call("wait", {"seconds": 1})
    assert tools.call("issue_refund", args)["amount"] == "49.99"
    assert len(snapshot(database)["refunds"]) == 2
    # Reads are never limited; wait exists only under this drift.
    assert tools.call("get_order", {"order_id": "O-1001"})["refunded_amount"] == "49.99"
    with pytest.raises(ToolFailure, match="Unknown tool"):
        RefundTools(database).call("wait", {"seconds": 1})
    with pytest.raises(ToolFailure):
        tools.call("wait", {"seconds": 0})


def test_pagination_pages_list_results_with_a_cursor(database):
    from faultline.db import connect

    with connect(database) as db:
        for n in range(3):
            db.execute(
                "INSERT INTO orders VALUES (?, 'C-1001', 'Spoon', 100, 'delivered', '2026-09-01')",
                (f"O-2{n}",),
            )
    tools = RefundTools(database, "pagination")
    first = tools.call("list_orders", {"customer_id": "C-1001"})
    assert len(first["orders"]) == 2 and first["next_cursor"] == "2"
    second = tools.call("list_orders", {"customer_id": "C-1001", "cursor": "2"})
    assert len(second["orders"]) == 2 and second["next_cursor"] is None
    assert {o["order_id"] for o in first["orders"] + second["orders"]} == {
        "O-1001",
        "O-20",
        "O-21",
        "O-22",
    }
    with pytest.raises(ToolFailure, match="cursor"):
        tools.call("list_orders", {"customer_id": "C-1001", "cursor": "x"})
    assert "next_cursor" not in RefundTools(database).call("list_orders", {"customer_id": "C-1001"})


async def test_description_drift_changes_a_listed_description_mid_session(database):
    async with Client(create_server(database, "description_drift"), cache=None) as connection:
        client = ToolClient(connection, [])
        before = {
            s["function"]["name"]: s["function"]["description"] for s in await client.schemas()
        }
        await client.call("get_ticket", ticket_id="T-1001")
        after = {
            s["function"]["name"]: s["function"]["description"] for s in await client.schemas()
        }
    assert "add 10.00" not in before["issue_refund"]
    assert "add 10.00" in after["issue_refund"]
    assert {k: v for k, v in before.items() if k != "issue_refund"} == {
        k: v for k, v in after.items() if k != "issue_refund"
    }


def test_policy_v4_shortens_the_window(database):
    assert RefundTools(database).call("get_refund_policy", {})["window_days"] == 30
    policy = RefundTools(database, "policy_v4").call("get_refund_policy", {})
    assert policy == POLICIES[4] and policy["window_days"] == 14 and "14 days" in policy["text"]


async def test_schemas_follow_drifts(database):
    async def tools(drift):
        async with Client(create_server(database, drift), cache=None) as connection:
            return {
                s["function"]["name"]: s["function"]["parameters"]["properties"]
                for s in await ToolClient(connection, []).schemas()
            }

    baseline, renamed = await tools("baseline"), await tools("rename_param")
    assert "order_id" in baseline["issue_refund"] and "order_ref" in renamed["issue_refund"]
    assert "cursor" in (await tools("pagination"))["list_orders"]
    assert "wait" in await tools("rate_limit_429") and "wait" not in baseline
    assert "idempotency_key" in baseline["issue_refund"]


def test_idempotency_key_makes_a_repeated_refund_a_no_op(database):
    tools = RefundTools(database, "ambiguous_write")
    args = {"order_id": "O-1001", "amount": "49.99", "idempotency_key": "k1"}
    with pytest.raises(ToolFailure, match="504"):
        tools.call("issue_refund", args)
    first = snapshot(database)["refunds"]
    assert tools.call("issue_refund", args)["refund_id"] == first[-1]["refund_id"]
    assert snapshot(database)["refunds"] == first
    with pytest.raises(ToolFailure, match="idempotency_key"):
        tools.call("issue_refund", {**args, "amount": "1.00"})
