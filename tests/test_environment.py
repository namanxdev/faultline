import pytest

from drift_gym.db import snapshot
from drift_gym.environment import READ_TOOLS, RefundTools, ToolFailure

READ_ARGS = {
    "get_ticket": {"ticket_id": "T-1001"},
    "find_customer": {"email": "c1001@example.test"},
    "list_orders": {"customer_id": "C-1001"},
    "get_order": {"order_id": "O-1001"},
    "get_refund_policy": {},
}


@pytest.mark.parametrize("name", READ_TOOLS)
def test_transient_failure_is_once_per_read_tool(database, name):
    tools = RefundTools(database, "transient_503")
    with pytest.raises(ToolFailure, match="503.*Retry"):
        tools.call(name, READ_ARGS[name])
    assert isinstance(tools.call(name, READ_ARGS[name]), dict)
    assert isinstance(tools.call(name, READ_ARGS[name]), dict)
    # A fresh server has its own counters.
    with pytest.raises(ToolFailure, match="503"):
        RefundTools(database, "transient_503").call(name, READ_ARGS[name])


def test_rename_changes_nested_results_and_rejects_old_args(database):
    tools = RefundTools(database, "rename_param")
    ticket = tools.call("get_ticket", {"ticket_id": "T-1001"})
    assert ticket["order_ref"] == "O-1001" and "order_id" not in ticket
    orders = tools.call("list_orders", {"customer_id": "C-1001"})
    assert orders["orders"][0]["order_ref"] == "O-1001"
    for name, extra in [("get_order", {}), ("issue_refund", {"amount": "49.99"})]:
        with pytest.raises(ToolFailure, match="order_ref"):
            tools.call(name, {"order_id": "O-1001", **extra})
        assert tools.call(name, {"order_ref": "O-1001", **extra})["order_ref"] == "O-1001"


def test_ambiguous_write_commits_then_naive_retry_duplicates(database):
    tools = RefundTools(database, "ambiguous_write")
    args = {"order_id": "O-1001", "amount": "49.99"}
    with pytest.raises(ToolFailure, match="504.*may or may not"):
        tools.call("issue_refund", args)
    assert tools.call("get_order", {"order_id": "O-1001"})["refunded_amount"] == "49.99"
    tools.call("issue_refund", args)
    assert tools.call("get_order", {"order_id": "O-1001"})["refunded_amount"] == "99.98"


def test_server_does_not_enforce_policy(database):
    tools = RefundTools(database)
    # Even an old order can receive too much money: the agent and grader own policy.
    tools.call("issue_refund", {"order_id": "O-1004", "amount": "500.00"})
    assert snapshot(database)["refunds"][-1]["amount_cents"] == 50000
    with pytest.raises(ToolFailure, match="Unknown"):
        tools.call("issue_refund", {"order_id": "missing", "amount": "1.00"})
    with pytest.raises(ToolFailure):
        tools.call("issue_refund", {"order_id": "O-1001", "amount": "0"})


def test_policy_results_are_not_mutable_shared_state(database):
    tools = RefundTools(database)
    tools.call("get_refund_policy", {})["window_days"] = 100
    assert tools.call("get_refund_policy", {})["window_days"] == 30
