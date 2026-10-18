"""Declarative tool descriptions that the MCP server publishes and drifts rewrite."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Param:
    name: str
    type: type = str
    required: bool = True


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    params: tuple[Param, ...]
    kind: str  # "read" (safe to repeat) or "write" (changes state)
