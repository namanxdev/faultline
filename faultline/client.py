"""Record tool traffic and normalize MCP errors for both agent types."""

import json

from mcp import Client

from faultline.environment import ToolFailure


class ToolClient:
    def __init__(self, client: Client, transcript: list[dict]):
        self.client = client
        self.transcript = transcript

    async def schemas(self) -> list[dict]:
        result = await self.client.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in result.tools
        ]

    async def call(self, name: str, **arguments) -> dict:
        result = await self.client.call_tool(name, arguments)
        text = "\n".join(block.text for block in result.content if block.type == "text")
        if result.is_error:
            self.transcript.append({"tool": name, "arguments": arguments, "error": text})
            raise ToolFailure(text)
        value = result.structured_content
        if value is None:
            value = json.loads(text)
        if not isinstance(value, dict):
            raise ToolFailure("Tool returned a non-object response")
        self.transcript.append({"tool": name, "arguments": arguments, "result": value})
        return value
