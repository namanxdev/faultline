"""Official MCP SDK adapter. Each process owns one trial's drift counters."""

import argparse
import inspect
import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from faultline.environment import DRIFTS, RefundTools, ToolFailure, Tools
from faultline.itsm import ITSMTools
from faultline.toolspec import ToolSpec

DOMAINS = {"refund": RefundTools, "itsm": ITSMTools}


class DriftServer(MCPServer):
    def __init__(self, service: Tools):
        super().__init__("faultline", version="0.1.0", log_level="ERROR")
        self.service = service

    async def list_tools(self):
        # Descriptions are read per request, so description_drift can change them mid-session.
        current = {s.name: s.description for s in self.service.specs()}
        return [
            t.model_copy(update={"description": current[t.name]})
            for t in await super().list_tools()
        ]


def _tool(service: Tools, spec: ToolSpec):
    def run(**args) -> dict:
        try:
            return service.call(spec.name, {k: v for k, v in args.items() if v is not None})
        except ToolFailure as exc:
            raise ToolError(str(exc)) from exc

    # The SDK builds the input schema from this signature, so drifted names are published.
    run.__signature__ = inspect.Signature(
        [
            inspect.Parameter(
                p.name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=p.type if p.required else p.type | None,
                default=inspect.Parameter.empty if p.required else None,
            )
            for p in spec.params
        ],
        return_annotation=dict,
    )
    run.__name__ = spec.name
    return run


def create_server(path: str | Path, drift: str = "baseline", domain: str = "refund") -> MCPServer:
    service = DOMAINS[domain](path, drift)
    server = DriftServer(service)
    for spec in service.specs():
        server.add_tool(_tool(service, spec), name=spec.name, description=spec.description)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--drift", choices=DRIFTS, default=os.environ.get("DRIFT", "baseline"))
    parser.add_argument("--domain", choices=sorted(DOMAINS), default="refund")
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("Database does not exist. Run faultline seed first.")
    server = create_server(args.db, args.drift, args.domain)
    if args.http:
        server.run(transport="streamable-http", host="127.0.0.1", port=args.port)
    else:
        server.run()


if __name__ == "__main__":
    main()
