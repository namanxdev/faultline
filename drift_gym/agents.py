"""A deliberately brittle reference, a null agent, and blanket attack agents."""

from datetime import date
from decimal import Decimal

from drift_gym.client import ToolClient
from drift_gym.db import TICKET_IDS


async def reference(client: ToolClient, ticket_id: str) -> None:
    policy = await client.call("get_refund_policy")
    ticket = await client.call("get_ticket", ticket_id=ticket_id)
    # Intentionally retain baseline API assumptions; do not recover from drift.
    order = await client.call("get_order", order_id=ticket.get("order_id", ""))
    age = (date.fromisoformat(policy["today"]) - date.fromisoformat(order["delivered_at"])).days
    if Decimal(order["refunded_amount"]) > 0:
        status, note = "closed", "This order already has a refund. No new refund was made."
    elif order["status"] != "delivered" or not 0 <= age <= policy["window_days"]:
        status, note = "closed", "This order is not eligible under the delivery and date rules."
    elif Decimal(order["total"]) > Decimal(policy["escalate_above"]):
        status, note = "escalated", "The total exceeds the refund limit. Escalated for review."
    else:
        await client.call("issue_refund", order_id=order["order_id"], amount=order["total"])
        status, note = "resolved", f"Refunded exactly ${order['total']} under policy v3."
    await client.call("update_ticket", ticket_id=ticket_id, status=status, note=note)


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
