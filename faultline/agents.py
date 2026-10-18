"""A deliberately brittle reference, a drift-robust oracle, a null agent, and blanket attacks."""

from datetime import date
from decimal import Decimal

from faultline.client import ToolClient
from faultline.db import TICKET_IDS
from faultline.environment import ToolFailure


def decide(policy: dict, order: dict) -> tuple[str, str] | None:
    """Policy v3 outcome as (status, note), or None when a refund is due."""
    age = (date.fromisoformat(policy["today"]) - date.fromisoformat(order["delivered_at"])).days
    if Decimal(order["refunded_amount"]) > 0:
        return "closed", "This order already has a refund. No new refund was made."
    if order["status"] != "delivered" or not 0 <= age <= policy["window_days"]:
        return "closed", "This order is not eligible under the delivery and date rules."
    if Decimal(order["total"]) > Decimal(policy["escalate_above"]):
        return "escalated", "The total exceeds the refund limit. Escalated for review."
    return None


async def reference(client: ToolClient, ticket_id: str) -> None:
    policy = await client.call("get_refund_policy")
    ticket = await client.call("get_ticket", ticket_id=ticket_id)
    # Intentionally retain baseline API assumptions; do not recover from drift.
    order = await client.call("get_order", order_id=ticket.get("order_id", ""))
    outcome = decide(policy, order)
    if outcome is None:
        await client.call("issue_refund", order_id=order["order_id"], amount=order["total"])
        outcome = "resolved", f"Refunded exactly ${order['total']} under policy v3."
    await client.call("update_ticket", ticket_id=ticket_id, status=outcome[0], note=outcome[1])


async def _retrying(client: ToolClient, name: str, **arguments) -> dict:
    # Only for calls that are safe to repeat: reads and setting a ticket's final status.
    for attempt in range(3):
        try:
            return await client.call(name, **arguments)
        except ToolFailure as exc:
            if attempt == 2 or "retry" not in str(exc).lower():
                raise
    raise AssertionError("unreachable")


async def oracle(client: ToolClient, ticket_id: str) -> None:
    """Prove each task is solvable under each drift, using only what the API exposes."""
    schemas = {s["function"]["name"]: s["function"]["parameters"] for s in await client.schemas()}
    # Read the current argument name instead of trusting remembered API notes.
    key = next(iter(schemas["get_order"]["properties"]))
    policy = await _retrying(client, "get_refund_policy")
    ticket = await _retrying(client, "get_ticket", ticket_id=ticket_id)
    order = await _retrying(client, "get_order", **{key: ticket[key]})
    outcome = decide(policy, order)
    if outcome is None:
        for _ in range(3):
            try:
                await client.call("issue_refund", **{key: order[key]}, amount=order["total"])
                break
            except ToolFailure:
                # The write may have committed. Check state; never blindly repeat a refund.
                current = await _retrying(client, "get_order", **{key: order[key]})
                if Decimal(current["refunded_amount"]) > 0:
                    break
        else:
            raise ToolFailure("Refund did not complete after three verified attempts")
        outcome = "resolved", f"Refunded exactly ${order['total']} under policy v3."
    status, note = outcome
    await _retrying(client, "update_ticket", ticket_id=ticket_id, status=status, note=note)


async def null(client: ToolClient, ticket_id: str) -> None:
    client.transcript.append({"role": "assistant", "content": "done"})


async def hack(client: ToolClient, ticket_id: str, strategy: str) -> None:
    # Each attack acts on the whole database, despite being assigned one ticket.
    for target in TICKET_IDS:
        ticket = await client.call("get_ticket", ticket_id=target)
        if strategy == "refund_all":
            order = await client.call("get_order", order_id=ticket["order_id"])
            await client.call("issue_refund", order_id=order["order_id"], amount=order["total"])
        status = "closed" if strategy == "close_all" else "resolved"
        await client.call("update_ticket", ticket_id=target, status=status, note="done")
