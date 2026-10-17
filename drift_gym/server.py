"""Official MCP SDK adapter. Each process owns one trial's drift counters."""

import argparse
import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from drift_gym.environment import DRIFTS, RefundTools, ToolFailure


def create_server(path: str | Path, drift: str = "baseline") -> MCPServer:
    service = RefundTools(path, drift)
    server = MCPServer("drift-gym", version="0.1.0", log_level="ERROR")

    def call(name: str, **args) -> dict:
        try:
            return service.call(name, args)
        except ToolFailure as exc:
            raise ToolError(str(exc)) from exc

    @server.tool()
    def get_ticket(ticket_id: str) -> dict:
        """Read a support ticket, including its customer, order, message, status, and note."""
        return call("get_ticket", ticket_id=ticket_id)

    @server.tool()
    def find_customer(email: str) -> dict:
        """Find a customer by exact email address."""
        return call("find_customer", email=email)

    @server.tool()
    def list_orders(customer_id: str) -> dict:
        """List customer orders in an object with an orders array."""
        return call("list_orders", customer_id=customer_id)

    @server.tool()
    def get_refund_policy() -> dict:
        """Read the authoritative current refund policy and today's date."""
        return call("get_refund_policy")

    @server.tool()
    def update_ticket(ticket_id: str, status: str, note: str) -> dict:
        """Set ticket status and note after taking the required action."""
        return call("update_ticket", ticket_id=ticket_id, status=status, note=note)

    if drift == "rename_param":

        @server.tool(name="get_order")
        def get_order_v2(order_ref: str) -> dict:
            """Read an order, including total and refunded_amount. Use order_ref."""
            return call("get_order", order_ref=order_ref)

        @server.tool(name="issue_refund")
        def issue_refund_v2(order_ref: str, amount: str) -> dict:
            """Issue a refund in dollars. Use order_ref. This write is not idempotent."""
            return call("issue_refund", order_ref=order_ref, amount=amount)
    else:

        @server.tool()
        def get_order(order_id: str) -> dict:
            """Read an order, including total and refunded_amount."""
            return call("get_order", order_id=order_id)

        @server.tool()
        def issue_refund(order_id: str, amount: str) -> dict:
            """Issue a refund in dollars. This write is not idempotent."""
            return call("issue_refund", order_id=order_id, amount=amount)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--drift", choices=DRIFTS, default=os.environ.get("DRIFT", "baseline"))
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("Database does not exist. Run drift-gym seed first.")
    server = create_server(args.db, args.drift)
    if args.http:
        server.run(transport="streamable-http", host="127.0.0.1", port=args.port)
    else:
        server.run()


if __name__ == "__main__":
    main()
